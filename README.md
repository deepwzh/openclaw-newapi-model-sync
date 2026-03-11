# OpenClaw 模型同步工具

交互式 CLI 工具，用于从 New API 获取模型列表并同步到 OpenClaw 配置。

## 功能特性

- ✅ 自动从 New API 获取可用模型
- ✅ 智能识别推理模型（标记 🧠）
- ✅ 显示上下文窗口大小
- ✅ 交互式选择主模型（单选）
- ✅ 交互式选择 Agent 可用模型（多选，复选框）
- ✅ 自动备份配置文件
- ✅ 彩色输出，清晰易读

## 安装

### 全局安装（推荐）

```bash
uv tool install ~/tools/openclaw-model-sync
```

安装后可以直接使用：

```bash
openclaw-sync-models
```

### 开发模式

```bash
cd ~/tools/openclaw-model-sync
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 使用

```bash
# 使用默认配置路径 (~/.openclaw/openclaw.json)
openclaw-sync-models

# 或指定配置文件
openclaw-sync-models -c /path/to/openclaw.json
```

## 交互流程

1. **加载配置** - 读取现有 openclaw.json
2. **获取模型** - 从 New API 拉取模型列表
3. **选择主模型** - 单选，设置到 `agents.defaults.model.primary`
4. **选择可用模型** - 多选（空格勾选），设置到 `agents.defaults.models`
5. **确认更新** - 显示摘要并确认
6. **备份并写入** - 自动备份原配置，写入新配置

## 更新后

记得重启 Gateway：

```bash
openclaw gateway restart
```

## 卸载

```bash
uv tool uninstall openclaw-model-sync
```

## 依赖

- Python 3.8+
- questionary (交互式 TUI)
