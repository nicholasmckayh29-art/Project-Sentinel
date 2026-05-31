"""Format Slack Block Kit messages for pricing alerts."""

from __future__ import annotations

from typing import Any


def format_price_alert(
    *,
    model_name: str,
    savings_pct: float,
    workload_name: str,
    true_cost: float,
    baseline_true_cost: float,
    action: str,
    model_id: str,
    priority: str = "high",
) -> list[dict[str, Any]]:
    tag = "#critical" if priority == "critical" else "#medium"
    drop = abs(savings_pct)

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Price Alert: {model_name}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Savings:* {drop:.1f}% vs baseline"},
                {"type": "mrkdwn", "text": f"*Workload:* {workload_name}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*True Cost:* ${true_cost:.4f}/1K output tokens (was ${baseline_true_cost:.4f})\n"
                    f"*Action:* {action}\n"
                    f"*Tag:* {tag}"
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "url": f"https://pricepertoken.com/pricing/{model_id}",
                }
            ],
        },
    ]


def format_digest_summary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = "\n".join(
        f"• *{item['model_name']}* — {item['recommendation']}" for item in items[:10]
    )
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Weekly Digest*\n{lines or '_No items._'}"},
        }
    ]
    costs = [float(item.get("true_cost", 0)) for item in items[:10] if item.get("true_cost")]
    if costs:
        from backend.alerts.email_digest import quickchart_sparkline_url

        blocks.append(
            {
                "type": "image",
                "image_url": quickchart_sparkline_url(costs),
                "alt_text": "True cost trend",
            }
        )
    return blocks
