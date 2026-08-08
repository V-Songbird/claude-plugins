# hush benchmark — generated claims

Generated from 153 retained run records · batch `cost3-haiku-ecb659d2` · model `haiku` · seed `1786120000000` · arms: baseline, caveman, hush.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0.0180 | 0.0270 | 0.0175–0.0268 | 0.0175–0.0365 | — | — | — |
| coding | caveman | 12 | 0.0195 | 0.0278 | 0.0189–0.0273 | 0.0189–0.0366 | +8.0% | 25% | explain-rebase +12.2% |
| coding | hush | 12 | 0.0239 | 0.0344 | 0.0230–0.0363 | 0.0234–0.0454 | +32.5% | 0% | explain-rebase +37.6% |
| debugging | baseline | 18 | 0.0701 | 0.0789 | 0.0601–0.1135 | 0.0644–0.0934 | — | — | — |
| debugging | caveman | 18 | 0.0677 | 0.0763 | 0.0561–0.1028 | 0.0616–0.0910 | -3.4% | 50% | bugfix-expiry +6.4% |
| debugging | hush | 18 | 0.0663 | 0.0662 | 0.0571–0.0760 | 0.0599–0.0725 | -5.3% | 33% | bugfix-pagination +12.7% |
| doc-editing | baseline | 3 | 0.0595 | 0.0594 | 0.0591–0.0598 | 0.0586–0.0602 | — | — | — |
| doc-editing | caveman | 3 | 0.0615 | 0.0621 | 0.0613–0.0626 | 0.0605–0.0636 | +3.3% | 0% | runbook-edit +3.3% |
| doc-editing | hush | 3 | 0.0761 | 0.0745 | 0.0705–0.0793 | 0.0645–0.0845 | +27.8% | 0% | runbook-edit +27.8% |
| noisy-output | baseline | 12 | 0.0555 | 0.0568 | 0.0449–0.0686 | 0.0495–0.0641 | — | — | — |
| noisy-output | caveman | 12 | 0.0600 | 0.0613 | 0.0520–0.0692 | 0.0552–0.0673 | +8.1% | 0% | noisy-build +25.3% |
| noisy-output | hush | 12 | 0.0575 | 0.0539 | 0.0329–0.0644 | 0.0417–0.0661 | +3.6% | 50% | noisy-build +90.6% |
| search-heavy | baseline | 6 | 0.0290 | 0.0312 | 0.0225–0.0376 | 0.0225–0.0399 | — | — | — |
| search-heavy | caveman | 6 | 0.0307 | 0.0313 | 0.0274–0.0348 | 0.0277–0.0349 | +5.8% | 50% | call-site-sweep +22.5% |
| search-heavy | hush | 6 | 0.0356 | 0.0356 | 0.0311–0.0402 | 0.0307–0.0405 | +22.8% | 0% | call-site-sweep +40.4% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 21329 | 64355 | 21325–57889 | 19875–108835 | — | — | — |
| coding | caveman | 12 | 22854 | 61912 | 22850–54830 | 21367–102457 | +7.2% | 25% | write-validator +7.2% |
| coding | hush | 12 | 24084 | 67960 | 24083–77545 | 25190–110730 | +12.9% | 25% | write-validator +12.9% |
| debugging | baseline | 18 | 230013 | 257308 | 166103–353226 | 206645–307970 | — | — | — |
| debugging | caveman | 18 | 231823 | 248809 | 170695–297113 | 200287–297330 | +0.8% | 33% | bugfix-expiry +23.3% |
| debugging | hush | 18 | 199411 | 207147 | 152351–259293 | 178270–236024 | -13.3% | 33% | coupon-currency-flaky +38.1% |
| doc-editing | baseline | 3 | 221073 | 221132 | 221002–221233 | 220864–221400 | — | — | — |
| doc-editing | caveman | 3 | 234181 | 242833 | 234036–247304 | 225590–260076 | +5.9% | 0% | runbook-edit +5.9% |
| doc-editing | hush | 3 | 248555 | 238875 | 218568–264023 | 186571–291179 | +12.4% | 0% | runbook-edit +12.4% |
| noisy-output | baseline | 12 | 116624 | 122710 | 65346–176166 | 85282–160137 | — | — | — |
| noisy-output | caveman | 12 | 117903 | 137813 | 68403–209206 | 92710–182915 | +1.1% | 0% | noisy-build +24.5% |
| noisy-output | hush | 12 | 166865 | 157756 | 75883–225402 | 107324–208188 | +43.1% | 25% | noisy-build +53.0% |
| search-heavy | baseline | 6 | 76808 | 99695 | 48831–121605 | 43684–155706 | — | — | — |
| search-heavy | caveman | 6 | 71228 | 82704 | 70161–89821 | 66601–98807 | -7.3% | 50% | call-site-sweep +61.0% |
| search-heavy | hush | 6 | 74936 | 79185 | 73771–94506 | 63363–95006 | -2.4% | 50% | call-site-sweep +69.9% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 741 | 1203 | 633–1318 | 654–1752 | — | — | — |
| coding | caveman | 12 | 539 | 962 | 432–1050 | 467–1457 | -27.2% | 100% | — |
| coding | hush | 12 | 817 | 1138 | 634–1204 | 686–1590 | +10.3% | 50% | explain-rebase +34.5% |
| debugging | baseline | 18 | 2591 | 2774 | 1729–3024 | 2135–3414 | — | — | — |
| debugging | caveman | 18 | 2424 | 2190 | 1449–2685 | 1912–2467 | -6.4% | 83% | incident-followup +7.3% |
| debugging | hush | 18 | 2283 | 2320 | 1650–2775 | 1949–2690 | -11.9% | 83% | incident-followup +6.8% |
| doc-editing | baseline | 3 | 3043 | 3042 | 2993–3091 | 2931–3153 | — | — | — |
| doc-editing | caveman | 3 | 2755 | 2758 | 2736–2780 | 2708–2808 | -9.5% | 100% | — |
| doc-editing | hush | 3 | 3169 | 3131 | 2916–3366 | 2620–3642 | +4.1% | 0% | runbook-edit +4.1% |
| noisy-output | baseline | 12 | 1489 | 1456 | 804–1962 | 1049–1862 | — | — | — |
| noisy-output | caveman | 12 | 1753 | 1584 | 865–2201 | 1231–1936 | +17.7% | 50% | sidecar-follow +144.3% |
| noisy-output | hush | 12 | 1816 | 1520 | 840–2064 | 1143–1896 | +21.9% | 50% | sidecar-follow +22.1% |
| search-heavy | baseline | 6 | 1149 | 1129 | 778–1541 | 744–1513 | — | — | — |
| search-heavy | caveman | 6 | 933 | 959 | 695–1204 | 726–1192 | -18.8% | 100% | — |
| search-heavy | hush | 6 | 1276 | 1228 | 874–1534 | 906–1549 | +11.0% | 0% | call-site-sweep +3.8% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | baseline | 12 | 0 | 20 | 0–19 | -1–40 | — | — | — |
| coding | caveman | 12 | 0 | 2 | 0–0 | -2–6 | — | 100% | — |
| coding | hush | 12 | 0 | 0 | 0–0 | 0–0 | — | 100% | — |
| debugging | baseline | 18 | 131 | 115 | 83–158 | 87–143 | — | — | — |
| debugging | caveman | 18 | 31 | 38 | 13–68 | 24–52 | -76.3% | 100% | — |
| debugging | hush | 18 | 0 | 1 | 0–0 | -1–2 | -100.0% | 100% | — |
| doc-editing | baseline | 3 | 16 | 15 | 8–23 | -2–32 | — | — | — |
| doc-editing | caveman | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| doc-editing | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 12 | 47 | 52 | 0–85 | 22–82 | — | — | — |
| noisy-output | caveman | 12 | 4 | 10 | 0–14 | 2–17 | -91.5% | 100% | — |
| noisy-output | hush | 12 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 6 | 12 | 9 | 3–14 | 3–14 | — | — | — |
| search-heavy | caveman | 6 | 0 | 1 | 0–0 | -1–2 | -100.0% | 100% | — |
| search-heavy | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 51 | 0.0547 | 0.0542 | 159566 | 100% | 27 |
| caveman | 51 | 0.0552 | 0.0541 | 158823 | 96% | 24 |
| hush | 51 | 0.0527 | 0.0566 | 149588 | 94% | 28 |
