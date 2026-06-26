# Roadmap

## Phase 1 - Current observation MVP

- HACS-ready custom integration structure.
- UI config flow with Dobrichovice defaults.
- Async CHMI OpenData client.
- DataUpdateCoordinator polling.
- Weather entity and diagnostic sensors.
- Tests, CI, and docs.

## Phase 2 - Station selection

- Document how to discover CHMI station IDs from official OpenData metadata.
- Add validation tests for additional station examples.
- Consider a station picker if a suitable official metadata endpoint is stable.

## Phase 3 - Forecast

- Identify official ČHMÚ forecast OpenData endpoints.
- Add options for forecast source selection.
- Implement hourly and daily forecast methods only after data mapping is clear.
- Do not fake forecast data from current observations.

## Phase 4 - Additional products

- Evaluate official radar and warning OpenData endpoints.
- Add separate entities only where Home Assistant has a clear entity model.
- Keep each new data source behind parser fixtures and tests.
