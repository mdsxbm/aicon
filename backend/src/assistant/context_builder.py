from __future__ import annotations

from typing import Any


def _trim_text(value: Any, limit: int = 240) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


class CanvasAgentContextBuilder:
    def build(self, snapshot: dict[str, Any], selected_item_ids: list[str] | None = None) -> dict[str, Any]:
        document = dict(snapshot.get("document") or {})
        items = list(snapshot.get("items") or [])
        connections = list(snapshot.get("connections") or [])
        selected_items = list(snapshot.get("selected_items") or [])
        selected_ids = {str(item_id).strip() for item_id in selected_item_ids or [] if str(item_id).strip()}

        compact_items = [self._serialize_item(item) for item in items[:12]]
        compact_selected_items = [self._serialize_item(item) for item in selected_items[:6]]
        compact_connections = [self._serialize_connection(connection) for connection in connections[:20]]

        return {
            "document": {
                "id": str(document.get("id") or "").strip(),
                "title": str(document.get("title") or "").strip(),
            },
            "counts": {
                "items": len(items),
                "connections": len(connections),
                "selected_items": len(selected_items or selected_ids),
            },
            "selected_item_ids": list(selected_ids),
            "selected_items": compact_selected_items,
            "items": compact_items,
            "connections": compact_connections,
        }

    def _serialize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        content = dict(item.get("content") or {})
        return {
            "id": str(item.get("id") or "").strip(),
            "item_type": str(item.get("item_type") or "").strip(),
            "title": _trim_text(item.get("title"), 80),
            "content_summary": {
                "text": _trim_text(content.get("text"), 120),
                "prompt": _trim_text(content.get("prompt"), 160),
                "text_preview": _trim_text(content.get("text_preview"), 120),
            },
        }

    def _serialize_connection(self, connection: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(connection.get("id") or "").strip(),
            "source_item_id": str(connection.get("source_item_id") or "").strip(),
            "target_item_id": str(connection.get("target_item_id") or "").strip(),
            "source_handle": str(connection.get("source_handle") or "").strip(),
            "target_handle": str(connection.get("target_handle") or "").strip(),
        }
