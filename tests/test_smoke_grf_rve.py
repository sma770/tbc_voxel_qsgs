import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts.smoke_grf_rve import read_grf_metadata
from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.rve import load_rve_npz


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m2_3_grf_smoke.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_grf_rve.py"


def test_grf_smoke_config_exists_and_has_required_fields():
    assert CONFIG_PATH.exists()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config) >= {
        "method",
        "target_porosity",
        "seed",
        "voxel_shape",
        "physical_size_um",
        "correlation_lengths_um",
    }


def test_grf_smoke_script_runs_and_writes_readable_npz(tmp_path):
    output_path = tmp_path / "m2_3_grf_smoke_rve.npz"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--config",
            str(CONFIG_PATH),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    assert "method: anisotropic_grf_minimal" in completed.stdout
    assert "correlation_lengths_um: (2.0, 2.0, 10.0)" in completed.stdout

    array, metadata = load_rve_npz(output_path)
    grf_metadata = read_grf_metadata(output_path)

    assert array.ndim == 3
    assert array.shape == (16, 16, 16)
    assert set(np.unique(array).tolist()) <= {0, 1}

    total_voxels = 16 * 16 * 16
    assert abs(compute_porosity(array) - 0.10) <= 1 / total_voxels + 1e-12
    assert metadata.method == "anisotropic_grf_minimal"
    assert metadata.seed == 1
    assert metadata.voxel_shape == (16, 16, 16)
    assert metadata.physical_size_um == (40.0, 40.0, 40.0)
    assert metadata.target_porosity == 0.10
    assert abs(metadata.actual_porosity - 0.10) <= 1 / total_voxels + 1e-12
    assert grf_metadata["correlation_lengths_um"] == [2.0, 2.0, 10.0]
