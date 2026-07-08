from __future__ import annotations

"""M2-4：GRF 中间切片 SVG sanity check。

用途：生成一个 GRF RVE，并导出 xy/xz/yz 三个中间切片用于肉眼检查。
输入：JSON config，包含 GRF 参数。
输出：--out-dir 中的 3 个 SVG；这些 SVG 只是 sanity check，不是论文图。
相约定：SVG 中 black = pore phase 0，white = solid phase 1。
"""

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


# 读取 GRF slice config；target_porosity、correlation_lengths_um 在 config 中修改。
def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _middle_slices(rve: np.ndarray) -> dict[str, np.ndarray]:
    # 提取三个中间切片：xy at z=nz//2，xz at y=ny//2，yz at x=nx//2。
    nx, ny, nz = rve.shape
    return {
        "slice_xy.svg": rve[:, :, nz // 2],
        "slice_xz.svg": rve[:, ny // 2, :],
        "slice_yz.svg": rve[nx // 2, :, :],
    }


def _write_binary_slice_svg(path: Path, binary_slice: np.ndarray, cell_size: int = 8) -> None:
    # 修改提示：cell_size 控制 SVG 中每个 voxel 方块的像素大小。
    # 修改提示：fill 的 black/white 控制 pore/solid 的显示颜色。
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


def export_slices(config_path: Path, output_dir: Path) -> tuple[float, list[str], dict]:
    # 生成 RVE、计算实际孔隙率，并把三个中间切片写成 SVG。
    config = _load_config(config_path)
    rve = generate_anisotropic_grf_rve(
        voxel_shape=config["voxel_shape"],
        target_porosity=config["target_porosity"],
        correlation_lengths_um=config["correlation_lengths_um"],
        physical_size_um=config["physical_size_um"],
        seed=config["seed"],
    )
    actual_porosity = compute_porosity(rve)

    output_dir.mkdir(parents=True, exist_ok=True)
    filenames = []
    for filename, binary_slice in _middle_slices(rve).items():
        _write_binary_slice_svg(output_dir / filename, binary_slice)
        filenames.append(filename)

    return actual_porosity, filenames, config


def parse_args() -> argparse.Namespace:
    # 命令行参数：--config 指定输入 JSON，--out-dir 指定 SVG 输出目录。
    parser = argparse.ArgumentParser(description="Export M2-4 GRF middle-slice SVG sanity checks.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    actual_porosity, filenames, config = export_slices(args.config, args.out_dir)

    print(f"output directory: {args.out_dir}")
    print(f"voxel_shape: {tuple(config['voxel_shape'])}")
    print(f"target_porosity: {config['target_porosity']}")
    print(f"actual_porosity: {actual_porosity}")
    print(f"correlation_lengths_um: {tuple(config['correlation_lengths_um'])}")
    print(f"generated SVG filenames: {', '.join(filenames)}")


if __name__ == "__main__":
    main()
