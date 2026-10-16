# Coverage Gate Roadmap

## Goal

A free, local-first, fork-safe PR coverage gate with no external service.
Build the basics first, then add small unique features, each shippable and
testable on its own.

## Principles

- Keep existing inputs and behavior working unless a change is documented.
- One small, independently useful feature per release.
- Coverage thresholds and regressions are measured in percentage points.
- Prefer explicit configuration. Auto-detect only when unambiguous.
- Keep GitHub permissions minimal; treat fork PRs as untrusted.

## Tier 1: Basics

### 1. Stabilize current behavior

- Document Cobertura behavior, input defaults, and failure cases.
- Test threshold/regression equality, invalid values, missing reports,
  malformed XML, and out-of-range `line-rate`.
- Keep the composite action; no Docker migration without a measured benefit.

**Done when:** existing CLI/action inputs work unchanged and the documented
test and lint commands pass in CI.

### 2. GitHub run summary

- Write coverage, threshold, status, warning, and regression details to
  `$GITHUB_STEP_SUMMARY` (needs no token or extra permissions).

**Done when:** tests cover pass, fail, warning, and regression output, and the
CLI still works when `GITHUB_STEP_SUMMARY` is unset.

### 3. Per-file coverage data

- Extend the parser to expose per-file line hit data for Cobertura.
- Keep total-coverage behavior unchanged.

**Done when:** fixtures verify per-file percentages and uncovered line numbers.

### 4. Additional report formats

- Add a small parser interface returning the normalized metrics.
- Add LCOV, then coverage.py JSON, then JaCoCo XML, one per change.
- Explicit report path only.

**Done when:** each format has a fixture and tests for empty, malformed,
missing-data, and invalid-value reports, and existing threshold tests pass
unchanged.

## Tier 2: Unique features (after Tier 1)

### 5. Changed-code coverage report

- Read the PR diff and list uncovered changed lines, ranked by uncovered
  changed lines per file. Show raw counts.
- Report-only first; no gating. Say "not available" when line data is missing.

**Done when:** base/head fixtures verify line mapping, ranking, and
added/deleted/renamed files.

### 6. Fork-safe reporting kit

- The gate runs unprivileged in `pull_request` and uploads a small result
  artifact (coverage, status, PR number, head SHA).
- Optional `workflow_run` reporter posts or updates one PR comment. It never
  checks out fork code and validates run, PR, SHA, and artifact schema.
- Ship example workflows with minimal `permissions`.

**Done when:** fork PRs run with a read-only token and no secrets, the reporter
rejects mismatched or malformed artifacts, and repeated runs update one comment.

### 7. Opt-in report discovery

- `coverage-file: auto` proceeds only when exactly one supported report is
  found; otherwise fail and list candidates.

**Done when:** tests cover one, none, and multiple matches, and explicit paths
override discovery.

## Later (needs design first)

- **Trusted baselines:** decide durable storage, branch key, retention,
  missing-baseline behavior, and trusted writers. Do not use Actions cache as
  durable history. Manual `baseline-coverage` stays supported.
- **Security hardening:** dependency/base-image scanning, non-root runtime, and
  minimal workflow permissions.
- **Docker packaging:** only with a runner compatibility matrix and measured
  comparison against the composite action.

## Out of scope

- Guessing among multiple reports.
- Zero-day or cryptographic isolation claims without a specific threat model.
- Complexity or churn-weighted risk scores before changed-line reporting
  proves useful.
