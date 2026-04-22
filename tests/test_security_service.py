"""安全服务测试。"""

from app.models.entities import Role
from app.services.security_service import has_permission


def test_has_permission_sysadmin() -> None:
    """验证 sysadmin 拥有全权限。"""

    assert has_permission(Role.SYSADMIN, "any:permission") is True


def test_has_permission_customer_forbidden() -> None:
    """验证客户角色不能执行打包计算权限。"""

    assert has_permission(Role.CUSTOMER_USER, "packing:run") is False


def test_has_permission_packer_allowed() -> None:
    """验证打包员可以执行装箱计算。"""

    assert has_permission(Role.PACKER, "packing:run") is True


def test_has_permission_packer_catalog_read() -> None:
    """验证打包员可读取目录能力，保证 AI 解析链路联调。"""

    assert has_permission(Role.PACKER, "catalog:read") is True
