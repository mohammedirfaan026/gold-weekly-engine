"""
FastAPI application main entrypoint.
Private Gold Research Terminal Backend.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import settings
from database.db_session import engine, Base
from database.migrate import init_schema, seed_data_sources

from backend.api.health import router as health_router
from backend.api.market import router as market_router
from backend.api.events import router as events_router
from backend.api.regimes import router as regimes_router
from backend.api.research import router as research_router
from backend.api.backtests import router as backtests_router
from backend.api.data_health import router as data_health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_schema()
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Private Institutional Quantitative Research Terminal for Gold (XAUUSD)",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(market_router, prefix=settings.API_PREFIX)
app.include_router(events_router, prefix=settings.API_PREFIX)
app.include_router(regimes_router, prefix=settings.API_PREFIX)
app.include_router(research_router, prefix=settings.API_PREFIX)
app.include_router(backtests_router, prefix=settings.API_PREFIX)
app.include_router(data_health_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "terminal": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
