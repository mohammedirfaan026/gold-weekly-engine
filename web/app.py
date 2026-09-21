"""
Private read-only Gold Weekly dashboard (VPS-friendly).

Auth: single shared password from DASHBOARD_PASSWORD.
No trading / order buttons -- browse brief, news, run status only.

Usage:
    python -m web.app
    # or:  uvicorn/gunicorn via deploy scripts
"""

from __future__ import annotations

import json
import os
import secrets
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

LIVE_DIR = ROOT / "data" / "live"
BRIEF_JSON = LIVE_DIR / "latest_brief.json"
RUN_LOG = LIVE_DIR / "last_run.json"
NEWS_CSV = ROOT / "data" / "news" / "latest_news.csv"
NEWS_META = ROOT / "data" / "news" / "latest_news_meta.json"
BRIEF_MD = ROOT / "research" / "reports" / "LIVE_WEEKLY_DECISION_BRIEF.md"


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("DASHBOARD_SECRET_KEY") or secrets.token_hex(32)
    password = os.getenv("DASHBOARD_PASSWORD", "").strip()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not password:
                # Fail closed if no password configured on a public host
                return render_template(
                    "setup.html",
                    message="Set DASHBOARD_PASSWORD in .env before exposing this dashboard.",
                ), 503
            if not session.get("authed"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if secrets.compare_digest(request.form.get("password", ""), password):
                session["authed"] = True
                return redirect(request.args.get("next") or url_for("home"))
            error = "Incorrect password."
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def home():
        brief = _load_json(BRIEF_JSON)
        run = _load_json(RUN_LOG)
        if not brief:
            return render_template("empty.html", run=run)
        view = _brief_view(brief)
        return render_template("home.html", view=view, run=run)

    @app.route("/news")
    @login_required
    def news():
        brief = _load_json(BRIEF_JSON) or {}
        intel = brief.get("live_news_intelligence") or {}
        meta = _load_json(NEWS_META) or {}
        rows = []
        if NEWS_CSV.exists():
            try:
                import pandas as pd
                df = pd.read_csv(NEWS_CSV)
                rows = df.head(40).to_dict(orient="records")
            except Exception:
                rows = intel.get("top_headlines") or []
        else:
            rows = intel.get("top_headlines") or []
        return render_template("news.html", intel=intel, meta=meta, rows=rows)

    @app.route("/brief.txt")
    @login_required
    def brief_text():
        if not BRIEF_MD.exists():
            abort(404)
        return BRIEF_MD.read_text(encoding="utf-8"), 200, {"Content-Type": "text/plain; charset=utf-8"}

    @app.route("/health")
    def health():
        return {"status": "ok", "brief_present": BRIEF_JSON.exists()}

    return app


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _brief_view(brief: Dict[str, Any]) -> Dict[str, Any]:
    ident = brief.get("identification") or {}
    mkt = brief.get("current_market_state") or {}
    out = brief.get("model_output") or {}
    cal = out.get("confidence_calibration") or brief.get("confidence_calibration") or {}
    corr = (brief.get("scenario_map") or {}).get("expected_corridor") or brief.get("expected_corridor") or {}
    inv = (brief.get("scenario_map") or {}).get("invalidation") or brief.get("invalidation") or {}
    nt = brief.get("no_trade_circuit_breaker") or (brief.get("risk_controls") or {}).get("no_trade_circuit_breaker") or {}
    news = brief.get("live_news_intelligence") or {}
    size = news.get("suggested_position_size") or {}
    fac = mkt.get("factor_states") or {}

    return {
        "week": ident.get("observation_week") or brief.get("observation_week"),
        "generated": brief.get("generated_at_utc") or ident.get("prediction_timestamp"),
        "price": mkt.get("gold_reference_price") or brief.get("current_gold_price"),
        "stance": out.get("directional_stance") or brief.get("taxonomy_stance"),
        "bias": out.get("recursive_bias_score", brief.get("bias_score")),
        "expected_return": out.get("recursive_expected_return_pct", brief.get("expected_return_pct")),
        "tier": cal.get("tier"),
        "win_rate": cal.get("empirical_win_rate_pct"),
        "corridor_high": corr.get("upper_resistance_90pct"),
        "corridor_mid": corr.get("expected_center"),
        "corridor_low": corr.get("lower_support_10pct"),
        "invalidation": inv.get("note"),
        "breaker": nt.get("status_label"),
        "action": nt.get("action_guidance"),
        "size_label": size.get("label"),
        "size_rationale": size.get("rationale"),
        "news_flags": news.get("risk_flags") or [],
        "narrative": news.get("narrative_summary"),
        "headlines": (news.get("top_headlines") or [])[:6],
        "factors": fac,
        "model_version": ident.get("model_version"),
    }


app = create_app()


if __name__ == "__main__":
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "8787"))
    debug = os.getenv("DASHBOARD_DEBUG", "0") == "1"
    print(f"Gold dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
