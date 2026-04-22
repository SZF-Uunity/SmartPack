"""系统配置模块。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """统一管理系统配置，便于后续扩展到多环境部署。"""

    # 应用名称会用于日志输出和 OpenAPI 文档展示。
    app_name: str = "SmartPack 智能包装系统"
    # 数据库先使用 SQLite，后续可无缝切换为 PostgreSQL。
    database_url: str = "sqlite:///./smartpack.db"
    # 日志级别默认 INFO，保证链路可观测且不过度噪声。
    log_level: str = "INFO"
    # 企业级部署可通过环境变量快速调整分页与性能边界。
    default_page_size: int = 20
    max_page_size: int = 200

    # 允许从 .env 覆盖配置，便于本地和生产环境解耦。
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
