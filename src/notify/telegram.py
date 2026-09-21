"""Telegram delivery for Gold weekly decision briefs."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class TelegramNotifier:
    """Sends truncated weekly briefs to a private Telegram chat."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = (bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = (chat_id or os.getenv("TELEGRAM_CHAT_ID", "")).strip()

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, disable_preview: bool = True) -> Dict[str, Any]:
        if not self.configured:
            return {"ok": False, "skipped": True, "reason": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing"}
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        # Telegram hard limit ~4096 chars
        chunks = self._chunk(text, 3500)
        results = []
        for chunk in chunks:
            resp = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "disable_web_page_preview": disable_preview,
                },
                timeout=20,
            )
            try:
                payload = resp.json()
            except Exception:
                payload = {"ok": False, "status_code": resp.status_code, "text": resp.text[:200]}
            results.append(payload)
            if not payload.get("ok"):
                return {"ok": False, "results": results}
        return {"ok": True, "chunks": len(chunks), "results": results}

    def send_brief(self, brief: Dict[str, Any], dashboard_url: str = "") -> Dict[str, Any]:
        """Compose a compact trader SMS-style summary from brief dict."""
        text = self.format_brief_message(brief, dashboard_url=dashboard_url)
        return self.send_message(text)

    @staticmethod
    def format_brief_message(brief: Dict[str, Any], dashboard_url: str = "") -> str:
        ident = brief.get("identification") or {}
        mkt = brief.get("current_market_state") or {}
        out = brief.get("model_output") or {}
        cal = out.get("confidence_calibration") or brief.get("confidence_calibration") or {}
        corr = (brief.get("scenario_map") or {}).get("expected_corridor") or brief.get("expected_corridor") or {}
        nt = brief.get("no_trade_circuit_breaker") or (brief.get("risk_controls") or {}).get("no_trade_circuit_breaker") or {}
        news = brief.get("live_news_intelligence") or {}
        size = news.get("suggested_position_size") or {}
        headlines = news.get("top_headlines") or []

        week = ident.get("observation_week") or brief.get("observation_week") or "?"
        price = mkt.get("gold_reference_price") or brief.get("current_gold_price") or 0
        stance = out.get("directional_stance") or brief.get("taxonomy_stance") or "N/A"
        bias = out.get("recursive_bias_score", brief.get("bias_score", 0))
        exp = out.get("recursive_expected_return_pct", brief.get("expected_return_pct", 0))
        tier = cal.get("tier", "?")
        status = nt.get("status_label", "N/A")
        flags = ", ".join(news.get("risk_flags") or ["NONE"])

        lines = [
            "GOLD WEEKLY BRIEF",
            f"Week: {week}",
            f"Gold: ${float(price):,.2f}",
            f"Stance: {stance}",
            f"Bias: {float(bias):+.3f} | Exp: {float(exp):+.2f}% | Conf: {tier}",
            f"Corridor: ${float(corr.get('lower_support_10pct', 0)):,.0f} - ${float(corr.get('upper_resistance_90pct', 0)):,.0f}",
            f"Breaker: {status}",
            f"Size: {size.get('label', 'N/A')}",
            f"News flags: {flags}",
            "",
            "Top headlines:",
        ]
        for h in headlines[:5]:
            lines.append(f"- [{h.get('category', 'news')}] {h.get('title', '')[:120]}")
        lines += [
            "",
            "Your move: FOLLOW / FADE / PASS / OVERRIDE",
            "(No auto-trading. Confirm before you size risk.)",
        ]
        if dashboard_url:
            lines += ["", f"Dashboard: {dashboard_url}"]
        return "\n".join(lines)

    @staticmethod
    def _chunk(text: str, limit: int) -> List[str]:
        if len(text) <= limit:
            return [text]
        parts: List[str] = []
        buf: List[str] = []
        n = 0
        for line in text.splitlines(keepends=True):
            if n + len(line) > limit and buf:
                parts.append("".join(buf))
                buf = [line]
                n = len(line)
            else:
                buf.append(line)
                n += len(line)
        if buf:
            parts.append("".join(buf))
        return parts
