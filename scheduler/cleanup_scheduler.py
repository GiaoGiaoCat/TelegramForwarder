import asyncio
import os
import time
import logging
from datetime import datetime
from utils.constants import TEMP_DIR

logger = logging.getLogger(__name__)

class CleanupScheduler:
    """
    临时文件清理调度器
    定期清理超过指定时间的临时文件
    """

    def __init__(self, cleanup_interval_seconds=3600, file_age_seconds=3600):
        """
        初始化清理调度器

        Args:
            cleanup_interval_seconds: 清理任务执行间隔（秒），默认3600秒（1小时）
            file_age_seconds: 文件保留时长（秒），超过此时间的文件将被删除，默认3600秒（1小时）
        """
        self.cleanup_interval = cleanup_interval_seconds
        self.file_age = file_age_seconds
        self.task = None
        self.running = False

        # 确保临时目录存在
        os.makedirs(TEMP_DIR, exist_ok=True)

        logger.info(f'清理调度器初始化: 间隔={cleanup_interval_seconds}秒, 文件保留={file_age_seconds}秒')

    async def start(self):
        """启动清理调度器"""
        if self.running:
            logger.warning('清理调度器已在运行')
            return

        self.running = True
        self.task = asyncio.create_task(self._run_cleanup_loop())
        logger.info('清理调度器已启动')

    def stop(self):
        """停止清理调度器"""
        self.running = False
        if self.task:
            self.task.cancel()
            logger.info('清理调度器已停止')

    async def _run_cleanup_loop(self):
        """运行清理循环"""
        while self.running:
            try:
                # 执行清理
                await self._cleanup_old_files()

                # 等待下一次执行
                logger.info(f'下次清理将在 {self.cleanup_interval} 秒后执行')
                await asyncio.sleep(self.cleanup_interval)

            except asyncio.CancelledError:
                logger.info('清理任务已取消')
                break
            except Exception as e:
                logger.error(f'清理循环出错: {str(e)}')
                logger.exception(e)
                # 出错后等待一段时间再继续
                await asyncio.sleep(60)

    async def _cleanup_old_files(self):
        """清理超过指定时间的临时文件"""
        try:
            if not os.path.exists(TEMP_DIR):
                logger.warning(f'临时目录不存在: {TEMP_DIR}')
                return

            current_time = time.time()
            cleaned_count = 0
            cleaned_size = 0
            total_count = 0
            total_size = 0

            logger.info(f'开始清理临时文件，目录: {TEMP_DIR}')

            # 遍历临时目录中的所有文件
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)

                # 跳过目录
                if not os.path.isfile(file_path):
                    continue

                try:
                    # 获取文件信息
                    file_stat = os.stat(file_path)
                    file_age = current_time - file_stat.st_mtime
                    file_size = file_stat.st_size

                    total_count += 1
                    total_size += file_size

                    # 检查文件是否超过保留时间
                    if file_age > self.file_age:
                        # 删除文件
                        os.remove(file_path)
                        cleaned_count += 1
                        cleaned_size += file_size

                        # 转换文件大小为可读格式
                        size_str = self._format_size(file_size)
                        age_str = self._format_duration(file_age)

                        logger.info(f'已删除文件: {filename} (大小: {size_str}, 存在时间: {age_str})')

                except FileNotFoundError:
                    # 文件可能已被其他进程删除
                    logger.debug(f'文件不存在（可能已被删除）: {filename}')
                except PermissionError:
                    logger.warning(f'无权限删除文件: {filename}')
                except Exception as e:
                    logger.error(f'处理文件时出错 {filename}: {str(e)}')

            # 输出清理摘要
            total_size_str = self._format_size(total_size)
            cleaned_size_str = self._format_size(cleaned_size)

            if cleaned_count > 0:
                logger.info(
                    f'清理完成 - '
                    f'总文件数: {total_count} ({total_size_str}), '
                    f'清理文件数: {cleaned_count} ({cleaned_size_str}), '
                    f'剩余文件数: {total_count - cleaned_count} ({self._format_size(total_size - cleaned_size)})'
                )
            else:
                logger.info(f'清理完成 - 没有需要清理的文件（总文件数: {total_count}, 总大小: {total_size_str}）')

        except Exception as e:
            logger.error(f'清理临时文件时出错: {str(e)}')
            logger.exception(e)

    @staticmethod
    def _format_size(size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def _format_duration(seconds):
        """格式化时间长度"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            return f"{seconds/60:.0f}分钟"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}小时"
        else:
            return f"{seconds/86400:.1f}天"
