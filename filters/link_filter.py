import logging
import re
from filters.base_filter import BaseFilter

logger = logging.getLogger(__name__)


class LinkFilter(BaseFilter):
    """
    删除消息中的超链接和用户名，同时保留可读文本
    """

    _MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\((https?|tg):\/\/[^\s)]+?\)')
    _HTML_LINK_PATTERN = re.compile(r'<a\s+href="[^"]*">(.*?)<\/a>', re.IGNORECASE | re.DOTALL)
    _PLAIN_LINK_PATTERN = re.compile(r'(https?|tg):\/\/\S+')
    _USERNAME_PATTERN = re.compile(r'@[a-zA-Z0-9_]+')

    async def _process(self, context):
        """
        移除 Markdown、HTML 与纯文本形式的超链接，以及用户名
        """
        message_text = context.message_text
        if not message_text:
            return True

        original_text = message_text

        # Markdown 链接 [text](url) -> text
        message_text = self._MARKDOWN_LINK_PATTERN.sub(r'\1', message_text)

        # HTML 链接 <a href="url">text</a> -> text
        message_text = self._HTML_LINK_PATTERN.sub(r'\1', message_text)

        # 纯文本 URL http(s)/tg -> 删除
        message_text = self._PLAIN_LINK_PATTERN.sub('', message_text)

        # 用户名 @username -> 删除
        message_text = self._USERNAME_PATTERN.sub('', message_text)

        # 清理多余空白
        message_text = re.sub(r'[ \t]+', ' ', message_text)
        message_text = re.sub(r'\s+\n', '\n', message_text)
        message_text = re.sub(r'\n{3,}', '\n\n', message_text).strip()

        if message_text != original_text:
            logger.info('LinkFilter 移除了消息中的超链接和用户名')

        context.message_text = message_text
        context.check_message_text = message_text

        return True
