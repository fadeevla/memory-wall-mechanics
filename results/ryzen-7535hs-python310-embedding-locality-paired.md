# Paired embedding-locality analysis

Each effect pairs the random and sorted-within-bag median for the same data
seed. A ratio above 1 means sorting was slower. The interval bootstraps the
paired ratios, rather than comparing two marginal confidence intervals.

| Implementation | Seeds | Median change | Ratio 95% CI | Direction detected |
| --- | ---: | ---: | ---: | --- |
| `numba_fused` | 15 | +2.04% | [0.994, 1.060] | no |
| `numpy_gather_reduce` | 15 | +6.23% | [1.048, 1.084] | yes |
| `python_loops` | 15 | +2.32% | [1.022, 1.035] | yes |
| `torch_embedding_bag` | 15 | +1.00% | [0.976, 1.117] | no |

A non-detection means this experiment did not resolve a directional effect;
it is not evidence that the true effect is exactly zero.
