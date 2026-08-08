# hush benchmark — generated claims

Generated from 16 retained run records · batch `probe-opener-ce0bd038` · model `opus` · seed `1786135293353` · arms: hush, opener.

Segments: debugging, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | hush | 4 | 0.3540 | 0.3731 | 0.3348–0.3923 | 0.2988–0.4474 | — | — | — |
| debugging | opener | 4 | 0.3559 | 0.3685 | 0.3430–0.3814 | 0.3110–0.4260 | — | — | — |
| noisy-output | hush | 2 | 0.2696 | 0.2696 | 0.2677–0.2715 | 0.2620–0.2771 | — | — | — |
| noisy-output | opener | 2 | 0.2657 | 0.2657 | 0.2654–0.2660 | 0.2644–0.2670 | — | — | — |
| search-heavy | hush | 2 | 0.1956 | 0.1956 | 0.1946–0.1966 | 0.1915–0.1996 | — | — | — |
| search-heavy | opener | 2 | 0.2030 | 0.2030 | 0.1996–0.2065 | 0.1895–0.2166 | — | — | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | hush | 4 | 240475 | 259763 | 200615–299623 | 169847–349679 | — | — | — |
| debugging | opener | 4 | 231108 | 242796 | 210457–263446 | 180031–305560 | — | — | — |
| noisy-output | hush | 2 | 197059 | 197059 | 196934–197184 | 196569–197549 | — | — | — |
| noisy-output | opener | 2 | 196828 | 196828 | 196795–196860 | 196701–196954 | — | — | — |
| search-heavy | hush | 2 | 106339 | 106339 | 106309–106368 | 106224–106453 | — | — | — |
| search-heavy | opener | 2 | 119591 | 119591 | 112951–126232 | 93560–145622 | — | — | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | hush | 4 | 2710 | 2794 | 2488–3015 | 2303–3285 | — | — | — |
| debugging | opener | 4 | 2492 | 2463 | 2247–2708 | 2178–2748 | — | — | — |
| noisy-output | hush | 2 | 1705 | 1705 | 1637–1772 | 1441–1968 | — | — | — |
| noisy-output | opener | 2 | 1585 | 1585 | 1584–1586 | 1581–1589 | — | — | — |
| search-heavy | hush | 2 | 1042 | 1042 | 1006–1078 | 901–1183 | — | — | — |
| search-heavy | opener | 2 | 1085 | 1085 | 1077–1092 | 1056–1113 | — | — | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| debugging | hush | 4 | 7 | 7 | 6–8 | 5–9 | — | — | — |
| debugging | opener | 4 | 0 | 2 | 0–2 | -1–4 | — | — | — |
| noisy-output | hush | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | opener | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | hush | 2 | 5 | 5 | 2–7 | -4–13 | — | — | — |
| search-heavy | opener | 2 | 4 | 4 | 2–5 | -3–10 | — | — | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| hush | 8 | 0.3028 | 0.2886 | 205731 | 75% | 43 |
| opener | 8 | 0.3014 | 0.2890 | 200502 | 88% | 39 |
