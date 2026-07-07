import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m2_5_grf_iso_vs_aniso.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "compare_grf_iso_aniso_slices.py"
EXPECTED_FILES = {
    "isotropic_slice_xy.svg",
    "isotropic_slice_xz.svg",
    "isotropic_slice_yz.svg",
    "anisotropic_z_slice_xy.svg",
    "anisotropic_z_slice_xz.svg",
    "anisotropic_z_slice_yz.svg",
}


def test_iso_vs_aniso_config_exists_and_has_required_fields():
    assert CONFIG_PATH.exists()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config) >= {
        "method",
        "target_porosity",
        "seed",
        "voxel_shape",
        "physical_size_um",
        "cases",
    }
    assert len(config["cases"]) == 2
    case_names = {case["name"] for case in config["cases"]}
    assert case_names == {"isotropic", "anisotropic_z"}
    assert all("correlation_lengths_um" in case for case in config["cases"])


def test_compare_grf_iso_aniso_script_writes_only_expected_svgs(tmp_path):
    output_dir = tmp_path / "m2_5_grf_iso_vs_aniso_preview"

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

    assert "isotropic" in completed.stdout
    assert "anisotropic_z" in completed.stdout
    assert "actual_porosity" in completed.stdout

    output_files = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert output_files == EXPECTED_FILES

    for filename in EXPECTED_FILES:
        svg_path = output_dir / filename
        assert svg_path.stat().st_size > 0
        assert "<svg" in svg_path.read_text(encoding="utf-8")

    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.csv"))
    assert not list(tmp_path.rglob("*.log"))
    assert {path.name for path in tmp_path.rglob("*") if path.is_file()} == EXPECTED_FILES
