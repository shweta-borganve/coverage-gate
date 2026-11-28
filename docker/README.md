# Coverage Gate — Docker Action

A Docker-based GitHub Action that checks code coverage, detects regressions, and enforces coverage thresholds.

## Requirements

- GitHub Actions runner with Docker installed and a working Docker daemon.
- Coverage reports available inside the consumer repository workspace.

## Quick Start

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

Use a stable version tag after the next release updates the `v1` major-version tag.

## Supported Formats

| Format | Report |
|---|---|
| Cobertura XML | `coverage.xml` |
| JaCoCo XML | `jacoco.xml` |
| LCOV | `coverage.info` |
| Go coverprofile | `coverage.out` |
| coverage.py JSON | `coverage.json` |

OpenCover XML and Istanbul/NYC JSON are supported by the Composite Action, not the Docker Action.

## Multiple Reports

Provide comma-separated report paths:

```yaml
- name: Check combined coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: 'coverage.xml,coverage.info'
    threshold: '80'
```

Duplicate source lines are counted once. If any report marks a duplicate line as covered, that line is counted as covered.

## Inputs

| Input | Default | Description |
|---|---|---|
| `coverage-file` | Required | One or more comma-separated coverage report paths |
| `threshold` | `80` | Minimum overall coverage percentage |
| `changed-lines-threshold` | `0` | Minimum changed-line coverage percentage |
| `component-thresholds` | Empty | JSON mapping repository-relative files or directories to minimum coverage percentages |
| `warning-margin` | `5` | Warning margin in percentage points |
| `baseline-coverage` | Empty | Baseline for regression checks |
| `max-regression` | `5` | Maximum allowed coverage regression |
| `enable-coverage-badge` | `false` | Generate an SVG coverage badge |
| `badge-output-path` | `coverage-badge.svg` | Badge output path relative to the workspace |

## Outputs

| Output | Description |
|---|---|
| `coverage` | Measured overall coverage percentage |
| `changed-lines-coverage` | Changed-line coverage percentage |
| `changed-lines-passed` | Changed-line check result |
| `passed` | Overall coverage check result |

## Configuration Examples

### Component Thresholds

```yaml
- name: Check component coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    component-thresholds: |
      {
        "src/api/": 90,
        "src/database/": 85
      }
```

### Changed-Line Coverage

```yaml
with:
  coverage-file: coverage.xml
  threshold: '80'
  changed-lines-threshold: '90'
```

### Regression Detection

```yaml
with:
  coverage-file: coverage.xml
  threshold: '80'
  baseline-coverage: '85'
  max-regression: '5'
```

### Coverage Badge

```yaml
with:
  coverage-file: coverage.xml
  enable-coverage-badge: 'true'
  badge-output-path: coverage-badge.svg
```

The generated badge is written to the configured path in the repository workspace.

## Related Documentation

- [Main README](../README.md)
- [Compatibility](../docs/compatibility.md)
- [MIT License](../LICENSE)
