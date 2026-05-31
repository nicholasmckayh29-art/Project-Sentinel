"""Send alert emails to premium users via Resend."""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)


def _alert_subject(alert: dict[str, Any]) -> str:
    direction = "DROP" if (alert.get("pct_change") or 0) < 0 else "SPIKE"
    name = alert.get("display_name", alert.get("model_id", "UNKNOWN"))
    pct = abs(alert.get("pct_change") or 0)
    return f"INTEL // {name} {direction} {pct:.1f}%"


def _alert_html(alert: dict[str, Any]) -> str:
    direction = "▼" if (alert.get("pct_change") or 0) < 0 else "▲"
    color = "#00FF41" if direction == "▼" else "#FF3333"
    return f"""<!DOCTYPE html>
<html>
<body style="background:#0D0D0D;color:#E0E0E0;font-family:monospace;padding:24px">
<h1 style="color:#00FF41">[ CLASSIFIED ] PRICING SENTINEL</h1>
<p style="color:{color};font-size:18px">{direction} {alert.get("display_name", alert.get("model_id"))}</p>
<p>Workload: {alert.get("workload_name", alert.get("workload_id", "—"))}</p>
<p>Change: {alert.get("pct_change")}%</p>
<p>True Cost: ${alert.get("true_cost", 0):.4f}/1K tokens</p>
<p>Baseline True Cost: ${alert.get("baseline_true_cost", 0):.4f}/1K tokens</p>
<p style="color:#666">Priority: {alert.get("priority", "high").upper()} | Reason: {alert.get("reason")}</p>
</body>
</html>"""


def _users_for_alert(client, alert: dict[str, Any]) -> list[dict[str, str]]:
    model_id = alert.get("model_id")
    if not model_id:
        return []

    model_row = client.table("models").select("provider_id").eq("id", model_id).maybe_single().execute()
    provider_id = model_row.data.get("provider_id") if model_row.data else None

    recipients: dict[str, str] = {}

    for table, col, val in [
        ("user_watchlist_models", "model_id", model_id),
        ("user_watchlist_providers", "provider_id", provider_id),
    ]:
        if not val:
            continue
        rows = client.table(table).select("user_id").eq(col, val).execute()
        for row in rows.data or []:
            uid = row["user_id"]
            sub = (
                client.table("subscriptions")
                .select("status, current_period_end")
                .eq("user_id", uid)
                .maybe_single()
                .execute()
            )
            if not sub.data or sub.data.get("status") != "active":
                continue
            prefs = (
                client.table("notification_prefs")
                .select("email_alerts")
                .eq("user_id", uid)
                .maybe_single()
                .execute()
            )
            if prefs.data and not prefs.data.get("email_alerts", True):
                continue
            profile = client.auth.admin.get_user_by_id(uid)
            email = profile.user.email if profile and profile.user else None
            if email:
                recipients[uid] = email

    return [{"user_id": k, "email": v} for k, v in recipients.items()]


def send_premium_alert_emails(client, alerts: list[dict[str, Any]]) -> int:
    api_key = os.environ.get("RESEND_API_KEY")
    from_addr = os.environ.get("RESEND_FROM_EMAIL", "intel@pricing-sentinel.com")
    if not api_key:
        log.warning("RESEND_API_KEY not set — skipping email alerts")
        return 0

    import requests

    sent = 0
    for alert in alerts:
        for recipient in _users_for_alert(client, alert):
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_addr,
                    "to": [recipient["email"]],
                    "subject": _alert_subject(alert),
                    "html": _alert_html(alert),
                },
                timeout=30,
            )
            if resp.ok:
                sent += 1
            else:
                log.error("Resend failed for %s: %s", recipient["email"], resp.text)
    return sent
