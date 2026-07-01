# Status and Scope

CHMI Weather publishes measured CHMI station data into Home Assistant.

## Implemented Station-Data Scope

- HACS-ready custom integration structure.
- UI config flow with nearest-station selection from official `meta1` station
  metadata.
- Async CHMI OpenData client.
- DataUpdateCoordinator polling.
- Weather entity and station-supported measurement sensors.
- Current station values from official `now/data` files.
- Station element capability filtering from official `meta2` metadata.
- Shortest advertised station observation interval selection.
- `SRA1H` support for hourly precipitation when the station advertises it.
- `QUALITY` and `FLAG` diagnostics for selected current observation rows,
  including CHMI `meta3` flag descriptions and `meta4` quality-code
  descriptions when available.
- Data-quality details intentionally kept in diagnostics instead of regular
  disabled-by-default sensors.
- Official CHMI recent daily summary sensors for yesterday precipitation,
  yesterday temperature maximum/minimum, yesterday wind gust maximum, and
  precipitation this month.
- Weather condition mapping from station-measured SYNOP elements when
  advertised, including `ww`, `N`, `VV`, `Td`, `W1`, and `W2`.
- Parser validation fixtures for additional station examples beyond
  Dobrichovice, including a station with pressure and SYNOP `1H` elements.
- Tests, CI, and documentation.

## Non-Goals

- Text forecast sensors or events.
- Weather alert or warning entities.
- Radar, image, or camera entities.
- Non-station CHMI products.
