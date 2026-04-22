"""数据库会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有 ORM 模型都继承该类。"""


# SQLite 需要关闭同线程检查；如果切换数据库可按需调整参数。
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """FastAPI 依赖注入：为每个请求提供独立数据库会话。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
