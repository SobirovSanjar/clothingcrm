"""Customer CRUD routes (server-rendered HTML)."""
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Customer, User
from ..templating import templates

router = APIRouter(prefix="/customers", tags=["customers"])

CUSTOMER_TYPES = ["Retailer", "Distributor", "Boutique", "Online Store", "Wholesaler"]
STATUSES = ["Prospect", "Active", "Inactive"]


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value or "0")
    except (InvalidOperation, TypeError):
        return Decimal("0")


@router.get("", response_class=HTMLResponse)
async def list_customers(
    request: Request,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Customer).options(selectinload(Customer.owner)).order_by(
        Customer.company_name
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Customer.company_name.ilike(like),
                Customer.city.ilike(like),
                Customer.country.ilike(like),
                Customer.email.ilike(like),
            )
        )
    customers = (await db.execute(stmt)).scalars().all()
    return templates.TemplateResponse(
        "customers/list.html",
        {
            "request": request,
            "user": user,
            "active": "customers",
            "customers": customers,
            "q": q or "",
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_customer(
    request: Request, user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "customers/form.html",
        {
            "request": request,
            "user": user,
            "active": "customers",
            "customer": None,
            "types": CUSTOMER_TYPES,
            "statuses": STATUSES,
        },
    )


@router.post("/new")
async def create_customer(
    request: Request,
    company_name: str = Form(...),
    customer_type: str = Form("Retailer"),
    email: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    country: str = Form(""),
    status: str = Form("Prospect"),
    credit_limit: str = Form("0"),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customer = Customer(
        company_name=company_name.strip(),
        customer_type=customer_type,
        email=email.strip() or None,
        phone=phone.strip() or None,
        website=website.strip() or None,
        address=address.strip() or None,
        city=city.strip() or None,
        country=country.strip() or None,
        status=status,
        credit_limit=_to_decimal(credit_limit),
        notes=notes.strip() or None,
        owner_id=user.id if user else None,
    )
    db.add(customer)
    await db.commit()
    return RedirectResponse(f"/customers/{customer.id}", status_code=303)


@router.get("/{customer_id}", response_class=HTMLResponse)
async def view_customer(
    customer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customer = (
        await db.execute(
            select(Customer)
            .where(Customer.id == customer_id)
            .options(
                selectinload(Customer.owner),
                selectinload(Customer.contacts),
                selectinload(Customer.leads),
                selectinload(Customer.orders),
                selectinload(Customer.activities),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        return RedirectResponse("/customers", status_code=303)
    return templates.TemplateResponse(
        "customers/detail.html",
        {
            "request": request,
            "user": user,
            "active": "customers",
            "customer": customer,
        },
    )


@router.get("/{customer_id}/edit", response_class=HTMLResponse)
async def edit_customer(
    customer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        return RedirectResponse("/customers", status_code=303)
    return templates.TemplateResponse(
        "customers/form.html",
        {
            "request": request,
            "user": user,
            "active": "customers",
            "customer": customer,
            "types": CUSTOMER_TYPES,
            "statuses": STATUSES,
        },
    )


@router.post("/{customer_id}/edit")
async def update_customer(
    customer_id: int,
    company_name: str = Form(...),
    customer_type: str = Form("Retailer"),
    email: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    country: str = Form(""),
    status: str = Form("Prospect"),
    credit_limit: str = Form("0"),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        return RedirectResponse("/customers", status_code=303)
    customer.company_name = company_name.strip()
    customer.customer_type = customer_type
    customer.email = email.strip() or None
    customer.phone = phone.strip() or None
    customer.website = website.strip() or None
    customer.address = address.strip() or None
    customer.city = city.strip() or None
    customer.country = country.strip() or None
    customer.status = status
    customer.credit_limit = _to_decimal(credit_limit)
    customer.notes = notes.strip() or None
    await db.commit()
    return RedirectResponse(f"/customers/{customer.id}", status_code=303)


@router.post("/{customer_id}/delete")
async def delete_customer(
    customer_id: int, db: AsyncSession = Depends(get_db)
):
    customer = await db.get(Customer, customer_id)
    if customer:
        await db.delete(customer)
        await db.commit()
    return RedirectResponse("/customers", status_code=303)
