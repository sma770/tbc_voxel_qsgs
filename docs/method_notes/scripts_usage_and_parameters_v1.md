# 脚本用途与参数修改说明 v1

本文档说明 `scripts/` 目录下当前已有 Python 脚本的用途、输入输出、常用命令，以及后续修改参数时应该改哪里。

这些脚本主要用于工程 smoke workflow、sanity check 和最小统计闭环。SVG/HTML 预览均为本地人工检查用途，不是论文图，不是正式后处理结果图。

## 1. 总体约定

项目统一使用二值 RVE：

- `0 = pore phase`
- `1 = solid 8YSZ phase`

通常需要区分三类参数：

- 生成参数：在 `configs/*.json` 中修改，例如 `target_porosity`、`voxel_shape`、`core_probability`、`correlation_lengths_um`。
- 命令行参数：运行脚本时传入，例如 `--input`、`--out`、`--out-dir`、`--phase`、`--max-points`。
- 显示样式：在脚本内部修改，例如 SVG 的 `cell_size`、黑白颜色、HTML 预览的 `mesh_color` 和 `mesh_opacity`。

## 2. 当前脚本总览

| 脚本 | 主要用途 | 输入 | 输出 |
|---|---|---|---|
| `smoke_rve_io.py` | 手工确定性 RVE IO smoke | config JSON | `.npz` |
| `smoke_grf_rve.py` | GRF RVE 生成并保存/读取 | config JSON | `.npz` |
| `export_grf_slices.py` | 导出单个 GRF RVE 的中间切片 | config JSON | 3 个 SVG |
| `compare_grf_iso_aniso_slices.py` | 固定两组 GRF 参数的切片对比 | config JSON | 6 个 SVG |
| `compare_grf_morphology.py` | 固定两组 GRF 参数的形貌 summary 对比 | config JSON | comparison JSON |
| `summarize_rve_morphology.py` | 从 `.npz` 读取 RVE 并输出形貌 summary | RVE `.npz` | summary JSON |
| `smoke_qsgs_rve.py` | QSGS RVE 生成、保存、读取、切片 | QSGS config JSON | `.npz` + 3 个 SVG |
| `preview_qsgs_3d.py` | 读取 QSGS `.npz` 并生成 3D HTML 预览 | RVE `.npz` | interactive HTML |

## 3. 常用命令

### 3.1 QSGS smoke 与切片检查

```powershell
python scripts/smoke_qsgs_rve.py --config configs/qsgs_2_smoke_and_slices.json --out qsgs_2_smoke_rve.npz --slice-dir qsgs_2_slices_preview
```

含义：

- `--config`：QSGS 生成参数。
- `--out`：保存生成的 RVE `.npz`。
- `--slice-dir`：保存 `qsgs_slice_xy.svg`、`qsgs_slice_xz.svg`、`qsgs_slice_yz.svg`。

QSGS 生成参数在哪里改：

- `configs/qsgs_2_smoke_and_slices.json`
- `target_porosity`：目标孔隙率。
- `core_probability`：QSGS 初始固相核心概率 `Pc`。
- `direction_probabilities`：`D1` 到 `D26` 的方向生长概率。
- `voxel_shape`：体素网格尺寸，目前正式 smoke 使用 `[40, 40, 40]`。

### 3.2 QSGS 3D HTML 预览

```powershell
python scripts/preview_qsgs_3d.py --input qsgs_2_smoke_rve.npz --out-html qsgs_2_3d_preview.html --phase pore --max-points 20000
```

含义：

- `--input`：读取已经保存好的 RVE `.npz`。
- `--out-html`：输出可交互旋转、缩放、平移的 HTML。
- `--phase pore`：显示孔隙相，也就是 array 中的 `0`。
- `--phase solid`：显示实体相，也就是 array 中的 `1`。
- `--max-points`：最多参与 mesh rendering 的 voxel 数；超过时会固定随机种子下采样。

注意：`preview_qsgs_3d.py` 不读取 QSGS config，也不会修改孔隙率。孔隙率要在生成 `.npz` 之前修改 config。

QSGS 3D 显示样式在哪里改：

- 颜色和透明度：`scripts/preview_qsgs_3d.py` 中 `_cube_trace()` 的 `mesh_color` 和 `mesh_opacity`。
- 外露面判断：`_collect_exposed_faces()`。
- 面片转三角形：`_build_mesh3d_from_faces()`。
- 最大渲染数和下采样策略：`_downsample_voxels()`。

### 3.3 GRF smoke

```powershell
python scripts/smoke_grf_rve.py --config configs/m2_3_grf_smoke.json --out m2_3_grf_smoke_rve.npz
```

GRF 参数在哪里改：

- `configs/m2_3_grf_smoke.json`
- `target_porosity`：目标孔隙率。
- `correlation_lengths_um`：各向异性相关长度。
- `voxel_shape`：体素网格尺寸。
- `seed`：随机种子。

### 3.4 GRF 切片 sanity check

```powershell
python scripts/export_grf_slices.py --config configs/m2_4_grf_slices.json --out-dir m2_4_grf_slices_preview
```

SVG 显示样式在哪里改：

- `scripts/export_grf_slices.py` 中 `_write_binary_slice_svg()`。
- `cell_size` 控制每个 voxel 方块在 SVG 中的像素大小。
- `fill = "black"` 表示 pore，`fill = "white"` 表示 solid。

### 3.5 GRF isotropic vs anisotropic 切片对比

```powershell
python scripts/compare_grf_iso_aniso_slices.py --config configs/m2_5_grf_iso_vs_aniso.json --out-dir m2_5_grf_iso_vs_aniso_preview
```

该脚本只做固定两组参数的 visual sanity check，不输出科学结论。

### 3.6 形貌 summary

```powershell
python scripts/summarize_rve_morphology.py --input qsgs_2_smoke_rve.npz --out qsgs_2_morphology_summary.json
```

输出字段包括：

- `actual_porosity`
- `solid_fraction`
- `pore_voxel_count`
- `solid_voxel_count`
- `num_pore_clusters`
- `largest_pore_cluster_voxel_count`
- `percolates_x`
- `percolates_y`
- `percolates_z`

该脚本只包含基础体素统计和最小 pore connectivity，不包含孔径分布、表面积、各向异性指数。

### 3.7 GRF morphology comparison

```powershell
python scripts/compare_grf_morphology.py --config configs/m3_3_grf_morphology_compare.json --out m3_3_grf_morphology_compare_preview.json
```

该脚本在内存中生成两个 GRF RVE 并输出 comparison JSON，不保存中间 `.npz`。

## 4. 临时文件清理

手动预览后建议删除临时结果，避免误提交：

```powershell
Remove-Item qsgs_2_smoke_rve.npz
Remove-Item -Recurse -Force qsgs_2_slices_preview
Remove-Item qsgs_2_3d_preview.html
```

GRF 预览目录或 JSON 结果也应按实际文件名删除。

## 5. 当前边界

当前脚本不做以下内容：

- 不生成论文图。
- 不做 QSGS-vs-GRF 正式结论。
- 不实现 AHM、PBC、COMSOL 或 FEM。
- 不做大规模参数扫描。
- 不实现高级 morphology metrics，例如孔径分布、表面积、各向异性指数。

这些内容应在后续明确任务中单独实现。
