from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RVEMetadata:
    method: str = "unknown"
    target_porosity: float | None = None
    actual_porosity: float | None = None
    seed: int | None = None
    voxel_shape: tuple[int, int, int] | None = None
    physical_size_um: tuple[float, float, float] = (40.0, 40.0, 40.0)

    def __post_init__(self) -> None:
        if self.target_porosity is not None and not 0.0 <= self.target_porosity <= 1.0:
            raise ValueError("target_porosity must be None or a float between 0 and 1.")
        if self.actual_porosity is not None and not 0.0 <= self.actual_porosity <= 1.0:
            raise ValueError("actual_porosity must be None or a float between 0 and 1.")
        if len(self.physical_size_um) != 3:
            raise ValueError("physical_size_um must contain exactly three values.")
        object.__setattr__(
            self,
            "physical_size_um",
            tuple(float(value) for value in self.physical_size_um),
        )
        if self.voxel_shape is not None:
            if len(self.voxel_shape) != 3:
                raise ValueError("voxel_shape must contain exactly three values.")
            object.__setattr__(
                self,
                "voxel_shape",
                tuple(int(value) for value in self.voxel_shape),
            )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, value: str | bytes | np.ndarray) -> "RVEMetadata":
        if isinstance(value, np.ndarray):
            value = value.item()
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        payload = json.loads(value)
        return cls(**payload)


def validate_rve_array(array: Any) -> np.ndarray:
    voxels = np.asarray(array)
    if voxels.ndim != 3:
        raise ValueError("RVE array must be 3D.")

    if voxels.dtype == np.bool_:
        return voxels.astype(np.uint8)

    if not np.isin(voxels, [0, 1]).all():
        raise ValueError("RVE array values must be binary: 0 for pore, 1 for solid.")

    return voxels.astype(np.uint8, copy=False)


def _porosity_from_validated(voxels: np.ndarray) -> float:
    return float(np.count_nonzero(voxels == 0) / voxels.size)


def _metadata_with_array_values(metadata: RVEMetadata, voxels: np.ndarray) -> RVEMetadata:
    return replace(
        metadata,
        actual_porosity=_porosity_from_validated(voxels),
        voxel_shape=tuple(int(value) for value in voxels.shape),
    )


def save_rve_npz(path: str | Path, array: Any, metadata: RVEMetadata) -> None:
    voxels = validate_rve_array(array)
    metadata_to_save = _metadata_with_array_values(metadata, voxels)
    np.savez_compressed(
        Path(path),
        voxels=voxels,
        metadata_json=np.array(metadata_to_save.to_json()),
    )


def load_rve_npz(path: str | Path) -> tuple[np.ndarray, RVEMetadata]:
    with np.load(Path(path), allow_pickle=False) as data:
        voxels = validate_rve_array(data["voxels"])
        metadata = RVEMetadata.from_json(data["metadata_json"])

    return voxels, _metadata_with_array_values(metadata, voxels)
