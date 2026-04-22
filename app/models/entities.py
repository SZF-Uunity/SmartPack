"""核心业务实体定义。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Role(str, Enum):
    """系统角色枚举。"""

    SYSADMIN = "sysadmin"
    ADMIN = "admin"
    PACKER = "packer"
    CUSTOMER_USER = "customer_user"


class PackingStrategy(str, Enum):
    """装箱推荐策略。"""

    COST_FIRST = "cost_first"
    QUALITY_FIRST = "quality_first"
    BALANCED = "balanced"


class OrderStatus(str, Enum):
    """订单状态机定义。"""

    DRAFT = "draft"
    CALCULATING = "calculating"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELED = "canceled"


class SoftDeleteMixin:
    """软删除通用字段。

    所有业务表通过 is_deleted 保留历史数据，满足审计与追溯需求。
    """

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class TimestampMixin:
    """统一时间戳字段，便于排查问题与统计。"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(Base, SoftDeleteMixin, TimestampMixin):
    """用户实体，简化版只保留核心字段。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)


class Customer(Base, SoftDeleteMixin, TimestampMixin):
    """客户实体。"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    default_strategy: Mapped[PackingStrategy] = mapped_column(
        SAEnum(PackingStrategy),
        default=PackingStrategy.BALANCED,
        nullable=False,
    )

    orders: Mapped[list[Order]] = relationship("Order", back_populates="customer")


class Material(Base, SoftDeleteMixin, TimestampMixin):
    """包装材质实体。"""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    cushioning_score: Mapped[float] = mapped_column(Float, default=1.0)
    max_load_weight: Mapped[float] = mapped_column(Float, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_food_grade: Mapped[bool] = mapped_column(Boolean, default=False)


class Product(Base, SoftDeleteMixin, TimestampMixin):
    """产品实体。"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    fragile: Mapped[bool] = mapped_column(Boolean, default=False)
    stack_limit: Mapped[int] = mapped_column(Integer, default=1)


class Box(Base, SoftDeleteMixin, TimestampMixin):
    """包装箱实体。"""

    __tablename__ = "boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    inner_length: Mapped[float] = mapped_column(Float, nullable=False)
    inner_width: Mapped[float] = mapped_column(Float, nullable=False)
    inner_height: Mapped[float] = mapped_column(Float, nullable=False)
    outer_length: Mapped[float] = mapped_column(Float, nullable=False)
    outer_width: Mapped[float] = mapped_column(Float, nullable=False)
    outer_height: Mapped[float] = mapped_column(Float, nullable=False)
    max_load_weight: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)


class Kit(Base, SoftDeleteMixin, TimestampMixin):
    """套装实体。"""

    __tablename__ = "kits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    item_map: Mapped[dict] = mapped_column(JSON, default=dict)


class Order(Base, SoftDeleteMixin, TimestampMixin):
    """订单实体。"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.DRAFT)
    selected_plan_id: Mapped[int | None] = mapped_column(ForeignKey("packing_plans.id"), nullable=True)

    customer: Mapped[Customer] = relationship("Customer", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order")


class OrderItem(Base, SoftDeleteMixin, TimestampMixin):
    """订单商品明细。"""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")


class PackingPlan(Base, SoftDeleteMixin, TimestampMixin):
    """装箱方案结果。"""

    __tablename__ = "packing_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    strategy: Mapped[PackingStrategy] = mapped_column(SAEnum(PackingStrategy), nullable=False)
    box_id: Mapped[int] = mapped_column(ForeignKey("boxes.id"), nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    utilization: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    placement_3d: Mapped[list] = mapped_column(JSON, default=list)


class PlanTemplate(Base, SoftDeleteMixin, TimestampMixin):
    """装箱模板。"""

    __tablename__ = "plan_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    plan_payload: Mapped[dict] = mapped_column(JSON, default=dict)
