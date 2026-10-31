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
python -m pytest --cov=src --cov-report=xml:coverage.xml