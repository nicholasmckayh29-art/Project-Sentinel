"""Tests for true cost and alert validation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.calculate_true_cost import true_cost, value_score, weighted_benchmark_score
from backend.engine.validate_alerts import should_alert


CLAUDE_SONNET = {
    "model_id": "claude-sonnet-4-6",
    "pricing": {"output_per_1m": 15.0},
    "capabilities": {"caching": True, "batch_api": True, "json_mode": True, "function_calling": True},
    "benchmarks": {"mmlu": 0.88, "human_eval": 0.82, "mbpp": 0.85},
    "metadata": {"efficiency_ratio": 1.0},
}

GPT4O_MINI = {
    "model_id": "gpt-4o-mini",
    "pricing": {"output_per_1m": 0.6},
    "capabilities": {"caching": True, "batch_api": True, "json_mode": True, "function_calling": True},
    "benchmarks": {"mmlu": 0.82, "human_eval": 0.75, "mbpp": 0.72},
    "metadata": {"efficiency_ratio": 1.1},
}

HAIKU = {
    "model_id": "claude-haiku-4-5-20251001",
    "pricing": {"output_per_1m": 5.0},
    "capabilities": {"caching": True, "batch_api": True, "json_mode": True, "function_calling": True},
    "benchmarks": {"mmlu": 0.75, "human_eval": 0.70, "mbpp": 0.68},
    "metadata": {"efficiency_ratio": 1.05},
}

CODING_WORKLOAD = {
    "workload_id": "coding_assistant",
    "workload_type": "coding",
    "characteristics": {
        "avg_output_tokens": 500,
        "retry_rate": 0.05,
        "caching_eligible": True,
        "cache_hit_rate": 0.40,
        "can_batch": False,
    },
}


def test_true_cost_applies_caching_and_retries():
    cost = true_cost(CLAUDE_SONNET, CODING_WORKLOAD)
    # 15 * 0.5 * 1.05 * 0.6 / 1000 = 0.004725
    assert abs(cost - 0.004725) < 1e-6


def test_cheaper_model_has_lower_true_cost():
    sonnet = true_cost(CLAUDE_SONNET, CODING_WORKLOAD)
    mini = true_cost(GPT4O_MINI, CODING_WORKLOAD)
    assert mini < sonnet


def test_value_score_ranks_quality_per_dollar():
    sonnet_score = value_score(CLAUDE_SONNET, CODING_WORKLOAD)
    mini_score = value_score(GPT4O_MINI, CODING_WORKLOAD)
    assert mini_score > sonnet_score


def test_weighted_benchmark_for_coding():
    score = weighted_benchmark_score(CLAUDE_SONNET, CODING_WORKLOAD)
    expected = 0.82 * 0.5 + 0.85 * 0.3 + 0.88 * 0.2
    assert abs(score - expected) < 1e-6


def test_should_alert_on_significant_price_drop():
    baseline = {**HAIKU, "pricing": {"output_per_1m": 10.0}}
    current = {**HAIKU, "pricing": {"output_per_1m": 5.0}}
    leader = CLAUDE_SONNET
    result = should_alert(current, baseline, leader, CODING_WORKLOAD)
    assert result["trigger"] is True
    assert result["reason"] == "significant_price_drop"
    assert result["pct_change"] <= -15


def test_no_alert_when_change_is_noise():
    baseline = {**GPT4O_MINI, "pricing": {"output_per_1m": 0.60}}
    current = {**GPT4O_MINI, "pricing": {"output_per_1m": 0.58}}
    result = should_alert(current, baseline, CLAUDE_SONNET, CODING_WORKLOAD)
    assert result["trigger"] is False
