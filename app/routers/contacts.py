"""Contact CRUD routes. Contacts always belong to a customer."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Contact, Customer, User
from ..templating import templates

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_class=HTMLResponse)
async def list_contacts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contacts = (
        await db.execute(
            select(Contact)
            .options(selectinload(Contact.customer))
            .order_by(Contact.last_name, Contact.first_name)
        )
    ).scalars().all()
    return templates.TemplateResponse(
        "contacts/list.html",
        {
            "request": request,
            "user": user,
            "active": "contacts",
            "contacts": contacts,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_contact(
    request: Request,
    customer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "contacts/form.html",
        {
            "request": request,
            "user": user,
            "active": "contacts",
            "contact": None,
            "customers": customers,
            "preselect_customer": customer_id,
        },
    )


@router.post("/new")
async def create_contact(
    customer_id: int = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    title: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    contact = Contact(
        customer_id=customer_id,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        title=title.strip() or None,
        email=email.strip() or None,
        phone=phone.strip() or None,
        is_primary=is_primary,
    )
    db.add(contact)
    await db.commit()
    return RedirectResponse(f"/customers/{customer_id}", status_code=303)


@router.get("/{contact_id}/edit", response_class=HTMLResponse)
async def edit_contact(
    contact_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        return RedirectResponse("/contacts", status_code=303)
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "contacts/form.html",
        {
            "request": request,
            "user": user,
            "active": "contacts",
            "contact": contact,
            "customers": customers,
            "preselect_customer": contact.customer_id,
        },
    )


@router.post("/{contact_id}/edit")
async def update_contact(
    contact_id: int,
    customer_id: int = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    title: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        return RedirectResponse("/contacts", status_code=303)
    contact.customer_id = customer_id
    contact.first_name = first_name.strip()
    contact.last_name = last_name.strip()
    contact.title = title.strip() or None
    contact.email = email.strip() or None
    contact.phone = phone.strip() or None
    contact.is_primary = is_primary
    await db.commit()
    return RedirectResponse(f"/customers/{customer_id}", status_code=303)


@router.post("/{contact_id}/delete")
async def delete_contact(
    contact_id: int, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    customer_id = contact.customer_id if contact else None
    if contact:
        await db.delete(contact)
        await db.commit()
    if customer_id:
        return RedirectResponse(f"/customers/{customer_id}", status_code=303)
    return RedirectResponse("/contacts", status_code=303)
