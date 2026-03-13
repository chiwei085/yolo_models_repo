# 匯出 Ultralytics YOLO 為 ONNX

[![Language: English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![語言：繁體中文](https://img.shields.io/badge/%E8%AA%9E%E8%A8%80-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-green)](./README.zh-TW.md)

> [!TIP]
> 想看英文版？請參考 [`README.md`](./README.md)。

先安裝 CLI，再跑一條指令拿到 ONNX。

## 快速開始

先用 `uv` 安裝：

```bash
uv tool install .
```

先跑最短範例：

```bash
yolo-export-onnx --model yolov8n
```

你會在這裡拿到輸出：

```bash
./exports/onnx/yolov8n_img640_static_opset13.onnx
```

## 自訂路徑範例

先把 `yolov8n.pt` 下載到你自己的資料夾：

```bash
wget -O ./checkpoints/yolov8n.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
```

再從本地路徑匯出：

```bash
yolo-export-onnx \
  --model ./checkpoints/yolov8n.pt \
  --out-dir ./artifacts/onnx \
  --output-name yolov8n_local.onnx
```

這種用法適合：
- 權重想放在自己的專案目錄
- 要匯出下載好的或自行訓練的 `.pt`
- 想自己控制輸出檔名

## 支援的輸入

- Ultralytics 模型 ID，例如 `yolov8n`、`yolo11n`、`yolo11n-seg`、`yolo11n-pose`、`yolo11n-cls`、`yolo11n-obb`
- 本地模型路徑，例如 `./checkpoints/custom.pt` 或 `./configs/model.yaml`

## 預設值

- `--model yolov8n`
- `--imgsz 640`
- `--no-dynamic`
- `--opset 13`
- `--device cpu`
- `--out-dir ./exports/onnx`

為什麼預設 `opset=13`：
- 對 TensorRT、OpenCV DNN、ONNX Runtime 來說，通常是更穩妥的相容性基線。

## CLI 參數

| 參數 | 預設值 | 說明 |
| --- | --- | --- |
| `--model` | `yolov8n` | Ultralytics 模型 ID 或本地路徑 |
| `--imgsz` | `640` | 輸入尺寸 |
| `--dynamic` / `--no-dynamic` | static | 動態或固定 shape |
| `--opset` | `13` | ONNX opset 版本 |
| `--device` | `cpu` | 匯出使用裝置 |
| `--out-dir` | `exports/onnx` | 相對路徑會以目前工作目錄為基準 |
| `--output-name` | - | 明確指定 ONNX 檔名 |
| `--cache-dir` | 使用者快取目錄 | 覆寫下載權重快取位置 |
| `--log-file` | - | 寫入持久化錯誤 log |
| `--force` | `False` | 覆蓋既有輸出 |
| `--verbose` | `False` | 顯示更多 Ultralytics 日誌 |

## 路徑行為

- 輸出預設寫到你執行指令當下的 `./exports/onnx/`
- 下載的 `.pt` 權重會快取到平台使用者快取目錄
- 沒有指定 `--log-file` 就不會落地 log 檔
- 若輸入是本地模型路徑，產生的檔名會帶短 hash，避免同名撞檔

## 更多範例

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

## 輸出資訊

成功時會輸出：
- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`
- 如果有用到或更新快取 `.pt`，會額外印出 `Cache: <path>`

失敗時：
- 錯誤摘要直接輸出到 stderr
- 若有指定 `--log-file`，同一份內容也會寫進檔案

## 直接下載這個 repo 已匯出的 ONNX

```bash
wget -O model.onnx \
  "https://github.com/chiwei085/yolo_models_repo/raw/refs/heads/master/exports/onnx/yolov8n_img640_static_opset13.onnx"
```
