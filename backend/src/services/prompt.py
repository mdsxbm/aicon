"""
AI导演引擎 - 提示词生成服务

提供服务：
- 批量生成图像提示词
- 支持多种LLM提供商（Volcengine、DeepSeek）
- 提示词模板管理
- 风格预设管理

设计原则：
- 异常处理遵循统一策略
- 方法职责单一，保持简洁
"""
import asyncio
import json
from typing import List, Dict

from src.core.exceptions import NotFoundError
from src.core.logging import get_logger
from src.models import Sentence, APIKey, ChapterStatus, SentenceStatus
from src.services import ChapterService
from src.services.api_key import APIKeyService
from src.services.base import SessionManagedService
from src.services.provider.base import BaseLLMProvider
from src.services.provider.factory import ProviderFactory

logger = get_logger(__name__)


# 定义单个句子的处理函数
async def process_sentence(sentence: Sentence, api_key: APIKey, llm_provider: BaseLLMProvider, system_prompt: str):
    """
        处理单个句子，生成提示词

        Args:
            sentence: 句子对象
            api_key: API密钥对象
            llm_provider: LLM提供商实例
            system_prompt: 系统提示词

        Returns:
            Tuple[Sentence, str]: 包含句子对象和生成的提示词

    """
    model_name = "doubao-pro" if api_key.provider == "volcengine" else "deepseek-chat"
    logger.info(
        f"开始处理句子: sentence_id={sentence.id}, 内容长度={len(sentence.content)}字符, 模型={model_name}")

    # 调用LLM
    try:
        logger.debug(f"调用LLM生成提示词: provider={api_key.provider}, model={model_name}")
        response = await llm_provider.completions(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence.content}
            ],
        )

        prompt = response.choices[0].message.content.strip()
        logger.info(f"句子处理完成: sentence_id={sentence.id}, 生成提示词长度={len(prompt)}字符")
        logger.debug(f"生成的提示词: {prompt}")

        # 返回句子和生成的提示词
        return sentence, prompt
    except Exception as e:
        logger.error(f"处理句子失败: sentence_id={sentence.id}, 错误={str(e)}")
        raise


class PromptService(SessionManagedService):
    """
    提示词生成服务
    
    负责调用LLM将小说文本转换为绘画提示词。
    支持多种LLM提供商和风格预设。
    """

    def __init__(self):
        super().__init__()

    # 风格预设模板
    STYLE_TEMPLATES = {
        "cinematic": "Cinematic lighting, 8k resolution, photorealistic, movie still, detailed texture, dramatic atmosphere.",
        "anime": "Anime style, Makoto Shinkai style, vibrant colors, detailed background, high quality.",
        "illustration": "Digital illustration, artstation, concept art, fantasy style, detailed.",
        "ink": "Chinese ink painting style, watercolor, traditional art, artistic, abstract."
    }

    async def generate_prompts_batch(
            self,
            chapter_id: str,
            api_key_id: str,
            style: str = "cinematic"
    ) -> None:
        """
        批量生成提示词
        
        调用LLM将小说句子转换为英文绘画提示词。
        
        Args:
            chapter_id: 章节ID
            api_key_id: API密钥ID
            style: 风格预设名称
            
        Returns:
            List[Dict]: 包含 prompt 字段的字典列表
            
        Raises:
            BusinessLogicError: 当API调用失败或参数无效时
        """
        # 确保使用正确的上下文管理
        async with self:
            # 1.查找出章节
            chapter_server = ChapterService(self.db_session)
            sentences = await chapter_server.get_sentences(chapter_id, SentenceStatus.PENDING)
            if len(sentences) == 0:
                raise NotFoundError("未处理句子数据为空", resource_id=chapter_id, resource_type='chapter')

            # 2.查询获取api_key
            api_key_service = APIKeyService(self.db_session)

            # 获取项目owner_id作为用户ID
            chapter = sentences[0].paragraph.chapter
            user_id = chapter.project.owner_id

            api_key = await api_key_service.get_api_key_by_id(api_key_id, user_id)
            if not api_key:
                raise NotFoundError("未找到API密钥", resource_id=api_key_id, resource_type='api_key')

            # 3.创建LLM提供商实例
            logger.info(f"创建LLM提供商实例: provider={api_key.provider}, max_concurrency=5")
            llm_provider = ProviderFactory.create(provider=api_key.provider, api_key=api_key.get_api_key(),
                                                max_concurrency=5)

            # 4.构建系统提示词（修改为处理单个句子）
            base_prompt = """你是一个专业的AI绘画提示词生成专家(AI Director)。
            你的任务是将中文小说句子转换为高质量的英文Stable Diffusion提示词。

            请遵循以下规则：
            1. 输出格式必须是纯文本，不要包含markdown标记或其他文字。
            2. 直接输出英文提示词，不要有任何前缀或后缀。
            3. 提示词结构：(Subject description), (Action/Pose), (Environment/Background), (Lighting/Atmosphere), (Style modifiers), (Quality tags)
            4. 翻译要准确传达原文的意境、情感和视觉要素。
            5. 如果句子是心理描写或无具体画面，请生成符合上下文氛围的意象画面。

            """
            style_suffix = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES["cinematic"])
            system_prompt = base_prompt + f"风格要求：{style_suffix}"
            logger.debug(f"构建系统提示词完成，风格: {style}")

            # 5.为每个句子创建并发送LLM请求（并发）
            # 并发处理所有句子
            logger.info(f"开始并发处理所有句子，总数: {len(sentences)}")
            tasks = [process_sentence(sentence, api_key, llm_provider, system_prompt) for sentence in sentences]
            results = await asyncio.gather(*tasks)
            logger.info(f"所有句子处理完成，成功生成 {len(results)} 个提示词")

            # 6.保存结果到数据库
            logger.info("开始更新数据库，保存提示词结果")
            for sentence, prompt in results:
                sentence.image_prompt = prompt
                sentence.status = SentenceStatus.GENERATED_PROMPTS
                sentence.image_style = style
                logger.debug(f"更新句子: sentence_id={sentence.id}, status=completed")

            # 7.更新章节状态为提示词生成完成
            chapter.status = ChapterStatus.GENERATED_PROMPTS.value
            logger.info(f"更新章节状态: chapter_id={chapter.id}, status={chapter.status}")

            # 批量更新
            logger.info("执行数据库批量更新")
            await self.db_session.flush()
            await self.db_session.commit()
            logger.info("数据库更新完成")

            # 7.更新API密钥使用统计
            logger.info(f"更新API密钥使用统计: api_key_id={api_key_id}")
            await api_key_service.update_usage(api_key_id, user_id)
            logger.info("API密钥使用统计更新完成")

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


prompt_service = PromptService()


__all__ = ["PromptService","prompt_service"]

if __name__ == "__main__":
    import asyncio


    async def main():
        # 使用async with上下文管理器来管理会话
        async with PromptService() as prompt_service:
            # 在这里可以调用服务方法进行测试
            chapter_id = '25e644a9-4b24-4e3f-bf16-ed476ebd3ff1'
            api_key_id = '02d73ef2-572f-4ffd-a76e-baca8d279194'
            res = await prompt_service.generate_prompts_batch(chapter_id, api_key_id)


    asyncio.run(main())
