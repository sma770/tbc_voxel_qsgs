from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from tbc_voxel_qsgs import RVEMetadata, compute_porosity, load_rve_npz, save_rve_npz


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def create_manual_smoke_rve(voxel_shape: list[int], target_porosity: float) -> np.ndarray:
    shape = tuple(int(value) for value in voxel_shape)
    if len(shape) != 3:
        raise ValueError("voxel_shape must contain exactly three values.")
    if not 0.0 <= target_porosity <= 1.0:
        raise ValueError("target_porosity must be between 0 and 1.")

    voxels = np.ones(shape, dtype=np.uint8)
    total_voxels = int(voxels.size)
    num_pores = round(target_porosity * total_voxels)
    flat = voxels.reshape(-1)
    flat[:num_pores] = 0
    return voxels


def run_smoke(config_path: Path, output_path: Path) -> tuple[np.ndarray, RVEMetadata]:
    config = load_config(config_path)
    voxels = create_manual_smoke_rve(config["voxel_shape"], float(config["target_porosity"]))
    actual_porosity = compute_porosity(voxels)

    metadata = RVEMetadata(
        method=config["method"],
        target_porosity=float(config["target_porosity"]),
        actual_porosity=actual_porosity,
        seed=int(config["seed"]),
        voxel_shape=tuple(int(value) for value in config["voxel_shape"]),
        physical_size_um=tuple(float(value) for value in config["physical_size_um"]),
    )

    save_rve_npz(output_path, voxels, metadata)
    return load_rve_npz(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the M2-1 RVE IO smoke workflow.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, metadata = run_smoke(args.config, args.out)

    print(f"output path: {args.out}")
    print(f"voxel_shape: {metadata.voxel_shape}")
    print(f"target_porosity: {metadata.target_porosity}")
    print(f"actual_porosity: {metadata.actual_porosity}")
    print(f"method: {metadata.method}")
    print(f"seed: {metadata.seed}")


if __name__ == "__main__":
    main()
