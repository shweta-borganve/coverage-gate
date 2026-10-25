# Coverage Gate Compatibility Contract

## 1. Supported Runners

- GitHub-hosted Ubuntu Linux runners are the initial supported environment for the GitHub Action.
- Local development is supported on systems where Python 3.11 or a compatible version is available.
- Docker can be used to run Coverage Gate and its tests in a container.
- The current GitHub Action is a Composite Action and does not require Docker.

## 2. Supported Coverage Report Formats

Coverage Gate supports the following coverage report formats:

- **Cobertura XML (`.xml`):** Reads the root-level `coverage` element and its `line-rate` attribute.
- **LCOV (`.info`):** Reads source file records and line execution data from `SF:`, `DA:`, and `end_of_record` entries.

The report parser is selected based on the file extension:

- `.xml` selects the Cobertura parser.
- `.info` selects the LCOV parser.
- Unsupported file extensions produce a clear error.

JaCoCo XML and coverage.py JSON are not currently supported.

## 3. Coverage Metrics

- Coverage Gate checks line coverage for enforcement.
- Cobertura XML uses the `line-rate` value, a decimal between `0` and `1`, converted to a percentage.
- For example, `line-rate="0.85"` represents 85% line coverage.
- LCOV uses line execution data from `DA` records.
- An LCOV line is considered covered when its hit count is greater than zero.
- An LCOV line with a hit count of zero is considered uncovered.
- Overall and per-file coverage are calculated from the available line data.
- Branch coverage is not currently used for enforcement.

## 4. Missing and Invalid Reports

- A missing report file must produce a clear error.
- Malformed XML must produce a clear error.
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
