"""True cost and value score calculations for workload-aware model comparison."""

from __future__ import annotations

from typing import Any

BENCHMARK_WEIGHTS: dict[str, dict[str, float]] = {
    "coding": {"human_eval": 0.5, "mbpp": 0.3, "mmlu": 0.2},
    "reasoning": {"gsm8k": 0.4, "mmlu": 0.4, "bbh": 0.2},
    "general": {"mmlu": 0.6, "bbh": 0.3, "truthful_qa": 0.1},
}

WORKLOAD_TYPE_MAP = {
    "coding_assistant": "coding",
    "bulk_processing": "general",
    "customer_support": "general",
    "reasoning_tasks": "reasoning",
}


def _workload_type(workload: dict[str, Any]) -> str:
    explicit = workload.get("workload_type")
    if explicit:
        return explicit
    return WORKLOAD_TYPE_MAP.get(workload.get("workload_id", ""), "general")


def retry_rate_for_workload(model: dict[str, Any], workload: dict[str, Any]) -> float:
    characteristics = workload.get("characteristics", workload)
    return float(characteristics.get("retry_rate", 0.0))


def true_cost(model: dict[str, Any], workload: dict[str, Any]) -> float:
    """
    Compute effective cost per 1K output tokens for a model/workload pair.

    Applies amplification (token efficiency), retries, prompt caching, and batch discounts.
    """
    characteristics = workload.get("characteristics", workload)
    pricing = model.get("pricing", {})
    capabilities = model.get("capabilities", {})
    metadata = model.get("metadata", {})

    base = float(pricing.get("output_per_1m", 0.0))
    avg_output_tokens = float(characteristics.get("avg_output_tokens", 0.0))
    efficiency_ratio = float(metadata.get("efficiency_ratio", 1.0))
    amplification = (avg_output_tokens / 1000.0) * efficiency_ratio
    retry_mult = 1.0 + retry_rate_for_workload(model, workload)

    cache_hit_rate = float(characteristics.get("cache_hit_rate", 0.0))
    caching_eligible = bool(characteristics.get("caching_eligible", False))
    cache_mult = (1.0 - cache_hit_rate) if capabilities.get("caching") and caching_eligible else 1.0

    can_batch = bool(characteristics.get("can_batch", characteristics.get("batch_eligible", False)))
    batch_disc = 0.8 if capabilities.get("batch_api") and can_batch else 1.0

    if base <= 0 or avg_output_tokens <= 0:
        return 0.0

    # Cost per 1K output tokens after workload-specific adjustments.
    return (base * amplification * retry_mult * cache_mult * batch_disc) / 1000.0


def weighted_benchmark_score(model: dict[str, Any], workload: dict[str, Any]) -> float:
    weights = BENCHMARK_WEIGHTS.get(_workload_type(workload), BENCHMARK_WEIGHTS["general"])
    benchmarks = model.get("benchmarks", {})
    return sum(float(benchmarks.get(name, 0.0)) * weight for name, weight in weights.items())


def value_score(model: dict[str, Any], workload: dict[str, Any]) -> float:
    score = weighted_benchmark_score(model, workload)
    cost = true_cost(model, workload)
    return score / cost if cost > 0 else 0.0


def meets_quality_requirements(model: dict[str, Any], workload: dict[str, Any]) -> bool:
    characteristics = workload.get("characteristics", workload)
    requirements = characteristics.get("quality_requirements", {})
    capabilities = model.get("capabilities", {})
    benchmarks = model.get("benchmarks", {})

    min_score = requirements.get("min_benchmark_score")
    if min_score is not None and weighted_benchmark_score(model, workload) < float(min_score):
        return False
    if requirements.get("requires_json_mode") and not capabilities.get("json_mode"):
        return False
    if requirements.get("requires_function_calling") and not capabilities.get("function_calling"):
        return False
    if requirements.get("requires_vision") and not capabilities.get("vision"):
        return False

    for benchmark_name, minimum in requirements.items():
        if benchmark_name.startswith("min_") and benchmark_name.endswith("_score"):
            continue
        if benchmark_name in benchmarks and float(benchmarks[benchmark_name]) < float(minimum):
            return False

    return True
