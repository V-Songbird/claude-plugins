# hush benchmark — generated claims

Generated from 306 retained run records · batch `h2h-sonnet-2c5df75b` · model `sonnet` · seed `1786061500000` · arms: baseline, adhd, caveman, hush, nextstep, simple-english.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.0676 | 0.1072 | 0.0616–0.1169 | 0.0653–0.1491 | — | — | — |
| coding | adhd | 12 | 0.0769 | 0.1061 | 0.0742–0.1066 | 0.0734–0.1389 | +13.8% | 50% | explain-rebase +28.1% |
| coding | caveman | 12 | 0.0714 | 0.1062 | 0.0690–0.1168 | 0.0724–0.1400 | +5.7% | 25% | explain-rebase +17.9% |
| coding | hush | 12 | 0.0815 | 0.1153 | 0.0777–0.1304 | 0.0822–0.1485 | +20.5% | 25% | explain-rerender +48.2% |
| coding | nextstep | 12 | 0.0805 | 0.1162 | 0.0793–0.1333 | 0.0820–0.1504 | +19.1% | 25% | explain-rebase +32.5% |
| coding | simple-english | 12 | 0.0793 | 0.1080 | 0.0753–0.1185 | 0.0769–0.1391 | +17.3% | 25% | explain-rebase +42.0% |
| debugging | baseline | 18 | 0.1645 | 0.2094 | 0.1291–0.2436 | 0.1535–0.2654 | — | — | — |
| debugging | adhd | 18 | 0.1706 | 0.2153 | 0.1279–0.2252 | 0.1579–0.2727 | +3.7% | 33% | bugfix-pagination +15.1% |
| debugging | caveman | 18 | 0.1637 | 0.2029 | 0.1274–0.2020 | 0.1528–0.2531 | -0.5% | 50% | checkout-bug +49.3% |
| debugging | hush | 18 | 0.1711 | 0.2055 | 0.1419–0.2147 | 0.1644–0.2466 | +4.0% | 33% | bugfix-pagination +28.1% |
| debugging | nextstep | 18 | 0.1998 | 0.2215 | 0.1436–0.2573 | 0.1764–0.2666 | +21.4% | 33% | bugfix-pagination +28.8% |
| debugging | simple-english | 18 | 0.1727 | 0.2330 | 0.1281–0.3263 | 0.1687–0.2973 | +5.0% | 17% | incident-pool-leak +34.9% |
| doc-editing | baseline | 3 | 0.2232 | 0.2410 | 0.2190–0.2542 | 0.1976–0.2845 | — | — | — |
| doc-editing | adhd | 3 | 0.2293 | 0.2303 | 0.2225–0.2377 | 0.2131–0.2475 | +2.7% | 0% | runbook-edit +2.7% |
| doc-editing | caveman | 3 | 0.2165 | 0.2205 | 0.2150–0.2240 | 0.2096–0.2315 | -3.0% | 100% | — |
| doc-editing | hush | 3 | 0.2933 | 0.3043 | 0.2667–0.3364 | 0.2247–0.3839 | +31.4% | 0% | runbook-edit +31.4% |
| doc-editing | nextstep | 3 | 0.2926 | 0.2915 | 0.2857–0.2979 | 0.2777–0.3054 | +31.1% | 0% | runbook-edit +31.1% |
| doc-editing | simple-english | 3 | 0.2637 | 0.2529 | 0.2370–0.2742 | 0.2095–0.2962 | +18.1% | 0% | runbook-edit +18.1% |
| noisy-output | baseline | 12 | 0.1921 | 0.2158 | 0.1772–0.2437 | 0.1841–0.2476 | — | — | — |
| noisy-output | adhd | 12 | 0.1839 | 0.2173 | 0.1795–0.2540 | 0.1862–0.2483 | -4.2% | 25% | sidecar-follow +7.4% |
| noisy-output | caveman | 12 | 0.2020 | 0.2175 | 0.1765–0.2508 | 0.1873–0.2478 | +5.1% | 25% | noisy-build +25.2% |
| noisy-output | hush | 12 | 0.1951 | 0.1934 | 0.1574–0.2194 | 0.1672–0.2195 | +1.6% | 75% | noisy-build +0.8% |
| noisy-output | nextstep | 12 | 0.1816 | 0.1784 | 0.1696–0.1921 | 0.1580–0.1988 | -5.5% | 75% | noisy-build +1.2% |
| noisy-output | simple-english | 12 | 0.2008 | 0.2220 | 0.1720–0.2503 | 0.1890–0.2549 | +4.5% | 0% | dep-bump-warnings +12.9% |
| search-heavy | baseline | 6 | 0.1259 | 0.1260 | 0.1228–0.1285 | 0.1213–0.1307 | — | — | — |
| search-heavy | adhd | 6 | 0.1443 | 0.1438 | 0.1367–0.1509 | 0.1370–0.1507 | +14.6% | 0% | call-site-sweep +17.2% |
| search-heavy | caveman | 6 | 0.1237 | 0.1203 | 0.1140–0.1312 | 0.1091–0.1315 | -1.7% | 50% | repo-summary +7.2% |
| search-heavy | hush | 6 | 0.1524 | 0.1555 | 0.1464–0.1651 | 0.1433–0.1676 | +21.0% | 0% | call-site-sweep +31.1% |
| search-heavy | nextstep | 6 | 0.1483 | 0.1513 | 0.1467–0.1609 | 0.1327–0.1699 | +17.8% | 0% | call-site-sweep +27.9% |
| search-heavy | simple-english | 6 | 0.1289 | 0.1329 | 0.1235–0.1431 | 0.1203–0.1455 | +2.4% | 0% | repo-summary +5.1% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 42421 | 127784 | 28136–133616 | 35232–220337 | — | — | — |
| coding | adhd | 12 | 30540 | 89054 | 30536–80908 | 28617–149491 | -28.0% | 50% | explain-rerender +8.5% |
| coding | caveman | 12 | 30333 | 99006 | 30332–111694 | 35269–162743 | -28.5% | 25% | explain-rerender +7.8% |
| coding | hush | 12 | 31767 | 89965 | 31763–107732 | 33580–146350 | -25.1% | 50% | explain-rerender +12.9% |
| coding | nextstep | 12 | 31900 | 93749 | 31899–133999 | 36625–150873 | -24.8% | 50% | explain-rerender +13.4% |
| coding | simple-english | 12 | 43631 | 99895 | 28948–106509 | 36446–163344 | +2.9% | 25% | write-validator +3.1% |
| debugging | baseline | 18 | 186936 | 238973 | 149355–279799 | 180435–297510 | — | — | — |
| debugging | adhd | 18 | 199611 | 260579 | 156834–231333 | 185800–335358 | +6.8% | 33% | incident-followup +16.3% |
| debugging | caveman | 18 | 193189 | 239481 | 157292–276723 | 186373–292589 | +3.3% | 50% | checkout-bug +95.6% |
| debugging | hush | 18 | 202091 | 243930 | 165813–272533 | 194275–293585 | +8.1% | 50% | coupon-currency-flaky +29.8% |
| debugging | nextstep | 18 | 209833 | 255858 | 165109–327142 | 200168–311549 | +12.2% | 50% | coupon-currency-flaky +29.8% |
| debugging | simple-english | 18 | 184837 | 250340 | 150210–261175 | 181393–319286 | -1.1% | 33% | incident-followup +13.0% |
| doc-editing | baseline | 3 | 351158 | 387319 | 348267–408291 | 310707–463932 | — | — | — |
| doc-editing | adhd | 3 | 369589 | 371087 | 353207–388218 | 331441–410733 | +5.2% | 0% | runbook-edit +5.2% |
| doc-editing | caveman | 3 | 337035 | 348401 | 336438–354681 | 324943–371858 | -4.0% | 100% | — |
| doc-editing | hush | 3 | 427667 | 423633 | 372483–476801 | 305520–541746 | +21.8% | 0% | runbook-edit +21.8% |
| doc-editing | nextstep | 3 | 429490 | 418686 | 411978–430797 | 394904–442468 | +22.3% | 0% | runbook-edit +22.3% |
| doc-editing | simple-english | 3 | 413173 | 390353 | 368833–423284 | 324803–455904 | +17.7% | 0% | runbook-edit +17.7% |
| noisy-output | baseline | 12 | 195932 | 195897 | 138492–238078 | 153605–238189 | — | — | — |
| noisy-output | adhd | 12 | 208586 | 184256 | 135795–215279 | 149533–218979 | +6.5% | 50% | sidecar-follow +7.3% |
| noisy-output | caveman | 12 | 159771 | 161473 | 135155–198479 | 132823–190123 | -18.5% | 50% | sidecar-follow +6.7% |
| noisy-output | hush | 12 | 214196 | 203925 | 160007–245552 | 169813–238037 | +9.3% | 25% | sidecar-follow +67.3% |
| noisy-output | nextstep | 12 | 188719 | 190404 | 127952–240193 | 150064–230745 | -3.7% | 50% | sidecar-follow +35.0% |
| noisy-output | simple-english | 12 | 170255 | 188855 | 131018–246290 | 143461–234248 | -13.1% | 25% | sidecar-follow +2.5% |
| search-heavy | baseline | 6 | 119447 | 132192 | 116568–140340 | 112710–151674 | — | — | — |
| search-heavy | adhd | 6 | 128342 | 138416 | 125774–152254 | 112925–163906 | +7.4% | 50% | repo-summary +8.3% |
| search-heavy | caveman | 6 | 111044 | 109622 | 94658–124723 | 96343–122902 | -7.0% | 50% | repo-summary +7.5% |
| search-heavy | hush | 6 | 131482 | 139603 | 112474–157280 | 107992–171213 | +10.1% | 0% | repo-summary +13.2% |
| search-heavy | nextstep | 6 | 131983 | 123120 | 112419–132027 | 109600–136640 | +10.5% | 50% | repo-summary +13.6% |
| search-heavy | simple-english | 6 | 99978 | 105784 | 92092–114648 | 90942–120626 | -16.3% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 686 | 1121 | 604–1468 | 652–1590 | — | — | — |
| coding | adhd | 12 | 732 | 986 | 553–1157 | 530–1442 | +6.8% | 50% | explain-rebase +39.2% |
| coding | caveman | 12 | 449 | 832 | 285–995 | 358–1306 | -34.5% | 100% | — |
| coding | hush | 12 | 513 | 974 | 255–1558 | 487–1462 | -25.2% | 75% | explain-rerender +82.9% |
| coding | nextstep | 12 | 397 | 869 | 308–1004 | 369–1369 | -42.2% | 100% | — |
| coding | simple-english | 12 | 1198 | 1441 | 708–2304 | 997–1885 | +74.7% | 50% | explain-rebase +273.8% |
| debugging | baseline | 18 | 1815 | 1927 | 880–2539 | 1386–2468 | — | — | — |
| debugging | adhd | 18 | 1480 | 1398 | 631–1812 | 1071–1725 | -18.5% | 100% | — |
| debugging | caveman | 18 | 1353 | 1409 | 684–1719 | 1057–1762 | -25.5% | 67% | checkout-bug +23.7% |
| debugging | hush | 18 | 1467 | 1449 | 718–1684 | 1126–1772 | -19.2% | 83% | checkout-bug +5.3% |
| debugging | nextstep | 18 | 1633 | 1530 | 682–1918 | 1160–1901 | -10.1% | 83% | bugfix-pagination +2.9% |
| debugging | simple-english | 18 | 1655 | 1880 | 781–2284 | 1248–2513 | -8.8% | 17% | bugfix-pagination +5.3% |
| doc-editing | baseline | 3 | 2767 | 2973 | 2612–3232 | 2244–3703 | — | — | — |
| doc-editing | adhd | 3 | 2187 | 2183 | 2106–2262 | 2007–2359 | -21.0% | 100% | — |
| doc-editing | caveman | 3 | 2094 | 2099 | 2013–2182 | 1907–2290 | -24.3% | 100% | — |
| doc-editing | hush | 3 | 2612 | 2891 | 2311–3333 | 1703–4080 | -5.6% | 100% | — |
| doc-editing | nextstep | 3 | 2603 | 2729 | 2584–2811 | 2443–3014 | -5.9% | 100% | — |
| doc-editing | simple-english | 3 | 3142 | 3331 | 2757–3811 | 2124–4538 | +13.6% | 0% | runbook-edit +13.6% |
| noisy-output | baseline | 12 | 1600 | 1496 | 1033–1981 | 1139–1854 | — | — | — |
| noisy-output | adhd | 12 | 986 | 1003 | 758–1142 | 761–1244 | -38.4% | 100% | — |
| noisy-output | caveman | 12 | 892 | 954 | 635–1259 | 690–1218 | -44.3% | 100% | — |
| noisy-output | hush | 12 | 1188 | 1362 | 836–1830 | 1019–1705 | -25.7% | 50% | log-triage +16.9% |
| noisy-output | nextstep | 12 | 1055 | 1170 | 820–1419 | 864–1475 | -34.1% | 100% | — |
| noisy-output | simple-english | 12 | 1639 | 1618 | 993–2118 | 1138–2097 | +2.4% | 50% | log-triage +17.3% |
| search-heavy | baseline | 6 | 1483 | 1508 | 1336–1836 | 1183–1833 | — | — | — |
| search-heavy | adhd | 6 | 1630 | 1430 | 1014–1774 | 1040–1820 | +9.9% | 100% | — |
| search-heavy | caveman | 6 | 1002 | 1018 | 682–1383 | 701–1336 | -32.4% | 100% | — |
| search-heavy | hush | 6 | 1511 | 1590 | 1412–1698 | 1394–1786 | +1.9% | 50% | call-site-sweep +6.0% |
| search-heavy | nextstep | 6 | 1503 | 1406 | 1334–1611 | 1109–1702 | +1.3% | 100% | — |
| search-heavy | simple-english | 6 | 1393 | 1713 | 931–1787 | 566–2860 | -6.1% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 14 | 0–11 | -2–30 | — | — | — |
| coding | adhd | 12 | 0 | 8 | 0–7 | -0–16 | — | 100% | — |
| coding | caveman | 12 | 0 | 6 | 0–6 | -0–12 | — | 100% | — |
| coding | hush | 12 | 0 | 1 | 0–0 | -1–3 | — | 100% | — |
| coding | nextstep | 12 | 0 | 3 | 0–0 | -2–8 | — | 100% | — |
| coding | simple-english | 12 | 0 | 13 | 0–11 | -1–27 | — | 0% | refactor-rename +4.7% |
| debugging | baseline | 18 | 56 | 75 | 23–102 | 44–105 | — | — | — |
| debugging | adhd | 18 | 28 | 49 | 17–61 | 27–71 | -50.0% | 100% | — |
| debugging | caveman | 18 | 21 | 32 | 17–34 | 18–45 | -63.4% | 100% | — |
| debugging | hush | 18 | 0 | 1 | 0–0 | -1–3 | -100.0% | 100% | — |
| debugging | nextstep | 18 | 0 | 1 | 0–0 | -1–3 | -100.0% | 100% | — |
| debugging | simple-english | 18 | 38 | 67 | 19–103 | 34–100 | -33.0% | 67% | coupon-currency-flaky +24.7% |
| doc-editing | baseline | 3 | 0 | 8 | 0–12 | -8–24 | — | — | — |
| doc-editing | adhd | 3 | 0 | 2 | 0–4 | -2–7 | — | — | — |
| doc-editing | caveman | 3 | 0 | 4 | 0–6 | -4–11 | — | — | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | nextstep | 3 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | simple-english | 3 | 11 | 8 | 6–12 | 0–15 | — | — | — |
| noisy-output | baseline | 12 | 15 | 32 | 0–62 | 11–52 | — | — | — |
| noisy-output | adhd | 12 | 11 | 15 | 0–30 | 6–24 | -30.0% | 100% | — |
| noisy-output | caveman | 12 | 4 | 6 | 0–10 | 2–11 | -73.3% | 100% | — |
| noisy-output | hush | 12 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | nextstep | 12 | 0 | 1 | 0–0 | -1–2 | -100.0% | 100% | — |
| noisy-output | simple-english | 12 | 20 | 31 | 0–60 | 13–50 | +30.0% | 50% | dep-bump-warnings +17.6% |
| search-heavy | baseline | 6 | 3 | 8 | 0–14 | -0–16 | — | — | — |
| search-heavy | adhd | 6 | 10 | 10 | 2–13 | 2–19 | +233.3% | 0% | repo-summary +83.3% |
| search-heavy | caveman | 6 | 0 | 2 | 0–5 | -0–4 | -100.0% | 100% | — |
| search-heavy | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | nextstep | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | simple-english | 6 | 10 | 11 | 9–11 | 4–18 | +216.7% | 0% | repo-summary +83.3% |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.1789 | 0.1652 | 198839 | 98% | 23 |
| adhd | 51 | 0.1826 | 0.1761 | 194390 | 94% | 20 |
| caveman | 51 | 0.1749 | 0.1629 | 179203 | 98% | 21 |
| hush | 51 | 0.1813 | 0.1657 | 196587 | 98% | 25 |
| nextstep | 51 | 0.1825 | 0.1785 | 196276 | 94% | 23 |
| simple-english | 51 | 0.1904 | 0.1694 | 191703 | 96% | 22 |
