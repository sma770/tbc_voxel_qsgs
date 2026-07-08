from __future__ import annotations

"""M2-3：GRF RVE IO smoke workflow。

用途：把 minimal Anisotropic GRF generator 接入 RVE .npz 保存/读取流程。
输入：JSON config，包含 voxel_shape、target_porosity、correlation_lengths_um 等。
输出：用户通过 --out 指定的 .npz；这是 smoke test 产物，不是论文结果。
注意：correlation_lengths_um 是 GRF 参数，当前用额外 JSON 字段写入 .npz 供 smoke 检查。
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
from tbc_voxel_qsgs.rve import RVEMetadata, load_rve_npz, save_rve_npz


# 读取 GRF smoke config；GRF 相关参数优先在 config 文件中修改。
def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_grf_metadata(path: Path, correlation_lengths_um: tuple[float, float, float]) -> None:
    # M2-3 为了记录 correlation_lengths_um，额外写入 grf_metadata_json。
    # 这里没有修改 RVE 标准 metadata schema。
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
    # 读取 M2-3 额外记录的 GRF 参数；没有该字段时返回空 dict。
    with np.load(path, allow_pickle=False) as data:
        if "grf_metadata_json" not in data.files:
            return {}
        return json.loads(data["grf_metadata_json"].item())


def run_smoke(config_path: Path, output_path: Path):
    # 串起 GRF workflow：config -> GRF RVE -> porosity -> save/load -> metadata。
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
    # 命令行参数：--config 指定 GRF 参数 JSON，--out 指定输出 .npz。
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
