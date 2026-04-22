"""API 公共依赖。"""

import logging

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Role
from app.services.security_service import SecurityService, has_permission

logger = logging.getLogger(__name__)


class RequestContext:
    """请求上下文。

    将认证后的角色和 API Key 名称集中存放，便于后续审计日志统一使用。
    """

    def __init__(self, role: Role, api_key_name: str):
        self.role = role
        self.api_key_name = api_key_name


# 公开健康检查和文档之外的接口统一启用 API Key 保护。
def get_request_context(
    db: Session = Depends(get_db),
    x_api_key: str = Header(default=""),
    x_user_role: str = Header(default=Role.PACKER.value),
    x_forwarded_for: str = Header(default="127.0.0.1"),
) -> RequestContext:
    """鉴权依赖：校验 API Key + 解析角色。"""

    if not x_api_key:
        raise HTTPException(status_code=401, detail="缺少 API Key")

    try:
        role = Role(x_user_role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="非法角色标识") from exc

    client_ip = x_forwarded_for.split(",")[0].strip() or "127.0.0.1"
    service = SecurityService(db)
    try:
        api_key = service.validate_api_key(x_api_key, client_ip)
        logger.info("安全链路：请求鉴权成功 role=%s ip=%s", role.value, client_ip)
        return RequestContext(role=role, api_key_name=api_key.name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def require_permission(permission: str):
    """权限依赖工厂。

    通过闭包方式减少重复代码，符合低耦合可演进设计。
    """

    def dependency(ctx: RequestContext = Depends(get_request_context)) -> RequestContext:
        if not has_permission(ctx.role, permission):
            raise HTTPException(status_code=403, detail=f"角色 {ctx.role.value} 无权限执行 {permission}")
        return ctx

    return dependency
