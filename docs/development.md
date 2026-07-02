# Development

CHMI Weather is intentionally small and async-first. Home Assistant entity
modules should expose coordinator data and avoid parsing, HTTP calls, or data
normalization.

This project is an experimental custom integration with the current station-data
scope implemented. Keep public-facing documentation explicit that it is not
recommended for production use and that users install it at their own risk.

## Local setup

```bash
python -m pip install -e ".[dev]"
```

Run the validation suite before finishing a change:

```bash
ruff check .
ruff format --check .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
```

Run the security checks for published integration code:

```bash
bandit -r custom_components/chmi_weather
pip-audit --local --skip-editable --progress-spinner off
```

Run dependency audit in a clean environment with only `.[dev]` installed when
you need to distinguish project dependencies from Home Assistant test harness
dependencies.

## Home Assistant compatibility tests

The fast unit tests in `tests/` use local stubs so parser and entity behavior can
be checked without installing Home Assistant. Real integration behavior must also
be tested with the Home Assistant test harness in `tests_ha/`.

Install and run against the latest checked stable Home Assistant test package:

```bash
python -m pip install ".[dev,ha-stable]"
pytest tests_ha -o asyncio_mode=auto
```

As of 2026-07-02, Home Assistant stable is `2026.7.0`, but the latest available
`pytest-homeassistant-custom-component` package still maps to `2026.7.0b3`.
The latest checked stable harness package remains Home Assistant `2026.6.4`, via
`pytest-homeassistant-custom-component==0.13.340`, until a test harness package
for stable `2026.7.0` is published. Home Assistant stable testing currently
requires Python 3.14.

`pytest-homeassistant-custom-component` is intentionally excluded from
Dependabot version updates because newer package releases can point at Home
Assistant beta builds. Update the `ha-stable` pin manually only after confirming
that the package maps to the latest stable Home Assistant release.

### Automated Dependency PRs

Review every automated dependency PR before merging. Do not merge Dependabot or
GitHub Actions update PRs solely because CI is green. Check the diff, release
notes, changed dependency role, and whether the update changes the meaning of a
test job.

For Home Assistant compatibility dependencies, preserve the split between
stable and beta coverage:

- `ha-stable` uses the manually verified stable Home Assistant test harness pin.
- `ha-beta` intentionally installs the latest available beta/pre-release test
  harness with `--pre`.
- If an automated PR would move the stable harness to a beta Home Assistant
  version, close it and keep the stable pin unchanged.
- Update `ha-stable` manually only after verifying the package maps to the
  latest Home Assistant stable release.

Run the beta/pre-release check before deployment-oriented changes and when Home
Assistant publishes a beta:

```bash
python -m pip install ".[dev]"
python -m pip install --upgrade --pre "pytest-homeassistant-custom-component>=0.13.343"
pytest tests_ha -o asyncio_mode=auto
```

As of 2026-07-02, that beta path installs Home Assistant `2026.7.0b3`, via
`pytest-homeassistant-custom-component==0.13.343`. If the beta job fails because
of a Home Assistant API change, capture the failure and warn users before the
next stable Home Assistant release.

The GitHub Actions workflow runs:

- HACS repository validation,
- Home Assistant hassfest metadata validation,
- unit checks on every push and pull request,
- Home Assistant stable integration tests,
- Home Assistant beta/pre-release integration tests,
- a daily scheduled run to surface new Home Assistant compatibility issues.

## Translations

Custom integration translations live in
`custom_components/chmi_weather/translations/<language>.json`. Do not add a
`strings.json` file for this custom integration. Home Assistant Core uses
`strings.json` and `[%key:...]` placeholders as build-time features, but custom
integrations are loaded directly from complete per-language translation files.

Keep `translations/en.json` as the complete English default. Add future
translations as BCP47 language-code files such as `cs.json` or `sk.json`, and
keep their key structure identical to `en.json`. Run the translation tests after
changing config flow labels, options flow labels, or entity translation keys.

## Branch and Release Workflow

Development must not happen directly on `main`.

Use this branch flow:

1. Keep `main` as the public HACS/release branch.
2. Keep `develop` as the integration branch for upcoming work.
3. Create all feature, fix, documentation, and dependency branches from
   `develop`.
4. Open feature/fix PRs from the working branch back into `develop`.
5. Open release PRs from `develop` into `main`.

Before opening a release PR from `develop` to `main`:

1. Choose the next semantic version.
2. Update `custom_components/chmi_weather/manifest.json`.
3. Update `pyproject.toml`.
4. Update `CHANGELOG.md` with user-visible changes, compatibility notes, and
   migration notes when needed.
5. Run unit tests, Home Assistant stable tests, and Home Assistant beta tests.

After the release PR is merged to `main`:

1. Create a GitHub release and tag using the same version as the integration
   manifest.
2. Use GitHub generated release notes and review them before publishing.
3. Confirm the release notes include the right user-visible changes,
   compatibility notes, dependency updates, and breaking changes.
4. Confirm HACS can see the new version from the public repository.

Dependabot is configured to open dependency PRs against `develop`, not `main`.

## Public Release Checklist

Before making the repository public or publishing a release:

1. Confirm `README.md`, `DISCLAIMER.md`, and `NOTICE.md` still describe the
   development status, no-warranty terms, data attribution, and third-party
   project relationship.
2. Run `git grep` or another secret scan over tracked files and review the git
   history for tokens, keys, private URLs, local paths, and personal data.
3. Run the unit, Home Assistant stable, and Home Assistant beta test commands.
4. Confirm `custom_components/chmi_weather/manifest.json` still has `domain`,
   `documentation`, `issue_tracker`, `codeowners`, `name`, and `version`.
5. Confirm GitHub Actions HACS validation and hassfest validation pass.
6. Run Bandit and pip-audit for the published integration code and clean dev
   dependency set.
7. Confirm the GitHub repository has a short description and relevant topics for
   HACS discoverability.
8. Check GitHub Actions logs because public repository visibility also makes
   existing public-facing repository activity and CI logs easier to inspect.

## Workflow

1. Update or add a fixture when the CHMI OpenData shape changes.
2. Update parser tests before changing parser behavior.
3. Keep `api.py` independent from Home Assistant entities.
4. Keep station interval selection in the parser/client layer and poll through
   `ChmiDataUpdateCoordinator`.
5. Keep weather and sensor properties memory-only.

## Manual Home Assistant check

1. Copy `custom_components/chmi_weather` to `/config/custom_components/`.
2. Restart Home Assistant.
3. Add CHMI Weather from Settings -> Devices & services -> Add integration.
4. Use the Home Assistant location or enter GPS coordinates.
5. Select Dobřichovice or another offered nearby CHMI OpenData station.
6. Confirm the `weather` entity, station-supported measurement sensors, and
   technical diagnostic sensors are created.
7. Check Home Assistant logs for setup or update warnings.

## Reference docs

- Home Assistant testing guide:
  https://developers.home-assistant.io/docs/development_testing/
- Home Assistant config entry runtime data rule:
  https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/
- Home Assistant config flow connection test rule:
  https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure/
- Home Assistant custom integration localization:
  https://developers.home-assistant.io/docs/internationalization/custom_integration/
- Home Assistant weather entity guide:
  https://developers.home-assistant.io/docs/core/entity/weather/
- pytest-homeassistant-custom-component:
  https://github.com/MatthewFlamm/pytest-homeassistant-custom-component
