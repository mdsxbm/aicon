"""
文本处理工具函数 - 统一的文本处理模块
提供段落分割、句子分割、文本分析等功能
严格按照 data-model.md 规范实现，为章节识别和解析提供支持
"""

import re
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter

from src.core.logging import get_logger

logger = get_logger(__name__)


class ParagraphSplitter:
    """段落分割器，委托给 RecursiveCharacterTextSplitter"""

    def __init__(self, chunk_size: int = 500):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)

    def split_into_paragraphs(self, text: str) -> List[str]:
        if not text:
            return []
        return self.splitter.split_text(text)


class SentenceSplitter(TextSplitter):
    """长句切分器，支持中英文分句、长度控制和清理"""

    def __init__(
            self,
            target_min_chars: int = 100,
            target_max_chars: int = 300,
            strict_mode: bool = True
    ):
        super().__init__()
        self.target_min_chars = target_min_chars
        self.target_max_chars = target_max_chars
        self.strict_mode = strict_mode

        # 中英文标点分句
        self._split_pattern = re.compile(r"(?<=[。！？!?])\s*|(?<=[\.\?\!])\s+")

        # 清理句子开头、结尾、空格、全角空格、特殊符号
        self._clean_patterns = [
            re.compile(r'^[\s……·—–"\'《》【】()（）\[\]{}，,、;:;:\t]+'),  # 开头多余符号
            re.compile(r'[，,、;:;:\s…—–《》【】()（）\[\]{}]+(?=[。！？!?。])|[，,、;:;:\s…—–《》【】()（）\[\]{}]+$'),  # 结尾多余符号
            re.compile(r'^["\'“”‘’]+|["\'“”‘’]+$'),  # 引号
            re.compile(r'^《+|》+$'),  # 书名号
            re.compile(r'[\u3000]+'),  # 全角空格
            re.compile(r'[\t\u200b\ufeff]+'),  # 制表符和特殊空白
        ]

    def _clean_sentence(self, sentence: str) -> str:
        if not sentence:
            return ""

        cleaned = sentence.strip()

        # 1. 去掉开头和结尾的多余符号
        cleaned = re.sub(r'^[\s……·—–\-_"\'《》【】()（）\[\]{}，,、;:;:\t]+', '', cleaned)
        cleaned = re.sub(r'[\s……·—–\-_"\'《》【】()（）\[\]{}，,、;:;:\t]+$', '', cleaned)

        # 2. 去掉重复符号（连续2次及以上的）
        cleaned = re.sub(r'(…{2,}|—{2,}|-{2,})', lambda m: m.group(0)[0], cleaned)

        # 3. 去掉全角空格、制表符、零宽字符
        cleaned = re.sub(r'[\u3000\t\u200b\ufeff]+', '', cleaned)

        # 4. 过滤无意义或过短片段
        if not cleaned or all(c in '，,、;:;:；：！？!?.…—·"\'《》【】()（）\[\]{}' or c.isspace() for c in cleaned):
            return ""
        if len(cleaned) < 3 and not any('\u4e00' <= c <= '\u9fff' for c in cleaned):
            return ""

        return cleaned

    def base_split(self, text: str) -> List[str]:
        """按中英文标点基础分句并清理"""
        parts = re.split(self._split_pattern, text)
        sentences = [self._clean_sentence(p.strip()) for p in parts]
        return [s for s in sentences if s]

    def merge_sentences(self, sentences: List[str]) -> List[str]:
        """合并短句生成长句，严格控制长度在 target_min_chars ~ target_max_chars"""
        merged = []
        buffer = ""

        for s in sentences:
            if not s:
                continue
            candidate = buffer + s if buffer else s

            if len(candidate) > self.target_max_chars:
                # 如果 buffer 不为空，先加入 merged
                if buffer:
                    merged.append(buffer)
                # 超长句子强制切分
                while len(s) > self.target_max_chars:
                    merged.append(s[:self.target_max_chars])
                    s = s[self.target_max_chars:]
                buffer = s
            else:
                buffer = candidate

        if buffer:
            merged.append(buffer)

        if self.strict_mode:
            # 保证每段长度 >= target_min_chars
            final = []
            temp = ""
            for m in merged:
                if len(temp) + len(m) < self.target_min_chars:
                    temp += m
                else:
                    if temp:
                        final.append(temp)
                        temp = ""
                    final.append(m)
            if temp:
                final.append(temp)
            return final

        return merged

    def split_text(self, text: str) -> List[str]:
        sentences = self.base_split(text)
        return self.merge_sentences(sentences)


# 全局实例
paragraph_splitter = ParagraphSplitter()
sentence_splitter = SentenceSplitter()

__all__ = [
    'ParagraphSplitter',
    'SentenceSplitter',
    'paragraph_splitter',
    'sentence_splitter'
]
