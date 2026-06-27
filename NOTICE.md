# Notices

## Project License

CHMI Weather source code is licensed under the MIT License. See `LICENSE`.

The MIT License allows use, copying, modification, publication, distribution,
sublicensing, and sale of the software, provided the license and copyright notice
are included with copies or substantial portions of the software. The license
also states that the software is provided as-is, without warranty, and limits
liability of the authors and copyright holders.

## CHMI OpenData

Runtime weather observations, station metadata, and test fixtures derived from
CHMI data are sourced from CHMI OpenData:

```text
https://opendata.chmi.cz
```

CHMI states that its open data may be used free of charge when respecting the
Creative Commons Attribution 4.0 International license (CC BY 4.0):

```text
https://www.chmi.cz/o-chmu/produkty-a-sluzby/data-a-vyhodnoceni
https://creativecommons.org/licenses/by/4.0/
```

This integration parses, normalizes, and displays selected current observation
values and station metadata from CHMI OpenData. Test fixtures in
`tests/fixtures/` are small samples derived from CHMI OpenData and are included
for parser and integration testing.

When publishing screenshots, examples, derived data, dashboards, or any other
output that includes CHMI OpenData, give credit to CHMI, link to the license
where practical, and indicate if you changed or transformed the data. A suitable
short attribution is:

```text
Data source: Czech Hydrometeorological Institute (CHMI) OpenData, CC BY 4.0.
```

This repository does not grant any rights to CHMI names, marks, logos, or data
beyond the rights made available by CHMI and the applicable data license.

## Third-Party Projects

Home Assistant, HACS, Nabu Casa, Open Home Foundation, and CHMI are separate
third-party projects or organizations. Their names are used only to identify
compatibility targets and data sources.
