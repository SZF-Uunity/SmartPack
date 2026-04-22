"""装箱计算服务。"""

import logging

from sqlalchemy.orm import Session

from app.models.entities import (
    Box,
    Order,
    OrderItem,
    OrderStatus,
    PackingPlan,
    PackingStrategy,
    Product,
)

logger = logging.getLogger(__name__)


class PackingService:
    """核心装箱服务，包含三种策略计算与排序逻辑。"""

    def __init__(self, db: Session):
        self.db = db

    def _volume(self, length: float, width: float, height: float) -> float:
        """统一体积计算，减少重复代码。"""

        return length * width * height

    def _get_order_items(self, order_id: int) -> list[tuple[Product, int]]:
        """获取订单明细并加载商品信息。"""

        rows = (
            self.db.query(OrderItem, Product)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(OrderItem.order_id == order_id, OrderItem.is_deleted.is_(False), Product.is_deleted.is_(False))
            .all()
        )
        return [(product, item.quantity) for item, product in rows]

    def _choose_box(self, total_volume: float, total_weight: float) -> list[Box]:
        """筛选符合容量与承重条件的启用箱型。

        业务规则：停用箱子不参与装箱计算。
        """

        boxes = (
            self.db.query(Box)
            .filter(Box.enabled.is_(True), Box.is_deleted.is_(False), Box.max_load_weight >= total_weight)
            .all()
        )
        return [
            box
            for box in boxes
            if self._volume(box.inner_length, box.inner_width, box.inner_height) >= total_volume
        ]

    def generate_plans(self, order_id: int) -> list[PackingPlan]:
        """生成成本优先、质量优先、均衡三种方案。"""

        logger.info("装箱链路开始：order_id=%s", order_id)
        order = self.db.query(Order).filter(Order.id == order_id, Order.is_deleted.is_(False)).first()
        if not order:
            raise ValueError("订单不存在")

        if order.status == OrderStatus.CONFIRMED:
            # 业务规则：订单确认后不可变更。
            raise ValueError("订单已确认，禁止重新计算方案")

        items = self._get_order_items(order_id)
        if not items:
            raise ValueError("订单无可计算商品")

        total_volume = sum(self._volume(p.length, p.width, p.height) * qty for p, qty in items)
        total_weight = sum(p.weight * qty for p, qty in items)
        fragile_count = sum(1 for p, _ in items if p.fragile)

        candidate_boxes = self._choose_box(total_volume, total_weight)
        if not candidate_boxes:
            raise ValueError("没有满足条件的箱型")

        plans: list[PackingPlan] = []
        for strategy in [PackingStrategy.COST_FIRST, PackingStrategy.QUALITY_FIRST, PackingStrategy.BALANCED]:
            # 不同策略通过不同评分函数排序，实现可扩展策略引擎。
            ranked = sorted(
                candidate_boxes,
                key=lambda b: self._score_box(
                    box=b,
                    total_volume=total_volume,
                    fragile_count=fragile_count,
                    strategy=strategy,
                ),
            )
            best_box = ranked[0]
            plan = PackingPlan(
                order_id=order_id,
                strategy=strategy,
                box_id=best_box.id,
                total_cost=best_box.cost + fragile_count * 0.5,
                utilization=round(total_volume / self._volume(best_box.inner_length, best_box.inner_width, best_box.inner_height), 4),
                quality_score=round((best_box.max_load_weight / max(total_weight, 0.1)) + (2 if fragile_count else 0), 4),
                placement_3d=self._mock_placement(items),
            )
            self.db.add(plan)
            plans.append(plan)

        order.status = OrderStatus.CALCULATING
        self.db.commit()
        for plan in plans:
            self.db.refresh(plan)
        logger.info("装箱链路完成：order_id=%s 生成方案数=%s", order_id, len(plans))
        return plans

    def _score_box(self, box: Box, total_volume: float, fragile_count: int, strategy: PackingStrategy) -> float:
        """根据策略返回评分，分值越低越优。"""

        volume = self._volume(box.inner_length, box.inner_width, box.inner_height)
        utilization_gap = abs(1 - (total_volume / volume))
        if strategy == PackingStrategy.COST_FIRST:
            return box.cost * 0.8 + utilization_gap
        if strategy == PackingStrategy.QUALITY_FIRST:
            return -box.max_load_weight - fragile_count
        return box.cost * 0.4 + utilization_gap * 0.6

    def _mock_placement(self, items: list[tuple[Product, int]]) -> list[dict]:
        """返回简化版 3D 坐标，用于前端渲染占位。

        后续可替换为真实 3D 装箱算法（如遗传算法或启发式搜索）。
        """

        placement: list[dict] = []
        x_cursor = 0.0
        for product, quantity in items:
            for _ in range(quantity):
                placement.append(
                    {
                        "sku": product.sku,
                        "x": x_cursor,
                        "y": 0.0,
                        "z": 0.0,
                        "l": product.length,
                        "w": product.width,
                        "h": product.height,
                    }
                )
                x_cursor += product.length
        return placement
