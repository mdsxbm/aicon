from __future__ import annotations

from typing import Any


class CanvasAssistantCanvasReadTools:
    def __init__(self, service: Any | None = None) -> None:
        self.service = service

    async def get_canvas_snapshot(self, document_id: str, user_id: str, item_ids: list[str] | None = None) -> dict[str, Any]:
        if self.service is None:
            return {"document": {"id": document_id}, "items": [], "connections": [], "selected_items": []}
        graph = await self.service.get_graph(document_id, user_id)
        items = [self._serialize_item(item) for item in list(graph.get("items") or [])]
        normalized_ids = {str(item_id).strip() for item_id in item_ids or [] if str(item_id).strip()}
        return {
            "document": self._serialize_document(graph.get("document")),
            "items": items,
            "connections": [self._serialize_connection(connection) for connection in list(graph.get("connections") or [])],
            "selected_items": [item for item in items if str(item.get("id") or "").strip() in normalized_ids],
        }

    def _serialize_document(self, document: Any) -> dict[str, Any]:
        if document is None:
            return {}
        if isinstance(document, dict):
            return dict(document)
        if hasattr(document, "to_dict"):
            return dict(document.to_dict())
        return {"id": getattr(document, "id", ""), "title": getattr(document, "title", "")}

    def _serialize_item(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return {
                "id": item.get("id"),
                "item_type": item.get("item_type"),
                "title": item.get("title", ""),
                "content": dict(item.get("content") or {}),
            }
        base = dict(item.to_dict()) if hasattr(item, "to_dict") else {}
        return {
            "id": base.get("id", getattr(item, "id", "")),
            "item_type": base.get("item_type", getattr(item, "item_type", "")),
            "title": base.get("title", getattr(item, "title", "")),
            "content": dict(base.get("content_json", getattr(item, "content_json", {})) or {}),
        }

    def _serialize_connection(self, connection: Any) -> dict[str, Any]:
        if isinstance(connection, dict):
            return dict(connection)
        if hasattr(connection, "to_dict"):
            return dict(connection.to_dict())
        return {
            "id": getattr(connection, "id", ""),
            "source_item_id": getattr(connection, "source_item_id", ""),
            "target_item_id": getattr(connection, "target_item_id", ""),
            "source_handle": getattr(connection, "source_handle", ""),
            "target_handle": getattr(connection, "target_handle", ""),
        }


class CanvasAssistantCanvasWriteTools:
    def __init__(self, service: Any | None = None) -> None:
        self.service = service

    async def create_items(self, document_id: str, user_id: str, items: list[dict[str, Any]]) -> list[Any]:
        if self.service is None:
            return items
        return [await self.service.create_item(document_id, user_id, item) for item in items]

    async def update_items(self, document_id: str, user_id: str, updates: list[dict[str, Any]]) -> list[Any]:
        if self.service is None:
            return updates
        return [
            await self.service.update_item(document_id, update.get("item_id"), user_id, update.get("patch") or {})
            for update in updates
        ]

    async def delete_items(self, document_id: str, user_id: str, item_ids: list[str]) -> list[str]:
        if self.service is None:
            return item_ids
        for item_id in item_ids:
            await self.service.delete_item(document_id, item_id, user_id)
        return item_ids

    async def create_connections(self, document_id: str, user_id: str, connections: list[dict[str, Any]]) -> list[Any]:
        if self.service is None:
            return connections
        return [await self.service.create_connection(document_id, user_id, connection) for connection in connections]

    async def delete_connections(self, document_id: str, user_id: str, connection_ids: list[str]) -> list[str]:
        if self.service is None:
            return connection_ids
        for connection_id in connection_ids:
            await self.service.delete_connection(document_id, connection_id, user_id)
        return connection_ids
