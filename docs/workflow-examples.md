# GitHub Actions Workflow Examples

These examples show how to generate coverage reports and run Coverage Gate for Python, Java, JavaScript/TypeScript, Go, and .NET projects.

All examples use the Coverage Gate Composite Action. Replace `@main` with `@v1` after the next stable release updates the major-version tag.

## 1. Python — Cobertura XML

**Coverage report:** `coverage.xml`

```yaml
name: Python Coverage

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run tests and generate coverage
        run: pytest --cov --cov-report=xml:coverage.xml

      - name: Check coverage
        uses: shweta-borganve/coverage-gate@main
        with:
          coverage-file: coverage.xml
          threshold: "80"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 2. Java — JaCoCo XML

**Coverage report:** `target/site/jacoco/jacoco.xml`

Add the JaCoCo Maven plugin inside the `build/plugins` section of your `pom.xml`:

```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.12</version>
  <executions>
    <execution>
      <goals>
        <goal>prepare-agent</goal>
      </goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>verify</phase>
      <goals>
        <goal>report</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

Java workflow:

```yaml
name: Java Coverage

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
          cache: maven

      - name: Build, test, and generate JaCoCo report
        run: mvn -B verify

      - name: Check coverage
        uses: shweta-borganve/coverage-gate@main
        with:
          coverage-file: target/site/jacoco/jacoco.xml
          threshold: "80"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 3. JavaScript and TypeScript — LCOV

**Coverage report:** `coverage/lcov.info`

Configure Jest to generate LCOV coverage output:

```javascript
module.exports = {
  collectCoverage: true,
  coverageReporters: ["text", "lcov"],
};
```

JavaScript and TypeScript workflow:

```yaml
name: JavaScript Coverage

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Run tests and generate coverage
        run: npx jest --coverage --coverageReporters=text --coverageReporters=lcov

      - name: Check coverage
        uses: shweta-borganve/coverage-gate@main
        with:
          coverage-file: coverage/lcov.info
          threshold: "80"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 4. Go — Coverprofile

**Coverage report:** `coverage.out`

```yaml
name: Go Coverage

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"

      - name: Run tests and generate coverage
        run: go test ./... -coverprofile=coverage.out

      - name: Check coverage
        uses: shweta-borganve/coverage-gate@main
        with:
          coverage-file: coverage.out
          threshold: "80"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 5. .NET — OpenCover XML

**Coverage report:** `TestResults/Coverage/coverage.opencover.xml`

Install Coverlet MSBuild in your test project. Replace the example project path with your actual test project path:

```bash
dotnet add path/to/Your.Tests.csproj package coverlet.msbuild
```

.NET workflow for a single test project:

```yaml
name: .NET Coverage

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "8.0.x"

      - name: Restore dependencies
        run: dotnet restore path/to/Your.Tests.csproj

      - name: Run tests and generate OpenCover report
        run: |
          mkdir -p TestResults/Coverage
          dotnet test path/to/Your.Tests.csproj --no-restore \
            /p:CollectCoverage=true \
            /p:CoverletOutputFormat=opencover \
            /p:CoverletOutput=TestResults/Coverage/

      - name: Check coverage
        uses: shweta-borganve/coverage-gate@main
        with:
          coverage-file: TestResults/Coverage/coverage.opencover.xml
          threshold: "80"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Permissions

The examples grant:

- `contents: read` for checking out repository code.
- `pull-requests: write` for Coverage Gate pull request comments.

If you disable pull request comments, remove `pull-requests: write` and the `github-token` input.

## Important Notes

- Generate the coverage report before running Coverage Gate.
- The `coverage-file` path is relative to the repository workspace.
- The threshold represents line coverage.
- Branch coverage is reported separately when available; it is not currently enforced.
- Changed-line coverage enforcement applies to pull requests.
- The Docker Action does not currently support OpenCover XML or Istanbul / NYC JSON. Use the Composite Action for those formats.
- These are workflow templates, not end-to-end tested sample applications. Adjust SDK versions, test commands, project paths, and report paths for your repository.
- The JavaScript example uses Jest. Adapt the configuration and test command if your project uses another test runner.
