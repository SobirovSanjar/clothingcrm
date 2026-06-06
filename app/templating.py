"""Shared Jinja2 templates instance and custom filters.

NOTE: Jinja variable delimiters are configured as [[ ... ]] instead of the
default double-brace syntax. Block tags still use {% ... %}.
"""
import datetime as dt

from fastapi.templating import Jinja2Templates

from .config import settings

templates = Jinja2Templates(
    directory="app/templates",
    variable_start_string="[[",
    variable_end_string="]]",
)


def money(value) -> str:
    try:
        return "${:,.2f}".format(float(value or 0))
    except (TypeError, ValueError):
        return "$0.00"


def date_fmt(value) -> str:
    if not value:
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%d %b %Y")
    return str(value)


def date_input(value) -> str:
    """Format a date for an <input type=date> value (YYYY-MM-DD)."""
    if not value:
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value)


templates.env.filters["money"] = money
templates.env.filters["date_fmt"] = date_fmt
templates.env.filters["date_input"] = date_input
templates.env.globals["app_name"] = settings.APP_NAME
