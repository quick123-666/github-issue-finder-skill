# Multipart Parser Stripping \n and \r from Binary Content

- **Repo:** mitmproxy/mitmproxy
- **Issue:** [#4466](https://github.com/mitmproxy/mitmproxy/issues/4466) — Error parsing multipart with newline in the content
- **PR:** [#8221](https://github.com/mitmproxy/mitmproxy/pull/8221)
- **Date:** 2026-05-10

## Problem

`decode_multipart()` in `mitmproxy/net/http/multipart.py` uses `bytes.splitlines()` to split body content, which discards `\n` and `\r` bytes. This corrupts binary data in multipart form uploads.

## Root Cause

Original code:

```python
body = body.splitlines()
```

`bytes.splitlines()` removes line-ending characters (`\n`, `\r\n`, `\r`), which is fine for text but destructive for binary content where `\n` and `\r` are meaningful data bytes.

## Fix

**File:** `mitmproxy/net/http/multipart.py`

Replace `splitlines()` with manual boundary splitting:

```python
# Find headers/body separator
header_end = body.find(b"\r\n\r\n")
if header_end == -1:
    header_end = body.find(b"\n\n")
# Body starts after the separator
body_start = header_end + (4 if body[header_end:header_end+4] == b"\r\n\r\n" else 2)
value = body[body_start:]
```

For trailing boundary delimiters, use a `while` loop to strip all trailing `\r\n`/`\n` sequences (not just one):

```python
while value.endswith(b"\r\n") or value.endswith(b"\n"):
    if value.endswith(b"\r\n"):
        value = value[:-2]
    else:
        value = value[:-1]
```

## CI Fixes (3 rounds)

During CI, three issues were discovered and fixed:

| Round | Issue | Fix |
|-------|-------|-----|
| 1 | str+bytes concatenation in test | Use `b"..."` for all bytes parts |
| 2 | Only one trailing CRLF stripped | `if` → `while` loop |
| 3 | Python 3.13+ implicit bytes/f-string concat error in parens | Encode f-string header as bytes first, then concat with bytes |

## Test

Added `test_decode_preserves_newlines()` with three cases:
1. `\n` preserved in text content
2. `\r\n` preserved in text content
3. Binary data (`\x00`) preserved alongside `\n` and `\r\n`

## Key Insight

- `bytes.splitlines()` is destructive for binary data — never use it for bodies that may contain binary content
- Python 3.12+ changed f-string parsing; implicit concatenation of `f"..."` and `b"..."` inside parentheses causes `SyntaxError: cannot mix bytes and nonbytes literals`
- `encode_multipart` has an artifact where `hdrs.append(b"")` produces an extra `\r\n` after each value — this is a pre-existing behavior that tests account for

## Keywords

`bytes.splitlines()` `binary data` `multipart` `form data` `newline` `CRLF` `Python 3.13` `f-string` `implicit concatenation` `SyntaxError` `encode artifact` `while loop` `trailing delimiter`
