# hush benchmark — generated claims

Generated from 102 retained run records · batch `claims2-haiku-55fd2b8b` · model `haiku` · seed `1785984308646` · arms: baseline, hush.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.0174 | 0.0270 | 0.0169–0.0268 | 0.0169–0.0371 | — | — | — |
| coding | hush | 12 | 0.0227 | 0.0321 | 0.0225–0.0307 | 0.0221–0.0421 | +30.6% | 0% | explain-rebase +35.4% |
| debugging | baseline | 18 | 0.0656 | 0.0815 | 0.0487–0.1054 | 0.0623–0.1007 | — | — | — |
| debugging | hush | 18 | 0.0652 | 0.0636 | 0.0502–0.0748 | 0.0556–0.0716 | -0.6% | 67% | bugfix-expiry +18.3% |
| doc-editing | baseline | 3 | 0.0519 | 0.0520 | 0.0490–0.0550 | 0.0453–0.0588 | — | — | — |
| doc-editing | hush | 3 | 0.0753 | 0.0762 | 0.0745–0.0775 | 0.0727–0.0797 | +45.0% | 0% | runbook-edit +45.0% |
| noisy-output | baseline | 12 | 0.0599 | 0.0594 | 0.0486–0.0729 | 0.0526–0.0661 | — | — | — |
| noisy-output | hush | 12 | 0.0504 | 0.0481 | 0.0325–0.0618 | 0.0393–0.0569 | -15.9% | 50% | noisy-build +18.6% |
| search-heavy | baseline | 6 | 0.0277 | 0.0299 | 0.0209–0.0361 | 0.0214–0.0383 | — | — | — |
| search-heavy | hush | 6 | 0.0343 | 0.0362 | 0.0277–0.0400 | 0.0276–0.0448 | +23.8% | 0% | call-site-sweep +32.2% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 21214 | 66721 | 21210–63962 | 19966–113476 | — | — | — |
| coding | hush | 12 | 23915 | 65692 | 23911–57716 | 22205–109179 | +12.7% | 25% | write-validator +12.7% |
| debugging | baseline | 18 | 237883 | 246046 | 186506–308958 | 208488–283604 | — | — | — |
| debugging | hush | 18 | 222601 | 205004 | 156010–239429 | 181312–228696 | -6.4% | 83% | coupon-currency-flaky +8.3% |
| doc-editing | baseline | 3 | 191935 | 192801 | 179315–205855 | 162756–222846 | — | — | — |
| doc-editing | hush | 3 | 246054 | 239367 | 235613–246465 | 225448–253286 | +28.2% | 0% | runbook-edit +28.2% |
| noisy-output | baseline | 12 | 108887 | 125642 | 65126–201264 | 86649–164635 | — | — | — |
| noisy-output | hush | 12 | 134279 | 151313 | 75388–241531 | 100363–202262 | +23.3% | 25% | noisy-build +38.9% |
| search-heavy | baseline | 6 | 65871 | 88385 | 43129–104962 | 38391–138380 | — | — | — |
| search-heavy | hush | 6 | 74051 | 87578 | 48599–99745 | 46061–129095 | +12.4% | 50% | call-site-sweep +12.7% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 655 | 1166 | 560–1228 | 586–1746 | — | — | — |
| coding | hush | 12 | 642 | 1075 | 603–1107 | 591–1558 | -2.0% | 75% | explain-rebase +21.3% |
| debugging | baseline | 18 | 2738 | 2717 | 1944–2977 | 2292–3143 | — | — | — |
| debugging | hush | 18 | 2458 | 2383 | 1719–2732 | 1984–2781 | -10.2% | 100% | — |
| doc-editing | baseline | 3 | 2490 | 2461 | 2241–2696 | 1946–2977 | — | — | — |
| doc-editing | hush | 3 | 3155 | 3563 | 3041–3882 | 2530–4596 | +26.7% | 0% | runbook-edit +26.7% |
| noisy-output | baseline | 12 | 1606 | 1531 | 1054–2136 | 1209–1853 | — | — | — |
| noisy-output | hush | 12 | 1553 | 1461 | 783–2046 | 1082–1840 | -3.3% | 50% | noisy-build +24.2% |
| search-heavy | baseline | 6 | 1176 | 1129 | 651–1608 | 704–1553 | — | — | — |
| search-heavy | hush | 6 | 1241 | 1252 | 856–1419 | 829–1675 | +5.6% | 50% | call-site-sweep +26.9% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 25 | 0–22 | -1–50 | — | — | — |
| coding | hush | 12 | 0 | 0 | 0–0 | 0–0 | — | 100% | — |
| debugging | baseline | 18 | 107 | 109 | 81–152 | 80–138 | — | — | — |
| debugging | hush | 18 | 0 | 4 | 0–0 | -2–9 | -100.0% | 100% | — |
| doc-editing | baseline | 3 | 10 | 13 | 5–20 | -4–30 | — | — | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 12 | 46 | 51 | 11–96 | 25–77 | — | — | — |
| noisy-output | hush | 12 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 6 | 17 | 17 | 15–19 | 13–21 | — | — | — |
| search-heavy | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.0557 | 0.0513 | 153841 | 98% | 30 |
| hush | 51 | 0.0501 | 0.0512 | 147798 | 92% | 32 |
