# Coverage Gate

A reusable GitHub Action to enforce test coverage thresholds and detect coverage regressions.

## Features
- Coverage threshold and regression checks
- Changed-line coverage analysis
- Cobertura XML, LCOV, and coverage.py JSON support
- GitHub summaries and PR comments
- Historical coverage tracking and SVG badges

## Project Structure

```text
coverage-gate/
├── src/                    # Core application
│   ├── main.py             # Workflow coordination
│   ├── parser.py           # Coverage report parsing
│   ├── enforcer.py         # Threshold and regression checks
│   ├── changed_lines.py    # Changed-line analysis
│   ├── changed_coverage.py # Coverage calculations
│   ├── coverage_trend.py   # Historical coverage tracking
│   ├── pr_comment.py      # Pull request comments
│   ├── summary.py          # GitHub summaries
│   ├── badge.py            # SVG badges
│   └── logger_config.py    # Logging
├── docker/                 # Docker Action and entry point
├── tests/                  # Automated tests and fixtures
├── docs/                   # Roadmap and compatibility docs
├── .github/workflows/      # CI and release workflows
├── action.yml              # Composite Action
├── Dockerfile              # Root Docker configuration
└── requirements*.txt       # Dependencies
```

## Architecture

`src/main.py` coordinates the application, and `src/parser.py` parses coverage reports. Other modules handle enforcement, changed-line analysis, PR comments, trends, summaries, badges, and logging.

The Docker Action reuses the shared `src/` code to avoid duplication.

## Development

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -q
```

## Documentation
- [Roadmap](docs/ROADMAP.md)
- [Compatibility](docs/compatibility.md)
- [Docker Action](docker/README.md)

[GitHub Repository](https://github.com/shweta-borganve/coverage-gate)
