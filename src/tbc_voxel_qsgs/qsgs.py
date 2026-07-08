from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


QSGS_DIRECTION_OFFSETS = {
    "D1": (+1, 0, 0),
    "D2": (0, -1, 0),
    "D3": (-1, 0, 0),
    "D4": (0, +1, 0),
    "D5": (0, 0, +1),
    "D6": (0, 0, -1),
    "D7": (+1, -1, 0),
    "D8": (-1, -1, 0),
    "D9": (-1, +1, 0),
    "D10": (+1, +1, 0),
    "D11": (+1, 0, +1),
    "D12": (+1, 0, -1),
    "D13": (-1, 0, -1),
    "D14": (-1, 0, +1),
    "D15": (0, -1, +1),
    "D16": (0, -1, -1),
    "D17": (0, +1, -1),
    "D18": (0, +1, +1),
    "D19": (-1, +1, -1),
    "D20": (-1, +1, +1),
    "D21": (-1, -1, +1),
    "D22": (-1, -1, -1),
    "D23": (+1, -1, +1),
    "D24": (+1, -1, -1),
    "D25": (+1, +1, +1),
    "D26": (+1, +1, -1),
}


def _validate_voxel_shape(values: Sequence[Any]) -> tuple[int, int, int]:
    try:
        shape = tuple(values)
    except TypeError as exc:
        raise ValueError("voxel_shape must be a sequence of three positive integers.") from exc
    if len(shape) != 3:
        raise ValueError("voxel_shape must be a sequence of three positive integers.")
    if not all(isinstance(value, (int, np.integer)) and int(value) > 0 for value in shape):
        raise ValueError("voxel_shape must be a sequence of three positive integers.")
    return tuple(int(value) for value in shape)


def _validate_probability(value: Any, name: str) -> float:
    try:
        probability = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a probability between 0 and 1.") from exc
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"{name} must be a probability between 0 and 1.")
    return probability


def _validate_direction_probabilities(values: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise ValueError("direction_probabilities must be a mapping with keys D1 through D26.")
    expected_keys = set(QSGS_DIRECTION_OFFSETS)
    actual_keys = set(values)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        raise ValueError(
            "direction_probabilities must contain exactly D1 through D26; "
            f"missing={missing}, extra={extra}."
        )
    return {key: _validate_probability(values[key], key) for key in QSGS_DIRECTION_OFFSETS}


def _validate_max_iterations(value: Any) -> int:
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool) or int(value) <= 0:
        raise ValueError("max_iterations must be a positive integer.")
    return int(value)


def _validate_seed(seed: Any) -> np.random.Generator:
    try:
        return np.random.default_rng(seed)
    except (TypeError, ValueError) as exc:
        raise ValueError("seed must be usable by numpy.random.default_rng.") from exc


def _target_solid_count(target_porosity: float, total_voxel_count: int) -> int:
    return int(round((1.0 - target_porosity) * total_voxel_count))


def _random_keep_indices(indices: np.ndarray, keep_count: int, rng: np.random.Generator) -> np.ndarray:
    if keep_count == 0:
        return np.empty((0, 3), dtype=int)
    selected = rng.choice(len(indices), size=keep_count, replace=False)
    return indices[selected]


def generate_qsgs_rve(
    voxel_shape,
    target_porosity,
    core_probability,
    direction_probabilities,
    seed,
    max_iterations=10000,
):
    """Generate a binary solid/pore minimal QSGS baseline RVE.

    QSGS-1 is a binary solid-growth engineering baseline and does not include Pirm.
    """
    shape = _validate_voxel_shape(voxel_shape)
    porosity = _validate_probability(target_porosity, "target_porosity")
    core_probability = _validate_probability(core_probability, "core_probability")
    direction_probabilities = _validate_direction_probabilities(direction_probabilities)
    max_iterations = _validate_max_iterations(max_iterations)
    rng = _validate_seed(seed)

    total_voxel_count = int(np.prod(shape))
    target_solid_count = _target_solid_count(porosity, total_voxel_count)

    if target_solid_count == 0:
        return np.zeros(shape, dtype=np.uint8)
    if target_solid_count == total_voxel_count:
        return np.ones(shape, dtype=np.uint8)

    rve = (rng.random(shape) < core_probability).astype(np.uint8)
    solid_count = int(np.count_nonzero(rve))

    if solid_count == 0:
        flat_index = int(rng.integers(total_voxel_count))
        rve.reshape(-1)[flat_index] = 1
        solid_count = 1

    if solid_count > target_solid_count:
        solid_indices = np.argwhere(rve == 1)
        kept_indices = _random_keep_indices(solid_indices, target_solid_count, rng)
        rve.fill(0)
        if len(kept_indices):
            rve[tuple(kept_indices.T)] = 1
        return rve.astype(np.uint8, copy=False)

    for _ in range(max_iterations):
        if solid_count >= target_solid_count:
            return rve.astype(np.uint8, copy=False)

        candidates: set[tuple[int, int, int]] = set()
        for solid_position in np.argwhere(rve == 1):
            x, y, z = (int(value) for value in solid_position)
            for direction, offset in QSGS_DIRECTION_OFFSETS.items():
                dx, dy, dz = offset
                nx = x + dx
                ny = y + dy
                nz = z + dz
                if not (0 <= nx < shape[0] and 0 <= ny < shape[1] and 0 <= nz < shape[2]):
                    continue
                if rve[nx, ny, nz] == 1:
                    continue
                if rng.random() < direction_probabilities[direction]:
                    candidates.add((nx, ny, nz))

        if not candidates:
            raise RuntimeError(
                "QSGS growth stalled before reaching target solid count; "
                "increase probabilities or max_iterations."
            )

        needed = target_solid_count - solid_count
        candidate_list = sorted(candidates)
        if len(candidate_list) > needed:
            selected = rng.choice(len(candidate_list), size=needed, replace=False)
            candidate_list = [candidate_list[int(index)] for index in selected]

        xs, ys, zs = zip(*candidate_list)
        rve[xs, ys, zs] = 1
        solid_count = int(np.count_nonzero(rve))

    raise RuntimeError("QSGS reached max_iterations before reaching target solid count.")
