# Pylint JUnit Reporter — PR Review & Comparison

- **Repo:** pylint-dev/pylint
- **Issue:** [#9143](https://github.com/pylint-dev/pylint/issues/9143) — Add pylint-junit reporter class
- **Reviewed PRs:** [#10985](https://github.com/pylint-dev/pylint/pull/10985) (hamza-mobeen), [#11001](https://github.com/pylint-dev/pylint/pull/11001) (ours, abandoned)
- **Date:** 2026-05-10

## Context

Two competing PRs implementing a JUnit XML reporter for pylint. Reviewed both and recommended merging #10985 with improvements.

## Comparison

| Aspect | #11001 (ours) | #10985 (hamza-mobeen) |
|--------|---------------|----------------------|
| Architecture | Adds to existing `JSONReporter` | Hook-based, clean standalone module |
| Test location | In existing test file | Separate `test_junit_reporter.py` |
| CI integration | Custom JUnit writing | Uses standard `pytest-junit` |
| Error elements | Missing `<error>` for fatal | Not present |
| `MultiReporter` import | **Bug:** accidentally removed | Not addressed |
| Test coverage | 8 tests | 14 tests |

## Decision

Abandoned #11001. Recommended merging #10985 after:
1. Adding `<error>` element for fatal messages
2. Using `sorted()` for deterministic output
3. Including file/line/category attributes

## Key Insight

- Before writing a competing PR, always check if someone else has already submitted one
- Hook-based architecture (register via `linter.register_reporter()`) is cleaner than modifying existing reporter classes
- JUnit XML should include: `classname`, `file`, `line`, `category` attributes for CI tool integration
- `sorted()` is critical for deterministic XML output in parallel test environments

## Keywords

`JUnit` `XML` `reporter` `hook-based` `register_reporter` `CI integration` `sorted()` `deterministic output` `competing PR` `plugin architecture` `test_suite` `test_case`
