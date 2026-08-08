# hush benchmark — generated claims

Generated from 6 retained run records · batch `prenudge-5d07dcbc` · model `sonnet` · seed `1786171915528` · arms: prenudge.

Segments: long-session.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | prenudge | 6 | 0.6588 | 0.6663 | 0.6447–0.7065 | 0.6183–0.7144 | — | — | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | prenudge | 6 | 765442 | 789924 | 705183–875642 | 691240–888608 | — | — | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | prenudge | 6 | 7526 | 6925 | 4674–8319 | 4855–8996 | — | — | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | prenudge | 6 | 0 | 0 | 0–0 | 0–0 | — | — | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| prenudge | 6 | 0.6663 | 0.6588 | 789924 | 100% | 126 |
