# hush benchmark — generated claims

Generated from 48 retained run records · batch `terse-cb21d29f` · model `sonnet` · seed `1786167821765` · arms: baseline, allnudge, hush, terse.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.4708 | 0.4965 | 0.3248–0.6503 | 0.3384–0.6547 | — | — | — |
| long-session | allnudge | 6 | 0.6357 | 0.6246 | 0.5060–0.7574 | 0.4861–0.7631 | +35.0% | 0% | feature-drift +62.0% |
| long-session | hush | 6 | 0.5963 | 0.6248 | 0.5647–0.6864 | 0.5402–0.7094 | +26.6% | 33% | feature-drift +81.7% |
| long-session | terse | 6 | 0.5852 | 0.5900 | 0.4535–0.7139 | 0.4547–0.7254 | +24.3% | 33% | feature-drift +94.2% |
| noisy-output | baseline | 4 | 0.2105 | 0.2191 | 0.1985–0.2311 | 0.1731–0.2651 | — | — | — |
| noisy-output | allnudge | 4 | 0.2171 | 0.2278 | 0.2026–0.2423 | 0.1922–0.2634 | +3.2% | 50% | monorepo-build +13.3% |
| noisy-output | hush | 4 | 0.2331 | 0.2513 | 0.2187–0.2656 | 0.1957–0.3068 | +10.8% | 0% | failing-suite +18.3% |
| noisy-output | terse | 4 | 0.2368 | 0.2445 | 0.2205–0.2607 | 0.1960–0.2929 | +12.5% | 0% | failing-suite +18.7% |
| search-heavy | baseline | 2 | 0.6683 | 0.6683 | 0.6174–0.7192 | 0.4689–0.8678 | — | — | — |
| search-heavy | allnudge | 2 | 0.6402 | 0.6402 | 0.6202–0.6603 | 0.5617–0.7188 | -4.2% | 100% | — |
| search-heavy | hush | 2 | 0.6106 | 0.6106 | 0.6099–0.6113 | 0.6078–0.6134 | -8.6% | 100% | — |
| search-heavy | terse | 2 | 0.6771 | 0.6771 | 0.6711–0.6832 | 0.6535–0.7008 | +1.3% | 0% | repo-sweep +1.3% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 608574 | 628322 | 376521–807161 | 395375–861268 | — | — | — |
| long-session | allnudge | 6 | 735570 | 672529 | 504046–814808 | 508494–836564 | +20.9% | 33% | feature-drift +64.3% |
| long-session | hush | 6 | 711039 | 733923 | 670645–752284 | 633572–834275 | +16.8% | 33% | feature-drift +104.2% |
| long-session | terse | 6 | 622179 | 625814 | 528102–694373 | 530491–721137 | +2.2% | 67% | feature-drift +78.2% |
| noisy-output | baseline | 4 | 215880 | 230497 | 197662–248715 | 184382–276611 | — | — | — |
| noisy-output | allnudge | 4 | 257621 | 274713 | 209333–323001 | 178551–370875 | +19.3% | 0% | failing-suite +31.1% |
| noisy-output | hush | 4 | 249900 | 259764 | 249233–260430 | 239885–279643 | +15.8% | 0% | failing-suite +27.1% |
| noisy-output | terse | 4 | 253935 | 253938 | 216295–291579 | 210967–296909 | +17.6% | 50% | failing-suite +29.6% |
| search-heavy | baseline | 2 | 889326 | 889326 | 599187–1179465 | -248019–2026671 | — | — | — |
| search-heavy | allnudge | 2 | 343245 | 343245 | 336916–349573 | 318438–368051 | -61.4% | 100% | — |
| search-heavy | hush | 2 | 356322 | 356322 | 346000–366644 | 315860–396784 | -59.9% | 100% | — |
| search-heavy | terse | 2 | 353600 | 353600 | 334225–372976 | 277648–429552 | -60.2% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 7374 | 7205 | 5599–8984 | 5164–9246 | — | — | — |
| long-session | allnudge | 6 | 8235 | 7389 | 4715–9064 | 4844–9933 | +11.7% | 33% | feature-drift +11.7% |
| long-session | hush | 6 | 7682 | 7327 | 5033–9249 | 5268–9387 | +4.2% | 33% | feature-drift +33.9% |
| long-session | terse | 6 | 9358 | 8242 | 5116–9973 | 4835–11649 | +26.9% | 67% | feature-drift +59.0% |
| noisy-output | baseline | 4 | 1678 | 1969 | 1286–2361 | 974–2963 | — | — | — |
| noisy-output | allnudge | 4 | 1842 | 1851 | 1324–2370 | 1234–2468 | +9.8% | 50% | failing-suite +5.7% |
| noisy-output | hush | 4 | 2046 | 2022 | 1416–2653 | 1198–2846 | +21.9% | 0% | failing-suite +6.4% |
| noisy-output | terse | 4 | 1495 | 1692 | 1327–1860 | 930–2453 | -10.9% | 100% | — |
| search-heavy | baseline | 2 | 9923 | 9923 | 9819–10027 | 9515–10331 | — | — | — |
| search-heavy | allnudge | 2 | 10643 | 10643 | 10485–10800 | 10024–11261 | +7.3% | 0% | repo-sweep +7.3% |
| search-heavy | hush | 2 | 10317 | 10317 | 10072–10563 | 9355–11279 | +4.0% | 0% | repo-sweep +4.0% |
| search-heavy | terse | 2 | 11249 | 11249 | 11175–11324 | 10957–11541 | +13.4% | 0% | repo-sweep +13.4% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 7 | 22 | 0–29 | -5–49 | — | — | — |
| long-session | allnudge | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| long-session | hush | 6 | 0 | 5 | 0–0 | -5–16 | -100.0% | 100% | — |
| long-session | terse | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 4 | 59 | 61 | 26–94 | 20–102 | — | — | — |
| noisy-output | allnudge | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | hush | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | terse | 4 | 0 | 2 | 0–2 | -2–7 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 76 | 76 | 75–76 | 73–78 | — | — | — |
| search-heavy | allnudge | 2 | 8 | 8 | 6–9 | 3–12 | -90.1% | 100% | — |
| search-heavy | hush | 2 | 11 | 11 | 11–12 | 9–13 | -85.4% | 100% | — |
| search-heavy | terse | 2 | 14 | 14 | 13–14 | 11–16 | -82.1% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4327 | 0.3281 | 539214 | 100% | 75 |
| allnudge | 12 | 0.4949 | 0.5316 | 485043 | 100% | 74 |
| hush | 12 | 0.4979 | 0.5717 | 512937 | 100% | 80 |
| terse | 12 | 0.4893 | 0.4806 | 456486 | 100% | 76 |
