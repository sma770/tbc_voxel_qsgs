from __future__ import annotations

from typing import Any

import numpy as np

from .rve import validate_rve_array


def compute_porosity(array: Any) -> float:
    voxels = validate_rve_array(array)
    return float(np.count_nonzero(voxels == 0) / voxels.size)
