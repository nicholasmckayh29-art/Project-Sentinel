"""Post formatted Slack Block Kit messages via the Slack Web API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

log = logging.getLogger(__name__)

SLACK_CHAT_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


class SlackClient:
    """Thin wrapper around Slack chat.postMessage."""

    def __init__(
        self,
        *,
        token: str | None = None,
        channel_id: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.token = token if token is not None else os.environ.get("SLACK_BOT_TOKEN")
        self.channel_id = channel_id if channel_id is not None else os.environ.get("SLACK_CHANNEL_ID")
        self._session = session or requests.Session()

    @property
    def has_token(self) -> bool:
        return bool(self.token)

    @property
    def has_channel(self) -> bool:
        return bool(self.channel_id)

    def is_configured(self) -> bool:
        return self.has_token and self.has_channel

    def post_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        text: str = "Pricing alert",
    ) -> dict[str, Any]:
        """Post Block Kit blocks to the configured channel."""
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN is not set")
        if not self.channel_id:
            raise ValueError("SLACK_CHANNEL_ID is not set")

        response = self._session.post(
            SLACK_CHAT_POST_MESSAGE_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": self.channel_id,
                "blocks": blocks,
                "text": text,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "unknown Slack API error"))
        return payload

    def post_alert(self, alert: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any] | None:
        """Post a single alert's slack_blocks. Returns API response, or None in dry-run."""
        blocks = alert.get("slack_blocks")
        if not blocks:
            log.warning("Alert for %s has no slack_blocks; skipping", alert.get("model_id", "unknown"))
            return None

        model_name = alert.get("display_name", alert.get("model_id", "model"))
        fallback_text = f"Price Alert: {model_name}"

        if dry_run:
            log.info("Dry run — would post Slack message for %s", model_name)
            print(json.dumps({"text": fallback_text, "blocks": blocks}, indent=2))
            return None

        return self.post_blocks(blocks, text=fallback_text)


def deliver_slack_alerts(
    alerts: list[dict[str, Any]],
    *,
    dry_run: bool = False,
    client: SlackClient | None = None,
) -> dict[str, Any]:
    """Post alerts to Slack when configured; otherwise log and continue."""
    slack = client or SlackClient()

    if not alerts:
        return {"delivered": 0, "skipped": 0, "failed": 0, "dry_run": dry_run}

    if dry_run:
        for alert in alerts:
            slack.post_alert(alert, dry_run=True)
        return {"delivered": 0, "skipped": 0, "failed": 0, "dry_run": True, "printed": len(alerts)}

    if not slack.has_token:
        log.warning("SLACK_BOT_TOKEN not set; skipping Slack delivery for %d alert(s)", len(alerts))
        return {"delivered": 0, "skipped": len(alerts), "failed": 0, "reason": "no_token"}

    if not slack.has_channel:
        log.warning("SLACK_CHANNEL_ID not set; skipping Slack delivery for %d alert(s)", len(alerts))
        return {"delivered": 0, "skipped": len(alerts), "failed": 0, "reason": "no_channel"}

    delivered = 0
    failed = 0
    for alert in alerts:
        try:
            slack.post_alert(alert, dry_run=False)
            delivered += 1
        except Exception:
            failed += 1
            log.exception(
                "Failed to post Slack alert for %s",
                alert.get("model_id", "unknown"),
            )

    log.info("Slack delivery complete: %d delivered, %d failed", delivered, failed)
    return {"delivered": delivered, "skipped": 0, "failed": failed, "dry_run": False}
