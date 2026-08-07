# hush benchmark — generated claims

Generated from 306 retained run records · batch `h2h-haiku-3ef718cd` · model `haiku` · seed `1786061500000` · arms: baseline, adhd, caveman, hush, nextstep, simple-english.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.0176 | 0.0262 | 0.0171–0.0348 | 0.0183–0.0341 | — | — | — |
| coding | adhd | 12 | 0.0207 | 0.0326 | 0.0202–0.0298 | 0.0198–0.0453 | +18.0% | 0% | refactor-rename +53.4% |
| coding | caveman | 12 | 0.0197 | 0.0296 | 0.0190–0.0318 | 0.0195–0.0396 | +12.2% | 0% | refactor-rename +25.5% |
| coding | hush | 12 | 0.0230 | 0.0348 | 0.0227–0.0377 | 0.0231–0.0464 | +31.0% | 0% | refactor-rename +43.4% |
| coding | nextstep | 12 | 0.0228 | 0.0364 | 0.0227–0.0347 | 0.0222–0.0507 | +29.9% | 0% | refactor-rename +56.7% |
| coding | simple-english | 12 | 0.0186 | 0.0271 | 0.0180–0.0274 | 0.0181–0.0361 | +5.5% | 0% | refactor-rename +10.9% |
| debugging | baseline | 18 | 0.0707 | 0.0771 | 0.0480–0.1085 | 0.0613–0.0929 | — | — | — |
| debugging | adhd | 18 | 0.0720 | 0.0805 | 0.0475–0.1235 | 0.0633–0.0976 | +2.0% | 17% | incident-pool-leak +16.3% |
| debugging | caveman | 18 | 0.0661 | 0.0733 | 0.0407–0.1122 | 0.0580–0.0887 | -6.4% | 67% | checkout-bug +10.8% |
| debugging | hush | 18 | 0.0698 | 0.0677 | 0.0511–0.0758 | 0.0597–0.0758 | -1.2% | 33% | checkout-bug +25.1% |
| debugging | nextstep | 18 | 0.0700 | 0.0690 | 0.0542–0.0795 | 0.0613–0.0767 | -1.0% | 33% | bugfix-expiry +29.6% |
| debugging | simple-english | 18 | 0.0705 | 0.0793 | 0.0435–0.1127 | 0.0621–0.0965 | -0.2% | 17% | coupon-currency-flaky +14.8% |
| doc-editing | baseline | 3 | 0.0605 | 0.0577 | 0.0545–0.0624 | 0.0484–0.0671 | — | — | — |
| doc-editing | adhd | 3 | 0.0652 | 0.0649 | 0.0645–0.0655 | 0.0637–0.0661 | +7.9% | 0% | runbook-edit +7.9% |
| doc-editing | caveman | 3 | 0.0534 | 0.0541 | 0.0530–0.0549 | 0.0519–0.0563 | -11.7% | 100% | — |
| doc-editing | hush | 3 | 0.0735 | 0.0743 | 0.0713–0.0769 | 0.0679–0.0807 | +21.6% | 0% | runbook-edit +21.6% |
| doc-editing | nextstep | 3 | 0.0817 | 0.0799 | 0.0782–0.0825 | 0.0748–0.0851 | +35.2% | 0% | runbook-edit +35.2% |
| doc-editing | simple-english | 3 | 0.0602 | 0.0634 | 0.0575–0.0677 | 0.0514–0.0754 | -0.4% | 100% | — |
| noisy-output | baseline | 12 | 0.0618 | 0.0614 | 0.0485–0.0749 | 0.0531–0.0698 | — | — | — |
| noisy-output | adhd | 12 | 0.0562 | 0.0619 | 0.0502–0.0757 | 0.0543–0.0694 | -9.1% | 25% | dep-bump-warnings +52.2% |
| noisy-output | caveman | 12 | 0.0583 | 0.0601 | 0.0470–0.0748 | 0.0523–0.0678 | -5.7% | 25% | dep-bump-warnings +29.1% |
| noisy-output | hush | 12 | 0.0549 | 0.0531 | 0.0337–0.0679 | 0.0424–0.0639 | -11.1% | 75% | dep-bump-warnings +33.2% |
| noisy-output | nextstep | 12 | 0.0505 | 0.0533 | 0.0333–0.0659 | 0.0410–0.0657 | -18.3% | 75% | dep-bump-warnings +46.7% |
| noisy-output | simple-english | 12 | 0.0582 | 0.0603 | 0.0539–0.0697 | 0.0541–0.0666 | -5.8% | 25% | dep-bump-warnings +26.4% |
| search-heavy | baseline | 6 | 0.0292 | 0.0290 | 0.0215–0.0359 | 0.0225–0.0354 | — | — | — |
| search-heavy | adhd | 6 | 0.0333 | 0.0339 | 0.0253–0.0398 | 0.0260–0.0418 | +14.1% | 0% | call-site-sweep +15.7% |
| search-heavy | caveman | 6 | 0.0348 | 0.0341 | 0.0281–0.0367 | 0.0274–0.0408 | +19.2% | 50% | call-site-sweep +24.4% |
| search-heavy | hush | 6 | 0.0352 | 0.0345 | 0.0295–0.0391 | 0.0294–0.0395 | +20.5% | 0% | call-site-sweep +35.6% |
| search-heavy | nextstep | 6 | 0.0359 | 0.0348 | 0.0289–0.0405 | 0.0296–0.0400 | +22.9% | 0% | call-site-sweep +34.8% |
| search-heavy | simple-english | 6 | 0.0293 | 0.0289 | 0.0229–0.0336 | 0.0236–0.0343 | +0.3% | 50% | call-site-sweep +6.5% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 21216 | 60811 | 21212–117276 | 26989–94634 | — | — | — |
| coding | adhd | 12 | 23026 | 81521 | 23022–62484 | 19342–143700 | +8.5% | 0% | refactor-rename +91.8% |
| coding | caveman | 12 | 22741 | 72937 | 22737–61586 | 20592–125282 | +7.2% | 0% | refactor-rename +63.8% |
| coding | hush | 12 | 23971 | 71650 | 23970–83750 | 25347–117953 | +13.0% | 0% | refactor-rename +50.4% |
| coding | nextstep | 12 | 24082 | 78402 | 24078–65355 | 20629–136175 | +13.5% | 0% | refactor-rename +54.9% |
| coding | simple-english | 12 | 21787 | 59390 | 21783–59366 | 20896–97885 | +2.7% | 0% | refactor-rename +20.8% |
| debugging | baseline | 18 | 253996 | 264122 | 169777–344905 | 209783–318462 | — | — | — |
| debugging | adhd | 18 | 272357 | 291734 | 155791–408296 | 227777–355690 | +7.2% | 17% | incident-pool-leak +37.0% |
| debugging | caveman | 18 | 270830 | 253480 | 144810–361492 | 204745–302215 | +6.6% | 17% | checkout-bug +17.0% |
| debugging | hush | 18 | 217442 | 226906 | 185791–267101 | 198114–255697 | -14.4% | 67% | bugfix-expiry +31.5% |
| debugging | nextstep | 18 | 233794 | 236636 | 185321–260567 | 206844–266428 | -8.0% | 50% | bugfix-expiry +34.4% |
| debugging | simple-english | 18 | 239455 | 269075 | 163184–348261 | 204403–333747 | -5.7% | 33% | incident-followup +14.8% |
| doc-editing | baseline | 3 | 221020 | 211865 | 194303–234005 | 166051–257679 | — | — | — |
| doc-editing | adhd | 3 | 238928 | 238541 | 238244–239033 | 237571–239511 | +8.1% | 0% | runbook-edit +8.1% |
| doc-editing | caveman | 3 | 179387 | 179206 | 179061–179442 | 178739–179672 | -18.8% | 100% | — |
| doc-editing | hush | 3 | 191515 | 209476 | 190581–219391 | 172426–246526 | -13.3% | 100% | — |
| doc-editing | nextstep | 3 | 252613 | 269097 | 250320–279633 | 232201–305993 | +14.3% | 0% | runbook-edit +14.3% |
| doc-editing | simple-english | 3 | 183033 | 177772 | 165869–192306 | 147414–208130 | -17.2% | 100% | — |
| noisy-output | baseline | 12 | 167030 | 135323 | 68647–179030 | 97266–173380 | — | — | — |
| noisy-output | adhd | 12 | 110942 | 149298 | 68797–227632 | 95141–203456 | -33.6% | 0% | dep-bump-warnings +70.3% |
| noisy-output | caveman | 12 | 122111 | 144924 | 68199–194903 | 90245–199603 | -26.9% | 25% | dep-bump-warnings +42.9% |
| noisy-output | hush | 12 | 140125 | 157659 | 75885–220179 | 105317–210001 | -16.1% | 0% | sidecar-follow +38.6% |
| noisy-output | nextstep | 12 | 158233 | 160185 | 75958–251484 | 106866–213504 | -5.3% | 25% | dep-bump-warnings +54.8% |
| noisy-output | simple-english | 12 | 124045 | 137144 | 66256–208416 | 91460–182829 | -25.7% | 0% | dep-bump-warnings +32.6% |
| search-heavy | baseline | 6 | 76843 | 76885 | 48574–105170 | 51952–101818 | — | — | — |
| search-heavy | adhd | 6 | 83302 | 95599 | 52723–113768 | 50863–140335 | +8.4% | 0% | call-site-sweep +8.4% |
| search-heavy | caveman | 6 | 86349 | 95297 | 71713–94188 | 55893–134700 | +12.4% | 50% | call-site-sweep +60.8% |
| search-heavy | hush | 6 | 74732 | 74629 | 55116–93495 | 56124–93135 | -2.7% | 50% | call-site-sweep +12.9% |
| search-heavy | nextstep | 6 | 86947 | 78782 | 55148–100332 | 58537–99027 | +13.1% | 50% | call-site-sweep +13.5% |
| search-heavy | simple-english | 6 | 78380 | 74851 | 49869–90211 | 52484–97218 | +2.0% | 50% | call-site-sweep +2.6% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 694 | 1153 | 598–1485 | 679–1626 | — | — | — |
| coding | adhd | 12 | 720 | 1248 | 621–1279 | 633–1863 | +3.7% | 50% | explain-rebase +39.4% |
| coding | caveman | 12 | 630 | 1122 | 487–1816 | 619–1625 | -9.2% | 75% | refactor-rename +1.1% |
| coding | hush | 12 | 681 | 1147 | 625–1357 | 663–1631 | -1.9% | 50% | explain-rebase +10.5% |
| coding | nextstep | 12 | 603 | 1108 | 564–1091 | 554–1663 | -13.0% | 50% | refactor-rename +3.5% |
| coding | simple-english | 12 | 665 | 1147 | 544–1202 | 593–1700 | -4.2% | 75% | refactor-rename +6.1% |
| debugging | baseline | 18 | 2841 | 2796 | 2069–3006 | 2321–3271 | — | — | — |
| debugging | adhd | 18 | 2638 | 2422 | 1813–2900 | 2100–2745 | -7.1% | 100% | — |
| debugging | caveman | 18 | 2127 | 2106 | 1330–2577 | 1733–2478 | -25.1% | 100% | — |
| debugging | hush | 18 | 2656 | 2552 | 1587–3103 | 2119–2986 | -6.5% | 67% | incident-followup +9.0% |
| debugging | nextstep | 18 | 2385 | 2598 | 1866–3211 | 2209–2988 | -16.1% | 33% | checkout-bug +9.6% |
| debugging | simple-english | 18 | 2802 | 2757 | 1779–3350 | 2295–3219 | -1.4% | 50% | coupon-currency-flaky +28.6% |
| doc-editing | baseline | 3 | 3202 | 2962 | 2760–3285 | 2323–3602 | — | — | — |
| doc-editing | adhd | 3 | 3244 | 3208 | 3150–3285 | 3052–3364 | +1.3% | 0% | runbook-edit +1.3% |
| doc-editing | caveman | 3 | 2500 | 2591 | 2452–2685 | 2313–2869 | -21.9% | 100% | — |
| doc-editing | hush | 3 | 3520 | 3381 | 3261–3571 | 3004–3758 | +9.9% | 0% | runbook-edit +9.9% |
| doc-editing | nextstep | 3 | 3213 | 3339 | 3118–3497 | 2892–3785 | +0.3% | 0% | runbook-edit +0.3% |
| doc-editing | simple-english | 3 | 3359 | 4128 | 3332–4540 | 2567–5688 | +4.9% | 0% | runbook-edit +4.9% |
| noisy-output | baseline | 12 | 1442 | 1535 | 1194–2071 | 1164–1906 | — | — | — |
| noisy-output | adhd | 12 | 1639 | 1626 | 1124–2159 | 1229–2023 | +13.6% | 50% | sidecar-follow +20.7% |
| noisy-output | caveman | 12 | 1344 | 1386 | 796–1914 | 1019–1753 | -6.8% | 50% | sidecar-follow +41.5% |
| noisy-output | hush | 12 | 1367 | 1576 | 829–2265 | 1128–2024 | -5.2% | 50% | sidecar-follow +35.0% |
| noisy-output | nextstep | 12 | 1634 | 1452 | 847–1872 | 1094–1810 | +13.3% | 50% | sidecar-follow +41.9% |
| noisy-output | simple-english | 12 | 1852 | 1586 | 1062–2096 | 1231–1942 | +28.4% | 50% | sidecar-follow +41.7% |
| search-heavy | baseline | 6 | 1117 | 1173 | 700–1640 | 747–1599 | — | — | — |
| search-heavy | adhd | 6 | 1307 | 1233 | 749–1687 | 801–1664 | +17.0% | 50% | repo-summary +0.6% |
| search-heavy | caveman | 6 | 1078 | 1075 | 799–1294 | 770–1380 | -3.5% | 50% | call-site-sweep +10.4% |
| search-heavy | hush | 6 | 1253 | 1158 | 982–1392 | 859–1456 | +12.1% | 50% | call-site-sweep +37.0% |
| search-heavy | nextstep | 6 | 1185 | 1155 | 869–1463 | 875–1434 | +6.1% | 50% | call-site-sweep +24.3% |
| search-heavy | simple-english | 6 | 1023 | 1032 | 687–1375 | 708–1356 | -8.4% | 100% | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 19 | 0–29 | 1–38 | — | — | — |
| coding | adhd | 12 | 0 | 9 | 0–6 | -1–20 | — | 100% | — |
| coding | caveman | 12 | 0 | 2 | 0–0 | -2–6 | — | 100% | — |
| coding | hush | 12 | 0 | 0 | 0–0 | 0–0 | — | 100% | — |
| coding | nextstep | 12 | 0 | 0 | 0–0 | 0–0 | — | 100% | — |
| coding | simple-english | 12 | 0 | 18 | 0–10 | -2–39 | — | 0% | refactor-rename +15.9% |
| debugging | baseline | 18 | 112 | 113 | 89–139 | 82–143 | — | — | — |
| debugging | adhd | 18 | 79 | 73 | 40–106 | 53–94 | -29.5% | 80% | bugfix-pagination +11.6% |
| debugging | caveman | 18 | 38 | 42 | 28–66 | 29–54 | -66.5% | 100% | — |
| debugging | hush | 18 | 0 | 7 | 0–0 | -6–19 | -100.0% | 100% | — |
| debugging | nextstep | 18 | 0 | 6 | 0–0 | -2–13 | -100.0% | 100% | — |
| debugging | simple-english | 18 | 107 | 116 | 71–173 | 86–146 | -4.9% | 60% | checkout-bug +29.6% |
| doc-editing | baseline | 3 | 28 | 29 | 28–31 | 26–33 | — | — | — |
| doc-editing | adhd | 3 | 13 | 12 | 7–19 | -1–26 | -53.6% | 100% | — |
| doc-editing | caveman | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| doc-editing | nextstep | 3 | 0 | 6 | 0–9 | -5–17 | -100.0% | 100% | — |
| doc-editing | simple-english | 3 | 36 | 33 | 25–42 | 13–52 | +28.6% | 0% | runbook-edit +28.6% |
| noisy-output | baseline | 12 | 45 | 51 | 8–92 | 23–78 | — | — | — |
| noisy-output | adhd | 12 | 22 | 33 | 0–55 | 12–55 | -51.7% | 100% | — |
| noisy-output | caveman | 12 | 7 | 11 | 0–16 | 3–18 | -85.4% | 100% | — |
| noisy-output | hush | 12 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | nextstep | 12 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | simple-english | 12 | 48 | 49 | 0–88 | 22–77 | +6.7% | 67% | noisy-build +4.5% |
| search-heavy | baseline | 6 | 12 | 9 | 3–14 | 3–14 | — | — | — |
| search-heavy | adhd | 6 | 8 | 8 | 8–10 | 4–11 | -33.3% | 100% | — |
| search-heavy | caveman | 6 | 0 | 2 | 0–3 | -1–4 | -100.0% | 100% | — |
| search-heavy | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | nextstep | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | simple-english | 6 | 17 | 14 | 11–20 | 7–21 | +37.5% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.0547 | 0.0485 | 160877 | 100% | 29 |
| adhd | 51 | 0.0584 | 0.0545 | 182554 | 96% | 29 |
| caveman | 51 | 0.0542 | 0.0492 | 162478 | 100% | 25 |
| hush | 51 | 0.0530 | 0.0505 | 155142 | 96% | 31 |
| nextstep | 51 | 0.0543 | 0.0540 | 164755 | 96% | 33 |
| simple-english | 51 | 0.0557 | 0.0530 | 160474 | 92% | 27 |
