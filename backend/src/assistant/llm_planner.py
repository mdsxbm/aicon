from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.assistant.context_builder import CanvasAgentContextBuilder
from src.assistant.prompt_builder import CanvasAgentPromptBuilder
from src.services.api_key import APIKeyService
from src.services.provider.factory import ProviderFactory

ALLOWED_TOOL_NAMES = {
    "canvas.create_items",
    "canvas.update_items",
    "canvas.delete_items",
    "canvas.create_connections",
    "canvas.delete_connections",
    "generation.submit",
}


def _extract_message_content(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content.strip()
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            content = ((choices[0] or {}).get("message") or {}).get("content")
            if isinstance(content, str):
                return content.strip()
    return ""


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("planner response does not contain json object")
    return json.loads(text[start : end + 1])


class CanvasAssistantLLMPlanner:
    def __init__(
        self,
        db_session: AsyncSession,
        api_key_service: APIKeyService | None = None,
        context_builder: CanvasAgentContextBuilder | None = None,
        prompt_builder: CanvasAgentPromptBuilder | None = None,
        provider_factory: Any = ProviderFactory,
    ) -> None:
        self.db_session = db_session
        self.api_key_service = api_key_service or APIKeyService(db_session)
        self.context_builder = context_builder or CanvasAgentContextBuilder()
        self.prompt_builder = prompt_builder or CanvasAgentPromptBuilder()
        self.provider_factory = provider_factory

    async def __call__(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        api_key_id = str(payload.get("api_key_id") or "").strip()
        chat_model_id = str(payload.get("chat_model_id") or "").strip()
        user_id = str(payload.get("user_id") or "").strip()
        if not (api_key_id and chat_model_id and user_id):
            return None

        api_key = await self.api_key_service.get_api_key_by_id(api_key_id, user_id)
        provider = self.provider_factory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url,
        )
        context = self.context_builder.build(payload.get("snapshot") or {}, payload.get("selected_item_ids") or [])
        messages = self.prompt_builder.build_messages(payload, context)
        completion_kwargs = {
            "model": chat_model_id,
            "messages": messages,
            "temperature": 0.2,
        }
        response_format = self._build_response_format(str(api_key.provider or "").strip().lower(), chat_model_id)
        if response_format is not None:
            completion_kwargs["response_format"] = response_format
        response = await provider.completions(**completion_kwargs)
        content = _extract_message_content(response)
        if not content:
            raise ValueError("planner llm returned empty content")
        parsed = _extract_json_payload(content)
        return self._normalize_plan(parsed)

    def _normalize_plan(self, parsed: dict[str, Any]) -> dict[str, Any]:
        mode = str(parsed.get("mode") or "conversation").strip().lower()
        reply = str(parsed.get("reply") or "").strip()
        target_item_ids = [
            str(item_id).strip()
            for item_id in parsed.get("target_item_ids") or []
            if str(item_id).strip()
        ]
        operations = []
        for operation in parsed.get("operations") or []:
            if not isinstance(operation, dict):
                continue
            tool_name = str(operation.get("tool_name") or "").strip()
            if tool_name not in ALLOWED_TOOL_NAMES:
                continue
            operations.append({"tool_name": tool_name, "args": dict(operation.get("args") or {})})
        if mode == "interrupt" and operations:
            return {
                "mode": "interrupt",
                "reply": reply,
                "target_item_ids": target_item_ids,
                "needs_interrupt": bool(parsed.get("needs_interrupt", True)),
                "operations": operations,
            }
        return {
            "mode": "conversation",
            "reply": reply,
            "target_item_ids": target_item_ids,
        }

    def _build_response_format(self, provider: str, model: str) -> dict[str, Any] | None:
        if not provider:
            return None
        openai_compatible = {"openai", "deepseek", "custom", "vectorengine", "siliconflow"}
        if provider in openai_compatible:
            return {"type": "json_object"}
        if provider == "volcengine" and model:
            return {"type": "json_object"}
        return None
