# hush benchmark — generated claims

Generated from 153 retained run records · batch `cost3-opus-6b5bc90a` · model `opus` · seed `1786120000000` · arms: baseline, caveman, hush.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.1396 | 0.1677 | 0.0989–0.2086 | 0.1202–0.2152 | — | — | — |
| coding | caveman | 12 | 0.1019 | 0.1495 | 0.1005–0.1504 | 0.1006–0.1984 | -27.0% | 50% | explain-rebase +7.5% |
| coding | hush | 12 | 0.1569 | 0.1989 | 0.1339–0.2305 | 0.1473–0.2504 | +12.4% | 0% | explain-rerender +38.7% |
| debugging | baseline | 18 | 0.3312 | 0.3669 | 0.2188–0.4635 | 0.2924–0.4413 | — | — | — |
| debugging | caveman | 18 | 0.3151 | 0.3547 | 0.2529–0.3659 | 0.2889–0.4205 | -4.9% | 50% | bugfix-pagination +13.9% |
| debugging | hush | 18 | 0.3428 | 0.3971 | 0.2774–0.4190 | 0.3171–0.4770 | +3.5% | 33% | bugfix-pagination +33.3% |
| doc-editing | baseline | 3 | 0.4376 | 0.4515 | 0.4019–0.4942 | 0.3462–0.5568 | — | — | — |
| doc-editing | caveman | 3 | 0.3959 | 0.4114 | 0.3735–0.4416 | 0.3328–0.4899 | -9.5% | 100% | — |
| doc-editing | hush | 3 | 0.6236 | 0.5986 | 0.5581–0.6517 | 0.4899–0.7074 | +42.5% | 0% | runbook-edit +42.5% |
| noisy-output | baseline | 12 | 0.2808 | 0.3200 | 0.2641–0.3324 | 0.2570–0.3829 | — | — | — |
| noisy-output | caveman | 12 | 0.2722 | 0.2963 | 0.2580–0.3113 | 0.2590–0.3337 | -3.1% | 50% | noisy-build +1.5% |
| noisy-output | hush | 12 | 0.2890 | 0.3055 | 0.2571–0.3345 | 0.2592–0.3518 | +2.9% | 25% | log-triage +13.0% |
| search-heavy | baseline | 6 | 0.2489 | 0.2748 | 0.2344–0.2945 | 0.2243–0.3252 | — | — | — |
| search-heavy | caveman | 6 | 0.2092 | 0.2186 | 0.1947–0.2331 | 0.1887–0.2484 | -15.9% | 100% | — |
| search-heavy | hush | 6 | 0.3352 | 0.3255 | 0.2086–0.4322 | 0.2251–0.4259 | +34.7% | 50% | call-site-sweep +41.4% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 56953 | 82794 | 38443–113161 | 44787–120802 | — | — | — |
| coding | caveman | 12 | 24064 | 64206 | 24060–59168 | 22897–105515 | -57.7% | 50% | explain-rebase +9.9% |
| coding | hush | 12 | 51332 | 71388 | 25514–96377 | 40874–101902 | -9.9% | 50% | explain-rerender +16.7% |
| debugging | baseline | 18 | 226017 | 244056 | 190135–296231 | 212055–276056 | — | — | — |
| debugging | caveman | 18 | 229254 | 252854 | 219280–275135 | 222653–283056 | +1.4% | 67% | bugfix-pagination +24.4% |
| debugging | hush | 18 | 247274 | 278440 | 236575–286731 | 244814–312065 | +9.4% | 33% | bugfix-pagination +49.7% |
| doc-editing | baseline | 3 | 362263 | 366815 | 316233–415122 | 254824–478807 | — | — | — |
| doc-editing | caveman | 3 | 367566 | 374637 | 338205–407535 | 295878–453397 | +1.5% | 0% | runbook-edit +1.5% |
| doc-editing | hush | 3 | 499931 | 482388 | 435448–538100 | 364960–599816 | +38.0% | 0% | runbook-edit +38.0% |
| noisy-output | baseline | 12 | 172275 | 172835 | 160869–196537 | 153784–191886 | — | — | — |
| noisy-output | caveman | 12 | 185543 | 177906 | 168948–189835 | 147660–208152 | +7.7% | 25% | noisy-build +7.6% |
| noisy-output | hush | 12 | 199311 | 200095 | 188123–203553 | 178066–222123 | +15.7% | 0% | sidecar-follow +38.1% |
| search-heavy | baseline | 6 | 114695 | 135343 | 98870–150659 | 91259–179427 | — | — | — |
| search-heavy | caveman | 6 | 99770 | 108633 | 90546–113818 | 81531–135734 | -13.0% | 50% | repo-summary +5.1% |
| search-heavy | hush | 6 | 167682 | 175754 | 106485–232872 | 113888–237619 | +46.2% | 0% | call-site-sweep +45.1% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 1973 | 2151 | 1321–2974 | 1604–2698 | — | — | — |
| coding | caveman | 12 | 804 | 1308 | 744–1483 | 786–1831 | -59.2% | 100% | — |
| coding | hush | 12 | 1803 | 1763 | 1298–2300 | 1434–2092 | -8.6% | 75% | explain-rerender +7.0% |
| debugging | baseline | 18 | 3723 | 4490 | 1667–6342 | 3022–5958 | — | — | — |
| debugging | caveman | 18 | 2526 | 3041 | 1429–3336 | 2101–3981 | -32.2% | 100% | — |
| debugging | hush | 18 | 1990 | 2966 | 1203–3026 | 1812–4119 | -46.6% | 100% | — |
| doc-editing | baseline | 3 | 4663 | 5075 | 4377–5567 | 3669–6481 | — | — | — |
| doc-editing | caveman | 3 | 3225 | 3455 | 2993–3803 | 2512–4399 | -30.8% | 100% | — |
| doc-editing | hush | 3 | 4053 | 3829 | 3581–4190 | 3107–4552 | -13.1% | 100% | — |
| noisy-output | baseline | 12 | 2842 | 3181 | 1740–4032 | 2142–4221 | — | — | — |
| noisy-output | caveman | 12 | 2036 | 2322 | 1413–2801 | 1493–3151 | -28.4% | 100% | — |
| noisy-output | hush | 12 | 2140 | 2297 | 1497–2722 | 1644–2950 | -24.7% | 100% | — |
| search-heavy | baseline | 6 | 3803 | 3769 | 3131–4480 | 2631–4906 | — | — | — |
| search-heavy | caveman | 6 | 1765 | 1646 | 1369–1905 | 1361–1930 | -53.6% | 100% | — |
| search-heavy | hush | 6 | 2309 | 2035 | 1434–2532 | 1483–2587 | -39.3% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 25 | 0–32 | 2–49 | — | — | — |
| coding | caveman | 12 | 0 | 1 | 0–0 | -0–2 | — | 100% | — |
| coding | hush | 12 | 0 | 0 | 0–0 | 0–0 | — | 100% | — |
| debugging | baseline | 18 | 52 | 52 | 39–64 | 41–63 | — | — | — |
| debugging | caveman | 18 | 15 | 14 | 8–18 | 10–17 | -72.1% | 100% | — |
| debugging | hush | 18 | 0 | 3 | 0–6 | 1–5 | -100.0% | 100% | — |
| doc-editing | baseline | 3 | 19 | 30 | 13–42 | -5–64 | — | — | — |
| doc-editing | caveman | 3 | 0 | 2 | 0–3 | -2–6 | -100.0% | 100% | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 12 | 25 | 26 | 6–38 | 13–38 | — | — | — |
| noisy-output | caveman | 12 | 5 | 11 | 0–8 | 0–21 | -79.6% | 100% | — |
| noisy-output | hush | 12 | 0 | 2 | 0–2 | -0–4 | -100.0% | 100% | — |
| search-heavy | baseline | 6 | 21 | 27 | 19–30 | 13–40 | — | — | — |
| search-heavy | caveman | 6 | 3 | 3 | 0–6 | 0–6 | -85.7% | 100% | — |
| search-heavy | hush | 6 | 4 | 4 | 0–7 | 0–7 | -83.3% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.3031 | 0.2760 | 183785 | 100% | 47 |
| caveman | 51 | 0.2800 | 0.2702 | 181028 | 100% | 36 |
| hush | 51 | 0.3323 | 0.3018 | 211204 | 98% | 38 |
