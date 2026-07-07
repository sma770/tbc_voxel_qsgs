import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tbc_voxel_qsgs import compute_porosity, load_rve_npz


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m2_1_rve_smoke.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_rve_io.py"


def test_smoke_config_exists_and_has_required_fields():
    assert CONFIG_PATH.exists()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config) >= {
        "method",
        "target_porosity",
        "seed",
        "voxel_shape",
        "physical_size_um",
    }


def test_smoke_script_runs_and_writes_readable_npz(tmp_path):
    output_path = tmp_path / "m2_1_smoke_rve.npz"

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
    assert "actual_porosity: 0.25" in completed.stdout

    array, metadata = load_rve_npz(output_path)

    assert array.ndim == 3
    assert set(np.unique(array).tolist()) <= {0, 1}
    assert compute_porosity(array) == 0.25
    assert metadata.method == "manual_smoke_rve"
    assert metadata.target_porosity == 0.25
    assert metadata.actual_porosity == 0.25
    assert metadata.voxel_shape == (4, 4, 4)
    assert metadata.physical_size_um == (40.0, 40.0, 40.0)
