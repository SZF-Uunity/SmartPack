"""应用入口。"""

import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import Base, SessionLocal, engine
from app.services.bootstrap_service import BootstrapService

# 启动时先初始化日志，确保后续启动链路都有日志记录。
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.1.0")
app.include_router(router, prefix="/api/v1", tags=["smartpack"])

# 前端静态资源目录，采用模块化组织便于后续替换为 React/Vue 构建产物。
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "assets"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
    db = SessionLocal()
    try:
        BootstrapService(db).seed_if_needed()
    finally:
        db.close()
    logger.info("系统启动完成：数据库表已就绪")


@app.get("/app")
def serve_console() -> FileResponse:
    """返回前端控制台页面。"""

    logger.info("前端链路：访问企业控制台页面")
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check() -> dict:
    """健康检查接口。"""

    return {"status": "ok", "version": "1.1.0"}
