# hush benchmark — generated claims

Generated from 36 retained run records · batch `probe-nudge-04a7a3df` · model `opus` · seed `1786135293353` · arms: firstcall, firstcall2, hush.

Segments: debugging, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | firstcall | 6 | 0.3623 | 0.3589 | 0.3225–0.3893 | 0.3245–0.3933 | — | — | — |
| debugging | firstcall2 | 6 | 0.3858 | 0.4145 | 0.3620–0.4257 | 0.3484–0.4807 | — | — | — |
| debugging | hush | 6 | 0.4048 | 0.3977 | 0.3441–0.4168 | 0.3385–0.4570 | — | — | — |
| noisy-output | firstcall | 3 | 0.2601 | 0.2637 | 0.2564–0.2692 | 0.2488–0.2787 | — | — | — |
| noisy-output | firstcall2 | 3 | 0.2757 | 0.2735 | 0.2714–0.2767 | 0.2671–0.2799 | — | — | — |
| noisy-output | hush | 3 | 0.2683 | 0.2674 | 0.2667–0.2685 | 0.2652–0.2696 | — | — | — |
| search-heavy | firstcall | 3 | 0.1958 | 0.1952 | 0.1949–0.1959 | 0.1940–0.1965 | — | — | — |
| search-heavy | firstcall2 | 3 | 0.1980 | 0.2025 | 0.1974–0.2054 | 0.1925–0.2126 | — | — | — |
| search-heavy | hush | 3 | 0.1966 | 0.1960 | 0.1956–0.1968 | 0.1945–0.1975 | — | — | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | firstcall | 6 | 229924 | 228098 | 182716–258635 | 187405–268791 | — | — | — |
| debugging | firstcall2 | 6 | 238150 | 266118 | 214155–276383 | 203482–328755 | — | — | — |
| debugging | hush | 6 | 280599 | 278233 | 224562–308037 | 225410–331056 | — | — | — |
| noisy-output | firstcall | 3 | 196576 | 196886 | 196214–197403 | 195507–198265 | — | — | — |
| noisy-output | firstcall2 | 3 | 197936 | 197694 | 197452–198057 | 196970–198418 | — | — | — |
| noisy-output | hush | 3 | 196908 | 196936 | 196843–197016 | 196738–197134 | — | — | — |
| search-heavy | firstcall | 3 | 106397 | 106389 | 106385–106397 | 106373–106405 | — | — | — |
| search-heavy | firstcall2 | 3 | 106593 | 106586 | 106578–106598 | 106563–106610 | — | — | — |
| search-heavy | hush | 3 | 106303 | 106347 | 106290–106382 | 106234–106460 | — | — | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | firstcall | 6 | 2616 | 2643 | 2310–2855 | 2301–2985 | — | — | — |
| debugging | firstcall2 | 6 | 4075 | 3448 | 2472–4211 | 2490–4405 | — | — | — |
| debugging | hush | 6 | 2511 | 2829 | 2438–3204 | 2255–3402 | — | — | — |
| noisy-output | firstcall | 3 | 1423 | 1513 | 1322–1659 | 1122–1903 | — | — | — |
| noisy-output | firstcall2 | 3 | 1848 | 1783 | 1733–1866 | 1620–1946 | — | — | — |
| noisy-output | hush | 3 | 1651 | 1631 | 1603–1669 | 1554–1707 | — | — | — |
| search-heavy | firstcall | 3 | 1044 | 1018 | 1005–1045 | 967–1070 | — | — | — |
| search-heavy | firstcall2 | 3 | 1099 | 1284 | 1080–1396 | 883–1684 | — | — | — |
| search-heavy | hush | 3 | 1073 | 1057 | 1039–1084 | 1004–1110 | — | — | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | firstcall | 6 | 5 | 5 | 1–7 | 1–8 | — | — | — |
| debugging | firstcall2 | 6 | 8 | 8 | 7–10 | 7–10 | — | — | — |
| debugging | hush | 6 | 7 | 7 | 6–7 | 6–9 | — | — | — |
| noisy-output | firstcall | 3 | 0 | 2 | 0–4 | -2–7 | — | — | — |
| noisy-output | firstcall2 | 3 | 8 | 8 | 8–8 | 8–8 | — | — | — |
| noisy-output | hush | 3 | 7 | 5 | 4–7 | 0–9 | — | — | — |
| search-heavy | firstcall | 3 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | firstcall2 | 3 | 7 | 7 | 7–7 | 6–7 | — | — | — |
| search-heavy | hush | 3 | 0 | 2 | 0–4 | -2–7 | — | — | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| firstcall | 12 | 0.2942 | 0.2940 | 189868 | 75% | 42 |
| firstcall2 | 12 | 0.3263 | 0.3145 | 209129 | 83% | 40 |
| hush | 12 | 0.3147 | 0.2911 | 214937 | 83% | 39 |
