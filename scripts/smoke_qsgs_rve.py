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

from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.qsgs import generate_qsgs_rve
from tbc_voxel_qsgs.rve import RVEMetadata, load_rve_npz, save_rve_npz


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _metadata_from_config(config: dict, actual_porosity: float) -> RVEMetadata:
    return RVEMetadata(
        method=config["method"],
        target_porosity=float(config["target_porosity"]),
        actual_porosity=actual_porosity,
        seed=int(config["seed"]),
        voxel_shape=tuple(int(value) for value in config["voxel_shape"]),
        physical_size_um=tuple(float(value) for value in config["physical_size_um"]),
    )


def _middle_slices(rve: np.ndarray) -> dict[str, np.ndarray]:
    nx, ny, nz = rve.shape
    return {
        "qsgs_slice_xy.svg": rve[:, :, nz // 2],
        "qsgs_slice_xz.svg": rve[:, ny // 2, :],
        "qsgs_slice_yz.svg": rve[nx // 2, :, :],
    }


def _write_binary_slice_svg(path: Path, binary_slice: np.ndarray, cell_size: int = 8) -> None:
    rows, cols = binary_slice.shape
    width = cols * cell_size
    height = rows * cell_size
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]

    for row in range(rows):
        for col in range(cols):
            fill = "black" if int(binary_slice[row, col]) == 0 else "white"
            lines.append(
                f'<rect x="{col * cell_size}" y="{row * cell_size}" '
                f'width="{cell_size}" height="{cell_size}" fill="{fill}"/>'
            )

    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_smoke(config_path: Path, output_path: Path, slice_dir: Path):
    config = _load_config(config_path)
    rve = generate_qsgs_rve(
        voxel_shape=config["voxel_shape"],
        target_porosity=config["target_porosity"],
        core_probability=config["core_probability"],
        direction_probabilities=config["direction_probabilities"],
        seed=config["seed"],
        max_iterations=config["max_iterations"],
    )
    actual_porosity = compute_porosity(rve)
    metadata = _metadata_from_config(config, actual_porosity)

    save_rve_npz(output_path, rve, metadata)
    loaded_rve, loaded_metadata = load_rve_npz(output_path)

    slice_dir.mkdir(parents=True, exist_ok=True)
    filenames = []
    for filename, binary_slice in _middle_slices(loaded_rve).items():
        _write_binary_slice_svg(slice_dir / filename, binary_slice)
        filenames.append(filename)

    return loaded_rve, loaded_metadata, filenames, config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QSGS-2 RVE IO and slice SVG smoke workflow.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--slice-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, metadata, filenames, config = run_smoke(args.config, args.out, args.slice_dir)

    print(f"output npz path: {args.out}")
    print(f"slice directory: {args.slice_dir}")
    print(f"method: {metadata.method}")
    print(f"voxel_shape: {metadata.voxel_shape}")
    print(f"physical_size_um: {metadata.physical_size_um}")
    print(f"target_porosity: {metadata.target_porosity}")
    print(f"actual_porosity: {metadata.actual_porosity}")
    print(f"seed: {metadata.seed}")
    print(f"core_probability: {config['core_probability']}")
    print(f"D2 probability: {config['direction_probabilities']['D2']}")
    print(f"D4 probability: {config['direction_probabilities']['D4']}")
    print(f"generated SVG filenames: {', '.join(filenames)}")


if __name__ == "__main__":
    main()
