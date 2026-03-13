# Export Ultralytics YOLO to ONNX

[![Language: English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![語言：繁體中文](https://img.shields.io/badge/%E8%AA%9E%E8%A8%80-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-green)](./README.zh-TW.md)

> [!TIP]
> Prefer Traditional Chinese? See [`README.zh-TW.md`](./README.zh-TW.md).

This repo provides an installable CLI for exporting Ultralytics YOLO models to ONNX, plus a few checked-in example artifacts.

Supported model inputs:
- Ultralytics model ids (for current supported families), e.g. `yolov8n`, `yolo11n`, `yolo11n-seg`, `yolo11n-pose`, `yolo11n-cls`, `yolo11n-obb`
- Local model path, e.g. `./checkpoints/custom.pt` or `./configs/model.yaml`

### Install

With `uv`:

```bash
uv tool install .
```

Or with `pip`:

```bash
pip install .
```

### Export command

Default behavior is static input shape (`--no-dynamic`) with opset 13:

```bash
yolo-export-onnx
```

Why default `opset=13`:
- It is generally a safer baseline for cross-runtime compatibility (TensorRT / OpenCV DNN / ONNX Runtime) than newer opsets that may not be fully supported in older deployments.

### Recommended preset

For CPU / OpenCV DNN / ONNX Runtime general use:

- `imgsz=640`
- `--no-dynamic`
- `opset=13`
- `device=cpu`

```bash
yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13 --device cpu
```

Why:
- Fixed shape is usually more stable for TensorRT/OpenCV integration.
- It also makes performance comparisons easier and more consistent.

### Download an exported ONNX directly

This repository is public, so exported files can be downloaded directly from the `raw` URL.
Use `-L` with `curl` to follow redirects.

```bash
curl -L -o model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```

Or use `wget`:

```bash
wget -O model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```

### CLI options

- `--model` (default: `yolov8n`, accepts Ultralytics model id or local path)
- `--imgsz` (default: `640`)
- `--dynamic` / `--no-dynamic` (default: static)
- `--opset` (default: `13`)
- `--device` (default: `cpu`)
- `--out-dir` (default: `exports/onnx` relative to the current working directory)
- `--output-name` (explicit ONNX filename)
- `--cache-dir` (override the user cache directory used for downloaded weights)
- `--log-file` (optional persistent error log file)
- `--force` (overwrite existing file)
- `--verbose` (more Ultralytics logs)

### Path behavior

- Default output path: `./exports/onnx/` under the directory where you run the command
- Default cache path: platform user cache dir, e.g. `~/.cache/yolo-export-onnx/weights/` on Linux
- Default log file: none; errors are printed to stderr unless `--log-file` is provided

For local model paths, the generated filename includes a short path hash to avoid collisions between files with the same basename.

### Examples

Export `yolov8n` static 640:

```bash
yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13
```

Export `yolov8s` static 960 and overwrite if same output name exists:

```bash
yolo-export-onnx --model yolov8s --imgsz 960 --no-dynamic --opset 13 --force
```

Export dynamic shape ONNX:

```bash
yolo-export-onnx --model yolov8n --imgsz 640 --dynamic --opset 13
```

Export segmentation model (`yolo11n-seg`):

```bash
yolo-export-onnx --model yolo11n-seg --imgsz 640 --no-dynamic --opset 13
```

Export pose model (`yolo11n-pose`):

```bash
yolo-export-onnx --model yolo11n-pose --imgsz 640 --no-dynamic --opset 13
```

Custom output directory:

```bash
yolo-export-onnx --model yolov8n --imgsz 512 --out-dir ./artifacts/onnx --force
```

Explicit output name and log file:

```bash
yolo-export-onnx --model ./checkpoints/custom.pt --output-name detector.onnx --log-file ./logs/export.log
```

### Export result output

On success, the tool prints:

- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`
- `Cache: <path>` when a cached `.pt` weight file is used or updated

On failure:
- CLI prints the error summary to stderr
- If `--log-file` is set, the same error is also written there

Model download behavior:
- Downloaded `.pt` weights are cached in the user cache directory unless `--cache-dir` is provided.
- Local model paths are used directly and are not copied into the cache.
