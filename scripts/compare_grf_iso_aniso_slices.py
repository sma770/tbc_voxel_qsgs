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


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _middle_slices(rve: np.ndarray) -> dict[str, np.ndarray]:
    nx, ny, nz = rve.shape
    return {
        "xy": rve[:, :, nz // 2],
        "xz": rve[:, ny // 2, :],
        "yz": rve[nx // 2, :, :],
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


def _export_case_slices(config: dict, case: dict, output_dir: Path) -> dict:
    rve = generate_anisotropic_grf_rve(
        voxel_shape=config["voxel_shape"],
        target_porosity=config["target_porosity"],
        correlation_lengths_um=case["correlation_lengths_um"],
        physical_size_um=config["physical_size_um"],
        seed=config["seed"],
    )
    actual_porosity = compute_porosity(rve)

    filenames = []
    for plane, binary_slice in _middle_slices(rve).items():
        filename = f"{case['name']}_slice_{plane}.svg"
        _write_binary_slice_svg(output_dir / filename, binary_slice)
        filenames.append(filename)

    return {
        "name": case["name"],
        "correlation_lengths_um": case["correlation_lengths_um"],
        "target_porosity": config["target_porosity"],
        "actual_porosity": actual_porosity,
        "filenames": filenames,
    }


def run_comparison(config_path: Path, output_dir: Path) -> list[dict]:
    config = _load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return [_export_case_slices(config, case, output_dir) for case in config["cases"]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export M2-5 isotropic vs anisotropic GRF slice SVGs.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = run_comparison(args.config, args.out_dir)

    print(f"output directory: {args.out_dir}")
    for summary in summaries:
        print(f"case: {summary['name']}")
        print(f"correlation_lengths_um: {tuple(summary['correlation_lengths_um'])}")
        print(f"target_porosity: {summary['target_porosity']}")
        print(f"actual_porosity: {summary['actual_porosity']}")
        print(f"exported SVG filenames: {', '.join(summary['filenames'])}")


if __name__ == "__main__":
    main()
