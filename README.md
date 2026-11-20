# Coverage Gate

A reusable GitHub Action that checks Python test coverage and helps prevent coverage regressions.

## Features

- Coverage threshold enforcement
- Warning and regression checks
- Per-file and changed-line coverage
- GitHub Actions summary and outputs
- Automatic pull request coverage comments
- Cobertura XML and LCOV support

## Quick Start

Generate a coverage report:

```bash
python -m pip install pytest pytest-cov
python -m pytest --cov=src --cov-report=xml:coverage.xml
```

Add Coverage Gate to your workflow:

```yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

## Pull Request Comments

Enable automatic PR comments by adding:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Then configure the action:

```yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
    enable-pr-comment: 'true'
```

Comments are updated instead of duplicated. If publishing fails (for example, on fork PRs with read-only tokens), a warning is logged and the coverage result is unaffected.

## Configuration

| Input | Description | Default |
|---|---|---|
| `coverage-file` | Coverage report path | Required |
| `threshold` | Minimum coverage (%) | `80` |
| `changed-lines-threshold` | Minimum changed-line coverage (%) | `0` |
| `warning-margin` | Warning range (%) | `5` |
| `baseline-coverage` | Baseline coverage (%) | Empty |
| `max-regression` | Maximum coverage drop (%) | `5` |
| `github-token` | Token for PR comments | Empty |
| `enable-pr-comment` | Enable PR comments | `true` |

## Docker Action

See [docker/README.md](docker/README.md) for Docker usage.

## Repository

[GitHub: shweta-borganve/coverage-gate](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve
