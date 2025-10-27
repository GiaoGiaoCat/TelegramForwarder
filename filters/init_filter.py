import logging
import os
import pytz
import asyncio
from utils.constants import TEMP_DIR
from utils.media import get_max_media_size

from filters.base_filter import BaseFilter

logger = logging.getLogger(__name__)

class InitFilter(BaseFilter):
    """
    初始化过滤器，为context添加基本信息
    """
    
    async def _process(self, context):
        """
        添加原始链接和发送者信息
        
        Args:
            context: 消息上下文
            
        Returns:
            bool: 是否继续处理
        """
        rule = context.rule
        event = context.event

        # logger.info(f"InitFilter处理消息前，context: {context.__dict__}")
        try:
            #处理媒体组消息
            if event.message.grouped_id:
                logger.info(f'[InitFilter] 检测到媒体组消息，组ID: {event.message.grouped_id}, 消息ID: {event.message.id}')
                # 等待更长时间让所有媒体消息到达
                # await asyncio.sleep(1)

                # 收集媒体组的所有消息
                try:
                    # 使用消息所在的 chat 进行查询，而不是 event.chat_id
                    # 这样可以避免 entity 解析问题
                    chat = await event.message.get_chat()
                    logger.info(f'[InitFilter] 开始查询媒体组消息，chat: {chat.id if hasattr(chat, "id") else chat}')

                    # 获取 user_client 用于查询历史消息
                    # Bot 账号无法调用 iter_messages (BotMethodInvalidError)
                    from utils.common import get_main_module
                    main = await get_main_module()
                    query_client = main.user_client if (main and hasattr(main, 'user_client')) else event.client

                    found_messages = 0
                    async for message in query_client.iter_messages(
                        chat,
                        limit=20,
                        min_id=event.message.id - 10,
                        max_id=event.message.id + 10
                    ):
                        if message.grouped_id == event.message.grouped_id:
                            found_messages += 1
                            if message.text:
                                # 保存第一条消息的文本和按钮
                                context.message_text = message.text or ''
                                context.original_message_text = message.text or ''
                                context.check_message_text = message.text or ''
                                context.buttons = message.buttons if hasattr(message, 'buttons') else None
                            logger.info(f'[InitFilter] 找到媒体组消息 {found_messages}: ID={message.id}, 文本={message.text}')

                    logger.info(f'[InitFilter] 媒体组查询完成，共找到 {found_messages} 条同组消息')

                except Exception as e:
                    logger.error(f'[InitFilter] 收集媒体组消息时出错: {str(e)}')
                    logger.exception(e)
                    context.errors.append(f"收集媒体组消息错误: {str(e)}")
           
        finally:
            # logger.info(f"InitFilter处理消息后，context: {context.__dict__}")
            return True
