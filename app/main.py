"""应用入口。"""

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import Base, engine

# 启动时先初始化日志，确保后续启动链路都有日志记录。
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix="/api/v1", tags=["smartpack"])


@app.on_event("startup")
def on_startup() -> None:
    """启动事件：创建数据库表结构。"""

    Base.metadata.create_all(bind=engine)
    logger.info("系统启动完成：数据库表已就绪")


@app.get("/health")
def health_check() -> dict:
    """健康检查接口。"""

    return {"status": "ok"}
