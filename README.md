## Export Ultralytics YOLO to ONNX

This repo keeps YOLO weights and exported ONNX artifacts in stable locations for reproducible reruns.

### Directory layout

- `models/`: downloaded `.pt` weights (example: `models/yolov8n.pt`)
- `exports/onnx/`: exported ONNX files (example: `exports/onnx/yolov8n_img640_static_opset13.onnx`)
- `tools/export_onnx.py`: CLI exporter

Supported model inputs:
- Ultralytics model ids (for current supported families), e.g. `yolov8n`, `yolo11n`, `yolo11n-seg`, `yolo11n-pose`, `yolo11n-cls`, `yolo11n-obb`
- Local model path, e.g. `./checkpoints/custom.pt` or `./configs/model.yaml`

### Install dependencies (uv)

```bash
uv add ultralytics onnx numpy loguru
```

### Export command

Default behavior is static input shape (`--no-dynamic`) with opset 13:

```bash
uv run yolo-export-onnx
```

Why default `opset=13`:
- It is generally a safer baseline for cross-runtime compatibility (TensorRT / OpenCV DNN / ONNX Runtime) than newer opsets that may not be fully supported in older deployments.

### CLI options

- `--model` (default: `yolov8n`, accepts Ultralytics model id or local path)
- `--imgsz` (default: `640`)
- `--dynamic` / `--no-dynamic` (default: static)
- `--opset` (default: `13`)
- `--device` (default: `cpu`)
- `--out-dir` (default: `exports/onnx`)
- `--force` (overwrite existing file)
- `--verbose` (more Ultralytics logs)

### Examples

Export `yolov8n` static 640:

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13
```

Export `yolov8s` static 960 and overwrite if same output name exists:

```bash
uv run yolo-export-onnx --model yolov8s --imgsz 960 --no-dynamic --opset 13 --force
```

Export dynamic shape ONNX:

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 640 --dynamic --opset 13
```

Export segmentation model (`yolo11n-seg`):

```bash
uv run yolo-export-onnx --model yolo11n-seg --imgsz 640 --no-dynamic --opset 13
```

Export pose model (`yolo11n-pose`):

```bash
uv run yolo-export-onnx --model yolo11n-pose --imgsz 640 --no-dynamic --opset 13
```

Custom output directory:

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 512 --out-dir exports/onnx --force
```

### Export result output

On success, the tool prints:

- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`

On failure:
- Error details are appended to `logs/export_onnx.log`
- CLI prints a short message that points to the log file

Model download behavior:
- If the source resolves to a `.pt` model and `models/<model_tag>.pt` exists, it is reused and not downloaded again.
- If a `.pt` model is downloaded by Ultralytics, the script persists it into `models/` for future reruns.
