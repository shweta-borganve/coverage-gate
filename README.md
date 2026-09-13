Coverage Gate

A reusable GitHub Action that checks test coverage from a **Cobertura XML coverage report** and fails the CI pipeline when coverage is below the configured threshold.

Why Coverage Gate?

Having tests in a project does not automatically mean that enough of the code is being tested.

Coverage Gate provides a simple way to enforce a minimum test coverage requirement in CI/CD.

For example:

text
Project coverage: 91%
Required coverage: 80%

91% >= 80%
        ↓
   Coverage Gate
        ↓
       PASS


If coverage is below the required threshold:

text
Project coverage: 70%
Required coverage: 80%

70% < 80%
        ↓
   Coverage Gate
        ↓
       FAIL


This helps teams maintain a minimum level of test coverage as the codebase changes.



## How It Works

The action expects a coverage report in **Cobertura XML format**.

The general flow is:

text
Application code
       ↓
     Tests
       ↓
pytest + coverage
       ↓
coverage.xml
       ↓
Coverage Gate
       ↓
Compare coverage with threshold
       ↓
   PASS / FAIL


Coverage Gate reads the coverage percentage from the XML report and compares it with the configured threshold.

---

## Features

* Reusable GitHub Action
* Reads Cobertura XML coverage reports
* Configurable coverage threshold
* Fails the GitHub Actions job when coverage is below the threshold
* Can be used across multiple repositories
* Provides clear coverage and threshold information in CI logs

---

## Inputs

| Input           | Description                               | Required | Example                        |
| --------------- | ----------------------------------------- | -------: | ------------------------------ |
| `coverage-file` | Path to the Cobertura XML coverage report |      Yes | `coverage-output/coverage.xml` |
| `threshold`     | Minimum required coverage percentage      |      Yes | `80`                           |

---

## Usage

First, generate a Cobertura XML coverage report in your repository.

For a Python project using pytest:

```yaml
- name: Run unit tests with coverage
  run: |
    pytest --cov=src --cov-report=xml:coverage-output/coverage.xml
```

Then use Coverage Gate:

```yaml
- name: Run coverage gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage-output/coverage.xml
    threshold: "80"
```

The complete flow can look like:

```yaml
name: Python CI

on:
  push:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: |
          mkdir -p coverage-output
          pytest --cov=src --cov-report=xml:coverage-output/coverage.xml

      - name: Run coverage gate
        uses: shweta-borganve/coverage-gate@v1
        with:
          coverage-file: coverage-output/coverage.xml
          threshold: "80"
```

---

## Using Coverage Gate in Another Repository

Coverage Gate is designed to be reusable.

A different GitHub repository does **not** need to copy the Coverage Gate source code.

It only needs to generate a compatible coverage report and call the action:

```yaml
- name: Run coverage gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage-output/coverage.xml
    threshold: "80"
```

This means the same Coverage Gate can be used by multiple repositories:

```text
                  Coverage Gate
                       ↑
             reusable GitHub Action
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
 Billing System   Project A       Project B
```

Each repository can choose its own coverage threshold.

For example:

```text
Billing System → 80%
Project A      → 75%
Project B      → 90%
```

---

## Example: Billing System Integration

Coverage Gate is integrated into my **Billing System** project.

The Billing System's GitHub Actions workflow first runs the tests and generates:

```text
coverage-output/coverage.xml
```

Then it passes that file to Coverage Gate:

```yaml
- name: Run coverage gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage-output/coverage.xml
    threshold: "80"
```

The flow is:

```text
Billing System
      ↓
pytest
      ↓
Coverage report
      ↓
coverage-output/coverage.xml
      ↓
Coverage Gate
      ↓
Compare with 80%
      ↓
PASS / FAIL
```

In the Billing System CI run, the project achieved **91% coverage**, which was above the required **80% threshold**, so the Coverage Gate passed.

---

## Coverage Report Format

Coverage Gate expects a Cobertura XML report.

A coverage tool such as `pytest-cov` can generate this report:

```bash
pytest --cov=src --cov-report=xml:coverage-output/coverage.xml
```

The resulting XML contains coverage information such as the overall line coverage rate.

Coverage Gate parses this information and converts it into a percentage for comparison.

For example:

```text
XML line-rate = 0.91

0.91 × 100 = 91%

Coverage = 91%
Threshold = 80%

91 >= 80
→ PASS
```

---

## What Happens When the Gate Fails?

Suppose the project has:

```text
Coverage = 65%
Threshold = 80%
```

Coverage Gate detects that:

```text
65 < 80
```

and exits with a failure status.

Because the GitHub Actions step fails, the CI job also fails.

This makes the coverage requirement enforceable instead of being only informational.

---

## Project Structure

```text
coverage-gate/
│
├── src/
│   ├── __init__.py
│   ├── parser.py
│   ├── enforcer.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   └── fixtures/
│       └── sample.xml
│
├── action.yml
├── requirements.txt
└── README.md
```

### `src/parser.py`

Responsible for reading the Cobertura XML report and extracting the coverage information.

It converts the XML `line-rate` value into a percentage.

Example:

```text
line-rate = 0.85
        ↓
0.85 × 100
        ↓
85%
```

### `src/enforcer.py`

Responsible for applying the coverage rule.

It compares:

```text
actual coverage
        vs
required threshold
```

and determines whether the gate should pass or fail.

### `src/main.py`

Acts as the entry point of the Coverage Gate application.

It connects the input configuration, coverage parsing and threshold enforcement.

### `action.yml`

Defines the project as a GitHub Action.

It specifies the action's inputs and how GitHub should execute it.

### `tests/`

Contains unit tests for the Coverage Gate implementation.

### `tests/fixtures/sample.xml`

A sample Cobertura XML file used during testing.

It allows the parser to be tested without depending on a real project's coverage report.

---

## Local Development

Create a virtual environment and install the dependencies:

```bash
pip install -r requirements.txt
```

Run the tests:

```bash
pytest
```

The tests verify that the coverage XML is parsed correctly and that the coverage logic behaves as expected.

---

## Design

Coverage Gate follows a simple separation of responsibilities:

```text
GitHub Actions
      ↓
   action.yml
      ↓
   main.py
      ↓
   parser.py
      ↓
Read coverage.xml
      ↓
 enforcer.py
      ↓
Compare coverage
      ↓
 PASS / FAIL
```

The parser is responsible for **reading coverage**.

The enforcer is responsible for **checking the rule**.

The GitHub Action configuration is responsible for **making the functionality reusable in CI/CD**.

---

## Key Benefits

### 1. Reusable

The same action can be used by multiple GitHub repositories.

### 2. Automated

The coverage check happens automatically during CI.

### 3. Enforced

A project cannot silently ignore a coverage requirement because the workflow fails when coverage is below the threshold.

### 4. Configurable

Each repository can choose its own minimum coverage threshold.

### 5. Separate from the Application

Coverage enforcement is kept outside the application code, allowing the same tool to be reused across different projects.

---

## Technologies Used

* Python
* GitHub Actions
* pytest
* Cobertura XML
* XML parsing with Python
* GitHub Action inputs

---

## Author

**Shweta Boraganve**

GitHub: `shweta-borganve`

Coverage Gate repository:

`shweta-borganve/coverage-gate`

Billing System integration:

`shweta-borganve/Billing-System`