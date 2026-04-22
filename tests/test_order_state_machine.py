"""订单状态机测试。"""

import pytest

from app.models.entities import OrderStatus
from app.services.order_service import OrderService


class FakeOrder:
    """简易订单对象，用于单元测试。"""

    def __init__(self):
        self.id = 1
        self.status = OrderStatus.DRAFT
        self.is_deleted = False


class FakeQuery:
    """模拟 SQLAlchemy Query 最小能力。"""

    def __init__(self, order: FakeOrder):
        self.order = order

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.order


class FakeDB:
    """模拟数据库会话。"""

    def __init__(self, order: FakeOrder):
        self.order = order

    def query(self, _model):
        return FakeQuery(self.order)

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


def test_status_transition_success() -> None:
    """验证允许的状态流转成功。"""

    order = FakeOrder()
    service = OrderService(FakeDB(order))
    result = service.transit_status(1, OrderStatus.CALCULATING)
    assert result.status == OrderStatus.CALCULATING


def test_status_transition_invalid() -> None:
    """验证非法状态流转会被阻止。"""

    order = FakeOrder()
    order.status = OrderStatus.CONFIRMED
    service = OrderService(FakeDB(order))

    with pytest.raises(ValueError):
        service.transit_status(1, OrderStatus.CALCULATING)
