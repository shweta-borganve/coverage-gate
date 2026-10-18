docs/update-readme
# Coverage Gate

Coverage Gate is a reusable GitHub Action that helps Python developers monitor test coverage and maintain code quality in CI.

## Features

- **Coverage Threshold:** Enforces a minimum line-coverage requirement.
- **Warning Margin:** Warns when coverage approaches the configured threshold.
- **Regression Checks:** Detects coverage drops against a configured baseline.
- **Per-File Coverage:** Shows coverage results for individual files.
- **Changed-Line Coverage:** Reports covered and uncovered lines added in pull requests.
- **GitHub Actions Summary:** Displays coverage results directly in the workflow summary.

## Quick Start

### 1. Generate a coverage report

Install `pytest-cov` and generate a Cobertura XML report:

```bash
python -m pip install pytest pytest-cov
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

Replace the example action version with the version you intend to use.

## Configuration

| Input | Purpose |
|---|---|
| `coverage-file` | Path to the Cobertura XML report |
| `threshold` | Minimum required coverage (%) |
| `warning-margin` | Warning range near the threshold |
| `baseline-coverage` | Optional baseline coverage |
| `max-regression` | Maximum allowed coverage drop |

See `action.yml` for supported inputs and defaults.

# COVERAGE GATE

**Coverage Gate** is a reusable GitHub Composite Action that checks Python test coverage from a Cobertura XML report and enforces configurable coverage rules in CI.

It helps teams maintain a minimum coverage level, identify potential coverage regressions, and review per-file coverage results directly in GitHub Actions.

## Features

- Parses Cobertura XML coverage reports.
- Enforces a configurable minimum line-coverage threshold.
- Warns when coverage approaches the configured threshold.
- Supports baseline coverage and configurable regression limits.
- Reports overall and per-file coverage in the GitHub Actions job summary.
- Exposes the current coverage percentage as a GitHub Actions output.
- Validates coverage report data and handles invalid or missing reports.
- Includes automated tests and code-quality checks.
- Supports local development and Docker-based testing.
- Uses GitHub Actions for CI and automated release workflows.

## How It Works
Test Suite
    |
    v
Cobertura XML Report
    |
    v
Coverage Gate
    |
    v
Parse Coverage Data
    |
    v
Evaluate Coverage Rules
    |
    +----> GitHub Actions Summary
    |
    +----> Coverage Output
    |
    v
    PASS / FAIL


Coverage Gate consumes an existing coverage report. It does not calculate code coverage itself; the test and coverage tools generate the report.

For example, if the report contains a line-rate of `0.85`, the overall line coverage is 85%.

- Required coverage: 80% → PASS
- Required coverage: 90% → FAIL

## Requirements

- A GitHub repository using GitHub Actions.
- Python 3.11 or later for local development.
- A valid Cobertura XML coverage report.
- Docker and Docker Compose are optional for container-based development and testing.

## GitHub Actions Usage

Generate a Cobertura XML report in your repository, then add Coverage Gate as a step in your workflow.

yaml
name: Test and Coverage

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov

      - name: Run tests and generate coverage report
        run: |
          pytest --cov=src --cov-report=xml:coverage.xml

      - name: Enforce coverage requirements
        uses: shweta-borganve/coverage-gate@v1
        with:
          coverage-file: coverage.xml
          threshold: "80"
          warning-margin: "5"


Adjust the test command and coverage target to match your repository. The coverage report must exist before the Coverage Gate step runs.

## Configuration

Coverage Gate accepts the following inputs:

| Input | Required | Default | Description |
|---|---|---|---|
| `coverage-file` | Yes | — | Path to the Cobertura XML coverage report, relative to the workspace. |
| `threshold` | Yes | `80` | Minimum allowed line-coverage percentage. |
| `warning-margin` | No | `5` | Margin in percentage points used for coverage warnings near the threshold. |
| `baseline-coverage` | No | Empty | Previous coverage percentage used for regression detection. |
| `max-regression` | No | `5` | Maximum allowed coverage decrease in percentage points. |

### Example: Configure all inputs

- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage.xml
    threshold: "80"
    warning-margin: "5"
    baseline-coverage: "89"
    max-regression: "5"


The baseline input is optional. Provide it when you want to compare current coverage against a known previous value.

## Coverage Threshold and Regression Detection

These rules serve different purposes.

### 1. Minimum coverage threshold

The threshold checks whether current coverage meets the minimum requirement.

For example:


Current coverage: 85%
Required coverage: 80%

85% >= 80%  -> PASS


If current coverage is below the threshold, the gate fails.

### 2. Coverage regression

Regression detection compares current coverage against the supplied baseline.

For example:


Baseline coverage: 89%
Current coverage: 85%
Maximum regression: 5 percentage points

Coverage drop: 4 percentage points
Result: PASS


If the decrease exceeds the configured maximum regression, the gate fails.

A passing regression check does not replace the minimum threshold check; both rules can apply.

## GitHub Actions Output

Coverage Gate exposes the current coverage percentage through the `coverage` output.

yaml
- name: Run Coverage Gate
  id: coverage
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage.xml
    threshold: "80"

- name: Display coverage
  run: echo "Current coverage: ${{ steps.coverage.outputs.coverage }}%"


## Coverage Summary

Coverage Gate writes a summary to the GitHub Actions job summary.

The summary can include:

- Overall coverage percentage.
- The configured threshold and evaluation result.
- Per-file line-coverage percentages when per-file data is available.

The per-file results help identify which source files have lower coverage and may need additional tests.

## Project Structure

coverage-gate/
├── src/
│   ├── __init__.py
│   ├── parser.py
│   ├── enforcer.py
│   ├── main.py
│   └── summary.py
├── tests/
│   ├── fixtures/
│   │   ├── sample.xml
│   │   ├── per_file.xml
│   │   ├── duplicate_filenames.xml
│   │   └── unsupported.xml
│   ├── test_parser.py
│   └── ...
├── .github/
│   └── workflows/
├── action.yml
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md


- **`parser.py`** — Reads and validates Cobertura XML data, including overall and per-file line coverage.
- **`enforcer.py`** — Evaluates the configured coverage threshold, warning margin, and regression rules.
- **`summary.py`** — Builds the coverage summary for GitHub Actions.
- **`main.py`** — Provides the local command-line entry point.
- **`action.yml`** — Defines the reusable GitHub Composite Action, its inputs, and its output.

## Run Locally

### 1. Clone the repository


git clone https://github.com/shweta-borganve/coverage-gate.git
cd coverage-gate


### 2. Create and activate a virtual environment


python3 -m venv .venv
source .venv/bin/activate

On Windows PowerShell, activate it with:


.venv\Scripts\Activate.ps1


### 3. Install dependencies


python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest ruff black isort


### 4. Run the tests


pytest -v


### 5. Run code-quality checks


ruff check .
black --check .
isort --check-only src tests
git diff --check


## Run the CLI

The local CLI accepts a coverage report and the threshold, with optional arguments for warning and regression checks.

Basic example:


python -m src.main tests/fixtures/sample.xml 80


With a warning margin:


python -m src.main tests/fixtures/sample.xml 80 10


With baseline and regression settings:


python -m src.main tests/fixtures/sample.xml 80 5 90 5

The arguments are:

1. Coverage report path.
2. Minimum coverage threshold.
3. Warning margin.
4. Baseline coverage.
5. Maximum allowed regression.

## Docker

Docker can be used to run Coverage Gate in a container.

### Build the image


docker build -t coverage-gate:local .


### Run Coverage Gate


docker run --rm coverage-gate:local tests/fixtures/sample.xml 80


### Run tests with Docker Compose


docker compose run --build --rm tests


This builds the image if needed, runs the test suite in a container, and removes the test container after execution.

## Development and Releases

Coverage Gate is developed using Git, feature branches, pull requests, and GitHub Actions.

The development workflow includes:

1. Create a feature branch.
2. Implement the change and add or update tests.
3. Run the test suite and code-quality checks.
4. Push the branch and open a pull request.
5. Review and merge the changes after CI passes.
6. Use the repository's configured release workflow to publish releases.

The repository uses semantic-release automation to manage versioning based on commit messages and the release configuration.

## Technologies

- Python
- XML parsing
- pytest
- Ruff
- Black
- isort
- Git and GitHub
- GitHub Actions
- GitHub Composite Actions
- Docker and Docker Compose
- Semantic versioning and automated releases

## What This Project Demonstrates

Coverage Gate demonstrates how a small Python application can be packaged as reusable CI infrastructure.

It brings together XML parsing, validation, automated testing, configurable quality rules, GitHub Actions integration, job summaries, and release automation.

## Repository

GitHub: [shweta-borganve/coverage-gate](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve
 main
