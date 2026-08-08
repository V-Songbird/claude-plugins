# hush benchmark — generated claims

Generated from 48 retained run records · batch `turnword-6550a7d9` · model `sonnet` · seed `1786174781150` · arms: baseline, turncur, turnfin, turnshort.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.5551 | 0.5562 | 0.4323–0.6403 | 0.4322–0.6802 | — | — | — |
| long-session | turncur | 6 | 0.5596 | 0.6073 | 0.5318–0.7106 | 0.4736–0.7410 | +0.8% | 33% | feature-drift +60.6% |
| long-session | turnfin | 6 | 0.6192 | 0.6157 | 0.6076–0.6499 | 0.5326–0.6987 | +11.5% | 0% | feature-drift +17.1% |
| long-session | turnshort | 6 | 0.5739 | 0.5863 | 0.5092–0.6575 | 0.5153–0.6573 | +3.4% | 33% | feature-drift +14.8% |
| noisy-output | baseline | 4 | 0.1890 | 0.1952 | 0.1847–0.1995 | 0.1740–0.2164 | — | — | — |
| noisy-output | turncur | 4 | 0.2026 | 0.2120 | 0.1959–0.2187 | 0.1867–0.2372 | +7.2% | 0% | monorepo-build +9.9% |
| noisy-output | turnfin | 4 | 0.1934 | 0.1941 | 0.1878–0.1996 | 0.1795–0.2086 | +2.3% | 50% | failing-suite +7.9% |
| noisy-output | turnshort | 4 | 0.2083 | 0.2358 | 0.1895–0.2545 | 0.1664–0.3051 | +10.2% | 50% | failing-suite +49.5% |
| search-heavy | baseline | 2 | 0.6884 | 0.6884 | 0.6133–0.7636 | 0.3939–0.9830 | — | — | — |
| search-heavy | turncur | 2 | 0.8811 | 0.8811 | 0.8732–0.8890 | 0.8502–0.9120 | +28.0% | 0% | repo-sweep +28.0% |
| search-heavy | turnfin | 2 | 0.6434 | 0.6434 | 0.5943–0.6925 | 0.4508–0.8360 | -6.5% | 100% | — |
| search-heavy | turnshort | 2 | 0.6442 | 0.6442 | 0.6387–0.6496 | 0.6229–0.6654 | -6.4% | 100% | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 793328 | 777383 | 682536–873037 | 553904–1000862 | — | — | — |
| long-session | turncur | 6 | 767392 | 849284 | 600969–861561 | 520772–1177797 | -3.3% | 67% | feature-drift +108.7% |
| long-session | turnfin | 6 | 762744 | 740170 | 724618–801554 | 653389–826950 | -3.9% | 33% | feature-drift +12.3% |
| long-session | turnshort | 6 | 728797 | 734544 | 706575–763883 | 709422–759666 | -8.1% | 67% | feature-drift +20.5% |
| noisy-output | baseline | 4 | 232660 | 226020 | 222651–236029 | 204059–247981 | — | — | — |
| noisy-output | turncur | 4 | 216675 | 258940 | 215826–259789 | 174690–343190 | -6.9% | 50% | monorepo-build +37.3% |
| noisy-output | turnfin | 4 | 213049 | 214916 | 202084–225881 | 183220–246612 | -8.4% | 50% | failing-suite +1.4% |
| noisy-output | turnshort | 4 | 247001 | 251284 | 215357–282927 | 209377–293191 | +6.2% | 50% | failing-suite +23.7% |
| search-heavy | baseline | 2 | 858285 | 858285 | 576457–1140112 | -246480–1963049 | — | — | — |
| search-heavy | turncur | 2 | 1761408 | 1761408 | 1741295–1781520 | 1682566–1840249 | +105.2% | 0% | repo-sweep +105.2% |
| search-heavy | turnfin | 2 | 457670 | 457670 | 432724–482615 | 359882–555457 | -46.7% | 100% | — |
| search-heavy | turnshort | 2 | 532075 | 532075 | 495300–568851 | 387915–676235 | -38.0% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 8833 | 8107 | 6297–10009 | 6077–10136 | — | — | — |
| long-session | turncur | 6 | 8568 | 7246 | 4282–9581 | 4505–9986 | -3.0% | 67% | feature-drift +10.5% |
| long-session | turnfin | 6 | 8140 | 7523 | 4925–8861 | 4656–10390 | -7.8% | 67% | feature-drift +21.2% |
| long-session | turnshort | 6 | 8405 | 7264 | 5211–9156 | 5143–9386 | -4.9% | 67% | feature-drift +4.7% |
| noisy-output | baseline | 4 | 1860 | 1848 | 1530–2179 | 1421–2275 | — | — | — |
| noisy-output | turncur | 4 | 1730 | 1594 | 1539–1784 | 1280–1907 | -7.0% | 100% | — |
| noisy-output | turnfin | 4 | 1432 | 1432 | 1352–1512 | 1216–1647 | -23.0% | 100% | — |
| noisy-output | turnshort | 4 | 1438 | 1434 | 1395–1476 | 1367–1500 | -22.7% | 100% | — |
| search-heavy | baseline | 2 | 10700 | 10700 | 10484–10915 | 9856–11543 | — | — | — |
| search-heavy | turncur | 2 | 10887 | 10887 | 10647–11127 | 9946–11828 | +1.8% | 0% | repo-sweep +1.8% |
| search-heavy | turnfin | 2 | 11354 | 11354 | 10950–11758 | 9770–12938 | +6.1% | 0% | repo-sweep +6.1% |
| search-heavy | turnshort | 2 | 11158 | 11158 | 10525–11792 | 8675–13641 | +4.3% | 0% | repo-sweep +4.3% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 9 | 21 | 0–33 | -2–44 | — | — | — |
| long-session | turncur | 6 | 0 | 20 | 0–0 | -19–58 | -100.0% | 67% | feature-drift +64.8% |
| long-session | turnfin | 6 | 0 | 1 | 0–0 | -1–3 | -100.0% | 100% | — |
| long-session | turnshort | 6 | 0 | 2 | 0–0 | -2–6 | -100.0% | 100% | — |
| noisy-output | baseline | 4 | 59 | 66 | 48–76 | 37–94 | — | — | — |
| noisy-output | turncur | 4 | 0 | 2 | 0–2 | -2–5 | -100.0% | 100% | — |
| noisy-output | turnfin | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | turnshort | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 86 | 86 | 82–91 | 68–104 | — | — | — |
| search-heavy | turncur | 2 | 53 | 53 | 39–66 | 1–104 | -39.0% | 100% | — |
| search-heavy | turnfin | 2 | 65 | 65 | 62–68 | 53–77 | -24.4% | 100% | — |
| search-heavy | turnshort | 2 | 45 | 45 | 36–53 | 12–77 | -48.3% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4579 | 0.4591 | 607079 | 100% | 84 |
| turncur | 12 | 0.5211 | 0.5333 | 804523 | 100% | 90 |
| turnfin | 12 | 0.4798 | 0.5760 | 518002 | 100% | 87 |
| turnshort | 12 | 0.4791 | 0.5125 | 539713 | 100% | 82 |
