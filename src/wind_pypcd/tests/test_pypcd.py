"""
Basic sanity checks for wind_pypcd.
"""

from pathlib import Path

import numpy as np
import pytest

header1 = """\
# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z i
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH 500028
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 500028
DATA binary_compressed
"""

header2 = """\
VERSION .7
FIELDS x y z normal_x normal_y normal_z curvature boundary k vp_x vp_y vp_z principal_curvature_x principal_curvature_y principal_curvature_z pc1 pc2
SIZE 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4
TYPE F F F F F F F F F F F F F F F F F
COUNT 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
WIDTH 19812
HEIGHT 1
VIEWPOINT 0.0 0.0 0.0 1.0 0.0 0.0 0.0
POINTS 19812
DATA ascii
"""


def cloud_centroid(pc):
    xyz = np.empty((pc.points, 3), dtype=float)
    xyz[:, 0] = pc.pc_data["x"]
    xyz[:, 1] = pc.pc_data["y"]
    xyz[:, 2] = pc.pc_data["z"]
    return xyz.mean(0)


def make_sample_point_cloud():
    from wind_pypcd import pypcd

    dtype = np.dtype(
        [
            ("x", np.float32),
            ("y", np.float32),
            ("z", np.float32),
            ("intensity", np.float32),
        ]
    )
    arr = np.array(
        [
            (0.0, 0.5, -1.0, 1.0),
            (1.5, -0.25, 0.0, 2.0),
            (3.0, 2.0, 0.75, 0.5),
        ],
        dtype=dtype,
    )
    return pypcd.PointCloud.from_array(arr)


def test_parse_header():
    from wind_pypcd.pypcd import parse_header

    lines = header1.split("\n")
    md = parse_header(lines)
    assert md["version"] == "0.7"
    assert md["fields"] == ["x", "y", "z", "i"]
    assert md["size"] == [4, 4, 4, 4]
    assert md["type"] == ["F", "F", "F", "F"]
    assert md["count"] == [1, 1, 1, 1]
    assert md["width"] == 500028
    assert md["height"] == 1
    assert md["viewpoint"] == [0, 0, 0, 1, 0, 0, 0]
    assert md["points"] == 500028
    assert md["data"] == "binary_compressed"


def test_from_path(tmp_path):
    from wind_pypcd import pypcd

    original = make_sample_point_cloud()
    sample_path = tmp_path / "sample.pcd"
    original.save_pcd(sample_path, compression="binary_compressed")

    loaded = pypcd.PointCloud.from_path(sample_path)

    loaded_md = loaded.get_metadata()
    original_md = original.get_metadata()
    assert loaded_md["points"] == original_md["points"]
    assert loaded_md["width"] == original_md["width"]
    assert loaded_md["fields"] == list(original_md["fields"])
    np.testing.assert_equal(loaded.pc_data, original.pc_data)


def test_add_fields():
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()

    old_md = pc.get_metadata()
    # new_dt = [(f, pc.pc_data.dtype[f]) for f in pc.pc_data.dtype.fields]
    # new_data = [pc.pc_data[n] for n in pc.pc_data.dtype.names]
    md = {"fields": ["bla", "bar"], "count": [1, 1], "size": [4, 4], "type": ["F", "F"]}
    d = np.rec.fromarrays(
        (np.random.random(len(pc.pc_data)), np.random.random(len(pc.pc_data)))
    )
    newpc = pypcd.add_fields(pc, md, d)

    new_md = newpc.get_metadata()
    assert len(old_md["fields"]) + len(md["fields"]) == len(new_md["fields"])


def test_path_roundtrip_ascii(tmp_path):
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    md = pc.get_metadata()

    tmp_fname = tmp_path / "out_ascii.pcd"

    pc.save_pcd(tmp_fname, compression="ascii")

    assert tmp_fname.exists()

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    expected_md = md.copy()
    expected_md["data"] = "ascii"
    expected_md["version"] = "0.7"
    expected_md["fields"] = list(expected_md["fields"])
    assert md2 == expected_md

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)


def test_path_roundtrip_binary(tmp_path):
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    md = pc.get_metadata()

    tmp_fname = tmp_path / "out_binary.pcd"

    pc.save_pcd(tmp_fname, compression="binary")

    assert tmp_fname.exists()

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    expected_md = md.copy()
    expected_md["data"] = "binary"
    expected_md["version"] = "0.7"
    expected_md["fields"] = list(expected_md["fields"])
    assert md2 == expected_md

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)


def test_path_roundtrip_binary_compressed(tmp_path):
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    md = pc.get_metadata()

    tmp_fname = tmp_path / "out_compressed.pcd"

    pc.save_pcd(tmp_fname, compression="binary_compressed")

    assert tmp_fname.exists()

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    expected_md = md.copy()
    expected_md["data"] = "binary_compressed"
    expected_md["version"] = "0.7"
    expected_md["fields"] = list(expected_md["fields"])
    assert md2 == expected_md

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)


def test_cat_pointclouds():
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    pc2 = pc.copy()
    pc2.pc_data["x"] += 0.1
    pc3 = pypcd.cat_point_clouds(pc, pc2)
    md = pc.get_metadata()
    md2 = pc2.get_metadata()
    md3 = pc3.get_metadata()
    assert md3["fields"] == md["fields"]
    assert md3["width"] == md["width"] + md2["width"]


def test_ascii_bin1(tmp_path):
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    ascii_path = tmp_path / "cloud_ascii.pcd"
    binary_path = tmp_path / "cloud_binary.pcd"
    pc.save_pcd(ascii_path, compression="ascii")
    pc.save_pcd(binary_path, compression="binary")

    apc1 = pypcd.point_cloud_from_path(ascii_path)
    bpc1 = pypcd.point_cloud_from_path(binary_path)
    am = cloud_centroid(apc1)
    bm = cloud_centroid(bpc1)
    assert np.allclose(am, bm)


def test_pcd_to_bin_xyzi(tmp_path):
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    source_pcd = tmp_path / "source_cloud.pcd"
    pc.save_pcd(source_pcd, compression="binary_compressed")

    bin_path = tmp_path / "cloud_xyzi.bin"
    pypcd.pcd_to_bin(source_pcd, output_path=bin_path, target_format="xyzi")

    assert bin_path.exists()
    data = np.fromfile(bin_path, dtype=np.float32).reshape(-1, 4)
    assert data.shape[1] == 4
    assert data.shape[0] > 0
    assert np.isfinite(data).all()


def test_pointcloud_to_bin_defaults(tmp_path):
    from wind_pypcd import pypcd

    xyz = np.array([[0.0, 0.0, 0.0], [1.0, -1.0, 2.0]], dtype=np.float32)
    pc = pypcd.PointCloud.from_array_without_dtype(xyz, format="xyz")
    bin_path = tmp_path / "cloud_xyzit.bin"

    pypcd.pointcloud_to_bin(
        pc,
        output_path=bin_path,
        target_format="xyzit",
        default_intensity=5.5,
        default_time=0.1,
    )

    assert bin_path.exists()
    arr = np.fromfile(bin_path, dtype=np.float32).reshape(-1, 5)
    assert np.allclose(arr[:, 3], 5.5)
    assert np.allclose(arr[:, 4], 0.1)


def test_point_cloud_to_buffer_types():
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()

    ascii_buf = pypcd.point_cloud_to_buffer(pc, data_compression="ascii")
    binary_buf = pypcd.point_cloud_to_buffer(pc, data_compression="binary")
    compressed_buf = pypcd.point_cloud_to_buffer(
        pc, data_compression="binary_compressed"
    )

    assert isinstance(ascii_buf, str)
    assert isinstance(binary_buf, bytes)
    assert isinstance(compressed_buf, bytes)
    assert ascii_buf.startswith("VERSION")
    assert binary_buf.startswith(b"VERSION")
    assert compressed_buf.startswith(b"VERSION")


def test_point_cloud_bytes_roundtrip_binary():
    from wind_pypcd import pypcd

    pc = make_sample_point_cloud()
    blob = pc.to_bytes(compression="binary")

    assert isinstance(blob, bytes)
    restored = pypcd.PointCloud.from_bytes(blob)

    np.testing.assert_equal(pc.pc_data, restored.pc_data)
    assert restored.get_metadata()["data"] == "binary"
