# Coverage Gate

A reusable GitHub Action that enforces test coverage thresholds and prevents coverage regressions.

It evaluates Cobertura XML coverage reports against configurable rules and displays results directly in GitHub Actions.

## Features

feature/lcov-only
- Configurable coverage thresholds
- Coverage regression checks
- Per-file and changed-line coverage
- GitHub Actions summary
- Cobertura XML and LCOV support

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
main

## Quick Start

Generate a Cobertura report:

```bash
feature/lcov-only
python -m pytest --cov=src --cov-report=xml:coverage.xml
```

Add Coverage Gate to your workflow.

**For XML:**

```yaml
- uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

**For LCOV:**

```yaml
- uses: shweta-borganve/coverage-gate@v1.5.1
  with:
    coverage-file: lcov.info
    threshold: '80'
```

## Configuration

| Input | Purpose |
|---|---|
| `coverage-file` | `.xml` or `.info` report path |
| `threshold` | Minimum coverage (%) |
| `warning-margin` | Warning range |
| `baseline-coverage` | Baseline coverage (%) |
| `max-regression` | Maximum allowed regression (%) |

GitHub: [Coverage Gate](https://github.com/shweta-borganve/coverage-gate)

python -m pip install pytest pytest-cov
python -m pytest --cov=src --cov-report=xml:coverage.xml
main
