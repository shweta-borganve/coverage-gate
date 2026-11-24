# Coverage Gate

A reusable GitHub Action to enforce code coverage thresholds and detect coverage regressions.

## Features

- Overall and changed-line coverage checks
- Coverage regression detection
- Cobertura XML, LCOV, and coverage.py JSON support
- GitHub Actions summaries and pull request comments
- Coverage history and SVG badges
- Composite and Docker Action support

## Supported Formats

| Format | File |
|---|---|
| Cobertura XML | `coverage.xml` |
| LCOV | `coverage.info` |
| coverage.py JSON | `coverage.json` |

## Quick Start

Generate a coverage report using pytest:

```bash
pytest --cov=src --cov-report=xml:coverage.xml
```

Add this step to `.github/workflows/ci.yml`:

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

Use a published version tag instead of `@main` when available.

## Inputs

| Input | Default | Description |
|---|---|---|
| `coverage-file` | Required | Path to the coverage report |
| `threshold` | `80` | Minimum overall coverage percentage |
| `changed-lines-threshold` | `0` | Minimum changed-line coverage |
| `warning-margin` | `5` | Warning margin in percentage points |
| `baseline-coverage` | Empty | Baseline coverage for regression checks |
| `max-regression` | `5` | Maximum allowed coverage regression |
| `github-token` | Empty | Token for pull request comments |
| `enable-pr-comment` | `true` | Enable pull request comments |
| `enable-coverage-trend` | `false` | Enable coverage history tracking |
| `history-token` | Empty | Token for coverage history operations |
| `enable-coverage-badge` | `false` | Generate an SVG coverage badge |
| `badge-output-path` | `coverage-badge.svg` | Badge output file path |

## Outputs

| Output | Description |
|---|---|
| `coverage` | Measured overall coverage percentage |
| `threshold` | Configured coverage threshold |
| `passed` | Whether the coverage check passed |
| `changed-lines-coverage` | Changed-line coverage percentage |
| `changed-lines-passed` | Whether the changed-line check passed |

The Docker Action exposes `coverage`, `changed-lines-coverage`, `changed-lines-passed`, and `passed`.

## Configuration Examples

### Changed-line coverage

```yaml
- name: Check changed-line coverage
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    changed-lines-threshold: '90'
```

### Coverage regression detection

```yaml
- name: Check coverage regression
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    baseline-coverage: '85'
    max-regression: '5'
```

### Coverage badge

```yaml
- name: Generate coverage badge
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    enable-coverage-badge: 'true'
    badge-output-path: coverage-badge.svg
```

## Required Permissions

For pull request comments, configure:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Coverage history operations may require additional `actions: read` and `actions: write` permissions, depending on the workflow.

## Docker Action

The Docker Action can be used separately:

```yaml
- name: Check coverage with Docker
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

**Requirement:** The GitHub Actions runner must have Docker installed and a working Docker daemon.

See [Docker Action documentation](docker/README.md).

## Development

Install development dependencies and run tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Project Structure

- `src/` – Core application
- `docker/` – Docker Action and entrypoint
- `tests/` – Automated tests
- `docs/` – Project documentation

## Documentation

- [Roadmap](docs/ROADMAP.md)
- [Compatibility](docs/compatibility.md)
- [Docker Action](docker/README.md)

## Repository

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)
