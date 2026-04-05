from __future__ import annotations

from typing import Any


class CanvasAgentPlanner:
    def __init__(self, llm_planner: Any | None = None) -> None:
        self.llm_planner = llm_planner

    async def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        llm_plan = await self._try_llm_plan(payload)
        if llm_plan:
            translated = self._translate_llm_plan(llm_plan)
            if translated:
                return translated
        return self._fallback_plan(payload)

    async def _try_llm_plan(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if self.llm_planner is None:
            return None
        try:
            return await self.llm_planner(payload)
        except Exception:
            return None

    def _translate_llm_plan(self, llm_plan: dict[str, Any]) -> dict[str, Any] | None:
        mode = str(llm_plan.get("mode") or "").strip().lower()
        reply = str(llm_plan.get("reply") or "").strip()
        if mode == "conversation" and reply:
            return {"kind": "conversation", "message": reply}
        if mode == "interrupt":
            operations = list(llm_plan.get("operations") or [])
            if not operations:
                return None
            return {
                "kind": "action",
                "intent": "llm_planned_action",
                "message": reply or "准备执行画布操作。",
                "requires_interrupt": bool(llm_plan.get("needs_interrupt", True)),
                "operations": operations,
            }
        return None

    def _fallback_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = str(payload.get("message") or "").strip()
        selected_ids = [str(item_id).strip() for item_id in payload.get("selected_item_ids") or [] if str(item_id).strip()]
        snapshot = payload.get("snapshot") or {}
        selected_items = list(snapshot.get("selected_items") or [])

        if not message:
            return {"kind": "conversation", "message": "请直接告诉我要在画布上做什么，例如改标题、创建节点、生成图片或连接节点。"}

        lowered = message.lower()
        if any(keyword in lowered for keyword in ("你好", "hello", "hi", "你能做什么")):
            return {
                "kind": "conversation",
                "message": "我可以读取当前画布、定位节点、更新提示词、调整节点与连线，并提交文本/图片/视频生成任务。",
            }

        if selected_ids and ("标题" in message or "rename" in lowered or "改成" in message):
            target_title = "新标题"
            if "改成" in message:
                target_title = message.split("改成", 1)[1].strip(" 。,，")
            return {
                "kind": "action",
                "intent": "update_items",
                "message": f"准备把 {len(selected_ids)} 个节点更新为新标题。",
                "requires_interrupt": True,
                "operations": [
                    {
                        "tool_name": "canvas.update_items",
                        "args": {
                            "updates": [{"item_id": item_id, "patch": {"title": target_title}} for item_id in selected_ids]
                        },
                    }
                ],
            }

        if selected_items and any(keyword in message for keyword in ("生成图片", "生成图", "出图")):
            return {
                "kind": "action",
                "intent": "submit_generation",
                "message": "准备为当前节点提交图片生成任务。",
                "requires_interrupt": True,
                "operations": [
                    {
                        "tool_name": "generation.submit",
                        "args": {
                            "requests": [
                                {"item_id": str(item.get("id") or ""), "kind": "image", "payload": {"prompt": message}}
                                for item in selected_items
                            ]
                        },
                    }
                ],
            }

        if any(keyword in message for keyword in ("创建节点", "新建节点", "新增节点")):
            return {
                "kind": "action",
                "intent": "create_items",
                "message": "准备创建一个新文本节点。",
                "requires_interrupt": True,
                "operations": [
                    {
                        "tool_name": "canvas.create_items",
                        "args": {
                            "items": [{"item_type": "text", "title": "新节点", "content": {"text": message}}]
                        },
                    }
                ],
            }

        item_titles = [str(item.get("title") or "").strip() for item in list(snapshot.get("items") or [])[:3] if str(item.get("title") or "").strip()]
        context_hint = f"当前画布里我先看到了：{'、'.join(item_titles)}。" if item_titles else "当前画布里还没有可直接操作的节点。"
        return {
            "kind": "conversation",
            "message": f"{context_hint} 请明确告诉我要改哪个节点、改什么字段，或者让我为哪个节点生成文本/图片/视频。",
        }
