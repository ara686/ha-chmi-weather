# Development

CHMI Weather is intentionally small and async-first. Home Assistant entity
modules should expose coordinator data and avoid parsing, HTTP calls, or data
normalization.

## Local setup

```bash
python -m pip install -e ".[dev]"
```

Run the validation suite before finishing a change:

```bash
ruff check .
ruff format --check .
pytest
```

## Workflow

1. Update or add a fixture when the CHMI OpenData shape changes.
2. Update parser tests before changing parser behavior.
3. Keep `api.py` independent from Home Assistant entities.
4. Keep polling inside `ChmiDataUpdateCoordinator`.
5. Keep weather and sensor properties memory-only.

## Manual Home Assistant check

1. Copy `custom_components/chmi_weather` to `/config/custom_components/`.
2. Restart Home Assistant.
3. Add CHMI Weather from Settings -> Devices & services -> Add integration.
4. Use station ID `0-203-0-11521`.
5. Confirm `weather.chmi_dobrichovice` and diagnostic sensors are created.
6. Check Home Assistant logs for setup or update warnings.
