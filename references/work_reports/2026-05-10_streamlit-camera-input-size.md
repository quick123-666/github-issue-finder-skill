# Streamlit `st.camera_input` Size Parameter

- **Repo:** streamlit/streamlit
- **Issue:** [#4320](https://github.com/streamlit/streamlit/issues/4320)
- **PR:** [#15109](https://github.com/streamlit/streamlit/pull/15109)
- **Date:** 2026-05-10

## Problem

`st.camera_input` always returns images at whatever resolution the browser's camera sensor decides, often matching the widget's CSS dimensions rather than a consistent capture resolution. Users get unpredictable image sizes.

## Root Cause

The camera input widget used `{ ideal: debouncedWidth }` as the only `getUserMedia` video constraint. There was no way for users to specify a desired capture resolution. The frontend component had no mechanism to receive and apply resolution constraints from the Python layer.

## Fix

Three-layer change spanning proto, Python, and frontend:

1. **Proto** (`CameraInput.proto`): Added `uint32 camera_width = 7` and `uint32 camera_height = 8` to the `CameraInput` message.

2. **Python** (`camera_input.py`): Added `size: tuple[int, int] | None = None` parameter to both `camera_input()` and `_camera_input()`. When set, populates the proto fields.

3. **Frontend** (`WebcamComponent.tsx`): Added `cameraWidth`/`cameraHeight` props. When non-zero (indicating user-specified size), passed as `{ exact: cameraWidth }` constraints to `getUserMedia`. When zero (default), falls back to `{ ideal: debouncedWidth }` for backward compatibility.

4. **Frontend** (`CameraInput.tsx`): Forwarded `element.cameraWidth`/`element.cameraHeight` from the deserialized proto to `WebcamComponent`.

### Key snippets

```python
# Python API
def camera_input(
    ...,
    size: tuple[int, int] | None = None,
) -> UploadedFile | None:
```

```python
# Proto field population
if size is not None:
    camera_input_proto.camera_width = size[0]
    camera_input_proto.camera_height = size[1]
```

```typescript
// getUSerMedia constraint
videoConstraints={{
  width: cameraWidth ? { exact: cameraWidth } : { ideal: debouncedWidth },
  height: cameraHeight ? { exact: cameraHeight } : undefined,
  facingMode,
}}
```

## Key Insight

When adding a feature that spans proto → Python → frontend in Streamlit:

- **Proto:** Add fields to the existing message. Use `uint32` (defaults to 0) since `optional` proto3 syntax is not used in this codebase.
- **Python:** Add the parameter to BOTH the public function AND the internal `_camera_input()` function. Pass it through the call chain.
- **Frontend:** The proto's property names follow snake_case (e.g. `camera_width`), but TypeScript accesses them as camelCase (`element.cameraWidth`) because the protobuf JS compiler auto-converts.
- **Defaults:** Zero values in proto fields mean "not specified" (uint32 default). Frontend treats `0` as falsy to preserve backward compatibility.
- **Test plan:** Add both a Python unit test (checking proto field values) and a typing test (`camera_input_types.py`). No E2E test needed since camera access requires real hardware.
