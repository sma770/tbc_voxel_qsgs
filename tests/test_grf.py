import json
from pathlib import Path

import numpy as np
import pytest

from tbc_voxel_qsgs.grf import generate_anisotropic_grf_rve
from tbc_voxel_qsgs.metrics import compute_porosity


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "m2_2_grf_minimal.json"


def _generate(seed=1, target_porosity=0.10):
    return generate_anisotropic_grf_rve(
        voxel_shape=[16, 16, 16],
        target_porosity=target_porosity,
        correlation_lengths_um=[2.0, 2.0, 10.0],
        physical_size_um=[40.0, 40.0, 40.0],
        seed=seed,
    )


def test_generated_rve_is_3d_binary_array_with_requested_shape():
    rve = _generate()

    assert rve.ndim == 3
    assert rve.shape == (16, 16, 16)
    assert rve.dtype == np.uint8
    assert set(np.unique(rve).tolist()) <= {0, 1}


def test_generated_porosity_is_close_to_target():
    rve = _generate(target_porosity=0.10)
    total_voxels = 16 * 16 * 16

    assert abs(compute_porosity(rve) - 0.10) <= 1 / total_voxels + 1e-12


def test_same_seed_generates_identical_rve():
    first = _generate(seed=1)
    second = _generate(seed=1)

    np.testing.assert_array_equal(first, second)


def test_different_seed_generates_different_rve():
    first = _generate(seed=1)
    second = _generate(seed=2)

    assert not np.array_equal(first, second)


def test_zero_porosity_outputs_all_solid():
    rve = _generate(target_porosity=0.0)

    assert np.all(rve == 1)


def test_unit_porosity_outputs_all_pore():
    rve = _generate(target_porosity=1.0)

    assert np.all(rve == 0)


@pytest.mark.parametrize("target_porosity", [-0.1, 1.1])
def test_invalid_target_porosity_raises_value_error(target_porosity):
    with pytest.raises(ValueError, match="target_porosity"):
        _generate(target_porosity=target_porosity)


@pytest.mark.parametrize("voxel_shape", [[16, 16], [16, 0, 16], [16, -1, 16]])
def test_invalid_voxel_shape_raises_value_error(voxel_shape):
    with pytest.raises(ValueError, match="voxel_shape"):
        generate_anisotropic_grf_rve(
            voxel_shape=voxel_shape,
            target_porosity=0.10,
            correlation_lengths_um=[2.0, 2.0, 10.0],
            physical_size_um=[40.0, 40.0, 40.0],
            seed=1,
        )


@pytest.mark.parametrize(
    "correlation_lengths_um",
    [[2.0, 2.0], [2.0, 0.0, 10.0], [2.0, -1.0, 10.0]],
)
def test_invalid_correlation_lengths_raise_value_error(correlation_lengths_um):
    with pytest.raises(ValueError, match="correlation_lengths_um"):
        generate_anisotropic_grf_rve(
            voxel_shape=[16, 16, 16],
            target_porosity=0.10,
            correlation_lengths_um=correlation_lengths_um,
            physical_size_um=[40.0, 40.0, 40.0],
            seed=1,
        )


@pytest.mark.parametrize("physical_size_um", [[40.0, 40.0], [40.0, 0.0, 40.0]])
def test_invalid_physical_size_raises_value_error(physical_size_um):
    with pytest.raises(ValueError, match="physical_size_um"):
        generate_anisotropic_grf_rve(
            voxel_shape=[16, 16, 16],
            target_porosity=0.10,
            correlation_lengths_um=[2.0, 2.0, 10.0],
            physical_size_um=physical_size_um,
            seed=1,
        )


def test_config_exists_and_has_required_fields():
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
