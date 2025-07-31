import os
from typing import Dict, List, Tuple, Union

import numpy as np

from wind_pypcd import pypcd


def _validate_transform_matrix(transform: np.ndarray) -> None:
    """验证变换矩阵的有效性
    
    Args:
        transform: 待验证的变换矩阵
        
    Raises:
        ValueError: 变换矩阵无效时
    """
    if not isinstance(transform, np.ndarray):
        raise ValueError("Transform must be a numpy array")
    
    if transform.shape != (4, 4):
        raise ValueError("Transform must be a 4x4 matrix")
    
    if not np.isfinite(transform).all():
        raise ValueError("Transform matrix contains invalid values (NaN or Inf)")


def _extract_point_cloud_data(pc: pypcd.PointCloud) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """从PointCloud对象中提取坐标和强度数据
    
    Args:
        pc: PointCloud对象
        
    Returns:
        x, y, z, intensity arrays
        
    Raises:
        ValueError: 点云数据无效时
    """
    try:
        x = pc.pc_data["x"].flatten()
        y = pc.pc_data["y"].flatten() 
        z = pc.pc_data["z"].flatten()
        intensity = pc.pc_data["intensity"].flatten()
    except KeyError as e:
        raise ValueError(f"Missing required field in point cloud: {e}")
    except Exception as e:
        raise ValueError(f"Failed to extract point cloud data: {e}")
    
    # 检查数据长度一致性
    if not (len(x) == len(y) == len(z) == len(intensity)):
        raise ValueError("Point cloud field arrays have inconsistent lengths")
    
    return x, y, z, intensity


def _apply_transform_to_points(x: np.ndarray, y: np.ndarray, z: np.ndarray, 
                              intensity: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """对点云数据应用坐标变换
    
    Args:
        x, y, z: 坐标数组
        intensity: 强度数组
        transform: 4x4变换矩阵
        
    Returns:
        变换后的点云数组 [N, 4] (x, y, z, intensity)
        
    Raises:
        ValueError: 数据无效时
    """
    # 过滤NaN值 - 更高效的方式
    valid_mask = (np.isfinite(x) & np.isfinite(y) & 
                  np.isfinite(z) & np.isfinite(intensity))
    
    if not np.any(valid_mask):
        raise ValueError("No valid points found after filtering NaN values")
    
    # 只处理有效点
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    z_valid = z[valid_mask]
    intensity_valid = intensity[valid_mask]
    
    # 构建齐次坐标 [N, 4]
    points_homo = np.column_stack([
        x_valid,
        y_valid, 
        z_valid,
        np.ones(len(x_valid), dtype=np.float32)
    ])
    
    # 应用变换矩阵
    try:
        transformed_points = (transform @ points_homo.T).T
    except Exception as e:
        raise ValueError(f"Failed to apply transformation: {e}")
    
    # 替换最后一列为intensity
    transformed_points[:, 3] = intensity_valid
    
    return transformed_points.astype(np.float32)


def transform_point_cloud(pc: pypcd.PointCloud, transform: np.ndarray) -> np.ndarray:
    """对PointCloud对象应用坐标变换
    
    Args:
        pc: PointCloud对象
        transform: 4x4变换矩阵
        
    Returns:
        变换后的点云数组 [N, 4] (x, y, z, intensity)
        
    Raises:
        ValueError: 输入参数无效时
    """
    if not isinstance(pc, pypcd.PointCloud):
        raise ValueError("pc must be a PointCloud object")
    
    _validate_transform_matrix(transform)
    
    # 提取点云数据
    x, y, z, intensity = _extract_point_cloud_data(pc)
    
    # 应用变换
    return _apply_transform_to_points(x, y, z, intensity, transform)


def transform_pcd(pcd_path: str, transform: np.ndarray) -> np.ndarray:
    """从文件路径加载PCD并应用坐标变换
    
    Args:
        pcd_path: PCD文件路径
        transform: 4x4变换矩阵
        
    Returns:
        变换后的点云数组 [N, 4] (x, y, z, intensity)
        
    Raises:
        ValueError: 输入参数无效时
        FileNotFoundError: 文件不存在时
    """
    if not isinstance(pcd_path, str):
        raise ValueError("pcd_path must be a string")
    
    if not os.path.exists(pcd_path):
        raise FileNotFoundError(f"PCD file not found: {pcd_path}")
    
    try:
        pc = pypcd.PointCloud.from_path(pcd_path)
    except Exception as e:
        raise ValueError(f"Failed to load PCD file {pcd_path}: {e}")
    
    return transform_point_cloud(pc, transform)


def transform_pcd_from_bytes(pcd_bytes: bytes, transform: np.ndarray) -> np.ndarray:
    """从字节数据加载PCD并应用坐标变换
    
    Args:
        pcd_bytes: PCD文件的字节数据
        transform: 4x4变换矩阵
        
    Returns:
        变换后的点云数组 [N, 4] (x, y, z, intensity)
        
    Raises:
        ValueError: 输入参数无效时
    """
    if not isinstance(pcd_bytes, bytes):
        raise ValueError("pcd_bytes must be bytes")
    
    try:
        pc = pypcd.PointCloud.from_bytes(pcd_bytes)
    except Exception as e:
        raise ValueError(f"Failed to load PCD from bytes: {e}")
    
    return transform_point_cloud(pc, transform)


def fusion_pcd(datas: Dict[str, str], calib: Dict[str, np.ndarray], save_path: str) -> str:
    """根据标定信息合并多个PCD文件
    
    Args:
        datas: 传感器数据，key为frame_id，value为pcd文件路径
        calib: 标定信息，key为frame_id，value为4x4变换矩阵
        save_path: 融合后的PCD文件保存路径
        
    Returns:
        保存的融合PCD文件路径
        
    Raises:
        ValueError: 输入参数无效时
        FileNotFoundError: PCD文件不存在时
    """
    # 参数类型验证
    if not isinstance(datas, dict):
        raise ValueError("datas must be a dictionary")
    if not isinstance(calib, dict):
        raise ValueError("calib must be a dictionary")
    if not isinstance(save_path, str):
        raise ValueError("save_path must be a string")
    
    # 参数验证
    if not datas or not calib:
        raise ValueError("datas and calib cannot be empty")
    
    if not all(key in calib for key in datas.keys()):
        raise ValueError("All sensors in datas must have corresponding calibration in calib")
    
    # 验证变换矩阵
    for sensor, transform in calib.items():
        if sensor in datas:
            _validate_transform_matrix(transform)
        
    # 检查文件是否存在
    for sensor, pcd_path in datas.items():
        if not os.path.exists(pcd_path):
            raise FileNotFoundError(f"PCD file not found: {pcd_path}")
    
    # 处理点云数据
    point_clouds = []
    
    for sensor in datas.keys():
        try:
            transformed_points = transform_pcd(datas[sensor], calib[sensor])
            point_clouds.append(transformed_points)
            print(f"Processed {sensor}: {len(transformed_points)} points")
        except Exception as e:
            print(f"Warning: Failed to process {sensor}: {e}")
            continue
    
    if not point_clouds:
        raise ValueError("No valid point clouds to fuse")
    
    # 合并所有点云 - 一次性拼接更高效
    fused_points = np.vstack(point_clouds)
    print(f"Total fused points: {len(fused_points)}")
    
    # 转换为结构化数组并保存
    structured_array = numpy_array_to_structured_array(fused_points)
    fusion_pc = pypcd.PointCloud.from_array(structured_array)
    
    # 确保保存目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 保存融合后的点云
    fusion_pc.save_pcd(save_path, compression="binary_compressed")
    print(f"Fused point cloud saved to: {save_path}")
    
    return save_path

def numpy_array_to_structured_array(arr: np.ndarray) -> np.ndarray:
    """将常规的numpy数组转换为结构化数组

    Args:
        arr: 输入的numpy数组，每一列对应一个字段 [N, 4] (x, y, z, intensity)

    Returns:
        结构化数组
        
    Raises:
        ValueError: 输入数组格式不正确时
    """
    if not isinstance(arr, np.ndarray):
        raise ValueError("arr must be a numpy array")
    
    if arr.ndim != 2:
        raise ValueError("arr must be a 2D array")
    
    if arr.shape[1] != 4:
        raise ValueError("Expected a Nx4 numpy array")
    
    if arr.size == 0:
        raise ValueError("arr cannot be empty")
    
    dtype = [("x", "f4"), ("y", "f4"), ("z", "f4"), ("intensity", "f4")]
    structured_arr = np.zeros(arr.shape[0], dtype=dtype)

    structured_arr["x"] = arr[:, 0]
    structured_arr["y"] = arr[:, 1]
    structured_arr["z"] = arr[:, 2]
    structured_arr["intensity"] = arr[:, 3]

    return structured_arr


def fusion_pcd_bytes(datas_bytes: Dict[str, bytes], calib: Dict[str, np.ndarray], 
                    compression: str = "binary_compressed") -> bytes:
    """根据标定信息合并多个PCD字节数据
    
    Args:
        datas_bytes: 传感器字节数据，key为frame_id，value为pcd文件的字节数据
        calib: 标定信息，key为frame_id，value为4x4变换矩阵
        compression: 压缩格式，可选 "ascii", "binary", "binary_compressed"
        
    Returns:
        融合后的PCD文件字节数据
        
    Raises:
        ValueError: 输入参数无效时
    """
    # 参数类型验证
    if not isinstance(datas_bytes, dict):
        raise ValueError("datas_bytes must be a dictionary")
    if not isinstance(calib, dict):
        raise ValueError("calib must be a dictionary")
    if not isinstance(compression, str):
        raise ValueError("compression must be a string")
    
    # 验证压缩格式
    valid_compressions = {"ascii", "binary", "binary_compressed"}
    if compression not in valid_compressions:
        raise ValueError(f"compression must be one of {valid_compressions}")
    
    # 参数验证
    if not datas_bytes or not calib:
        raise ValueError("datas_bytes and calib cannot be empty")
    
    if not all(key in calib for key in datas_bytes.keys()):
        raise ValueError("All sensors in datas_bytes must have corresponding calibration in calib")
    
    # 验证变换矩阵
    for sensor, transform in calib.items():
        if sensor in datas_bytes:
            _validate_transform_matrix(transform)
    
    # 验证字节数据类型
    for sensor, data in datas_bytes.items():
        if not isinstance(data, bytes):
            raise ValueError(f"Data for sensor {sensor} must be bytes")
        
    # 处理每个传感器的点云数据
    point_clouds = []
    
    for sensor in datas_bytes.keys():
        try:
            transformed_points = transform_pcd_from_bytes(datas_bytes[sensor], calib[sensor])
            point_clouds.append(transformed_points)
            print(f"Processed {sensor}: {len(transformed_points)} points")
        except Exception as e:
            print(f"Warning: Failed to process {sensor}: {e}")
            continue
    
    if not point_clouds:
        raise ValueError("No valid point clouds to fuse")
    
    # 合并所有点云
    fused_points = np.vstack(point_clouds)
    print(f"Total fused points: {len(fused_points)}")
    
    # 转换为结构化数组
    structured_array = numpy_array_to_structured_array(fused_points)
    fusion_pc = pypcd.PointCloud.from_array(structured_array)
    
    # 使用改进后的方法转换为字节数据
    fused_bytes = fusion_pc.to_bytes(compression=compression)
    
    return fused_bytes


def load_pcd_as_bytes(file_path: str) -> bytes:
    """加载PCD文件为字节数据
    
    Args:
        file_path: PCD文件路径
        
    Returns:
        PCD文件的字节数据
        
    Raises:
        ValueError: 输入参数无效时
        FileNotFoundError: 文件不存在时
    """
    if not isinstance(file_path, str):
        raise ValueError("file_path must be a string")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")


def save_bytes_as_pcd(pcd_bytes: bytes, file_path: str) -> None:
    """将字节数据保存为PCD文件
    
    Args:
        pcd_bytes: PCD文件的字节数据
        file_path: 保存路径
        
    Raises:
        ValueError: 输入参数无效时
    """
    if not isinstance(pcd_bytes, bytes):
        raise ValueError("pcd_bytes must be bytes")
    
    if not isinstance(file_path, str):
        raise ValueError("file_path must be a string")
    
    if len(pcd_bytes) == 0:
        raise ValueError("pcd_bytes cannot be empty")
    
    try:
        # 确保保存目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(pcd_bytes)
    except Exception as e:
        raise ValueError(f"Failed to save file {file_path}: {e}")


def _point_in_3d_box(points: np.ndarray, box: dict) -> np.ndarray:
    """检查点是否在3D box内
    
    Args:
        points: 点云数组 [N, 3] (x, y, z)
        box: 3D box定义字典
        
    Returns:
        布尔数组，True表示点在box内
    """
    if points.shape[1] < 3:
        raise ValueError("points must have at least 3 columns (x, y, z)")
    
    # 提取box参数
    cx, cy, cz = box["x"], box["y"], box["z"]
    length, width, height = box["length"], box["width"], box["height"]
    yaw = box.get("yaw", 0.0)  # 默认yaw为0
    
    # 将点平移到box中心为原点的坐标系
    translated_points = points[:, :3] - np.array([cx, cy, cz])
    
    # 如果有旋转，需要反向旋转点到box的本地坐标系
    if yaw != 0.0:
        cos_yaw = np.cos(-yaw)  # 反向旋转
        sin_yaw = np.sin(-yaw)
        rotation_matrix = np.array([
            [cos_yaw, -sin_yaw, 0],
            [sin_yaw, cos_yaw, 0],
            [0, 0, 1]
        ])
        translated_points = translated_points @ rotation_matrix.T
    
    # 检查点是否在box范围内
    half_length = length / 2.0
    half_width = width / 2.0
    half_height = height / 2.0
    
    inside_x = np.abs(translated_points[:, 0]) <= half_length
    inside_y = np.abs(translated_points[:, 1]) <= half_width
    inside_z = np.abs(translated_points[:, 2]) <= half_height
    
    return inside_x & inside_y & inside_z


def _filter_points_by_ignore_areas(points: np.ndarray, ignore_areas: List[dict]) -> np.ndarray:
    """根据忽略区域过滤点云
    
    Args:
        points: 点云数组 [N, 4] (x, y, z, intensity)
        ignore_areas: 忽略区域列表
        
    Returns:
        过滤后的点云数组
    """
    if not ignore_areas:
        return points
    
    if points.shape[1] < 3:
        raise ValueError("points must have at least 3 columns (x, y, z)")
    
    # 初始化所有点都不在忽略区域内
    points_to_ignore = np.zeros(len(points), dtype=bool)
    
    # 检查每个忽略区域
    for box in ignore_areas:
        # 验证box参数
        required_keys = ["x", "y", "z", "length", "width", "height"]
        if not all(key in box for key in required_keys):
            raise ValueError(f"Box must contain keys: {required_keys}")
        
        # 检查哪些点在当前box内
        in_box = _point_in_3d_box(points, box)
        points_to_ignore |= in_box
    
    # 返回不在任何忽略区域内的点
    return points[~points_to_ignore]


def fuse_pointclouds(lidar_objs: List[Tuple[str, bytes, List[dict]]]) -> bytes:
    """融合多个点云，支持忽略指定的3D box区域
    
    Args:
        lidar_objs: [(channel_name, pcd_bytes, ignore_area_json)]
            - channel_name: 传感器通道名称
            - pcd_bytes: PCD文件的字节数据
            - ignore_area_json: 忽略区域列表，每个元素是包含3D box定义的字典
                {
                    "x": 0.0,      # box中心x坐标
                    "y": 4.5,      # box中心y坐标  
                    "z": 0.0,      # box中心z坐标
                    "length": 30.0, # x方向长度（yaw=0时）
                    "width": 10.0,  # y方向宽度（yaw=0时）
                    "height": 10.0, # z方向高度
                    "yaw": 0.0      # 绕z轴旋转角度（弧度）
                }
                
    Returns:
        融合后的PCD文件字节数据
        
    Raises:
        ValueError: 输入参数无效时
    """
    # 参数验证
    if not isinstance(lidar_objs, list):
        raise ValueError("lidar_objs must be a list")
    
    if not lidar_objs:
        raise ValueError("lidar_objs cannot be empty")
    
    # 验证每个lidar对象的格式
    for i, obj in enumerate(lidar_objs):
        if not isinstance(obj, (tuple, list)) or len(obj) != 3:
            raise ValueError(f"lidar_objs[{i}] must be a tuple/list of length 3")
        
        channel_name, pcd_bytes, ignore_areas = obj
        
        if not isinstance(channel_name, str):
            raise ValueError(f"lidar_objs[{i}][0] (channel_name) must be a string")
        
        if not isinstance(pcd_bytes, bytes):
            raise ValueError(f"lidar_objs[{i}][1] (pcd_bytes) must be bytes")
        
        if not isinstance(ignore_areas, list):
            raise ValueError(f"lidar_objs[{i}][2] (ignore_areas) must be a list")
    
    point_clouds = []
    
    for channel_name, pcd_bytes, ignore_areas in lidar_objs:
        try:
            # 加载点云数据
            pc = pypcd.PointCloud.from_bytes(pcd_bytes)
            
            # 提取点云数据
            x, y, z, intensity = _extract_point_cloud_data(pc)
            
            # 过滤NaN值
            valid_mask = (np.isfinite(x) & np.isfinite(y) & 
                         np.isfinite(z) & np.isfinite(intensity))
            
            if not np.any(valid_mask):
                print(f"Warning: No valid points found in {channel_name}")
                continue
            
            # 构建点云数组 [N, 4]
            points = np.column_stack([
                x[valid_mask],
                y[valid_mask],
                z[valid_mask],
                intensity[valid_mask]
            ]).astype(np.float32)
            
            # 应用忽略区域过滤
            if ignore_areas:
                original_count = len(points)
                points = _filter_points_by_ignore_areas(points, ignore_areas)
                filtered_count = original_count - len(points)
                print(f"Filtered {filtered_count} points from {channel_name} "
                      f"(kept {len(points)}/{original_count})")
            
            if len(points) > 0:
                point_clouds.append(points)
                print(f"Processed {channel_name}: {len(points)} points")
            else:
                print(f"Warning: No points remaining after filtering for {channel_name}")
                
        except Exception as e:
            print(f"Warning: Failed to process {channel_name}: {e}")
            continue
    
    if not point_clouds:
        raise ValueError("No valid point clouds to fuse")
    
    # 合并所有点云
    fused_points = np.vstack(point_clouds)
    print(f"Total fused points: {len(fused_points)}")
    
    # 转换为结构化数组
    structured_array = numpy_array_to_structured_array(fused_points)
    fusion_pc = pypcd.PointCloud.from_array(structured_array)
    
    # 转换为字节数据
    fused_bytes = fusion_pc.to_bytes(compression="binary_compressed")
    
    return fused_bytes


def test_fuse_pointclouds():
    """测试fuse_pointclouds函数"""
    print("\n=== 测试 fuse_pointclouds 函数 ===")
    
    # 定义忽略区域 - 两个3x2x1的box
    front_ignore_areas = [
        {
            "x": 3.0,
            "y": 0.0, 
            "z": 0.0,
            "length": 2.0,
            "width": 2.0,
            "height": 2.0,
            "yaw": 0.0
        },
    ]

    left_ignore_areas = [
        {
            "x": 0.0,
            "y": 3.0, 
            "z": 0.0,
            "length": 2.0,
            "width": 2.0,
            "height": 2.0,
            "yaw": 0.0
        },
    ]

    right_ignore_areas = [
        {
            "x": 0.0,
            "y": -3.0, 
            "z": 0.0,
            "length": 2.0,
            "width": 2.0,
            "height": 2.0,
            "yaw": 0.0
        },
    ]
    
    # 准备测试数据
    test_lidar_objs = []
    
    # 只测试front_lidar（top lidar）
    try:
        front_lidar_bytes = load_pcd_as_bytes("test_data/front_lidar.pcd")
        test_lidar_objs.append(("top_lidar", front_lidar_bytes, front_ignore_areas))
        
        # 其他两个lidar不设置忽略区域
        left_lidar_bytes = load_pcd_as_bytes("test_data/left_lidar.pcd") 
        test_lidar_objs.append(("left_lidar", left_lidar_bytes, left_ignore_areas))
        
        right_lidar_bytes = load_pcd_as_bytes("test_data/right_lidar.pcd")
        test_lidar_objs.append(("right_lidar", right_lidar_bytes, right_ignore_areas))
        
    except Exception as e:
        print(f"Error loading test data: {e}")
        return
    
    try:
        # 执行融合
        fused_bytes = fuse_pointclouds(test_lidar_objs)
        print(f"Fusion successful! Result size: {len(fused_bytes)} bytes")
        
        # 保存结果
        test_save_path = "test_data/results/fused_with_ignore_areas.pcd"
        save_bytes_as_pcd(fused_bytes, test_save_path)
        print(f"Test result saved to: {test_save_path}")
        
        # 与原始融合结果对比
        try:
            original_bytes = load_pcd_as_bytes("test_data/results/fused_from_bytes.pcd")
            print(f"Original fusion size: {len(original_bytes)} bytes")
            print(f"Size difference: {len(original_bytes) - len(fused_bytes)} bytes")
            print("(Positive difference means filtered version is smaller)")
        except Exception as e:
            print(f"Could not load original fusion result for comparison: {e}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":

    print("=== 原始文件路径方式 ===")
    # Example usage - 原始方式
    datas = {
        "front_lidar": "test_data/front_lidar.pcd",
        "left_lidar": "test_data/left_lidar.pcd",
        "right_lidar": "test_data/right_lidar.pcd",
    }
    calib = {
        "front_lidar": np.eye(4),
        "left_lidar": np.eye(4),
        "right_lidar": np.eye(4),
    }
    save_path = "test_data/results/fused.pcd"
    
    fusion_pcd(datas, calib, save_path)
    
    print("\n=== 字节数据方式 ===")
    # Example usage - 字节数据方式
    datas_bytes = {}
    for sensor, file_path in datas.items():
        datas_bytes[sensor] = load_pcd_as_bytes(file_path)
        print(f"Loaded {sensor}: {len(datas_bytes[sensor])} bytes")
    
    # 使用字节数据进行融合
    fused_bytes = fusion_pcd_bytes(datas_bytes, calib, compression="binary_compressed")
    print(f"Fused PCD size: {len(fused_bytes)} bytes")
    
    # 保存融合后的字节数据
    bytes_save_path = "test_data/results/fused_from_bytes.pcd"
    save_bytes_as_pcd(fused_bytes, bytes_save_path)
    print(f"Saved fused PCD to: {bytes_save_path}")
    
    # 验证两种方式的结果是否一致
    original_size = os.path.getsize(save_path)
    bytes_size = os.path.getsize(bytes_save_path)
    print(f"\n=== 结果对比 ===")
    print(f"原始方式文件大小: {original_size} bytes")
    print(f"字节方式文件大小: {bytes_size} bytes")
    print(f"大小差异: {abs(original_size - bytes_size)} bytes")
    
    # 测试新的fuse_pointclouds函数
    test_fuse_pointclouds()