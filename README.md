# Export Ultralytics YOLO to ONNX

[![Language: English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![語言：繁體中文](https://img.shields.io/badge/%E8%AA%9E%E8%A8%80-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-green)](./README.zh-TW.md)

> [!TIP]
> Prefer Traditional Chinese? See [`README.zh-TW.md`](./README.zh-TW.md).

Install a CLI, run one command, get an ONNX file.

## Quick start

Install with `uv`:

```bash
uv tool install .
```

Run the default example:

```bash
yolo-export-onnx --model yolov8n
```

You will get an ONNX file under:

```bash
./exports/onnx/yolov8n_img640_static_opset13.onnx
```

## Custom path example

```bash
wget -O ./checkpoints/yolov8n.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
```

Export that local file:

```bash
yolo-export-onnx \
  --model ./checkpoints/yolov8n.pt \
  --out-dir ./artifacts/onnx \
  --output-name yolov8n_local.onnx
```

This flow is useful when you want to:
- keep weights in your own project directory
- export from a downloaded or custom-trained `.pt`
- control the output filename directly

## What the tool accepts

- Ultralytics model ids such as `yolov8n`, `yolo11n`, `yolo11n-seg`, `yolo11n-pose`, `yolo11n-cls`, `yolo11n-obb`
- Local model paths such as `./checkpoints/custom.pt` or `./configs/model.yaml`

## Defaults

- `--model yolov8n`
- `--imgsz 640`
- `--no-dynamic`
- `--opset 13`
- `--device cpu`
- `--out-dir ./exports/onnx`

Why `opset=13` by default:
- It is usually a safer baseline for TensorRT, OpenCV DNN, and ONNX Runtime compatibility.

## CLI options

| Option | Default | Notes |
| --- | --- | --- |
| `--model` | `yolov8n` | Ultralytics model id or local path |
| `--imgsz` | `640` | Input image size |
| `--dynamic` / `--no-dynamic` | static | Dynamic or fixed shape |
| `--opset` | `13` | ONNX opset version |
| `--device` | `cpu` | Export device |
| `--out-dir` | `exports/onnx` | Relative to your current working directory |
| `--output-name` | - | Explicit ONNX filename |
| `--cache-dir` | user cache dir | Override downloaded weight cache |
| `--log-file` | - | Write persistent error logs |
| `--force` | `False` | Overwrite existing output |
| `--verbose` | `False` | More Ultralytics logs |

## Path behavior

- Output files go to `./exports/onnx/` by default, relative to where you run the command.
- Downloaded `.pt` weights are cached in the platform user cache directory.
- No log file is written unless you set `--log-file`.
- Local model paths include a short hash in generated names to avoid collisions.

## More examples

```bash
yolo-export-onnx --model yolov8s --imgsz 960 --force
```

```bash
yolo-export-onnx --model yolov8n --dynamic
```

```bash
yolo-export-onnx --model yolo11n-seg
```

```bash
yolo-export-onnx --model yolo11n-pose
```

## Output

Success prints:
- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`
- `Cache: <path>` when a cached `.pt` file is used or updated

On failure:
- the error summary is printed to stderr
- if `--log-file` is set, the same error is written there

## Download a pre-exported ONNX from this repo

```bash
wget -O model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```
