# Coverage Gate Compatibility Contract

## 1. Supported Environments

- The primary GitHub Action is a Composite Action.
- The Composite Action sets up Python 3.11.
- GitHub-hosted Ubuntu Linux runners are the officially tested environment.
- The CI test matrix covers Python 3.11, 3.12, and 3.13.
- Linting and formatting checks run on Python 3.12.
- Docker images and the Docker Action are built and tested in CI.
- The Composite Action does not require Docker to execute.

## 2. Supported Coverage Report Formats

Coverage Gate supports the following report formats:

| Format | File type | Identification |
|---|---|---|
| Cobertura | XML | `coverage` root element |
| JaCoCo | XML | `report` root element |
| OpenCover | XML | `CoverageSession` root element |
| LCOV | Text | `.info` extension |
| coverage.py | JSON | Coverage.py JSON structure |
| Go coverprofile | Text | `.out` or `.coverprofile` extension |
| Istanbul / NYC | JSON | Istanbul statement coverage structure |

XML namespaces are supported when identifying supported XML report roots.

### Composite Action

The Composite Action supports all seven formats listed above.

### Docker Action

The Docker Action supports:

- Cobertura XML
- JaCoCo XML
- LCOV
- Go coverprofile
- coverage.py JSON

OpenCover XML and Istanbul / NYC JSON are not currently documented as supported by the Docker Action.

## 3. Multiple Coverage Reports

- Multiple report paths can be supplied as a comma-separated list.
- Each report is parsed using its supported format.
- Coverage data from the reports is merged before overall coverage is calculated.
- Duplicate file and line entries are merged.
- A line is considered covered if any valid report records it as covered.
- Changed-line coverage uses the merged line-coverage data.
- Report paths must point to valid supported reports.

## 4. Coverage Metrics and Semantics

### Overall line coverage

- Overall line coverage is calculated from covered and total executable lines.
- Coverage values are represented as percentages.
- Global threshold and regression checks operate on line coverage.
- The parser uses the report format's supported coverage data to calculate the metrics.

For example, 85 covered lines out of 100 executable lines represents 85% line coverage.

### Per-file line coverage

- Per-file coverage is calculated using the available line-level coverage information.
- A line with a positive hit count is covered.
- A line with zero hits is uncovered.
- Duplicate entries for the same file and line are merged.
- A line is considered covered if any valid entry reports it as covered.

### Component coverage

- Component thresholds can be configured for repository-relative files or directories.
- Each configured component is checked against its minimum coverage percentage.
- Component thresholds are configured using the `component-thresholds` input.
- Component paths must resolve within the repository workspace.

### Changed-line coverage

- Changed-line coverage uses line-level coverage data and the relevant source-code diff.
- Source filenames are normalized to repository-relative paths when they can be resolved inside the working directory.
- Unresolvable paths must not be guessed to be repository files.
- Changed-line coverage is separate from overall line coverage.
- Changed-line enforcement applies to pull request checks.
- When pull request comparison data is unavailable, the action reports the limitation rather than silently treating missing data as successful coverage.

### Branch coverage

- Branch coverage is reported separately from line coverage when branch data is available.
- Branch coverage does not replace overall line coverage.
- Global line-coverage thresholds are not branch-coverage thresholds.
- Branch coverage is not currently used for enforcement.

### Regression detection

- Baseline coverage can be supplied for regression detection.
- Maximum allowed regression is configurable.
- Regression checks use coverage percentages and remain separate from changed-line coverage.

## 5. Missing and Invalid Reports

- A missing report file must produce a clear error.
- Malformed XML or JSON must produce a clear error.
- Unsupported XML root elements must be rejected.
- Invalid or incomplete report structures must not be treated as valid coverage reports.
- Invalid line numbers, hit counts, or inconsistent coverage data must be handled safely.
- Empty or unsupported reports must not be treated as valid coverage reports.
- Invalid reports must never cause a coverage check to pass silently.
- Error messages and logs should help identify the report or data that failed.

## 6. Source Paths

- Per-file coverage uses filenames provided by the report.
- Changed-line analysis resolves source filenames against the repository working directory when possible.
- Cobertura source entries may be used when resolving filenames.
- LCOV, Go, JSON, JaCoCo, and OpenCover source paths are normalized where supported by their parsers.
- A resolved repository file is represented with a repository-relative path.
- Paths that cannot be resolved inside the working directory must not be treated as repository files.
- Path handling must prevent workspace escape through unsafe paths or symlinks.
- Path handling must be tested on supported environments before its behavior is broadened.

## 7. Compatibility and Testing

- Existing report-format behavior must remain compatible as new features are added.
- Valid and invalid fixtures for supported report formats must be covered by automated tests.
- Parser changes must test relevant edge cases, including malformed input, duplicate lines, missing attributes, and invalid numeric values.
- Multiple-report merging must preserve correct coverage semantics.
- Changes must pass the project test suite and applicable code-quality checks.
- New report formats must not silently change existing coverage semantics.

## 8. Future Extensions

Potential extensions include:

- Additional branch coverage enforcement.
- Additional report formats.
- Further compatibility testing across operating systems and execution environments.

Each extension must define its supported input, metric semantics, validation behavior, error handling, and automated tests before release.
