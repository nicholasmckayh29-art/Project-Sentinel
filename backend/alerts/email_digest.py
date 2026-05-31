"""Generate weekly HTML email digests for the Release Radar Analyst."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote


def quickchart_sparkline_url(values: list[float], *, width: int = 400, height: int = 120) -> str:
    """Build a QuickChart URL for a simple line sparkline (email-safe PNG)."""
    if not values:
        values = [0.0, 0.0]
    data = ",".join(f"{v:.4f}" for v in values[-30:])
    chart = (
        "{type:'line',data:{labels:[],datasets:[{data:["
        + data
        + "],borderColor:'rgb(0,255,65)',fill:false}]},options:{legend:{display:false},scales:{xAxes:[{display:false}],yAxes:[{display:false}]}}}"
    )
    return f"https://quickchart.io/chart?w={width}&h={height}&c={quote(chart)}"


def render_weekly_digest(
    *,
    moves: list[dict[str, Any]],
    top_picks: list[dict[str, Any]],
    watch_items: list[str] | None = None,
    date: datetime | None = None,
) -> str:
    when = date or datetime.now(timezone.utc)
    title_date = when.strftime("%B %d, %Y")

    moves_html = "\n".join(
        f"  <li><strong>{item['model']}</strong> {item['summary']} → "
        f"<em>Recommendation: {item['recommendation']}</em></li>"
        for item in moves
    ) or "  <li><em>No major pricing moves detected.</em></li>"

    picks_rows = "\n".join(
        f"  <tr><td>{pick['model']}</td><td>{pick['use_case']}</td>"
        f"<td>${pick['true_cost']:.2f}/1M</td><td>{pick['savings_pct']:.0f}%</td></tr>"
        for pick in top_picks
    )

    watch_html = ""
    if watch_items:
        watch_html = f"<p><em>Next week: {'; '.join(watch_items)}</em></p>"

    chart_html = ""
    if top_picks:
        sample_values = [float(p.get("true_cost", 0)) for p in top_picks[:10]]
        chart_url = quickchart_sparkline_url(sample_values)
        chart_html = f'<p><img src="{chart_url}" alt="True cost trend" width="400" /></p>'

    return f"""<!DOCTYPE html>
<html>
<body>
<h1>AI Model Intelligence Briefing — {title_date}</h1>
<h2>This Week's Moves</h2>
<ul>
{moves_html}
</ul>
<h2>Top Value Picks</h2>
<table border="1">
  <tr><th>Model</th><th>Use Case</th><th>True Cost</th><th>Savings vs Leader</th></tr>
  {picks_rows}
</table>
{chart_html}
{watch_html}
</body>
</html>
"""
