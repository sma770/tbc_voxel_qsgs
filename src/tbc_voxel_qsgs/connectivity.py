from __future__ import annotations

from typing import Any

import numpy as np

from .rve import validate_rve_array


_NEIGHBOR_OFFSETS = (
    (-1, 0, 0),
    (1, 0, 0),
    (0, -1, 0),
    (0, 1, 0),
    (0, 0, -1),
    (0, 0, 1),
)


def compute_pore_connectivity(array: Any) -> dict:
    voxels = validate_rve_array(array)
    nx, ny, nz = voxels.shape
    pore_mask = voxels == 0
    visited = np.zeros(voxels.shape, dtype=bool)
    pore_voxel_count = int(np.count_nonzero(pore_mask))

    if pore_voxel_count == 0:
        return {
            "pore_voxel_count": 0,
            "num_pore_clusters": 0,
            "largest_pore_cluster_voxel_count": 0,
            "largest_pore_cluster_fraction_of_pores": 0.0,
            "percolates_x": False,
            "percolates_y": False,
            "percolates_z": False,
        }

    num_pore_clusters = 0
    largest_cluster_size = 0
    percolates_x = False
    percolates_y = False
    percolates_z = False

    for start in np.argwhere(pore_mask):
        sx, sy, sz = (int(value) for value in start)
        if visited[sx, sy, sz]:
            continue

        num_pore_clusters += 1
        cluster_size = 0
        touches_x_min = touches_x_max = False
        touches_y_min = touches_y_max = False
        touches_z_min = touches_z_max = False
        stack = [(sx, sy, sz)]
        visited[sx, sy, sz] = True

        while stack:
            x, y, z = stack.pop()
            cluster_size += 1
            touches_x_min = touches_x_min or x == 0
            touches_x_max = touches_x_max or x == nx - 1
            touches_y_min = touches_y_min or y == 0
            touches_y_max = touches_y_max or y == ny - 1
            touches_z_min = touches_z_min or z == 0
            touches_z_max = touches_z_max or z == nz - 1

            for dx, dy, dz in _NEIGHBOR_OFFSETS:
                neighbor_x = x + dx
                neighbor_y = y + dy
                neighbor_z = z + dz
                if not (0 <= neighbor_x < nx and 0 <= neighbor_y < ny and 0 <= neighbor_z < nz):
                    continue
                if visited[neighbor_x, neighbor_y, neighbor_z]:
                    continue
                if not pore_mask[neighbor_x, neighbor_y, neighbor_z]:
                    continue

                visited[neighbor_x, neighbor_y, neighbor_z] = True
                stack.append((neighbor_x, neighbor_y, neighbor_z))

        largest_cluster_size = max(largest_cluster_size, cluster_size)
        percolates_x = percolates_x or (touches_x_min and touches_x_max)
        percolates_y = percolates_y or (touches_y_min and touches_y_max)
        percolates_z = percolates_z or (touches_z_min and touches_z_max)

    return {
        "pore_voxel_count": int(pore_voxel_count),
        "num_pore_clusters": int(num_pore_clusters),
        "largest_pore_cluster_voxel_count": int(largest_cluster_size),
        "largest_pore_cluster_fraction_of_pores": float(largest_cluster_size / pore_voxel_count),
        "percolates_x": bool(percolates_x),
        "percolates_y": bool(percolates_y),
        "percolates_z": bool(percolates_z),
    }
