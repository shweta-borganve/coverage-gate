# Coverage Gate

feature/public-release-preparation
A lightweight GitHub Action to enforce code coverage, detect regressions, and monitor coverage changes in your repository.

A reusable GitHub Action that checks code coverage, prevents coverage regressions, and helps maintain code quality across projects and monorepos.
 main

## Features

- Overall and changed-line coverage enforcement
- Multiple coverage report parsing and merging
feature/public-release-preparation
- File and directory-specific thresholds
- Coverage regression detection
- Branch coverage reporting
- Pull request comments and GitHub Actions summaries
- Coverage history using Actions artifacts
- SVG coverage badge generation
- Composite and Docker Action support
- Local-first execution without an external coverage service

## Quick Start

Generate a coverage report and add this step to your GitHub Actions workflow:

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
main

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

Use `@v1` after the next release updates the major-version tag.

 feature/public-release-preparation
## Supported Formats

| Format | Composite | Docker |
|---|:---:|:---:|
| Cobertura XML | Yes | Yes |
| JaCoCo XML | Yes | Yes |
| OpenCover XML | Yes | No |
| LCOV | Yes | Yes |
| coverage.py JSON | Yes | Yes |
| Go coverprofile | Yes | Yes |
| Istanbul / NYC JSON | Yes | No |

Multiple reports can be supplied as comma-separated paths. Duplicate source lines are merged and counted once.

## Configuration

**Component thresholds**
```yaml
component-thresholds: |
  {
    "src/api/": 90,
    "src/database/": 85
  }
```

**Changed-line coverage**
```yaml
changed-lines-threshold: '90'
```

Changed-line enforcement applies to pull requests, not push or workflow-dispatch events.

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
main

**Regression detection**
```yaml
feature/public-release-preparation
baseline-coverage: '85'
max-regression: '5'
```

**Coverage history**
```yaml
enable-coverage-trend: 'true'
```

Uses GitHub Actions artifacts to compare coverage with previous runs of the same branch and workflow. The default history token is `github.token`.

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
 main

**Coverage badge**
```yaml
feature/public-release-preparation
enable-coverage-badge: 'true'
badge-output-path: coverage-badge.svg
```

## Inputs

| Input | Default | Description |
|---|---|---|
| `coverage-file` | Required | One or more comma-separated report paths |
| `threshold` | `80` | Minimum overall coverage (%) |
| `component-thresholds` | Empty | JSON file/directory thresholds |
| `changed-lines-threshold` | `0` | Minimum changed-line coverage (%) |
| `warning-margin` | `5` | Warning margin (percentage points) |
| `baseline-coverage` | Empty | Regression baseline (%) |
| `max-regression` | `5` | Maximum allowed regression |
| `github-token` | Empty | Token for pull request comments |
| `enable-pr-comment` | `true` | Enable pull request comments |
| `enable-coverage-trend` | `false` | Enable coverage history |
| `history-token` | `github.token` | Token for reading history artifacts |
| `enable-coverage-badge` | `false` | Generate an SVG badge |
| `badge-output-path` | `coverage-badge.svg` | Badge output path |

## Outputs

| Output | Description |
|---|---|
| `coverage` | Overall coverage (%) |
| `threshold` | Configured coverage threshold |
| `passed` | Overall check result |
| `changed-lines-coverage` | Changed-line coverage (%) |
| `changed-lines-passed` | Changed-line check result |

Branch coverage is reported separately when available; it is not currently enforced.

## Permissions

Grant only the permissions needed by enabled features:

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
 main

```yaml
permissions:
  contents: read
  pull-requests: write  # PR comments
  actions: read         # Coverage history
```

 feature/public-release-preparation
The `github-token` input must be supplied for PR comments. The `history-token` defaults to `github.token`.

## Docker Action

Use `shweta-borganve/coverage-gate/docker@main`.

Requires a GitHub Actions runner with Docker installed and running. Supports the five Docker formats listed above, multiple reports, and component thresholds.

Coverage history may also require `actions: read` and `actions: write`.

## Docker Action

Use `shweta-borganve/coverage-gate/docker@main` for the Docker version.

**Requirement:** A working Docker installation and daemon on the GitHub Actions runner.
main

See [Docker documentation](docker/README.md).

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
 feature/public-release-preparation
ruff check .
black --check .
isort --check-only src tests
```


ruff check src tests
black --check src tests
isort --check-only src tests
```

## Project Structure

- `src/` – Core logic and coverage parsers
- `docker/` – Docker Action
- `tests/` – Automated tests and fixtures
- `docs/` – Project documentation

 main
## Documentation

- [Compatibility](docs/compatibility.md)
- [Docker Action](docker/README.md)
- [Workflow Examples](docs/workflow-examples.md)
- [Roadmap](docs/ROADMAP.md)

## License

[MIT License](LICENSE)

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)
