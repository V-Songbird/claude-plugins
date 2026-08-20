# Changelog

## 4.1.0 — 2026-05-02

### Breaking
- The `timeout` option is now milliseconds everywhere. It used to be seconds
  on the HTTP client and milliseconds everywhere else.

### Added
- Idempotency keys on every write endpoint.

### Fixed
- A retry after a 429 no longer drops the request body.

## 4.0.3 — 2026-04-11

### Fixed
- The client no longer hangs when the server closes mid-body.

<!-- 4.2.0 goes here. Same three headings, same order. Only write down what
     someone installing this package would notice. -->
