# CHMI Weather

CHMI Weather is a Home Assistant custom integration for weather station data from
ČHMÚ OpenData. The MVP reads current 10-minute observations for one configured
station, creates a standard `weather` entity, and can expose diagnostic sensors
for the raw measured values.

The integration uses official ČHMÚ OpenData JSON endpoints only. It does not
scrape `chmi.cz` HTML pages.

## Status

This repository currently contains an MVP for the Dobrichovice station:

- Station name: `Dobrichovice`
- WSI / station ID: `0-203-0-11521`
- Latitude: `49.9335`
- Longitude: `14.2759`
- Current data endpoint pattern:
  `https://opendata.chmi.cz/meteorology/climate/now/data/10m-0-203-0-11521-YYYYMMDD.json`

`YYYYMMDD` is selected from the current UTC day. If today's file is missing or
empty, the integration tries yesterday's UTC file.

## Installation with HACS

1. Open HACS in Home Assistant.
2. Open the three-dot menu and choose Custom repositories.
3. Add `https://github.com/ara686/ha-chmi-weather`.
4. Select Integration as the repository type.
5. Install CHMI Weather.
6. Restart Home Assistant.

## Manual installation

1. Copy `custom_components/chmi_weather` into
   `/config/custom_components/chmi_weather` in Home Assistant.
2. Restart Home Assistant.

## Add the integration

1. Go to Settings -> Devices & services.
2. Choose Add integration.
3. Search for CHMI Weather.
4. Use the Dobrichovice defaults or enter another CHMI station:
   - Station name
   - WSI / station ID
   - Latitude
   - Longitude

During setup the integration validates that the station ID is not empty, the
OpenData endpoint is reachable, and at least one usable observation value can be
parsed.

## Entities

For Dobrichovice the MVP creates:

- `weather.chmi_dobrichovice`
- `sensor.chmi_dobrichovice_temperature`
- `sensor.chmi_dobrichovice_humidity`
- `sensor.chmi_dobrichovice_pressure`
- `sensor.chmi_dobrichovice_precipitation_10m`
- `sensor.chmi_dobrichovice_wind_speed`
- `sensor.chmi_dobrichovice_wind_gust`
- `sensor.chmi_dobrichovice_wind_direction`
- `sensor.chmi_dobrichovice_last_update`

All entities are attached to one Home Assistant device:

- Manufacturer: ČHMÚ
- Model: OpenData weather station
- Name: CHMI Dobrichovice
- Identifier: `("chmi_weather", "0-203-0-11521")`

## Known MVP limitations

- The MVP uses only current measured data from one station.
- Forecast is not implemented yet.
- The weather condition is best-effort: rain in the last 10 minutes maps to
  `rainy`; otherwise it maps to `partlycloudy`.
- Data quality and freshness depend on the ČHMÚ OpenData endpoint.
- The Dobrichovice current JSON currently does not include pressure element `P`,
  so pressure can be unavailable for this station.

## Troubleshooting

- If setup fails with a connection error, check Home Assistant network access to
  `https://opendata.chmi.cz`.
- If setup fails with no usable data, verify the station ID and the daily JSON
  file in a browser.
- If sensors are missing, check the integration options and ensure diagnostic
  sensors are enabled.
- Download diagnostics from Settings -> Devices & services -> CHMI Weather when
  opening an issue.

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run checks:

```bash
ruff check .
ruff format --check .
pytest
```

See `docs/development.md` and `AGENTS.md` before changing parser or Home
Assistant integration behavior.

## Roadmap

1. Current observations MVP.
2. Forecast source selection without fake forecast data.
3. Hourly and daily forecast entities using official ČHMÚ OpenData.
4. Radar or warning support if suitable official OpenData endpoints are stable.
