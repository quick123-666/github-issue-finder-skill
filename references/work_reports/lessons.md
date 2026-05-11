# Accumulated Lessons — Cross-Cutting Patterns

Lessons extracted from all work reports that apply beyond their specific project.

## 1. Rust → Python Error Type Mismatch

**Source:** mitmproxy WireGuard EADDRINUSE (#8222)

Python libraries wrapping Rust code (via PyO3, `mitmproxy_rs`, etc.) raise `RuntimeError` for all error conditions, even when the underlying error is a standard OS error like EADDRINUSE.

**Rule of thumb:**
- Rust binding errors → likely `RuntimeError`, not `OSError`
- Check the error message string for known patterns ("Address already in use", "os error N")
- Convert to `OSError` with proper `errno` so existing Python error handlers work
- Cross-platform: EADDRINUSE = 48 (macOS) = 98 (Linux)

**Applies to:** Any project using Rust Python bindings (`mitmproxy_rs`, `pydantic-core`, `ruff`, `uv`, etc.)

---

## 2. `bytes.splitlines()` Destroys Binary Data

**Source:** mitmproxy multipart newlines (#8221)

`bytes.splitlines()` strips `\n`, `\r\n`, and `\r` characters. This is fine for text but corrupts binary payloads where these bytes have meaning.

**Rule of thumb:**
- NEVER use `splitlines()` on content that may contain binary data
- Manual boundary/token splitting preserves all bytes
- Use `bytes.find(delimiter)` + slicing instead

**Applies to:** Any protocol parser, multipart form handling, binary stream processing.

---

## 3. Python 3.12+ F-String + Bytes Literal Pitfall

**Source:** mitmproxy multipart test (#8221, CI round 3)

Inside parenthesized expressions, Python 3.12+ implicitly concatenates adjacent string literals. Mixing `f"..."` and `b"..."` this way causes:

```
SyntaxError: cannot mix bytes and nonbytes literals
```

**Rule of thumb:**
- Convert f-string parts to bytes FIRST (`.encode()`), then concatenate with `b"..."` using `+`
- OR use variables for the intermediate values
- Never rely on implicit concatenation across `f"..."` and `b"..."` boundaries

---

## 4. Click `multiple=True` for Repeated CLI Options

**Source:** poetry multiple `--author` (#10889)

For CLI options that accept multiple values, use `multiple=True` on the click decorator — don't create separate `--author` / `--authors` flags.

```python
@click.option("--author", "authors", multiple=True)
```

**Rule of thumb:**
- `multiple=True` → receives as `tuple[str, ...]`
- When changing scalar to list, update ALL callers (tests, fixtures, conftest)
- Interactive loops: ask → append → confirm → repeat

---

## 5. Before Writing Code, Check for Existing PRs

**Source:** pylint JUnit reporter review + poetry multiple `--author`

Two people independently implemented the same feature (JUnit reporter for pylint). Poetry maintainer noted 4 competing PRs for the same `--author` fix.

**Rule of thumb:**
- **BEFORE implementing:** search `repo:owner/name "keyword" is:pr is:open` to find competing PRs
- Search GitHub issue comments for links to PRs (many issues have "I created PR #..." comments)
- If 1+ competing PRs exist, don't submit another unless yours is meaningfully different
- Better to comment on an existing PR with improvements than open a duplicate
- Check labels like "contributions: claimed" which indicate someone is already working on it

---

## 6. CI Failures Are Often Infrastructure, Not Your Code

**Source:** poetry multiple `--author` CI

Poetry's CI repeatedly failed with "runner lost communication" across all Python versions. The `poetry-plugin-export` tests (subset) passed fine.

**Rule of thumb:**
- Check if a subset of tests passes (e.g., `poetry-plugin-export` tests) while full test suite fails
- "Runner lost communication" / timeout errors are usually GitHub Actions infrastructure issues
- Look at annotations: if they just say "exit code 1" with no test failure details, it's infra
- Re-run CI or wait — these usually resolve on retry

---

## 7. Error Message Improvement Pattern

**Source:** mitmproxy WireGuard EADDRINUSE (#8222)

The web UI port conflict handler shows the "gold standard" for error messages:

```
Web server failed to listen on 127.0.0.1:8081 with [Errno 48] Address already in use
Try specifying a different port by using `--set web_port=8083`.
```

**Rule of thumb for error messages:**
1. State WHAT failed: "{component} failed to listen on {host}:{port}"
2. State WHY: "with {error type} {error detail}"
3. Suggest HOW TO FIX: "Try specifying a different port by using `--flag=port`"

---

## 8. Proto-Python-Frontend Three-Layer Pattern (Streamlit)

**Source:** streamlit camera_input size parameter (#15109)

When adding a feature that spans proto → Python → frontend:

1. **Proto:** Add fields to the existing message. Use `uint32` (default 0 = not set). No `optional` keyword needed.
2. **Python:** Add param to BOTH the public API function AND the internal `_func()` — they share the same signature.
3. **Frontend:** Proto snake_case → JS camelCase (automatic). Check `falsy` (0) for default-proto fields.
4. **Tests:** Add Python unit test (check proto field values) + typing test. Skip E2E for hardware-dependent features.

---

## 9. Encode Artifacts from Multipart Builders

**Source:** mitmproxy multipart (#8221)

`encode_multipart` in mitmproxy adds `hdrs.append(b"")` after each value, producing an extra `\r\n\r\n` in encoded output. The old `splitlines()` parser silently consumed these, but a byte-accurate parser must handle them.

**Rule of thumb:**
- When replacing a lossy parser with a lossless one, the lossy parser may have been hiding artifacts from the encoder
- Test round-trips: encode → decode → compare with original
- A `while` loop (not `if`) is needed to strip multiple trailing delimiter sequences

---

## 10. AsyncLocalStorage for Nested Context Tracking

**Source:** jestjs/jest test.step (#16157)

When implementing nested, async-safe context tracking (e.g., test steps within tests), use `AsyncLocalStorage` from `node:async_hooks`:

```typescript
const stepStorage = new AsyncLocalStorage<string | undefined>();

async function step<T>(title: string, body: () => T | Promise<T>): Promise<T> {
  const currentPath = stepStorage.getStore();
  const fullPath = currentPath ? `${currentPath} > ${title}` : title;
  return stepStorage.run(fullPath, async () => {
    try { return await body(); }
    catch (error) {
      if (error instanceof Error) error.message = `step "${fullPath}": ${error.message}`;
      throw error;
    }
  });
}
```

**Rule of thumb:**
- `AsyncLocalStorage` is the correct tool for per-coroutine state that must survive `await` boundaries
- Nesting: `.run()` automatically restores the parent store when the child completes
- Compatible with concurrent execution (each `run()` creates an independent async context)
- Type parameter: use `T | undefined` when the store may not be initialized
