"""Generate minimal binary voxel RVEs for the TBC QSGS comparison project.

The output is a canonical binary RVE:
    rve_zyx[z, y, x], uint8, 0 = pore, 1 = solid.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from scipy.ndimage import gaussian_filter

from rve_io import (
    PHASE_CONVENTION,
    SCHEMA_VERSION,
    phase_counts,
    porosity,
    read_json,
    save_rve_case,
    utc_now_iso,
    validate_binary_rve,
    write_json,
)


def require_len3(name: str, values: Any, cast: type = float) -> list[Any]:
    if not isinstance(values, list | tuple) or len(values) != 3:
        raise ValueError(f"{name} must be a 3-item list")
    return [cast(value) for value in values]


def merge_case(defaults: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(case)
    parameters = dict(defaults.get("parameters", {}))
    parameters.update(case.get("parameters", {}))
    merged["parameters"] = parameters
    return merged


def exact_lowest_mask(values: np.ndarray, fraction: float) -> np.ndarray:
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"target porosity must be in [0, 1], got {fraction}")

    flat = values.ravel()
    selected_count = int(round(fraction * flat.size))
    mask = np.zeros(flat.size, dtype=bool)
    if selected_count <= 0:
        return mask.reshape(values.shape)
    if selected_count >= flat.size:
        mask[:] = True
        return mask.reshape(values.shape)

    selected = np.argpartition(flat, selected_count - 1)[:selected_count]
    mask[selected] = True
    return mask.reshape(values.shape)


def build_simple_random(
    rng: np.random.Generator,
    shape_zyx: tuple[int, int, int],
    target_porosity: float,
) -> np.ndarray:
    noise = rng.random(shape_zyx)
    pore_mask = exact_lowest_mask(noise, target_porosity)
    rve = np.ones(shape_zyx, dtype=np.uint8)
    rve[pore_mask] = 0
    return rve


def build_anisotropic_correlated(
    rng: np.random.Generator,
    shape_zyx: tuple[int, int, int],
    voxel_size_um_xyz: list[float],
    target_porosity: float,
    parameters: dict[str, Any],
) -> np.ndarray:
    correlation_um_xyz = require_len3(
        "parameters.correlation_length_um_xyz",
        parameters["correlation_length_um_xyz"],
        float,
    )
    boundary_mode = parameters.get("boundary_mode", "periodic_wrap")
    if boundary_mode != "periodic_wrap":
        raise ValueError("Only boundary_mode='periodic_wrap' is supported in the minimal generator")

    sigma_xyz = [
        max(correlation_um_xyz[i] / voxel_size_um_xyz[i], 0.0)
        for i in range(3)
    ]
    sigma_zyx = (sigma_xyz[2], sigma_xyz[1], sigma_xyz[0])

    noise = rng.normal(loc=0.0, scale=1.0, size=shape_zyx)
    field = gaussian_filter(noise, sigma=sigma_zyx, mode="wrap")
    pore_mask = exact_lowest_mask(field, target_porosity)

    rve = np.ones(shape_zyx, dtype=np.uint8)
    rve[pore_mask] = 0
    return rve


def render_slice_preview(
    rve_zyx: np.ndarray,
    geometry: dict[str, Any],
    title: str,
    path: Path,
) -> Path:
    nz, ny, nx = rve_zyx.shape
    size_x, size_y, size_z = geometry["rve_size_um_xyz"]

    xy = rve_zyx[nz // 2, :, :]
    xz = rve_zyx[:, ny // 2, :]
    yz = rve_zyx[:, :, nx // 2]

    cmap = ListedColormap(["#111111", "#e8dfc7"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), constrained_layout=False)

    axes[0].imshow(
        xy,
        origin="lower",
        cmap=cmap,
        vmin=0,
        vmax=1,
        extent=[0, size_x, 0, size_y],
        interpolation="nearest",
    )
    axes[0].set_title("X-Y mid slice")
    axes[0].set_xlabel("x (um)")
    axes[0].set_ylabel("y (um)")

    axes[1].imshow(
        xz,
        origin="lower",
        cmap=cmap,
        vmin=0,
        vmax=1,
        extent=[0, size_x, 0, size_z],
        interpolation="nearest",
    )
    axes[1].set_title("X-Z mid slice")
    axes[1].set_xlabel("x (um)")
    axes[1].set_ylabel("z (um)")

    axes[2].imshow(
        yz,
        origin="lower",
        cmap=cmap,
        vmin=0,
        vmax=1,
        extent=[0, size_y, 0, size_z],
        interpolation="nearest",
    )
    axes[2].set_title("Y-Z mid slice")
    axes[2].set_xlabel("y (um)")
    axes[2].set_ylabel("z (um)")

    for ax in axes:
        ax.set_aspect("equal")

    handles = [
        plt.Line2D([0], [0], color="#111111", lw=7, label="0: pore"),
        plt.Line2D([0], [0], color="#e8dfc7", lw=7, label="1: solid 8YSZ"),
    ]
    fig.suptitle(title)
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.02))
    fig.subplots_adjust(left=0.055, right=0.985, top=0.82, bottom=0.24, wspace=0.28)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def build_case_metadata(
    case: dict[str, Any],
    config_path: Path,
    array_path: Path,
    metadata_path: Path,
    figure_path: Path | None,
    rve_zyx: np.ndarray,
    runtime_seconds: float,
) -> dict[str, Any]:
    counts = phase_counts(rve_zyx)
    actual_porosity = porosity(rve_zyx)
    target_porosity = float(case["target_porosity"])

    nx, ny, nz = require_len3("grid_shape_xyz", case["grid_shape_xyz"], int)
    size_x, size_y, size_z = require_len3("rve_size_um_xyz", case["rve_size_um_xyz"], float)
    voxel_size_um_xyz = [size_x / nx, size_y / ny, size_z / nz]

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case["case_id"],
        "method": case["method"],
        "generated_at_utc": utc_now_iso(),
        "config_path": str(config_path.as_posix()),
        "array_path": str(array_path.as_posix()),
        "metadata_path": str(metadata_path.as_posix()),
        "figure_paths": [str(figure_path.as_posix())] if figure_path else [],
        "phase_convention": PHASE_CONVENTION,
        "array": {
            "name": "rve_zyx",
            "axis_order": "zyx",
            "shape_zyx": [int(nz), int(ny), int(nx)],
            "dtype": "uint8",
        },
        "geometry": {
            "rve_size_um_xyz": [size_x, size_y, size_z],
            "grid_shape_xyz": [int(nx), int(ny), int(nz)],
            "voxel_size_um_xyz": voxel_size_um_xyz,
            "length_unit": "um",
        },
        "porosity": {
            "target": target_porosity,
            "actual": actual_porosity,
            "absolute_error": abs(actual_porosity - target_porosity),
            "pore_voxels": counts["0"],
            "solid_voxels": counts["1"],
        },
        "random": {
            "seed": int(case["seed"]),
            "deterministic_given_seed": True,
        },
        "generation_parameters": case.get("parameters", {}),
        "runtime_seconds": runtime_seconds,
        "validation": {
            "binary_values": [0, 1],
            "shape_matches_config": list(rve_zyx.shape) == [int(nz), int(ny), int(nx)],
            "actual_porosity_matches_requested_count": True,
        },
        "known_limitations": [
            "This is a synthetic binary voxel RVE, not yet validated against SEM/CT data.",
            "The current output is for morphology and later homogenization input; it does not compute AHM results.",
        ],
    }
    return metadata


def generate_case(config_path: Path, config: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()

    nx, ny, nz = require_len3("grid_shape_xyz", case["grid_shape_xyz"], int)
    rve_size_um_xyz = require_len3("rve_size_um_xyz", case["rve_size_um_xyz"], float)
    voxel_size_um_xyz = [
        rve_size_um_xyz[0] / nx,
        rve_size_um_xyz[1] / ny,
        rve_size_um_xyz[2] / nz,
    ]
    shape_zyx = (int(nz), int(ny), int(nx))
    target_porosity = float(case["target_porosity"])
    rng = np.random.default_rng(int(case["seed"]))

    method = case["method"]
    if method == "simple_random":
        rve_zyx = build_simple_random(rng, shape_zyx, target_porosity)
    elif method == "anisotropic_correlated":
        rve_zyx = build_anisotropic_correlated(
            rng,
            shape_zyx,
            voxel_size_um_xyz,
            target_porosity,
            case.get("parameters", {}),
        )
    else:
        raise ValueError(f"Unsupported method: {method}")

    validate_binary_rve(rve_zyx)

    outputs = config["outputs"]
    case_id = case["case_id"]
    method_dir = method
    array_path = Path(outputs["array_dir"]) / method_dir / f"{case_id}.npz"
    metadata_path = Path(outputs["metadata_dir"]) / method_dir / f"{case_id}_metadata.json"
    figure_path = Path(outputs["figure_dir"]) / method_dir / f"{case_id}_slices.png"

    runtime_seconds = time.perf_counter() - started
    geometry = {
        "rve_size_um_xyz": rve_size_um_xyz,
        "grid_shape_xyz": [nx, ny, nz],
        "voxel_size_um_xyz": voxel_size_um_xyz,
    }
    render_slice_preview(
        rve_zyx,
        geometry,
        title=f"{case_id} ({method}, porosity={porosity(rve_zyx):.4f})",
        path=figure_path,
    )

    metadata = build_case_metadata(
        case=case,
        config_path=config_path,
        array_path=array_path,
        metadata_path=metadata_path,
        figure_path=figure_path,
        rve_zyx=rve_zyx,
        runtime_seconds=runtime_seconds,
    )
    save_rve_case(rve_zyx, metadata, array_path, metadata_path)
    return metadata


def write_batch_summary(config: dict[str, Any], records: list[dict[str, Any]]) -> None:
    log_dir = Path(config["outputs"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    batch_id = config["batch_id"]

    write_json(log_dir / f"{batch_id}_summary.json", {"batch_id": batch_id, "cases": records})

    csv_path = log_dir / f"{batch_id}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "method",
                "seed",
                "target_porosity",
                "actual_porosity",
                "grid_shape_xyz",
                "rve_size_um_xyz",
                "runtime_seconds",
                "array_path",
                "metadata_path",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "case_id": record["case_id"],
                    "method": record["method"],
                    "seed": record["random"]["seed"],
                    "target_porosity": record["porosity"]["target"],
                    "actual_porosity": record["porosity"]["actual"],
                    "grid_shape_xyz": record["geometry"]["grid_shape_xyz"],
                    "rve_size_um_xyz": record["geometry"]["rve_size_um_xyz"],
                    "runtime_seconds": f"{record['runtime_seconds']:.6f}",
                    "array_path": record["array_path"],
                    "metadata_path": record["metadata_path"],
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/voxel_rve_minimal_v1.json",
        help="Path to the voxel RVE generation config.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Optional case_id to run. Repeat this option to run multiple cases.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = read_json(config_path)
    defaults = config.get("defaults", {})
    requested = set(args.case_id)

    records: list[dict[str, Any]] = []
    for raw_case in config["cases"]:
        if requested and raw_case["case_id"] not in requested:
            continue
        case = merge_case(defaults, raw_case)
        records.append(generate_case(config_path, config, case))

    if not records:
        raise ValueError("No cases were generated. Check --case-id or config.cases.")

    write_batch_summary(config, records)

    for record in records:
        print(
            f"{record['case_id']}: method={record['method']}, "
            f"porosity={record['porosity']['actual']:.6f}, "
            f"array={record['array_path']}"
        )


if __name__ == "__main__":
    main()
