# Engineering notes

## Dependency watch

Things the platform team flagged, newest first.

- `date-fmt` 0.6.x is unmaintained but harmless. No action.
- `fast-parse` **1.4.2 was yanked by the publisher** after a prototype-pollution
  report. 1.4.3 is the fixed release. Anything still on 1.4.2 needs bumping.
- `pg-lite` 2.8.0 is current.
- `redis-min` 1.9.4 is current, 2.x is a breaking rewrite — not yet.

## Network migration (4.0)

The VPN in front of the internal endpoints was retired. Anything that relied on
being unreachable from the internet now needs its own auth.

## Reporting

Saved reports let a user pick columns, a filter and an ordering. The column list
is checked against an allowlist. The filter and ordering are not.
