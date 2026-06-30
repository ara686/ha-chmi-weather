## Summary

- 

## Validation

- [ ] ruff check .
- [ ] ruff format --check .
- [ ] PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
- [ ] bandit -r custom_components/chmi_weather
- [ ] pip-audit --local --skip-editable --progress-spinner off in a clean dev environment
- [ ] pytest tests_ha -o asyncio_mode=auto against latest Home Assistant stable
- [ ] pytest tests_ha -o asyncio_mode=auto against latest Home Assistant beta/pre-release
- [ ] GitHub Actions HACS validation passed
- [ ] GitHub Actions hassfest validation passed

## Public Safety

- [ ] User-facing docs still state development status, no production recommendation, and use-at-own-risk terms.
- [ ] License and CHMI OpenData attribution notices are still accurate.
- [ ] No secrets, tokens, private URLs, or personal data were added.

## Notes

- 
