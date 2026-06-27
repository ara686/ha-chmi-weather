# CHMI OpenData

The MVP uses official CHMI OpenData current observation files, not HTML station
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
10m-{station_id}-{YYYYMMDD}.json
```

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

The parser selects the latest valid numeric value per mapped element.

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
which 10-minute diagnostic sensors should be created for the station.

Observed header:

```text
OBS_TYPE,WSI,EG_EL_ABBREVIATION,NAME,UN_DESCRIPTION,HEIGHT,SCHEDULE
```

Only `OBS_TYPE` value `10M` is used for the current observation MVP. For the
Dobřichovice fixture, wind is advertised through `D`, `F`, and `Fmax`, while
pressure `P` is not advertised.

## Element mapping

| Field | CHMI element |
| --- | --- |
| Temperature | `T` |
| Humidity | `H` |
| Pressure | `P` |
| Precipitation 10m | `SRA10M` |
| Wind speed | `F` |
| Wind gust | `Fmax` |
| Wind direction | `D` |

The sampled Dobřichovice metadata contains `TPM` but not `P`. The MVP keeps the
requested `P` pressure mapping but does not create the pressure diagnostic sensor
unless the station advertises `P` in `meta2`.
