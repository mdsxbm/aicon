from types import SimpleNamespace

import pytest

from src.assistant.llm_planner import CanvasAssistantLLMPlanner


class _FakeAPIKey:
    provider = "openai"
    base_url = "https://example.com/v1"

    def get_api_key(self):
        return "secret"


class _FakeAPIKeyService:
    async def get_api_key_by_id(self, key_id: str, user_id: str):
        return _FakeAPIKey()


class _FakeProvider:
    def __init__(self) -> None:
        self.calls = []

    async def completions(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"mode":"conversation","reply":"我看到当前画布里有一个文本节点《开场》。","target_item_ids":["item-1"]}'
                    )
                )
            ]
        )


class _FakeProviderFactory:
    def __init__(self, provider):
        self.provider = provider

    def create(self, **kwargs):
        return self.provider


@pytest.mark.asyncio
async def test_llm_planner_uses_response_format_and_examples() -> None:
    provider = _FakeProvider()
    planner = CanvasAssistantLLMPlanner(
        db_session=None,
        api_key_service=_FakeAPIKeyService(),
        provider_factory=_FakeProviderFactory(provider),
    )

    result = await planner(
        {
            "user_id": "user-1",
            "api_key_id": "key-1",
            "chat_model_id": "gpt-4.1-mini",
            "message": "这个画布接下来做什么？",
            "selected_item_ids": [],
            "snapshot": {
                "document": {"id": "doc-1", "title": "测试画布"},
                "items": [{"id": "item-1", "item_type": "text", "title": "开场", "content": {"text": "雨夜"}}],
                "connections": [],
                "selected_items": [],
            },
            "conversation": [{"role": "user", "content": "你好"}],
        }
    )

    assert result["mode"] == "conversation"
    assert provider.calls[0]["response_format"] == {"type": "json_object"}
    assert "示例 1" in provider.calls[0]["messages"][0]["content"]
