"""订单业务服务。"""

import logging

from sqlalchemy.orm import Session

from app.models.entities import Order, OrderItem, OrderStatus
from app.schemas.dto import OrderCreate

logger = logging.getLogger(__name__)


class OrderService:
    """封装订单创建、状态流转与确认逻辑。"""

    allowed_transitions = {
        OrderStatus.DRAFT: {OrderStatus.CALCULATING, OrderStatus.CANCELED},
        OrderStatus.CALCULATING: {OrderStatus.CONFIRMED, OrderStatus.CANCELED},
        OrderStatus.CONFIRMED: {OrderStatus.SHIPPED},
        OrderStatus.SHIPPED: set(),
        OrderStatus.CANCELED: set(),
    }

    def __init__(self, db: Session):
        self.db = db

    def create_order(self, payload: OrderCreate) -> Order:
        """创建订单和订单明细。"""

        logger.info("订单链路：创建订单 customer_id=%s", payload.customer_id)
        order = Order(customer_id=payload.customer_id, status=OrderStatus.DRAFT)
        self.db.add(order)
        self.db.flush()

        for item in payload.items:
            self.db.add(OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity))

        self.db.commit()
        self.db.refresh(order)
        return order

    def transit_status(self, order_id: int, next_status: OrderStatus) -> Order:
        """按状态机执行订单状态迁移。"""

        order = self.db.query(Order).filter(Order.id == order_id, Order.is_deleted.is_(False)).first()
        if not order:
            raise ValueError("订单不存在")
        if next_status not in self.allowed_transitions[order.status]:
            raise ValueError(f"非法状态流转: {order.status} -> {next_status}")

        logger.info("订单状态流转：order_id=%s %s->%s", order_id, order.status, next_status)
        order.status = next_status
        self.db.commit()
        self.db.refresh(order)
        return order

    def bind_plan(self, order_id: int, plan_id: int) -> Order:
        """为订单绑定最终方案，确认后禁止修改。"""

        order = self.db.query(Order).filter(Order.id == order_id, Order.is_deleted.is_(False)).first()
        if not order:
            raise ValueError("订单不存在")
        if order.status == OrderStatus.CONFIRMED:
            raise ValueError("订单已确认，不能修改绑定方案")

        logger.info("订单绑定方案：order_id=%s plan_id=%s", order_id, plan_id)
        order.selected_plan_id = plan_id
        self.db.commit()
        self.db.refresh(order)
        return order
