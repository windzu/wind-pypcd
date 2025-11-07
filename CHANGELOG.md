# Changelog

所有显著的变更会记录在此文档中。遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的格式，并基于语义化版本控制。

## [Unreleased]

- 在此处记录尚未发布到 PyPI 的改动。准备发布前，请将条目移动到新的版本章节。

## [0.4.0] - 2025-11-07

### Added

- 新增轴对齐裁剪函数 `crop_point_cloud`、`crop_pcd`、`crop_pcd_from_bytes` 及示例文档，支持按 min/max XYZ 裁剪点云。
- 创建 `.github/workflows/publish-release.yml`，在发布 Release 时自动构建并上传包到 PyPI。
- 补充 `docs/release_workflow.md` 与开发指南/README 链接，明确版本发布流程，新增 `CHANGELOG.md` 模板。

## [0.3.0] - 2025-11-07

- 初始整理的变更记录（版本号与发布日期请在下次发布前更新）。
