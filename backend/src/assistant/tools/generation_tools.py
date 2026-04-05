from __future__ import annotations

from typing import Any, Awaitable, Callable


DispatchFn = Callable[[str], Any]


class CanvasAssistantGenerationTools:
    def __init__(
        self,
        generation_service: Any | None = None,
        dispatch_text: DispatchFn | None = None,
        dispatch_image: DispatchFn | None = None,
        dispatch_video: DispatchFn | None = None,
    ) -> None:
        self.generation_service = generation_service
        self.dispatch_text = dispatch_text
        self.dispatch_image = dispatch_image
        self.dispatch_video = dispatch_video

    async def submit_generation_tasks(self, user_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        submitted = []
        if self.generation_service is None:
            for request in requests:
                submitted.append(
                    {
                        "item_id": str(request.get("item_id") or "").strip(),
                        "kind": str(request.get("kind") or "").strip(),
                        "status": "submitted",
                    }
                )
            return {"submitted": submitted}

        for request in requests:
            item_id = str(request.get("item_id") or "").strip()
            kind = str(request.get("kind") or "").strip()
            payload = dict(request.get("payload") or {})
            if kind == "text":
                _item, generation = await self.generation_service.prepare_text_generation(item_id, user_id, payload)
                task_id = self.dispatch_text(str(generation.id)) if self.dispatch_text else ""
            elif kind == "video":
                _item, generation = await self.generation_service.prepare_video_generation(item_id, user_id, payload)
                task_id = self.dispatch_video(str(generation.id)) if self.dispatch_video else ""
            else:
                _item, generation = await self.generation_service.prepare_image_generation(item_id, user_id, payload)
                task_id = self.dispatch_image(str(generation.id)) if self.dispatch_image else ""
            _item, generation = await self.generation_service.attach_task(str(generation.id), task_id)
            submitted.append(
                {
                    "item_id": item_id,
                    "kind": kind,
                    "generation_id": str(generation.id),
                    "task_id": task_id,
                    "status": "submitted",
                }
            )
        return {"submitted": submitted}


class CanvasAssistantObservationTools:
    def __init__(self, read_tools: Any | None = None) -> None:
        self.read_tools = read_tools

    async def observe_effects(self, document_id: str, user_id: str, item_ids: list[str]) -> dict[str, Any]:
        if self.read_tools is None:
            return {"items": [], "connections": []}
        snapshot = await self.read_tools.get_canvas_snapshot(document_id, user_id, item_ids=item_ids)
        return {
            "items": list(snapshot.get("selected_items") or []),
            "connections": list(snapshot.get("connections") or []),
        }
