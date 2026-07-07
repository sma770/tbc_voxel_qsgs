import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m3_3_grf_morphology_compare.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "compare_grf_morphology.py"
CASE_KEYS = {
    "name",
    "correlation_lengths_um",
    "actual_porosity",
    "solid_fraction",
    "total_voxel_count",
    "pore_voxel_count",
    "solid_voxel_count",
    "num_pore_clusters",
    "largest_pore_cluster_voxel_count",
    "largest_pore_cluster_fraction_of_pores",
    "percolates_x",
    "percolates_y",
    "percolates_z",
}


def test_grf_morphology_compare_config_exists_and_has_required_fields():
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
    assert {case["name"] for case in config["cases"]} == {"isotropic", "anisotropic_z"}
    assert all(set(case) >= {"name", "correlation_lengths_um"} for case in config["cases"])


def test_compare_grf_morphology_script_writes_expected_json_only(tmp_path):
    output_path = tmp_path / "m3_3_grf_morphology_compare_preview.json"

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

    assert "isotropic" in completed.stdout
    assert "anisotropic_z" in completed.stdout
    assert "actual_porosity" in completed.stdout
    assert "num_pore_clusters" in completed.stdout
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    comparison = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(comparison["cases"]) == 2

    for case in comparison["cases"]:
        assert set(case) >= CASE_KEYS
        assert case["pore_voxel_count"] + case["solid_voxel_count"] == case["total_voxel_count"]
        assert case["actual_porosity"] == case["pore_voxel_count"] / case["total_voxel_count"]
        assert case["solid_fraction"] == case["solid_voxel_count"] / case["total_voxel_count"]
        assert abs(case["actual_porosity"] - comparison["target_porosity"]) <= (
            1 / case["total_voxel_count"] + 1e-12
        )
        assert type(case["percolates_x"]) is bool
        assert type(case["percolates_y"]) is bool
        assert type(case["percolates_z"]) is bool

    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.svg"))
    assert not list(tmp_path.rglob("*.csv"))
    assert not list(tmp_path.rglob("*.log"))
    assert {path.name for path in tmp_path.rglob("*") if path.is_file()} == {output_path.name}
