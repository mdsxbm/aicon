"""
assistant 通用计划结构。

这一版不再围绕“固定 workflow”建模，而是把 assistant 输出收敛成三类：
1. `conversation_only`：纯对话，不改画布。
2. `ask_follow_up`：当前任务还缺信息，需要继续追问。
3. `operation_plan`：已经形成可执行的通用画布操作计划。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class AskFollowUpPlan(BaseModel):
    """继续追问计划。"""

    kind: Literal["ask_follow_up"]
    question: str
    reason: str = ""
    task: str = ""
    missing_slots: list[str] = Field(default_factory=list)


class ConversationOnlyPlan(BaseModel):
    """纯对话计划。"""

    kind: Literal["conversation_only"]
    message: str


class UpdateItemPayload(BaseModel):
    """单个节点 patch。"""

    item_id: str
    patch: dict[str, Any] = Field(default_factory=dict)


class CreateItemsOperation(BaseModel):
    type: Literal["create_items"]
    items: list[dict[str, Any]]


class UpdateItemsOperation(BaseModel):
    type: Literal["update_items"]
    updates: list[UpdateItemPayload]


class ConnectItemsOperation(BaseModel):
    type: Literal["connect_items"]
    connections: list[dict[str, Any]]


class DeleteItemsOperation(BaseModel):
    type: Literal["delete_items"]
    item_ids: list[str]


class SubmitGenerationOperation(BaseModel):
    type: Literal["submit_generation"]
    requests: list[dict[str, Any]]


Operation = (
    CreateItemsOperation
    | UpdateItemsOperation
    | ConnectItemsOperation
    | DeleteItemsOperation
    | SubmitGenerationOperation
)


class OperationPlan(BaseModel):
    """通用画布操作计划。"""

    kind: Literal["operation_plan"]
    title: str = ""
    message: str = ""
    requires_confirmation: bool = False
    operations: list[Operation] = Field(default_factory=list)


AssistantPlan = AskFollowUpPlan | ConversationOnlyPlan | OperationPlan


def validate_assistant_plan(raw_plan: dict[str, Any]) -> AssistantPlan:
    """校验并规范化 assistant 计划。

    参数说明：
    - raw_plan: 大模型或规则规划器产出的原始计划字典。
    """
    try:
        kind = str(raw_plan.get("kind") or "").strip()
        if kind == "ask_follow_up":
            return AskFollowUpPlan.model_validate(raw_plan)
        if kind == "conversation_only":
            return ConversationOnlyPlan.model_validate(raw_plan)
        if kind == "operation_plan":
            return OperationPlan.model_validate(raw_plan)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    raise ValueError(
        "assistant plan kind must be 'ask_follow_up', 'conversation_only' or 'operation_plan'"
    )

