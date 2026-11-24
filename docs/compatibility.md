# Coverage Gate Compatibility Contract

## 1. Supported Environments

- The GitHub Action uses the Composite Action runtime and sets up Python 3.11.
- GitHub-hosted Ubuntu Linux runners are the initial officially supported environment for the GitHub Action.
- The CI test matrix covers Python 3.11, 3.12, and 3.13.
- Linting and formatting checks run on Python 3.12.
- Docker images are built and tested in CI.
- The current GitHub Action is a Composite Action and does not require Docker to execute the action itself.

## 2. Supported Coverage Report Formats

Coverage Gate supports these report formats:

- **Cobertura XML:** identified by XML content with a `coverage` root element.
- **LCOV:** identified by the `.info` file extension.
- **coverage.py JSON:** identified by the `.json` file extension.

JaCoCo XML is not currently supported.

### Cobertura XML

- The overall coverage report must have a `coverage` root element.
- The root element must contain a numeric `line-rate` attribute.
- The `line-rate` value must be finite and between `0` and `1`, inclusive.
- Per-file line coverage is calculated from valid line entries.

### LCOV

- LCOV reports use the `.info` file extension.
- Source files are identified by `SF` records.
- Line coverage is read from `DA` records or validated `LF` and `LH` counts.
- The report must contain source and usable line coverage data.
- Invalid or inconsistent line counts are rejected.

### coverage.py JSON

- JSON reports use the `.json` file extension.
- The report must contain `totals` and `files` objects.
- Overall coverage is calculated using `covered_lines` and `num_statements`.
- Per-file coverage uses `executed_lines`, `missing_lines`, and file summary data.
- Total and per-file line counts must be consistent.
- Invalid or incomplete line data is rejected.

## 3. Coverage Metrics and Semantics

### Overall line coverage

- Cobertura XML uses the root-level `line-rate`.
- LCOV uses the total covered and found line counts.
- coverage.py JSON uses `covered_lines` and `num_statements`.
- Coverage values are converted to percentages.
- Threshold and regression checks operate on coverage percentages.

For example, a Cobertura `line-rate` of `0.85` represents 85% overall line coverage.

### Per-file line coverage

- Cobertura XML uses valid line entries from each class.
- LCOV uses source-file records and line-hit data.
- coverage.py JSON uses executed and missing line lists.
- A line with a positive hit count is covered; a line with zero hits is uncovered.
- Duplicate Cobertura or LCOV entries for the same filename and line number are merged. A line is considered covered if any valid entry reports a positive hit count.
- Per-file percentages are calculated from the unique line numbers collected for each file.

### Changed-line coverage

- Changed-line coverage uses individual line-hit information from the report and the relevant source-code diff.
- Source filenames are normalized to repository-relative paths when they can be resolved inside the working directory.
- Unresolvable paths must not be guessed to be repository files.
- Changed-line coverage is a separate metric from overall line coverage.

### Branch coverage

- Branch coverage is not currently used for enforcement.
- A report may contain branch-related attributes, but they do not change the overall line-coverage calculation.

## 4. Missing and Invalid Reports

- A missing report file must produce a clear error.
- Malformed XML or JSON must produce a clear error.
- A report with an unsupported XML root element must be rejected.
- A missing, non-numeric, non-finite, or out-of-range Cobertura `line-rate` must be rejected.
- Invalid LCOV source records, line numbers, hit counts, or inconsistent counts must be rejected.
- Invalid JSON structures, missing line data, invalid counts, or inconsistent totals must be rejected.
- Line numbers must be positive integers, and hit counts must be non-negative integers.
- Empty or unsupported reports must not be treated as valid coverage reports.
- Invalid reports must never cause a coverage check to pass silently.
- Error messages and logs should help identify the report or data that failed.

## 5. Source Paths

- The overall coverage parser does not need source paths to calculate the Cobertura root-level coverage percentage.
- Per-file coverage uses filenames provided by the report.
- Changed-line analysis may use the Cobertura `<sources>` entries to resolve filenames against the repository working directory.
- LCOV and JSON source filenames are normalized against the working directory when possible.
- A resolved repository file is represented with a repository-relative path.
- If a filename cannot be resolved inside the working directory, its original path is preserved rather than inventing a repository-relative path.
- JSON filenames that collide after normalization are rejected.
- Path handling must be tested on supported environments before its behavior is broadened.

## 6. Compatibility and Testing

- Existing Cobertura behavior must remain compatible as new features are added.
- Valid and invalid fixtures for every supported report format must be covered by automated tests.
- Parser changes must test relevant edge cases, including malformed input, duplicate lines, missing attributes, and invalid numeric values.
- Changes must pass the project test suite and applicable code-quality checks.
- New report formats must not silently change existing coverage semantics.

## 7. Future Extensions

Potential extensions include:

- JaCoCo XML report parsing.
- Additional coverage metrics, such as branch coverage enforcement.

Each extension must define its supported input, metric semantics, validation behavior, error handling, and automated tests before release.
