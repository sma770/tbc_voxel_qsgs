import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m2_4_grf_slices.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "export_grf_slices.py"
EXPECTED_FILES = {"slice_xy.svg", "slice_xz.svg", "slice_yz.svg"}


def test_grf_slices_config_exists_and_has_required_fields():
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


def test_export_grf_slices_script_writes_only_three_svgs(tmp_path):
    output_dir = tmp_path / "m2_4_grf_slices_preview"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--config",
            str(CONFIG_PATH),
            "--out-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "actual_porosity" in completed.stdout
    assert output_dir.exists()

    output_files = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert output_files == EXPECTED_FILES

    for filename in EXPECTED_FILES:
        svg_path = output_dir / filename
        assert svg_path.stat().st_size > 0
        assert "<svg" in svg_path.read_text(encoding="utf-8")

    assert not list(tmp_path.rglob("*.npz"))
    assert {path.name for path in tmp_path.rglob("*") if path.is_file()} == EXPECTED_FILES
