"""安全与访问控制服务。"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import ApiKey, Role
from app.utils.security import hash_api_key

logger = logging.getLogger(__name__)


class SecurityService:
    """封装 API Key 校验、IP 白名单和速率限制。"""

    # 使用进程内窗口计数器，部署多副本时可替换为 Redis 实现。
    _request_windows: dict[str, deque[datetime]] = defaultdict(deque)

    def __init__(self, db: Session):
        self.db = db

    def validate_api_key(self, raw_key: str, client_ip: str) -> ApiKey:
        """校验 API Key 可用性。

        校验项包含：是否存在、是否启用、IP 是否命中白名单、速率是否超限。
        """

        logger.info("安全链路：开始校验 API Key")
        key_hash = hash_api_key(raw_key)
        api_key = (
            self.db.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash, ApiKey.enabled.is_(True), ApiKey.is_deleted.is_(False))
            .first()
        )
        if not api_key:
            raise PermissionError("API Key 无效")

        if api_key.ip_whitelist and client_ip not in api_key.ip_whitelist:
            raise PermissionError("当前 IP 不在白名单")

        self._check_rate_limit(raw_key, api_key.rate_limit_per_minute)
        logger.info("安全链路：API Key 校验通过 key_name=%s", api_key.name)
        return api_key

    def _check_rate_limit(self, raw_key: str, limit_per_minute: int) -> None:
        """滑动窗口限流。

        为保持低耦合，这里仅依赖标准库，后续可以替换为网关或 Redis 限流组件。
        """

        now = datetime.utcnow()
        window = self._request_windows[raw_key]
        threshold = now - timedelta(minutes=1)

        while window and window[0] < threshold:
            window.popleft()

        if len(window) >= limit_per_minute:
            raise PermissionError("请求过于频繁，请稍后重试")

        window.append(now)


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.SYSADMIN: {"*"},
    Role.ADMIN: {
        "catalog:write",
        "catalog:read",
        "order:approve",
        "order:read",
        "template:write",
        "template:read",
    },
    Role.PACKER: {
        "order:create",
        "order:read",
        "packing:run",
        "template:read",
        "template:write",
    },
    Role.CUSTOMER_USER: {
        "order:read:mine",
        "template:read:mine",
    },
}


def has_permission(role: Role, permission: str) -> bool:
    """统一权限判断函数。"""

    role_permissions = ROLE_PERMISSIONS.get(role, set())
    return "*" in role_permissions or permission in role_permissions
