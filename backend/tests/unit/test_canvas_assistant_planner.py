import pytest

from src.assistant.planner import CanvasAgentPlanner


class _FakeLLMPlanner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def __call__(self, payload):
        self.calls.append(payload)
        return self.result


@pytest.mark.asyncio
async def test_planner_returns_conversation_for_greeting() -> None:
    planner = CanvasAgentPlanner()

    plan = await planner(
        {
            "user_id": "user-1",
            "message": "你好",
            "selected_item_ids": [],
            "snapshot": {"document": {"id": "doc-1"}, "items": [], "connections": [], "selected_items": []},
        }
    )

    assert plan["kind"] == "conversation"
    assert "画布" in plan["message"]


@pytest.mark.asyncio
async def test_planner_returns_interruptible_update_action_for_selected_items() -> None:
    planner = CanvasAgentPlanner()

    plan = await planner(
        {
            "user_id": "user-1",
            "message": "把这个节点标题改成新标题",
            "selected_item_ids": ["item-1"],
            "snapshot": {
                "document": {"id": "doc-1"},
                "items": [{"id": "item-1", "item_type": "text", "title": "旧标题", "content": {"text": "旧内容"}}],
                "connections": [],
                "selected_items": [{"id": "item-1", "item_type": "text", "title": "旧标题", "content": {"text": "旧内容"}}],
            },
        }
    )

    assert plan["kind"] == "action"
    assert plan["requires_interrupt"] is True
    assert plan["operations"][0]["tool_name"] == "canvas.update_items"


@pytest.mark.asyncio
async def test_planner_returns_generation_submission_for_generate_request() -> None:
    planner = CanvasAgentPlanner()

    plan = await planner(
        {
            "user_id": "user-1",
            "message": "给这个节点生成图片",
            "selected_item_ids": ["item-1"],
            "snapshot": {
                "document": {"id": "doc-1"},
                "items": [{"id": "item-1", "item_type": "image", "title": "镜头 1", "content": {"prompt": "雨夜"}}],
                "connections": [],
                "selected_items": [{"id": "item-1", "item_type": "image", "title": "镜头 1", "content": {"prompt": "雨夜"}}],
            },
        }
    )

    assert plan["kind"] == "action"
    assert plan["operations"][0]["tool_name"] == "generation.submit"


@pytest.mark.asyncio
async def test_planner_prefers_llm_conversation_response_over_static_fallback() -> None:
    llm_planner = _FakeLLMPlanner(
        {
            "mode": "conversation",
            "reply": "我看到当前画布只有一个文本节点《开场旁白》，你可以让我直接改标题、扩写文案或继续往下生成图片节点。",
            "target_item_ids": ["item-1"],
        }
    )
    planner = CanvasAgentPlanner(llm_planner=llm_planner)

    plan = await planner(
        {
            "user_id": "user-1",
            "api_key_id": "key-1",
            "chat_model_id": "gpt-4o-mini",
            "message": "这个画布现在适合下一步做什么？",
            "selected_item_ids": [],
            "snapshot": {
                "document": {"id": "doc-1"},
                "items": [{"id": "item-1", "item_type": "text", "title": "开场旁白", "content": {"text": "雨夜"}}],
                "connections": [],
                "selected_items": [],
            },
        }
    )

    assert plan == {
        "kind": "conversation",
        "message": "我看到当前画布只有一个文本节点《开场旁白》，你可以让我直接改标题、扩写文案或继续往下生成图片节点。",
    }
    assert len(llm_planner.calls) == 1


@pytest.mark.asyncio
async def test_planner_translates_llm_structured_operations_into_interruptible_action() -> None:
    llm_planner = _FakeLLMPlanner(
        {
            "mode": "interrupt",
            "reply": "我准备把当前选中的节点标题改成“雨夜开场”。",
            "needs_interrupt": True,
            "target_item_ids": ["item-1"],
            "operations": [
                {
                    "tool_name": "canvas.update_items",
                    "args": {"updates": [{"item_id": "item-1", "patch": {"title": "雨夜开场"}}]},
                }
            ],
        }
    )
    planner = CanvasAgentPlanner(llm_planner=llm_planner)

    plan = await planner(
        {
            "user_id": "user-1",
            "api_key_id": "key-1",
            "chat_model_id": "gpt-4o-mini",
            "message": "把这个节点标题改成雨夜开场",
            "selected_item_ids": ["item-1"],
            "snapshot": {
                "document": {"id": "doc-1"},
                "items": [{"id": "item-1", "item_type": "text", "title": "旧标题", "content": {"text": "旧内容"}}],
                "connections": [],
                "selected_items": [{"id": "item-1", "item_type": "text", "title": "旧标题", "content": {"text": "旧内容"}}],
            },
        }
    )

    assert plan["kind"] == "action"
    assert plan["requires_interrupt"] is True
    assert plan["message"] == "我准备把当前选中的节点标题改成“雨夜开场”。"
    assert plan["operations"] == [
        {
            "tool_name": "canvas.update_items",
            "args": {"updates": [{"item_id": "item-1", "patch": {"title": "雨夜开场"}}]},
        }
    ]
