/*
 * tbc_wedge_crack_local_v1_smooth_crack.java
 */

import com.comsol.model.*;
import com.comsol.model.util.*;

/** Model exported on Jun 8 2026, 15:16 by COMSOL 6.4.0.293. */
public class tbc_wedge_crack_local_v1_smooth_crack {

  public static Model run() {
    Model model = ModelUtil.create("Model");

    model.label("tbc_wedge_crack_local_v1_smooth");
    model.label("tbc_wedge_crack_local_v1_smooth");

    model.modelPath("E:\\tbc_voxel_qsgs\\comsol_models\\tbc_wedge_crack_local_v1");

    model.component().create("comp1", true);

    model.component("comp1").geom().create("geom1", 3);

    model.param().set("Lx", "3.2[mm]");
    model.param().set("Lx", "3.2[mm]", "Local model length in crack direction");
    model.param().set("Ly", "101[um]");
    model.param().set("Ly", "101[um]", "Local model width across crack opening");
    model.param().set("t_sub", "1[mm]");
    model.param().set("t_sub", "1[mm]", "Inconel substrate thickness");
    model.param().set("t_bond", "0.15[mm]");
    model.param().set("t_bond", "0.15[mm]", "MCrAlY bond coat thickness");
    model.param().set("t_ysz", "0.3[mm]");
    model.param().set("t_ysz", "0.3[mm]", "YSZ ceramic top coat thickness");
    model.param().set("crack_len", "3[mm]");
    model.param().set("crack_len", "3[mm]", "Wedge crack length");
    model.param().set("crack_w_top", "0.03[mm]");
    model.param().set("crack_w_top", "0.03[mm]", "Crack opening width at top surface");
    model.param().set("crack_w_bot", "0.005[mm]");
    model.param().set("crack_w_bot", "0.005[mm]", "Crack bottom width");
    model.param().set("crack_depth", "0.24[mm]");
    model.param().set("crack_depth", "0.24[mm]", "Crack depth in YSZ layer");
    model.param().set("ysz_ligament", "0.06[mm]");
    model.param().set("ysz_ligament", "0.06[mm]", "YSZ ligament left above bond coat");

    model.component("comp1").geom("geom1").feature().create("blk_inconel", "Block");
    model.component("comp1").geom("geom1").feature("blk_inconel").set("pos", new String[]{"0", "-5.05e-05", "0"});
    model.component("comp1").geom("geom1").feature("blk_inconel")
         .set("size", new String[]{"0.0032", "0.000101", "0.001"});
    model.component("comp1").geom("geom1").feature().create("blk_mcraly", "Block");
    model.component("comp1").geom("geom1").feature("blk_mcraly").set("pos", new String[]{"0", "-5.05e-05", "0.001"});
    model.component("comp1").geom("geom1").feature("blk_mcraly")
         .set("size", new String[]{"0.0032", "0.000101", "0.00015"});
    model.component("comp1").geom("geom1").feature().create("blk_ysz", "Block");
    model.component("comp1").geom("geom1").feature("blk_ysz").set("pos", new String[]{"0", "-5.05e-05", "0.00115"});
    model.component("comp1").geom("geom1").feature("blk_ysz")
         .set("size", new String[]{"0.0032", "0.000101", "0.0003"});
    model.component("comp1").geom("geom1").feature().create("wp_crack_yz", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").set("planetype", "quick");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").set("quickplane", "yz");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").set("quickx", "0.0001");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").geom().feature().create("pol_crack_yz", "Polygon");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").geom().feature("pol_crack_yz")
         .set("type", "solid");
    model.component("comp1").geom("geom1").feature("wp_crack_yz").geom().feature("pol_crack_yz")
         .set("x", new String[]{"-1.5e-05", "1.5e-05", "2.5e-06", "-2.5e-06"});
    model.component("comp1").geom("geom1").feature("wp_crack_yz").geom().feature("pol_crack_yz")
         .set("y", new String[]{"0.00145", "0.00145", "0.00121", "0.00121"});
    model.component("comp1").geom("geom1").feature().create("ext_crack", "Extrude");
    model.component("comp1").geom("geom1").feature("ext_crack").set("extrudefrom", "workplane");
    model.component("comp1").geom("geom1").feature("ext_crack").set("workplane", "wp_crack_yz");
    model.component("comp1").geom("geom1").feature("ext_crack").selection("input").set("wp_crack_yz");
    model.component("comp1").geom("geom1").feature("ext_crack").set("distance", "0.003");
    model.component("comp1").geom("geom1").feature("ext_crack").set("reverse", "off");
    model.component("comp1").geom("geom1").feature().create("dif_cracked_ysz", "Difference");
    model.component("comp1").geom("geom1").feature("dif_cracked_ysz").selection("input").set("blk_ysz");
    model.component("comp1").geom("geom1").feature("dif_cracked_ysz").selection("input2").set("ext_crack");
    model.component("comp1").geom("geom1").run();

    model
         .description("Continuous wedge crack local TBC geometry. Included angle from widths/depth = 5.9629 deg. Geometry only: materials, mesh, boundary conditions, and studies are not finalized.");

    return model;
  }

  public static void main(String[] args) {
    run();
  }

}
