"""HTTP 路由定义。"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import OrderStatus, PackingPlan, PlanTemplate
from app.repositories.catalog_repository import CatalogRepository
from app.schemas.dto import (
    AIExtractRequest,
    AIExtractResponse,
    BoxCreate,
    ComparePlanResponse,
    OrderCreate,
    PlanResponse,
    ProductCreate,
)
from app.services.ai_service import AIService
from app.services.order_service import OrderService
from app.services.packing_service import PackingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """创建产品。"""

    logger.info("接口调用：创建产品 sku=%s", payload.sku)
    repo = CatalogRepository(db)
    try:
        return repo.create_product(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/boxes")
def create_box(payload: BoxCreate, db: Session = Depends(get_db)):
    """创建箱型。"""

    logger.info("接口调用：创建箱型 code=%s", payload.code)
    repo = CatalogRepository(db)
    try:
        return repo.create_box(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """创建订单。"""

    service = OrderService(db)
    try:
        return service.create_order(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/plans", response_model=ComparePlanResponse)
def calculate_plans(order_id: int, db: Session = Depends(get_db)):
    """生成并对比三种策略的装箱方案。"""

    service = PackingService(db)
    try:
        plans = service.generate_plans(order_id)
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
def bind_plan(order_id: int, plan_id: int, db: Session = Depends(get_db)):
    """绑定最终方案。"""

    service = OrderService(db)
    try:
        return service.bind_plan(order_id, plan_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db)):
    """确认订单并冻结内容。"""

    service = OrderService(db)
    try:
        return service.transit_status(order_id, OrderStatus.CONFIRMED)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ai/extract", response_model=AIExtractResponse)
def ai_extract(payload: AIExtractRequest):
    """AI 辅助解析接口。"""

    service = AIService()
    return service.extract_product_features(payload.description)


@router.post("/templates/{plan_id}")
def save_template(plan_id: int, name: str, db: Session = Depends(get_db)):
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
    logger.info("模板链路：保存模板 name=%s plan_id=%s", name, plan_id)
    return template
