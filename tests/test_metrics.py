import numpy as np

from tbc_voxel_qsgs.metrics import compute_porosity


def test_all_solid_porosity_is_zero():
    array = np.ones((2, 3, 4), dtype=np.uint8)

    assert compute_porosity(array) == 0.0


def test_all_pore_porosity_is_one():
    array = np.zeros((2, 3, 4), dtype=np.uint8)

    assert compute_porosity(array) == 1.0


def test_known_small_array_porosity():
    array = np.array(
        [
            [[0, 1], [1, 1]],
            [[0, 0], [1, 1]],
        ],
        dtype=np.uint8,
    )

    assert compute_porosity(array) == 3 / 8
