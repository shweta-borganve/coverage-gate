# Coverage Gate — Docker Action

A Docker-based GitHub Action to check code coverage and detect regressions.

## Requirements

- GitHub Actions runner with Docker installed and a working Docker daemon.
- Coverage report available inside the consumer repository workspace.

## Quick Start

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

Use a published version tag instead of `@main` when available.

## Supported Formats

- Cobertura XML (`.xml`)
- LCOV (`.info`)
- coverage.py JSON (`.json`)

## Inputs

| Input | Default | Description |
|---|---|---|
| `coverage-file` | Required | Coverage report path |
| `threshold` | `80` | Minimum overall coverage percentage |
| `changed-lines-threshold` | `0` | Minimum changed-line coverage |
| `warning-margin` | `5` | Warning margin in percentage points |
| `baseline-coverage` | Empty | Baseline for regression checks |
| `max-regression` | `5` | Maximum allowed coverage regression |
| `enable-coverage-badge` | `false` | Generate an SVG coverage badge |
| `badge-output-path` | `coverage-badge.svg` | Badge output path |

## Outputs

| Output | Description |
|---|---|
| `coverage` | Measured overall coverage percentage |
| `changed-lines-coverage` | Changed-line coverage percentage |
| `changed-lines-passed` | Changed-line check result |
| `passed` | Overall check result |

## Configuration Examples

### Changed-line coverage

```yaml
with:
  coverage-file: coverage.xml
  threshold: '80'
  changed-lines-threshold: '90'
```

### Regression detection

```yaml
with:
  coverage-file: coverage.xml
  threshold: '80'
  baseline-coverage: '85'
  max-regression: '5'
```

### Coverage badge

```yaml
with:
  coverage-file: coverage.xml
  enable-coverage-badge: 'true'
  badge-output-path: coverage-badge.svg
```
