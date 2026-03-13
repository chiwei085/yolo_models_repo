import hashlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import onnx
import typer
from loguru import logger
from platformdirs import user_cache_dir
from ultralytics import YOLO

APP_NAME = "yolo-export-onnx"
app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=False,
)


@dataclass(slots=True)
class ModelSpec:
    load_ref: str
    model_key: str
    display_name: str
    cache_weights: bool
    cache_path: Path | None


@dataclass(slots=True)
class ExportOptions:
    model: str
    imgsz: int
    dynamic: bool
    opset: int
    device: str
    out_dir: Path
    output_name: str | None
    cache_dir: Path | None
    log_file: Path | None
    force: bool
    verbose: bool


def configure_logger(log_file: Path | None) -> None:
    logger.remove()
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_file, level="ERROR", backtrace=True, diagnose=False)


def fail(message: str, code: int = 1, log_file: Path | None = None) -> int:
    logger.error(message)
    print(f"ERROR: {message}", file=sys.stderr)
    if log_file is not None:
        print(f"Log: {log_file}", file=sys.stderr)
    return code


def sanitize_name(value: str) -> str:
    return (
        "".join(char if char.isalnum() or char in "._-" else "_" for char in value).strip("._-")
        or "model"
    )


def build_model_spec(model_arg: str, cache_dir: Path) -> ModelSpec:
    model_input = model_arg.strip()
    if not model_input:
        raise ValueError("invalid --model value")

    local = Path(model_input).expanduser()
    if local.exists():
        resolved = local.resolve()
        digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:8]
        base_name = sanitize_name(resolved.stem)
        model_key = f"{base_name}_{digest}"
        return ModelSpec(
            load_ref=str(resolved),
            model_key=model_key,
            display_name=str(resolved),
            cache_weights=False,
            cache_path=None,
        )

    suffix = Path(model_input).suffix.lower()
    normalized = model_input.removesuffix(".pt")
    model_key = sanitize_name(normalized)
    cache_weights = suffix in {"", ".pt"}
    cache_path = cache_dir / "weights" / f"{model_key}.pt"
    if cache_weights and cache_path.exists():
        return ModelSpec(
            load_ref=str(cache_path),
            model_key=model_key,
            display_name=model_input,
            cache_weights=cache_weights,
            cache_path=cache_path,
        )

    load_ref = model_input if suffix else f"{model_input}.pt"
    return ModelSpec(
        load_ref=load_ref,
        model_key=model_key,
        display_name=model_input,
        cache_weights=cache_weights,
        cache_path=cache_path if cache_weights else None,
    )


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


def resolve_cache_dir(cache_dir: Path | None) -> Path:
    if cache_dir is not None:
        return cache_dir.expanduser().resolve()
    return Path(user_cache_dir(APP_NAME)).resolve()


def resolve_output_dir(out_dir: Path) -> Path:
    expanded = out_dir.expanduser()
    return expanded.resolve() if expanded.is_absolute() else (Path.cwd() / expanded).resolve()


def build_output_path(options: ExportOptions, model_key: str, out_dir: Path) -> Path:
    if options.output_name:
        name = (
            options.output_name
            if options.output_name.endswith(".onnx")
            else f"{options.output_name}.onnx"
        )
        return out_dir / name

    dyn_tag = "dynamic" if options.dynamic else "static"
    return out_dir / f"{model_key}_img{options.imgsz}_{dyn_tag}_opset{options.opset}.onnx"


def maybe_cache_weights(yolo: YOLO, cache_path: Path | None) -> None:
    if cache_path is None:
        return

    ckpt_raw = getattr(yolo.model, "pt_path", None) or getattr(yolo, "ckpt_path", None)
    if not ckpt_raw:
        return

    ckpt = Path(str(ckpt_raw)).resolve()
    if not ckpt.exists():
        return

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if ckpt != cache_path:
        shutil.copy2(ckpt, cache_path)


def export_onnx(options: ExportOptions) -> int:
    log_file = options.log_file.expanduser().resolve() if options.log_file else None
    configure_logger(log_file)

    try:
        cache_dir = resolve_cache_dir(options.cache_dir)
        out_dir = resolve_output_dir(options.out_dir)
        model = build_model_spec(options.model, cache_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError) as exc:
        return fail(str(exc), code=2, log_file=log_file)

    target_onnx = build_output_path(options, model.model_key, out_dir)
    if target_onnx.exists() and not options.force:
        return fail(
            f"output already exists: {target_onnx} (use --force to overwrite)",
            code=2,
            log_file=log_file,
        )

    try:
        yolo = YOLO(model.load_ref)
        if model.cache_weights:
            maybe_cache_weights(yolo, model.cache_path)
        if target_onnx.exists() and options.force:
            target_onnx.unlink()
        exported = yolo.export(
            format="onnx",
            imgsz=options.imgsz,
            dynamic=options.dynamic,
            opset=options.opset,
            simplify=False,
            device=options.device,
            verbose=options.verbose,
        )
        exported_path = Path(str(exported)).resolve()
        if exported_path != target_onnx:
            shutil.move(str(exported_path), str(target_onnx))
        inputs, outputs = read_onnx_io(target_onnx)
    except OSError as exc:
        return fail(f"failed to finalize output {target_onnx}: {exc}", log_file=log_file)
    except Exception as exc:  # noqa: BLE001
        return fail(f"cannot export model '{model.display_name}': {exc}", log_file=log_file)

    size_mb = target_onnx.stat().st_size / (1024 * 1024)
    print(f"OK exported: {target_onnx}")
    print(f"Input: {'; '.join(inputs) if inputs else '<none>'}")
    print(f"Output: {'; '.join(outputs) if outputs else '<none>'}")
    print(f"Size: {size_mb:.2f} MB")
    if model.cache_path is not None and model.cache_path.exists():
        print(f"Cache: {model.cache_path}")
    return 0


@app.command()
def export(
    model: Annotated[
        str,
        typer.Option(help="Ultralytics model id or local path."),
    ] = "yolov8n",
    imgsz: Annotated[
        int,
        typer.Option(help="Input image size, e.g. 320/512/640/960/1280."),
    ] = 640,
    dynamic: Annotated[
        bool,
        typer.Option("--dynamic/--no-dynamic", help="Enable dynamic shape export."),
    ] = False,
    opset: Annotated[
        int,
        typer.Option(help="ONNX opset version."),
    ] = 13,
    device: Annotated[
        str,
        typer.Option(help="Export device, e.g. cpu or cuda:0."),
    ] = "cpu",
    out_dir: Annotated[
        Path,
        typer.Option(
            help=(
                "Output directory for ONNX files, relative to the current working "
                "directory when not absolute."
            )
        ),
    ] = Path("exports/onnx"),
    output_name: Annotated[
        str | None,
        typer.Option(help="Optional explicit ONNX filename; .onnx is appended when missing."),
    ] = None,
    cache_dir: Annotated[
        Path | None,
        typer.Option(help="Override the model cache directory."),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(help="Optional log file path for persistent error logs."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(help="Overwrite target ONNX if it exists."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(help="Enable verbose Ultralytics logs."),
    ] = False,
) -> None:
    options = ExportOptions(
        model=model,
        imgsz=imgsz,
        dynamic=dynamic,
        opset=opset,
        device=device,
        out_dir=out_dir,
        output_name=output_name,
        cache_dir=cache_dir,
        log_file=log_file,
        force=force,
        verbose=verbose,
    )
    raise typer.Exit(code=export_onnx(options))


def main() -> None:
    app(prog_name=APP_NAME)


if __name__ == "__main__":
    main()
