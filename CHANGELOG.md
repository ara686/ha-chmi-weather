# Changelog

## Unreleased

- Renamed the displayed `last_update` diagnostic sensor to `Observation time`
  to clarify that it shows the CHMI observation timestamp.
- Added a `Last successful poll` diagnostic sensor showing when Home Assistant
  last successfully downloaded CHMI OpenData.
- Updated coordinator notifications so diagnostic poll timestamps refresh even
  when CHMI returns the same observation values.

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
