# hush benchmark — generated claims

Generated from 153 retained run records · batch `cost3-sonnet-2276efca` · model `sonnet` · seed `1786120000000` · arms: baseline, caveman, hush.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.0677 | 0.1031 | 0.0622–0.1130 | 0.0672–0.1390 | — | — | — |
| coding | caveman | 12 | 0.0710 | 0.1050 | 0.0695–0.1057 | 0.0692–0.1408 | +4.9% | 50% | explain-rebase +15.6% |
| coding | hush | 12 | 0.0813 | 0.1185 | 0.0789–0.1173 | 0.0794–0.1577 | +20.2% | 25% | explain-rerender +32.2% |
| debugging | baseline | 18 | 0.1680 | 0.2256 | 0.1320–0.2934 | 0.1671–0.2842 | — | — | — |
| debugging | caveman | 18 | 0.1662 | 0.2189 | 0.1365–0.2312 | 0.1626–0.2752 | -1.1% | 33% | bugfix-pagination +13.3% |
| debugging | hush | 18 | 0.2015 | 0.2198 | 0.1607–0.2544 | 0.1846–0.2550 | +20.0% | 33% | bugfix-pagination +27.6% |
| doc-editing | baseline | 3 | 0.2206 | 0.2255 | 0.2111–0.2374 | 0.1953–0.2556 | — | — | — |
| doc-editing | caveman | 3 | 0.2123 | 0.2088 | 0.2069–0.2124 | 0.2016–0.2159 | -3.7% | 100% | — |
| doc-editing | hush | 3 | 0.2521 | 0.2613 | 0.2498–0.2683 | 0.2386–0.2841 | +14.3% | 0% | runbook-edit +14.3% |
| noisy-output | baseline | 12 | 0.1965 | 0.2210 | 0.1810–0.2482 | 0.1885–0.2534 | — | — | — |
| noisy-output | caveman | 12 | 0.2159 | 0.2246 | 0.1820–0.2559 | 0.1980–0.2513 | +9.9% | 50% | noisy-build +25.1% |
| noisy-output | hush | 12 | 0.1892 | 0.1880 | 0.1619–0.2180 | 0.1704–0.2057 | -3.7% | 75% | dep-bump-warnings +14.0% |
| search-heavy | baseline | 6 | 0.1242 | 0.1264 | 0.1216–0.1285 | 0.1209–0.1319 | — | — | — |
| search-heavy | caveman | 6 | 0.1397 | 0.1381 | 0.1290–0.1501 | 0.1264–0.1498 | +12.4% | 0% | call-site-sweep +16.7% |
| search-heavy | hush | 6 | 0.1619 | 0.1614 | 0.1484–0.1739 | 0.1495–0.1733 | +30.3% | 0% | call-site-sweep +34.6% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 42547 | 113513 | 28299–134322 | 41071–185954 | — | — | — |
| coding | caveman | 12 | 30496 | 97112 | 30492–96926 | 28920–165305 | -28.3% | 50% | explain-rerender +7.8% |
| coding | hush | 12 | 31930 | 100247 | 31926–85272 | 29096–171398 | -25.0% | 50% | explain-rerender +12.8% |
| debugging | baseline | 18 | 189110 | 248193 | 149993–256689 | 182177–314210 | — | — | — |
| debugging | caveman | 18 | 196144 | 257059 | 157950–268603 | 192302–321817 | +3.7% | 17% | coupon-currency-flaky +38.9% |
| debugging | hush | 18 | 216085 | 231618 | 166442–286112 | 197618–265617 | +14.3% | 33% | coupon-currency-flaky +28.9% |
| doc-editing | baseline | 3 | 352306 | 362651 | 334461–385669 | 303823–421479 | — | — | — |
| doc-editing | caveman | 3 | 336195 | 325358 | 319490–336645 | 303230–347486 | -4.6% | 100% | — |
| doc-editing | hush | 3 | 320851 | 356140 | 320486–374150 | 286257–426023 | -8.9% | 100% | — |
| noisy-output | baseline | 12 | 198308 | 198665 | 196041–227235 | 174103–223227 | — | — | — |
| noisy-output | caveman | 12 | 160464 | 179108 | 135645–215300 | 139899–218316 | -19.1% | 75% | dep-bump-warnings +28.4% |
| noisy-output | hush | 12 | 185970 | 206849 | 163912–244060 | 173947–239751 | -6.2% | 25% | dep-bump-warnings +21.0% |
| search-heavy | baseline | 6 | 117661 | 117617 | 116839–124839 | 106494–128740 | — | — | — |
| search-heavy | caveman | 6 | 128112 | 127961 | 125134–131397 | 110928–144993 | +8.9% | 0% | repo-summary +6.9% |
| search-heavy | hush | 6 | 136281 | 148099 | 132173–145374 | 125382–170815 | +15.8% | 0% | call-site-sweep +15.8% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 647 | 1069 | 609–1149 | 621–1518 | — | — | — |
| coding | caveman | 12 | 356 | 771 | 257–832 | 279–1262 | -45.0% | 100% | — |
| coding | hush | 12 | 436 | 888 | 276–1134 | 368–1408 | -32.7% | 75% | refactor-rename +2.7% |
| debugging | baseline | 18 | 1641 | 1766 | 889–2098 | 1281–2251 | — | — | — |
| debugging | caveman | 18 | 1382 | 1486 | 684–1861 | 1121–1851 | -15.8% | 100% | — |
| debugging | hush | 18 | 1361 | 1364 | 680–1835 | 1089–1638 | -17.1% | 100% | — |
| doc-editing | baseline | 3 | 2564 | 2641 | 2401–2843 | 2136–3146 | — | — | — |
| doc-editing | caveman | 3 | 1851 | 1850 | 1845–1855 | 1838–1861 | -27.8% | 100% | — |
| doc-editing | hush | 3 | 2305 | 2322 | 2277–2359 | 2227–2416 | -10.1% | 100% | — |
| noisy-output | baseline | 12 | 1434 | 1390 | 1153–1743 | 1101–1679 | — | — | — |
| noisy-output | caveman | 12 | 804 | 951 | 629–1264 | 636–1265 | -43.9% | 100% | — |
| noisy-output | hush | 12 | 1110 | 1380 | 964–1881 | 1053–1707 | -22.6% | 50% | sidecar-follow +73.2% |
| search-heavy | baseline | 6 | 1206 | 1201 | 654–1692 | 685–1716 | — | — | — |
| search-heavy | caveman | 6 | 1247 | 1198 | 972–1367 | 879–1517 | +3.4% | 50% | call-site-sweep +44.0% |
| search-heavy | hush | 6 | 1457 | 1349 | 1164–1533 | 1094–1604 | +20.8% | 50% | call-site-sweep +75.9% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 13 | 0–9 | -1–26 | — | — | — |
| coding | caveman | 12 | 0 | 5 | 0–4 | -0–10 | — | 100% | — |
| coding | hush | 12 | 0 | 8 | 0–4 | -1–17 | — | 100% | — |
| debugging | baseline | 18 | 34 | 64 | 22–108 | 35–93 | — | — | — |
| debugging | caveman | 18 | 21 | 32 | 11–34 | 16–48 | -38.8% | 100% | — |
| debugging | hush | 18 | 0 | 1 | 0–0 | -0–1 | -100.0% | 100% | — |
| doc-editing | baseline | 3 | 11 | 15 | 6–23 | -5–35 | — | — | — |
| doc-editing | caveman | 3 | 0 | 3 | 0–5 | -3–10 | -100.0% | 100% | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 12 | 11 | 29 | 0–59 | 10–47 | — | — | — |
| noisy-output | caveman | 12 | 0 | 7 | 0–12 | 1–12 | -100.0% | 100% | — |
| noisy-output | hush | 12 | 0 | 1 | 0–0 | -1–2 | -100.0% | 100% | — |
| search-heavy | baseline | 6 | 7 | 11 | 0–22 | 1–21 | — | — | — |
| search-heavy | caveman | 6 | 4 | 4 | 0–8 | 0–8 | -50.0% | 100% | — |
| search-heavy | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.1840 | 0.1695 | 196221 | 100% | 23 |
| caveman | 51 | 0.1834 | 0.1743 | 189913 | 92% | 17 |
| hush | 51 | 0.1841 | 0.1769 | 192378 | 96% | 24 |
