import logging
import os
import copy

logger = logging.getLogger(__name__)

async def get_media_size(media):
    """获取媒体文件大小"""
    if not media:
        return 0

    try:
        # 对于所有类型的媒体，先尝试获取 document
        if hasattr(media, 'document') and media.document:
            return media.document.size

        # 对于照片，获取最大尺寸
        if hasattr(media, 'photo') and media.photo:
            # 获取最大尺寸的照片
            largest_photo = max(media.photo.sizes, key=lambda x: x.size if hasattr(x, 'size') else 0)
            return largest_photo.size if hasattr(largest_photo, 'size') else 0

        # 如果是其他类型，尝试直接获取 size 属性
        if hasattr(media, 'size'):
            return media.size

    except Exception as e:
        logger.error(f'获取媒体大小时出错: {str(e)}')

    return 0

async def get_max_media_size():
    """获取媒体文件大小上限"""
    max_media_size_str = os.getenv('MAX_MEDIA_SIZE')
    if not max_media_size_str:
        logger.error('未设置 MAX_MEDIA_SIZE 环境变量')
        raise ValueError('必须在 .env 文件中设置 MAX_MEDIA_SIZE')
    return float(max_media_size_str) * 1024 * 1024  # 转换为字节，支持小数


async def collect_media_metadata(message, file_path, temp_dir):
    """
    收集媒体附加信息，例如视频封面和属性

    Args:
        message: Telethon 消息对象
        file_path: 已下载媒体文件路径
        temp_dir: 临时目录（用于存放封面）

    Returns:
        dict: 包含 thumb、attributes、mime_type 等信息的字典
    """
    metadata = {}

    try:
        document = getattr(message, 'video', None) or getattr(message, 'document', None)
        if not document:
            return metadata

        mime_type = getattr(document, 'mime_type', None)
        if not mime_type or not mime_type.startswith('video/'):
            return metadata

        metadata['mime_type'] = mime_type
        metadata['supports_streaming'] = True

        if getattr(document, 'attributes', None):
            metadata['attributes'] = [copy.deepcopy(attr) for attr in document.attributes]

        try:
            thumbs = getattr(document, 'thumbs', None)
            if thumbs:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                thumb_path = os.path.join(temp_dir, f"{base_name}_thumb.jpg")
                if not os.path.exists(thumb_path):
                    downloaded = await message.download_media(file=thumb_path, thumb=-1)
                    if downloaded:
                        metadata['thumb'] = downloaded
                else:
                    metadata['thumb'] = thumb_path
        except Exception as exc:
            logger.warning(f'下载视频封面失败: {exc}')

    except Exception as exc:
        logger.warning(f'收集媒体元数据失败: {exc}')

    return metadata
