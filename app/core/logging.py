"""日志初始化模块。"""

import logging

from app.core.config import settings


def setup_logging() -> None:
    """初始化全局日志格式。

    日志格式保持简洁，包含时间、等级、模块与中文信息，覆盖关键链路。
    """

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
