# True Cost Formula

The platform uses **True Cost** — not raw token list prices — to compare models for a specific workload.

## Formula

```
TrueCost = (output_per_1m × amplification × retry_mult × cache_mult × batch_disc) / 1000
```

Where:

| Variable | Meaning |
|----------|---------|
| `output_per_1m` | Provider list price for 1M output tokens (USD) |
| `amplification` | `(avg_output_tokens / 1000) × efficiency_ratio` |
| `retry_mult` | `1 + retry_rate` for the workload |
| `cache_mult` | `1 - cache_hit_rate` when model supports caching and workload is eligible; else `1.0` |
| `batch_disc` | `0.8` when batch API is supported and workload allows batching; else `1.0` |

Result is **USD per 1K output tokens** after workload-specific adjustments.

## Value Score

```
ValueScore = WeightedBenchmarkScore / TrueCost
```

Benchmark weights vary by workload type (`coding`, `reasoning`, `general`).

## Alert Thresholds

Alerts fire when:

1. True Cost drops **≥15%** vs baseline with quality degradation **≤5%**, or
2. A new model's Value Score exceeds the incumbent by **≥20%**.

See `config/threshold_rules.json` for tunable parameters.
