# 开发环境与测试指南

本文档面向项目贡献者，说明如何准备开发环境并验证功能。当前官方支持的解释器版本为 Python 3.8、3.9、3.10 与 3.12。

## 1. 准备解释器

推荐使用 [uv](https://github.com/astral-sh/uv) 管理多版本 Python：

```bash
uv python install 3.8 3.9 3.10 3.12
```

安装完成后，可通过 `uv python list` 检查已就绪的解释器。

如未使用 uv，也可以从系统包管理器或官方安装包获取对应 Python 版本，并确保它们出现在 `python3.x` 可执行路径中。

## 2. 创建虚拟环境

任意支持版本的解释器都能创建虚拟环境。以下示例使用 uv：

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
```

或使用标准库 `venv`：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

为了避免意外混用系统包，建议始终在激活虚拟环境后再进行依赖安装与测试。

## 3. 安装依赖

开发必备依赖仅包含项目本身、`numpy`、`python-lzf` 与 `pytest`：

```bash
pip install -e .
pip install pytest
```

如需运行文档示例或额外工具，请根据需要手动安装其它第三方包。

## 4. 使用 tox 运行测试矩阵

tox 已预配置好 4 个环境（`py38`、`py39`、`py310`、`py312`），并自动设置 `PYTHONPATH=src` 以复用源码：

```bash
tox                # 运行全部支持版本
tox -e py310       # 仅运行指定版本
tox -- -k binary   # 传递自定义 pytest 过滤条件
```

tox 会在本地自动创建临时虚拟环境，并安装打包后的分发件用于测试，能够较好模拟最终用户场景。

## 5. 手动运行 pytest

若只需在当前虚拟环境内快速验证，可直接运行 pytest：

```bash
export PYTHONPATH=$(pwd)/src
pytest -vv
```

需要开启特定测试或调试时，可结合 `-k`、`-x` 等 pytest 参数。

## 6. 常见问题排查

- **解释器缺失**：当 tox 提示缺少某个 `py3x` 环境时，请确认该版本已通过 uv 安装并在 PATH 中可见。
- **依赖冲突**：开发环境中引入额外包后，如遇编译或导入冲突，建议创建全新虚拟环境重试。
- **测试性能**：当前测试套件使用自生成的小型点云数据，正常情况下执行时间 <1 秒。如明显变慢，可检查是否加载了大型外部数据。

## 7. 提交前检查清单

- 确认所有相关 tox 环境通过：`tox`。
- 如修改了依赖或用户文档，请同步更新 `pyproject.toml`、`README.md` 以及本文档。
- 遵循项目现有的代码风格并保持注释精简。

## 8. 发布前的额外步骤

- 在进入 PR 之前完成版本号与 `CHANGELOG.md` 的更新，版本格式遵循语义化版本控制。
- 合并至 `main` 后按照 `docs/release_workflow.md` 中的步骤草拟 GitHub Release 并发布。
- Release notes 建议基于 changelog 编辑，确保与最终 PyPI 发布内容一致。

感谢你的贡献，祝开发顺利！
