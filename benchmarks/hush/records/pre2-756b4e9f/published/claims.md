# hush benchmark — generated claims

Generated from 12 retained run records · batch `pre2-756b4e9f` · model `sonnet` · seed `1786174006947` · arms: baseline, prenudge.

Segments: noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| noisy-output | baseline | 4 | 0.1828 | 0.1878 | 0.1784–0.1922 | 0.1686–0.2070 | — | — | — |
| noisy-output | prenudge | 4 | 0.2290 | 0.2280 | 0.2147–0.2423 | 0.2055–0.2504 | +25.2% | 0% | monorepo-build +22.9% |
| search-heavy | baseline | 2 | 0.6399 | 0.6399 | 0.6188–0.6609 | 0.5573–0.7224 | — | — | — |
| search-heavy | prenudge | 2 | 0.6306 | 0.6306 | 0.5842–0.6770 | 0.4487–0.8126 | -1.4% | 100% | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| noisy-output | baseline | 4 | 196789 | 204042 | 195885–204946 | 188089–219995 | — | — | — |
| noisy-output | prenudge | 4 | 257548 | 250108 | 248739–258916 | 233292–266923 | +30.9% | 0% | failing-suite +24.2% |
| search-heavy | baseline | 2 | 777738 | 777738 | 589743–965734 | 40796–1514680 | — | — | — |
| search-heavy | prenudge | 2 | 388313 | 388313 | 326319–450307 | 145297–631329 | -50.1% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| noisy-output | baseline | 4 | 1854 | 2264 | 1612–2506 | 1053–3474 | — | — | — |
| noisy-output | prenudge | 4 | 2222 | 2314 | 1322–3215 | 1056–3572 | +19.9% | 50% | monorepo-build +12.1% |
| search-heavy | baseline | 2 | 10388 | 10388 | 10235–10540 | 9791–10984 | — | — | — |
| search-heavy | prenudge | 2 | 10139 | 10139 | 10030–10248 | 9712–10566 | -2.4% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| noisy-output | baseline | 4 | 29 | 44 | 23–49 | 2–86 | — | — | — |
| noisy-output | prenudge | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 122 | 122 | 116–129 | 97–147 | — | — | — |
| search-heavy | prenudge | 2 | 22 | 22 | 16–29 | -3–47 | -82.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 6 | 0.3385 | 0.2000 | 395274 | 100% | 36 |
| prenudge | 6 | 0.3622 | 0.2459 | 296176 | 100% | 44 |
