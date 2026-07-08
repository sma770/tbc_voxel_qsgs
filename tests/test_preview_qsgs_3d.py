import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tbc_voxel_qsgs.rve import RVEMetadata, save_rve_npz


pytest.importorskip("plotly")


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "preview_qsgs_3d.py"


def test_preview_qsgs_3d_writes_interactive_html_to_tmp_path(tmp_path):
    input_npz = tmp_path / "small_qsgs_rve.npz"
    output_html = tmp_path / "qsgs_2_3d_preview.html"
    rve = np.ones((6, 6, 6), dtype=np.uint8)
    rve[1:4, 1:4, 1:4] = 0
    metadata = RVEMetadata(
        method="qsgs_minimal",
        target_porosity=None,
        actual_porosity=None,
        seed=1,
        voxel_shape=None,
        physical_size_um=(40.0, 40.0, 40.0),
    )
    save_rve_npz(input_npz, rve, metadata)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(input_npz),
            "--out-html",
            str(output_html),
            "--phase",
            "pore",
            "--max-points",
            "20",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_html.exists()
    assert output_html.stat().st_size > 0
    html = output_html.read_text(encoding="utf-8").lower()
    assert "plotly" in html
    assert "mesh3d" in html
    assert "visual sanity check" in completed.stdout
    assert "not a paper figure" in completed.stdout
    assert "selected phase" in completed.stdout
    assert "number of exposed faces" in completed.stdout
    assert not (REPO_ROOT / "qsgs_2_3d_preview.html").exists()
    assert not (REPO_ROOT / "small_qsgs_rve.npz").exists()
