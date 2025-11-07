# 功能说明与使用示例

本文档总结了 `wind-pypcd` 当前具备的核心能力，并结合 `main.py` 中的实用封装函数与单元测试覆盖范围，给出可直接运行的使用示例。项目官方支持的 Python 版本为 3.8、3.9、3.10 与 3.12。

## 1. 点云数据的读取与写入

`wind_pypcd.pypcd.PointCloud` 作为核心入口，支持从磁盘、字节流加载 PCD，并以多种格式写回。

- **文件读取**：`PointCloud.from_path(path)`
- **字节读取**：`PointCloud.from_bytes(blob)`
- **保存回文件**：`pc.save_pcd(path, compression="ascii|binary|binary_compressed")`
- **缓冲区导出**：`point_cloud_to_buffer(pc, data_compression=...)` 可返回 `str` 或 `bytes`

> 单元测试 `test_path_roundtrip_ascii/binary/binary_compressed`、`test_point_cloud_to_buffer_types` 验证了三种格式的读写一致性。

### 示例 · PCD 读写为不同格式

```python
from wind_pypcd import pypcd

pc = pypcd.PointCloud.from_path("sample.pcd")
pc.save_pcd("sample_ascii.pcd", compression="ascii")
pc.save_pcd("sample_binary.pcd", compression="binary")
blob = pc.to_bytes(compression="binary_compressed")
restored = pypcd.PointCloud.from_bytes(blob)
assert restored.get_metadata()["data"] == "binary_compressed"
```

## 2. 点云变换与校验

`main.py` 提供了针对点云变换的封装：

- `_validate_transform_matrix(transform)`：检查 4×4 矩阵尺寸、数值有效性。
- `transform_point_cloud(pc, transform)`：对 `PointCloud` 对象应用变换。
- `transform_pcd(path, transform)`：从文件读取后变换。
- `transform_pcd_from_bytes(blob, transform)`：从字节数据读取后变换。

这些函数会自动过滤 NaN/Inf 点、构造齐次坐标并返回 `Nx4` 的 `float32` 数组（x, y, z, intensity）。

### 示例 · 绕 Z 轴旋转点云并平移

```python
import numpy as np
from wind_pypcd import pypcd
from main import transform_point_cloud

pc = pypcd.PointCloud.from_path("lidar_front.pcd")
angle = np.deg2rad(30)
transform = np.array([
    [np.cos(angle), -np.sin(angle), 0.0, 1.0],
    [np.sin(angle),  np.cos(angle), 0.0, 0.5],
    [0.0,            0.0,           1.0, 0.0],
    [0.0,            0.0,           0.0, 1.0],
], dtype=np.float32)
points = transform_point_cloud(pc, transform)
print(points.shape)  # (N, 4)
```

## 3. 多雷达点云融合

### 3.1 基于文件路径的融合

`fusion_pcd(datas, calib, save_path)` 负责：

1. 逐个加载传感器 PCD。
2. 按 `calib` 提供的 4×4 变换矩阵进行坐标变换。
3. 将所有点拼接为单一结构化数组（x, y, z, intensity）。
4. 保存为压缩二进制 PCD。

### 示例 · 基于文件路径的融合

```python
from main import fusion_pcd
import numpy as np

datas = {
    "front_lidar": "data/front.pcd",
    "left_lidar": "data/left.pcd",
}
calib = {
    "front_lidar": np.eye(4),
    "left_lidar": np.array([
        [0, -1, 0, -2],
        [1,  0, 0,  0],
        [0,  0, 1,  1],
        [0,  0, 0,  1],
    ])
}
output = fusion_pcd(datas, calib, "output/fused.pcd")
print(output)
```

### 3.2 基于字节流的融合

`fusion_pcd_bytes(datas_bytes, calib, compression)` 与上述流程一致，但输入和输出均为字节流，适用于内存管线或网络传输。

### 3.3 带忽略区域的融合

`fuse_pointclouds(lidar_objs)` 在融合前支持对每个点云应用多个 3D box 过滤区域，避免车辆本体等静态障碍被纳入输出。

```python
from main import fuse_pointclouds, load_pcd_as_bytes

lidar_objs = [
    ("front", load_pcd_as_bytes("front.pcd"), [{
        "x": 0.0, "y": 0.0, "z": 0.0,
        "length": 4.5, "width": 2.0, "height": 2.0,
        "yaw": 0.0,
    }]),
    ("roof", load_pcd_as_bytes("roof.pcd"), []),
]
merged = fuse_pointclouds(lidar_objs)
```

## 4. PCD 与 BIN 互转

- `pypcd.pcd_to_bin(pcd_path, output_path=None, target_format=None, default_intensity=0.0, default_time=0.0)`：根据字段自动推断或强制输出为 `xyz`、`xyzi`、`xyzit` 格式。单元测试 `test_pcd_to_bin_xyzi` 覆盖了基础行为。
- `pypcd.pointcloud_to_bin(pc, output_path, target_format, default_intensity, default_time)`：直接使用 `PointCloud` 对象输出。
- `pypcd.pcd_bytes_to_bin(blob, output_path=None, ...)`：处理内存数据。

```python
from wind_pypcd import pypcd

# 自动推断输出格式
pypcd.pcd_to_bin("front.pcd")

# 强制输出 xyzit，并指定缺失字段默认值
pypcd.pcd_to_bin(
    "front.pcd",
    output_path="front_xyzit.bin",
    target_format="xyzit",
    default_intensity=0.0,
    default_time=0.0,
)
```

`test_pointcloud_to_bin_defaults` 确保缺省值写入正确，`test_point_cloud_bytes_roundtrip_binary` 验证了二进制往返的稳定性。

## 5. 点云拼接与字段操作

- `pypcd.cat_point_clouds(pc1, pc2)`：拼接点云，保持字段一致性（测试 `test_cat_pointclouds`）。
- `pypcd.add_fields(pc, md, data)`：在原点云上追加字段，同时维护元数据（测试 `test_add_fields`）。
- `pypcd.PointCloud.from_array` 与 `from_array_without_dtype`：从结构化数组或普通数组快速创建点云对象。

### 示例 · 为点云追加随机字段

```python
from wind_pypcd import pypcd
import numpy as np

pc = pypcd.PointCloud.from_path("input.pcd")
meta = {"fields": ["reflect"], "count": [1], "size": [4], "type": ["F"]}
data = np.rec.fromarrays([np.random.rand(pc.points)])
pc2 = pypcd.add_fields(pc, meta, data)
pc2.save_pcd("with_reflect.pcd", compression="binary_compressed")
```

## 6. 轴对齐裁剪（类似 PCL CropBox）

`main.py` 新增的裁剪辅助函数支持以最小 / 最大坐标描述的轴对齐包围盒（AABB）：

- `crop_point_cloud(pc, min_bounds, max_bounds)`：对 `PointCloud` 对象进行原地过滤并返回新点云。
- `crop_pcd(path, min_bounds, max_bounds, output_path=None, compression="binary_compressed")`：直接从文件裁剪，返回新的 `PointCloud` 或落盘路径。
- `crop_pcd_from_bytes(blob, min_bounds, max_bounds, compression="binary_compressed")`：处理内存字节流。

边界使用 `(min_x, min_y, min_z)` / `(max_x, max_y, max_z)` 表示，函数内部会校验维度与数值合法性。

### 示例 · 裁剪指定范围内的点

```python
from main import crop_point_cloud
from wind_pypcd import pypcd

pc = pypcd.PointCloud.from_path("front_lidar.pcd")
min_bounds = (-5.0, -2.0, -1.5)
max_bounds = (5.0,  3.0,  1.5)
cropped_pc = crop_point_cloud(pc, min_bounds, max_bounds)
cropped_pc.save_pcd("front_lidar_cropped.pcd", compression="binary_compressed")
print(cropped_pc.get_metadata()["points"])
```

## 7. 辅助工具函数

- `load_pcd_as_bytes(path)` / `save_bytes_as_pcd(blob, path)`：便捷完成文件与字节流的互转。
- `_point_in_3d_box(points, box)` & `_filter_points_by_ignore_areas(points, ignore_areas)`：`fuse_pointclouds` 使用的内部过滤逻辑，可作为自定义过滤器参考。
- `numpy_array_to_structured_array(arr)`：将 `Nx4` 普通数组转为结构化数组，便于 `PointCloud.from_array` 复用。

## 8. 测试覆盖概览

`src/wind_pypcd/tests/test_pypcd.py` 的 12 个用例覆盖了：

- PCD 头部解析与元数据校验
- 文件与字节流在 ascii/binary/binary_compressed 三种模式下的读写一致性
- 点云拼接、字段追加、元数据一致性
- PCD → BIN 转换及默认值补全
- `PointCloud.to_bytes` / `from_bytes` 往返
- 缓冲区类型与内容检查

结合这些测试，能够确保典型的读写、变换、拼接与格式转换场景均能稳定运行。

---

如需进一步了解环境准备与测试流程，请参阅 `docs/development_guide.md`。欢迎根据自身业务继续扩展示例，并通过 tox 运行测试以确保功能稳定。
