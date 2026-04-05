from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentInterrupt:
    interrupt_id: str
    kind: str
    title: str
    message: str
    actions: list[str] = field(default_factory=lambda: ["approve", "reject"])
    selected_model_id: str = ""
    model_options: list[dict[str, Any]] = field(default_factory=list)
    scope_item_ids: list[str] = field(default_factory=list)


@dataclass
class CanvasAgentSession:
    session_id: str
    user_id: str
    document_id: str
    conversation: list[dict[str, Any]] = field(default_factory=list)
    selected_item_ids: list[str] = field(default_factory=list)
    checkpoint_id: str = ""
    checkpoint_state: dict[str, Any] = field(default_factory=dict)
    pending_interrupt: AgentInterrupt | None = None
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    resume_in_flight: bool = False


@dataclass
class CanvasAssistantTurnResult:
    session_id: str
    message: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    pending_interrupt: AgentInterrupt | None = None
