# SKILL.md

## CHMI OpenData integration skill

Use this skill when modifying the CHMI Weather Home Assistant integration.

## Data source rules

- Use CHMI OpenData endpoints only.
- Never scrape station HTML pages.
- Current 10 minute station files are expected under:
  `https://opendata.chmi.cz/meteorology/climate/now/data/`
- File naming pattern:
  `10m-{station_id}-{YYYYMMDD}.json`
- Use UTC date for file selection.
- If today is missing or empty, try yesterday as fallback.

## Parser rules

- Normalize CHMI raw data into `ChmiObservation`.
- Keep element-code mapping in `const.py`.
- Keep parser tolerant to missing values.
- Prefer `None` over invalid numeric values.
- Always add/update fixture tests when parser behavior changes.

## Home Assistant rules

- Use config entries.
- Use config flow.
- Use DataUpdateCoordinator.
- Use async aiohttp.
- Keep weather and sensor entities thin.
- Do not fake unavailable values.
- Use correct device_class, state_class and units.

## Testing checklist

Before finishing a change:

```bash
ruff check .
ruff format --check .
pytest
```

## Manual HA test checklist

1. Copy `custom_components/chmi_weather` to Home Assistant
   `/config/custom_components/`.
2. Restart Home Assistant.
3. Add integration from UI.
4. Use station id `0-203-0-11521`.
5. Verify `weather.chmi_dobrichovice`.
6. Verify diagnostic sensors.
7. Check logs for warnings/errors.

## Development workflow

Postupuj po malych krocich:

### Phase 1 - repository bootstrap

- vytvor strukturu
- manifest
- hacs.json
- pyproject
- ruff config
- README skeleton
- AGENTS.md
- SKILL.md

### Phase 2 - parser and API client

- vytvor model
- vytvor API klienta
- vytvor fixture
- pridej parser testy

### Phase 3 - Home Assistant integration

- `__init__.py`
- `config_flow.py`
- `coordinator.py`
- `weather.py`
- `sensor.py`
- `diagnostics.py`

### Phase 4 - tests and docs

- pytest coverage pro MVP
- README doplnit
- docs doplnit
- CI workflow

## Output after completion

Na konci napis:

- seznam vytvorenych souboru
- co je hotove
- co neni hotove
- jak lokalne spustit testy
- jak integraci rucne nainstalovat do HA
- dalsi doporucene kroky
