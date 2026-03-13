# 匯出 Ultralytics YOLO 為 ONNX

[![Language: English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![語言：繁體中文](https://img.shields.io/badge/%E8%AA%9E%E8%A8%80-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-green)](./README.zh-TW.md)

> [!TIP]
> 想看英文版？請參考 [`README.md`](./README.md)。

這個 repo 提供可安裝的 CLI，用來把 Ultralytics YOLO 匯出成 ONNX，並保留少量已提交的範例產物。

支援的模型輸入：
- Ultralytics 模型 ID（目前支援家族），例如：`yolov8n`、`yolo11n`、`yolo11n-seg`、`yolo11n-pose`、`yolo11n-cls`、`yolo11n-obb`
- 本地模型路徑，例如：`./checkpoints/custom.pt` 或 `./configs/model.yaml`

## 安裝

使用 `uv`：

```bash
uv tool install .
```

或使用 `pip`：

```bash
pip install .
```

## 匯出指令

預設為固定輸入尺寸（`--no-dynamic`）且 `opset=13`：

```bash
yolo-export-onnx
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
yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13 --device cpu
```

原因：
- 固定 shape 通常更利於 TensorRT / OpenCV 整合穩定性。
- 也更容易做一致、公平的效能比較。

## 直接下載已匯出的 ONNX

此 repo 已公開，可直接透過 `raw` 連結下載匯出檔案。  
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
| `--out-dir` | `exports/onnx` | 輸出目錄；若為相對路徑，會以目前工作目錄為基準 |
| `--output-name` | - | 明確指定 ONNX 檔名 |
| `--cache-dir` | - | 覆寫下載權重使用的快取目錄 |
| `--log-file` | - | 指定持久化錯誤 log 檔案 |
| `--force` | - | 若檔案存在則覆蓋 |
| `--verbose` | - | 顯示更多 Ultralytics 日誌 |

## 路徑行為

- 預設輸出目錄：執行指令當下工作目錄下的 `./exports/onnx/`
- 預設快取目錄：平台使用者快取目錄，例如 Linux 上通常是 `~/.cache/yolo-export-onnx/weights/`
- 預設不寫 log 檔；除非額外指定 `--log-file`

若輸入是本地模型路徑，輸出檔名會包含一段短 hash，避免不同資料夾裡同名模型互相撞名。

## 使用範例

匯出 `yolov8n`，固定 640：

```bash
yolo-export-onnx --model yolov8n --imgsz 640 --no-dynamic --opset 13
```

匯出 `yolov8s`，固定 960，若同名輸出已存在則覆蓋：

```bash
yolo-export-onnx --model yolov8s --imgsz 960 --no-dynamic --opset 13 --force
```

匯出動態 shape ONNX：

```bash
yolo-export-onnx --model yolov8n --imgsz 640 --dynamic --opset 13
```

匯出分割模型（`yolo11n-seg`）：

```bash
yolo-export-onnx --model yolo11n-seg --imgsz 640 --no-dynamic --opset 13
```

匯出姿態模型（`yolo11n-pose`）：

```bash
yolo-export-onnx --model yolo11n-pose --imgsz 640 --no-dynamic --opset 13
```

自訂輸出目錄：

```bash
yolo-export-onnx --model yolov8n --imgsz 512 --out-dir ./artifacts/onnx --force
```

指定輸出檔名與 log 檔：

```bash
yolo-export-onnx --model ./checkpoints/custom.pt --output-name detector.onnx --log-file ./logs/export.log
```

## 匯出結果輸出

成功時工具會輸出：

- `OK exported: <path>`
- `Input: <name:shape>`
- `Output: <name:shape>`
- `Size: <MB>`
- 若有使用或更新快取權重，會額外輸出 `Cache: <path>`

失敗時：
- CLI 會直接把錯誤摘要輸出到 stderr
- 若有指定 `--log-file`，同一份錯誤也會寫入該檔案

模型下載行為：
- 下載得到的 `.pt` 權重會快取到使用者快取目錄；若有指定 `--cache-dir` 則改用該路徑。
- 本地模型路徑會直接使用，不會複製進快取。
