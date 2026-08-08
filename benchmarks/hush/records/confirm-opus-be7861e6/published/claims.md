# hush benchmark — generated claims

Generated from 102 retained run records · batch `confirm-opus-be7861e6` · model `opus` · seed `1786140000000` · arms: firstcall, hush, lookfurther.

Segments: coding, debugging, doc-editing, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 0.2387 | 0.2655 | 0.1650–0.3773 | 0.1886–0.3424 | — | — | — |
| coding | hush | 8 | 0.1716 | 0.2125 | 0.1428–0.2451 | 0.1432–0.2819 | — | — | — |
| coding | lookfurther | 8 | 0.2119 | 0.2319 | 0.1487–0.2890 | 0.1621–0.3017 | — | — | — |
| debugging | firstcall | 12 | 0.3818 | 0.4321 | 0.3030–0.4950 | 0.3378–0.5264 | — | — | — |
| debugging | hush | 12 | 0.3624 | 0.3996 | 0.3291–0.3823 | 0.3057–0.4935 | — | — | — |
| debugging | lookfurther | 12 | 0.4136 | 0.5572 | 0.3655–0.8109 | 0.3906–0.7237 | — | — | — |
| doc-editing | firstcall | 2 | 0.5550 | 0.5550 | 0.5446–0.5654 | 0.5144–0.5956 | — | — | — |
| doc-editing | hush | 2 | 0.5751 | 0.5751 | 0.5521–0.5981 | 0.4850–0.6652 | — | — | — |
| doc-editing | lookfurther | 2 | 0.6632 | 0.6632 | 0.6587–0.6677 | 0.6456–0.6808 | — | — | — |
| noisy-output | firstcall | 8 | 0.3134 | 0.3112 | 0.2711–0.3415 | 0.2755–0.3469 | — | — | — |
| noisy-output | hush | 8 | 0.2858 | 0.3061 | 0.2551–0.3168 | 0.2453–0.3668 | — | — | — |
| noisy-output | lookfurther | 8 | 0.2960 | 0.3034 | 0.2514–0.3350 | 0.2507–0.3560 | — | — | — |
| search-heavy | firstcall | 4 | 0.2428 | 0.2507 | 0.1972–0.2962 | 0.1887–0.3126 | — | — | — |
| search-heavy | hush | 4 | 0.3151 | 0.3182 | 0.1949–0.4384 | 0.1785–0.4578 | — | — | — |
| search-heavy | lookfurther | 4 | 0.3207 | 0.3414 | 0.2131–0.4489 | 0.1763–0.5065 | — | — | — |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 82210 | 139077 | 52650–224625 | 64494–213660 | — | — | — |
| coding | hush | 8 | 66137 | 96078 | 44880–113755 | 38206–153950 | — | — | — |
| coding | lookfurther | 8 | 80678 | 106670 | 44914–156557 | 48683–164657 | — | — | — |
| debugging | firstcall | 12 | 247409 | 272435 | 230152–330644 | 233815–311055 | — | — | — |
| debugging | hush | 12 | 240208 | 254242 | 188281–267950 | 204504–303981 | — | — | — |
| debugging | lookfurther | 12 | 277801 | 345388 | 233151–440495 | 247466–443309 | — | — | — |
| doc-editing | firstcall | 2 | 364992 | 364992 | 358857–371126 | 340943–389040 | — | — | — |
| doc-editing | hush | 2 | 393769 | 393769 | 385318–402219 | 360642–426895 | — | — | — |
| doc-editing | lookfurther | 2 | 512704 | 512704 | 506241–519166 | 487371–538036 | — | — | — |
| noisy-output | firstcall | 8 | 198308 | 201411 | 190880–206957 | 181912–220910 | — | — | — |
| noisy-output | hush | 8 | 198935 | 194265 | 185903–202684 | 171229–217300 | — | — | — |
| noisy-output | lookfurther | 8 | 199816 | 194155 | 181415–213434 | 166798–221512 | — | — | — |
| search-heavy | firstcall | 4 | 129147 | 133406 | 106443–156110 | 102138–164673 | — | — | — |
| search-heavy | hush | 4 | 149275 | 161412 | 106297–204390 | 96060–226763 | — | — | — |
| search-heavy | lookfurther | 4 | 170893 | 181183 | 99948–252128 | 77724–284642 | — | — | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 2436 | 2881 | 1765–3537 | 1795–3968 | — | — | — |
| coding | hush | 8 | 1807 | 1906 | 1338–2549 | 1484–2329 | — | — | — |
| coding | lookfurther | 8 | 2280 | 2324 | 1608–2904 | 1783–2865 | — | — | — |
| debugging | firstcall | 12 | 1884 | 3193 | 1218–4255 | 1719–4666 | — | — | — |
| debugging | hush | 12 | 2040 | 2711 | 871–2753 | 1303–4118 | — | — | — |
| debugging | lookfurther | 12 | 3745 | 5094 | 1196–7789 | 2602–7585 | — | — | — |
| doc-editing | firstcall | 2 | 4736 | 4736 | 4385–5086 | 3363–6108 | — | — | — |
| doc-editing | hush | 2 | 4920 | 4920 | 4404–5436 | 2897–6943 | — | — | — |
| doc-editing | lookfurther | 2 | 5398 | 5398 | 5240–5557 | 4777–6019 | — | — | — |
| noisy-output | firstcall | 8 | 1830 | 2246 | 1655–2949 | 1618–2874 | — | — | — |
| noisy-output | hush | 8 | 1888 | 2004 | 1496–2372 | 1505–2504 | — | — | — |
| noisy-output | lookfurther | 8 | 2265 | 2485 | 1450–2849 | 1582–3387 | — | — | — |
| search-heavy | firstcall | 4 | 1576 | 1706 | 1088–2194 | 970–2441 | — | — | — |
| search-heavy | hush | 4 | 1615 | 1657 | 1028–2244 | 936–2378 | — | — | — |
| search-heavy | lookfurther | 4 | 2142 | 2458 | 1871–2729 | 1073–3843 | — | — | — |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| coding | firstcall | 8 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| coding | hush | 8 | 0 | 1 | 0–0 | -1–2 | — | — | — |
| coding | lookfurther | 8 | 0 | 2 | 0–0 | -2–5 | — | — | — |
| debugging | firstcall | 12 | 0 | 4 | 0–8 | 1–6 | — | — | — |
| debugging | hush | 12 | 0 | 2 | 0–5 | 1–4 | — | — | — |
| debugging | lookfurther | 12 | 6 | 4 | 0–6 | 2–6 | — | — | — |
| doc-editing | firstcall | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | hush | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| doc-editing | lookfurther | 2 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| noisy-output | firstcall | 8 | 0 | 1 | 0–0 | -1–3 | — | — | — |
| noisy-output | hush | 8 | 0 | 3 | 0–7 | 0–6 | — | — | — |
| noisy-output | lookfurther | 8 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | firstcall | 4 | 3 | 3 | 0–6 | -0–7 | — | — | — |
| search-heavy | hush | 4 | 0 | 0 | 0–0 | 0–0 | — | — | — |
| search-heavy | lookfurther | 4 | 0 | 0 | 0–0 | 0–0 | — | — | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| firstcall | 34 | 0.3504 | 0.3196 | 213433 | 94% | 42 |
| hush | 34 | 0.3343 | 0.3252 | 200201 | 94% | 39 |
| lookfurther | 34 | 0.4018 | 0.3489 | 244159 | 100% | 47 |
