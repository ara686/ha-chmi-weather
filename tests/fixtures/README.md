# Test Fixtures

The fixture files in this directory are small samples derived from CHMI
OpenData. CHMI states that its open data may be used free of charge when
respecting the Creative Commons Attribution 4.0 International license
(CC BY 4.0).

The fixtures were trimmed and stored in repository-friendly JSON files for
parser and integration tests. Dobrichovice current data is split into a `10M`
sample and a companion `1H` sample because CHMI publishes `SRA10M` and `SRA1H`
through separate current-observation files. Dobrichovice recent daily data is a
trimmed `dly` sample used for daily summary sensors. Additional station samples
cover current pressure data and hourly SYNOP elements.

Attribution:

```text
Data source: Czech Hydrometeorological Institute (CHMI) OpenData, CC BY 4.0.
```
