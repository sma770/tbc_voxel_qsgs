from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from tbc_voxel_qsgs.rve import load_rve_npz


def _validate_binary_3d(array: np.ndarray) -> np.ndarray:
    if array.ndim != 3:
        raise ValueError("RVE array must be 3D.")
    if not np.isin(array, [0, 1]).all():
        raise ValueError("RVE array values must be binary: 0 for pore, 1 for solid.")
    return array


def _get_selected_voxel_indices(array: np.ndarray, phase: str) -> np.ndarray:
    phase_value = 0 if phase == "pore" else 1
    return np.argwhere(array == phase_value)


def _downsample_voxels(voxels: np.ndarray, max_points: int) -> tuple[np.ndarray, bool]:
    if len(voxels) <= max_points:
        return voxels, False
    # Change the deterministic seed or sampling policy here if dense previews need
    # a different downsampling behavior.
    rng = np.random.default_rng(0)
    indices = rng.choice(len(voxels), size=max_points, replace=False)
    return voxels[indices], True


_FACE_DEFINITIONS = (
    ((-1, 0, 0), lambda x, y, z: ((x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1))),
    ((1, 0, 0), lambda x, y, z: ((x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z))),
    ((0, -1, 0), lambda x, y, z: ((x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z))),
    ((0, 1, 0), lambda x, y, z: ((x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1))),
    ((0, 0, -1), lambda x, y, z: ((x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z))),
    ((0, 0, 1), lambda x, y, z: ((x, y, z + 1), (x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y, z + 1))),
)


def _collect_exposed_faces(voxels: np.ndarray) -> list[tuple[tuple[int, int, int], ...]]:
    # QSGS-2.5: cube-based voxel rendering.
    # Build exposed voxel faces only; internal shared faces are omitted.
    selected = {tuple(int(value) for value in voxel) for voxel in voxels}
    exposed_faces = []
    for x, y, z in selected:
        for offset, face_builder in _FACE_DEFINITIONS:
            dx, dy, dz = offset
            if (x + dx, y + dy, z + dz) not in selected:
                exposed_faces.append(face_builder(x, y, z))
    return exposed_faces


def _build_mesh3d_from_faces(faces: list[tuple[tuple[int, int, int], ...]]) -> tuple[list[float], ...]:
    # Convert voxel faces to Plotly Mesh3d triangles. This intentionally keeps
    # duplicate vertices for readability.
    x_values: list[float] = []
    y_values: list[float] = []
    z_values: list[float] = []
    i_values: list[int] = []
    j_values: list[int] = []
    k_values: list[int] = []

    for face in faces:
        base_index = len(x_values)
        for x, y, z in face:
            x_values.append(float(x))
            y_values.append(float(y))
            z_values.append(float(z))
        i_values.extend((base_index, base_index))
        j_values.extend((base_index + 1, base_index + 2))
        k_values.extend((base_index + 2, base_index + 3))

    return x_values, y_values, z_values, i_values, j_values, k_values


def _cube_trace(go, faces: list[tuple[tuple[int, int, int], ...]], phase: str):
    # Rendering details:
    # - cube appearance and face behavior: _collect_exposed_faces / _build_mesh3d_from_faces
    # - color and opacity: mesh_color / mesh_opacity below
    # Previous point rendering replaced by cube surface mesh.
    mesh_color = "black" if phase == "pore" else "lightgray"
    mesh_opacity = 0.82 if phase == "pore" else 0.55
    x_values, y_values, z_values, i_values, j_values, k_values = _build_mesh3d_from_faces(faces)
    return go.Mesh3d(
        x=x_values,
        y=y_values,
        z=z_values,
        i=i_values,
        j=j_values,
        k=k_values,
        color=mesh_color,
        opacity=mesh_opacity,
        flatshading=True,
        name=phase,
    )


def _write_plotly_html(
    faces: list[tuple[tuple[int, int, int], ...]], phase: str, output_html: Path
) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise RuntimeError(
            "Plotly is required for interactive 3D preview. Install it with: pip install plotly"
        ) from exc

    trace = _cube_trace(go, faces, phase)
    figure = go.Figure(data=[trace])
    figure.update_layout(
        scene={
            "xaxis_title": "X",
            "yaxis_title": "Y",
            "zaxis_title": "Z",
            "aspectmode": "cube",
        },
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(str(output_html), include_plotlyjs=True, full_html=True)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--max-points must be a positive integer.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--max-points must be a positive integer.")
    return parsed


def build_preview(input_npz: Path, output_html: Path, phase: str, max_points: int) -> dict:
    rve, _ = load_rve_npz(input_npz)
    rve = _validate_binary_3d(rve)
    selected_voxels = _get_selected_voxel_indices(rve, phase)
    plotted_voxels, was_downsampled = _downsample_voxels(selected_voxels, max_points)
    exposed_faces = _collect_exposed_faces(plotted_voxels)
    _write_plotly_html(exposed_faces, phase, output_html)

    return {
        "voxel_shape": tuple(int(value) for value in rve.shape),
        "pore_voxel_count": int(np.count_nonzero(rve == 0)),
        "solid_voxel_count": int(np.count_nonzero(rve == 1)),
        "selected_phase_voxel_count": int(len(selected_voxels)),
        "plotted_voxel_count": int(len(plotted_voxels)),
        "exposed_face_count": int(len(exposed_faces)),
        "triangle_count": int(len(exposed_faces) * 2),
        "was_downsampled": bool(was_downsampled),
        "phase": phase,
        "max_points": int(max_points),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local interactive 3D QSGS RVE preview.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-html", required=True, type=Path)
    parser.add_argument("--phase", choices=("pore", "solid"), default="pore")
    parser.add_argument("--max-points", type=_positive_int, default=20000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_preview(args.input, args.out_html, args.phase, args.max_points)

    print(f"input npz path: {args.input}")
    print(f"output html path: {args.out_html}")
    print(f"voxel_shape: {summary['voxel_shape']}")
    print(f"number of pore voxels: {summary['pore_voxel_count']}")
    print(f"number of solid voxels: {summary['solid_voxel_count']}")
    print(f"selected phase: {summary['phase']}")
    print(f"number of selected phase voxels: {summary['selected_phase_voxel_count']}")
    print(f"number of plotted voxels: {summary['plotted_voxel_count']}")
    print(f"number of exposed faces: {summary['exposed_face_count']}")
    print(f"number of triangles: {summary['triangle_count']}")
    print(f"phase shown: {summary['phase']}")
    print(f"max_points: {summary['max_points']}")
    if summary["selected_phase_voxel_count"] == 0:
        print("selected phase has 0 voxels")
    if summary["was_downsampled"]:
        print("selected voxels were downsampled before mesh rendering")
    print("note: this is a visual sanity check, not a paper figure")


if __name__ == "__main__":
    main()
