# TBC wedge crack COMSOL model v1

本目录保存老师给出的三层 TBC 楔形裂纹子任务的第一版 COMSOL 模型。

## 文件

- `tbc_wedge_crack_local_v1_smooth_crack.mph`：连续斜壁楔形裂纹 COMSOL 6.4 模型，推荐作为后续力学分析起点。
- `tbc_wedge_crack_local_v1_smooth_crack.java`：连续楔形模型的 Java 源文件，可用于复现模型。
- `tbc_wedge_crack_local_v1_stepped_crack.mph`：旧版阶梯式楔形裂纹模型，用于和 `1 um` 体素分组结果对照。
- `tbc_wedge_crack_local_v1_stepped_crack.java`：旧版阶梯模型的 Java 源文件。

## 模型定义

- 局部模型尺寸：`3.2 mm x 101 um x 1.45 mm`。
- 三层结构：
  - `Inconel substrate`：`1.00 mm`
  - `MCrAlY bond coat`：`0.15 mm`
  - `YSZ ceramic top coat`：`0.30 mm`
- 裂纹：
  - 位于 YSZ 层内。
  - 长度：`3.0 mm`
  - 顶部开口宽度：`30 um`
  - 底部宽度：`5 um`
  - 深度：`240 um`
  - 距离粘结层保留陶瓷厚度：`60 um`

## 重要说明

推荐使用 `smooth_crack` 版本。该版本通过 `Y-Z` 工作平面绘制连续梯形裂纹截面，再沿 `X` 方向拉伸 `3 mm`，最后从 YSZ 陶瓷层中执行布尔差集。因此裂纹侧壁是连续斜面，更符合老师描述的 wedge-shaped crack，也更适合后续应力集中和线弹性力学分析。

`stepped_crack` 版本采用按 `1 um` 体素宽度分组的阶梯式楔形裂纹：裂纹由 26 个不同宽度的切除块组成。为保持裂纹关于中心线对称，COMSOL 连续几何中的奇偶宽度过渡会出现单侧 `0.5 um` 的边界变化；因此它是“宽度分组对应”的中心对称阶梯几何，不是逐体素边界完全重合的网格模型。

当前两个 COMSOL 文件都还是几何模型，尚未完成材料参数、边界条件和求解步设置。下一步力学分析建议从 `smooth_crack` 版本开始，在裂纹尖端局部加密网格。
