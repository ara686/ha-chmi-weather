# CHMI Weather

> [!WARNING]
> CHMI Weather is experimental software under active development. It is not
> recommended for production use. Install and use it at your own risk, and do
> not rely on it for safety-critical, life-critical, property protection,
> emergency, operational, or compliance decisions.

CHMI Weather is a Home Assistant custom integration for weather station data from
ČHMÚ OpenData. The integration reads measured data for one configured station,
including current observations at the shortest interval advertised by official
CHMI metadata and selected recent daily station summaries. It creates a standard
`weather` entity, regular sensor entities for measured station values, and
technical diagnostic sensors for troubleshooting timestamps.
The project scope is limited to measured CHMI station data published into Home
Assistant.

The integration uses official ČHMÚ OpenData JSON endpoints only. It does not
scrape `chmi.cz` HTML pages.

CHMI text forecasts, weather alerts/warnings, radar products, image entities, and
camera entities are intentionally out of scope for this integration.

This project is not affiliated with, endorsed by, certified by, or supported by
CHMI, Home Assistant, HACS, Nabu Casa, or the Open Home Foundation.

## Status

The current station-data scope is implemented: one configured CHMI station,
current observations, selected recent daily station summaries,
capability-filtered sensors, diagnostics, and a Home Assistant weather entity.
The integration remains experimental while it is validated on multiple Home
Assistant installations.

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
observation value can be parsed. Supported sensors are selected from the
official OpenData `meta2` file for the station, so Home Assistant only exposes
values the station advertises for the selected observation interval. The
same metadata is used to select the shortest available observation interval for
the station. Current CHMI metadata commonly advertises `10M` and `1H`; when both
are available, the integration uses `10M`. If the station also advertises hourly
`SRA1H`, the integration may fetch the matching `1h` file and use that value for
the `Precipitation 1h` sensor.

The `Enable technical diagnostic sensors` option controls only troubleshooting
timestamp sensors such as `Observation time` and `Last successful poll`.
Measured station values such as precipitation, temperature, humidity, pressure,
and wind remain regular Home Assistant sensor entities.

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
- `sensor.chmi_dobrichovice_temperature_maximum_10m`
- `sensor.chmi_dobrichovice_temperature_minimum_10m`
- `sensor.chmi_dobrichovice_apparent_temperature`
- `sensor.chmi_dobrichovice_humidity`
- `sensor.chmi_dobrichovice_precipitation_10m`
- `sensor.chmi_dobrichovice_precipitation_1h`
- `sensor.chmi_dobrichovice_precipitation_today`
- `sensor.chmi_dobrichovice_precipitation_this_month`
- `sensor.chmi_dobrichovice_wind_speed`
- `sensor.chmi_dobrichovice_average_wind_speed`
- `sensor.chmi_dobrichovice_wind_gust`
- `sensor.chmi_dobrichovice_wind_direction`
- `sensor.chmi_dobrichovice_average_wind_direction`
- `sensor.chmi_dobrichovice_wind_gust_direction`
- `sensor.chmi_dobrichovice_observation_time`
- `sensor.chmi_dobrichovice_last_successful_poll`

Existing Home Assistant installations may keep the older entity ID
`sensor.chmi_dobrichovice_last_update`; the entity unique ID is kept stable, but
the displayed name is `Observation time`. It shows the timestamp published by
CHMI for the latest station observation. `Last successful poll` shows when Home
Assistant last successfully downloaded data from CHMI OpenData. These two
timestamp entities are categorized as Home Assistant diagnostic entities; the
measured station values above are regular sensor entities.

Existing Home Assistant installations may also keep the older entity ID
`sensor.chmi_dobrichovice_chmi_month_precipitation`; the entity unique ID is
kept stable, but the displayed name is `Precipitation this month`.

`Precipitation 10m` is the raw CHMI `SRA10M` interval value. `Precipitation 1h`
uses raw CHMI `SRA1H` when the station advertises it; otherwise it falls back to
the sum of the latest hour of available `SRA10M` rows. `Precipitation today` is
the cumulative sum of `SRA10M` rows for the current Home Assistant local date and
uses the `total_increasing` state class so Home Assistant can derive calendar
rainfall totals with Utility Meter helpers.

Rainfall sensors suggest one decimal place for Home Assistant display precision,
matching the 0.1 mm resolution CHMI commonly publishes. If an existing entity
still displays whole millimeters, check whether Home Assistant has a stored
entity display-precision override for that sensor.

`Precipitation this month` comes from official CHMI `recent/data/daily` station
files. The monthly precipitation value is the sum of usable daily `SRA` rows in
the current monthly CHMI daily file up to the last completed local date. If CHMI
publishes station rows for the month but no usable `SRA` rows yet, the value is
`0.0` instead of `Unknown`. During temporary incomplete daily updates, the
integration keeps the last known value from the same month.

All entities are attached to one Home Assistant device:

- Manufacturer: ČHMÚ
- Model: OpenData weather station
- Name: CHMI Dobřichovice
- Identifier: `("chmi_weather", "0-203-0-11521")`

## Known limitations

- The integration uses measured data for one configured station, including
  current observations and selected official CHMI recent daily station
  summaries.
- Text forecasts, weather alerts/warnings, radar products, image entities, and
  camera entities are outside the project scope.
- The weather condition is best-effort. When the station advertises SYNOP
  elements such as `ww`, `N`, `VV`, `Td`, `W1`, or `W2`, the integration uses
  those measured station values. Otherwise it falls back to recent
  precipitation and then `partlycloudy`.
- Data quality and freshness depend on the ČHMÚ OpenData endpoint.
- Home Assistant history only records data after the integration polls
  successfully; CHMI data already missed by an older polling configuration is
  not backfilled.
- The Dobřichovice `meta2` metadata currently does not advertise pressure
  element `P`, so the pressure sensor is not created for this station.
- Direct `Precipitation 1h` and `Precipitation today` values are limited to rows
  available in the current and previous UTC CHMI `now/data` files. Home Assistant
  Utility Meter history continues from the states recorded by Home Assistant
  after the integration is installed.
- `Precipitation this month` depends on CHMI `recent/data/daily` files. It
  appears as unavailable if CHMI has not published a usable monthly daily file
  for the station yet and there is no last known same-month value to keep.
- CHMI data quality flags are available in integration diagnostics, not as
  normal sensor attributes.

## Home Assistant statistics

Numeric CHMI Weather sensors expose Home Assistant state classes where the value
semantics fit long-term statistics. Use native Home Assistant statistics cards or
Statistics helpers for weather extrema and averages such as daily, weekly, or
monthly temperature maximums, humidity averages, pressure trends, wind gust
maximums, average wind speed, and circular wind-direction means.

For rainfall cycles, use `sensor.chmi_dobrichovice_precipitation_today` as the
source for Home Assistant Utility Meter helpers with `delta_values` left
disabled. Do not use `sensor.chmi_dobrichovice_precipitation_10m` directly as a
Utility Meter source; it is a per-observation interval value, not a cumulative
meter. Use `sensor.chmi_dobrichovice_precipitation_this_month` when you want the
official CHMI month-to-date daily-summary total instead of a Home Assistant
Utility Meter total built from integration history. See `docs/statistics.md` for
example hourly, daily, weekly, and monthly rainfall helpers.

## Troubleshooting

- If setup fails with a connection error, check Home Assistant network access to
  `https://opendata.chmi.cz`.
- If setup fails with no usable data, verify the station ID and the daily JSON
  file in a browser.
- If measured sensors are missing, check the selected station capabilities in
  diagnostics and verify that the station advertises the related CHMI element.
- If `Observation time` or `Last successful poll` are missing, ensure technical
  diagnostic sensors are enabled in the integration options.
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
GitHub Actions also runs HACS repository validation and Home Assistant hassfest
metadata validation on pull requests, pushes, scheduled checks, and manual runs.

Translations live in
`custom_components/chmi_weather/translations/<language>.json`. English in
`en.json` is the default text, and Home Assistant selects `cs.json`, `sk.json`,
or another future language file according to the user's selected Home Assistant
language. Keep every language file structurally aligned with `en.json`; the
translation tests enforce this.

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

## Status and Scope

See `docs/status.md` for the implemented station-data scope and explicit
non-goals.
