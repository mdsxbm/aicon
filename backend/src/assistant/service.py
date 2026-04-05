from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.api.schemas.canvas_assistant import CanvasAssistantChatRequest, CanvasAssistantResumeRequest
from src.assistant.planner import CanvasAgentPlanner
from src.assistant.session_store import InMemoryCanvasAssistantSessionStore
from src.assistant.tools.canvas_tools import CanvasAssistantCanvasReadTools, CanvasAssistantCanvasWriteTools
from src.assistant.tools.generation_tools import CanvasAssistantGenerationTools, CanvasAssistantObservationTools
from src.assistant.types import AgentInterrupt, CanvasAgentSession, CanvasAssistantTurnResult


class CanvasAssistantService:
    def __init__(
        self,
        session_store: Any | None = None,
        planner: Any | None = None,
        canvas_read_tools: Any | None = None,
        canvas_write_tools: Any | None = None,
        generation_tools: Any | None = None,
        observation_tools: Any | None = None,
    ) -> None:
        self.session_store = session_store or InMemoryCanvasAssistantSessionStore()
        self.planner = planner or CanvasAgentPlanner()
        self.canvas_read_tools = canvas_read_tools or CanvasAssistantCanvasReadTools()
        self.canvas_write_tools = canvas_write_tools or CanvasAssistantCanvasWriteTools()
        self.generation_tools = generation_tools or CanvasAssistantGenerationTools()
        self.observation_tools = observation_tools or CanvasAssistantObservationTools(self.canvas_read_tools)

    async def chat(self, request: CanvasAssistantChatRequest, user_id: str) -> CanvasAssistantTurnResult:
        session_id = request.session_id or str(uuid4())
        session = await self.session_store.get_or_create(session_id, user_id, request.document_id)
        session_id = session.session_id
        snapshot = await self.canvas_read_tools.get_canvas_snapshot(
            request.document_id,
            user_id,
            item_ids=request.selected_item_ids,
        )
        session.selected_item_ids = list(request.selected_item_ids)
        session.conversation.append({"role": "user", "content": request.message})

        plan = await self.planner(
            {
                "message": request.message,
                "user_id": user_id,
                "document_id": request.document_id,
                "api_key_id": request.api_key_id,
                "chat_model_id": request.chat_model_id,
                "selected_item_ids": request.selected_item_ids,
                "snapshot": snapshot,
                "conversation": session.conversation,
            }
        )

        events = [{"type": "agent.session.started", "data": {"session_id": session_id}}]
        if plan.get("kind") == "conversation":
            message = str(plan.get("message") or "").strip()
            session.conversation.append({"role": "assistant", "content": message})
            events.append({"type": "agent.message.delta", "data": {"delta": message}})
            events.append({"type": "agent.done", "data": {"session_id": session_id}})
            await self.session_store.save(session)
            return CanvasAssistantTurnResult(session_id=session_id, message=message, events=events)

        interrupt = AgentInterrupt(
            interrupt_id=f"interrupt-{uuid4()}",
            kind="confirm_execute",
            title="确认执行画布操作",
            message=str(plan.get("message") or "准备执行画布操作。").strip(),
            scope_item_ids=list(request.selected_item_ids),
        )
        session.pending_interrupt = interrupt
        session.checkpoint_id = f"checkpoint-{uuid4()}"
        session.checkpoint_state = {"operations": list(plan.get("operations") or [])}
        await self.session_store.save(session)
        events.extend(
            [
                {"type": "agent.step.started", "data": {"id": "step-plan", "title": "Plan turn", "status": "running"}},
                {"type": "agent.step.completed", "data": {"id": "step-plan", "title": "Plan turn", "status": "completed"}},
                {
                    "type": "agent.interrupt.requested",
                    "data": {
                        "session_id": session_id,
                        "interrupt_id": interrupt.interrupt_id,
                        "kind": interrupt.kind,
                        "title": interrupt.title,
                        "message": interrupt.message,
                        "actions": interrupt.actions,
                        "selected_model_id": interrupt.selected_model_id,
                        "model_options": interrupt.model_options,
                        "scope_item_ids": interrupt.scope_item_ids,
                    },
                },
                {"type": "agent.done", "data": {"session_id": session_id}},
            ]
        )
        return CanvasAssistantTurnResult(
            session_id=session_id,
            message=interrupt.message,
            events=events,
            pending_interrupt=interrupt,
        )

    async def resume(self, request: CanvasAssistantResumeRequest, user_id: str) -> CanvasAssistantTurnResult:
        session = await self.session_store.begin_resume(
            request.session_id,
            user_id,
            request.document_id,
            request.interrupt_id,
        )
        events = [{"type": "agent.session.started", "data": {"session_id": session.session_id}}]
        if request.decision == "reject":
            await self.session_store.clear_interrupt(session)
            message = "已取消当前操作。"
            session.conversation.append({"role": "assistant", "content": message})
            events.append({"type": "agent.message.delta", "data": {"delta": message}})
            events.append({"type": "agent.done", "data": {"session_id": session.session_id}})
            return CanvasAssistantTurnResult(session_id=session.session_id, message=message, events=events)

        operations = list((session.checkpoint_state or {}).get("operations") or [])
        observation_item_ids = list(request.selected_item_ids or session.selected_item_ids)
        tool_results: list[dict[str, Any]] = []
        observation = None
        executed_operation_count = 0
        events.append({"type": "agent.step.started", "data": {"id": "step-execute", "title": "Execute tools", "status": "running"}})
        for operation in operations:
            tool_name = str(operation.get("tool_name") or "").strip()
            args = dict(operation.get("args") or {})
            if not tool_name:
                continue
            if tool_name == "observe.effects":
                observation = await self.observation_tools.observe_effects(
                    document_id=request.document_id,
                    user_id=user_id,
                    item_ids=args.get("item_ids") or observation_item_ids,
                )
                continue
            events.append({"type": "agent.tool.call", "data": {"id": f"tool-{uuid4()}", "tool_name": tool_name, "args": args}})
            result = await self._run_tool(tool_name, args, request.document_id, user_id)
            executed_operation_count += 1
            tool_results.append({"tool_name": tool_name, "result": result})
            events.append({"type": "agent.tool.result", "data": {"tool_name": tool_name, "result": result}})
            if tool_name.startswith("canvas.") and not observation_item_ids:
                observation_item_ids = self._extract_item_ids(result)

        if observation_item_ids:
            observation = observation or await self.observation_tools.observe_effects(
                document_id=request.document_id,
                user_id=user_id,
                item_ids=observation_item_ids,
            )
        events.append({"type": "agent.step.completed", "data": {"id": "step-execute", "title": "Execute tools", "status": "completed"}})
        message = f"已完成 {executed_operation_count} 个操作，并同步最新画布状态。"
        session.conversation.append({"role": "assistant", "content": message})
        session.tool_trace = tool_results
        session.checkpoint_state = {}
        session.pending_interrupt = None
        session.resume_in_flight = False
        await self.session_store.save(session)
        events.append({"type": "agent.message.delta", "data": {"delta": message}})
        events.append({"type": "agent.done", "data": {"session_id": session.session_id, "observation": observation or {}}})
        return CanvasAssistantTurnResult(session_id=session.session_id, message=message, events=events)

    async def _run_tool(self, tool_name: str, args: dict[str, Any], document_id: str, user_id: str) -> Any:
        if tool_name == "canvas.create_items":
            return await self.canvas_write_tools.create_items(document_id, user_id, args.get("items") or [])
        if tool_name == "canvas.update_items":
            return await self.canvas_write_tools.update_items(document_id, user_id, args.get("updates") or [])
        if tool_name == "canvas.delete_items":
            return await self.canvas_write_tools.delete_items(document_id, user_id, args.get("item_ids") or [])
        if tool_name == "canvas.create_connections":
            return await self.canvas_write_tools.create_connections(document_id, user_id, args.get("connections") or [])
        if tool_name == "canvas.delete_connections":
            return await self.canvas_write_tools.delete_connections(document_id, user_id, args.get("connection_ids") or [])
        if tool_name == "generation.submit":
            return await self.generation_tools.submit_generation_tasks(user_id=user_id, requests=args.get("requests") or [])
        if tool_name == "observe.effects":
            return await self.observation_tools.observe_effects(
                document_id=document_id,
                user_id=user_id,
                item_ids=args.get("item_ids") or [],
            )
        return {}

    def _extract_item_ids(self, result: Any) -> list[str]:
        items = result if isinstance(result, list) else result.get("items") if isinstance(result, dict) else []
        return [str(item.get("id") or "").strip() for item in items or [] if isinstance(item, dict) and str(item.get("id") or "").strip()]
