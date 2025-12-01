# src/services/providers/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLMProvider(ABC):
    """
    纯粹 LLM Provider 接口。
    不参杂任何业务、文本处理、拼接逻辑。

    所有 Provider 都必须实现 completions() 方法。
    """

    @abstractmethod
    async def completions(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            **kwargs: Any
    ) -> Any:
        """
        LLM 的 completions 调用（纯粹透传）
        """
        pass

    @abstractmethod
    async def generate_image(
            self,
            prompt: str,
            model: str = None,
            **kwargs: Any
    ) -> Any:
        """
        生成图像的调用（纯粹透传）
        """
        pass

    @abstractmethod
    async def generate_audio(
            self,
            input_text: str,
            voice: str = "alloy",
            model: str = "tts-1",
            **kwargs: Any
    ) -> Any:
        """
        生成音频的调用（纯粹透传）
        """
        pass
