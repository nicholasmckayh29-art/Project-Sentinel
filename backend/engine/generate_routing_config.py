"""Generate opinionated routing_config.yaml (Routine 3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engine.calculate_true_cost import meets_quality_requirements, true_cost, value_score  # noqa: E402
from backend.engine.fetch_prices import apply_capability_overrides  # noqa: E402

DATA_DIR = ROOT / "data"
OUTPUT_PATH = ROOT / "routing_config.yaml"

TIER_DEFAULTS = {
    "tier_1_critical": {"top_n": 2, "primary_weight": 0.7},
    "tier_2_standard": {"top_n": 2, "primary_weight": 0.6},
    "tier_3_bulk": {"top_n": 2, "primary_weight": 0.8},
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def rank_models_for_workload(models: list[dict[str, Any]], workload: dict[str, Any]) -> list[dict[str, Any]]:
    eligible = [model for model in models if meets_quality_requirements(model, workload)]
    ranked = sorted(eligible, key=lambda model: value_score(model, workload), reverse=True)
    return ranked


def build_route(workload: dict[str, Any], ranked: list[dict[str, Any]]) -> dict[str, Any]:
    tier = workload.get("tier", "tier_2_standard")
    defaults = TIER_DEFAULTS.get(tier, TIER_DEFAULTS["tier_2_standard"])
    top = ranked[: defaults["top_n"]]
    if not top:
        return {}

    primary_weight = defaults["primary_weight"]
    models = [{"model": top[0]["model_id"], "weight": round(primary_weight, 2)}]
    if len(top) > 1:
        models.append({"model": top[1]["model_id"], "weight": round(1.0 - primary_weight, 2)})

    characteristics = workload.get("characteristics", workload)
    return {
        "name": workload.get("name", workload.get("workload_id")),
        "workload_id": workload.get("workload_id"),
        "models": models,
        "caching": bool(characteristics.get("caching_eligible", False)),
        "max_retries": 2,
    }


def project_savings(models: list[dict[str, Any]], workloads: list[dict[str, Any]]) -> dict[str, float]:
    current_spend = 0.0
    optimized_spend = 0.0

    for workload in workloads:
        characteristics = workload.get("characteristics", workload)
        daily_volume = float(characteristics.get("daily_volume", 0))
        avg_output = float(characteristics.get("avg_output_tokens", 0))
        monthly_tokens = daily_volume * avg_output * 30

        ranked = rank_models_for_workload(models, workload)
        if not ranked:
            continue

        current_leader = max(ranked, key=lambda model: true_cost(model, workload))
        best = ranked[0]
        current_spend += (monthly_tokens / 1000.0) * true_cost(current_leader, workload)
        optimized_spend += (monthly_tokens / 1000.0) * true_cost(best, workload)

    savings = current_spend - optimized_spend
    pct = (savings / current_spend * 100.0) if current_spend else 0.0
    return {
        "current_monthly_spend_usd": round(current_spend, 2),
        "optimized_monthly_spend_usd": round(optimized_spend, 2),
        "projected_savings_usd": round(savings, 2),
        "projected_savings_pct": round(pct, 2),
    }


def generate_routing_config(models: list[dict[str, Any]], workloads: list[dict[str, Any]]) -> dict[str, Any]:
    routes = []
    for workload in workloads:
        ranked = rank_models_for_workload(models, workload)
        route = build_route(workload, ranked)
        if route:
            routes.append(route)

    return {
        "routes": routes,
        "projections": project_savings(models, workloads),
    }


def write_routing_config(config: dict[str, Any], output_path: Path | None = None) -> Path:
    path = output_path or OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    return path


def load_routing_config(output_path: Path | None = None) -> dict[str, Any] | None:
    path = output_path or OUTPUT_PATH
    if not path.exists():
        return None
    with path.open() as handle:
        return yaml.safe_load(handle)


def build_routing_config(
    prices_path: Path = DATA_DIR / "current_prices.json",
    workloads_path: Path = DATA_DIR / "workloads.json",
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Generate routing config from current prices and write to disk."""
    path = output_path or OUTPUT_PATH
    prices = _load_json(prices_path)
    workloads_payload = _load_json(workloads_path)
    models = apply_capability_overrides(prices.get("models", []))
    workloads = workloads_payload.get("workloads", [])
    config = generate_routing_config(models, workloads)
    write_routing_config(config, path)
    return config


def get_routing_config(output_path: Path | None = None) -> dict[str, Any]:
    """Return routing config from disk, generating it if missing."""
    path = output_path or OUTPUT_PATH
    config = load_routing_config(path)
    if config is not None:
        return config
    return build_routing_config(output_path=path)


def main() -> int:
    config = build_routing_config()
    print(json.dumps({"status": "ok", "route_count": len(config["routes"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
