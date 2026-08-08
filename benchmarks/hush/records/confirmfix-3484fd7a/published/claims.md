# hush benchmark — generated claims

Generated from 24 retained run records · batch `confirmfix-3484fd7a` · model `sonnet` · seed `1786153613114` · arms: baseline, hush.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.6034 | 0.6114 | 0.4996–0.6926 | 0.4673–0.7555 | — | — | — |
| long-session | hush | 6 | 0.5913 | 0.6218 | 0.5503–0.7162 | 0.5214–0.7223 | -2.0% | 33% | feature-drift +30.2% |
| noisy-output | baseline | 4 | 0.1699 | 0.1727 | 0.1680–0.1746 | 0.1650–0.1803 | — | — | — |
| noisy-output | hush | 4 | 0.2088 | 0.2086 | 0.2074–0.2100 | 0.2064–0.2108 | +22.9% | 0% | monorepo-build +23.4% |
| search-heavy | baseline | 2 | 0.6631 | 0.6631 | 0.6029–0.7234 | 0.4271–0.8992 | — | — | — |
| search-heavy | hush | 2 | 0.6008 | 0.6008 | 0.5988–0.6028 | 0.5928–0.6088 | -9.4% | 100% | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 782947 | 733120 | 612295–920764 | 546042–920197 | — | — | — |
| long-session | hush | 6 | 764872 | 735686 | 626716–887411 | 566989–904383 | -2.3% | 67% | feature-drift +48.2% |
| noisy-output | baseline | 4 | 197729 | 204824 | 193190–209364 | 187156–222493 | — | — | — |
| noisy-output | hush | 4 | 234095 | 235425 | 216111–253409 | 213432–257418 | +18.4% | 0% | failing-suite +17.6% |
| search-heavy | baseline | 2 | 892911 | 892911 | 609991–1175830 | -216135–2001956 | — | — | — |
| search-heavy | hush | 2 | 365748 | 365748 | 317709–413788 | 177433–554063 | -59.0% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 10336 | 9281 | 5994–11917 | 6204–12357 | — | — | — |
| long-session | hush | 6 | 6532 | 6904 | 4920–7953 | 4532–9276 | -36.8% | 100% | — |
| noisy-output | baseline | 4 | 1589 | 1550 | 1350–1789 | 1255–1844 | — | — | — |
| noisy-output | hush | 4 | 1717 | 1746 | 1216–2246 | 1133–2358 | +8.0% | 50% | monorepo-build +26.9% |
| search-heavy | baseline | 2 | 10587 | 10587 | 10281–10894 | 9386–11788 | — | — | — |
| search-heavy | hush | 2 | 10936 | 10936 | 10451–11420 | 9037–12834 | +3.3% | 0% | repo-sweep +3.3% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 25 | 41 | 13–38 | -2–84 | — | — | — |
| long-session | hush | 6 | 0 | 2 | 0–5 | -1–5 | -100.0% | 100% | — |
| noisy-output | baseline | 4 | 46 | 42 | 39–49 | 30–54 | — | — | — |
| noisy-output | hush | 4 | 0 | 4 | 0–4 | -4–13 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 113 | 113 | 108–117 | 96–129 | — | — | — |
| search-heavy | hush | 2 | 25 | 25 | 17–32 | -4–53 | -78.2% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4738 | 0.5114 | 583653 | 100% | 82 |
| hush | 12 | 0.4806 | 0.5622 | 507276 | 100% | 85 |
