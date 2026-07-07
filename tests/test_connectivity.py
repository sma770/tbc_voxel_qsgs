import numpy as np
import pytest

from tbc_voxel_qsgs.connectivity import compute_pore_connectivity


def test_all_solid_array_has_zero_clusters_and_no_percolation():
    result = compute_pore_connectivity(np.ones((3, 3, 3), dtype=np.uint8))

    assert result["pore_voxel_count"] == 0
    assert result["num_pore_clusters"] == 0
    assert result["largest_pore_cluster_voxel_count"] == 0
    assert result["largest_pore_cluster_fraction_of_pores"] == 0.0
    assert result["percolates_x"] is False
    assert result["percolates_y"] is False
    assert result["percolates_z"] is False


def test_all_pore_array_has_one_cluster_and_percolates_all_directions():
    result = compute_pore_connectivity(np.zeros((3, 3, 3), dtype=np.uint8))

    assert result["pore_voxel_count"] == 27
    assert result["num_pore_clusters"] == 1
    assert result["largest_pore_cluster_voxel_count"] == 27
    assert result["largest_pore_cluster_fraction_of_pores"] == 1.0
    assert result["percolates_x"] is True
    assert result["percolates_y"] is True
    assert result["percolates_z"] is True


def test_two_isolated_pore_voxels_are_two_clusters():
    array = np.ones((3, 3, 3), dtype=np.uint8)
    array[0, 0, 0] = 0
    array[2, 2, 2] = 0

    result = compute_pore_connectivity(array)

    assert result["num_pore_clusters"] == 2


def test_x_direction_pore_line_percolates_x_only():
    array = np.ones((3, 3, 3), dtype=np.uint8)
    array[:, 1, 1] = 0

    result = compute_pore_connectivity(array)

    assert result["percolates_x"] is True
    assert result["percolates_y"] is False
    assert result["percolates_z"] is False


def test_y_direction_pore_line_percolates_y_only():
    array = np.ones((3, 3, 3), dtype=np.uint8)
    array[1, :, 1] = 0

    result = compute_pore_connectivity(array)

    assert result["percolates_x"] is False
    assert result["percolates_y"] is True
    assert result["percolates_z"] is False


def test_z_direction_pore_line_percolates_z_only():
    array = np.ones((3, 3, 3), dtype=np.uint8)
    array[1, 1, :] = 0

    result = compute_pore_connectivity(array)

    assert result["percolates_x"] is False
    assert result["percolates_y"] is False
    assert result["percolates_z"] is True


def test_diagonal_only_pores_are_not_connected_with_six_connectivity():
    array = np.ones((2, 2, 2), dtype=np.uint8)
    array[0, 0, 0] = 0
    array[1, 1, 1] = 0

    result = compute_pore_connectivity(array)

    assert result["num_pore_clusters"] == 2


def test_largest_pore_cluster_fraction_of_pores():
    array = np.ones((4, 4, 4), dtype=np.uint8)
    array[0, 0, 0] = 0
    array[0, 0, 1] = 0
    array[0, 0, 2] = 0
    array[3, 3, 3] = 0

    result = compute_pore_connectivity(array)

    assert result["pore_voxel_count"] == 4
    assert result["num_pore_clusters"] == 2
    assert result["largest_pore_cluster_voxel_count"] == 3
    assert result["largest_pore_cluster_fraction_of_pores"] == 3 / 4


def test_invalid_dimension_raises_value_error():
    with pytest.raises(ValueError, match="3D"):
        compute_pore_connectivity(np.ones((3, 3), dtype=np.uint8))


def test_invalid_values_raise_value_error():
    array = np.ones((2, 2, 2), dtype=np.uint8)
    array[0, 0, 0] = 2

    with pytest.raises(ValueError, match="binary"):
        compute_pore_connectivity(array)


def test_return_value_types_are_python_native_types():
    array = np.ones((3, 3, 3), dtype=np.uint8)
    array[:, 1, 1] = 0

    result = compute_pore_connectivity(array)

    assert type(result["pore_voxel_count"]) is int
    assert type(result["num_pore_clusters"]) is int
    assert type(result["largest_pore_cluster_voxel_count"]) is int
    assert type(result["largest_pore_cluster_fraction_of_pores"]) is float
    assert type(result["percolates_x"]) is bool
    assert type(result["percolates_y"]) is bool
    assert type(result["percolates_z"]) is bool
