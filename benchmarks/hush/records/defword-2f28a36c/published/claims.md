# hush benchmark — generated claims

Generated from 36 retained run records · batch `defword-2f28a36c` · model `sonnet` · seed `1786177231404` · arms: baseline, defcur, deffin.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.5899 | 0.5892 | 0.4504–0.7006 | 0.4606–0.7179 | — | — | — |
| long-session | defcur | 6 | 0.6994 | 0.7150 | 0.6858–0.7519 | 0.6539–0.7761 | +18.6% | 0% | feature-drift +48.9% |
| long-session | deffin | 6 | 0.6986 | 0.7009 | 0.6779–0.7081 | 0.6353–0.7666 | +18.4% | 33% | feature-drift +39.5% |
| noisy-output | baseline | 4 | 0.1899 | 0.1959 | 0.1814–0.2044 | 0.1690–0.2227 | — | — | — |
| noisy-output | defcur | 4 | 0.2203 | 0.2171 | 0.2139–0.2235 | 0.2044–0.2297 | +16.0% | 0% | failing-suite +18.4% |
| noisy-output | deffin | 4 | 0.2012 | 0.2119 | 0.2001–0.2130 | 0.1890–0.2349 | +5.9% | 0% | failing-suite +13.3% |
| search-heavy | baseline | 2 | 0.6536 | 0.6536 | 0.5677–0.7395 | 0.3167–0.9905 | — | — | — |
| search-heavy | defcur | 2 | 0.6149 | 0.6149 | 0.5857–0.6441 | 0.5005–0.7293 | -5.9% | 100% | — |
| search-heavy | deffin | 2 | 0.6857 | 0.6857 | 0.6533–0.7181 | 0.5587–0.8126 | +4.9% | 0% | repo-sweep +4.9% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 883232 | 858170 | 736187–1019241 | 675095–1041244 | — | — | — |
| long-session | defcur | 6 | 776510 | 816356 | 706668–895020 | 669846–962866 | -12.1% | 67% | feature-drift +31.2% |
| long-session | deffin | 6 | 801003 | 825455 | 703365–948258 | 714656–936255 | -9.3% | 67% | feature-drift +41.1% |
| noisy-output | baseline | 4 | 230487 | 253544 | 221014–263018 | 182690–324399 | — | — | — |
| noisy-output | defcur | 4 | 251908 | 253000 | 242261–262647 | 224005–281995 | +9.3% | 50% | failing-suite +10.8% |
| noisy-output | deffin | 4 | 218848 | 236710 | 218130–237428 | 200235–273185 | -5.0% | 50% | failing-suite +2.9% |
| search-heavy | baseline | 2 | 1013185 | 1013185 | 689324–1337047 | -256352–2282722 | — | — | — |
| search-heavy | defcur | 2 | 341634 | 341634 | 299240–384029 | 175448–507820 | -66.3% | 100% | — |
| search-heavy | deffin | 2 | 385706 | 385706 | 361676–409735 | 291511–479900 | -61.9% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 8552 | 8640 | 5529–10976 | 5583–11696 | — | — | — |
| long-session | defcur | 6 | 8412 | 7999 | 5732–9818 | 5829–10169 | -1.6% | 33% | feature-drift +11.5% |
| long-session | deffin | 6 | 6224 | 6203 | 4893–7315 | 4750–7656 | -27.2% | 67% | incident-forensics +16.0% |
| noisy-output | baseline | 4 | 1804 | 1845 | 1420–2229 | 1288–2402 | — | — | — |
| noisy-output | defcur | 4 | 1635 | 1641 | 1427–1849 | 1192–2089 | -9.4% | 100% | — |
| noisy-output | deffin | 4 | 1474 | 1689 | 1168–1995 | 969–2409 | -18.3% | 100% | — |
| search-heavy | baseline | 2 | 10195 | 10195 | 9911–10479 | 9082–11308 | — | — | — |
| search-heavy | defcur | 2 | 10131 | 10131 | 10095–10168 | 9988–10274 | -0.6% | 100% | — |
| search-heavy | deffin | 2 | 11672 | 11672 | 10943–12400 | 8815–14528 | +14.5% | 0% | repo-sweep +14.5% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 22 | 161 | 13–94 | -90–412 | — | — | — |
| long-session | defcur | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| long-session | deffin | 6 | 0 | 1 | 0–0 | -1–3 | -100.0% | 100% | — |
| noisy-output | baseline | 4 | 63 | 70 | 41–92 | 29–110 | — | — | — |
| noisy-output | defcur | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | deffin | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 113 | 113 | 105–120 | 84–141 | — | — | — |
| search-heavy | defcur | 2 | 11 | 11 | 10–12 | 7–15 | -90.2% | 100% | — |
| search-heavy | deffin | 2 | 39 | 39 | 39–40 | 37–41 | -65.3% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4688 | 0.4554 | 682464 | 100% | 76 |
| defcur | 12 | 0.5323 | 0.6413 | 549450 | 100% | 84 |
| deffin | 12 | 0.5354 | 0.6471 | 555915 | 100% | 81 |
