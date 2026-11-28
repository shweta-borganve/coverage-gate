# Coverage Gate

A lightweight GitHub Action to enforce code coverage, detect regressions, and monitor coverage changes in your repository.

## Features

- Overall and changed-line coverage enforcement
- Multiple coverage report parsing and merging
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

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

Use `@v1` after the next release updates the major-version tag.

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

**Regression detection**
```yaml
baseline-coverage: '85'
max-regression: '5'
```

**Coverage history**
```yaml
enable-coverage-trend: 'true'
```

Uses GitHub Actions artifacts to compare coverage with previous runs of the same branch and workflow. The default history token is `github.token`.

**Coverage badge**
```yaml
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

```yaml
permissions:
  contents: read
  pull-requests: write  # PR comments
  actions: read         # Coverage history
```

The `github-token` input must be supplied for PR comments. The `history-token` defaults to `github.token`.

## Docker Action

Use `shweta-borganve/coverage-gate/docker@main`.

Requires a GitHub Actions runner with Docker installed and running. Supports the five Docker formats listed above, multiple reports, and component thresholds.

See [Docker documentation](docker/README.md).

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
black --check .
isort --check-only src tests
```

## Documentation

- [Compatibility](docs/compatibility.md)
- [Docker Action](docker/README.md)
- [Workflow Examples](docs/workflow-examples.md)
- [Roadmap](docs/ROADMAP.md)

## License

[MIT License](LICENSE)

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)
