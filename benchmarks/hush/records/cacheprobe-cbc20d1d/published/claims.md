# hush benchmark — generated claims

Generated from 12 retained run records · batch `cacheprobe-cbc20d1d` · model `sonnet` · seed `1786151075446` · arms: baseline, hush, nonudge.

Segments: long-session.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 4 | 0.6457 | 0.5922 | 0.5640–0.6740 | 0.4547–0.7298 | — | — | — |
| long-session | hush | 4 | 0.7969 | 0.8516 | 0.7241–0.9244 | 0.6824–1.0207 | +23.4% | 0% | marathon-audit +44.1% |
| long-session | nonudge | 4 | 0.5261 | 0.5278 | 0.5212–0.5327 | 0.5128–0.5427 | -18.5% | 50% | feature-drift +2.6% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 4 | 756799 | 702736 | 639417–820118 | 483096–922376 | — | — | — |
| long-session | hush | 4 | 882671 | 885759 | 863669–904761 | 826381–945136 | +16.6% | 0% | feature-drift +30.6% |
| long-session | nonudge | 4 | 753542 | 771268 | 723575–801236 | 659423–883114 | -0.4% | 0% | marathon-audit +11.4% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 4 | 11006 | 10956 | 9979–11983 | 9411–12500 | — | — | — |
| long-session | hush | 4 | 11645 | 12709 | 11364–12990 | 9970–15447 | +5.8% | 0% | marathon-audit +29.7% |
| long-session | nonudge | 4 | 8946 | 8797 | 8113–9629 | 7793–9800 | -18.7% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 4 | 31 | 32 | 21–42 | 5–59 | — | — | — |
| long-session | hush | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| long-session | nonudge | 4 | 0 | 5 | 0–5 | -5–14 | -100.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 4 | 0.5922 | 0.6457 | 702736 | 100% | 138 |
| hush | 4 | 0.8516 | 0.7969 | 885759 | 100% | 161 |
| nonudge | 4 | 0.5278 | 0.5261 | 771268 | 100% | 130 |
