"""系统启动引导服务。"""

import logging

from sqlalchemy.orm import Session

from app.models.entities import ApiKey, Box, Customer, Material, PackingStrategy, Product, Role, User
from app.utils.security import hash_api_key, hash_password

logger = logging.getLogger(__name__)


class BootstrapService:
    """初始化联调用基础数据。

    该服务仅在数据库为空时写入最小可用数据，确保前后端可直接联调。
    """

    def __init__(self, db: Session):
        self.db = db

    def seed_if_needed(self) -> None:
        """按需初始化演示数据。"""

        has_user = self.db.query(User).filter(User.is_deleted.is_(False)).first()
        if has_user:
            logger.info("引导链路：检测到已有用户数据，跳过初始化")
            return

        logger.info("引导链路：开始初始化联调基础数据")

        sysadmin = User(username="sysadmin", password_hash=hash_password("SmartPack@123"), role=Role.SYSADMIN)
        admin = User(username="admin", password_hash=hash_password("SmartPack@123"), role=Role.ADMIN)
        packer = User(username="packer", password_hash=hash_password("SmartPack@123"), role=Role.PACKER)
        self.db.add_all([sysadmin, admin, packer])
        self.db.flush()

        # 提供一个默认 API Key，便于本地联调；生产环境必须立即替换。
        raw_api_key = "dev-smartpack-key-please-change"
        self.db.add(
            ApiKey(
                name="dev-default",
                key_hash=hash_api_key(raw_api_key),
                owner_user_id=sysadmin.id,
                enabled=True,
                ip_whitelist=[],
                rate_limit_per_minute=600,
            )
        )

        customer = Customer(name="默认联调客户", default_strategy=PackingStrategy.BALANCED)
        material = Material(
            code="M-STD-001",
            name="标准瓦楞纸",
            cushioning_score=1.2,
            max_load_weight=20,
            unit_price=1.5,
            is_food_grade=False,
        )
        self.db.add_all([customer, material])
        self.db.flush()

        self.db.add(
            Box(
                code="B-STD-001",
                name="标准箱-小",
                inner_length=30,
                inner_width=20,
                inner_height=15,
                outer_length=32,
                outer_width=22,
                outer_height=17,
                max_load_weight=15,
                cost=3.5,
                enabled=True,
                material_id=material.id,
            )
        )
        self.db.add(
            Product(
                sku="SKU-DEMO-001",
                name="演示玻璃杯",
                length=10,
                width=10,
                height=12,
                weight=0.8,
                fragile=True,
                stack_limit=1,
            )
        )

        self.db.commit()
        logger.info("引导链路：基础数据初始化完成，默认API Key=%s", raw_api_key)
