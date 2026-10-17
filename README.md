# Coverage Gate

**A reusable GitHub Action for enforcing Python test coverage requirements.**

Coverage Gate helps development teams maintain minimum test coverage, detect coverage regressions, and review coverage results directly in GitHub Actions.

It reads an existing Cobertura XML coverage report, evaluates configurable coverage rules, and reports whether the coverage requirements have been met.

## Features

- **Minimum coverage threshold:** Enforce a required line-coverage percentage.
- **Coverage warnings:** Warn when coverage approaches the configured threshold.
- **Regression detection:** Compare current coverage with a supplied baseline.
- **Per-file coverage:** Display individual file coverage when the report provides the required data.
- **GitHub Actions integration:** Run coverage checks automatically in CI workflows.
- **Job summaries:** Display coverage results in the GitHub Actions summary.
- **Action outputs:** Expose the current coverage percentage for use in subsequent workflow steps.
- **Input validation:** Handle missing, invalid, and unsupported coverage reports.
- **Automated testing:** Verify functionality using pytest and code-quality tools.
- **Docker support:** Run the project and its tests in a containerized environment.
- **Changed-line parsing foundation:** Identify newly added lines in Git diffs as a foundation for future changed-code coverage reporting.

## The Problem

Passing automated tests does not necessarily mean that enough of an application's code has been tested. Without an enforced coverage policy, teams may merge changes even when coverage falls below their required standard.

Coverage Gate addresses this problem by automatically checking an existing coverage report against configurable rules. This helps developers identify coverage issues earlier and maintain consistent testing standards throughout development.

## How It Works

text
Python Application and Tests
             |
             v
   Generate Coverage Report
             |
             v
       Cobertura XML
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
       +-----+-----+
       |           |
       v           v
   GitHub       Coverage
   Summary      Output
             |
             v
        PASS / FAIL


Coverage Gate does not generate the coverage report itself. A testing and coverage tool, such as `pytest-cov`, generates the report before Coverage Gate runs.

For example, if the report contains a line-rate of `0.85`, the overall line coverage is 85%.

- Required coverage: 80% — **PASS**
- Required coverage: 90% — **FAIL**

## Requirements

- A GitHub repository that uses GitHub Actions.
- Python 3.11 or later for local development.
- A valid Cobertura XML coverage report.
- Docker and Docker Compose for optional container-based development and testing.

## GitHub Actions Usage

First, generate a Cobertura XML coverage report in your repository. Then add Coverage Gate to your GitHub Actions workflow.

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


Adjust the test command, coverage target, and action version to match your repository. The coverage report must exist before the Coverage Gate step runs.

## Configuration

Coverage Gate accepts the following inputs:

| Input | Required | Default | Description |
|---|---|---|---|
| `coverage-file` | Yes | — | Path to the Cobertura XML report, relative to the workspace. |
| `threshold` | Yes | `80` | Minimum required line-coverage percentage. |
| `warning-margin` | No | `5` | Margin in percentage points used for coverage warnings near the threshold. |
| `baseline-coverage` | No | Empty | Previous coverage percentage used for regression detection. |
| `max-regression` | No | `5` | Maximum allowed decrease in coverage, in percentage points. |

### Example: Configure all inputs

yaml
- name: Coverage Gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage.xml
    threshold: "80"
    warning-margin: "5"
    baseline-coverage: "89"
    max-regression: "5"


The baseline is optional. Supply it when you want to compare the current coverage against a known previous value.

## Coverage Threshold and Regression Detection

Coverage Gate supports two different types of coverage checks.

### 1. Minimum coverage threshold

The threshold ensures that current coverage meets the team's minimum requirement.

For example:

text
Current coverage: 85%
Required coverage: 80%

Result: PASS


If current coverage falls below the configured threshold, the coverage check fails.

### 2. Coverage regression

Regression detection compares current coverage with a supplied baseline.

For example:

text
Baseline coverage: 89%
Current coverage: 85%
Maximum regression: 5 percentage points

Coverage decrease: 4 percentage points
Regression result: PASS


If the decrease exceeds the configured maximum regression, the regression check fails.

**Note:** Passing the regression check does not replace the minimum threshold check. Both rules can apply independently.

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


This output can be used by subsequent workflow steps.

## Coverage Summary

Coverage Gate writes a summary to the GitHub Actions job summary.

Depending on the available report data, the summary can include:

- Overall coverage percentage.
- Configured coverage threshold.
- Evaluation status.
- Per-file coverage percentages.
- Warning and regression information.

Per-file results help developers identify source files that may need additional tests.

## Project Structure

The following structure highlights the main application files and supporting project configuration. Some test files and fixtures are omitted for readability.

text
coverage-gate/
├── .github/
│   └── workflows/
├── src/
│   ├── __init__.py
│   ├── parser.py
│   ├── enforcer.py
│   ├── main.py
│   ├── summary.py
│   └── changed_lines.py
├── tests/
│   ├── fixtures/
│   │   ├── sample.xml
│   │   └── unsupported.xml
│   ├── test_parser.py
│   └── test_changed_lines.py
├── action.yml
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md


### Important files

- **`src/parser.py`** — Reads and validates Cobertura XML coverage data, including overall and per-line coverage information.
- **`src/enforcer.py`** — Evaluates configured coverage thresholds, warning margins, and regression rules.
- **`src/summary.py`** — Generates the coverage summary for GitHub Actions.
- **`src/main.py`** — Provides the local command-line entry point.
- **`src/changed_lines.py`** — Parses Git diff output and identifies newly added line numbers by file. This is groundwork for changed-code coverage reporting.
- **`tests/`** — Contains automated tests and test fixtures.
- **`action.yml`** — Defines the reusable GitHub Composite Action, its inputs, steps, and outputs.
- **`Dockerfile`** — Defines the environment used to build the Docker image.
- **`compose.yaml`** — Configures Docker Compose workflows, including container-based testing.
- **`requirements.txt`** — Lists the project's Python dependencies.

## Run Locally

### 1. Clone the repository

bash
git clone https://github.com/shweta-borganve/coverage-gate.git
cd coverage-gate


### 2. Create and activate a virtual environment

On Linux or WSL:

bash
python3 -m venv .venv
source .venv/bin/activate


On Windows PowerShell:

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1


### 3. Install dependencies

bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest ruff black isort


### 4. Run the tests

bash
pytest -v


### 5. Run code-quality checks

bash
ruff check .
black --check .
isort --check-only src tests
git diff --check


These checks help identify common Python code-quality issues, inconsistent formatting, unsorted imports, and whitespace problems.

## Run the CLI

Coverage Gate provides a local command-line interface for checking coverage reports.

Basic example:

bash
python -m src.main tests/fixtures/sample.xml 80


With a warning margin:

bash
python -m src.main tests/fixtures/sample.xml 80 10


With baseline and regression settings:

bash
python -m src.main tests/fixtures/sample.xml 80 5 90 5


The positional arguments are:

1. Coverage report path.
2. Minimum coverage threshold.
3. Warning margin.
4. Baseline coverage.
5. Maximum allowed regression.

## Docker

Docker provides an optional way to run Coverage Gate in a containerized environment.

### Build the image

bash
docker build -t coverage-gate:local .


### Run Coverage Gate

bash
docker run --rm coverage-gate:local tests/fixtures/sample.xml 80


### Run tests with Docker Compose

bash
docker compose run --build --rm tests


This builds the image if needed, runs the configured `tests` service, and removes the test container after execution.

### Why Docker?

- Provides a consistent, configured runtime environment.
- Helps isolate application dependencies from the host environment.
- Simplifies container-based testing.
- Makes it easier for other developers to reproduce the project's setup.

Docker is optional. You can also run Coverage Gate directly using a Python virtual environment.

## Development and Releases

Coverage Gate follows a Git-based development workflow using feature branches, pull requests, automated tests, and GitHub Actions.

The development workflow includes:

1. Create a feature branch.
2. Implement the change and add or update tests.
3. Run the test suite and code-quality checks.
4. Push the branch and open a pull request.
5. Review and merge the changes after required checks pass.
6. Use the repository's configured release workflow to publish releases.

The repository uses semantic-release automation to manage versioning according to its release configuration and commit conventions.

## Technologies

- Python
- XML parsing
- pytest and pytest-cov
- Ruff
- Black
- isort
- Git and GitHub
- GitHub Actions and Composite Actions
- Docker and Docker Compose
- Semantic-release automation

## What This Project Demonstrates

Coverage Gate demonstrates how Python can be used to build reusable CI infrastructure.

It combines XML parsing, input validation, configurable quality rules, automated testing, GitHub Actions integration, job summaries, and Docker-based development workflows.

The changed-line parsing component also establishes a foundation for identifying newly added code in Git diffs for future changed-code coverage reporting.

## Repository

GitHub: [shweta-borganve/coverage-gate](https://github.com/shweta-borganve/coverage-gate)

**Author:** Shweta Boraganve