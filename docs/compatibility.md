# Coverage Gate Compatibility Contract

## 1. Supported Runners

- GitHub-hosted Ubuntu Linux runners are the initial supported environment for the GitHub Action.
- Local development is supported on systems where Python 3.11 or a compatible version is available.
- Docker can be used to run Coverage Gate and its tests in a container.
- The current GitHub Action is a Composite Action and does not require Docker.

## 2. Supported Coverage Report Formats

- Cobertura XML is the only currently supported coverage report format.
- The report must contain a `coverage` root element with a `line-rate` attribute.
- LCOV, JaCoCo XML, and coverage.py JSON are not supported yet.

## 3. Coverage Metrics

- Coverage Gate currently checks line coverage only.
- The `line-rate` value is a decimal between `0` and `1`.
- The value is multiplied by 100 to obtain a percentage.
- For example, `line-rate="0.85"` represents 85% line coverage.
- Branch coverage is not currently used for enforcement.

## 4. Missing and Invalid Reports

- A missing report file must produce a clear error.
- Malformed XML must produce a clear error.
- A report without the required `line-rate` attribute must produce a clear error.
- A non-numeric or out-of-range `line-rate` must be rejected.
- Empty or unsupported reports must not be treated as valid coverage reports.
- Invalid reports must not cause the coverage check to pass silently.

## 5. Source Paths

- The current parser reads only the root-level line coverage value.
- It does not currently read or normalize source file paths.
- Path normalization will be addressed if future features need file-level coverage analysis.

## 6. Compatibility and Testing

- Existing Cobertura behavior must remain compatible when new features are added.
- Valid and invalid report fixtures must be covered by automated tests.
- Changes must pass the project's test suite and code-quality checks.

## 7. Future Extensions

Additional report formats may be added in separate changes after their schemas, coverage metrics, and error-handling rules are defined.