# Changelog

## 0.1.3

- Select the shortest CHMI OpenData observation interval advertised by station
  `meta2` metadata instead of assuming every station should use `10m` files.
- Cap the effective coordinator polling interval to the station observation
  interval, so existing entries with a longer saved option start polling at the
  best available interval after reload.
- Added diagnostics for advertised observation interval, configured update
  interval, and effective update interval.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required; station capabilities are refreshed during
  setup.
- Breaking changes: none.

## 0.1.2

- Renamed the displayed `last_update` diagnostic sensor to `Observation time`
  to clarify that it shows the CHMI observation timestamp.
- Added a `Last successful poll` diagnostic sensor showing when Home Assistant
  last successfully downloaded CHMI OpenData.
- Updated coordinator notifications so diagnostic poll timestamps refresh even
  when CHMI returns the same observation values.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required.
- Breaking changes: none.

## 0.1.1

- Added `SECURITY.md` with vulnerability reporting guidance and dependency audit
  scope.
- Added CI security checks for the published integration code using Bandit and
  pip-audit.
- Hardened CHMI station ID handling before building OpenData URLs.
- Updated GitHub Actions runtime versions.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required.
- Breaking changes: none.

## 0.1.0

- Initial MVP scaffold for CHMI Weather.
- Added CHMI OpenData current-observation parser and async API client.
- Added Home Assistant config flow, DataUpdateCoordinator, weather entity,
  diagnostic sensors, diagnostics, tests, docs, and CI.
