import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tbc_voxel_qsgs.rve import RVEMetadata, save_rve_npz


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m3_0_morphology_summary.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "summarize_rve_morphology.py"
EXPECTED_METRICS = {
    "voxel_shape",
    "physical_size_um",
    "target_porosity",
    "actual_porosity",
    "solid_fraction",
    "pore_voxel_count",
    "solid_voxel_count",
    "total_voxel_count",
}


def test_morphology_summary_config_exists_and_has_required_fields():
    assert CONFIG_PATH.exists()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config) >= {"input_rve_npz", "output_summary_json", "metrics"}
    assert set(config["metrics"]) >= EXPECTED_METRICS


def test_summarize_rve_morphology_script_writes_basic_json_summary(tmp_path):
    input_path = tmp_path / "test_rve.npz"
    output_path = tmp_path / "summary.json"
    rve = np.array(
        [
            [[0, 1], [1, 1]],
            [[0, 0], [1, 1]],
        ],
        dtype=np.uint8,
    )
    metadata = RVEMetadata(
        method="unit_test_rve",
        target_porosity=0.25,
        actual_porosity=None,
        seed=7,
        voxel_shape=None,
        physical_size_um=(40.0, 40.0, 40.0),
    )
    save_rve_npz(input_path, rve, metadata)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(input_path),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "actual_porosity" in completed.stdout
    assert output_path.exists()

    summary = json.loads(output_path.read_text(encoding="utf-8"))
    assert set(summary) >= {
        "voxel_shape",
        "actual_porosity",
        "solid_fraction",
        "total_voxel_count",
        "pore_voxel_count",
        "solid_voxel_count",
    }
    assert summary["method"] == "unit_test_rve"
    assert summary["seed"] == 7
    assert summary["physical_size_um"] == [40.0, 40.0, 40.0]
    assert summary["target_porosity"] == 0.25
    assert summary["voxel_shape"] == [2, 2, 2]
    assert summary["pore_voxel_count"] + summary["solid_voxel_count"] == summary["total_voxel_count"]
    assert summary["actual_porosity"] == summary["pore_voxel_count"] / summary["total_voxel_count"]
    assert summary["solid_fraction"] == summary["solid_voxel_count"] / summary["total_voxel_count"]
