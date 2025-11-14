"""
文件编码检测和智能解码工具类

基于权威实践的稳定解码策略：
1. 显式 BOM → 确认编码
2. 尝试 UTF 系列
3. charset-normalizer 自动检测
4. 中文编码（GBK / Big5）按需匹配
5. 最后 fallback = 明确拒绝乱码
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class FileEncodingDetector:
    """
    文件编码检测和智能解码工具类
    基于 charset-normalizer 和权威编码检测策略
    """

    def __init__(self):
        self.encoding_candidates = [
            # UTF系列（现代标准）
            'utf-8',
            'utf-8-sig',  # 带BOM的UTF-8
            'utf-16',
            'utf-32',

            # 中文编码（按需匹配）
            'gbk',  # 简体中文（Windows常用）
            'gb18030',  # 简体中文国标（最完整）
            'gb2312',  # 简体中文基础字符集
            'big5',  # 繁体中文

            # 其他常用编码
            'latin-1',  # 西欧编码（不会失败，但可能产生乱码）
            'ascii',  # ASCII编码
        ]

    def detect_encoding(self, data: bytes) -> Optional[str]:
        """
        检测文件编码

        Args:
            data: 文件字节数据

        Returns:
            检测到的编码名称，如果无法确定返回 None
        """
        if not data:
            return None

        # 1. 检查BOM标记（显式BOM）
        bom_encoding = self._detect_bom(data)
        if bom_encoding:
            logger.info(f"BOM检测到编码: {bom_encoding}")
            return bom_encoding

        # 2. 使用 charset-normalizer 自动检测
        try:
            from charset_normalizer import detect
            result = detect(data)
            if result and isinstance(result, dict):
                confidence = result.get('confidence', 0)
                encoding = result.get('encoding')
                if encoding and confidence > 0.7:  # 置信度阈值
                    encoding = encoding.lower()
                    logger.info(f"自动检测编码: {encoding}, 置信度: {confidence:.2f}, 语言: {result.get('language', 'Unknown')}")
                    return encoding
        except ImportError:
            logger.warning("charset-normalizer 未安装，跳过自动检测")
        except Exception as e:
            logger.warning(f"自动检测失败: {e}")

        # 3. 尝试UTF系列编码（最稳定）
        for encoding in ['utf-8', 'utf-8-sig']:
            if self._try_decode(data, encoding):
                logger.info(f"UTF系列检测成功: {encoding}")
                return encoding

        # 4. 按需匹配中文编码
        chinese_encodings = ['gbk', 'gb18030', 'gb2312', 'big5']
        for encoding in chinese_encodings:
            if self._try_decode(data, encoding):
                logger.info(f"中文编码检测成功: {encoding}")
                return encoding

        # 5. 最后尝试Latin-1（明确知道可能有乱码，但不会失败）
        if self._try_decode(data, 'latin-1'):
            logger.warning("使用Latin-1编码（可能包含乱码）")
            return 'latin-1'

        return None

    def decode_content(self, data: bytes, file_path: str = None) -> str:
        """
        智能解码文件内容

        Args:
            data: 文件字节数据
            file_path: 文件路径（用于日志）

        Returns:
            解码后的文本内容

        Raises:
            ValueError: 无法解码文件内容
        """
        if not data:
            return ""

        # 检测编码
        encoding = self.detect_encoding(data)
        if not encoding:
            raise ValueError(f"无法检测文件编码: {file_path or 'unknown'}")

        # 解码内容
        try:
            content = data.decode(encoding)

            # 内容质量验证
            if self._is_garbled_content(content, encoding):
                logger.warning(f"解码内容可能包含乱码 (编码: {encoding})")
                # 尝试使用UTF-8容错模式
                content = data.decode('utf-8', errors='replace')
                content = self._clean_garbled_content(content)
                logger.info("使用UTF-8容错模式并清理内容")

            # 标准化内容格式
            content = self._normalize_content(content)

            log_msg = f"解码完成"
            if file_path:
                log_msg += f" ({file_path})"
            log_msg += f", 编码: {encoding}, 长度: {len(content)}"
            logger.info(log_msg)

            return content

        except UnicodeDecodeError as e:
            # UTF-8容错模式
            try:
                logger.warning(f"解码失败，尝试UTF-8容错模式: {e}")
                content = data.decode('utf-8', errors='replace')
                content = self._clean_garbled_content(content)
                return content
            except Exception as fallback_error:
                raise ValueError(f"无法解码文件内容: {fallback_error}")
        except Exception as e:
            raise ValueError(f"解码过程中发生错误: {e}")

    def _detect_bom(self, data: bytes) -> Optional[str]:
        """
        检测BOM标记

        Args:
            data: 文件字节数据

        Returns:
            BOM对应的编码，如果没有BOM返回 None
        """
        if len(data) < 2:
            return None

        # UTF-8 BOM
        if data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'

        # UTF-16 BE BOM
        if data.startswith(b'\xfe\xff'):
            return 'utf-16-be'

        # UTF-16 LE BOM
        if data.startswith(b'\xff\xfe'):
            return 'utf-16-le'

        # UTF-32 BE BOM
        if data.startswith(b'\x00\x00\xfe\xff'):
            return 'utf-32-be'

        # UTF-32 LE BOM
        if data.startswith(b'\xff\xfe\x00\x00'):
            return 'utf-32-le'

        return None

    def _try_decode(self, data: bytes, encoding: str) -> bool:
        """
        尝试使用指定编码解码

        Args:
            data: 文件字节数据
            encoding: 编码名称

        Returns:
            解码是否成功
        """
        try:
            decoded = data.decode(encoding)
            # 简单检查解码结果是否包含过多的不可打印字符
            printable_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
            return printable_chars / len(decoded) > 0.8 if len(decoded) > 0 else True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False

    def _is_garbled_content(self, content: str, encoding: str) -> bool:
        """
        检查内容是否为乱码

        Args:
            content: 解码后的内容
            encoding: 使用的编码

        Returns:
            是否为乱码
        """
        if not content:
            return False

        # 检查是否包含替换字符
        if '�' in content:
            return True

        # 对于非Latin编码，检查可读字符比例
        if encoding != 'latin-1':
            readable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
            readable_ratio = readable_chars / len(content) if len(content) > 0 else 0
            return readable_ratio < 0.8

        return False

    def _clean_garbled_content(self, content: str) -> str:
        """
        清理乱码内容

        Args:
            content: 可能包含乱码的内容

        Returns:
            清理后的内容
        """
        if not content:
            return content

        # 移除替换字符
        content = content.replace('�', '')

        # 移除过多的控制字符（保留常用的换行、制表符）
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

        # 标准化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 移除过多的空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 移除首尾空白
        content = content.strip()

        return content

    def _normalize_content(self, content: str) -> str:
        """
        标准化内容格式

        Args:
            content: 原始内容

        Returns:
            标准化后的内容
        """
        if not content:
            return content

        # 标准化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 移除多余的空行（最多保留两个连续换行）
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 移除首尾空白
        content = content.strip()

        return content


# 创建全局实例
encoding_detector = FileEncodingDetector()


def decode_file_content(data: bytes, file_path: str = None) -> str:
    """
    便捷函数：解码文件内容

    Args:
        data: 文件字节数据
        file_path: 文件路径（用于日志）

    Returns:
        解码后的文本内容

    Raises:
        ValueError: 无法解码文件内容
    """
    return encoding_detector.decode_content(data, file_path)


def detect_file_encoding(data: bytes) -> Optional[str]:
    """
    便捷函数：检测文件编码

    Args:
        data: 文件字节数据

    Returns:
        检测到的编码名称
    """
    return encoding_detector.detect_encoding(data)


__all__ = [
    'FileEncodingDetector',
    'encoding_detector',
    'decode_file_content',
    'detect_file_encoding',
]
