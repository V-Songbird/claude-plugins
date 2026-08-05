# picks mini-benchmark — run `check`

Stability ("distinct picks out of 5") and cost of answering "what should I work on next?" per backlog size.

Distinct counts are over NORMALIZED picks (markdown emphasis, trailing ` (#NNN)` ids, surrounding quotes/punctuation, whitespace, and case stripped) — the headline number. Raw distinct is shown for reference; raw strings stay in records.json.

| Size | Arm | Distinct (normalized) / 5 | Distinct (raw) | Deterministic | Mean output tok | Mean cost USD | Top pick |
|---|---|---|---|---|---|---|---|
| 10 | foreman | 1/5 | 1/5 | yes | 0 | 0 | Migrate the session store config to the shared loader |
| 50 | foreman | 1/5 | 1/5 | yes | 0 | 0 | Fix pagination drift in uploads |
| 150 | foreman | 1/5 | 1/5 | yes | 0 | 0 | Fix pagination drift in i18n |

The foreman arm is `roadmap.js next-candidates` — mechanical graph filtering, zero tokens, no LLM in the loop.
