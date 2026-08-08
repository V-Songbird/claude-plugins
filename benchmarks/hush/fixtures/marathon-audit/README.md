# acme service

A single deployable carrying the public API, the internal endpoints and the
reporting layer.

- `src/routes/` — one file per resource, grouped by area
- `src/service/` — the logic behind each route
- `src/repo/` — direct database access
- `config/` — one file per environment
- `NOTES.md` — running notes from the platform team

Routes are mounted in `src/app.js`. Anything under `/internal` was originally
reachable only over the VPN.
