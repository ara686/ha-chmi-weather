# CHMI OpenData

The integration uses official CHMI OpenData station data files, not HTML station
pages.

## Data License and Attribution

CHMI OpenData is a third-party data source. CHMI states that its open data may
be used free of charge when respecting the Creative Commons Attribution 4.0
International license (CC BY 4.0).

When publishing examples, screenshots, derived data, dashboards, or other output
that includes CHMI OpenData, give credit to CHMI, link to the license where
practical, and indicate if you changed or transformed the data. A suitable short
attribution is:

```text
Data source: Czech Hydrometeorological Institute (CHMI) OpenData, CC BY 4.0.
```

This integration stores and displays data from CHMI OpenData but does not make
any claim that the upstream data is complete, current, correct, or suitable for
production, safety, emergency, or compliance use.

The Home Assistant weather entity exposes attribution through the entity
metadata. Test fixtures derived from CHMI OpenData are documented in
`tests/fixtures/README.md`.

## Current observations

Base URL:

```text
https://opendata.chmi.cz/meteorology/climate/now/data
```

File pattern:

```text
{interval_prefix}-{station_id}-{YYYYMMDD}.json
```

The interval prefix is selected from official `meta2` metadata. Known current
prefixes are `10m` for `OBS_TYPE` / `SCHEDULE` value `10M` and `1h` for `1H`.
The parser selects the shortest advertised interval for the station and falls
back to longer intervals when no shorter interval is advertised.

Some stations advertise companion hourly elements even when the selected current
observation interval is `10M`. When `meta2` advertises `SRA1H`, the integration
can fetch the matching `1h` file and use that raw value for `Precipitation 1h`.
When `meta2` advertises hourly SYNOP weather elements such as `ww`, `N`, `VV`,
`Td`, `W1`, or `W2`, the integration can fetch the matching `1h` file and use
those measured station values for the Home Assistant weather condition.

`YYYYMMDD` is calculated from the current UTC day. If today's file is missing or
does not contain usable rows, the API client tries yesterday's UTC file.

## Observed JSON shape

The Dobrichovice fixture is based on the live endpoint sampled on 2026-06-26:

```text
STATION,ELEMENT,DT,VAL,FLAG,QUALITY
```

Rows are arrays:

```json
["0-203-0-11521", "T", "2026-06-26T08:50:00Z", 32.7, "", 5.0]
```

The parser selects the latest valid numeric value per mapped element. For
`SRA10M`, it also keeps timestamped interval samples from the selected daily file
so the integration can derive one-hour and rainfall totals. During normal Home
Assistant polling, the integration combines the current and previous UTC daily
files before calculating `Precipitation today` for the Home Assistant local date.
The parser also keeps the selected row's `QUALITY` and `FLAG` values for
diagnostics.

## Recent daily summaries

Base URL:

```text
https://opendata.chmi.cz/meteorology/climate/recent/data/daily
```

File pattern:

```text
dly-{station_id}-{YYYYMM}.json
```

`YYYYMM` is selected from the last completed date in the Home Assistant local
timezone. CHMI creates daily files after the day ends and the files contain
station daily rows from the first day of the month through the latest published
day.

Observed header:

```text
STATION,ELEMENT,VTYPE,DT,VAL,FLAG,QUALITY
```

The integration reads the selected station rows from the monthly daily file and
sums usable `SRA` rows up to the last completed local date for `Precipitation
this month`. If CHMI has published station rows for the month but no usable
`SRA` rows yet, the parsed monthly precipitation total is `0.0`.

## Station metadata

Base URL:

```text
https://opendata.chmi.cz/meteorology/climate/now/metadata
```

File pattern:

```text
meta1-{YYYYMMDD}.json
```

`meta1` contains station-level metadata. The integration uses the current UTC
day and falls back to yesterday when the current metadata file is not available
yet.

Observed header:

```text
WSI,GH_ID,FULL_NAME,GEOGR1,GEOGR2,ELEVATION,BEGIN_DATE
```

`GEOGR1` is longitude and `GEOGR2` is latitude. During config flow validation,
the integration uses this official metadata to offer the nearest stations for
entered GPS coordinates and then stores the selected WSI, station name, and
coordinates.

`meta2` contains station element metadata. The integration uses it to determine
which sensors should be created for the station and which current observation
interval should be used.

Observed header:

```text
OBS_TYPE,WSI,EG_EL_ABBREVIATION,NAME,UN_DESCRIPTION,HEIGHT,SCHEDULE
```

For current observations, the integration selects the shortest usable `OBS_TYPE`
/ `SCHEDULE` value for each station and stores supported elements grouped by
interval. The Dobřichovice fixture advertises both `10M` and `1H`, so the
integration uses `10M` and the `10m-*` data files for station data. It also
records that hourly `SRA1H` is available in the `1h-*` data file. For the
Dobřichovice fixture, wind is advertised through `D`, `Dmax`, `Dprum`, `F`,
`Fmax`, and `Fprum`, while pressure `P` is not advertised for the selected
interval.

## Element mapping

| Field | CHMI element |
| --- | --- |
| Temperature | `T` |
| Temperature maximum 10m | `TMA` |
| Temperature minimum 10m | `TMI` |
| Apparent temperature | `TPM` |
| Humidity | `H` |
| Pressure | `P` |
| Precipitation 10m | `SRA10M` |
| Precipitation 1h | `SRA1H`, or derived from `SRA10M` |
| Precipitation today | derived from `SRA10M` |
| Precipitation this month | sum of `SRA` from recent daily |
| Weather condition | `ww`, `N`, `VV`, `Td`, `W1`, `W2` from current/SYNOP data |
| Wind speed | `F` |
| Average wind speed | `Fprum` |
| Wind gust | `Fmax` |
| Wind direction | `D` |
| Average wind direction | `Dprum` |
| Wind gust direction | `Dmax` |

The sampled Dobřichovice metadata contains `TPM` but not `P`. The integration
keeps the requested `P` pressure mapping but does not create the pressure
sensor unless the station advertises `P` in `meta2`.

## Data quality diagnostics

Current observation rows include CHMI `FLAG` and `QUALITY` columns. The
integration exposes these details only through Home Assistant diagnostics:

- `quality_by_element`: selected `QUALITY` code and the official CHMI `meta4`
  description for each parsed element.
- `flag_by_element`: selected `FLAG` value and the official CHMI `meta3`
  description for each parsed element when CHMI publishes one.
- `quality_code_descriptions`: current CHMI `meta4` quality-code descriptions.

If the `meta4` file is temporarily unavailable during setup, the integration
falls back to its built-in quality-code descriptions. If the `meta3` file is
temporarily unavailable, flag descriptions are omitted but the raw selected
`FLAG` values remain available in diagnostics.

The data quality values are intentionally not exposed as regular sensors or
regular sensor attributes. They describe the provenance and usability of source
rows rather than a user-facing weather measurement, and exposing one sensor per
element would create noisy entities that are better handled through diagnostics.
