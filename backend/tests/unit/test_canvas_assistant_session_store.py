import json
import uuid

import pytest

from src.assistant.session_store import RedisCanvasAssistantSessionStore
from src.assistant.types import AgentInterrupt, CanvasAgentSession
from src.models.canvas import CanvasItem


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def delete(self, *keys: str):
        removed = 0
        for key in keys:
            if key in self.values:
                removed += 1
                self.values.pop(key, None)
        return removed


@pytest.mark.asyncio
async def test_redis_session_store_persists_pending_interrupt_and_checkpoint() -> None:
    store = RedisCanvasAssistantSessionStore(FakeRedis(), ttl_seconds=600)
    session = CanvasAgentSession(
        session_id="session-1",
        user_id="user-1",
        document_id="doc-1",
        conversation=[{"role": "user", "content": "hello"}],
        pending_interrupt=AgentInterrupt(
            interrupt_id="interrupt-1",
            kind="confirm_execute",
            title="确认执行画布操作",
            message="准备执行",
            actions=["approve", "reject"],
            scope_item_ids=["item-1"],
        ),
        checkpoint_id="checkpoint-1",
        checkpoint_state={"operations": [{"tool_name": "canvas.update_items"}]},
    )

    await store.save(session)
    restored = await store.require("session-1", "user-1", "doc-1")

    assert restored.pending_interrupt is not None
    assert restored.pending_interrupt.interrupt_id == "interrupt-1"
    assert restored.checkpoint_state == {"operations": [{"tool_name": "canvas.update_items"}]}


@pytest.mark.asyncio
async def test_redis_session_store_rejects_duplicate_resume_lock() -> None:
    redis = FakeRedis()
    store = RedisCanvasAssistantSessionStore(redis, ttl_seconds=600)
    session = CanvasAgentSession(
        session_id="session-1",
        user_id="user-1",
        document_id="doc-1",
        pending_interrupt=AgentInterrupt(
            interrupt_id="interrupt-1",
            kind="confirm_execute",
            title="确认执行画布操作",
            message="准备执行",
            actions=["approve", "reject"],
        ),
    )
    await store.save(session)

    resumed = await store.begin_resume("session-1", "user-1", "doc-1", "interrupt-1")
    assert resumed.session_id == "session-1"

    with pytest.raises(ValueError, match="already resuming"):
        await store.begin_resume("session-1", "user-1", "doc-1", "interrupt-1")

    payload = json.loads(redis.values[store._session_key("session-1")])
    assert payload["resume_in_flight"] is True


@pytest.mark.asyncio
async def test_redis_session_store_serializes_canvas_models_in_tool_trace() -> None:
    store = RedisCanvasAssistantSessionStore(FakeRedis(), ttl_seconds=600)
    item = CanvasItem(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        item_type="text",
        title="新标题",
        content_json={"text": "内容"},
        generation_config_json={},
        last_output_json={},
    )
    session = CanvasAgentSession(
        session_id="session-serialize",
        user_id="user-1",
        document_id="doc-1",
        tool_trace=[{"tool_name": "canvas.update_items", "result": [item]}],
    )

    await store.save(session)
    restored = await store.require("session-serialize", "user-1", "doc-1")

    serialized_item = restored.tool_trace[0]["result"][0]
    assert serialized_item["title"] == "新标题"
