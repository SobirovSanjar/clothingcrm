"""Activity / task routes (calls, emails, meetings, tasks, notes)."""
import datetime as dt

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Activity, Customer, User
from ..templating import templates

router = APIRouter(prefix="/activities", tags=["activities"])


def _to_date(value: str):
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


@router.get("", response_class=HTMLResponse)
async def list_activities(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    activities = (
        await db.execute(
            select(Activity)
            .options(selectinload(Activity.customer), selectinload(Activity.owner))
            .order_by(Activity.completed, Activity.created_at.desc())
        )
    ).scalars().all()
    return templates.TemplateResponse(
        "activities/list.html",
        {
            "request": request,
            "user": user,
            "active": "activities",
            "activities": activities,
            "today": dt.date.today(),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_activity(
    request: Request,
    customer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "activities/form.html",
        {
            "request": request,
            "user": user,
            "active": "activities",
            "activity": None,
            "customers": customers,
            "types": Activity.TYPES,
            "preselect_customer": customer_id,
        },
    )


@router.post("/new")
async def create_activity(
    type: str = Form("Note"),
    subject: str = Form(...),
    description: str = Form(""),
    customer_id: str = Form(""),
    due_date: str = Form(""),
    completed: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    activity = Activity(
        type=type,
        subject=subject.strip(),
        description=description.strip() or None,
        customer_id=int(customer_id) if customer_id else None,
        due_date=_to_date(due_date),
        completed=completed,
        owner_id=user.id if user else None,
    )
    db.add(activity)
    await db.commit()
    return RedirectResponse("/activities", status_code=303)


@router.get("/{activity_id}/edit", response_class=HTMLResponse)
async def edit_activity(
    activity_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    activity = await db.get(Activity, activity_id)
    if not activity:
        return RedirectResponse("/activities", status_code=303)
    customers = (
        await db.execute(select(Customer).order_by(Customer.company_name))
    ).scalars().all()
    return templates.TemplateResponse(
        "activities/form.html",
        {
            "request": request,
            "user": user,
            "active": "activities",
            "activity": activity,
            "customers": customers,
            "types": Activity.TYPES,
            "preselect_customer": activity.customer_id,
        },
    )


@router.post("/{activity_id}/edit")
async def update_activity(
    activity_id: int,
    type: str = Form("Note"),
    subject: str = Form(...),
    description: str = Form(""),
    customer_id: str = Form(""),
    due_date: str = Form(""),
    completed: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    activity = await db.get(Activity, activity_id)
    if not activity:
        return RedirectResponse("/activities", status_code=303)
    activity.type = type
    activity.subject = subject.strip()
    activity.description = description.strip() or None
    activity.customer_id = int(customer_id) if customer_id else None
    activity.due_date = _to_date(due_date)
    activity.completed = completed
    await db.commit()
    return RedirectResponse("/activities", status_code=303)


@router.post("/{activity_id}/toggle")
async def toggle_activity(
    activity_id: int, db: AsyncSession = Depends(get_db)
):
    activity = await db.get(Activity, activity_id)
    if activity:
        activity.completed = not activity.completed
        await db.commit()
    return RedirectResponse("/activities", status_code=303)


@router.post("/{activity_id}/delete")
async def delete_activity(
    activity_id: int, db: AsyncSession = Depends(get_db)
):
    activity = await db.get(Activity, activity_id)
    if activity:
        await db.delete(activity)
        await db.commit()
    return RedirectResponse("/activities", status_code=303)
