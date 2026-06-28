# CHMI Weather

> [!WARNING]
> CHMI Weather is experimental software under active development. It is not
> recommended for production use. Install and use it at your own risk, and do
> not rely on it for safety-critical, life-critical, property protection,
> emergency, operational, or compliance decisions.

CHMI Weather is a Home Assistant custom integration for weather station data from
ČHMÚ OpenData. The MVP reads current observations for one configured station at
the shortest interval advertised by official CHMI metadata, creates a standard
`weather` entity, and can expose diagnostic sensors for the raw measured values.

The integration uses official ČHMÚ OpenData JSON endpoints only. It does not
scrape `chmi.cz` HTML pages.

This project is not affiliated with, endorsed by, certified by, or supported by
CHMI, Home Assistant, HACS, Nabu Casa, or the Open Home Foundation.

## Status

This repository currently contains a development-preview MVP for current CHMI
OpenData station observations. APIs, entity behavior, configuration flow,
diagnostics, and supported station data may change without notice until the
project reaches a stable release.

During setup, Home Assistant suggests nearby stations from the official CHMI
station metadata and stores the selected WSI / station ID.

Dobřichovice is the reference station used by fixtures and manual test scripts:

- Station name: `Dobřichovice`
- WSI / station ID: `0-203-0-11521`
- Latitude: `49.9335`
- Longitude: `14.2759`
- Best advertised observation interval: `10M`
- Current data endpoint pattern for the selected interval:
  `https://opendata.chmi.cz/meteorology/climate/now/data/10m-0-203-0-11521-YYYYMMDD.json`

`YYYYMMDD` is selected from the current UTC day. If today's file is missing or
empty, the integration tries yesterday's UTC file.

## Installation with HACS

Use HACS installation only for testing and development systems. For normal HACS
custom repository installation, the GitHub repository must be public or otherwise
accessible to the Home Assistant instance through a configured GitHub account.

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
4. Use the Home Assistant location if it is configured, or enter GPS
   coordinates for the target location.
5. Select one of the nearest CHMI OpenData stations offered by the integration.

During setup the integration loads official `meta1` station metadata, sorts the
nearest stations by distance from the configured Home Assistant location or
entered GPS coordinates, and stores the selected WSI / station ID. If Home
Assistant has no configured location, the coordinate fields are not prefilled. It
then validates that the OpenData endpoint is reachable and at least one usable
observation value can be parsed. Supported diagnostic sensors are selected from
the official OpenData `meta2` file for the station, so Home Assistant only
exposes values the station advertises for the selected observation interval. The
same metadata is used to select the shortest available observation interval for
the station. Current CHMI metadata commonly advertises `10M` and `1H`; when both
are available, the integration uses `10M`.

The update interval option is capped by the selected station observation
interval. For example, if a station advertises `10M` data and an older config
entry still has `60` minutes saved, the coordinator polls every 10 minutes. This
affects new Home Assistant history from the next polling cycles onward; it does
not retroactively fill missing history.

## Entities

For Dobřichovice, when the station advertises the supported elements currently
present in the official `meta2` file, the integration creates:

- `weather.chmi_dobrichovice`
- `sensor.chmi_dobrichovice_temperature`
- `sensor.chmi_dobrichovice_humidity`
- `sensor.chmi_dobrichovice_precipitation_10m`
- `sensor.chmi_dobrichovice_precipitation_1h`
- `sensor.chmi_dobrichovice_precipitation_today`
- `sensor.chmi_dobrichovice_wind_speed`
- `sensor.chmi_dobrichovice_wind_gust`
- `sensor.chmi_dobrichovice_wind_direction`
- `sensor.chmi_dobrichovice_observation_time`
- `sensor.chmi_dobrichovice_last_successful_poll`

Existing Home Assistant installations may keep the older entity ID
`sensor.chmi_dobrichovice_last_update`; the entity unique ID is kept stable, but
the displayed name is `Observation time`. It shows the timestamp published by
CHMI for the latest station observation. `Last successful poll` shows when Home
Assistant last successfully downloaded data from CHMI OpenData.

`Precipitation 10m` is the raw CHMI `SRA10M` interval value. `Precipitation 1h`
is the sum of the latest hour of available `SRA10M` rows in the selected CHMI
daily file. `Precipitation today` is the cumulative sum of `SRA10M` rows in the
current CHMI daily file and uses the `total_increasing` state class so Home
Assistant can derive calendar rainfall totals with Utility Meter helpers.

All entities are attached to one Home Assistant device:

- Manufacturer: ČHMÚ
- Model: OpenData weather station
- Name: CHMI Dobřichovice
- Identifier: `("chmi_weather", "0-203-0-11521")`

## Known MVP limitations

- The integration is under active development and is not production-ready.
- The MVP uses only current measured data from one station.
- Forecast is not implemented yet.
- The weather condition is best-effort: rain in the last 10 minutes maps to
  `rainy`; otherwise it maps to `partlycloudy`.
- Data quality and freshness depend on the ČHMÚ OpenData endpoint.
- Home Assistant history only records data after the integration polls
  successfully; CHMI data already missed by an older polling configuration is
  not backfilled.
- The Dobřichovice `meta2` metadata currently does not advertise pressure
  element `P`, so the pressure diagnostic sensor is not created for this station.
- Direct `Precipitation 1h` and `Precipitation today` values are limited to rows
  available in the selected CHMI daily file. Home Assistant Utility Meter history
  continues from the states recorded by Home Assistant after the integration is
  installed.

## Home Assistant statistics

Numeric CHMI Weather sensors expose Home Assistant state classes where the value
semantics fit long-term statistics. Use native Home Assistant statistics cards or
Statistics helpers for weather extrema and averages such as daily, weekly, or
monthly temperature maximums, humidity averages, pressure trends, wind gust
maximums, and circular wind-direction means.

For rainfall cycles, use `sensor.chmi_dobrichovice_precipitation_today` as the
source for Home Assistant Utility Meter helpers with `delta_values` left
disabled. Do not use `sensor.chmi_dobrichovice_precipitation_10m` directly as a
Utility Meter source; it is a per-observation interval value, not a cumulative
meter. See `docs/statistics.md` for example hourly, daily, weekly, and monthly
rainfall helpers.

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
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
pytest tests_ha -o asyncio_mode=auto
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` runs fast parser and entity unit tests
without loading Home Assistant's pytest plugin into the stub test environment.
`pytest tests_ha -o asyncio_mode=auto` loads the custom integration through Home
Assistant test fixtures and should be run before deployment-oriented changes.

See `docs/development.md` and `AGENTS.md` before changing parser or Home
Assistant integration behavior.

## License and Notices

The source code is licensed under the MIT License. See `LICENSE`.

This software is provided as-is, without warranty, and without a support
guarantee. See `DISCLAIMER.md` for project risk and support limitations.

CHMI OpenData is a third-party data source. CHMI states that its open data may be
used free of charge when respecting the Creative Commons Attribution 4.0
International license (CC BY 4.0). Runtime entities expose CHMI OpenData
attribution, and fixture data is documented separately in
`tests/fixtures/README.md`. See `NOTICE.md` for data attribution and third-party
notices.

See `SECURITY.md` for vulnerability reporting and dependency audit scope.

## Roadmap

1. Current observations MVP.
2. Forecast source selection without fake forecast data.
3. Hourly and daily forecast entities using official ČHMÚ OpenData.
4. Radar or warning support if suitable official OpenData endpoints are stable.
