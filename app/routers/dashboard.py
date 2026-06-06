"""Dashboard route with KPIs and pipeline overview."""
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Activity, Customer, Lead, Order, Product, User
from ..templating import templates

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total_customers = await db.scalar(select(func.count(Customer.id)))
    total_products = await db.scalar(select(func.count(Product.id)))
    open_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.stage.notin_(["Won", "Lost"]))
    )
    won_value = await db.scalar(
        select(func.coalesce(func.sum(Lead.value), 0)).where(Lead.stage == "Won")
    )
    open_value = await db.scalar(
        select(func.coalesce(func.sum(Lead.value), 0)).where(
            Lead.stage.notin_(["Won", "Lost"])
        )
    )
    total_orders = await db.scalar(select(func.count(Order.id)))
    order_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.status != "Cancelled"
        )
    )

    # Pipeline grouped by stage
    pipeline_rows = (
        await db.execute(
            select(
                Lead.stage,
                func.count(Lead.id),
                func.coalesce(func.sum(Lead.value), 0),
            ).group_by(Lead.stage)
        )
    ).all()
    pipeline = {stage: {"count": 0, "value": Decimal("0")} for stage in Lead.STAGES}
    for stage, count, value in pipeline_rows:
        if stage in pipeline:
            pipeline[stage] = {"count": count, "value": value}
    max_pipeline = max((p["count"] for p in pipeline.values()), default=0)

    recent_activities = (
        await db.execute(
            select(Activity)
            .options(selectinload(Activity.customer))
            .order_by(Activity.created_at.desc())
            .limit(6)
        )
    ).scalars().all()

    recent_orders = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.customer))
            .order_by(Order.created_at.desc())
            .limit(6)
        )
    ).scalars().all()

    low_stock = (
        await db.execute(
            select(Product).where(Product.stock_qty < 25).order_by(Product.stock_qty).limit(6)
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "active": "dashboard",
            "total_customers": total_customers,
            "total_products": total_products,
            "open_leads": open_leads,
            "won_value": won_value,
            "open_value": open_value,
            "total_orders": total_orders,
            "order_revenue": order_revenue,
            "pipeline": pipeline,
            "max_pipeline": max_pipeline,
            "recent_activities": recent_activities,
            "recent_orders": recent_orders,
            "low_stock": low_stock,
        },
    )
