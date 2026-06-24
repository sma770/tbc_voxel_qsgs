"""Generate a four-phase voxelized local TBC wedge-crack model.

The generated label volume is intended for geometry definition,
visual checks, and morphology calculations. Mechanical simulation should
use a continuous parametric geometry and an adaptive FE mesh.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


PHASE_NAMES = {
    0: "crack/air",
    1: "YSZ ceramic",
    2: "MCrAlY bond coat",
    3: "Inconel substrate",
}

PHASE_COLORS = {
    0: "#111111",
    1: "#f2f0df",
    2: "#b8b8b8",
    3: "#6d83a3",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def rounded_voxels(length_um: float, voxel_um: float, name: str) -> int:
    value = length_um / voxel_um
    rounded = int(round(value))
    if not math.isclose(value, rounded, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{name}={length_um} um is not an integer multiple of voxel_size={voxel_um} um")
    if rounded <= 0:
        raise ValueError(f"{name} must be positive")
    return rounded


def phase_cmap() -> tuple[ListedColormap, BoundaryNorm]:
    colors = [PHASE_COLORS[i] for i in range(4)]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    return cmap, norm


def centered_interval(total_voxels: int, width_voxels: int) -> slice:
    if width_voxels > total_voxels:
        raise ValueError(f"width_voxels={width_voxels} exceeds total_voxels={total_voxels}")
    start = (total_voxels - width_voxels) // 2
    return slice(start, start + width_voxels)


def count_phase_labels(labels: np.ndarray, max_label: int, chunk_z: int = 32) -> dict[str, int]:
    counts = np.zeros(max_label + 1, dtype=np.int64)
    for z0 in range(0, labels.shape[0], chunk_z):
        chunk = np.asarray(labels[z0 : z0 + chunk_z, :, :])
        counts += np.bincount(chunk.ravel(), minlength=max_label + 1)[: max_label + 1]
    return {str(label): int(count) for label, count in enumerate(counts) if count > 0}


def crack_width_voxels(
    depth_from_top_voxels: np.ndarray,
    crack_depth_voxels: int,
    top_width_voxels: int,
    bottom_width_voxels: int,
) -> np.ndarray:
    if crack_depth_voxels <= 1:
        return np.full_like(depth_from_top_voxels, bottom_width_voxels)

    t = depth_from_top_voxels / (crack_depth_voxels - 1)
    widths = top_width_voxels + (bottom_width_voxels - top_width_voxels) * t
    widths = np.rint(widths).astype(np.int32)
    return np.clip(widths, min(top_width_voxels, bottom_width_voxels), max(top_width_voxels, bottom_width_voxels))


def build_volume(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    model_id = config["model_id"]
    voxel_um = float(config["voxel_size_um"])

    nx = rounded_voxels(float(config["domain_um"]["x"]), voxel_um, "domain_um.x")
    ny = rounded_voxels(float(config["domain_um"]["y"]), voxel_um, "domain_um.y")
    nz = rounded_voxels(float(config["domain_um"]["z"]), voxel_um, "domain_um.z")

    layer_voxels: list[dict[str, Any]] = []
    z_cursor = 0
    for layer in config["layers"]:
        thickness_voxels = rounded_voxels(float(layer["thickness_um"]), voxel_um, layer["name"])
        layer_voxels.append(
            {
                "name": layer["name"],
                "phase": layer["phase"],
                "label": int(layer["label"]),
                "z_start": z_cursor,
                "z_stop": z_cursor + thickness_voxels,
                "thickness_voxels": thickness_voxels,
            }
        )
        z_cursor += thickness_voxels
    if z_cursor != nz:
        raise ValueError(f"Layer thickness sum {z_cursor} voxels does not match domain z {nz} voxels")

    crack_cfg = config["crack"]
    crack_label = int(crack_cfg["label"])
    crack_length_voxels = rounded_voxels(float(crack_cfg["length_um"]), voxel_um, "crack.length_um")
    top_width_voxels = rounded_voxels(float(crack_cfg["top_width_um"]), voxel_um, "crack.top_width_um")
    bottom_width_voxels = rounded_voxels(float(crack_cfg["bottom_width_um"]), voxel_um, "crack.bottom_width_um")
    crack_depth_voxels = rounded_voxels(float(crack_cfg["depth_um"]), voxel_um, "crack.depth_um")
    ceramic_ligament_voxels = rounded_voxels(
        float(crack_cfg["ceramic_ligament_to_bondcoat_um"]), voxel_um, "crack.ceramic_ligament_to_bondcoat_um"
    )

    x_slice = centered_interval(nx, crack_length_voxels)
    y_slices = {
        width: centered_interval(ny, width)
        for width in range(bottom_width_voxels, top_width_voxels + 1)
    }

    ysz_layer = next(layer for layer in layer_voxels if layer["phase"] == "ysz")
    bond_layer = next(layer for layer in layer_voxels if layer["phase"] == "mcraly")
    ceramic_top = ysz_layer["z_stop"]
    crack_z_start = ceramic_top - crack_depth_voxels
    crack_z_stop = ceramic_top
    if crack_z_start - bond_layer["z_stop"] != ceramic_ligament_voxels:
        raise ValueError("Crack depth and ceramic ligament do not match the configured ceramic layer thickness")

    array_dir = Path(config["outputs"]["array_dir"])
    array_dir.mkdir(parents=True, exist_ok=True)
    array_path = array_dir / f"{model_id}_labels_zyx_uint8.npy"
    labels = np.lib.format.open_memmap(array_path, mode="w+", dtype=np.uint8, shape=(nz, ny, nx))

    for layer in layer_voxels:
        labels[layer["z_start"] : layer["z_stop"], :, :] = np.uint8(layer["label"])

    depth_from_top = np.arange(crack_depth_voxels, dtype=np.int32)
    widths_by_depth = crack_width_voxels(depth_from_top, crack_depth_voxels, top_width_voxels, bottom_width_voxels)
    for local_idx, width in enumerate(widths_by_depth):
        z = crack_z_stop - 1 - local_idx
        labels[z, y_slices[int(width)], x_slice] = np.uint8(crack_label)

    labels.flush()

    max_phase_label = max(PHASE_NAMES)
    phase_counts = count_phase_labels(labels, max_phase_label)
    total_voxels = int(nx * ny * nz)
    phase_volume_fractions = {
        label: count / total_voxels for label, count in phase_counts.items()
    }

    included_angle_deg = math.degrees(
        2.0
        * math.atan(
            (float(crack_cfg["top_width_um"]) - float(crack_cfg["bottom_width_um"]))
            / (2.0 * float(crack_cfg["depth_um"]))
        )
    )

    geometry_checks = run_geometry_checks(
        labels_path=array_path,
        shape=(nz, ny, nx),
        phase_labels={int(k): v for k, v in PHASE_NAMES.items()},
        x_slice=x_slice,
        crack_z_start=crack_z_start,
        crack_z_stop=crack_z_stop,
        bond_z_stop=bond_layer["z_stop"],
        top_width_voxels=top_width_voxels,
        bottom_width_voxels=bottom_width_voxels,
        crack_depth_voxels=crack_depth_voxels,
        crack_label=crack_label,
    )

    metadata = {
        "model_id": model_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path.as_posix()),
        "array_path": str(array_path.as_posix()),
        "array_shape_zyx": [nz, ny, nx],
        "dtype": "uint8",
        "voxel_size_um": voxel_um,
        "domain_um_actual": {
            "x": nx * voxel_um,
            "y": ny * voxel_um,
            "z": nz * voxel_um,
        },
        "layer_voxels": layer_voxels,
        "phase_labels": PHASE_NAMES,
        "phase_counts": phase_counts,
        "phase_volume_fractions": phase_volume_fractions,
        "crack": {
            "x_voxel_range": [x_slice.start, x_slice.stop],
            "z_voxel_range": [crack_z_start, crack_z_stop],
            "length_voxels": crack_length_voxels,
            "top_width_voxels": top_width_voxels,
            "bottom_width_voxels": bottom_width_voxels,
            "depth_voxels": crack_depth_voxels,
            "included_angle_from_widths_deg": included_angle_deg,
            "sidewall_angle_from_vertical_deg": included_angle_deg / 2.0,
            "widths_by_depth_voxels_unique": sorted(int(x) for x in np.unique(widths_by_depth)),
        },
        "geometry_checks": geometry_checks,
        "runtime_seconds": time.perf_counter() - started,
        "reproducibility": {
            "random_seed": None,
            "deterministic": True,
            "generation_method": "parameterized geometric voxelization",
        },
        "mechanics_note": (
            "Use this voxel volume for structure definition and checks. For COMSOL mechanics, "
            "build the equivalent continuous parametric geometry and let COMSOL create an adaptive FE mesh."
        ),
    }

    metadata_path = Path(config["outputs"]["metadata_dir"]) / f"{model_id}_metadata.json"
    write_json(metadata_path, metadata)

    figure_paths = render_figures(config, metadata, array_path)
    metadata["figure_paths"] = [str(path.as_posix()) for path in figure_paths]
    write_json(metadata_path, metadata)

    log_path = Path(config["outputs"]["log_dir"]) / f"{model_id}_generation_summary.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(format_summary(metadata), encoding="utf-8")

    metadata["summary_log_path"] = str(log_path.as_posix())
    write_json(metadata_path, metadata)
    return metadata


def run_geometry_checks(
    labels_path: Path,
    shape: tuple[int, int, int],
    phase_labels: dict[int, str],
    x_slice: slice,
    crack_z_start: int,
    crack_z_stop: int,
    bond_z_stop: int,
    top_width_voxels: int,
    bottom_width_voxels: int,
    crack_depth_voxels: int,
    crack_label: int,
) -> dict[str, Any]:
    labels = np.load(labels_path, mmap_mode="r")
    nz, ny, nx = shape
    x_center = (x_slice.start + x_slice.stop) // 2

    top_z = crack_z_stop - 1
    bottom_z = crack_z_start
    top_width_actual = int(np.count_nonzero(labels[top_z, :, x_center] == crack_label))
    bottom_width_actual = int(np.count_nonzero(labels[bottom_z, :, x_center] == crack_label))
    depth_actual = int(np.count_nonzero(np.any(labels[:, :, x_center] == crack_label, axis=1)))
    length_top_actual = int(np.count_nonzero(labels[top_z, ny // 2, :] == crack_label))
    crack_below_ysz = int(np.count_nonzero(labels[:bond_z_stop, :, :] == crack_label))

    checks = {
        "top_width_voxels_expected": top_width_voxels,
        "top_width_voxels_actual": top_width_actual,
        "bottom_width_voxels_expected": bottom_width_voxels,
        "bottom_width_voxels_actual": bottom_width_actual,
        "depth_voxels_expected": crack_depth_voxels,
        "depth_voxels_actual": depth_actual,
        "length_voxels_expected": x_slice.stop - x_slice.start,
        "length_voxels_actual_at_top_centerline": length_top_actual,
        "crack_voxels_below_bondcoat_top_expected": 0,
        "crack_voxels_below_bondcoat_top_actual": crack_below_ysz,
    }
    checks["passed"] = all(
        [
            top_width_actual == top_width_voxels,
            bottom_width_actual == bottom_width_voxels,
            depth_actual == crack_depth_voxels,
            length_top_actual == x_slice.stop - x_slice.start,
            crack_below_ysz == 0,
            int(np.min(labels)) >= min(phase_labels),
            int(np.max(labels)) <= max(phase_labels),
            labels.shape == (nz, ny, nx),
        ]
    )
    return checks


def render_figures(config: dict[str, Any], metadata: dict[str, Any], array_path: Path) -> list[Path]:
    figure_dir = Path(config["outputs"]["figure_dir"])
    figure_dir.mkdir(parents=True, exist_ok=True)
    model_id = config["model_id"]

    labels = np.load(array_path, mmap_mode="r")
    nz, ny, nx = labels.shape
    voxel_um = float(config["voxel_size_um"])
    cmap, norm = phase_cmap()

    paths: list[Path] = []
    paths.append(render_sections(labels, voxel_um, figure_dir / f"{model_id}_sections.png", cmap, norm))
    paths.append(render_geometry_preview(config, metadata, figure_dir / f"{model_id}_geometry_preview.png"))
    return paths


def render_sections(
    labels: np.ndarray,
    voxel_um: float,
    path: Path,
    cmap: ListedColormap,
    norm: BoundaryNorm,
) -> Path:
    nz, ny, nx = labels.shape
    x_center = nx // 2
    y_center = ny // 2
    z_top = nz - 1

    yz = labels[:, :, x_center]
    xy_top = labels[z_top, :, :]
    xz = labels[:, y_center, :]

    fig, axes = plt.subplots(3, 1, figsize=(12, 12), constrained_layout=True)

    axes[0].imshow(
        yz,
        origin="lower",
        cmap=cmap,
        norm=norm,
        extent=[-ny * voxel_um / 2, ny * voxel_um / 2, 0, nz * voxel_um],
        aspect="equal",
        interpolation="nearest",
    )
    axes[0].set_title("Y-Z cross-section at crack center (equal scale)")
    axes[0].set_xlabel("y (um)")
    axes[0].set_ylabel("z (um)")

    axes[1].imshow(
        xy_top,
        origin="lower",
        cmap=cmap,
        norm=norm,
        extent=[0, nx * voxel_um, -ny * voxel_um / 2, ny * voxel_um / 2],
        aspect="equal",
        interpolation="nearest",
    )
    axes[1].set_title("X-Y top surface view (equal scale)")
    axes[1].set_xlabel("x (um)")
    axes[1].set_ylabel("y (um)")

    axes[2].imshow(
        xz,
        origin="lower",
        cmap=cmap,
        norm=norm,
        extent=[0, nx * voxel_um, 0, nz * voxel_um],
        aspect="equal",
        interpolation="nearest",
    )
    axes[2].set_title("X-Z longitudinal section at crack centerline (equal scale)")
    axes[2].set_xlabel("x (um)")
    axes[2].set_ylabel("z (um)")

    handles = [
        plt.Line2D([0], [0], color=PHASE_COLORS[label], lw=8, label=f"{label}: {name}")
        for label, name in PHASE_NAMES.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4)
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def cuboid_faces(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> list[list[tuple[float, float, float]]]:
    return [
        [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    ]


def render_geometry_preview(config: dict[str, Any], metadata: dict[str, Any], path: Path) -> Path:
    domain = metadata["domain_um_actual"]
    crack = config["crack"]
    x_len = domain["x"]
    y_len = domain["y"]

    z0 = 0.0
    substrate_top = float(config["layers"][0]["thickness_um"])
    bond_top = substrate_top + float(config["layers"][1]["thickness_um"])
    ceramic_top = bond_top + float(config["layers"][2]["thickness_um"])

    crack_length = float(crack["length_um"])
    x0 = (x_len - crack_length) / 2
    x1 = x0 + crack_length
    top_half = float(crack["top_width_um"]) / 2
    bottom_half = float(crack["bottom_width_um"]) / 2
    crack_depth = float(crack["depth_um"])
    crack_bottom = ceramic_top - crack_depth

    fig = plt.figure(figsize=(12, 8), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")

    layer_specs = [
        (0.0, substrate_top, PHASE_COLORS[3], "Inconel substrate"),
        (substrate_top, bond_top, PHASE_COLORS[2], "MCrAlY bond coat"),
        (bond_top, ceramic_top, PHASE_COLORS[1], "YSZ ceramic"),
    ]
    for lo, hi, color, label in layer_specs:
        faces = cuboid_faces(0, x_len, -y_len / 2, y_len / 2, lo, hi)
        poly = Poly3DCollection(faces, facecolors=color, edgecolors="#505050", linewidths=0.25, alpha=0.16)
        poly.set_label(label)
        ax.add_collection3d(poly)

    crack_vertices = [
        (x0, -top_half, ceramic_top),
        (x1, -top_half, ceramic_top),
        (x1, top_half, ceramic_top),
        (x0, top_half, ceramic_top),
        (x0, -bottom_half, crack_bottom),
        (x1, -bottom_half, crack_bottom),
        (x1, bottom_half, crack_bottom),
        (x0, bottom_half, crack_bottom),
    ]
    faces = [
        [crack_vertices[i] for i in [0, 1, 2, 3]],
        [crack_vertices[i] for i in [4, 5, 6, 7]],
        [crack_vertices[i] for i in [0, 1, 5, 4]],
        [crack_vertices[i] for i in [3, 2, 6, 7]],
        [crack_vertices[i] for i in [0, 3, 7, 4]],
        [crack_vertices[i] for i in [1, 2, 6, 5]],
    ]
    crack_poly = Poly3DCollection(faces, facecolors=PHASE_COLORS[0], edgecolors="#000000", linewidths=0.8, alpha=0.85)
    crack_poly.set_label("wedge crack / air")
    ax.add_collection3d(crack_poly)

    ax.set_xlim(0, x_len)
    ax.set_ylim(-y_len / 2, y_len / 2)
    ax.set_zlim(z0, ceramic_top)
    ax.set_yticks([-50, 0, 50])
    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_zlabel("z (um)")
    ax.set_title("Parameterized local TBC wedge-crack geometry (equal scale)")
    ax.view_init(elev=22, azim=-54)
    ax.set_box_aspect((x_len, y_len, ceramic_top))

    handles = [
        plt.Line2D([0], [0], color=PHASE_COLORS[3], lw=8, label="3: Inconel"),
        plt.Line2D([0], [0], color=PHASE_COLORS[2], lw=8, label="2: MCrAlY"),
        plt.Line2D([0], [0], color=PHASE_COLORS[1], lw=8, label="1: YSZ"),
        plt.Line2D([0], [0], color=PHASE_COLORS[0], lw=8, label="0: crack/air"),
    ]
    ax.legend(handles=handles, loc="upper left")
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def format_summary(metadata: dict[str, Any]) -> str:
    checks = metadata["geometry_checks"]
    lines = [
        f"model_id: {metadata['model_id']}",
        f"array_path: {metadata['array_path']}",
        f"array_shape_zyx: {metadata['array_shape_zyx']}",
        f"voxel_size_um: {metadata['voxel_size_um']}",
        f"runtime_seconds: {metadata['runtime_seconds']:.3f}",
        f"geometry_checks_passed: {checks['passed']}",
        f"top_width_voxels: {checks['top_width_voxels_actual']}",
        f"bottom_width_voxels: {checks['bottom_width_voxels_actual']}",
        f"depth_voxels: {checks['depth_voxels_actual']}",
        f"length_voxels: {checks['length_voxels_actual_at_top_centerline']}",
        f"included_angle_from_widths_deg: {metadata['crack']['included_angle_from_widths_deg']:.4f}",
        "phase_counts:",
    ]
    for label, count in sorted(metadata["phase_counts"].items(), key=lambda item: int(item[0])):
        lines.append(f"  {label} ({PHASE_NAMES[int(label)]}): {count}")
    lines.append("figures:")
    for path in metadata.get("figure_paths", []):
        lines.append(f"  {path}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/tbc_wedge_crack_local_v1.json",
        help="Path to the JSON model config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = read_json(config_path)
    metadata = build_volume(config, config_path)
    print(format_summary(metadata))


if __name__ == "__main__":
    main()
