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

from tbc_voxel_qsgs.connectivity import compute_pore_connectivity
from tbc_voxel_qsgs.grf import generate_anisotropic_grf_rve
from tbc_voxel_qsgs.metrics import compute_porosity


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _case_summary(config: dict, case: dict) -> dict:
    rve = generate_anisotropic_grf_rve(
        voxel_shape=config["voxel_shape"],
        target_porosity=config["target_porosity"],
        correlation_lengths_um=case["correlation_lengths_um"],
        physical_size_um=config["physical_size_um"],
        seed=config["seed"],
    )

    total_voxel_count = int(rve.size)
    pore_voxel_count = int(np.count_nonzero(rve == 0))
    solid_voxel_count = int(np.count_nonzero(rve == 1))
    connectivity = compute_pore_connectivity(rve)
    if connectivity["pore_voxel_count"] != pore_voxel_count:
        raise ValueError("Connectivity pore_voxel_count does not match basic summary.")

    summary = {
        "name": str(case["name"]),
        "correlation_lengths_um": [float(value) for value in case["correlation_lengths_um"]],
        "actual_porosity": float(compute_porosity(rve)),
        "solid_fraction": float(solid_voxel_count / total_voxel_count),
        "total_voxel_count": total_voxel_count,
        "pore_voxel_count": pore_voxel_count,
        "solid_voxel_count": solid_voxel_count,
    }
    for key in (
        "num_pore_clusters",
        "largest_pore_cluster_voxel_count",
        "largest_pore_cluster_fraction_of_pores",
        "percolates_x",
        "percolates_y",
        "percolates_z",
    ):
        summary[key] = connectivity[key]
    return summary


def build_comparison(config_path: Path) -> dict:
    config = _load_config(config_path)
    return {
        "method": str(config["method"]),
        "target_porosity": float(config["target_porosity"]),
        "seed": int(config["seed"]),
        "voxel_shape": [int(value) for value in config["voxel_shape"]],
        "physical_size_um": [float(value) for value in config["physical_size_um"]],
        "cases": [_case_summary(config, case) for case in config["cases"]],
    }


def write_comparison(comparison: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(comparison, file, indent=2)
        file.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare minimal GRF morphology summaries.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparison = build_comparison(args.config)
    write_comparison(comparison, args.out)

    print(f"output: {args.out}")
    print("case | correlation_lengths_um | actual_porosity | num_pore_clusters | percolates_x | percolates_y | percolates_z")
    for case in comparison["cases"]:
        print(
            f"{case['name']} | {tuple(case['correlation_lengths_um'])} | "
            f"{case['actual_porosity']} | {case['num_pore_clusters']} | "
            f"{case['percolates_x']} | {case['percolates_y']} | {case['percolates_z']}"
        )


if __name__ == "__main__":
    main()
