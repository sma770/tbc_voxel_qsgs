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

from tbc_voxel_qsgs.grf import generate_anisotropic_grf_rve
from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.rve import RVEMetadata, load_rve_npz, save_rve_npz


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_grf_metadata(path: Path, correlation_lengths_um: tuple[float, float, float]) -> None:
    with np.load(path, allow_pickle=False) as data:
        payload = {name: data[name] for name in data.files}

    payload["grf_metadata_json"] = np.array(
        json.dumps(
            {"correlation_lengths_um": list(correlation_lengths_um)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    np.savez_compressed(path, **payload)


def read_grf_metadata(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as data:
        if "grf_metadata_json" not in data.files:
            return {}
        return json.loads(data["grf_metadata_json"].item())


def run_smoke(config_path: Path, output_path: Path):
    config = load_config(config_path)
    correlation_lengths_um = tuple(float(value) for value in config["correlation_lengths_um"])

    rve = generate_anisotropic_grf_rve(
        voxel_shape=config["voxel_shape"],
        target_porosity=config["target_porosity"],
        correlation_lengths_um=config["correlation_lengths_um"],
        physical_size_um=config["physical_size_um"],
        seed=config["seed"],
    )
    actual_porosity = compute_porosity(rve)

    metadata = RVEMetadata(
        method=config["method"],
        target_porosity=float(config["target_porosity"]),
        actual_porosity=actual_porosity,
        seed=int(config["seed"]),
        voxel_shape=tuple(int(value) for value in config["voxel_shape"]),
        physical_size_um=tuple(float(value) for value in config["physical_size_um"]),
    )

    save_rve_npz(output_path, rve, metadata)
    _write_grf_metadata(output_path, correlation_lengths_um)
    loaded_rve, loaded_metadata = load_rve_npz(output_path)
    grf_metadata = read_grf_metadata(output_path)
    return loaded_rve, loaded_metadata, grf_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the M2-3 GRF RVE IO smoke workflow.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, metadata, grf_metadata = run_smoke(args.config, args.out)

    print(f"output path: {args.out}")
    print(f"method: {metadata.method}")
    print(f"voxel_shape: {metadata.voxel_shape}")
    print(f"physical_size_um: {metadata.physical_size_um}")
    print(f"correlation_lengths_um: {tuple(grf_metadata['correlation_lengths_um'])}")
    print(f"target_porosity: {metadata.target_porosity}")
    print(f"actual_porosity: {metadata.actual_porosity}")
    print(f"seed: {metadata.seed}")


if __name__ == "__main__":
    main()
