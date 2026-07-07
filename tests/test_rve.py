import numpy as np
import pytest

from tbc_voxel_qsgs.rve import RVEMetadata, load_rve_npz, save_rve_npz, validate_rve_array


def test_validate_rejects_non_3d_array():
    with pytest.raises(ValueError, match="3D"):
        validate_rve_array(np.ones((2, 2), dtype=np.uint8))


def test_validate_rejects_non_binary_array():
    with pytest.raises(ValueError, match="binary"):
        validate_rve_array(np.array([[[0, 1], [2, 1]]], dtype=np.uint8))


def test_validate_accepts_bool_array_and_returns_uint8():
    array = np.array([[[True, False], [True, True]]])

    validated = validate_rve_array(array)

    assert validated.dtype == np.uint8
    np.testing.assert_array_equal(validated, np.array([[[1, 0], [1, 1]]], dtype=np.uint8))


def test_save_load_npz_preserves_array_and_updates_metadata(tmp_path):
    array = np.array(
        [
            [[0, 1], [1, 1]],
            [[0, 0], [1, 1]],
        ],
        dtype=np.uint8,
    )
    metadata = RVEMetadata(
        method="unknown",
        target_porosity=0.25,
        actual_porosity=0.0,
        seed=123,
        voxel_shape=(1, 1, 1),
        physical_size_um=(40.0, 40.0, 40.0),
    )
    path = tmp_path / "rve.npz"

    save_rve_npz(path, array, metadata)
    loaded_array, loaded_metadata = load_rve_npz(path)

    np.testing.assert_array_equal(loaded_array, array)
    assert loaded_array.dtype == np.uint8
    assert loaded_metadata.actual_porosity == 3 / 8
    assert loaded_metadata.voxel_shape == (2, 2, 2)
    assert loaded_metadata.physical_size_um == (40.0, 40.0, 40.0)
    assert loaded_metadata.seed == 123
