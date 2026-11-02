# Coverage Gate

Coverage Gate is a reusable GitHub Action that helps Python developers monitor test coverage and maintain code quality in CI.

It evaluates Cobertura XML coverage reports against configurable rules and displays results directly in GitHub Actions.

## Features

- **Coverage Threshold:** Enforces a minimum line-coverage requirement.
- **Warning Margin:** Warns when coverage approaches the configured threshold.
- **Regression Checks:** Detects coverage drops against a configured baseline.
- **Per-File Coverage:** Shows coverage results for individual files.
- **Changed-Line Coverage:** Reports covered and uncovered lines added in pull requests.
- **GitHub Actions Summary:** Displays coverage results directly in the workflow summary.
- **Coverage Output:** Exposes the measured coverage percentage as a GitHub Actions output.
- **Input Validation:** Validates coverage settings and coverage report data.

## How It Works

1. Your test suite generates a Cobertura XML coverage report.
2. Coverage Gate reads and validates the report.
3. It evaluates the configured threshold and regression rules.
4. It publishes the coverage results to the GitHub Actions summary.
5. The workflow passes or fails based on the configured rules.

## Quick Start

### 1. Generate a coverage report

Install `pytest-cov` and generate a Cobertura XML report:

```bash
python -m pip install pytest pytest-cov
feature/optional-docker-support
python -m pytest --cov=src --cov-report=xml:coverage.xml
```

Replace `src` with your project's source directory if needed.

### 2. Add Coverage Gate to your workflow

Add this step to your GitHub Actions workflow after generating the coverage report:

```yaml
- name: Check test coverage
  uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

## Docker Action

A Docker-based version is available for containerized workflows. The existing Composite Action remains unchanged.

See [`docker/README.md`](docker/README.md) for usage and configuration.

## Configuration

| Input | Purpose |
|---|---|
| `coverage-file` | Path to the Cobertura XML report |
| `threshold` | Minimum required coverage (%) |
| `warning-margin` | Warning range near the threshold |
| `baseline-coverage` | Optional baseline coverage |
| `max-regression` | Maximum allowed coverage drop |

## Repository

GitHub: [shweta-borganve/coverage-gate](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve

python -m pytest --cov=src --cov-report=xml:coverage.xml
 main
