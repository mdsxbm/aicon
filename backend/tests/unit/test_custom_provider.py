import pytest
from unittest.mock import AsyncMock, patch

from src.services.provider.custom_provider import CustomProvider


class TestCustomProvider:
    @pytest.mark.asyncio
    async def test_generate_image_maps_aspect_ratio_for_gemini_models(self):
        provider = CustomProvider(api_key="test-key", base_url="https://api.aiconapi.me/v1")

        with patch.object(
            provider,
            "generate_image_gemini",
            AsyncMock(return_value={"candidates": []}),
        ) as generate_image_gemini, patch.object(
            provider,
            "_wrap_gemini_response",
            return_value={"data": []},
        ):
            await provider.generate_image(
                prompt="两人武器对峙",
                model="gemini-3.1-flash-image-preview",
                aspect_ratio="9:16",
                reference_images=["uploads/reference.jpg"],
            )

        generate_image_gemini.assert_awaited_once_with(
            "两人武器对峙",
            "gemini-3.1-flash-image-preview",
            aspectRatio="9:16",
            reference_images=["uploads/reference.jpg"],
        )
