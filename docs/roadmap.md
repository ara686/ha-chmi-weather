# Roadmap

CHMI Weather is scoped to measured CHMI station data published into Home
Assistant. It should not implement CHMI text forecasts, alerts/warnings, radar
products, image entities, or camera entities.

## Done

- HACS-ready custom integration structure.
- UI config flow with nearest-station selection from official `meta1` station
  metadata.
- Async CHMI OpenData client.
- DataUpdateCoordinator polling.
- Weather entity and station-supported diagnostic sensors.
- Current station values from official `now/data` files.
- Station element capability filtering from official `meta2` metadata.
- `SRA1H` support for hourly precipitation when the station advertises it.
- `QUALITY` and `FLAG` diagnostics for selected current observation rows,
  including CHMI `meta3` flag descriptions and `meta4` quality-code
  descriptions when available.
- Data-quality details intentionally kept in diagnostics instead of regular
  disabled-by-default sensors.
- Tests, CI, and docs.

## TODO

- Add official CHMI station recent/daily summary support where data is available:
  `yesterday_precipitation`, `yesterday_temperature_max`,
  `yesterday_temperature_min`, `yesterday_wind_gust_max`, and
  `month_precipitation_chmi`.
- Improve the weather condition using station-measured elements when advertised,
  such as 1-hour SYNOP `ww`, `W1`, `W2`, `N`, `VV`, and `Td`.
- Add validation tests for additional station examples.

## Non-Goals

- Text forecast sensors or events.
- Weather alert or warning entities.
- Radar, image, or camera entities.
- Non-station CHMI products.
