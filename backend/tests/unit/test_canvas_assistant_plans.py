import pytest

from src.assistant.plans import validate_assistant_plan


def test_validate_assistant_plan_accepts_ask_follow_up() -> None:
    plan = validate_assistant_plan(
        {
            "kind": "ask_follow_up",
            "question": "你希望这个剧本偏向什么类型和长度？",
            "reason": "生成剧本前信息不足。",
            "task": "create_nodes",
            "missing_slots": ["genre", "duration"],
        }
    )

    assert plan.kind == "ask_follow_up"
    assert plan.question == "你希望这个剧本偏向什么类型和长度？"
    assert plan.task == "create_nodes"
    assert plan.missing_slots == ["genre", "duration"]


def test_validate_assistant_plan_accepts_conversation_only() -> None:
    plan = validate_assistant_plan(
        {
            "kind": "conversation_only",
            "message": "你好，我可以帮你生成剧本、拆分节点、优化提示词。",
        }
    )

    assert plan.kind == "conversation_only"
    assert plan.message == "你好，我可以帮你生成剧本、拆分节点、优化提示词。"


def test_validate_assistant_plan_accepts_operation_plan_with_generic_actions() -> None:
    plan = validate_assistant_plan(
        {
            "kind": "operation_plan",
            "title": "批量调整镜头节点",
            "message": "我会更新两个节点，并提交一个生成任务。",
            "requires_confirmation": True,
            "operations": [
                {
                    "type": "update_items",
                    "updates": [
                        {"item_id": "shot-1", "patch": {"title": "镜头 1 - 夜景版"}},
                        {"item_id": "shot-2", "patch": {"title": "镜头 2 - 夜景版"}},
                    ],
                },
                {
                    "type": "submit_generation",
                    "requests": [
                        {"item_id": "shot-2", "kind": "image"},
                    ],
                },
            ],
        }
    )

    assert plan.kind == "operation_plan"
    assert plan.requires_confirmation is True
    assert plan.operations[0].type == "update_items"
    assert plan.operations[1].type == "submit_generation"


def test_validate_assistant_plan_rejects_update_items_missing_item_id() -> None:
    with pytest.raises(ValueError):
        validate_assistant_plan(
            {
                "kind": "operation_plan",
                "operations": [
                    {
                        "type": "update_items",
                        "updates": [{"patch": {"title": "New title"}}],
                    }
                ],
            }
        )
