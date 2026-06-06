"""Order management routes, including line items."""
import datetime as dt
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Customer, Order, OrderItem, Product, User
from ..templating import templates

router = APIRouter(prefix="/orders", tags=["orders"])


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value or "0")
    except (InvalidOperation, TypeError):
        return Decimal("0")


async def _next_order_number(db: AsyncSession) -> str:
    count = await db.scalar(select(func.count(Order.id)))
    return f"SO-{dt.date.today().year}-{(count or 0) + 1:04d}"


@router.get("", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.customer))
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()
    return templates.TemplateResponse(
        "orders/list.html",
        {
            "request": request,
            "user": user,
            "active": "orders",
            "orders": orders,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_order(
    request: Request,
    customer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "orders/form.html",
        {
            "request": request,
            "user": user,
            "active": "orders",
            "order": None,
            "customers": customers,
            "statuses": Order.STATUSES,
            "preselect_customer": customer_id,
        },
    )


@router.post("/new")
async def create_order(
    customer_id: int = Form(...),
    status: str = Form("Draft"),
    order_date: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    try:
        parsed_date = dt.date.fromisoformat(order_date) if order_date else dt.date.today()
    except ValueError:
        parsed_date = dt.date.today()
    order = Order(
        order_number=await _next_order_number(db),
        customer_id=customer_id,
        status=status,
        order_date=parsed_date,
        notes=notes.strip() or None,
        total_amount=Decimal("0.00"),
    )
    db.add(order)
    await db.commit()
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
async def view_order(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = (
        await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
        )
    ).scalar_one_or_none()
    if not order:
        return RedirectResponse("/orders", status_code=303)
    products = (
        await db.execute(select(Product).order_by(Product.name))
    ).scalars().all()
    return templates.TemplateResponse(
        "orders/detail.html",
        {
            "request": request,
            "user": user,
            "active": "orders",
            "order": order,
            "products": products,
            "statuses": Order.STATUSES,
        },
    )


@router.post("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if order and status in Order.STATUSES:
        order.status = status
        await db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.post("/{order_id}/items/add")
async def add_item(
    order_id: int,
    product_id: int = Form(...),
    quantity: int = Form(1),
    db: AsyncSession = Depends(get_db),
):
    order = (
        await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
    ).scalar_one_or_none()
    product = await db.get(Product, product_id)
    if order and product:
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=max(1, quantity),
            unit_price=product.unit_price,
        )
        db.add(item)
        await db.flush()
        await db.refresh(order, attribute_names=["items"])
        order.recalculate_total()
        await db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.post("/{order_id}/items/{item_id}/delete")
async def remove_item(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(OrderItem, item_id)
    if item and item.order_id == order_id:
        await db.delete(item)
        await db.flush()
    order = (
        await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
    ).scalar_one_or_none()
    if order:
        order.recalculate_total()
        await db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.post("/{order_id}/delete")
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if order:
        await db.delete(order)
        await db.commit()
    return RedirectResponse("/orders", status_code=303)
