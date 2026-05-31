"""Routing coverage after model_capabilities expansion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.fetch_prices import apply_capability_overrides  # noqa: E402
from backend.engine.generate_routing_config import generate_routing_config  # noqa: E402


def test_all_workloads_have_routes():
    prices = json.loads((ROOT / "data" / "current_prices.json").read_text())
    workloads = json.loads((ROOT / "data" / "workloads.json").read_text())["workloads"]
    models = apply_capability_overrides(prices["models"])

    config = generate_routing_config(models, workloads)
    route_ids = {route["workload_id"] for route in config["routes"]}
    expected = {workload["workload_id"] for workload in workloads}

    assert route_ids == expected
    assert len(config["routes"]) == 3
    for route in config["routes"]:
        assert len(route["models"]) >= 1
        weights = sum(entry["weight"] for entry in route["models"])
        assert abs(weights - 1.0) < 0.01


def test_model_capabilities_covers_all_priced_models():
    prices = json.loads((ROOT / "data" / "current_prices.json").read_text())
    capabilities = json.loads((ROOT / "data" / "model_capabilities.json").read_text())

    price_ids = {model["model_id"] for model in prices["models"]}
    capability_ids = {entry["model_id"] for entry in capabilities["models"]}

    assert capability_ids == price_ids
    assert len(capability_ids) == prices["model_count"]


def test_generate_routing_config_cli_writes_three_routes(tmp_path, monkeypatch):
    import backend.engine.generate_routing_config as routing_module

    output_path = tmp_path / "routing_config.yaml"
    monkeypatch.setattr(routing_module, "OUTPUT_PATH", output_path)

    assert routing_module.main() == 0
    config = yaml.safe_load(output_path.read_text())
    assert len(config["routes"]) == 3
