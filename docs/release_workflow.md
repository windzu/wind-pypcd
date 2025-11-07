# 发布流程说明

本文档描述从拉取新分支到发布 PyPI 版本的推荐流程。请在执行前确认 `PYPI_API_TOKEN` 已配置在 GitHub 仓库的 Secrets 中。

## 1. 准备与分支策略

1. 从 `main` 拉取最新代码：`git checkout main && git pull origin main`
2. 为新功能或修复创建分支：`git checkout -b feat/<feature-name>`
3. 若本次迭代涉及重要功能或破坏性变更，请在开发过程中同步更新：
   - `pyproject.toml` 中的 `version`
   - `CHANGELOG.md` 中对应版本的条目
   - 相关文档（如 README、API 文档等）

## 2. 开发与测试

- 遵循项目的代码规范，必要时更新或新增测试。
- 使用 `tox -e py38,py39,py310,py312 -- -vv` 确认所有受支持环境通过。
- 更新 `docs/features_and_examples.md`、`docs/development_guide.md` 等文档，确保示例与流程同步。

## 3. 提交与拉取请求（PR）

1. 将修改提交到远程分支，并创建 PR 合并至 `main`。
2. 在 PR 描述中：
   - 概述主要变更
   - 指出版本号与 changelog 是否已更新
   - 链接相关 Issue（如有）
3. Wait for code review 并解决反馈。

## 4. 合并后操作

1. PR 合并到 `main` 后，从最新 `main` 创建 Git tag（建议命名为 `v<版本号>`），或在 GitHub Release 页面草拟新发布时指定该 tag。
2. 在 GitHub 上点击“Draft a new release”：
   - 选择合适的 tag（如 `v0.3.1`）
   - Release title 通常与版本号一致
   - Release notes 可参考 `CHANGELOG.md` 中对应条目，可选择“自动生成 Release Notes”进行补充
3. 点击 “Publish release”。

## 5. 自动化发布到 PyPI

- 发布动作会触发 `.github/workflows/publish-release.yml`
  - 校验 Git tag 与 `pyproject.toml` 版本一致
  - 构建 `sdist` 与 `wheel`
  - 使用 `PYPI_API_TOKEN` 上传到 PyPI
- 若 workflow 失败，可在 Actions 页面查看日志并重新发布（或删除 release 后重新创建）。

## 6. 其他注意事项

- 请确保 `pyproject.toml` 的 `version` 与 Release tag 对齐（例如 tag 为 `v0.3.1`，版本号应为 `0.3.1`）。
- 若需要撤销某次发布，请及时在 PyPI 删除相应文件，并更新 Release 信息。
- 如果未来需要支持 TestPyPI 或预发布流程，可在 workflow 中扩展额外 job。
