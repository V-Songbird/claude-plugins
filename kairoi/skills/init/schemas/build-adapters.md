# Build Adapter Detection

How to detect the project's stack and generate `.kairoi/build-adapter.json`.

## Detection Priority

Check for these files in the project root, in order. First match wins.

| Detect File | Stack ID | Test Command | Source Dirs | Test Dirs |
|---|---|---|---|---|
| `package.json` | See Node.js section below | — | `['src/']` | `['__tests__/', 'test/', 'tests/']` |
| `pyproject.toml` | `python-pytest` | `pytest` | `['src/', '.']` | `['tests/', 'test/']` |
| `requirements.txt` | `python-pytest` | `pytest` | `['src/', '.']` | `['tests/', 'test/']` |
| `Cargo.toml` | `rust-cargo` | `cargo test` | `['src/']` | `['tests/']` |
| `go.mod` | `go` | `go test ./...` | `['.']` | `['.']` |
| `build.gradle` or `build.gradle.kts` | `jvm-gradle` | `./gradlew test` | See JVM section | `['src/test/']` |
| `pom.xml` | `jvm-maven` | `mvn test` | See JVM section | `['src/test/']` |
| `*.csproj` or `*.sln` | `dotnet` | `dotnet test` | `['src/']` | `['tests/', 'test/']` |
| `composer.json` | `php-phpunit` | `./vendor/bin/phpunit` | `['src/']` | `['tests/']` |
| `Gemfile` | `ruby-rspec` | `bundle exec rspec` | `['lib/', 'app/']` | `['spec/']` |

### JVM Source Directory Detection

For `jvm-gradle` and `jvm-maven`, do NOT use `src/main/` directly — it often
contains generated code directories (`gen/`, `generated/`) that should not be
tracked as source. Instead:

1. Check which language directories exist under `src/main/`:
   `java/`, `kotlin/`, `scala/`, `groovy/`
2. Use those specific directories as `source_dirs`
3. Set `exclude_dirs` to common generated paths:
   `['src/main/gen/', 'src/main/generated/', 'build/generated/']`

**Example** for a Kotlin IntelliJ plugin:
```json
{
  "source_dirs": ["src/main/kotlin/"],
  "test_dirs": ["src/test/"],
  "exclude_dirs": ["src/main/gen/", "src/main/generated/"]
}
```

If no language directory is found, fall back to `src/main/` but still populate
`exclude_dirs` with `gen/` and `generated/` subdirectories if they exist.

### Node.js Sub-Detection

When `package.json` is found, read it and check:

1. If `scripts.test` contains `vitest` → stack: `node-vitest`
2. If `scripts.test` contains `jest` → stack: `node-jest`
3. If `devDependencies` or `dependencies` has `vitest` → stack: `node-vitest`
4. If `devDependencies` or `dependencies` has `jest` → stack: `node-jest`
5. If `devDependencies` has `@playwright/test` → add note: "Playwright detected for E2E"
6. Fallback: stack: `node-generic`, test command: `npm test`

Test command: prefer `npx vitest run` or `npx jest` over `npm test` for parseable output.

If `pnpm-lock.yaml` exists, use `pnpm` instead of `npm`/`npx`.
If `yarn.lock` exists, use `yarn` instead of `npm`/`npx`.
If `bun.lockb` exists, use `bun` instead of `npm`/`npx`.

## Source Directory Validation

After detection, verify the detected `source_dirs` and `test_dirs` actually exist in the project.
Remove any that don't. If ALL source dirs are missing, warn the user that the project structure
doesn't match the expected layout and ask them to specify source/test directories manually.
