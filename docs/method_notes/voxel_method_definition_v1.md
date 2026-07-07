# Voxel Method Definition v1

## 方法名称

Anisotropic GRF-based stochastic voxel method  
中文暂称：各向异性 GRF 随机体素法。

## 当前选择原因

由于本项目不采用真实显微图像重构路线，且师兄原始 QSGS/AHM 代码暂时无法获取，后续采用自建的随机体素生成方法作为 voxel method 主线。

## 基本思想

在三维体素网格上生成 Gaussian Random Field，通过设置各向异性空间相关长度控制孔隙的方向性与长细比，再通过阈值截断得到 binary RVE。

基本流程：

1. 建立三维体素网格；
2. 设定 RVE 物理尺寸，例如 40 μm × 40 μm × 40 μm；
3. 设定体素分辨率，例如 64 × 64 × 64；
4. 设定目标孔隙率；
5. 设定各向异性相关长度 lx、ly、lz；
6. 生成各向异性 Gaussian Random Field；
7. 按目标孔隙率确定 threshold；
8. threshold 截断得到 binary RVE；
9. 输出实际孔隙率、随机种子、生成耗时和可视化切片。

## 相定义

- 0 = pore phase
- 1 = solid 8YSZ phase

## 与 QSGS 的对比逻辑

QSGS 更偏向局部随机生长机制；Anisotropic GRF 更偏向全局空间相关场截断机制。两者可在相同 RVE 尺寸、目标孔隙率、材料参数和后续均匀化流程下比较。

## 当前限制

1. 当前只是 voxel method 的 v1 定义。
2. QSGS 原文参数仍需核验。
3. AHM/PBC 代码后续需要自建或寻找替代实现。
4. GRF 的相关长度与真实 EB-PVD 孔隙长细比之间的映射关系仍需后续验证。