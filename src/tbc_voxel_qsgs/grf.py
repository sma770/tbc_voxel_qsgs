from __future__ import annotations

from typing import Sequence

import numpy as np


def _validate_shape(values: Sequence[int], name: str) -> tuple[int, int, int]:
    try:
        result = tuple(int(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a sequence of three positive integers.") from exc

    if len(result) != 3 or any(value <= 0 for value in result):
        raise ValueError(f"{name} must be a sequence of three positive integers.")
    return result


def _validate_positive_triplet(values: Sequence[float], name: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a sequence of three positive numbers.") from exc

    if len(result) != 3 or any(value <= 0.0 for value in result):
        raise ValueError(f"{name} must be a sequence of three positive numbers.")
    return result


def _validate_target_porosity(value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("target_porosity must be a number between 0 and 1.") from exc

    if not 0.0 <= result <= 1.0:
        raise ValueError("target_porosity must be a number between 0 and 1.")
    return result


def _make_anisotropic_filter(
    voxel_shape: tuple[int, int, int],
    correlation_lengths_um: tuple[float, float, float],
    physical_size_um: tuple[float, float, float],
) -> np.ndarray:
    frequencies = [
        np.fft.fftfreq(n=voxel_shape[axis], d=physical_size_um[axis] / voxel_shape[axis])
        for axis in range(3)
    ]
    kx, ky, kz = np.meshgrid(*frequencies, indexing="ij")
    lx, ly, lz = correlation_lengths_um
    exponent = -0.5 * ((kx * lx) ** 2 + (ky * ly) ** 2 + (kz * lz) ** 2)
    return np.exp(exponent)


def generate_anisotropic_grf_rve(
    voxel_shape,
    target_porosity,
    correlation_lengths_um,
    physical_size_um,
    seed,
):
    shape = _validate_shape(voxel_shape, "voxel_shape")
    porosity = _validate_target_porosity(target_porosity)
    corr_lengths = _validate_positive_triplet(correlation_lengths_um, "correlation_lengths_um")
    size_um = _validate_positive_triplet(physical_size_um, "physical_size_um")

    try:
        rng = np.random.default_rng(seed)
    except TypeError as exc:
        raise ValueError("seed must be usable by numpy.random.default_rng.") from exc

    total_voxels = int(np.prod(shape))
    num_pores = round(porosity * total_voxels)

    if num_pores == 0:
        return np.ones(shape, dtype=np.uint8)
    if num_pores == total_voxels:
        return np.zeros(shape, dtype=np.uint8)

    white_noise = rng.standard_normal(shape)
    spectral_filter = _make_anisotropic_filter(shape, corr_lengths, size_um)
    smoothed_field = np.fft.ifftn(np.fft.fftn(white_noise) * spectral_filter).real

    rve = np.ones(total_voxels, dtype=np.uint8)
    pore_indices = np.argpartition(smoothed_field.reshape(-1), num_pores - 1)[:num_pores]
    rve[pore_indices] = 0
    return rve.reshape(shape)
