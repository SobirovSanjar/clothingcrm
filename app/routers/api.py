"""Lightweight JSON REST API (useful for integration testing / ERP-WMS sync).

Returns JSON instead of HTML. Mounted under /api.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Customer, Lead, Order, Product

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Health check that also verifies database connectivity."""
    await db.execute(select(1))
    return {"status": "ok", "database": "connected"}


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    return {
        "customers": await db.scalar(select(func.count(Customer.id))),
        "products": await db.scalar(select(func.count(Product.id))),
        "leads": await db.scalar(select(func.count(Lead.id))),
        "orders": await db.scalar(select(func.count(Order.id))),
        "open_pipeline_value": float(
            await db.scalar(
                select(func.coalesce(func.sum(Lead.value), 0)).where(
                    Lead.stage.notin_(["Won", "Lost"])
                )
            )
            or 0
        ),
    }


@router.get("/customers")
async def api_customers(db: AsyncSession = Depends(get_db)):
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return [
        {
            "id": c.id,
            "company_name": c.company_name,
            "type": c.customer_type,
            "status": c.status,
            "city": c.city,
            "country": c.country,
            "email": c.email,
            "credit_limit": float(c.credit_limit or 0),
        }
        for c in customers
    ]


@router.get("/products")
async def api_products(db: AsyncSession = Depends(get_db)):
    products = (
        await db.execute(select(Product).order_by(Product.name))
    ).scalars().all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "unit_price": float(p.unit_price or 0),
            "stock_qty": p.stock_qty,
        }
        for p in products
    ]


@router.get("/orders")
async def api_orders(db: AsyncSession = Depends(get_db)):
    orders = (
        await db.execute(
            select(Order).options(
                selectinload(Order.customer), selectinload(Order.items)
            ).order_by(Order.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer": o.customer.company_name if o.customer else None,
            "status": o.status,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "total_amount": float(o.total_amount or 0),
            "item_count": len(o.items),
        }
        for o in orders
    ]
