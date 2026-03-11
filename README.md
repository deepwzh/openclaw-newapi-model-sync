# OpenClaw New API 模型同步工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

交互式 CLI 工具，用于从 New API 获取模型列表并同步到 OpenClaw 配置文件。

## 功能特性

- ✅ 自动从 New API 获取可用模型
- ✅ 智能识别推理模型（标记 🧠）
- ✅ 自动设置上下文窗口和输出限制
- ✅ 交互式选择主模型（单选）
- ✅ 交互式选择 Agent 可用模型（多选，复选框）
- ✅ 自动备份配置文件
- ✅ 彩色输出，清晰易读
- ✅ 支持多 Provider

## 使用

### uvx 免安装运行（推荐）

无需安装，直接运行：

```bash
uvx --from git+https://github.com/deepwzh/openclaw-newapi-model-sync.git openclaw-sync-models
```

### 全局安装

```bash
# 从 GitHub 安装
uv tool install git+https://github.com/deepwzh/openclaw-newapi-model-sync.git

# 安装后直接使用
openclaw-sync-models
```

### 开发模式

```bash
git clone https://github.com/deepwzh/openclaw-newapi-model-sync.git
cd openclaw-newapi-model-sync
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 命令行参数

```bash
# 使用默认配置路径，交互式选择 provider
openclaw-sync-models

# 指定 provider 名称
openclaw-sync-models -p new-api

# 指定配置文件路径
openclaw-sync-models -c /path/to/openclaw.json

# 组合使用
openclaw-sync-models -c /path/to/openclaw.json -p my-provider
```

| 参数 | 说明 |
|------|------|
| `-c, --config` | 指定配置文件路径（默认: `~/.openclaw/openclaw.json`） |
| `-p, --provider` | 指定 provider 名称，不指定则交互式选择 |

## 前提条件

确保你的 OpenClaw 配置文件 (`~/.openclaw/openclaw.json`) 中已配置 provider：

```json
{
  "models": {
    "providers": {
      "new-api": {
        "baseUrl": "http://your-new-api-server:3000/v1",
        "apiKey": "your-api-key",
        "api": "openai-completions"
      },
      "another-provider": {
        "baseUrl": "http://another-server:3000/v1",
        "apiKey": "another-api-key",
        "api": "openai-completions"
      }
    }
  }
}
```

工具会自动识别所有可用的 provider，你可以：
- 使用 `-p` 参数直接指定
- 不指定参数，交互式选择

## 交互流程

1. **加载配置** - 读取现有 `openclaw.json`
2. **选择 Provider** - 选择要同步的 provider
3. **获取模型** - 从 API 拉取模型列表
4. **同步 Provider** - 将模型列表写入配置
5. **配置 Agent**（可选）
   - 选择主模型 → `agents.defaults.model.primary`
   - 选择可用模型 → `agents.defaults.models`
6. **备份并写入** - 自动备份原配置，写入新配置

### 更新后

重启 OpenClaw Gateway 以应用更改：

```bash
openclaw gateway restart
```

## 模型识别规则

### 推理模型标记

以下模型会被标记为推理模型（🧠）：
- 名称包含 `thinking`
- 名称包含 `pro`
- 名称包含 `gpt-5`
- 名称包含 `glm-4.6`
- 名称包含 `plus`
- 名称包含 `o1` 或 `o3`

### 上下文窗口

- **Gemini 系列**: 1M tokens 输入，64K 输出
- **Claude 系列**: 200K tokens 输入，8K 输出
- **其他模型**: 128K tokens 输入，16K 输出

### API 格式

- **GPT 系列**: 自动设置 `openai-responses`
- **Claude 系列**: 自动设置 `anthropic-messages`
- **其他模型**: 沿用 provider 默认配置

## 卸载

```bash
uv tool uninstall openclaw-newapi-model-sync
```

## 项目结构

```
openclaw-newapi-model-sync/
├── openclaw_model_sync.py   # 主程序
├── pyproject.toml           # 项目配置
├── README.md                # 本文档
├── LICENSE                  # MIT License
└── .gitignore               # Git 忽略规则
```

## 安全说明

- ⚠️ **请勿提交包含 API Key 的配置文件到版本控制**
- API 凭据从现有 OpenClaw 配置中读取，工具本身不存储任何密钥
- 每次更新前会自动备份原配置文件 (`.json.bak`)

## 依赖

- [questionary](https://github.com/tmbo/questionary) - 交互式 TUI

## License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 相关项目

- [OpenClaw](https://github.com/openclaw/openclaw) - 你的个人 AI 助手框架
- [New API](https://github.com/Calcium-Ion/new-api) - OpenAI API 管理与分发系统