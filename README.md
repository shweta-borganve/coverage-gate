# Coverage Gate

A reusable GitHub Action to enforce Python test coverage and prevent coverage regressions.

## Features

- Coverage threshold and regression checks
- Changed-line coverage enforcement
- Cobertura XML, LCOV, and coverage.py JSON support
- GitHub Actions summaries and outputs
- Automatic pull request comments
- Optional historical coverage tracking
- Optional SVG coverage badges

## Quick Start

Generate a coverage report using one of these formats:

**Cobertura XML**
```bash
pip install pytest pytest-cov
pytest --cov=src --cov-report=xml:coverage.xml
```

**coverage.py JSON**
```bash
pip install pytest pytest-cov
pytest --cov=src --cov-report=json:coverage.json
```

**LCOV**

Generate an LCOV report using a compatible coverage tool and configure its output path.

Add Coverage Gate to your workflow:

```yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

Set `coverage-file` to `coverage.json` or `coverage.info` for JSON or LCOV reports, respectively. The action selects the parser based on the file extension.

## Pull Request Comments

Add the required permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Configure the action:

```yaml
github-token: ${{ secrets.GITHUB_TOKEN }}
enable-pr-comment: 'true'
```

Comments are updated on subsequent runs instead of duplicated.

## Coverage Trend Tracking

Track historical coverage using GitHub Actions artifacts. Enable it with:

```yaml
permissions:
  contents: read
  actions: read

steps:
  - name: Coverage Gate
    uses: shweta-borganve/coverage-gate@v1.5.1
    with:
      coverage-file: coverage.xml
      threshold: '80'
      enable-coverage-trend: 'true'
```

- Disabled by default.
- Uses `github.token` unless `history-token` is provided.
- Stores history in artifacts retained for 90 days.
- Compares runs of the same branch and workflow.
- The first run creates history; subsequent runs can display trends.
- History failures do not affect coverage enforcement.

## Configuration

| Input | Description | Default |
|---|---|---|
| `coverage-file` | Cobertura XML, LCOV, or coverage.py JSON report path | Required |
| `threshold` | Minimum coverage (%) | `80` |
| `changed-lines-threshold` | Changed-line coverage (%) | `0` |
| `warning-margin` | Coverage warning margin | `5` |
| `baseline-coverage` | Baseline coverage (%) | Empty |
| `max-regression` | Maximum coverage drop | `5` |
| `github-token` | Pull request comment token | Empty |
| `enable-pr-comment` | Enable PR comments | `true` |
| `enable-coverage-trend` | Enable history tracking | `false` |
| `history-token` | Token for reading history artifacts | `github.token` |
| `enable-coverage-badge` | Generate an SVG coverage badge | `false` |
| `badge-output-path` | Output path for the SVG badge | `coverage-badge.svg` |

## Docker Action

See the [Docker documentation](docker/README.md).

## Repository

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve
