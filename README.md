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

Coverage Gate searches for its existing comment and updates it on subsequent runs.

To prevent multiple workflow runs from publishing comments for the same PR simultaneously, add workflow-level concurrency:

```yaml
concurrency:
  group: coverage-gate-pr-${{ github.event.pull_request.number || github.ref }}
  queue: max
  cancel-in-progress: false
```

Use the same concurrency group in every workflow in your repository that publishes Coverage Gate comments. This ensures those workflows run one at a time for the same PR.

This concurrency setting must be configured in the workflow that uses the action. It cannot be configured from inside the composite action itself.

If publishing fails (for example, on fork PRs with read-only tokens), a warning is logged and the coverage result is unaffected.

## Configuration

| Input | Description | Default |
|---|---|---|
| `coverage-file` | Coverage report path | Required |
| `threshold` | Minimum coverage (%) | `80` |
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
