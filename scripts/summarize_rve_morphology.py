from __future__ import annotations

"""M3-0/M3-2：RVE morphology summary workflow。

用途：读取已有 RVE .npz，输出基础体素统计、孔隙率和 pore connectivity JSON summary。
输入：--input 指定的 RVE .npz。
输出：--out 指定的 JSON summary；这是最小形貌统计，不是论文级高级指标。
相约定：0 = pore phase，1 = solid 8YSZ phase。
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

from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.connectivity import compute_pore_connectivity
from tbc_voxel_qsgs.rve import load_rve_npz


# 兼容 dataclass metadata 和 dict metadata，避免重做 metadata 系统。
def _metadata_get(metadata, key: str):
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


def _as_json_list(value):
    # JSON 不直接支持 tuple / NumPy scalar，这里转成普通 Python list。
    if value is None:
        return None
    return [float(item) if isinstance(item, float) else int(item) for item in value]


def summarize_rve(input_path: Path) -> dict:
    # 主流程：load .npz -> 校验 binary 3D -> 计算 counts/porosity/connectivity。
    rve, metadata = load_rve_npz(input_path)
    if rve.ndim != 3:
        raise ValueError("RVE array must be 3D.")
    if not np.isin(rve, [0, 1]).all():
        raise ValueError("RVE array values must be binary: 0 for pore, 1 for solid.")

    total_voxel_count = int(rve.size)
    pore_voxel_count = int(np.count_nonzero(rve == 0))
    solid_voxel_count = int(np.count_nonzero(rve == 1))
    actual_porosity = float(compute_porosity(rve))
    solid_fraction = float(solid_voxel_count / total_voxel_count)
    connectivity = compute_pore_connectivity(rve)
    if connectivity["pore_voxel_count"] != pore_voxel_count:
        # 保护性检查：避免 summary 中出现两个互相矛盾的 pore_voxel_count。
        raise ValueError("Connectivity pore_voxel_count does not match basic summary.")

    summary = {
        "voxel_shape": [int(value) for value in rve.shape],
        "actual_porosity": actual_porosity,
        "solid_fraction": solid_fraction,
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

    for key in ("method", "seed", "target_porosity"):
        value = _metadata_get(metadata, key)
        if value is not None:
            summary[key] = value

    physical_size_um = _metadata_get(metadata, "physical_size_um")
    if physical_size_um is not None:
        summary["physical_size_um"] = _as_json_list(physical_size_um)

    return summary


def write_summary(summary: dict, output_path: Path) -> None:
    # 写出 indent=2 的 JSON，方便人工检查。
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    # 命令行参数：--input 读取 .npz，--out 写出 JSON。
    parser = argparse.ArgumentParser(description="Write a minimal RVE morphology summary JSON.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = summarize_rve(args.input)
    write_summary(summary, args.out)

    print(f"input: {args.input}")
    print(f"output: {args.out}")
    print(f"voxel_shape: {tuple(summary['voxel_shape'])}")
    print(f"actual_porosity: {summary['actual_porosity']}")
    print(f"solid_fraction: {summary['solid_fraction']}")
    print(f"num_pore_clusters: {summary['num_pore_clusters']}")
    print(f"percolates_x: {summary['percolates_x']}")
    print(f"percolates_y: {summary['percolates_y']}")
    print(f"percolates_z: {summary['percolates_z']}")


if __name__ == "__main__":
    main()
