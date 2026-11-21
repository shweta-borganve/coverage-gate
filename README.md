# Coverage Gate

A reusable GitHub Action to enforce Python test coverage and prevent coverage regressions.

## Features

- Coverage threshold and regression checks
- Changed-line coverage enforcement
- Cobertura XML and LCOV support
- GitHub Actions summary and outputs
- Automatic pull request comments
- Optional historical coverage tracking

## Quick Start

Generate a coverage report:

```bash
pip install pytest pytest-cov
pytest --cov=src --cov-report=xml:coverage.xml
```

Add to your GitHub Actions workflow:

```yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

## Pull Request Comments

Add these permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Configure the action with:

```yaml
github-token: ${{ secrets.GITHUB_TOKEN }}
enable-pr-comment: 'true'
```

Comments are updated on subsequent runs instead of duplicated.

## Coverage Trend Tracking

Track historical coverage using GitHub Actions artifacts.

Enable it with:

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
- Compares coverage across runs of the same branch and workflow.
- The first run creates history; subsequent runs can display trends.
- History failures do not affect coverage enforcement.

## Configuration

| Input | Description | Default |
|---|---|---|
| `coverage-file` | Coverage report path | Required |
| `threshold` | Minimum coverage (%) | `80` |
| `changed-lines-threshold` | Changed-line coverage (%) | `0` |
| `warning-margin` | Coverage warning margin | `5` |
| `baseline-coverage` | Baseline coverage (%) | Empty |
| `max-regression` | Maximum coverage drop | `5` |
| `github-token` | Pull request comment token | Empty |
| `enable-pr-comment` | Enable PR comments | `true` |
| `enable-coverage-trend` | Enable history tracking | `false` |
| `history-token` | Token for reading history artifacts | `github.token` |

## Docker Action

See [Docker documentation](docker/README.md).

## Repository

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve
