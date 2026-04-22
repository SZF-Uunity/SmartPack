"""HTTP 路由定义。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import RequestContext, require_permission
from app.db.session import get_db
from app.models.entities import ApiKey, Order, OrderStatus, PackingPlan, PlanTemplate
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.security_repository import SecurityRepository
from app.schemas.dto import (
    AIExtractRequest,
    AIExtractResponse,
    ApiKeyCreate,
    BoxCreate,
    ComparePlanResponse,
    OrderCreate,
    PlanResponse,
    ProductCreate,
)
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.services.order_service import OrderService
from app.services.packing_service import PackingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/security/api-keys")
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("catalog:write")),
):
    """创建 API Key，仅管理员可执行。"""

    repo = SecurityRepository(db)
    audit = AuditService(db)
    try:
        api_key = repo.create_api_key(payload)
        audit.record(actor=ctx.api_key_name, action="create_api_key", target=f"api_key:{api_key.id}")
        return {
            "id": api_key.id,
            "name": api_key.name,
            "owner_user_id": api_key.owner_user_id,
            "enabled": api_key.enabled,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/security/api-keys")
def list_api_keys(
    db: Session = Depends(get_db),
    _ctx: RequestContext = Depends(require_permission("catalog:read")),
):
    """查询 API Key 元信息（不返回明文密钥）。"""

    rows = db.query(ApiKey).filter(ApiKey.is_deleted.is_(False)).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "owner_user_id": row.owner_user_id,
            "enabled": row.enabled,
            "ip_whitelist": row.ip_whitelist,
            "rate_limit_per_minute": row.rate_limit_per_minute,
        }
        for row in rows
    ]


@router.post("/products")
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("catalog:write")),
):
    """创建产品。"""

    logger.info("接口调用：创建产品 sku=%s", payload.sku)
    repo = CatalogRepository(db)
    audit = AuditService(db)
    try:
        product = repo.create_product(payload)
        audit.record(actor=ctx.api_key_name, action="create_product", target=f"product:{product.id}")
        return product
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/boxes")
def create_box(
    payload: BoxCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("catalog:write")),
):
    """创建箱型。"""

    logger.info("接口调用：创建箱型 code=%s", payload.code)
    repo = CatalogRepository(db)
    audit = AuditService(db)
    try:
        box = repo.create_box(payload)
        audit.record(actor=ctx.api_key_name, action="create_box", target=f"box:{box.id}")
        return box
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders")
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("order:create")),
):
    """创建订单。"""

    service = OrderService(db)
    audit = AuditService(db)
    try:
        order = service.create_order(payload)
        audit.record(actor=ctx.api_key_name, action="create_order", target=f"order:{order.id}")
        return order
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/orders")
def list_orders(
    customer_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("order:read")),
):
    """分页查询订单。

    企业级场景通常需要列表高频查询，因此预留分页参数并支持按客户过滤。
    """

    query = db.query(Order).filter(Order.is_deleted.is_(False))
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)

    rows = query.offset(skip).limit(limit).all()
    logger.info("接口调用：查询订单 skip=%s limit=%s", skip, limit)
    return rows


@router.post("/orders/{order_id}/plans", response_model=ComparePlanResponse)
def calculate_plans(
    order_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("packing:run")),
):
    """生成并对比三种策略的装箱方案。"""

    service = PackingService(db)
    audit = AuditService(db)
    try:
        plans = service.generate_plans(order_id)
        audit.record(actor=ctx.api_key_name, action="generate_plans", target=f"order:{order_id}")
        return ComparePlanResponse(
            order_id=order_id,
            status=OrderStatus.CALCULATING,
            plans=[
                PlanResponse(
                    plan_id=plan.id,
                    strategy=plan.strategy,
                    box_id=plan.box_id,
                    total_cost=plan.total_cost,
                    utilization=plan.utilization,
                    quality_score=plan.quality_score,
                    placement_3d=plan.placement_3d,
                )
                for plan in plans
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/bind-plan/{plan_id}")
def bind_plan(
    order_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("order:create")),
):
    """绑定最终方案。"""

    service = OrderService(db)
    audit = AuditService(db)
    try:
        order = service.bind_plan(order_id, plan_id)
        audit.record(actor=ctx.api_key_name, action="bind_plan", target=f"order:{order_id}")
        return order
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("order:approve")),
):
    """确认订单并冻结内容。"""

    service = OrderService(db)
    audit = AuditService(db)
    try:
        order = service.transit_status(order_id, OrderStatus.CONFIRMED)
        audit.record(actor=ctx.api_key_name, action="confirm_order", target=f"order:{order_id}")
        return order
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ai/extract", response_model=AIExtractResponse)
def ai_extract(
    payload: AIExtractRequest,
    _ctx: RequestContext = Depends(require_permission("catalog:read")),
):
    """AI 辅助解析接口。"""

    service = AIService()
    return service.extract_product_features(payload.description)


@router.post("/templates/{plan_id}")
def save_template(
    plan_id: int,
    name: str,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(require_permission("template:write")),
):
    """保存方案为模板，支持后续复用。"""

    plan = db.query(PackingPlan).filter(PackingPlan.id == plan_id, PackingPlan.is_deleted.is_(False)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")

    template = PlanTemplate(
        name=name,
        plan_payload={
            "strategy": plan.strategy.value,
            "box_id": plan.box_id,
            "placement_3d": plan.placement_3d,
        },
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    audit = AuditService(db)
    audit.record(actor=ctx.api_key_name, action="save_template", target=f"plan_template:{template.id}")
    logger.info("模板链路：保存模板 name=%s plan_id=%s", name, plan_id)
    return template
