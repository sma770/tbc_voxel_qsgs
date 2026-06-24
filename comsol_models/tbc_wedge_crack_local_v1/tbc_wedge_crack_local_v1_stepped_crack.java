/*
 * tbc_wedge_crack_local_v1_stepped_crack.java
 */

import com.comsol.model.*;
import com.comsol.model.util.*;

/** Model exported on Jun 6 2026, 17:16 by COMSOL 6.4.0.293. */
public class tbc_wedge_crack_local_v1_stepped_crack {

  public static Model run() {
    Model model = ModelUtil.create("Model");

    model.modelPath("E:\\tbc_voxel_qsgs\\comsol_models\\tbc_wedge_crack_local_v1");

    model.label("tbc_wedge_crack_local_v1");

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
    model.component("comp1").geom("geom1").feature("blk_inconel")
         .set("pos", new String[]{"0.0", "-5.05e-05", "0.0"});
    model.component("comp1").geom("geom1").feature("blk_inconel")
         .set("size", new String[]{"0.0032", "0.000101", "0.001"});
    model.component("comp1").geom("geom1").feature().create("blk_mcraly", "Block");
    model.component("comp1").geom("geom1").feature("blk_mcraly")
         .set("pos", new String[]{"0.0", "-5.05e-05", "0.001"});
    model.component("comp1").geom("geom1").feature("blk_mcraly")
         .set("size", new String[]{"0.0032", "0.000101", "0.00015"});
    model.component("comp1").geom("geom1").feature().create("blk_ysz", "Block");
    model.component("comp1").geom("geom1").feature("blk_ysz")
         .set("pos", new String[]{"0.0", "-5.05e-05", "0.00115"});
    model.component("comp1").geom("geom1").feature("blk_ysz")
         .set("size", new String[]{"0.0032", "0.000101", "0.0003"});
    model.component("comp1").geom("geom1").feature().create("cut_w30_01", "Block");
    model.component("comp1").geom("geom1").feature("cut_w30_01")
         .set("pos", new String[]{"0.0001", "-1.5e-05", "0.001445"});
    model.component("comp1").geom("geom1").feature("cut_w30_01")
         .set("size", new String[]{"0.003", "3e-05", "5e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w29_02", "Block");
    model.component("comp1").geom("geom1").feature("cut_w29_02")
         .set("pos", new String[]{"0.0001", "-1.45e-05", "0.001435"});
    model.component("comp1").geom("geom1").feature("cut_w29_02")
         .set("size", new String[]{"0.003", "2.9e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w28_03", "Block");
    model.component("comp1").geom("geom1").feature("cut_w28_03")
         .set("pos", new String[]{"0.0001", "-1.4e-05", "0.001426"});
    model.component("comp1").geom("geom1").feature("cut_w28_03")
         .set("size", new String[]{"0.003", "2.8e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w27_04", "Block");
    model.component("comp1").geom("geom1").feature("cut_w27_04")
         .set("pos", new String[]{"0.0001", "-1.35e-05", "0.001416"});
    model.component("comp1").geom("geom1").feature("cut_w27_04")
         .set("size", new String[]{"0.003", "2.7e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w26_05", "Block");
    model.component("comp1").geom("geom1").feature("cut_w26_05")
         .set("pos", new String[]{"0.0001", "-1.3e-05", "0.001406"});
    model.component("comp1").geom("geom1").feature("cut_w26_05")
         .set("size", new String[]{"0.003", "2.6e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w25_06", "Block");
    model.component("comp1").geom("geom1").feature("cut_w25_06")
         .set("pos", new String[]{"0.0001", "-1.25e-05", "0.001397"});
    model.component("comp1").geom("geom1").feature("cut_w25_06")
         .set("size", new String[]{"0.003", "2.5e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w24_07", "Block");
    model.component("comp1").geom("geom1").feature("cut_w24_07")
         .set("pos", new String[]{"0.0001", "-1.2e-05", "0.001387"});
    model.component("comp1").geom("geom1").feature("cut_w24_07")
         .set("size", new String[]{"0.003", "2.4e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w23_08", "Block");
    model.component("comp1").geom("geom1").feature("cut_w23_08")
         .set("pos", new String[]{"0.0001", "-1.15e-05", "0.001378"});
    model.component("comp1").geom("geom1").feature("cut_w23_08")
         .set("size", new String[]{"0.003", "2.3e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w22_09", "Block");
    model.component("comp1").geom("geom1").feature("cut_w22_09")
         .set("pos", new String[]{"0.0001", "-1.1e-05", "0.001368"});
    model.component("comp1").geom("geom1").feature("cut_w22_09")
         .set("size", new String[]{"0.003", "2.2e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w21_10", "Block");
    model.component("comp1").geom("geom1").feature("cut_w21_10")
         .set("pos", new String[]{"0.0001", "-1.05e-05", "0.001359"});
    model.component("comp1").geom("geom1").feature("cut_w21_10")
         .set("size", new String[]{"0.003", "2.1e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w20_11", "Block");
    model.component("comp1").geom("geom1").feature("cut_w20_11")
         .set("pos", new String[]{"0.0001", "-1e-05", "0.001349"});
    model.component("comp1").geom("geom1").feature("cut_w20_11")
         .set("size", new String[]{"0.003", "2e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w19_12", "Block");
    model.component("comp1").geom("geom1").feature("cut_w19_12")
         .set("pos", new String[]{"0.0001", "-9.5e-06", "0.00134"});
    model.component("comp1").geom("geom1").feature("cut_w19_12")
         .set("size", new String[]{"0.003", "1.9e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w18_13", "Block");
    model.component("comp1").geom("geom1").feature("cut_w18_13")
         .set("pos", new String[]{"0.0001", "-9e-06", "0.00133"});
    model.component("comp1").geom("geom1").feature("cut_w18_13")
         .set("size", new String[]{"0.003", "1.8e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w17_14", "Block");
    model.component("comp1").geom("geom1").feature("cut_w17_14")
         .set("pos", new String[]{"0.0001", "-8.5e-06", "0.00132"});
    model.component("comp1").geom("geom1").feature("cut_w17_14")
         .set("size", new String[]{"0.003", "1.7e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w16_15", "Block");
    model.component("comp1").geom("geom1").feature("cut_w16_15")
         .set("pos", new String[]{"0.0001", "-8e-06", "0.001311"});
    model.component("comp1").geom("geom1").feature("cut_w16_15")
         .set("size", new String[]{"0.003", "1.6e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w15_16", "Block");
    model.component("comp1").geom("geom1").feature("cut_w15_16")
         .set("pos", new String[]{"0.0001", "-7.5e-06", "0.001301"});
    model.component("comp1").geom("geom1").feature("cut_w15_16")
         .set("size", new String[]{"0.003", "1.5e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w14_17", "Block");
    model.component("comp1").geom("geom1").feature("cut_w14_17")
         .set("pos", new String[]{"0.0001", "-7e-06", "0.001292"});
    model.component("comp1").geom("geom1").feature("cut_w14_17")
         .set("size", new String[]{"0.003", "1.4e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w13_18", "Block");
    model.component("comp1").geom("geom1").feature("cut_w13_18")
         .set("pos", new String[]{"0.0001", "-6.5e-06", "0.001282"});
    model.component("comp1").geom("geom1").feature("cut_w13_18")
         .set("size", new String[]{"0.003", "1.3e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w12_19", "Block");
    model.component("comp1").geom("geom1").feature("cut_w12_19")
         .set("pos", new String[]{"0.0001", "-6e-06", "0.001273"});
    model.component("comp1").geom("geom1").feature("cut_w12_19")
         .set("size", new String[]{"0.003", "1.2e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w11_20", "Block");
    model.component("comp1").geom("geom1").feature("cut_w11_20")
         .set("pos", new String[]{"0.0001", "-5.5e-06", "0.001263"});
    model.component("comp1").geom("geom1").feature("cut_w11_20")
         .set("size", new String[]{"0.003", "1.1e-05", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w10_21", "Block");
    model.component("comp1").geom("geom1").feature("cut_w10_21")
         .set("pos", new String[]{"0.0001", "-5e-06", "0.001254"});
    model.component("comp1").geom("geom1").feature("cut_w10_21")
         .set("size", new String[]{"0.003", "1e-05", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w09_22", "Block");
    model.component("comp1").geom("geom1").feature("cut_w09_22")
         .set("pos", new String[]{"0.0001", "-4.5e-06", "0.001244"});
    model.component("comp1").geom("geom1").feature("cut_w09_22")
         .set("size", new String[]{"0.003", "9e-06", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w08_23", "Block");
    model.component("comp1").geom("geom1").feature("cut_w08_23")
         .set("pos", new String[]{"0.0001", "-4e-06", "0.001234"});
    model.component("comp1").geom("geom1").feature("cut_w08_23")
         .set("size", new String[]{"0.003", "8e-06", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w07_24", "Block");
    model.component("comp1").geom("geom1").feature("cut_w07_24")
         .set("pos", new String[]{"0.0001", "-3.5e-06", "0.001225"});
    model.component("comp1").geom("geom1").feature("cut_w07_24")
         .set("size", new String[]{"0.003", "7e-06", "9e-06"});
    model.component("comp1").geom("geom1").feature().create("cut_w06_25", "Block");
    model.component("comp1").geom("geom1").feature("cut_w06_25")
         .set("pos", new String[]{"0.0001", "-3e-06", "0.001215"});
    model.component("comp1").geom("geom1").feature("cut_w06_25")
         .set("size", new String[]{"0.003", "6e-06", "1e-05"});
    model.component("comp1").geom("geom1").feature().create("cut_w05_26", "Block");
    model.component("comp1").geom("geom1").feature("cut_w05_26")
         .set("pos", new String[]{"0.0001", "-2.5e-06", "0.00121"});
    model.component("comp1").geom("geom1").feature("cut_w05_26")
         .set("size", new String[]{"0.003", "5e-06", "5e-06"});
    model.component("comp1").geom("geom1").feature().create("dif_cracked_ysz", "Difference");
    model.component("comp1").geom("geom1").feature("dif_cracked_ysz").selection("input").set("blk_ysz");
    model.component("comp1").geom("geom1").feature("dif_cracked_ysz").selection("input2")
         .set("cut_w30_01", "cut_w29_02", "cut_w28_03", "cut_w27_04", "cut_w26_05", "cut_w25_06", "cut_w24_07", "cut_w23_08", "cut_w22_09", "cut_w21_10", "cut_w20_11", "cut_w19_12", "cut_w18_13", "cut_w17_14", "cut_w16_15", "cut_w15_16", "cut_w14_17", "cut_w13_18", "cut_w12_19", "cut_w11_20", "cut_w10_21", "cut_w09_22", "cut_w08_23", "cut_w07_24", "cut_w06_25", "cut_w05_26");
    model.component("comp1").geom("geom1").run();

    return model;
  }

  public static void main(String[] args) {
    run();
  }

}
