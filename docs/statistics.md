# Home Assistant Statistics

CHMI Weather intentionally exposes measured station values and lets Home
Assistant handle most statistics, history, and calendar cycles natively.

## Maxima, minima, and averages

Use Home Assistant statistics cards or Statistics helpers for extrema and
averages from current measured sensors:

- Temperature
- Temperature maximum 10m
- Temperature minimum 10m
- Apparent temperature
- Humidity
- Pressure, when advertised by the selected station
- Wind speed
- Average wind speed
- Wind gust
- Wind direction
- Average wind direction
- Wind gust direction
- Precipitation 10m
- Precipitation 1h
- Precipitation today
- Yesterday precipitation
- Yesterday temperature maximum
- Yesterday temperature minimum
- Yesterday wind gust maximum
- Precipitation this month

Common useful characteristics are `value_max`, `value_min`, `mean`,
`mean_circular`, `sum`, and `total`. Use `mean_circular` for wind direction
because wind direction is an angle.

For dashboard-only views, the built-in Statistic card and Statistics graph card
are usually enough. For reusable entities or automations, create Home Assistant
Statistics helpers with the desired source sensor, characteristic, and time
window.

## Rainfall totals

CHMI `SRA10M` is a rainfall interval value for one observation period. It is
useful as a raw sensor and for short-term dashboards, but it is not the best
source for Utility Meter helpers because repeated polls of the same upstream
timestamp must not be counted as new rainfall.

Use `Precipitation today` as the source for Utility Meter helpers. It is a
cumulative rainfall total derived from `SRA10M` rows for the current Home
Assistant local date and is exposed with Home Assistant state class
`total_increasing`.

Keep `delta_values` disabled for these Utility Meter helpers. The source is a
cumulative value, not a delta value.

```yaml
utility_meter:
  chmi_dobrichovice_precipitation_hourly:
    name: CHMI Dobrichovice precipitation hourly
    source: sensor.chmi_dobrichovice_precipitation_today
    cycle: hourly

  chmi_dobrichovice_precipitation_daily:
    name: CHMI Dobrichovice precipitation daily
    source: sensor.chmi_dobrichovice_precipitation_today
    cycle: daily

  chmi_dobrichovice_precipitation_weekly:
    name: CHMI Dobrichovice precipitation weekly
    source: sensor.chmi_dobrichovice_precipitation_today
    cycle: weekly

  chmi_dobrichovice_precipitation_monthly:
    name: CHMI Dobrichovice precipitation monthly
    source: sensor.chmi_dobrichovice_precipitation_today
    cycle: monthly
```

## Direct rainfall sensors

The integration exposes current rainfall sensors when the selected station
advertises the matching CHMI elements:

- `Precipitation 10m`: raw latest `SRA10M` interval value.
- `Precipitation 1h`: raw latest `SRA1H` value when advertised by the station,
  otherwise a rolling sum of the latest hour available from `SRA10M`.
- `Precipitation today`: cumulative sum for the current Home Assistant local
  date, intended as the Utility Meter source for calendar cycles.

Use `Precipitation 1h` for direct dashboard cards or automations that need the
latest rolling-hour rainfall. Use Utility Meter helpers based on `Precipitation
today` for hourly, daily, weekly, monthly, or yearly calendar totals.

The integration also exposes CHMI recent daily summary rainfall values when
published by CHMI:

- `Yesterday precipitation`: official daily `SRA` value for the last completed
  local date.
- `Precipitation this month`: sum of usable recent daily `SRA` rows in the CHMI
  monthly daily file up to that same date.

Use these CHMI recent daily values when you want the upstream daily summaries.
Use Utility Meter helpers when you want Home Assistant to maintain calendar
totals from the history recorded by this integration.
