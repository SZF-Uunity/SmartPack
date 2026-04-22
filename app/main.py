"""应用入口。"""

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import Base, engine

# 启动时先初始化日志，确保后续启动链路都有日志记录。
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(router, prefix="/api/v1", tags=["smartpack"])


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """请求上下文中间件。

    统一记录 request_id 和耗时，便于生产环境问题定位。
    """

    request_id = str(uuid.uuid4())
    start_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start_at) * 1000, 2)
    response.headers["X-Request-Id"] = request_id
    logger.info("访问链路：%s %s request_id=%s elapsed_ms=%s", request.method, request.url.path, request_id, elapsed_ms)
    return response


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    """统一业务异常输出。"""

    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.on_event("startup")
def on_startup() -> None:
    """启动事件：创建数据库表结构。"""

    Base.metadata.create_all(bind=engine)
    logger.info("系统启动完成：数据库表已就绪")


@app.get("/health")
def health_check() -> dict:
    """健康检查接口。"""

    return {"status": "ok", "version": "1.0.0"}
