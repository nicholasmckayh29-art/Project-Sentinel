"""Tests for Slack alert delivery."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.alerts.slack_client import SlackClient, deliver_slack_alerts  # noqa: E402
from backend.alerts.slack_formatter import format_price_alert  # noqa: E402

SAMPLE_BLOCKS = format_price_alert(
    model_name="GPT-4o Mini",
    savings_pct=-18.5,
    workload_name="AI Coding Assistant",
    true_cost=0.0012,
    baseline_true_cost=0.0015,
    action="Shift 20-40% of traffic and monitor quality",
    model_id="gpt-4o-mini",
    priority="high",
)

SAMPLE_ALERT = {
    "model_id": "gpt-4o-mini",
    "display_name": "GPT-4o Mini",
    "slack_blocks": SAMPLE_BLOCKS,
}


def _mock_response(*, ok: bool = True, status_code: int = 200, error: str | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"ok": ok, "error": error, "ts": "123.456"}
    response.raise_for_status = MagicMock()
    return response


def test_slack_client_post_blocks_success():
    session = MagicMock()
    session.post.return_value = _mock_response()

    client = SlackClient(token="xoxb-test", channel_id="C123", session=session)
    result = client.post_blocks(SAMPLE_BLOCKS, text="Price Alert: GPT-4o Mini")

    assert result["ok"] is True
    session.post.assert_called_once()
    call_kwargs = session.post.call_args
    assert call_kwargs[0][0] == "https://slack.com/api/chat.postMessage"
    payload = call_kwargs[1]["json"]
    assert payload["channel"] == "C123"
    assert payload["blocks"] == SAMPLE_BLOCKS
    assert call_kwargs[1]["headers"]["Authorization"] == "Bearer xoxb-test"


def test_slack_client_raises_on_api_error():
    session = MagicMock()
    session.post.return_value = _mock_response(ok=False, error="channel_not_found")

    client = SlackClient(token="xoxb-test", channel_id="C123", session=session)
    with pytest.raises(RuntimeError, match="channel_not_found"):
        client.post_blocks(SAMPLE_BLOCKS)


def test_slack_client_requires_token_and_channel():
    client = SlackClient(token="", channel_id="C123")
    with pytest.raises(ValueError, match="SLACK_BOT_TOKEN"):
        client.post_blocks(SAMPLE_BLOCKS)

    client = SlackClient(token="xoxb-test", channel_id="")
    with pytest.raises(ValueError, match="SLACK_CHANNEL_ID"):
        client.post_blocks(SAMPLE_BLOCKS)


def test_deliver_skips_when_token_missing(caplog):
    import logging

    caplog.set_level(logging.WARNING)
    result = deliver_slack_alerts([SAMPLE_ALERT], client=SlackClient(token="", channel_id="C123"))

    assert result == {"delivered": 0, "skipped": 1, "failed": 0, "reason": "no_token"}
    assert "SLACK_BOT_TOKEN not set" in caplog.text


def test_deliver_skips_when_channel_missing(caplog):
    import logging

    caplog.set_level(logging.WARNING)
    result = deliver_slack_alerts([SAMPLE_ALERT], client=SlackClient(token="xoxb-test", channel_id=""))

    assert result == {"delivered": 0, "skipped": 1, "failed": 0, "reason": "no_channel"}
    assert "SLACK_CHANNEL_ID not set" in caplog.text


def test_deliver_posts_all_alerts():
    session = MagicMock()
    session.post.return_value = _mock_response()
    client = SlackClient(token="xoxb-test", channel_id="C123", session=session)

    alerts = [SAMPLE_ALERT, {**SAMPLE_ALERT, "model_id": "claude-haiku"}]
    result = deliver_slack_alerts(alerts, client=client)

    assert result == {"delivered": 2, "skipped": 0, "failed": 0, "dry_run": False}
    assert session.post.call_count == 2


def test_deliver_counts_failures():
    session = MagicMock()
    session.post.return_value = _mock_response(ok=False, error="invalid_auth")
    client = SlackClient(token="xoxb-test", channel_id="C123", session=session)

    result = deliver_slack_alerts([SAMPLE_ALERT], client=client)

    assert result["delivered"] == 0
    assert result["failed"] == 1


def test_dry_run_prints_blocks_without_posting(capsys):
    session = MagicMock()
    client = SlackClient(token="xoxb-test", channel_id="C123", session=session)

    result = deliver_slack_alerts([SAMPLE_ALERT], dry_run=True, client=client)

    assert result == {"delivered": 0, "skipped": 0, "failed": 0, "dry_run": True, "printed": 1}
    session.post.assert_not_called()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["blocks"] == SAMPLE_BLOCKS


def test_deliver_empty_alerts():
    result = deliver_slack_alerts([])
    assert result == {"delivered": 0, "skipped": 0, "failed": 0, "dry_run": False}
