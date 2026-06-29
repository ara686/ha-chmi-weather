# Changelog

## Unreleased

- Excluded `pytest-homeassistant-custom-component` from Dependabot version
  updates so the Home Assistant stable test harness stays manually verified.

## 0.2.1

- Cleaned project status documentation to describe the implemented station-data
  scope while keeping the experimental non-production warning.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required.
- Breaking changes: none.

## 0.2.0

- Clarified that CHMI Weather is scoped only to measured station data published
  into Home Assistant.
- Removed the unused forecast source option from the integration options UI.
- Added station-data scope documentation and documented text forecasts,
  alerts/warnings, radar products, image entities, and camera entities as
  non-goals.
- Added CHMI `meta3` and `meta4` metadata loading so diagnostics include flag
  descriptions and official quality-code descriptions when available.
- Documented that CHMI data-quality details stay in diagnostics instead of
  separate disabled-by-default sensors.
- Added recent daily summary sensors from official CHMI `recent/data/daily`
  files for yesterday precipitation, yesterday temperature maximum/minimum,
  yesterday wind gust maximum, and CHMI month precipitation.
- Improved the Home Assistant weather condition by using station-measured SYNOP
  elements such as `ww`, `N`, `VV`, `Td`, `W1`, and `W2` when CHMI advertises
  them.
- Added parser validation fixtures for an additional CHMI station with pressure
  and SYNOP `1H` elements.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required; station capabilities are refreshed during
  setup, and new sensors appear when CHMI publishes matching station data.
- Breaking changes: none.

## 0.1.6

- Added current-station sensors for 10-minute temperature extrema, apparent
  temperature, average wind speed, average wind direction, and wind gust
  direction when advertised by CHMI `meta2`.
- Use raw hourly CHMI `SRA1H` for `Precipitation 1h` when the station advertises
  it, while keeping the existing `SRA10M` rolling-hour fallback.
- Added selected CHMI `QUALITY` and `FLAG` values to diagnostics.
- Updated CHMI OpenData docs, statistics guidance, translations, fixtures, and
  tests for the expanded current data set.
- Migration: no user action required; station capabilities are refreshed during
  setup.
- Breaking changes: none.

## 0.1.5

- Fixed `Precipitation today` to use the Home Assistant local date by combining
  current and previous UTC CHMI daily files, so rain after local midnight is not
  dropped when CHMI rolls over to a new UTC file.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required.
- Breaking changes: none.

## 0.1.4

- Added `Precipitation 1h` and `Precipitation today` diagnostic sensors derived
  from official CHMI `SRA10M` current-observation rows.
- Marked `Precipitation today` as `total_increasing` so Home Assistant Utility
  Meter helpers can derive hourly, daily, weekly, monthly, or yearly rainfall
  totals.
- Documented recommended Home Assistant Statistics and Utility Meter usage for
  weather extrema, averages, and rainfall totals.
- Compatibility: validated with Home Assistant stable and beta test harnesses.
- Migration: no user action required; new rainfall sensors appear for stations
  that advertise `SRA10M`.
- Breaking changes: none.

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

- Initial custom integration scaffold for CHMI Weather.
- Added CHMI OpenData current-observation parser and async API client.
- Added Home Assistant config flow, DataUpdateCoordinator, weather entity,
  diagnostic sensors, diagnostics, tests, docs, and CI.
