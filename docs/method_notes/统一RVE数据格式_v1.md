# 统一 RVE 数据格式 v1

生成日期：2026-06-09

当前用途：为后续 `QSGS`、`simple random voxel`、`anisotropic correlated voxel method` 输出建立统一 binary RVE 接口。该格式先服务于微结构生成与形貌指标，后续再接入 `AHM/PBC` 均匀化。

## 1. 核心约定

统一输出为三维二值体素数组：

```text
array name: rve_zyx
array order: z, y, x
shape: (Nz, Ny, Nx)
dtype: uint8

0 = pore
1 = solid phase / 8YSZ
```

注意：论文讨论中常按 `(x, y, z)` 描述物理尺寸；Python 数组中采用 `(z, y, x)`，因为 NumPy 切片和图像显示更自然。metadata 中必须同时记录：

```text
grid_shape_xyz = [Nx, Ny, Nz]
array.shape_zyx = [Nz, Ny, Nx]
rve_size_um_xyz = [Lx, Ly, Lz]
voxel_size_um_xyz = [dx, dy, dz]
```

## 2. 文件组织

推荐路径：

```text
data/processed/rve/<method>/<case_id>.npz
data/metadata/rve/<method>/<case_id>_metadata.json
results/figures/rve_preview/<method>/<case_id>_slices.png
results/logs/rve_generation/<batch_id>_summary.csv
results/logs/rve_generation/<batch_id>_summary.json
```

说明：

- `.npz` 保存 `rve_zyx` 和内嵌 `metadata_json`。
- `.json` 保存同一份 metadata，便于不用读取大数组也能查参数。
- `.png` 是三方向中截面预览图，只用于检查形貌，不作为定量结果。
- `summary.csv/json` 汇总批量生成结果。

## 3. Metadata 字段

最小 metadata 应包含：

```text
schema_version
case_id
method
generated_at_utc
config_path
array_path
metadata_path
figure_paths
phase_convention
array
geometry
porosity
random
generation_parameters
runtime_seconds
validation
known_limitations
```

关键字段含义：

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前为 `rve-binary-voxel-v1` |
| `case_id` | 唯一算例编号 |
| `method` | 生成方法，例如 `simple_random` 或 `anisotropic_correlated` |
| `phase_convention` | 固定为 `0=pore`, `1=solid` |
| `geometry.rve_size_um_xyz` | RVE 物理尺寸，单位 `um` |
| `geometry.grid_shape_xyz` | 体素网格数，按 `x,y,z` 记录 |
| `geometry.voxel_size_um_xyz` | 单个体素物理尺寸 |
| `porosity.target` | 目标孔隙率 |
| `porosity.actual` | 实际孔隙率 |
| `random.seed` | 随机种子 |
| `generation_parameters` | 当前方法的参数表 |

## 4. 最小生成器

当前入口：

```powershell
python src/microstructure/generate_voxel_rve.py --config configs/voxel_rve_minimal_v1.json
```

可只运行某个算例：

```powershell
python src/microstructure/generate_voxel_rve.py --config configs/voxel_rve_minimal_v1.json --case-id anisotropic_correlated_p10_seed20260609
```

当前支持两种方法：

| 方法 | 含义 | 论文定位 |
| --- | --- | --- |
| `simple_random` | 随机场独立取值后按目标孔隙率选出 pore voxel | 低级对照 |
| `anisotropic_correlated` | 标准正态随机场 -> 各向异性 Gaussian filter -> 按目标孔隙率阈值化 | 本文 voxel method 雏形 |

`anisotropic_correlated` 的当前核心参数：

```text
correlation_length_um_xyz = [lx, ly, lz]
```

它通过不同方向的相关长度表达方向性。当前配置示例使用：

```text
correlation_length_um_xyz = [1.5, 1.5, 5.0]
```

这表示 z 方向相关长度更长，用于模拟柱状方向更强的相关结构。这里的方向定义还需要结合原文坐标和师兄代码确认。

## 5. 与 AHM 的接口关系

AHM 或有限元均匀化阶段只应依赖统一接口：

```text
输入：rve_zyx, metadata
相约定：0 = pore, 1 = solid
材料参数：由 AHM 配置单独给定，例如 E=48 GPa, nu=0.12
边界条件：由 AHM/PBC 脚本单独给定
输出：effective mechanical properties
```

当前格式没有规定孔隙相在有限元中如何处理。后续需要确认：

- 孔隙相是否删除单元。
- 是否赋予极低刚度材料。
- 是否通过空洞边界处理。
- 是否需要从 voxel RVE 转换成 hexahedral mesh。

这些选择会影响等效力学性能，不能在论文中含糊处理。

## 6. 检查标准

每个生成结果至少检查：

1. `rve_zyx` 是否为 3D。
2. 数组值是否只包含 `0` 和 `1`。
3. `actual_porosity` 是否接近 `target_porosity`。
4. `grid_shape_xyz` 与 `array.shape_zyx` 是否对应。
5. `seed`、`method`、`parameters` 是否写入 metadata。
6. 切片图是否能看出结构合理，不出现全黑、全白或轴向混乱。

## 7. 下一步

该格式完成后，推荐继续做：

1. 读取 `.npz` 的 smoke check。
2. 增加形貌指标最小集：孔隙率、连通分量、最大孔隙连通域比例、表面积/体积比。
3. 将师兄提供的 QSGS 输出转换成同一格式。
4. 对相同 `target_porosity` 和 `grid_shape_xyz` 的 QSGS 与 voxel RVE 做形貌对比。
