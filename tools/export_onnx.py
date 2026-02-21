import argparse
import re
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

import onnx
from loguru import logger
from ultralytics import YOLO


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export an Ultralytics YOLO model to ONNX.")
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n",
        help="Ultralytics model id or local path (default: %(default)s)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size, e.g. 320/512/640/960/1280 (default: %(default)s)",
    )
    parser.add_argument(
        "--dynamic",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable dynamic shape export (default: %(default)s)",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=13,
        help="ONNX opset version (default: %(default)s)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Export device, e.g. cpu or cuda:0 (default: %(default)s)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="exports/onnx",
        help="Output directory for ONNX files (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite target ONNX if it exists (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose Ultralytics logs (default: %(default)s)",
    )
    return parser


def setup_logger(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(log_file, level="ERROR", format="{time:YYYY-MM-DDTHH:mm:ssZ} | {message}")


def fail(message: str, log_file: Path, code: int = 1) -> int:
    logger.error(message)
    print(f"ERROR: export failed. See log: {log_file}", file=sys.stderr)
    return code


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Cannot locate repo root (missing pyproject.toml).")


def build_model_tag(model_arg: str) -> str:
    base = Path(model_arg).name or model_arg
    base = base.split("?", maxsplit=1)[0]
    for suffix in (".pt", ".yaml", ".yml"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._-") or "model"


def resolve_model_ref(model_arg: str, weights_path: Path) -> tuple[str, bool]:
    model_input = model_arg.strip()
    if not model_input:
        raise ValueError("invalid --model value")

    local = Path(model_input).expanduser()
    if local.exists():
        return str(local.resolve()), local.suffix.lower() == ".pt"
    if weights_path.exists():
        return str(weights_path), True

    suffix = Path(model_input).suffix.lower()
    return (model_input, suffix == ".pt") if suffix else (f"{model_input}.pt", True)


def onnx_tensor_shape(info: onnx.ValueInfoProto) -> str:
    tensor = info.type.tensor_type
    if not tensor.HasField("shape"):
        return "<no shape>"

    dims: list[str] = []
    for dim in tensor.shape.dim:
        if dim.HasField("dim_value"):
            dims.append(str(dim.dim_value))
        elif dim.HasField("dim_param") and dim.dim_param:
            dims.append(dim.dim_param)
        else:
            dims.append("?")
    return "x".join(dims) if dims else "<scalar>"


def read_onnx_io(path: Path) -> tuple[list[str], list[str]]:
    graph = onnx.load(str(path)).graph
    inputs = [f"{item.name}: {onnx_tensor_shape(item)}" for item in graph.input]
    outputs = [f"{item.name}: {onnx_tensor_shape(item)}" for item in graph.output]
    return inputs, outputs


def export_onnx(args: argparse.Namespace) -> int:
    log_file = Path(__file__).resolve().parents[1] / "logs" / "export_onnx.log"
    setup_logger(log_file)

    try:
        repo_root = find_repo_root(Path(__file__).resolve().parent)
    except RuntimeError as exc:
        return fail(str(exc), log_file=log_file)

    model_tag = build_model_tag(args.model)
    models_dir = repo_root / "models"
    out_dir = Path(args.out_dir) if Path(args.out_dir).is_absolute() else repo_root / args.out_dir
    weights_path = models_dir / f"{model_tag}.pt"
    dyn_tag = "dynamic" if args.dynamic else "static"
    target_onnx = out_dir / f"{model_tag}_img{args.imgsz}_{dyn_tag}_opset{args.opset}.onnx"

    try:
        models_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return fail(f"cannot create output directories: {exc}", log_file=log_file)

    if target_onnx.exists() and not args.force:
        return fail(
            f"output already exists: {target_onnx}\nUse --force to overwrite.",
            log_file=log_file,
            code=2,
        )

    try:
        model_ref, cache_weights = resolve_model_ref(args.model, weights_path)
        yolo = YOLO(model_ref)
    except ValueError as exc:
        return fail(str(exc), log_file=log_file, code=2)
    except Exception as exc:  # noqa: BLE001
        return fail(f"cannot load model '{args.model}': {exc}", log_file=log_file)

    try:
        if cache_weights:
            ckpt_raw = getattr(yolo.model, "pt_path", None) or getattr(yolo, "ckpt_path", None)
            if ckpt_raw:
                ckpt = Path(str(ckpt_raw)).resolve()
                if ckpt.exists() and ckpt != weights_path:
                    shutil.copy2(ckpt, weights_path)
        if target_onnx.exists() and args.force:
            target_onnx.unlink()
    except OSError as exc:
        return fail(f"failed to prepare files: {exc}", log_file=log_file)

    try:
        exported = yolo.export(
            format="onnx",
            imgsz=args.imgsz,
            dynamic=args.dynamic,
            opset=args.opset,
            simplify=False,
            device=args.device,
            verbose=args.verbose,
        )
        exported_path = Path(str(exported)).resolve()
        if exported_path != target_onnx:
            shutil.move(str(exported_path), str(target_onnx))
        inputs, outputs = read_onnx_io(target_onnx)
    except OSError as exc:
        return fail(f"failed to finalize output {target_onnx}: {exc}", log_file=log_file)
    except Exception as exc:  # noqa: BLE001
        return fail(f"export failed or ONNX unreadable: {exc}", log_file=log_file)

    size_mb = target_onnx.stat().st_size / (1024 * 1024)
    print(f"OK exported: {target_onnx}")
    print(f"Input: {'; '.join(inputs) if inputs else '<none>'}")
    print(f"Output: {'; '.join(outputs) if outputs else '<none>'}")
    print(f"Size: {size_mb:.2f} MB")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return export_onnx(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
