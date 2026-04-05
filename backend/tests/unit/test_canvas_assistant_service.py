from unittest.mock import AsyncMock

import pytest

from src.api.schemas.canvas_assistant import CanvasAssistantChatRequest, CanvasAssistantResumeRequest
from src.assistant.service import CanvasAssistantService
from src.assistant.sse import encode_sse_event
from src.assistant.types import AgentInterrupt, CanvasAgentSession


def test_sse_event_writer_serializes_agent_event() -> None:
    body = encode_sse_event("agent.message.delta", {"delta": "hello"})
    assert body == 'data: {"type":"agent.message.delta","data":{"delta":"hello"}}\n\n'


@pytest.mark.asyncio
async def test_chat_emits_agent_interrupt_protocol_for_mutating_turn() -> None:
    planner = AsyncMock(
        return_value={
            "kind": "action",
            "intent": "update_items",
            "message": "把当前节点标题更新为新标题",
            "requires_interrupt": True,
            "operations": [
                {
                    "tool_name": "canvas.update_items",
                    "args": {
                        "updates": [
                            {
                                "item_id": "item-1",
                                "patch": {"title": "新标题"},
                            }
                        ]
                    },
                }
            ],
        }
    )
    store = AsyncMock()
    store.get_or_create.return_value = CanvasAgentSession(
        session_id="session-1",
        user_id="user-1",
        document_id="doc-1",
    )
    read_tools = AsyncMock()
    read_tools.get_canvas_snapshot.return_value = {
        "document": {"id": "doc-1"},
        "items": [{"id": "item-1", "title": "旧标题", "item_type": "text", "content": {"text": "旧内容"}}],
        "connections": [],
        "selected_items": [{"id": "item-1", "title": "旧标题", "item_type": "text", "content": {"text": "旧内容"}}],
    }

    service = CanvasAssistantService(
        session_store=store,
        planner=planner,
        canvas_read_tools=read_tools,
        canvas_write_tools=AsyncMock(),
        generation_tools=AsyncMock(),
        observation_tools=AsyncMock(),
    )

    result = await service.chat(
        CanvasAssistantChatRequest(
            document_id="doc-1",
            message="把这个节点标题改成新标题",
            selected_item_ids=["item-1"],
        ),
        user_id="user-1",
    )

    assert result.pending_interrupt is not None
    assert [event["type"] for event in result.events] == [
        "agent.session.started",
        "agent.step.started",
        "agent.step.completed",
        "agent.interrupt.requested",
        "agent.done",
    ]
    assert result.events[3]["data"] == {
        "session_id": "session-1",
        "interrupt_id": result.pending_interrupt.interrupt_id,
        "kind": "confirm_execute",
        "title": "确认执行画布操作",
        "message": "把当前节点标题更新为新标题",
        "actions": ["approve", "reject"],
        "selected_model_id": "",
        "model_options": [],
        "scope_item_ids": ["item-1"],
    }


@pytest.mark.asyncio
async def test_resume_executes_tools_and_emits_process_events() -> None:
    store = AsyncMock()
    store.begin_resume.return_value = CanvasAgentSession(
        session_id="session-1",
        user_id="user-1",
        document_id="doc-1",
        pending_interrupt=AgentInterrupt(
            interrupt_id="interrupt-1",
            kind="confirm_execute",
            title="确认执行画布操作",
            message="准备执行",
            actions=["approve", "reject"],
            scope_item_ids=["item-1"],
        ),
        checkpoint_state={
            "operations": [
                {
                    "tool_name": "canvas.update_items",
                    "args": {"updates": [{"item_id": "item-1", "patch": {"title": "新标题"}}]},
                },
                {
                    "tool_name": "observe.effects",
                    "args": {"item_ids": ["item-1"]},
                },
            ]
        },
    )
    read_tools = AsyncMock()
    write_tools = AsyncMock()
    write_tools.update_items.return_value = [{"id": "item-1", "title": "新标题"}]
    observation_tools = AsyncMock()
    observation_tools.observe_effects.return_value = {
        "items": [{"id": "item-1", "title": "新标题"}],
        "connections": [],
    }

    service = CanvasAssistantService(
        session_store=store,
        planner=AsyncMock(),
        canvas_read_tools=read_tools,
        canvas_write_tools=write_tools,
        generation_tools=AsyncMock(),
        observation_tools=observation_tools,
    )

    result = await service.resume(
        CanvasAssistantResumeRequest(
            document_id="doc-1",
            session_id="session-1",
            interrupt_id="interrupt-1",
            decision="approve",
            selected_item_ids=["item-1"],
        ),
        user_id="user-1",
    )

    assert [event["type"] for event in result.events] == [
        "agent.session.started",
        "agent.step.started",
        "agent.tool.call",
        "agent.tool.result",
        "agent.step.completed",
        "agent.message.delta",
        "agent.done",
    ]
    write_tools.update_items.assert_awaited_once()
    observation_tools.observe_effects.assert_awaited_once_with(
        document_id="doc-1",
        user_id="user-1",
        item_ids=["item-1"],
    )
    assert result.events[3]["data"]["tool_name"] == "canvas.update_items"
    assert result.events[5]["data"]["delta"] == "已完成 1 个操作，并同步最新画布状态。"
