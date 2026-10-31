# Coverage Gate Compatibility Contract

## 1. Supported Environments

- The GitHub Action uses the Composite Action runtime and sets up Python 3.11.
- GitHub-hosted Ubuntu Linux runners are the initial officially supported
  environment for the GitHub Action.
- The CI test matrix covers Python 3.11, 3.12, and 3.13.
- Linting and formatting checks run on Python 3.12.
- Docker images are built and tested in CI.
- The current GitHub Action is a Composite Action and does not require Docker
  to execute the action itself.


## 2. Supported Coverage Report Formats

feature/add-coverage-report-parser
Coverage Gate supports the following coverage report formats:

- **Cobertura XML (`.xml`):** Reads the root-level `coverage` element and its `line-rate` attribute.
- **LCOV (`.info`):** Reads source file records and line execution data from `SF:`, `DA:`, and `end_of_record` entries.

The report parser is selected based on the file extension:

- `.xml` selects the Cobertura parser.
- `.info` selects the LCOV parser.
- Unsupported file extensions produce a clear error.

JaCoCo XML and coverage.py JSON are not currently supported.

- Cobertura XML is the only currently supported coverage report format.
- The overall coverage report must have a `coverage` root element.
- The root element must contain a numeric `line-rate` attribute.
- LCOV, JaCoCo XML, and coverage.py JSON are not supported yet.
- Additional formats must be introduced through separate, tested changes.

## 3. Coverage Metrics and Semantics

### Overall line coverage

- Overall coverage is read from the root `coverage` element's `line-rate`.
- The value must be finite and between `0` and `1`, inclusive.
- Coverage Gate converts the value to a percentage by multiplying it by 100.
- For example, `line-rate="0.85"` represents 85% overall line coverage.
- Threshold and regression checks operate on coverage percentages.

### Per-file line coverage
 main

- Per-file coverage is calculated from valid line entries in the XML report.
- A line with `hits > 0` is covered; a line with `hits = 0` is uncovered.
- Duplicate entries for the same filename and line number are merged:
  the line is considered covered if any valid entry reports a positive hit count.
- Per-file percentages are derived from the unique line numbers collected
  for each file.
- The root-level `line-rate` remains the source of the overall coverage value;
  per-file percentages are not used to recalculate it.

### Changed-line coverage

- Changed-line coverage uses individual line-hit information from the report
  and the relevant source-code diff.
- Source filenames are normalized to repository-relative paths when they can
  be resolved inside the working directory.
- Unresolvable paths must not be guessed to be repository files.
- Changed-line coverage is a separate metric from overall line coverage.

### Branch coverage

feature/add-coverage-report-parser
- Coverage Gate checks line coverage for enforcement.
- Cobertura XML uses the `line-rate` value, a decimal between `0` and `1`, converted to a percentage.
- For example, `line-rate="0.85"` represents 85% line coverage.
- LCOV uses line execution data from `DA` records.
- An LCOV line is considered covered when its hit count is greater than zero.
- An LCOV line with a hit count of zero is considered uncovered.
- Overall and per-file coverage are calculated from the available line data.

main
- Branch coverage is not currently used for enforcement.
- A report may contain branch-related attributes, but they do not change
  the overall line-coverage calculation.

## 4. Missing and Invalid Reports

- A missing report file must produce a clear error.
- Malformed XML must produce a clear error.
feature/add-coverage-report-parser
- A Cobertura report without the required `coverage` root element or `line-rate` attribute must be rejected.
- A non-numeric, non-finite, or out-of-range Cobertura `line-rate` must be rejected.
- Empty LCOV reports must be rejected.
- Invalid LCOV line records, missing source filenames, invalid line numbers, negative hit counts, missing line data, and missing `end_of_record` entries must produce clear errors.
- Unsupported report formats must not be treated as valid coverage reports.
- Invalid reports must not cause the coverage check to pass silently.

## 5. Source Paths

- Cobertura XML provides per-file coverage information through its source and line data.
- LCOV identifies source files through `SF:` records.
- LCOV per-file coverage is calculated from the line records associated with each source file.
- LCOV source filenames are normalized where possible to repository-relative paths for consistent per-file and changed-line coverage reporting.
- Source path normalization may be addressed in future changes if additional features require it.

## 6. Compatibility and Testing

- Existing Cobertura behavior must remain compatible when new features are added.
- The Docker parser copy must remain synchronized with the corresponding parser in `src/`.
- Valid and invalid report fixtures must be covered by automated tests.
- Changes must pass the project's test suite and code-quality checks.
- LCOV support must not change the existing coverage enforcement behavior for Cobertura reports.

## 7. Future Extensions

Additional report formats may be added in separate changes after their schemas, coverage metrics, and error-handling rules are defined.

Potential future formats include coverage.py JSON and JaCoCo XML.

- A report with an unsupported root element must be rejected.
- A missing, non-numeric, non-finite, or out-of-range overall `line-rate`
  must be rejected.
- Line entries used by strict line-coverage parsing must have valid line
  numbers and hit counts.
- Line numbers must be positive integers, and hit counts must be
  non-negative integers.
- Empty or unsupported reports must not be treated as valid coverage reports.
- Invalid reports must never cause a coverage check to pass silently.
- Error messages and logs should help identify the report or data that failed.

## 5. Source Paths

- The overall coverage parser does not need source paths to calculate
  the root-level coverage percentage.
- Per-file coverage uses filenames provided by the report.
- Changed-line analysis may use the report's `<sources>` entries to resolve
  filenames against the repository working directory.
- A resolved repository file is represented with a repository-relative path.
- If a filename cannot be resolved inside the working directory, its original
  path is preserved rather than inventing a repository-relative path.
- Path handling must be tested on supported environments before its behavior
  is broadened.

## 6. Compatibility and Testing

- Existing Cobertura behavior must remain compatible as new features are added.
- Valid and invalid report fixtures must be covered by automated tests.
- Parser changes must test relevant edge cases, including malformed input,
  duplicate lines, missing attributes, and invalid numeric values.
- Changes must pass the project test suite and applicable code-quality checks.
- New report formats must not silently change existing Cobertura semantics.

## 7. Future Extensions

Potential extensions include:

- LCOV report parsing.
- JaCoCo XML report parsing.
- coverage.py JSON report parsing.
- Baseline comparison and publication.

Each extension must define its supported input, metric semantics,
validation behavior, error handling, and automated tests before release.
 main
