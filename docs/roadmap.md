# Roadmap

## Phase 1 - Current observation MVP

- HACS-ready custom integration structure.
- UI config flow with Dobrichovice defaults.
- Async CHMI OpenData client.
- DataUpdateCoordinator polling.
- Weather entity and diagnostic sensors.
- Tests, CI, and docs.

## Phase 2 - Station selection

- Use official `meta1` OpenData metadata to normalize station names and
  coordinates.
- Offer nearest stations by distance from user-entered GPS coordinates.
- Use official `meta2` OpenData metadata to select diagnostic sensors supported
  by the station.
- Add validation tests for additional station examples.
- Consider using Home Assistant location defaults more prominently in the picker.

## Phase 3 - Forecast

- Identify official ČHMÚ forecast OpenData endpoints.
- Add options for forecast source selection.
- Implement hourly and daily forecast methods only after data mapping is clear.
- Do not fake forecast data from current observations.

## Phase 4 - Additional products

- Evaluate official radar and warning OpenData endpoints.
- Add separate entities only where Home Assistant has a clear entity model.
- Keep each new data source behind parser fixtures and tests.
