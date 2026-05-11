# WireGuard Port Conflict Error Message Improvement

- **Repo:** mitmproxy/mitmproxy
- **Issue:** [#7650](https://github.com/mitmproxy/mitmproxy/issues/7650) — Better error message for WireGuard port conflict
- **PR:** [#8222](https://github.com/mitmproxy/mitmproxy/pull/8222)
- **Date:** 2026-05-10

## Problem

Running two mitmproxy instances in WireGuard mode simultaneously gives a confusing raw Rust error:

```
Address already in use (os error 48)
Error logged during startup, exiting...
```

The web UI port conflict produces a nice message with suggestions:

```
Web server failed to listen on 127.0.0.1:8081 with [Errno 48] Address already in use
Try specifying a different port by using `--set web_port=8083`.
```

## Root Cause

`mitmproxy_rs.wireguard.start_wireguard_server()` (Rust binding) raises `RuntimeError` instead of `OSError`. The existing error handler in `AsyncioServerInstance._start()` only catches `OSError`, so the WireGuard error bypasses it entirely, never producing the helpful suggestion.

## Fix

**File:** `mitmproxy/proxy/mode_servers.py`

Wrap the Rust `start_wireguard_server()` call in `try/except RuntimeError` and convert "Address already in use" errors to `OSError(errno.EADDRINUSE)`:

```python
async def start_udp_based_server(self, host, port):
    try:
        return await mitmproxy_rs.wireguard.start_wireguard_server(...)
    except RuntimeError as e:
        if "Address already in use" in str(e):
            raise OSError(errno.EADDRINUSE, str(e)) from e
        raise
```

This lets the existing `_start()` handler produce:

```
WireGuard server failed to listen on 0.0.0.0:51820 with Address already in use (os error 98)
Try specifying a different port by using `--mode wireguard@51822`.
```

**Test:** Mock `start_wireguard_server` to raise `RuntimeError`, verify it's converted to `OSError` with `errno.EADDRINUSE` and the helpful message.

## Key Insight

Rust libraries via `mitmproxy_rs` raise `RuntimeError` instead of `OSError`. Always check the error type when handling network errors from Rust bindings, and convert to `OSError` with proper `errno` so existing Python error handlers work.

## Keywords

`RuntimeError` `OSError` `EADDRINUSE` `Rust binding` `mitmproxy_rs` `PyO3` `error conversion` `WireGuard` `UDP` `error message` `cross-platform errno`
