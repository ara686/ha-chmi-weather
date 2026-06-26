# CHMI OpenData

The MVP uses official CHMI OpenData current observation files, not HTML station
pages.

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

The sampled Dobrichovice current file contains `TPM` but not `P`. The MVP keeps
the requested `P` pressure mapping and reports pressure as unavailable until a
confirmed pressure mapping is added.
