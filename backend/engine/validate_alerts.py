"""Alert validation logic for meaningful price and value shifts."""

from __future__ import annotations

from typing import Any

from backend.engine.calculate_true_cost import (
    true_cost,
    value_score,
    weighted_benchmark_score,
)


def quality_delta_from_baseline(
    model: dict[str, Any],
    baseline_model: dict[str, Any],
    workload: dict[str, Any],
) -> float:
    """Return quality change in percentage points (positive = improvement)."""
    current = weighted_benchmark_score(model, workload)
    baseline = weighted_benchmark_score(baseline_model, workload)
    if baseline <= 0:
        return 0.0
    return ((current - baseline) / baseline) * 100.0


def is_new_model(model: dict[str, Any], known_model_ids: set[str]) -> bool:
    return model.get("model_id") not in known_model_ids


def find_leader(models: list[dict[str, Any]], workload: dict[str, Any]) -> dict[str, Any] | None:
    eligible = [model for model in models if model.get("model_id")]
    if not eligible:
        return None
    return max(eligible, key=lambda model: value_score(model, workload))


def should_alert(
    model: dict[str, Any],
    baseline: dict[str, Any],
    current_leader: dict[str, Any],
    workload: dict[str, Any],
    *,
    known_model_ids: set[str] | None = None,
    price_drop_threshold_pct: float = 15.0,
    quality_floor_pct: float = -5.0,
    new_model_value_multiplier: float = 1.2,
) -> dict[str, Any]:
    baseline_cost = true_cost(baseline, workload)
    current_cost = true_cost(model, workload)
    if baseline_cost <= 0:
        return {"trigger": False, "reason": "invalid_baseline"}

    pct_change = ((current_cost - baseline_cost) / baseline_cost) * 100.0
    qual_change = quality_delta_from_baseline(model, baseline, workload)

    if pct_change <= -price_drop_threshold_pct and qual_change >= quality_floor_pct:
        priority = "critical" if pct_change <= -25 else "high"
        return {
            "trigger": True,
            "priority": priority,
            "reason": "significant_price_drop",
            "pct_change": round(pct_change, 2),
            "quality_delta_pct": round(qual_change, 2),
            "true_cost": round(current_cost, 4),
            "baseline_true_cost": round(baseline_cost, 4),
        }

    leader_score = value_score(current_leader, workload)
    candidate_score = value_score(model, workload)
    if (
        known_model_ids is not None
        and is_new_model(model, known_model_ids)
        and leader_score > 0
        and candidate_score > new_model_value_multiplier * leader_score
    ):
        return {
            "trigger": True,
            "priority": "high",
            "reason": "new_market_entry",
            "value_score": round(candidate_score, 4),
            "leader_value_score": round(leader_score, 4),
        }

    return {"trigger": False, "reason": "no_action", "pct_change": round(pct_change, 2)}


def scan_for_alerts(
    models: list[dict[str, Any]],
    baselines: dict[str, Any],
    workloads: list[dict[str, Any]],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    known_model_ids = set(baselines.get("model_ids", []))
    baseline_models = {
        entry["model_id"]: entry
        for entry in baselines.get("snapshots", [])
    }
    alerts: list[dict[str, Any]] = []

    price_drop_threshold = float(rules.get("price_drop_threshold_pct", 15))
    quality_floor = float(rules.get("quality_degradation_max_pct", -5))
    new_model_multiplier = float(rules.get("new_model_value_multiplier", 1.2))

    for workload in workloads:
        leader = find_leader(models, workload)
        if not leader:
            continue

        for model in models:
            baseline = baseline_models.get(model["model_id"])
            if not baseline:
                continue

            decision = should_alert(
                model,
                baseline,
                leader,
                workload,
                known_model_ids=known_model_ids,
                price_drop_threshold_pct=price_drop_threshold,
                quality_floor_pct=quality_floor,
                new_model_value_multiplier=new_model_multiplier,
            )
            if decision.get("trigger"):
                alerts.append(
                    {
                        "model_id": model["model_id"],
                        "display_name": model.get("display_name", model["model_id"]),
                        "workload_id": workload.get("workload_id"),
                        "workload_name": workload.get("name"),
                        **decision,
                    }
                )

    return alerts
