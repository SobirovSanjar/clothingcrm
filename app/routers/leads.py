"""Lead / opportunity CRUD routes (the sales pipeline)."""
from decimal import Decimal, InvalidOperation
import datetime as dt

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Customer, Lead, User
from ..templating import templates

router = APIRouter(prefix="/leads", tags=["leads"])


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value or "0")
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _to_date(value: str):
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


@router.get("", response_class=HTMLResponse)
async def list_leads(
    request: Request,
    view: str = "board",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    leads = (
        await db.execute(
            select(Lead)
            .options(selectinload(Lead.customer), selectinload(Lead.owner))
            .order_by(Lead.created_at.desc())
        )
    ).scalars().all()
    board = {stage: [] for stage in Lead.STAGES}
    for lead in leads:
        board.setdefault(lead.stage, []).append(lead)
    stage_totals = {
        stage: sum((l.value for l in items), Decimal("0"))
        for stage, items in board.items()
    }
    return templates.TemplateResponse(
        "leads/list.html",
        {
            "request": request,
            "user": user,
            "active": "leads",
            "leads": leads,
            "board": board,
            "stage_totals": stage_totals,
            "stages": Lead.STAGES,
            "view": view,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_lead(
    request: Request,
    customer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "leads/form.html",
        {
            "request": request,
            "user": user,
            "active": "leads",
            "lead": None,
            "customers": customers,
            "stages": Lead.STAGES,
            "preselect_customer": customer_id,
        },
    )


@router.post("/new")
async def create_lead(
    title: str = Form(...),
    customer_id: str = Form(""),
    stage: str = Form("New"),
    value: str = Form("0"),
    probability: int = Form(10),
    source: str = Form(""),
    expected_close_date: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lead = Lead(
        title=title.strip(),
        customer_id=int(customer_id) if customer_id else None,
        stage=stage,
        value=_to_decimal(value),
        probability=probability,
        source=source.strip() or None,
        expected_close_date=_to_date(expected_close_date),
        notes=notes.strip() or None,
        owner_id=user.id if user else None,
    )
    db.add(lead)
    await db.commit()
    return RedirectResponse("/leads", status_code=303)


@router.get("/{lead_id}/edit", response_class=HTMLResponse)
async def edit_lead(
    lead_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        return RedirectResponse("/leads", status_code=303)
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "leads/form.html",
        {
            "request": request,
            "user": user,
            "active": "leads",
            "lead": lead,
            "customers": customers,
            "stages": Lead.STAGES,
            "preselect_customer": lead.customer_id,
        },
    )


@router.post("/{lead_id}/edit")
async def update_lead(
    lead_id: int,
    title: str = Form(...),
    customer_id: str = Form(""),
    stage: str = Form("New"),
    value: str = Form("0"),
    probability: int = Form(10),
    source: str = Form(""),
    expected_close_date: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        return RedirectResponse("/leads", status_code=303)
    lead.title = title.strip()
    lead.customer_id = int(customer_id) if customer_id else None
    lead.stage = stage
    lead.value = _to_decimal(value)
    lead.probability = probability
    lead.source = source.strip() or None
    lead.expected_close_date = _to_date(expected_close_date)
    lead.notes = notes.strip() or None
    await db.commit()
    return RedirectResponse("/leads", status_code=303)


@router.post("/{lead_id}/stage")
async def quick_set_stage(
    lead_id: int,
    stage: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if lead and stage in Lead.STAGES:
        lead.stage = stage
        await db.commit()
    return RedirectResponse("/leads", status_code=303)


@router.post("/{lead_id}/delete")
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if lead:
        await db.delete(lead)
        await db.commit()
    return RedirectResponse("/leads", status_code=303)
