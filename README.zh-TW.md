# 匯出 Ultralytics YOLO 為 ONNX

[![Language: English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![語言：繁體中文](https://img.shields.io/badge/%E8%AA%9E%E8%A8%80-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-green)](./README.zh-TW.md)

> [!TIP]
> 想看英文版？請參考 [`README.md`](./README.md)。

此 repo 將 YOLO 權重與匯出的 ONNX 產物放在固定路徑，方便重現流程與重跑實驗。

## 目錄結構

- `models/`: 下載後的 `.pt` 權重（例如：`models/yolov8n.pt`）
- `exports/onnx/`: 匯出的 ONNX 檔案（例如：`exports/onnx/yolov8n_img640_static_opset13.onnx`）
- `tools/export_onnx.py`: CLI 匯出工具

支援的模型輸入：
- Ultralytics 模型 ID（目前支援家族），例如：`yolov8n`、`yolo11n`、`yolo11n-seg`、`yolo11n-pose`、`yolo11n-cls`、`yolo11n-obb`
- 本地模型路徑，例如：`./checkpoints/custom.pt` 或 `./configs/model.yaml`

## 安裝相依套件（uv）

```bash
uv add ultralytics onnx numpy loguru
```

## 匯出指令

預設為固定輸入尺寸（`--no-dynamic`）且 `opset=13`：

```bash
uv run yolo-export-onnx
```

為什麼預設 `opset=13`：
- 相比某些較新的 opset，在舊版部署環境中（TensorRT / OpenCV DNN / ONNX Runtime）通常有更好的跨 runtime 相容性。

## 建議預設組合

適用於 CPU / OpenCV DNN / ONNX Runtime 的一般用途：

- `imgsz=640`
- `--no-dynamic`
- `opset=13`
- `device=cpu`

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13 --device cpu
```

原因：
- 固定 shape 通常更利於 TensorRT / OpenCV 整合穩定性。
- 也更容易做一致、公平的效能比較。

## 直接下載已匯出的 ONNX

當此 repo 為 public 時，可直接透過 `raw` 連結下載匯出檔案。  
使用 `curl` 時建議加上 `-L` 以跟隨 redirect。

```bash
curl -L -o model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```

或使用 `wget`：

```bash
wget -O model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```

## CLI 參數

| 參數 | 預設值 | 說明 |
| --- | --- | --- |
| `--model` | `yolov8n` | 可用 Ultralytics 模型 ID 或本地路徑 |
| `--imgsz` | `640` | 輸入尺寸 |
| `--dynamic` / `--no-dynamic` | static | 動態或固定 shape |
| `--opset` | `13` | ONNX opset 版本 |
| `--device` | `cpu` | 匯出使用裝置 |
| `--out-dir` | `exports/onnx` | 輸出目錄 |
| `--force` | - | 若檔案存在則覆蓋 |
| `--verbose` | - | 顯示更多 Ultralytics 日誌 |

## 使用範例

匯出 `yolov8n`，固定 640：

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13
```

匯出 `yolov8s`，固定 960，若同名輸出已存在則覆蓋：

```bash
uv run yolo-export-onnx --model yolov8s --imgsz 960 --no-dynamic --opset 13 --force
```

匯出動態 shape ONNX：

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 640 --dynamic --opset 13
```

匯出分割模型（`yolo11n-seg`）：

```bash
uv run yolo-export-onnx --model yolo11n-seg --imgsz 640 --no-dynamic --opset 13
```

匯出姿態模型（`yolo11n-pose`）：

```bash
uv run yolo-export-onnx --model yolo11n-pose --imgsz 640 --no-dynamic --opset 13
```

自訂輸出目錄：

```bash
uv run yolo-export-onnx --model yolov8n --imgsz 512 --out-dir exports/onnx --force
```

## 匯出結果輸出

成功時工具會輸出：

- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`

失敗時：
- 錯誤細節會附加到 `logs/export_onnx.log`
- CLI 會輸出簡短訊息並提示查看 log

模型下載行為：
- 若來源解析為 `.pt` 且 `models/<model_tag>.pt` 已存在，會直接重用，不重複下載。
- 若 `.pt` 由 Ultralytics 下載，腳本會將其保存到 `models/` 供後續重跑使用。
