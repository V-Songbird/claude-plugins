# hush benchmark — generated claims

Generated from 170 retained run records · batch `claims2-sonnet-4c486329` · model `sonnet` · seed `1785982759651` · arms: baseline, hush.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 20 | 0.0680 | 0.1073 | 0.0608–0.1447 | 0.0777–0.1368 | — | — | — |
| coding | hush | 20 | 0.0820 | 0.1189 | 0.0782–0.1324 | 0.0923–0.1456 | +20.7% | 50% | explain-rebase +36.0% |
| debugging | baseline | 30 | 0.1550 | 0.2198 | 0.1263–0.3153 | 0.1750–0.2647 | — | — | — |
| debugging | hush | 30 | 0.1716 | 0.2108 | 0.1483–0.2070 | 0.1752–0.2464 | +10.7% | 33% | bugfix-pagination +27.3% |
| doc-editing | baseline | 5 | 0.2452 | 0.2349 | 0.2256–0.2456 | 0.2183–0.2515 | — | — | — |
| doc-editing | hush | 5 | 0.2676 | 0.2887 | 0.2671–0.2715 | 0.2461–0.3314 | +9.1% | 0% | runbook-edit +9.1% |
| noisy-output | baseline | 20 | 0.2211 | 0.2233 | 0.1775–0.2741 | 0.2002–0.2464 | — | — | — |
| noisy-output | hush | 20 | 0.1810 | 0.1817 | 0.1614–0.2022 | 0.1690–0.1944 | -18.2% | 100% | — |
| search-heavy | baseline | 10 | 0.1288 | 0.1320 | 0.1228–0.1385 | 0.1253–0.1387 | — | — | — |
| search-heavy | hush | 10 | 0.1486 | 0.1449 | 0.1373–0.1533 | 0.1380–0.1519 | +15.3% | 0% | repo-summary +18.3% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 20 | 42397 | 122237 | 28136–178038 | 61642–182832 | — | — | — |
| coding | hush | 20 | 31702 | 96667 | 31701–123132 | 49168–144167 | -25.2% | 50% | explain-rerender +12.7% |
| debugging | baseline | 30 | 198534 | 245672 | 150926–280515 | 200611–290733 | — | — | — |
| debugging | hush | 30 | 203393 | 241847 | 170196–247917 | 203835–279858 | +2.4% | 33% | bugfix-pagination +12.9% |
| doc-editing | baseline | 5 | 413642 | 387430 | 351985–413823 | 354866–419993 | — | — | — |
| doc-editing | hush | 5 | 388494 | 409547 | 387302–390188 | 350980–468114 | -6.1% | 100% | — |
| noisy-output | baseline | 20 | 195638 | 189083 | 138480–218948 | 155872–222294 | — | — | — |
| noisy-output | hush | 20 | 202013 | 202860 | 165277–240627 | 180948–224772 | +3.3% | 25% | sidecar-follow +67.1% |
| search-heavy | baseline | 10 | 118780 | 128091 | 116218–131490 | 117236–138947 | — | — | — |
| search-heavy | hush | 10 | 132161 | 139083 | 131173–157958 | 125505–152662 | +11.3% | 0% | call-site-sweep +24.7% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 20 | 695 | 1197 | 576–2104 | 814–1579 | — | — | — |
| coding | hush | 20 | 549 | 1021 | 314–2166 | 611–1431 | -21.0% | 75% | explain-rebase +4.8% |
| debugging | baseline | 30 | 1635 | 1965 | 908–2634 | 1549–2382 | — | — | — |
| debugging | hush | 30 | 1377 | 1512 | 710–1765 | 1202–1822 | -15.8% | 83% | bugfix-pagination +1.2% |
| doc-editing | baseline | 5 | 2866 | 2788 | 2863–2920 | 2446–3130 | — | — | — |
| doc-editing | hush | 5 | 2302 | 2597 | 2178–2437 | 1944–3249 | -19.7% | 100% | — |
| noisy-output | baseline | 20 | 1666 | 1527 | 1131–2038 | 1269–1785 | — | — | — |
| noisy-output | hush | 20 | 1087 | 1213 | 850–1664 | 1023–1403 | -34.8% | 75% | sidecar-follow +19.4% |
| search-heavy | baseline | 10 | 1396 | 1366 | 927–1798 | 1013–1719 | — | — | — |
| search-heavy | hush | 10 | 1424 | 1368 | 1053–1521 | 1110–1625 | +2.0% | 50% | call-site-sweep +53.8% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 20 | 0 | 16 | 0–12 | 3–28 | — | — | — |
| coding | hush | 20 | 0 | 2 | 0–0 | -1–4 | — | 100% | — |
| debugging | baseline | 30 | 40 | 72 | 19–121 | 42–102 | — | — | — |
| debugging | hush | 30 | 0 | 1 | 0–0 | -0–3 | -100.0% | 100% | — |
| doc-editing | baseline | 5 | 0 | 9 | 0–20 | -2–21 | — | — | — |
| doc-editing | hush | 5 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | baseline | 20 | 24 | 36 | 0–68 | 18–53 | — | — | — |
| noisy-output | hush | 20 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 10 | 27 | 26 | 21–38 | 16–35 | — | — | — |
| search-heavy | hush | 10 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 85 | 0.1847 | 0.1687 | 197819 | 98% | 25 |
| hush | 85 | 0.1792 | 0.1616 | 196289 | 98% | 25 |
