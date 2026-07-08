from __future__ import annotations

"""M2-5：isotropic vs anisotropic GRF 切片对比 smoke experiment。

用途：固定两组 correlation_lengths_um，导出两组 RVE 的 xy/xz/yz SVG 切片。
输入：JSON config，包含全局 seed/shape/porosity 和 cases。
输出：--out-dir 中的 6 个 SVG；只用于 visual sanity check，不是论文图。
注意：脚本只输出数据和文件名，不给出“哪种更好”的科学结论。
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


# 读取两组 GRF case 的对比 config。
def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _middle_slices(rve: np.ndarray) -> dict[str, np.ndarray]:
    # 统一提取中间 xy/xz/yz 切片，保证两个 case 的切片位置一致。
    nx, ny, nz = rve.shape
    return {
        "xy": rve[:, :, nz // 2],
        "xz": rve[:, ny // 2, :],
        "yz": rve[nx // 2, :, :],
    }


def _write_binary_slice_svg(path: Path, binary_slice: np.ndarray, cell_size: int = 8) -> None:
    # 修改提示：cell_size 控制 SVG 方块大小；fill 控制 pore/solid 黑白颜色。
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
    # 对单个 case 生成 RVE 并输出三张 SVG。
    # 文件名规则：{case_name}_slice_{plane}.svg。
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
    # 依次处理 config["cases"] 中的 isotropic / anisotropic_z 等固定 case。
    config = _load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return [_export_case_slices(config, case, output_dir) for case in config["cases"]]


def parse_args() -> argparse.Namespace:
    # 命令行参数：--config 指定 case config，--out-dir 指定 SVG 输出目录。
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
