"""Shared IO helpers for binary voxel RVE data.

Canonical convention:
    rve_zyx[z, y, x], uint8, 0 = pore, 1 = solid.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "rve-binary-voxel-v1"
PHASE_CONVENTION = {"0": "pore", "1": "solid"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def validate_binary_rve(rve_zyx: np.ndarray) -> None:
    if rve_zyx.ndim != 3:
        raise ValueError(f"RVE array must be 3D, got ndim={rve_zyx.ndim}")

    values = np.unique(rve_zyx)
    unexpected = [int(value) for value in values if int(value) not in (0, 1)]
    if unexpected:
        raise ValueError(f"RVE array must contain only 0/1 labels, got {unexpected}")


def porosity(rve_zyx: np.ndarray) -> float:
    validate_binary_rve(rve_zyx)
    return float(np.count_nonzero(rve_zyx == 0) / rve_zyx.size)


def phase_counts(rve_zyx: np.ndarray) -> dict[str, int]:
    validate_binary_rve(rve_zyx)
    pore_count = int(np.count_nonzero(rve_zyx == 0))
    solid_count = int(np.count_nonzero(rve_zyx == 1))
    return {"0": pore_count, "1": solid_count}


def save_rve_case(
    rve_zyx: np.ndarray,
    metadata: dict[str, Any],
    array_path: Path,
    metadata_path: Path,
) -> None:
    validate_binary_rve(rve_zyx)
    array_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
    np.savez_compressed(
        array_path,
        rve_zyx=rve_zyx.astype(np.uint8, copy=False),
        metadata_json=np.array(metadata_json),
    )
    write_json(metadata_path, metadata)


def load_rve_case(array_path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    with np.load(array_path, allow_pickle=False) as data:
        rve_zyx = data["rve_zyx"].astype(np.uint8, copy=False)
        metadata = json.loads(str(data["metadata_json"]))

    validate_binary_rve(rve_zyx)
    return rve_zyx, metadata
