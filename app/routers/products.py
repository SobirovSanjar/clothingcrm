"""Product catalogue CRUD routes."""
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Product, User
from ..templating import templates

router = APIRouter(prefix="/products", tags=["products"])

CATEGORIES = [
    "T-Shirts",
    "Shirts",
    "Trousers",
    "Jackets",
    "Dresses",
    "Knitwear",
    "Accessories",
    "Footwear",
    "General",
]


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value or "0")
    except (InvalidOperation, TypeError):
        return Decimal("0")


@router.get("", response_class=HTMLResponse)
async def list_products(
    request: Request,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Product).order_by(Product.name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(like),
                Product.sku.ilike(like),
                Product.category.ilike(like),
            )
        )
    products = (await db.execute(stmt)).scalars().all()
    return templates.TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "user": user,
            "active": "products",
            "products": products,
            "q": q or "",
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_product(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "products/form.html",
        {
            "request": request,
            "user": user,
            "active": "products",
            "product": None,
            "categories": CATEGORIES,
        },
    )


@router.post("/new")
async def create_product(
    sku: str = Form(...),
    name: str = Form(...),
    category: str = Form("General"),
    size: str = Form(""),
    color: str = Form(""),
    unit_price: str = Form("0"),
    stock_qty: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    product = Product(
        sku=sku.strip(),
        name=name.strip(),
        category=category,
        size=size.strip() or None,
        color=color.strip() or None,
        unit_price=_to_decimal(unit_price),
        stock_qty=stock_qty,
    )
    db.add(product)
    await db.commit()
    return RedirectResponse("/products", status_code=303)


@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product(
    product_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = await db.get(Product, product_id)
    if not product:
        return RedirectResponse("/products", status_code=303)
    return templates.TemplateResponse(
        "products/form.html",
        {
            "request": request,
            "user": user,
            "active": "products",
            "product": product,
            "categories": CATEGORIES,
        },
    )


@router.post("/{product_id}/edit")
async def update_product(
    product_id: int,
    sku: str = Form(...),
    name: str = Form(...),
    category: str = Form("General"),
    size: str = Form(""),
    color: str = Form(""),
    unit_price: str = Form("0"),
    stock_qty: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(Product, product_id)
    if not product:
        return RedirectResponse("/products", status_code=303)
    product.sku = sku.strip()
    product.name = name.strip()
    product.category = category
    product.size = size.strip() or None
    product.color = color.strip() or None
    product.unit_price = _to_decimal(unit_price)
    product.stock_qty = stock_qty
    await db.commit()
    return RedirectResponse("/products", status_code=303)


@router.post("/{product_id}/delete")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if product:
        await db.delete(product)
        await db.commit()
    return RedirectResponse("/products", status_code=303)
