# Coverage Gate

A reusable GitHub Action that checks code coverage, prevents coverage regressions, and helps maintain code quality across projects and monorepos.

## Features

- Overall and changed-line coverage enforcement
- Multiple coverage report parsing and merging
- Per-file and per-directory coverage thresholds
- Separate branch coverage reporting when available
- Coverage regression detection
- Pull request comments and GitHub Actions summaries
- Coverage history and SVG badges
- Composite and Docker Action support

## Supported Formats

| Format | Report |
|---|---|
| Cobertura XML | `coverage.xml` |
| LCOV | `coverage.info` |
| coverage.py JSON | `coverage.json` |
| JaCoCo XML | `jacoco.xml` |
| Go coverprofile | `coverage.out` |
| OpenCover XML | `opencover.xml` |
| Istanbul / NYC JSON | `coverage-final.json` |

The Composite Action supports the listed formats. The Docker Action currently lists Cobertura XML, JaCoCo XML, LCOV, Go coverprofile, and coverage.py JSON.

## Quick Start

Generate a report:

```bash
pytest --cov=src --cov-report=xml:coverage.xml
```

Add to `.github/workflows/ci.yml`:

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

Use a published version tag instead of `@main` when available.

## Configuration

### Multiple Reports (Docker Action)

Provide comma-separated report paths. Coverage Gate combines covered and valid line counts and counts duplicate source lines only once.

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: 'coverage.xml,coverage.info'
    threshold: '80'
```

### Component Thresholds

Set different minimum coverage percentages for repository-relative files or directories:

```yaml
- name: Check component coverage
  uses: shweta-borganve/coverage-gate@main
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

## Inputs

| Input | Default | Purpose |
|---|---|---|
| `coverage-file` | Required | Coverage report path(s) |
| `threshold` | `80` | Minimum overall coverage (%) |
| `component-thresholds` | Empty | JSON file/directory thresholds |
| `changed-lines-threshold` | `0` | Minimum changed-line coverage (%) |
| `warning-margin` | `5` | Warning margin (percentage points) |
| `baseline-coverage` | Empty | Baseline for regression checks |
| `max-regression` | `5` | Maximum allowed regression |
| `github-token` | Empty | Pull request comment token |
| `enable-pr-comment` | `true` | Enable pull request comments |
| `enable-coverage-trend` | `false` | Track coverage history |
| `history-token` | Empty | Token for history operations |
| `enable-coverage-badge` | `false` | Generate SVG badge |
| `badge-output-path` | `coverage-badge.svg` | Badge output location |

## Outputs

| Output | Description |
|---|---|
| `coverage` | Measured overall coverage (%) |
| `threshold` | Configured minimum threshold |
| `passed` | Overall check result |
| `changed-lines-coverage` | Changed-line coverage (%) |
| `changed-lines-passed` | Changed-line check result |

The Docker Action exposes `coverage`, `changed-lines-coverage`, `changed-lines-passed`, and `passed`.

Branch coverage is displayed separately in the summary when reliable branch data is available. It does not replace line coverage enforcement.

## Permissions

For pull request comments:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Coverage history may also require `actions: read` and `actions: write`.

## Docker Action

Use `shweta-borganve/coverage-gate/docker@main` for the Docker version.

**Requirement:** A working Docker installation and daemon on the GitHub Actions runner.

See [Docker documentation](docker/README.md).

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check src tests
black --check src tests
isort --check-only src tests
```

## Project Structure

- `src/` – Core logic and coverage parsers
- `docker/` – Docker Action
- `tests/` – Automated tests and fixtures
- `docs/` – Project documentation

## Documentation

- [Roadmap](docs/ROADMAP.md)
- [Compatibility](docs/compatibility.md)
- [Docker Action](docker/README.md)

## Repository

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)
