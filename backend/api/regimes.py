"""
Regime Engine API Router.
"""

from __future__ import annotations

from typing import Dict, List, Any
from fastapi import APIRouter

from backend.models.schemas import RegimeCurrentResponse
from research.services.regime_service import RegimeService

router = APIRouter(prefix="/regimes", tags=["Regimes"])


@router.get("/current", response_model=RegimeCurrentResponse)
def get_current_regimes():
    """Returns the current macro regime, gold trend, and positioning state."""
    svc = RegimeService()
    return svc.get_current_regimes()


@router.get("/history")
def get_regime_frequencies():
    """Returns historical frequency distributions and transition statistics across regimes."""
    svc = RegimeService()
    return svc.get_historical_frequencies()


@router.get("/definitions")
def get_regime_definitions():
    """Returns documented quantitative definitions and lookback periods for each regime."""
    svc = RegimeService()
    return svc.get_definitions()
