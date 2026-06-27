# Security Policy

CHMI Weather is an experimental Home Assistant custom integration. It is not
recommended for production use.

## Supported Versions

Only the latest code on `main` and active development on `develop` are considered
for security fixes. Older commits, local development branches, and unpublished
test scripts are not supported.

## Reporting a Vulnerability

Report suspected vulnerabilities through a private GitHub security advisory when
available, or open a GitHub issue if the report does not include sensitive
details.

Do not include real tokens, credentials, private URLs, Home Assistant backups, or
personal data in public issues.

## Scope

In scope:

- CHMI Weather integration code under `custom_components/chmi_weather`.
- Repository CI, release, and HACS packaging configuration.
- Test fixtures and documentation maintained in this repository.

Out of scope:

- Vulnerabilities in Home Assistant itself.
- Vulnerabilities in HACS.
- Vulnerabilities or availability issues in CHMI OpenData endpoints.
- Vulnerabilities in locally ignored developer scripts unless they are promoted
  into the published repository.

## Dependency Boundary

The integration declares no runtime Python package dependencies in
`manifest.json`; it uses Home Assistant's built-in async HTTP session.

Development and Home Assistant integration tests install Home Assistant test
harness dependencies. Those packages are pinned by Home Assistant and
`pytest-homeassistant-custom-component`. If a dependency audit reports a
vulnerability in a Home Assistant-pinned package, track the latest Home Assistant
stable and beta releases and update the test harness when upstream provides a
compatible fix.

Do not override Home Assistant-pinned transitive dependencies in the integration
unless Home Assistant compatibility has been verified.
