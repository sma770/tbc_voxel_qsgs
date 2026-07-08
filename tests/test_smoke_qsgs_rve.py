import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.qsgs import QSGS_DIRECTION_OFFSETS
from tbc_voxel_qsgs.rve import load_rve_npz


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "qsgs_2_smoke_and_slices.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_qsgs_rve.py"
EXPECTED_SVGS = {"qsgs_slice_xy.svg", "qsgs_slice_xz.svg", "qsgs_slice_yz.svg"}


def _direction_probabilities():
    return {
        key: (0.10 if key in {"D2", "D4"} else 0.60)
        for key in QSGS_DIRECTION_OFFSETS
    }


def _write_small_config(path: Path) -> dict:
    config = {
        "method": "qsgs_minimal",
        "target_porosity": 0.10,
        "seed": 1,
        "voxel_shape": [12, 12, 12],
        "physical_size_um": [40.0, 40.0, 40.0],
        "core_probability": 0.02,
        "direction_probabilities": _direction_probabilities(),
        "max_iterations": 10000,
    }
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def test_formal_qsgs_2_config_exists_and_has_required_fields():
    assert CONFIG_PATH.exists()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config) >= {
        "method",
        "target_porosity",
        "seed",
        "voxel_shape",
        "physical_size_um",
        "core_probability",
        "direction_probabilities",
        "max_iterations",
    }
    assert config["voxel_shape"] == [40, 40, 40]
    assert set(config["direction_probabilities"]) == {f"D{index}" for index in range(1, 27)}


def test_smoke_qsgs_rve_script_writes_npz_and_slice_svgs_to_tmp_path(tmp_path):
    config_path = tmp_path / "qsgs_2_small_test_config.json"
    config = _write_small_config(config_path)
    output_npz = tmp_path / "qsgs_2_smoke_rve.npz"
    slice_dir = tmp_path / "qsgs_2_slices_preview"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--config",
            str(config_path),
            "--out",
            str(output_npz),
            "--slice-dir",
            str(slice_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_npz.exists()
    loaded_rve, metadata = load_rve_npz(output_npz)
    assert loaded_rve.ndim == 3
    assert loaded_rve.shape == tuple(config["voxel_shape"])
    assert set(np.unique(loaded_rve).tolist()) <= {0, 1}

    total_voxel_count = int(loaded_rve.size)
    assert abs(compute_porosity(loaded_rve) - config["target_porosity"]) <= (
        1 / total_voxel_count + 1e-12
    )
    assert metadata.method == "qsgs_minimal"
    assert metadata.voxel_shape == tuple(config["voxel_shape"])

    output_files = {path.name for path in slice_dir.iterdir() if path.is_file()}
    assert output_files == EXPECTED_SVGS
    for filename in EXPECTED_SVGS:
        svg_path = slice_dir / filename
        assert svg_path.stat().st_size > 0
        assert "<svg" in svg_path.read_text(encoding="utf-8")

    assert "qsgs_minimal" in completed.stdout
    assert "actual_porosity" in completed.stdout
    assert "core_probability" in completed.stdout
    assert "qsgs_slice_xy.svg" in completed.stdout
    assert "qsgs_slice_xz.svg" in completed.stdout
    assert "qsgs_slice_yz.svg" in completed.stdout

    root_generated_patterns = [
        "qsgs_2_smoke_rve.npz",
        "qsgs_slice_xy.svg",
        "qsgs_slice_xz.svg",
        "qsgs_slice_yz.svg",
        "qsgs_2_smoke_and_slices_summary.json",
        "qsgs_2_smoke.log",
    ]
    assert not any((REPO_ROOT / pattern).exists() for pattern in root_generated_patterns)
