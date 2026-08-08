# hush benchmark — generated claims

Generated from 102 retained run records · batch `confirm-sonnet-0ebc013e` · model `sonnet` · seed `1786140000000` · arms: firstcall, hush, lookfurther.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 0.0922 | 0.1229 | 0.0838–0.1290 | 0.0777–0.1680 | — | — | — |
| coding | hush | 8 | 0.0815 | 0.1152 | 0.0790–0.1191 | 0.0720–0.1584 | — | — | — |
| coding | lookfurther | 8 | 0.0813 | 0.1195 | 0.0786–0.1218 | 0.0690–0.1700 | — | — | — |
| debugging | firstcall | 12 | 0.1968 | 0.2238 | 0.1618–0.2630 | 0.1756–0.2720 | — | — | — |
| debugging | hush | 12 | 0.2207 | 0.2326 | 0.1823–0.2611 | 0.1881–0.2770 | — | — | — |
| debugging | lookfurther | 12 | 0.2077 | 0.2323 | 0.1636–0.2551 | 0.1790–0.2855 | — | — | — |
| doc-editing | firstcall | 2 | 0.2774 | 0.2774 | 0.2682–0.2866 | 0.2414–0.3135 | — | — | — |
| doc-editing | hush | 2 | 0.2612 | 0.2612 | 0.2594–0.2629 | 0.2545–0.2679 | — | — | — |
| doc-editing | lookfurther | 2 | 0.2677 | 0.2677 | 0.2633–0.2722 | 0.2503–0.2852 | — | — | — |
| noisy-output | firstcall | 8 | 0.1915 | 0.1917 | 0.1702–0.2074 | 0.1623–0.2211 | — | — | — |
| noisy-output | hush | 8 | 0.1889 | 0.1868 | 0.1705–0.2092 | 0.1662–0.2074 | — | — | — |
| noisy-output | lookfurther | 8 | 0.1865 | 0.1840 | 0.1703–0.1949 | 0.1627–0.2053 | — | — | — |
| search-heavy | firstcall | 4 | 0.1638 | 0.1660 | 0.1517–0.1781 | 0.1311–0.2010 | — | — | — |
| search-heavy | hush | 4 | 0.1490 | 0.1484 | 0.1349–0.1625 | 0.1095–0.1873 | — | — | — |
| search-heavy | lookfurther | 4 | 0.1588 | 0.1614 | 0.1526–0.1676 | 0.1485–0.1743 | — | — | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 48063 | 106612 | 31939–118914 | 23824–189401 | — | — | — |
| coding | hush | 8 | 31930 | 93340 | 31926–99819 | 18229–168451 | — | — | — |
| coding | lookfurther | 8 | 31966 | 103418 | 31962–103381 | 11730–195105 | — | — | — |
| debugging | firstcall | 12 | 193191 | 231446 | 168540–258627 | 178690–284201 | — | — | — |
| debugging | hush | 12 | 245154 | 248731 | 165372–290198 | 199409–298053 | — | — | — |
| debugging | lookfurther | 12 | 198225 | 235576 | 165423–265237 | 183817–287335 | — | — | — |
| doc-editing | firstcall | 2 | 393853 | 393853 | 375514–412191 | 321967–465738 | — | — | — |
| doc-editing | hush | 2 | 355565 | 355565 | 354169–356960 | 350095–361034 | — | — | — |
| doc-editing | lookfurther | 2 | 374200 | 374200 | 365519–382880 | 340171–408228 | — | — | — |
| noisy-output | firstcall | 8 | 194615 | 195425 | 150977–241959 | 152797–238053 | — | — | — |
| noisy-output | hush | 8 | 203322 | 200572 | 160921–242419 | 158011–243133 | — | — | — |
| noisy-output | lookfurther | 8 | 189014 | 192167 | 161020–218825 | 153491–230842 | — | — | — |
| search-heavy | firstcall | 4 | 119249 | 128670 | 104424–143495 | 94017–163323 | — | — | — |
| search-heavy | hush | 4 | 131896 | 117311 | 114920–134287 | 82702–151920 | — | — | — |
| search-heavy | lookfurther | 4 | 132096 | 126123 | 125415–132803 | 113005–139241 | — | — | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 671 | 1041 | 563–1264 | 471–1610 | — | — | — |
| coding | hush | 8 | 446 | 847 | 280–924 | 221–1473 | — | — | — |
| coding | lookfurther | 8 | 421 | 871 | 239–1027 | 192–1549 | — | — | — |
| debugging | firstcall | 12 | 1367 | 1329 | 892–1683 | 1019–1639 | — | — | — |
| debugging | hush | 12 | 1546 | 1531 | 670–2169 | 1073–1989 | — | — | — |
| debugging | lookfurther | 12 | 1572 | 1676 | 679–1789 | 997–2354 | — | — | — |
| doc-editing | firstcall | 2 | 2465 | 2465 | 2336–2593 | 1960–2969 | — | — | — |
| doc-editing | hush | 2 | 2313 | 2313 | 2266–2361 | 2127–2499 | — | — | — |
| doc-editing | lookfurther | 2 | 2330 | 2330 | 2281–2379 | 2138–2522 | — | — | — |
| noisy-output | firstcall | 8 | 990 | 1154 | 895–1137 | 852–1456 | — | — | — |
| noisy-output | hush | 8 | 1111 | 1490 | 960–1908 | 941–2039 | — | — | — |
| noisy-output | lookfurther | 8 | 1139 | 1212 | 895–1575 | 947–1476 | — | — | — |
| search-heavy | firstcall | 4 | 1762 | 1690 | 1211–2241 | 985–2396 | — | — | — |
| search-heavy | hush | 4 | 1672 | 1564 | 1347–1890 | 912–2216 | — | — | — |
| search-heavy | lookfurther | 4 | 1868 | 2129 | 1566–2431 | 1122–3136 | — | — | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 0 | 8 | 0–5 | -3–18 | — | — | — |
| coding | hush | 8 | 0 | 7 | 0–6 | -2–15 | — | — | — |
| coding | lookfurther | 8 | 0 | 6 | 0–5 | -2–14 | — | — | — |
| debugging | firstcall | 12 | 0 | 3 | 0–0 | -1–8 | — | — | — |
| debugging | hush | 12 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| debugging | lookfurther | 12 | 0 | 3 | 0–0 | -3–9 | — | — | — |
| doc-editing | firstcall | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | hush | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | lookfurther | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | firstcall | 8 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | hush | 8 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | lookfurther | 8 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | firstcall | 4 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | hush | 4 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | lookfurther | 4 | 0 | 0 | 0–0 | 0–0 | — | — | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| firstcall | 34 | 0.1889 | 0.1813 | 191060 | 88% | 24 |
| hush | 34 | 0.1860 | 0.1918 | 191660 | 94% | 26 |
| lookfurther | 34 | 0.1881 | 0.1822 | 189543 | 97% | 26 |
