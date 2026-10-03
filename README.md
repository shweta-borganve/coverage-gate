COVERAGE GATE

A small GitHub Action I built to check test coverage in CI.

The action takes a Cobertura XML coverage report, reads the current line coverage, and checks it against a minimum percentage.

I started with a basic coverage check and then added warning, GitHub Actions output, configurable settings, and coverage regression checking.

How it works

text
pytest
  ↓
coverage.xml
  ↓
Coverage Gate
  ↓
read coverage
  ↓
check rules
  ↓
PASS / FAIL

For example, if the coverage is 85% and the required coverage is 80%, the check passes.

text
85% >= 80%  → PASS

If it is 75%:

text
75% < 80%   → FAIL


Features

- Cobertura XML coverage support
- Minimum coverage threshold
- Warning when coverage is close to the threshold
- Configurable warning margin
- Coverage regression check using a baseline
- Configurable maximum regression
- Coverage available as a GitHub Actions output
- Input validation and error handling
- pytest test suite
- Ruff, Black and isort checks
- GitHub Composite Action
- Automatic releases with semantic-release

Inputs

text
coverage-file
threshold
warning-margin
baseline-coverage
max-regression


Example:

yaml
- name: Run coverage gate
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage-output/coverage.xml
    threshold: "80"
    warning-margin: "5"
    baseline-coverage: "89"
    max-regression: "5"

The last two inputs are optional. They are used when I want to check whether coverage has dropped too much compared with an earlier value.

Regression check

The threshold and regression check are slightly different.

The threshold checks:

text
Is current coverage >= required coverage?

The regression check asks:

text
Did coverage drop more than the allowed amount?

For example:

text
Baseline coverage : 89%
Current coverage  : 85%
Allowed regression: 5%

Drop = 4 percentage points

4 <= 5
PASS

If the current coverage is 82%:

text
Baseline coverage : 89%
Current coverage  : 82%
Allowed regression: 5%

Drop = 7 percentage points

7 > 5
REGRESSION
FAIL


A drop equal to the maximum allowed value is accepted.

GitHub Actions output

The action also exposes the current coverage as an output.

yaml
- name: Run coverage gate
  id: coverage
  uses: shweta-borganve/coverage-gate@v1
  with:
    coverage-file: coverage-output/coverage.xml
    threshold: "80"

- name: Print coverage
  run: echo "Coverage: ${{ steps.coverage.outputs.coverage }}"

Project structure

text
coverage-gate/
├── src/
│   ├── parser.py
│   ├── enforcer.py
│   └── main.py
│
├── tests/
│   ├── test_parser.py
│   ├── test_enforcer.py
│   ├── test_main.py
│   └── fixtures/
│       └── sample.xml
│
├── .github/
│   └── workflows/
│       ├── pr-checks.yml
│       └── release.yml
│
├── action.yml
├── requirements.txt
└── README.md


parser.py handles the Cobertura XML file and converts the line-rate value into a percentage.

enforcer.py contains the coverage rules, including the threshold, warning and regression checks.

main.py provides the command-line entry point.

action.yml connects the Python code with GitHub Actions and defines the action inputs and output.

Running locally

I used a virtual environment for the project.
bash
python3 -m venv .venv
source .venv/bin/activate

Install the development tools:

bash
python -m pip install pytest ruff black isort

Run the tests:

bash
pytest

Current test result:

text
32 passed

I also check the code with:

bash
ruff check .
black --check .
isort --check-only .
git diff --check

Testing the CLI

Basic check:

bash
python -m src.main tests/fixtures/sample.xml 80

With warning margin:

bash
python -m src.main tests/fixtures/sample.xml 80 10

With regression checking:

bash
python -m src.main tests/fixtures/sample.xml 80 5 90 5

The arguments are:

text
coverage file
threshold
warning margin
baseline coverage
maximum regression

Development

I worked on the project feature by feature using Git branches and pull requests.

After making changes, I run the tests and code-quality checks locally, push the feature branch, and create a PR.

The PR workflow runs the project's tests and checks the Coverage Gate itself.

After the PR is merged into main, semantic-release creates the release automatically based on the commit message.

The current release is:

text
v1.5.0

Feature 6 was released with:

text
feat: add coverage regression detection

What I learned from this project

This project helped me get more comfortable with Python testing and GitHub Actions.

The main things I worked with were:

- Python and XML parsing
- pytest
- GitHub Actions
- Composite Actions
- Git branching and pull requests
- CI checks
- semantic versioning and releases

I also learned how to keep the parsing part separate from the actual coverage rules, which made it easier to add new checks later.

Repository

GitHub:

`https://github.com/shweta-borganve/coverage-gate`

Shweta Boraganve