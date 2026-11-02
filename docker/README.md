# Coverage Gate — Docker Action

A containerized version of Coverage Gate that checks Cobertura XML coverage against a configurable threshold.

## Usage

```yaml
- name: Check coverage
  uses: shweta-borganve/coverage-gate/docker@main
  with:
    coverage-file: coverage.xml
    threshold: '80'
```

## Inputs

- `coverage-file` — Path to the Cobertura XML report (required).
- `threshold` — Minimum coverage percentage (default: `80`).
- `warning-margin` — Warning margin in percentage points (default: `5`).
- `baseline-coverage` — Optional baseline for regression detection.
- `max-regression` — Maximum permitted regression in percentage points (default: `5`).

The action writes the measured coverage to its `coverage` output and adds a summary to GitHub Actions when the relevant environment variables are available.

Use a published version tag instead of `@main` when one is available.