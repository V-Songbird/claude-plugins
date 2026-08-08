# hush benchmark — generated claims

Generated from 60 retained run records · batch `nudgeladder-888376f1` · model `sonnet` · seed `1786151788484` · arms: baseline, hush, nudge0, nudge1, nudge3.

Segments: long-session, noisy-output, search-heavy.

## By segment

Every figure below is a per-segment distribution. Arms are compared task by task on medians, so one wild run cannot flip a task, and the worst single regression is named rather than averaged away.

### Cost per session <sub>(USD)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 0.6236 | 0.6020 | 0.4838–0.6993 | 0.4810–0.7229 | — | — | — |
| long-session | hush | 6 | 0.7756 | 1.0026 | 0.6584–0.9823 | 0.4477–1.5575 | +24.4% | 33% | feature-drift +249.7% |
| long-session | nudge0 | 6 | 0.5528 | 0.5829 | 0.4987–0.6243 | 0.4677–0.6982 | -11.3% | 67% | feature-drift +45.2% |
| long-session | nudge1 | 6 | 0.7077 | 0.7139 | 0.6644–0.7854 | 0.6448–0.7831 | +13.5% | 0% | feature-drift +38.4% |
| long-session | nudge3 | 6 | 0.7121 | 0.7431 | 0.6717–0.8517 | 0.6345–0.8517 | +14.2% | 0% | feature-drift +70.1% |
| noisy-output | baseline | 4 | 0.1868 | 0.1866 | 0.1765–0.1968 | 0.1648–0.2083 | — | — | — |
| noisy-output | hush | 4 | 0.2184 | 0.2224 | 0.2129–0.2279 | 0.2036–0.2412 | +16.9% | 0% | failing-suite +22.8% |
| noisy-output | nudge0 | 4 | 0.2096 | 0.2101 | 0.1961–0.2236 | 0.1939–0.2264 | +12.2% | 0% | failing-suite +14.6% |
| noisy-output | nudge1 | 4 | 0.1917 | 0.1953 | 0.1890–0.1981 | 0.1858–0.2049 | +2.6% | 50% | failing-suite +18.2% |
| noisy-output | nudge3 | 4 | 0.2094 | 0.2098 | 0.2029–0.2163 | 0.2007–0.2188 | +12.1% | 0% | failing-suite +21.6% |
| search-heavy | baseline | 2 | 0.6494 | 0.6494 | 0.6306–0.6683 | 0.5755–0.7234 | — | — | — |
| search-heavy | hush | 2 | 0.6347 | 0.6347 | 0.6204–0.6490 | 0.5786–0.6908 | -2.3% | 100% | — |
| search-heavy | nudge0 | 2 | 0.6550 | 0.6550 | 0.6414–0.6686 | 0.6018–0.7083 | +0.9% | 0% | repo-sweep +0.9% |
| search-heavy | nudge1 | 2 | 0.5781 | 0.5781 | 0.5758–0.5804 | 0.5691–0.5872 | -11.0% | 100% | — |
| search-heavy | nudge3 | 2 | 0.8167 | 0.8167 | 0.7163–0.9171 | 0.4231–1.2103 | +25.7% | 0% | repo-sweep +25.7% |

### Context traffic per session <sub>(Σ input+cache tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 889066 | 823933 | 758675–931085 | 644771–1003095 | — | — | — |
| long-session | hush | 6 | 874364 | 1123130 | 753446–1171577 | 592883–1653377 | -1.7% | 67% | feature-drift +170.4% |
| long-session | nudge0 | 6 | 784049 | 840270 | 716653–824303 | 673697–1006844 | -11.8% | 67% | feature-drift +54.8% |
| long-session | nudge1 | 6 | 840393 | 825831 | 727169–895550 | 731588–920073 | -5.5% | 67% | feature-drift +40.2% |
| long-session | nudge3 | 6 | 792439 | 929685 | 652526–1024437 | 600341–1259029 | -10.9% | 67% | feature-drift +85.3% |
| noisy-output | baseline | 4 | 214455 | 207069 | 190076–231447 | 176182–237956 | — | — | — |
| noisy-output | hush | 4 | 237187 | 238855 | 219185–256856 | 216368–261341 | +10.6% | 0% | failing-suite +19.3% |
| noisy-output | nudge0 | 4 | 234392 | 234784 | 215401–253774 | 212805–256763 | +9.3% | 0% | monorepo-build +18.0% |
| noisy-output | nudge1 | 4 | 216112 | 216175 | 215725–216562 | 214839–217510 | +0.8% | 50% | failing-suite +9.2% |
| noisy-output | nudge3 | 4 | 234898 | 226145 | 208906–252136 | 192406–259884 | +9.5% | 0% | failing-suite +18.2% |
| search-heavy | baseline | 2 | 510565 | 510565 | 479686–541443 | 389520–631609 | — | — | — |
| search-heavy | hush | 2 | 377304 | 377304 | 372319–382290 | 357761–396847 | -26.1% | 100% | — |
| search-heavy | nudge0 | 2 | 442458 | 442458 | 410428–474488 | 316900–568016 | -13.3% | 100% | — |
| search-heavy | nudge1 | 2 | 342270 | 342270 | 333458–351081 | 307729–376810 | -33.0% | 100% | — |
| search-heavy | nudge3 | 2 | 455005 | 455005 | 398570–511439 | 233780–676229 | -10.9% | 100% | — |

### Output tokens per session <sub>(tokens)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 9160 | 8665 | 6977–10509 | 6807–10523 | — | — | — |
| long-session | hush | 6 | 5862 | 5965 | 4395–6615 | 3873–8057 | -36.0% | 100% | — |
| long-session | nudge0 | 6 | 6845 | 6829 | 4460–9232 | 4684–8974 | -25.3% | 67% | feature-drift +6.4% |
| long-session | nudge1 | 6 | 8614 | 7669 | 5566–9990 | 5073–10264 | -6.0% | 100% | — |
| long-session | nudge3 | 6 | 8378 | 7704 | 4656–10432 | 4621–10787 | -8.5% | 67% | feature-drift +10.7% |
| noisy-output | baseline | 4 | 2023 | 2126 | 1258–2891 | 1061–3190 | — | — | — |
| noisy-output | hush | 4 | 2001 | 2095 | 1264–2832 | 1132–3058 | -1.1% | 50% | failing-suite +3.7% |
| noisy-output | nudge0 | 4 | 1831 | 1850 | 1138–2543 | 996–2704 | -9.5% | 100% | — |
| noisy-output | nudge1 | 4 | 1430 | 1430 | 1311–1549 | 1151–1708 | -29.3% | 50% | failing-suite +18.0% |
| noisy-output | nudge3 | 4 | 1878 | 1895 | 1376–2397 | 1236–2553 | -7.2% | 50% | failing-suite +9.4% |
| search-heavy | baseline | 2 | 10312 | 10312 | 10236–10387 | 10015–10608 | — | — | — |
| search-heavy | hush | 2 | 10085 | 10085 | 10007–10163 | 9779–10391 | -2.2% | 100% | — |
| search-heavy | nudge0 | 2 | 10309 | 10309 | 10240–10377 | 10039–10578 | -0.0% | 100% | — |
| search-heavy | nudge1 | 2 | 10146 | 10146 | 10135–10156 | 10103–10188 | -1.6% | 100% | — |
| search-heavy | nudge3 | 2 | 11510 | 11510 | 10654–12365 | 8157–14862 | +11.6% | 0% | repo-sweep +11.6% |

### Mid-turn narration per session <sub>(words)</sub>

| Segment | Arm | n | median | mean | p25–p75 | 95% CI | vs baseline (median) | win rate | worst task |
|---|---|---|---|---|---|---|---|---|---|
| long-session | baseline | 6 | 33 | 44 | 11–62 | 7–82 | — | — | — |
| long-session | hush | 6 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| long-session | nudge0 | 6 | 4 | 9 | 0–13 | -1–20 | -89.2% | 100% | — |
| long-session | nudge1 | 6 | 0 | 3 | 0–0 | -3–10 | -100.0% | 100% | — |
| long-session | nudge3 | 6 | 0 | 13 | 0–7 | -9–36 | -100.0% | 100% | — |
| noisy-output | baseline | 4 | 70 | 70 | 39–102 | 29–112 | — | — | — |
| noisy-output | hush | 4 | 0 | 4 | 0–4 | -4–11 | -100.0% | 100% | — |
| noisy-output | nudge0 | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| noisy-output | nudge1 | 4 | 0 | 9 | 0–9 | -9–27 | -100.0% | 100% | — |
| noisy-output | nudge3 | 4 | 0 | 0 | 0–0 | 0–0 | -100.0% | 100% | — |
| search-heavy | baseline | 2 | 135 | 135 | 128–141 | 110–159 | — | — | — |
| search-heavy | hush | 2 | 13 | 13 | 9–17 | -3–29 | -90.3% | 100% | — |
| search-heavy | nudge0 | 2 | 28 | 28 | 26–29 | 23–32 | -79.6% | 100% | — |
| search-heavy | nudge1 | 2 | 39 | 39 | 37–42 | 29–49 | -71.0% | 100% | — |
| search-heavy | nudge3 | 2 | 40 | 40 | 32–49 | 7–73 | -70.3% | 100% | — |

## Suite total

All segments pooled. Segments hold different numbers of tasks, so this line is a headline, not evidence — the per-segment tables above are the evidence.

| Arm | Runs | Mean cost USD | Median cost USD | Mean context traffic | Pass rate | Median wall s |
|---|---|---|---|---|---|---|
| baseline | 12 | 0.4714 | 0.5081 | 566084 | 100% | 87 |
| hush | 12 | 0.6812 | 0.6285 | 704067 | 100% | 77 |
| nudge0 | 12 | 0.4707 | 0.5123 | 572139 | 100% | 82 |
| nudge1 | 12 | 0.5184 | 0.5876 | 542018 | 100% | 78 |
| nudge3 | 12 | 0.5776 | 0.6400 | 616058 | 100% | 76 |
