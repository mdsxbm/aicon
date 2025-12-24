"""
图像处理工具函数
"""
import base64
import io
import re
import uuid
import aiohttp
from typing import Any, Tuple, Optional

from src.core.logging import get_logger
from src.utils.storage import get_storage_client, UploadFile

logger = get_logger(__name__)


async def extract_image_url_from_response(result: Any) -> str:
    """
    从Provider响应中提取图片URL
    
    支持多种响应格式：
    - result.data[0].url (Gemini等)
    - result.data[0].b64_json (Base64格式)
    - 直接字符串URL
    - result.url (简单对象)
    
    Args:
        result: Provider的generate_image响应
        
    Returns:
        str: 图片URL
        
    Raises:
        ValueError: 无法从响应中提取URL
    """
    if hasattr(result, 'data') and result.data:
        # Gemini等Provider返回的格式：result.data[0].url 或 result.data[0].b64_json
        image_data = result.data[0]
        
        if hasattr(image_data, 'url') and image_data.url:
            return image_data.url
        elif hasattr(image_data, 'b64_json') and image_data.b64_json:
            # Base64格式，需要调用者自行处理上传
            raise ValueError("检测到base64格式图片，请使用extract_and_upload_image处理")
        else:
            raise ValueError(f"无法从image_data中提取URL: {dir(image_data)}")
    elif isinstance(result, str):
        # 直接返回字符串URL
        return result
    elif hasattr(result, 'url'):
        # 直接有url属性
        return result.url
    else:
        raise ValueError(f"无法从响应中提取图片URL，响应类型: {type(result)}, 属性: {dir(result)}")


async def extract_and_upload_image(
    result: Any, 
    user_id: str, 
    metadata: dict = None
) -> str:
    """
    从Provider响应中提取图片并上传到存储
    
    支持：
    - URL格式（直接返回）
    - Base64格式（下载并上传）
    - Data URL格式（解码并上传）
    
    Args:
        result: Provider的generate_image响应
        user_id: 用户ID
        metadata: 上传元数据
        
    Returns:
        str: 存储对象的key
    """
    # 1. 提取图片数据
    image_bytes, mime_type = await _extract_image_bytes(result)
    
    # 2. 上传到存储
    storage_client = await get_storage_client()
    file_id = str(uuid.uuid4())
    
    # 根据MIME类型确定扩展名
    ext = _get_extension_from_mime(mime_type)
    
    upload_file = UploadFile(
        filename=f"{file_id}.{ext}",
        file=io.BytesIO(image_bytes),
    )
    
    storage_result = await storage_client.upload_file(
        user_id=user_id,
        file=upload_file,
        metadata=metadata or {}
    )
    
    return storage_result["object_key"]


async def _extract_image_bytes(result: Any) -> Tuple[bytes, str]:
    """
    从Provider响应中提取图片字节数据
    
    Returns:
        Tuple[bytes, str]: (图片字节数据, MIME类型)
    """
    if hasattr(result, 'data') and result.data:
        image_data = result.data[0]
        
        # 优先使用 b64_json (Gemini 新格式)
        if hasattr(image_data, 'b64_json') and image_data.b64_json:
            base64_data = image_data.b64_json
            mime_type = getattr(image_data, 'mime', 'image/png')
            logger.info(f"使用 b64_json 格式, MIME: {mime_type}")
            
            # 修复base64 padding问题
            # 确保base64字符串长度是4的倍数
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            
            image_bytes = base64.b64decode(base64_data)
            return image_bytes, mime_type
        
        # 使用 URL
        elif hasattr(image_data, 'url') and image_data.url:
            image_url = image_data.url
            return await _download_image_from_url(image_url)
        
        else:
            raise ValueError(f"image_data既没有b64_json也没有url: {dir(image_data)}")
    
    elif isinstance(result, str):
        # 字符串URL
        return await _download_image_from_url(result)
    
    elif hasattr(result, 'url'):
        return await _download_image_from_url(result.url)
    
    else:
        raise ValueError(f"无法从响应中提取图片数据: {type(result)}")


async def _download_image_from_url(image_url: str) -> Tuple[bytes, str]:
    """
    从URL下载图片
    
    支持：
    - data: URL (base64编码)
    - HTTP/HTTPS URL
    
    Returns:
        Tuple[bytes, str]: (图片字节数据, MIME类型)
    """
    if image_url.startswith("data:"):
        # 解析 data URL: data:image/jpeg;base64,/9j/4AAQ...
        match = re.match(r'data:([^;]+);base64,(.+)', image_url)
        if not match:
            raise ValueError(f"无效的 data URL 格式: {image_url[:100]}")
        
        mime_type = match.group(1)
        base64_data = match.group(2)
        image_bytes = base64.b64decode(base64_data)
        logger.info(f"从 data URL 解码图片, MIME: {mime_type}, 大小: {len(image_bytes)} bytes")
        return image_bytes, mime_type
    
    else:
        # HTTP/HTTPS URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载图片失败: {resp.status}")
                image_bytes = await resp.read()
                mime_type = resp.content_type or 'image/png'
                logger.info(f"从 HTTP URL 下载图片, 大小: {len(image_bytes)} bytes")
                return image_bytes, mime_type


def _get_extension_from_mime(mime_type: str) -> str:
    """根据MIME类型获取文件扩展名"""
    mime_to_ext = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp',
    }
    return mime_to_ext.get(mime_type.lower(), 'jpg')


__all__ = [
    'extract_image_url_from_response',
    'extract_and_upload_image',
]
