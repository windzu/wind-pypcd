# Wind-Pypcd

Wind-Pypcd 是一个功能强大的 Python 库，专门用于处理点云数据（PCD 格式）。它基于原始 pypcd 项目进行了大幅改进，提供了 Python 3 支持、字节流处理、3D 空间过滤、多点云融合等高级功能。

## 特性

- 🚀 读取和写入 PCD 文件（ASCII、二进制、压缩格式）
- 📦 字节流处理 - 支持内存中的 PCD 数据操作
- 🔄 点云变换 - 支持 4x4 变换矩阵的空间变换
- 🎯 3D 空间过滤 - 支持旋转 3D box 区域过滤
- 🔗 多点云融合 - 多传感器数据融合
- 📊 与 NumPy 数组的无缝集成
- ✅ 完整的类型注解和参数验证
- 🐍 Python 3.6+ 兼容性

## 安装

```bash
pip install wind-pypcd
```

或者从源码安装：

```bash
git clone https://github.com/windzu/wind-pypcd.git
cd wind-pypcd
pip install -e .
```

## 依赖

- Python 3.6+
- NumPy
- python-lzf

## 快速开始

### 基础 PCD 文件操作

```python
import wind_pypcd.pypcd as pypcd
import numpy as np

# 读取 PCD 文件
pc = pypcd.PointCloud.from_path('example.pcd')
print(f"点云包含 {pc.points} 个点")
print(f"字段: {pc.fields}")

# 转换为 numpy 数组
array = pc.pc_data

# 保存为不同格式
pc.save_pcd('ascii_output.pcd')  # ASCII 格式
pc.save_pcd('binary_output.pcd', compression='binary')  # 二进制格式
pc.save_pcd('compressed_output.pcd', compression='binary_compressed')  # 压缩格式
```

### 字节流处理

```python
from main import load_pcd_as_bytes, save_bytes_as_pcd

# 加载 PCD 文件为字节数据
pcd_bytes = load_pcd_as_bytes('input.pcd')
print(f"文件大小: {len(pcd_bytes)} bytes")

# 直接从字节数据创建点云对象
pc = pypcd.PointCloud.from_bytes(pcd_bytes)

# 转换回字节数据
output_bytes = pc.to_bytes(compression='binary_compressed')

# 保存字节数据为 PCD 文件
save_bytes_as_pcd(output_bytes, 'output.pcd')
```

## 点云变换

### 基础变换

```python
from main import transform_pcd, transform_pcd_from_bytes
import numpy as np

# 定义变换矩阵（4x4 齐次变换矩阵）
transform_matrix = np.array([
    [1.0, 0.0, 0.0, 1.0],  # x 方向平移 1 米
    [0.0, 1.0, 0.0, 2.0],  # y 方向平移 2 米
    [0.0, 0.0, 1.0, 0.0],  # z 方向无平移
    [0.0, 0.0, 0.0, 1.0]   # 齐次坐标
])

# 方式1: 从文件路径变换
transformed_points = transform_pcd('input.pcd', transform_matrix)
print(f"变换后的点云: {transformed_points.shape}")

# 方式2: 从字节数据变换
pcd_bytes = load_pcd_as_bytes('input.pcd')
transformed_points = transform_pcd_from_bytes(pcd_bytes, transform_matrix)
```

### 旋转变换示例

```python
import numpy as np

# 绕 z 轴旋转 45 度
angle = np.pi / 4  # 45 度转弧度
rotation_matrix = np.array([
    [np.cos(angle), -np.sin(angle), 0.0, 0.0],
    [np.sin(angle),  np.cos(angle), 0.0, 0.0],
    [0.0,           0.0,            1.0, 0.0],
    [0.0,           0.0,            0.0, 1.0]
])

transformed_points = transform_pcd('input.pcd', rotation_matrix)
```

## 多点云融合

### 基础融合

```python
from main import fusion_pcd, fusion_pcd_bytes
import numpy as np

# 方式1: 文件路径融合
datas = {
    "front_lidar": "data/front_lidar.pcd",
    "left_lidar": "data/left_lidar.pcd", 
    "right_lidar": "data/right_lidar.pcd"
}

# 定义每个传感器的标定矩阵
calib = {
    "front_lidar": np.eye(4),  # 前雷达无变换
    "left_lidar": np.array([   # 左雷达变换矩阵
        [0.0, -1.0, 0.0, -2.0],
        [1.0,  0.0, 0.0,  0.0],
        [0.0,  0.0, 1.0,  0.0],
        [0.0,  0.0, 0.0,  1.0]
    ]),
    "right_lidar": np.array([  # 右雷达变换矩阵
        [0.0,  1.0, 0.0,  2.0],
        [-1.0, 0.0, 0.0,  0.0],
        [0.0,  0.0, 1.0,  0.0],
        [0.0,  0.0, 0.0,  1.0]
    ])
}

# 执行融合
result_path = fusion_pcd(datas, calib, "output/fused.pcd")
print(f"融合结果保存到: {result_path}")
```

### 字节流融合

```python
# 方式2: 字节数据融合
datas_bytes = {}
for sensor, file_path in datas.items():
    datas_bytes[sensor] = load_pcd_as_bytes(file_path)

# 融合字节数据
fused_bytes = fusion_pcd_bytes(datas_bytes, calib, compression="binary_compressed")
print(f"融合后数据大小: {len(fused_bytes)} bytes")

# 保存结果
save_bytes_as_pcd(fused_bytes, "output/fused_from_bytes.pcd")
```

## 3D 空间过滤融合

### 高级融合与过滤

```python
from main import fuse_pointclouds

# 定义忽略区域 - 3D box 定义
ignore_areas = [
    {
        "x": 0.0,      # box 中心 x 坐标
        "y": 4.5,      # box 中心 y 坐标  
        "z": 0.0,      # box 中心 z 坐标
        "length": 30.0, # x 方向长度
        "width": 10.0,  # y 方向宽度
        "height": 10.0, # z 方向高度
        "yaw": 0.0      # 绕 z 轴旋转角度（弧度）
    },
    {
        "x": 10.0,
        "y": 0.0,
        "z": 0.0,
        "length": 5.0,
        "width": 5.0,
        "height": 8.0,
        "yaw": np.pi/4  # 45度旋转
    }
]

# 准备多传感器数据
lidar_objs = [
    ("front_lidar", load_pcd_as_bytes("data/front_lidar.pcd"), ignore_areas),
    ("left_lidar", load_pcd_as_bytes("data/left_lidar.pcd"), []),  # 无过滤区域
    ("right_lidar", load_pcd_as_bytes("data/right_lidar.pcd"), ignore_areas)
]

# 执行带过滤的融合
fused_bytes = fuse_pointclouds(lidar_objs)
save_bytes_as_pcd(fused_bytes, "output/fused_with_filtering.pcd")
```

### 动态忽略区域

```python
# 根据车辆位置动态设置忽略区域
vehicle_x, vehicle_y = 5.0, 2.0
vehicle_ignore_area = {
    "x": vehicle_x,
    "y": vehicle_y,
    "z": 0.0,
    "length": 4.5,  # 车辆长度
    "width": 2.0,   # 车辆宽度
    "height": 2.0,  # 车辆高度
    "yaw": 0.0
}

lidar_objs = [
    ("main_lidar", pcd_bytes, [vehicle_ignore_area])
]

filtered_result = fuse_pointclouds(lidar_objs)
```

## 高级功能

### 创建自定义点云

```python
import numpy as np

# 创建包含强度信息的点云
dtype = np.dtype([
    ('x', np.float32),
    ('y', np.float32),
    ('z', np.float32),
    ('intensity', np.float32)
])

# 生成示例数据
n_points = 1000
points = np.zeros(n_points, dtype=dtype)
points['x'] = np.random.random(n_points) * 100 - 50
points['y'] = np.random.random(n_points) * 100 - 50
points['z'] = np.random.random(n_points) * 10
points['intensity'] = np.random.random(n_points) * 255

# 创建点云对象
pc = pypcd.PointCloud.from_array(points)
pc.save_pcd('custom_cloud.pcd', compression='binary_compressed')
```

### 点云数据分析

```python
# 读取点云
pc = pypcd.PointCloud.from_path('input.pcd')

# 统计信息
print(f"点数: {pc.points}")
print(f"X 范围: {pc.pc_data['x'].min():.2f} ~ {pc.pc_data['x'].max():.2f}")
print(f"Y 范围: {pc.pc_data['y'].min():.2f} ~ {pc.pc_data['y'].max():.2f}")
print(f"Z 范围: {pc.pc_data['z'].min():.2f} ~ {pc.pc_data['z'].max():.2f}")

# 过滤操作
# 移除离群点（距离原点过远的点）
distances = np.sqrt(pc.pc_data['x']**2 + pc.pc_data['y']**2 + pc.pc_data['z']**2)
valid_mask = distances < 100.0  # 保留距离小于100米的点

# 移除NaN值
valid_mask &= (np.isfinite(pc.pc_data['x']) & 
               np.isfinite(pc.pc_data['y']) & 
               np.isfinite(pc.pc_data['z']))

# 高度过滤
valid_mask &= (pc.pc_data['z'] > -2.0) & (pc.pc_data['z'] < 10.0)

# 创建过滤后的点云
filtered_data = pc.pc_data[valid_mask]
filtered_pc = pypcd.PointCloud.from_array(filtered_data)
filtered_pc.save_pcd('filtered_output.pcd')

print(f"过滤前: {pc.points} 点")
print(f"过滤后: {filtered_pc.points} 点")
```

## 性能优化

### 批量处理

```python
import os
from concurrent.futures import ProcessPoolExecutor

def process_single_pcd(file_path):
    """处理单个PCD文件"""
    try:
        # 加载并变换
        transform = np.eye(4)
        transform[2, 3] = 1.0  # z方向平移1米
        
        result = transform_pcd(file_path, transform)
        
        # 保存结果
        output_path = file_path.replace('.pcd', '_transformed.pcd')
        # 这里需要额外的保存逻辑
        return output_path
    except Exception as e:
        print(f"处理 {file_path} 失败: {e}")
        return None

# 批量处理多个文件
pcd_files = ['file1.pcd', 'file2.pcd', 'file3.pcd']

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_single_pcd, pcd_files))

print(f"处理完成，结果: {[r for r in results if r is not None]}")
```

### 内存优化

```python
# 对于大文件，使用字节流处理避免重复加载
def efficient_multi_transform(file_path, transforms):
    """对同一文件应用多个变换"""
    # 只加载一次
    pcd_bytes = load_pcd_as_bytes(file_path)
    
    results = []
    for i, transform in enumerate(transforms):
        # 使用字节数据变换
        result = transform_pcd_from_bytes(pcd_bytes, transform)
        results.append(result)
    
    return results
```

## 错误处理

```python
from main import _validate_transform_matrix

try:
    # 验证变换矩阵
    invalid_matrix = np.array([[1, 2], [3, 4]])  # 错误的矩阵大小
    _validate_transform_matrix(invalid_matrix)
except ValueError as e:
    print(f"变换矩阵错误: {e}")

try:
    # 文件操作
    pc = pypcd.PointCloud.from_path('nonexistent.pcd')
except FileNotFoundError:
    print("文件不存在")
except Exception as e:
    print(f"读取文件错误: {e}")

try:
    # 融合操作
    result = fuse_pointclouds([])  # 空列表
except ValueError as e:
    print(f"融合参数错误: {e}")
```

## API 参考

### 核心函数

#### 变换函数

- `transform_point_cloud(pc, transform)` - 变换点云对象
- `transform_pcd(pcd_path, transform)` - 从文件路径变换
- `transform_pcd_from_bytes(pcd_bytes, transform)` - 从字节数据变换

#### 融合函数

- `fusion_pcd(datas, calib, save_path)` - 基础文件融合
- `fusion_pcd_bytes(datas_bytes, calib, compression)` - 字节数据融合
- `fuse_pointclouds(lidar_objs)` - 高级融合与3D过滤

#### 工具函数

- `load_pcd_as_bytes(file_path)` - 加载PCD为字节数据
- `save_bytes_as_pcd(pcd_bytes, file_path)` - 保存字节数据为PCD
- `numpy_array_to_structured_array(arr)` - NumPy数组转换

#### PointCloud 类方法

- `from_path(path)` - 从文件读取
- `from_bytes(data)` - 从字节数据读取
- `from_array(array)` - 从NumPy数组创建
- `to_bytes(compression)` - 转换为字节数据
- `save_pcd(path, compression)` - 保存到文件

### 参数说明

#### 变换矩阵格式

```python
# 4x4 齐次变换矩阵
transform = np.array([
    [R11, R12, R13, tx],  # 旋转和x平移
    [R21, R22, R23, ty],  # 旋转和y平移  
    [R31, R32, R33, tz],  # 旋转和z平移
    [0.0, 0.0, 0.0, 1.0]  # 齐次坐标
])
```

#### 3D Box 定义

```python
box = {
    "x": 0.0,        # 中心x坐标
    "y": 0.0,        # 中心y坐标
    "z": 0.0,        # 中心z坐标
    "length": 10.0,  # x方向长度
    "width": 5.0,    # y方向宽度
    "height": 3.0,   # z方向高度
    "yaw": 0.0       # 绕z轴旋转角度（弧度）
}
```

## 常见问题

### Q: 支持哪些 PCD 格式？

A: 支持 ASCII、二进制和二进制压缩格式，推荐使用 `binary_compressed` 以获得最佳性能。

### Q: 如何处理大型点云文件？

A: 使用字节流处理方式，避免重复文件 I/O 操作：

```python
# 推荐方式
pcd_bytes = load_pcd_as_bytes('large_file.pcd')
result = transform_pcd_from_bytes(pcd_bytes, transform)
```

### Q: 变换矩阵的坐标系约定是什么？

A: 使用右手坐标系，变换矩阵为4x4齐次变换矩阵，先旋转后平移。

### Q: 3D box 过滤支持旋转吗？

A: 是的，通过 `yaw` 参数可以设置绕 z 轴的旋转角度（弧度）。

### Q: 如何优化融合性能？

A:

1. 使用字节流方式减少文件 I/O
2. 对于重复操作，缓存加载的数据
3. 使用 `binary_compressed` 压缩格式
4. 合理设置忽略区域减少计算量

## 完整示例

```python
#!/usr/bin/env python3
"""
完整的多雷达融合示例
"""
import numpy as np
from main import *

def main():
    # 1. 准备测试数据
    print("=== 多雷达点云融合示例 ===")
    
    # 2. 定义传感器标定参数
    calib_matrices = {
        "front": np.eye(4),  # 前雷达作为基准
        "left": np.array([   # 左侧雷达 
            [0, -1, 0, -2],
            [1,  0, 0,  0], 
            [0,  0, 1,  1],
            [0,  0, 0,  1]
        ]),
        "right": np.array([  # 右侧雷达
            [0,  1, 0,  2],
            [-1, 0, 0,  0],
            [0,  0, 1,  1], 
            [0,  0, 0,  1]
        ])
    }
    
    # 3. 定义需要过滤的区域（如车辆本体）
    vehicle_ignore_area = {
        "x": 0.0, "y": 0.0, "z": 0.0,
        "length": 4.5, "width": 2.0, "height": 2.0,
        "yaw": 0.0
    }
    
    # 4. 准备融合数据
    lidar_data = []
    sensors = ["front", "left", "right"]
    
    for sensor in sensors:
        try:
            file_path = f"test_data/{sensor}_lidar.pcd"
            pcd_bytes = load_pcd_as_bytes(file_path)
            
            # 只对主车体区域进行过滤
            ignore_areas = [vehicle_ignore_area] if sensor == "front" else []
            
            lidar_data.append((f"{sensor}_lidar", pcd_bytes, ignore_areas))
            print(f"✓ 加载 {sensor} 雷达数据: {len(pcd_bytes)} bytes")
        except Exception as e:
            print(f"✗ 加载 {sensor} 雷达失败: {e}")
    
    # 5. 执行融合
    if lidar_data:
        try:
            print("\n开始融合...")
            fused_bytes = fuse_pointclouds(lidar_data)
            
            # 保存结果
            output_path = "output/multi_lidar_fused.pcd"
            save_bytes_as_pcd(fused_bytes, output_path)
            
            print(f"✓ 融合完成!")
            print(f"  输出文件: {output_path}")
            print(f"  文件大小: {len(fused_bytes)} bytes")
            
        except Exception as e:
            print(f"✗ 融合失败: {e}")
    else:
        print("✗ 没有可用的雷达数据")

if __name__ == "__main__":
    main()
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### 版本 0.2.0

- ✨ 新增字节流处理支持
- ✨ 新增3D空间过滤功能
- ✨ 新增高级多点云融合
- ✨ 完整的类型注解和参数验证
- 🐛 修复Python 3兼容性问题
- 📈 显著提升性能
- 📚 完善文档和示例

### 版本 0.1.0

- 🎉 初始版本
- 📖 基本的 PCD 读写功能
