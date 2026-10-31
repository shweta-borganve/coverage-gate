# Coverage Gate

A reusable GitHub Action that enforces test coverage thresholds and prevents coverage regressions.

## Features

- Configurable coverage thresholds
- Coverage regression checks
- Per-file and changed-line coverage
- GitHub Actions summary
- Cobertura XML and LCOV support

## Quick Start

Generate a Cobertura report:

```bash
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