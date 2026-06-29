# AGENTS.md

## Project goal

This repository contains a Home Assistant custom integration for CHMI OpenData
weather stations.

## Rules

- Do not scrape HTML pages from chmi.cz.
- Use only official CHMI OpenData endpoints.
- Keep Home Assistant code async-first.
- Use DataUpdateCoordinator for polling.
- Do not use blocking HTTP clients.
- Do not add dependencies unless clearly justified.
- Keep parser code isolated from Home Assistant entity code.
- Keep tests updated with every parser change.
- Keep README and docs updated with user-visible behavior changes.
- Do not fake forecast data.
- Do not expose forecast through legacy entity attributes.
- Prefer small incremental changes.
- After each meaningful change, run ruff and pytest.
- If endpoint structure is uncertain, add or update a fixture first.
- Use English for entity names, variables, code comments and docs.
- Review automated dependency PRs before merging; do not merge them only because
  CI is green.
- For Home Assistant test harness dependency updates, verify whether the package
  maps to a stable or beta Home Assistant release and preserve separate
  `ha-stable` and `ha-beta` coverage.
