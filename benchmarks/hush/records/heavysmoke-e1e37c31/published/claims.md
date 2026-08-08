# hush benchmark — generated claims

Generated from 12 retained run records · batch `heavysmoke-e1e37c31` · model `sonnet` · seed `1786150253947` · arms: baseline, hush.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 3 | 0.5556 | 0.5659 | 0.5336–0.5930 | 0.4979–0.6339 | — | — | — |
| long-session | hush | 3 | 0.7562 | 0.6392 | 0.5623–0.7746 | 0.3730–0.9054 | +36.1% | 33% | feature-drift +42.7% |
| noisy-output | baseline | 2 | 0.2669 | 0.2669 | 0.2341–0.2998 | 0.1383–0.3956 | — | — | — |
| noisy-output | hush | 2 | 0.2754 | 0.2754 | 0.2507–0.3001 | 0.1787–0.3721 | +3.2% | 50% | monorepo-build +12.3% |
| search-heavy | baseline | 1 | 0.5937 | 0.5937 | 0.5937–0.5937 | — | — | — | — |
| search-heavy | hush | 1 | 0.6091 | 0.6091 | 0.6091–0.6091 | — | +2.6% | 0% | repo-sweep +2.6% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 3 | 800561 | 790092 | 769021–816397 | 735508–844676 | — | — | — |
| long-session | hush | 3 | 855607 | 726159 | 650557–866486 | 450845–1001474 | +6.9% | 33% | feature-drift +19.0% |
| noisy-output | baseline | 2 | 249690 | 249690 | 242858–256521 | 222909–276470 | — | — | — |
| noisy-output | hush | 2 | 243747 | 243747 | 234582–252911 | 207823–279670 | -2.4% | 100% | — |
| search-heavy | baseline | 1 | 315131 | 315131 | 315131–315131 | — | — | — | — |
| search-heavy | hush | 1 | 332321 | 332321 | 332321–332321 | — | +5.5% | 0% | repo-sweep +5.5% |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 3 | 11439 | 9622 | 8486–11667 | 5606–13638 | — | — | — |
| long-session | hush | 3 | 11590 | 9298 | 7010–12732 | 2444–16152 | +1.3% | 33% | feature-drift +16.6% |
| noisy-output | baseline | 2 | 2011 | 2011 | 1854–2169 | 1394–2628 | — | — | — |
| noisy-output | hush | 2 | 1714 | 1714 | 1539–1888 | 1030–2397 | -14.8% | 100% | — |
| search-heavy | baseline | 1 | 10206 | 10206 | 10206–10206 | — | — | — | — |
| search-heavy | hush | 1 | 10612 | 10612 | 10612–10612 | — | +4.0% | 0% | repo-sweep +4.0% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 3 | 28 | 46 | 14–69 | -19–111 | — | — | — |
| long-session | hush | 3 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | baseline | 2 | 87 | 87 | 78–97 | 50–124 | — | — | — |
| noisy-output | hush | 2 | 6 | 6 | 3–8 | -5–16 | -93.7% | 100% | — |
| search-heavy | baseline | 1 | 32 | 32 | 32–32 | — | — | — | — |
| search-heavy | hush | 1 | 8 | 8 | 8–8 | — | -75.0% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 6 | 0.4709 | 0.5336 | 530798 | 100% | 90 |
| hush | 6 | 0.5129 | 0.4887 | 499715 | 100% | 75 |
