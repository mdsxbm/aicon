"""
AI导演引擎 - 提示词生成服务

提供服务：
- 批量生成图像提示词
- 支持多种LLM提供商（Volcengine、DeepSeek）
- 提示词模板管理
- 风格预设管理

设计原则：
- 使用BaseService统一管理数据库会话
- 异常处理遵循统一策略
- 方法职责单一，保持简洁
"""

from typing import List, Dict, Optional
import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessLogicError
from src.core.logging import get_logger
from src.services.base import BaseService

logger = get_logger(__name__)


class PromptService(BaseService):
    """
    提示词生成服务
    
    负责调用LLM将小说文本转换为绘画提示词。
    支持多种LLM提供商和风格预设。
    """
    
    # API端点配置
    VOLCENGINE_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
    
    # 风格预设模板
    STYLE_TEMPLATES = {
        "cinematic": "Cinematic lighting, 8k resolution, photorealistic, movie still, detailed texture, dramatic atmosphere.",
        "anime": "Anime style, Makoto Shinkai style, vibrant colors, detailed background, high quality.",
        "illustration": "Digital illustration, artstation, concept art, fantasy style, detailed.",
        "ink": "Chinese ink painting style, watercolor, traditional art, artistic, abstract."
    }
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化提示词生成服务
        
        Args:
            db_session: 可选的数据库会话
        """
        super().__init__(db_session)
        logger.debug(f"PromptService 初始化完成")

    async def generate_prompts_batch(
        self, 
        sentences: List[str], 
        api_key: str, 
        provider: str = "volcengine",
        model: Optional[str] = None,
        style: str = "cinematic"
    ) -> List[Dict[str, str]]:
        """
        批量生成提示词
        
        调用LLM将小说句子转换为英文绘画提示词。
        
        Args:
            sentences: 句子文本列表
            api_key: API密钥
            provider: 供应商 (volcengine/deepseek)
            model: 模型名称，可选
            style: 风格预设，默认cinematic
            
        Returns:
            List[Dict]: 包含 prompt 字段的字典列表
            
        Raises:
            BusinessLogicError: 当API调用失败或参数无效时
        """
        if not sentences:
            logger.warning("句子列表为空，返回空结果")
            return []
            
        if not api_key:
            raise BusinessLogicError("API密钥不能为空")
            
        # 构建系统提示词
        system_prompt = self._build_system_prompt(style)
        
        # 构建用户输入
        user_content = "请为以下小说句子生成英文绘画提示词(Stable Diffusion格式)：\n\n"
        for i, text in enumerate(sentences):
            user_content += f"{i+1}. {text}\n"
            
        # 调用API
        try:
            if provider == "volcengine":
                response_text = await self._call_volcengine(api_key, model, system_prompt, user_content)
            elif provider == "deepseek":
                response_text = await self._call_deepseek(api_key, model, system_prompt, user_content)
            else:
                raise BusinessLogicError(f"不支持的供应商: {provider}")
                
            # 解析结果
            prompts = self._parse_response(response_text, len(sentences))
            
            logger.info(f"成功生成 {len(prompts)} 个提示词，供应商: {provider}")
            return prompts
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP请求失败: {e}")
            raise BusinessLogicError(f"调用LLM服务失败: {str(e)}")
        except Exception as e:
            logger.error(f"生成提示词失败: {e}")
            raise BusinessLogicError(f"生成提示词失败: {str(e)}")

    def _build_system_prompt(self, style: str) -> str:
        """
        构建系统提示词
        
        Args:
            style: 风格预设名称
            
        Returns:
            str: 完整的系统提示词
        """
        base_prompt = """你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的英文Stable Diffusion提示词。

请遵循以下规则：
1. 输出格式必须是纯JSON数组，不要包含markdown标记或其他文字。
2. 数组中每个元素是一个字符串，对应输入的每一句话。
3. 提示词结构：(Subject description), (Action/Pose), (Environment/Background), (Lighting/Atmosphere), (Style modifiers), (Quality tags)
4. 翻译要准确传达原文的意境、情感和视觉要素。
5. 如果句子是心理描写或无具体画面，请生成符合上下文氛围的意象画面。

"""
        style_suffix = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES["cinematic"])
        return base_prompt + f"风格要求：{style_suffix}"

    async def _call_volcengine(
        self, 
        api_key: str, 
        model: Optional[str], 
        system_prompt: str, 
        user_content: str
    ) -> str:
        """
        调用火山引擎API
        
        Args:
            api_key: API密钥
            model: 模型名称
            system_prompt: 系统提示词
            user_content: 用户输入
            
        Returns:
            str: LLM响应文本
            
        Raises:
            httpx.HTTPError: 当HTTP请求失败时
        """
        # 默认模型
        if not model:
            model = "ep-20240604063038-s2k8p"  # 示例Endpoint ID
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.VOLCENGINE_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']

    async def _call_deepseek(
        self, 
        api_key: str, 
        model: Optional[str], 
        system_prompt: str, 
        user_content: str
    ) -> str:
        """
        调用DeepSeek API
        
        Args:
            api_key: API密钥
            model: 模型名称
            system_prompt: 系统提示词
            user_content: 用户输入
            
        Returns:
            str: LLM响应文本
            
        Raises:
            httpx.HTTPError: 当HTTP请求失败时
        """
        if not model:
            model = "deepseek-chat"
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.DEEPSEEK_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']

    def _parse_response(self, content: str, expected_count: int) -> List[Dict[str, str]]:
        """
        解析LLM响应
        
        Args:
            content: LLM返回的文本
            expected_count: 期望的提示词数量
            
        Returns:
            List[Dict]: 解析后的提示词列表
        """
        try:
            # 尝试清理可能的markdown标记
            clean_content = content.replace("```json", "").replace("```", "").strip()
            prompts_list = json.loads(clean_content)
            
            if not isinstance(prompts_list, list):
                raise ValueError("响应不是列表格式")
                
            # 补齐或截断
            results = []
            for i in range(expected_count):
                if i < len(prompts_list):
                    results.append({"prompt": str(prompts_list[i])})
                else:
                    results.append({"prompt": "Failed to generate prompt."})
                    logger.warning(f"提示词数量不足，第 {i+1} 个使用默认值")
                    
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}, 内容: {content[:200]}")
            # 降级处理：返回错误提示
            return [{"prompt": "Error parsing AI response."} for _ in range(expected_count)]
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return [{"prompt": "Error parsing AI response."} for _ in range(expected_count)]


__all__ = ["PromptService"]
