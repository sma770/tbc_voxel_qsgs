"""Create a COMSOL model with a continuous wedge-shaped crack.

This script uses the Python `mph` package to drive COMSOL's Java API.
It creates the same local three-layer TBC domain as the voxel model, but
cuts the YSZ layer with a continuous trapezoid-extruded wedge void instead
of the 1 um stepped block approximation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import mph


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def um(value: float) -> float:
    return value * 1e-6


def mm(value: float) -> float:
    return value * 1e-3


def as_str(value: float) -> str:
    return f"{value:.12g}"


def set_param(model: mph.Model, name: str, value: str, description: str) -> None:
    model.java.param().set(name, value)
    model.java.param().set(name, value, description)


def add_block(geom: Any, tag: str, pos: list[float], size: list[float]) -> None:
    geom.feature().create(tag, "Block")
    geom.feature(tag).set("pos", [as_str(x) for x in pos])
    geom.feature(tag).set("size", [as_str(x) for x in size])


def build_model(config: dict[str, Any], output_dir: Path, cores: int) -> tuple[Path, Path]:
    client = mph.start(cores=cores)
    model = client.create("tbc_wedge_crack_local_v1_smooth")
    model.java.label("tbc_wedge_crack_local_v1_smooth")
    model.java.modelPath(str(output_dir.resolve()))

    model.java.component().create("comp1", True)
    model.java.component("comp1").geom().create("geom1", 3)
    geom = model.java.component("comp1").geom("geom1")

    domain = config["domain_um"]
    layers = config["layers"]
    crack = config["crack"]

    x_len = um(float(domain["x"]))
    y_len = um(float(domain["y"]))
    substrate_t = um(float(layers[0]["thickness_um"]))
    bond_t = um(float(layers[1]["thickness_um"]))
    ysz_t = um(float(layers[2]["thickness_um"]))
    bond_top = substrate_t + bond_t
    ceramic_top = bond_top + ysz_t

    crack_len = um(float(crack["length_um"]))
    crack_x0 = (x_len - crack_len) / 2.0
    crack_top_half = um(float(crack["top_width_um"])) / 2.0
    crack_bot_half = um(float(crack["bottom_width_um"])) / 2.0
    crack_depth = um(float(crack["depth_um"]))
    crack_bottom = ceramic_top - crack_depth

    set_param(model, "Lx", "3.2[mm]", "Local model length in crack direction")
    set_param(model, "Ly", "101[um]", "Local model width across crack opening")
    set_param(model, "t_sub", "1[mm]", "Inconel substrate thickness")
    set_param(model, "t_bond", "0.15[mm]", "MCrAlY bond coat thickness")
    set_param(model, "t_ysz", "0.3[mm]", "YSZ ceramic top coat thickness")
    set_param(model, "crack_len", "3[mm]", "Wedge crack length")
    set_param(model, "crack_w_top", "0.03[mm]", "Crack opening width at top surface")
    set_param(model, "crack_w_bot", "0.005[mm]", "Crack bottom width")
    set_param(model, "crack_depth", "0.24[mm]", "Crack depth in YSZ layer")
    set_param(model, "ysz_ligament", "0.06[mm]", "YSZ ligament left above bond coat")

    add_block(
        geom,
        "blk_inconel",
        [0.0, -y_len / 2.0, 0.0],
        [x_len, y_len, substrate_t],
    )
    add_block(
        geom,
        "blk_mcraly",
        [0.0, -y_len / 2.0, substrate_t],
        [x_len, y_len, bond_t],
    )
    add_block(
        geom,
        "blk_ysz",
        [0.0, -y_len / 2.0, bond_top],
        [x_len, y_len, ysz_t],
    )

    # Draw the wedge cross-section in a Y-Z work plane located at crack_x0,
    # then extrude it along +X for the crack length.
    geom.feature().create("wp_crack_yz", "WorkPlane")
    wp = geom.feature("wp_crack_yz")
    wp.set("planetype", "quick")
    wp.set("quickplane", "yz")
    wp.set("quickx", as_str(crack_x0))
    wp.geom().feature().create("pol_crack_yz", "Polygon")
    polygon = wp.geom().feature("pol_crack_yz")
    polygon.set("type", "solid")
    polygon.set(
        "x",
        [
            as_str(-crack_top_half),
            as_str(crack_top_half),
            as_str(crack_bot_half),
            as_str(-crack_bot_half),
        ],
    )
    polygon.set(
        "y",
        [
            as_str(ceramic_top),
            as_str(ceramic_top),
            as_str(crack_bottom),
            as_str(crack_bottom),
        ],
    )

    geom.feature().create("ext_crack", "Extrude")
    ext = geom.feature("ext_crack")
    ext.set("extrudefrom", "workplane")
    ext.set("workplane", "wp_crack_yz")
    ext.selection("input").set("wp_crack_yz")
    ext.set("distance", as_str(crack_len))
    ext.set("reverse", "off")

    geom.feature().create("dif_cracked_ysz", "Difference")
    diff = geom.feature("dif_cracked_ysz")
    diff.selection("input").set("blk_ysz")
    diff.selection("input2").set("ext_crack")

    geom.run()

    included_angle = math.degrees(
        2.0
        * math.atan(
            (float(crack["top_width_um"]) - float(crack["bottom_width_um"]))
            / (2.0 * float(crack["depth_um"]))
        )
    )
    model.java.description(
        "Continuous wedge crack local TBC geometry. "
        f"Included angle from widths/depth = {included_angle:.4f} deg. "
        "Geometry only: materials, mesh, boundary conditions, and studies are not finalized."
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    mph_path = output_dir / "tbc_wedge_crack_local_v1_smooth_crack.mph"
    java_path = output_dir / "tbc_wedge_crack_local_v1_smooth_crack.java"
    model.save(mph_path)
    model.save(java_path)
    return mph_path, java_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/tbc_wedge_crack_local_v1.json")
    parser.add_argument(
        "--output-dir",
        default="comsol_models/tbc_wedge_crack_local_v1",
        help="Directory for the generated .mph and .java files.",
    )
    parser.add_argument("--cores", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = read_json(Path(args.config))
    mph_path, java_path = build_model(config, Path(args.output_dir), args.cores)
    print(f"saved_mph: {mph_path}")
    print(f"saved_java: {java_path}")


if __name__ == "__main__":
    main()
