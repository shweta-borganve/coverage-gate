# Coverage Gate

A lightweight, custom GitHub Action that parses Cobertura XML coverage reports and enforces a minimum test coverage threshold. If the coverage falls below your threshold, the action fails your CI pipeline.

---

## Features

* **XML Parsing:** Reads standard Cobertura coverage reports (`coverage.xml`).
* **Threshold Enforcement:** Compares total line coverage against a user-defined minimum percentage.
* **Composite Action:** Fast and easy to run in any GitHub Actions workflow using standard runners.

---

## Usage

Add this action to your workflow file (e.g., `.github/workflows/ci.yml`) in your project repository:

folder structure:
coverage-gate/
├── .github/
│   └── workflows/
│       └── (your workflow files if testing in other repos)
├── .pytest_cache/
├── src/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── enforcer.py
│   ├── main.py
│   └── parser.py
├── tests/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── fixtures/
│   │   └── sample.xml
│   └── test_parser.py
├── action.yml
├── README.md
└── requirements.txt 

Quick Breakdown of Key Files & Folders:
src/parser.py: Parses the Cobertura XML coverage report and extracts the line rate.

src/enforcer.py: Contains the logic to compare your actual coverage against your defined threshold.

src/main.py: The CLI entry point that ties the parser and enforcer together for execution.

tests/fixtures/sample.xml: Sample XML file used for local unit testing.

tests/test_parser.py: Pytest file that verifies the XML parser works correctly.

action.yml: Configures your repository as a composite GitHub Action.

requirements.txt: Lists project dependencies.

README.md: Documentation on how to use your action in other repositories. 