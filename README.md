# Coverage Gate

A reusable GitHub Action to enforce Python test coverage and prevent coverage regressions.

## Features

- Coverage threshold and regression checks
- Changed-line coverage enforcement
- Cobertura XML and LCOV support
- GitHub Actions summary and outputs
- Automatic pull request comments

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

Add these workflow permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Configure the action:

```yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
    github-token: ${{ secrets.GITHUB_TOKEN }}
    enable-pr-comment: 'true'
```

Comments are updated on subsequent runs instead of duplicated.

## Configuration

| Input | Description | Default |
|---|---|---|
| `coverage-file` | Coverage report path | Required |
| `threshold` | Minimum coverage (%) | `80` |
| `changed-lines-threshold` | Changed-line coverage (%) | `0` |
| `warning-margin` | Warning range (%) | `5` |
| `baseline-coverage` | Baseline coverage (%) | Empty |
| `max-regression` | Maximum coverage drop (%) | `5` |
| `github-token` | PR comment token | Empty |
| `enable-pr-comment` | Enable PR comments | `true` |

## Docker Action

See [Docker documentation](docker/README.md).

## Repository

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve
