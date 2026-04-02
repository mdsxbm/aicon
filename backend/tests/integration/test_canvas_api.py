import pytest
from unittest.mock import AsyncMock, Mock, patch

pytestmark = pytest.mark.integration


class TestCanvasDocumentApi:
    @pytest.mark.asyncio
    async def test_canvas_document_crud_and_graph_roundtrip(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "My Canvas"},
        )

        assert create_response.status_code == 201
        created = create_response.json()
        assert created["title"] == "My Canvas"
        canvas_id = created["id"]

        list_response = await client.get("/api/v1/canvas-documents", headers=auth_headers)
        assert list_response.status_code == 200
        listed = list_response.json()
        assert listed["total"] == 1
        assert listed["documents"][0]["id"] == canvas_id

        graph_payload = {
            "items": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "item_type": "text",
                    "title": "Script Node",
                    "position_x": 120,
                    "position_y": 180,
                    "width": 360,
                    "height": 220,
                    "z_index": 1,
                    "content": {"text": "", "prompt": "write an opening scene"},
                    "generation_config": {},
                }
            ],
            "connections": [],
        }

        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json=graph_payload,
        )
        assert save_graph_response.status_code == 200

        get_graph_response = await client.get(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
        )
        assert get_graph_response.status_code == 200
        graph = get_graph_response.json()
        assert graph["document"]["id"] == canvas_id
        assert len(graph["items"]) == 1
        assert graph["items"][0]["title"] == "Script Node"
        assert graph["items"][0]["content"]["prompt"] == "write an opening scene"

    @pytest.mark.asyncio
    async def test_generate_text_creates_pending_generation_record(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Generator Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        item_id = "22222222-2222-2222-2222-222222222222"
        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "id": item_id,
                        "item_type": "text",
                        "title": "Text Generator",
                        "position_x": 0,
                        "position_y": 0,
                        "width": 360,
                        "height": 220,
                        "z_index": 1,
                        "content": {"text": "", "prompt": "Generate a suspenseful intro"},
                        "generation_config": {
                            "api_key_id": "33333333-3333-3333-3333-333333333333",
                            "model": "deepseek-chat",
                        },
                    }
                ],
                "connections": [],
            },
        )
        assert save_graph_response.status_code == 200

        with (
            patch("src.api.v1.canvas.dispatch_canvas_text_generation", return_value="task-text-1"),
        ):
            generate_response = await client.post(
                f"/api/v1/canvas-items/{item_id}/generate-text",
                headers=auth_headers,
                json={},
            )

        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["status"] == "pending"
        assert generated["message"] == "文本生成任务已提交"
        assert generated["generation"]["status"] == "pending"
        assert generated["generation"]["result_payload"]["task_id"] == "task-text-1"
        assert generated["item"]["content"]["text"] == ""
        assert generated["item"]["last_run_status"] == "pending"

        history_response = await client.get(
            f"/api/v1/canvas-items/{item_id}/generations",
            headers=auth_headers,
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert history["total"] == 1
        assert history["generations"][0]["generation_type"] == "text"
        assert history["generations"][0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_generate_image_creates_pending_generation_record(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Image Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        item_id = "44444444-4444-4444-4444-444444444444"
        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "id": item_id,
                        "item_type": "image",
                        "title": "Image Generator",
                        "position_x": 0,
                        "position_y": 0,
                        "width": 360,
                        "height": 220,
                        "z_index": 1,
                        "content": {"prompt": "A bright white studio desk"},
                        "generation_config": {
                            "api_key_id": "33333333-3333-3333-3333-333333333333",
                            "model": "gpt-image-1",
                        },
                    }
                ],
                "connections": [],
            },
        )
        assert save_graph_response.status_code == 200

        with patch("src.api.v1.canvas.dispatch_canvas_image_generation", return_value="task-image-1"):
            generate_response = await client.post(
                f"/api/v1/canvas-items/{item_id}/generate-image",
                headers=auth_headers,
                json={},
            )

        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["status"] == "pending"
        assert generated["message"] == "图片生成任务已提交"
        assert generated["generation"]["status"] == "pending"
        assert generated["generation"]["result_payload"]["task_id"] == "task-image-1"
        assert generated["item"]["last_run_status"] == "pending"

    @pytest.mark.asyncio
    async def test_generate_video_creates_pending_generation_record(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Video Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        item_id = "55555555-5555-5555-5555-555555555555"
        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "id": item_id,
                        "item_type": "video",
                        "title": "Video Generator",
                        "position_x": 0,
                        "position_y": 0,
                        "width": 360,
                        "height": 220,
                        "z_index": 1,
                        "content": {"prompt": "A slow cinematic push-in over a clean desk"},
                        "generation_config": {
                            "api_key_id": "33333333-3333-3333-3333-333333333333",
                            "model": "veo_3_1-fast",
                        },
                    }
                ],
                "connections": [],
            },
        )
        assert save_graph_response.status_code == 200

        with patch("src.api.v1.canvas.dispatch_canvas_video_generation", return_value="task-video-1"):
            generate_response = await client.post(
                f"/api/v1/canvas-items/{item_id}/generate-video",
                headers=auth_headers,
                json={},
            )

        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["status"] == "pending"
        assert generated["message"] == "视频生成任务已提交"
        assert generated["generation"]["status"] == "pending"
        assert generated["generation"]["result_payload"]["task_id"] == "task-video-1"
        assert generated["item"]["last_run_status"] == "pending"

    @pytest.mark.asyncio
    async def test_generate_text_uses_prompt_tokens_and_resolved_mentions(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Structured Text Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        item_id = "66666666-6666-6666-6666-666666666666"
        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "id": item_id,
                        "item_type": "text",
                        "title": "Narration",
                        "position_x": 0,
                        "position_y": 0,
                        "width": 360,
                        "height": 220,
                        "z_index": 1,
                        "content": {"text": "", "prompt": "fallback prompt"},
                        "generation_config": {
                            "api_key_id": "33333333-3333-3333-3333-333333333333",
                            "model": "deepseek-chat",
                        },
                    }
                ],
                "connections": [],
            },
        )
        assert save_graph_response.status_code == 200

        with patch("src.api.v1.canvas.dispatch_canvas_text_generation", return_value="task-text-structured"):
            generate_response = await client.post(
                f"/api/v1/canvas-items/{item_id}/generate-text",
                headers=auth_headers,
                json={
                    "prompt_plain_text": "总结 @角色设定",
                    "prompt_tokens": [
                        {"type": "text", "text": "总结 "},
                        {
                            "type": "mention",
                            "mentionId": "mention-text-1",
                            "nodeId": "text-ref-1",
                            "nodeType": "text",
                            "nodeTitleSnapshot": "角色设定",
                        },
                    ],
                    "resolved_mentions": [
                        {
                            "mentionId": "mention-text-1",
                            "nodeId": "text-ref-1",
                            "nodeType": "text",
                            "nodeTitle": "角色设定",
                            "status": "resolved",
                            "resolvedContent": {
                                "text": "<p>主角是一名摄影师</p><p>沉默、克制。</p>",
                            },
                        }
                    ],
                },
            )

        assert generate_response.status_code == 200
        generated = generate_response.json()
        request_payload = generated["generation"]["request_payload"]
        assert request_payload["prompt"] == "总结 主角是一名摄影师\n\n沉默、克制。"
        assert request_payload["prompt_plain_text"] == "总结 @角色设定"
        assert request_payload["prompt_tokens"][1]["nodeId"] == "text-ref-1"
        assert request_payload["resolved_mentions"][0]["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_generate_video_builds_reference_images_from_prompt_mentions(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Structured Video Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        item_id = "77777777-7777-7777-7777-777777777777"
        save_graph_response = await client.put(
            f"/api/v1/canvas-documents/{canvas_id}/graph",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "id": item_id,
                        "item_type": "video",
                        "title": "Video Generator",
                        "position_x": 0,
                        "position_y": 0,
                        "width": 360,
                        "height": 220,
                        "z_index": 1,
                        "content": {"prompt": "fallback video prompt"},
                        "generation_config": {
                            "api_key_id": "33333333-3333-3333-3333-333333333333",
                            "model": "veo_3_1-fast",
                        },
                    }
                ],
                "connections": [],
            },
        )
        assert save_graph_response.status_code == 200

        with patch("src.api.v1.canvas.dispatch_canvas_video_generation", return_value="task-video-structured"):
            generate_response = await client.post(
                f"/api/v1/canvas-items/{item_id}/generate-video",
                headers=auth_headers,
                json={
                    "prompt_plain_text": "让镜头围绕 @参考图 缓慢推进，并体现 @文案",
                    "prompt_tokens": [
                        {"type": "text", "text": "让镜头围绕 "},
                        {
                            "type": "mention",
                            "mentionId": "mention-image-1",
                            "nodeId": "image-ref-1",
                            "nodeType": "image",
                            "nodeTitleSnapshot": "参考图",
                        },
                        {"type": "text", "text": " 缓慢推进，并体现 "},
                        {
                            "type": "mention",
                            "mentionId": "mention-text-1",
                            "nodeId": "text-ref-1",
                            "nodeType": "text",
                            "nodeTitleSnapshot": "文案",
                        },
                    ],
                    "resolved_mentions": [
                        {
                            "mentionId": "mention-image-1",
                            "nodeId": "image-ref-1",
                            "nodeType": "image",
                            "nodeTitle": "参考图",
                            "status": "resolved",
                            "resolvedContent": {
                                "object_key": "uploads/reference-1.png",
                                "url": "https://example.com/reference-1.png",
                            },
                        },
                        {
                            "mentionId": "mention-text-1",
                            "nodeId": "text-ref-1",
                            "nodeType": "text",
                            "nodeTitle": "文案",
                            "status": "resolved",
                            "resolvedContent": {"text": "夜色安静，镜头慢慢靠近桌面。"},
                        },
                    ],
                },
            )

        assert generate_response.status_code == 200
        generated = generate_response.json()
        request_payload = generated["generation"]["request_payload"]
        assert request_payload["prompt"] == "让镜头围绕 缓慢推进，并体现 夜色安静，镜头慢慢靠近桌面。"
        assert request_payload["options"]["reference_image_urls"] == ["uploads/reference-1.png"]
        assert request_payload["options"]["reference_text_ids"] == ["text-ref-1"]

    @pytest.mark.asyncio
    async def test_lite_snapshot_and_item_crud_flow(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Workbench Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        create_item_response = await client.post(
            f"/api/v1/canvas-documents/{canvas_id}/items",
            headers=auth_headers,
            json={
                "item_type": "text",
                "title": "Opening Beat",
                "position_x": 80,
                "position_y": 120,
                "width": 360,
                "height": 220,
                "z_index": 1,
                "content": {"text": "Opening text", "prompt": "Write a better intro"},
                "generation_config": {"model": "deepseek-chat"},
            },
        )
        assert create_item_response.status_code == 201
        item = create_item_response.json()
        item_id = item["id"]
        assert item["title"] == "Opening Beat"

        lite_response = await client.get(
            f"/api/v1/canvas-documents/{canvas_id}",
            headers=auth_headers,
            params={"mode": "lite"},
        )
        assert lite_response.status_code == 200
        lite_snapshot = lite_response.json()
        assert lite_snapshot["document"]["id"] == canvas_id
        assert len(lite_snapshot["items"]) == 1
        assert lite_snapshot["items"][0]["id"] == item_id
        assert "text_preview" in lite_snapshot["items"][0]["content"]
        assert "text" not in lite_snapshot["items"][0]["content"]

        detail_response = await client.get(
            f"/api/v1/canvas-documents/{canvas_id}/items/{item_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == item_id
        assert detail["content"]["text"] == "Opening text"

        patch_response = await client.patch(
            f"/api/v1/canvas-documents/{canvas_id}/items/{item_id}",
            headers=auth_headers,
            json={
                "title": "Opening Beat v2",
                "content": {"text": "Updated opening text"},
            },
        )
        assert patch_response.status_code == 200
        patched = patch_response.json()
        assert patched["title"] == "Opening Beat v2"
        assert patched["content"]["text"] == "Updated opening text"

        delete_response = await client.delete(
            f"/api/v1/canvas-documents/{canvas_id}/items/{item_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        after_delete_response = await client.get(
            f"/api/v1/canvas-documents/{canvas_id}",
            headers=auth_headers,
            params={"mode": "lite"},
        )
        assert after_delete_response.status_code == 200
        assert after_delete_response.json()["items"] == []

    @pytest.mark.asyncio
    async def test_connection_crud_and_preview_patch_flow(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/canvas-documents",
            headers=auth_headers,
            json={"title": "Connection Canvas"},
        )
        assert create_response.status_code == 201
        canvas_id = create_response.json()["id"]

        first_item_response = await client.post(
            f"/api/v1/canvas-documents/{canvas_id}/items",
            headers=auth_headers,
            json={
                "item_type": "image",
                "title": "Reference Image",
                "position_x": 60,
                "position_y": 80,
                "width": 340,
                "height": 280,
                "z_index": 1,
                "content": {
                    "prompt": "White studio desk",
                    "result_image_url": "https://example.com/reference.png",
                },
                "generation_config": {"model": "gpt-image-1"},
            },
        )
        assert first_item_response.status_code == 201
        first_item_id = first_item_response.json()["id"]

        second_item_response = await client.post(
            f"/api/v1/canvas-documents/{canvas_id}/items",
            headers=auth_headers,
            json={
                "item_type": "video",
                "title": "Downstream Video",
                "position_x": 480,
                "position_y": 80,
                "width": 360,
                "height": 300,
                "z_index": 2,
                "content": {
                    "prompt": "Slow push in",
                    "result_video_url": "https://example.com/clip.mp4",
                },
                "generation_config": {"model": "veo_3_1-fast"},
            },
        )
        assert second_item_response.status_code == 201
        second_item_id = second_item_response.json()["id"]

        connection_response = await client.post(
            f"/api/v1/canvas-documents/{canvas_id}/connections",
            headers=auth_headers,
            json={
                "source_item_id": first_item_id,
                "target_item_id": second_item_id,
                "source_handle": "right",
                "target_handle": "left",
            },
        )
        assert connection_response.status_code == 201
        connection = connection_response.json()
        assert connection["source_item_id"] == first_item_id
        assert connection["target_item_id"] == second_item_id

        preview_response = await client.post(
            f"/api/v1/canvas-documents/{canvas_id}/items/previews",
            headers=auth_headers,
            json={"item_ids": [first_item_id, second_item_id]},
        )
        assert preview_response.status_code == 200
        preview_payload = preview_response.json()
        assert len(preview_payload["items"]) == 2
        assert {item["id"] for item in preview_payload["items"]} == {first_item_id, second_item_id}

        delete_response = await client.delete(
            f"/api/v1/canvas-documents/{canvas_id}/connections/{connection['id']}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        snapshot_response = await client.get(
            f"/api/v1/canvas-documents/{canvas_id}",
            headers=auth_headers,
            params={"mode": "lite"},
        )
        assert snapshot_response.status_code == 200
        assert snapshot_response.json()["connections"] == []
