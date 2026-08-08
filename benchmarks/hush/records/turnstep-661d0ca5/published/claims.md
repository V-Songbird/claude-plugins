# hush benchmark — generated claims

Generated from 24 retained run records · batch `turnstep-661d0ca5` · model `sonnet` · seed `1786172329502` · arms: baseline, turnstep.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.5163 | 0.4987 | 0.4292–0.5667 | 0.4319–0.5655 | — | — | — |
| long-session | turnstep | 6 | 0.5904 | 0.5918 | 0.5765–0.6003 | 0.5769–0.6068 | +14.4% | 0% | feature-drift +30.1% |
| noisy-output | baseline | 4 | 0.1851 | 0.1837 | 0.1807–0.1882 | 0.1756–0.1918 | — | — | — |
| noisy-output | turnstep | 4 | 0.1975 | 0.2035 | 0.1915–0.2096 | 0.1841–0.2229 | +6.7% | 0% | failing-suite +19.3% |
| search-heavy | baseline | 2 | 0.6566 | 0.6566 | 0.6035–0.7098 | 0.4483–0.8650 | — | — | — |
| search-heavy | turnstep | 2 | 0.6007 | 0.6007 | 0.5889–0.6126 | 0.5544–0.6471 | -8.5% | 100% | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 717761 | 708541 | 629039–859727 | 565562–851521 | — | — | — |
| long-session | turnstep | 6 | 707656 | 677383 | 675295–726051 | 611038–743728 | -1.4% | 67% | feature-drift +10.7% |
| noisy-output | baseline | 4 | 195003 | 203888 | 194750–204141 | 186133–221643 | — | — | — |
| noisy-output | turnstep | 4 | 215771 | 235467 | 215728–235510 | 196764–274171 | +10.7% | 0% | failing-suite +19.9% |
| search-heavy | baseline | 2 | 844931 | 844931 | 590005–1099858 | -154381–1844243 | — | — | — |
| search-heavy | turnstep | 2 | 337536 | 337536 | 335917–339155 | 331190–343882 | -60.1% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 7394 | 7610 | 5255–10299 | 5264–9957 | — | — | — |
| long-session | turnstep | 6 | 7175 | 7709 | 4620–10648 | 4385–11033 | -3.0% | 67% | feature-drift +69.6% |
| noisy-output | baseline | 4 | 2030 | 2064 | 1346–2748 | 1240–2887 | — | — | — |
| noisy-output | turnstep | 4 | 1450 | 1495 | 1283–1661 | 1083–1906 | -28.6% | 100% | — |
| search-heavy | baseline | 2 | 10407 | 10407 | 10178–10635 | 9512–11301 | — | — | — |
| search-heavy | turnstep | 2 | 9985 | 9985 | 9960–10010 | 9887–10083 | -4.1% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 20 | 67 | 5–61 | -22–155 | — | — | — |
| long-session | turnstep | 6 | 0 | 8 | 0–14 | -3–19 | -100.0% | 67% | incident-forensics +52.4% |
| noisy-output | baseline | 4 | 68 | 62 | 56–74 | 43–81 | — | — | — |
| noisy-output | turnstep | 4 | 8 | 10 | 0–18 | -2–23 | -89.0% | 100% | — |
| search-heavy | baseline | 2 | 114 | 114 | 104–125 | 73–155 | — | — | — |
| search-heavy | turnstep | 2 | 45 | 45 | 45–45 | 45–45 | -60.5% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4200 | 0.4509 | 563055 | 100% | 80 |
| turnstep | 12 | 0.4639 | 0.5761 | 473437 | 100% | 77 |
