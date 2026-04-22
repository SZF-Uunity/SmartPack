"""接口层 DTO 定义。"""

from pydantic import BaseModel, Field

from app.models.entities import OrderStatus, PackingStrategy


class ProductCreate(BaseModel):
    """产品创建请求。"""

    sku: str
    name: str
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    weight: float = Field(gt=0)
    fragile: bool = False
    stack_limit: int = Field(default=1, ge=1)


class BoxCreate(BaseModel):
    """包装箱创建请求。"""

    code: str
    name: str
    inner_length: float = Field(gt=0)
    inner_width: float = Field(gt=0)
    inner_height: float = Field(gt=0)
    outer_length: float = Field(gt=0)
    outer_width: float = Field(gt=0)
    outer_height: float = Field(gt=0)
    max_load_weight: float = Field(gt=0)
    cost: float = Field(gt=0)
    material_id: int


class OrderItemCreate(BaseModel):
    """订单商品项。"""

    product_id: int
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    """订单创建请求。"""

    customer_id: int
    items: list[OrderItemCreate]


class PlanResponse(BaseModel):
    """装箱方案响应体。"""

    plan_id: int
    strategy: PackingStrategy
    box_id: int
    total_cost: float
    utilization: float
    quality_score: float
    placement_3d: list[dict]


class ComparePlanResponse(BaseModel):
    """多策略方案对比结果。"""

    order_id: int
    status: OrderStatus
    plans: list[PlanResponse]


class AIExtractRequest(BaseModel):
    """AI 文本解析请求。"""

    description: str


class AIExtractResponse(BaseModel):
    """AI 文本解析响应。"""

    suggested_fragile: bool
    suggested_length: float
    suggested_width: float
    suggested_height: float
    suggested_weight: float
    material_recommendation: str
