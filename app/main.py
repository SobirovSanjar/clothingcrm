"""Application entry point: builds the FastAPI app, middleware and routes."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import init_models
from .routers import (
    activities,
    api,
    auth,
    contacts,
    customers,
    dashboard,
    leads,
    orders,
    products,
)

# Paths that do not require authentication.
PUBLIC_PREFIXES = (
    "/login",
    "/static",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup.
    await init_models()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def require_login(request: Request, call_next):
    """Redirect unauthenticated users to the login page."""
    path = request.url.path
    is_public = any(path == p or path.startswith(p) for p in PUBLIC_PREFIXES)
    if not is_public and not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)


# SessionMiddleware is added LAST so it sits OUTERMOST in the stack and runs
# before require_login, ensuring request.session is available downstream.
# (Starlette executes the most-recently-added middleware first.)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE,
    same_site="lax",
)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(contacts.router)
app.include_router(leads.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(activities.router)
app.include_router(api.router)
