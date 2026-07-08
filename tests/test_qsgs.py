import json
from pathlib import Path

import numpy as np
import pytest

from tbc_voxel_qsgs.metrics import compute_porosity
from tbc_voxel_qsgs.qsgs import QSGS_DIRECTION_OFFSETS, generate_qsgs_rve


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "qsgs_1_minimal.json"


def _direction_probabilities(value=0.6):
    return {key: value for key in QSGS_DIRECTION_OFFSETS}


def _generate(seed=1, target_porosity=0.25, core_probability=0.02, max_iterations=100):
    return generate_qsgs_rve(
        voxel_shape=[12, 12, 12],
        target_porosity=target_porosity,
        core_probability=core_probability,
        direction_probabilities=_direction_probabilities(),
        seed=seed,
        max_iterations=max_iterations,
    )


def test_direction_offsets_have_expected_minimal_mapping():
    assert len(QSGS_DIRECTION_OFFSETS) == 26
    assert QSGS_DIRECTION_OFFSETS["D2"] == (0, -1, 0)
    assert QSGS_DIRECTION_OFFSETS["D4"] == (0, +1, 0)


def test_generated_array_is_3d_requested_shape_and_binary():
    rve = _generate()

    assert rve.ndim == 3
    assert rve.shape == (12, 12, 12)
    assert rve.dtype == np.uint8
    assert set(np.unique(rve).tolist()) <= {0, 1}


def test_generated_porosity_is_close_to_target_within_one_voxel():
    rve = _generate(target_porosity=0.25)
    total_voxel_count = int(rve.size)

    assert abs(compute_porosity(rve) - 0.25) <= 1 / total_voxel_count + 1e-12


def test_same_seed_gives_identical_rve():
    first = _generate(seed=1)
    second = _generate(seed=1)

    np.testing.assert_array_equal(first, second)


def test_different_seed_gives_different_rve_for_stable_case():
    first = _generate(seed=1)
    second = _generate(seed=2)

    assert not np.array_equal(first, second)


def test_target_porosity_one_returns_all_pore():
    rve = _generate(target_porosity=1.0)

    assert np.all(rve == 0)


def test_target_porosity_zero_returns_all_solid():
    rve = _generate(target_porosity=0.0)

    assert np.all(rve == 1)


def test_zero_core_probability_still_works_when_solid_is_needed():
    rve = _generate(target_porosity=0.5, core_probability=0.0)

    assert set(np.unique(rve).tolist()) == {0, 1}
    assert abs(compute_porosity(rve) - 0.5) <= 1 / rve.size + 1e-12


@pytest.mark.parametrize("voxel_shape", [[12, 12], [12, 0, 12], [12, 1.5, 12]])
def test_invalid_voxel_shape_raises_value_error(voxel_shape):
    with pytest.raises(ValueError, match="voxel_shape"):
        generate_qsgs_rve(
            voxel_shape=voxel_shape,
            target_porosity=0.25,
            core_probability=0.02,
            direction_probabilities=_direction_probabilities(),
            seed=1,
        )


@pytest.mark.parametrize("target_porosity", [-0.1, 1.1])
def test_invalid_target_porosity_raises_value_error(target_porosity):
    with pytest.raises(ValueError, match="target_porosity"):
        _generate(target_porosity=target_porosity)


@pytest.mark.parametrize("core_probability", [-0.1, 1.1])
def test_invalid_core_probability_raises_value_error(core_probability):
    with pytest.raises(ValueError, match="core_probability"):
        _generate(core_probability=core_probability)


def test_missing_direction_probability_key_raises_value_error():
    probabilities = _direction_probabilities()
    probabilities.pop("D1")

    with pytest.raises(ValueError, match="direction_probabilities"):
        generate_qsgs_rve([12, 12, 12], 0.25, 0.02, probabilities, seed=1)


def test_extra_direction_probability_key_raises_value_error():
    probabilities = _direction_probabilities()
    probabilities["D27"] = 0.1

    with pytest.raises(ValueError, match="direction_probabilities"):
        generate_qsgs_rve([12, 12, 12], 0.25, 0.02, probabilities, seed=1)


def test_invalid_direction_probability_raises_value_error():
    probabilities = _direction_probabilities()
    probabilities["D1"] = 1.1

    with pytest.raises(ValueError, match="D1"):
        generate_qsgs_rve([12, 12, 12], 0.25, 0.02, probabilities, seed=1)


@pytest.mark.parametrize("max_iterations", [0, -1, 1.5])
def test_invalid_max_iterations_raises_value_error(max_iterations):
    with pytest.raises(ValueError, match="max_iterations"):
        _generate(max_iterations=max_iterations)


def test_tiny_max_iterations_can_raise_runtime_error():
    probabilities = _direction_probabilities(value=0.0)

    with pytest.raises(RuntimeError, match="QSGS"):
        generate_qsgs_rve(
            voxel_shape=[12, 12, 12],
            target_porosity=0.5,
            core_probability=0.0,
            direction_probabilities=probabilities,
            seed=1,
            max_iterations=1,
        )


def test_config_file_exists_and_contains_required_fields():
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
