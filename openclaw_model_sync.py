#!/usr/bin/env python3
"""
OpenClaw 模型同步 CLI 工具
用于从 New API 获取模型列表并同步到 openclaw.json 配置
"""

import json
import subprocess
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

try:
    import questionary
    from questionary import Style
except ImportError:
    print("❌ 缺少依赖: questionary")
    print("请安装: uv pip install questionary")
    sys.exit(1)

# 自定义样式
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])

# ANSI 颜色
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text: str):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


class ModelSyncCLI:
    def __init__(self, config_path: str = None, provider_name: str = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认查找 ~/.openclaw/openclaw.json
            openclaw_dir = Path.home() / ".openclaw"
            self.config_path = openclaw_dir / "openclaw.json"
        
        self.config = {}
        self.provider_name = provider_name  # 可能为 None，需要后续选择
        self.api_base = None
        self.api_key = None
        
    def load_config(self) -> bool:
        """加载现有配置"""
        if not self.config_path.exists():
            print_error(f"配置文件不存在: {self.config_path}")
            return False
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print_success(f"已加载配置: {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            print_error(f"配置文件格式错误: {e}")
            return False
        except Exception as e:
            print_error(f"加载配置失败: {e}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """获取配置中所有可用的 provider 名称"""
        providers = self.config.get("models", {}).get("providers", {})
        return list(providers.keys())
    
    def select_provider(self) -> Optional[str]:
        """交互式选择 provider"""
        providers = self.get_available_providers()
        
        if not providers:
            print_error("配置中没有找到任何 provider")
            return None
        
        if len(providers) == 1:
            selected = providers[0]
            print_info(f"只有一个 provider，自动选择: {selected}")
            return selected
        
        print_header("选择 Provider")
        print_info(f"发现 {len(providers)} 个 provider")
        
        choices = [
            questionary.Choice(
                title=f"  {p}",
                value=p
            )
            for p in providers
        ]
        
        try:
            # 默认选择第一个或之前指定的
            default_value = self.provider_name if self.provider_name in providers else providers[0]
            
            selected = questionary.select(
                "选择要同步的 provider:",
                choices=choices,
                default=default_value,
                style=custom_style,
                use_arrow_keys=True
            ).ask()
            
            if selected:
                print_success(f"已选择 provider: {selected}")
            
            return selected
            
        except KeyboardInterrupt:
            print("\n")
            return None
    
    def load_provider_config(self) -> bool:
        """加载指定 provider 的 API 配置"""
        providers = self.config.get("models", {}).get("providers", {})
        provider_config = providers.get(self.provider_name, {})
        
        self.api_base = provider_config.get("baseUrl", "http://127.0.0.1:3000/v1")
        self.api_key = provider_config.get("apiKey", "")
        
        if not self.api_key:
            print_error(f"Provider '{self.provider_name}' 配置中未找到 API Key")
            return False
        
        print_info(f"API 地址: {self.api_base}")
        return True
    
    def fetch_models(self) -> List[Dict]:
        """从 API 获取模型列表"""
        print_info("正在获取模型列表...")
        
        curl_cmd = [
            'curl', '-s', '--location', '--request', 'GET',
            f'{self.api_base}/models',
            '--header', f'Authorization: Bearer {self.api_key}'
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            models = data.get("data", [])
            
            if not models:
                print_warning("未获取到任何模型")
                return []
            
            print_success(f"获取到 {len(models)} 个模型")
            return models
            
        except subprocess.CalledProcessError as e:
            print_error(f"API 请求失败: {e}")
            return []
        except json.JSONDecodeError as e:
            print_error(f"解析响应失败: {e}")
            return []
        except Exception as e:
            print_error(f"获取模型失败: {e}")
            return []
    
    def process_model(self, model_data: Dict) -> Dict:
        """处理单个模型数据"""
        m_id = model_data.get("id", "")
        model_api = model_data.get("api")
        
        # 智能识别模型特性
        is_reasoning = any(kw in m_id.lower() for kw in [
            "thinking", "pro", "gpt-5", "glm-4.6", "plus", "o1", "o3"
        ])
        is_gemini = "gemini" in m_id.lower()
        is_claude = "claude" in m_id.lower()
        
        # 根据模型类型设置上下文窗口
        if is_gemini:
            context_window = 1048576  # 1M tokens
            max_tokens = 64000
        elif is_claude:
            context_window = 200000
            max_tokens = 8192
        else:
            context_window = 128000
            max_tokens = 16384
        
        model_info = {
            "id": m_id,
            "name": f"{m_id} ({self.provider_name})",
            "reasoning": is_reasoning,
            "input": ["text", "image"],
            "cost": {
                "input": 0,
                "output": 0,
                "cacheRead": 0,
                "cacheWrite": 0
            },
            "contextWindow": context_window,
            "maxTokens": max_tokens
        }

        # 如果是 gpt 开头的模型，统一使用 openai-responses；
        # 如果是 claude 模型，使用 anthropic-messages；
        # 否则仅当服务端声明为 openai-responses 时才为该模型单独设置 api 字段。
        # 其他情况沿用 provider 顶层的默认配置（通常是 openai-completions），不再重复写入。
        if m_id.lower().startswith("gpt"):
            model_info["api"] = "openai-responses"
        elif is_claude:
            model_info["api"] = "anthropic-messages"
        elif model_api == "openai-responses":
            model_info["api"] = "openai-responses"

        return model_info
    
    def format_model_choice(self, model: Dict) -> str:
        """格式化模型选项显示"""
        reasoning_tag = "🧠 " if model.get("reasoning") else "   "
        context = model.get("contextWindow", 0)
        context_str = f"{context//1000}K" if context < 1000000 else f"{context//1000000}M"
        
        return f"{reasoning_tag}{model['id']:<45} [{context_str:>6}]"
    
    def model_id_with_provider(self, model_id: str) -> str:
        """生成带 provider 前缀的模型 ID"""
        return f"{self.provider_name}/{model_id}"
    
    def select_primary_model(self, 
                             models: List[Dict],
                             default_primary: Optional[str] = None) -> Optional[str]:
        """选择主模型"""
        print_header("选择主模型 (Primary)")
        
        choices = [
            questionary.Choice(
                title=self.format_model_choice(model),
                value=self.model_id_with_provider(model['id'])
            )
            for model in models
        ]
        
        # 添加跳过选项
        choices.insert(0, questionary.Choice(title="⏭️  跳过", value=None))
        
        try:
            # 如果有默认主模型且在当前列表中，则作为默认选中项
            default_value = None
            if default_primary is not None:
                values = [c.value for c in choices]
                if default_primary in values:
                    default_value = default_primary

            selected = questionary.select(
                "选择主模型:",
                choices=choices,
                default=default_value,
                style=custom_style,
                use_arrow_keys=True
            ).ask()
            
            if selected:
                print_success(f"已选择主模型: {selected}")
            
            return selected
            
        except KeyboardInterrupt:
            print("\n")
            return None
    
    def select_agent_models(self, 
                            models: List[Dict],
                            default_models: Optional[List[str]] = None) -> List[str]:
        """选择 agent 可用模型（多选）"""
        print_header("选择 Agent 可用模型（多选）")
        print_info("使用空格键勾选，回车确认")

        default_models = default_models or []
        default_set = set(default_models)

        choices = [
            questionary.Choice(
                title=self.format_model_choice(model),
                value=self.model_id_with_provider(model['id']),
                checked=(self.model_id_with_provider(model['id']) in default_set)
            )
            for model in models
        ]
        
        try:
            selected = questionary.checkbox(
                "选择可用模型 (空格勾选，回车确认):",
                choices=choices,
                style=custom_style,
                use_arrow_keys=True
            ).ask()
            
            if selected:
                print_success(f"已选择 {len(selected)} 个模型:")
                for m in selected:
                    print(f"  • {m}")
            
            return selected or []
            
        except KeyboardInterrupt:
            print("\n")
            return []
    
    def backup_config(self) -> bool:
        """备份配置文件"""
        backup_path = self.config_path.with_suffix('.json.bak')
        try:
            import shutil
            shutil.copy2(self.config_path, backup_path)
            print_success(f"已备份至: {backup_path}")
            return True
        except Exception as e:
            print_error(f"备份失败: {e}")
            return False
    
    def sync_provider_models(self, processed_models: List[Dict]) -> bool:
        """同步模型列表到 provider（不涉及 agent 配置）"""
        try:
            # 确保结构存在
            if "models" not in self.config:
                self.config["models"] = {}
            if "providers" not in self.config["models"]:
                self.config["models"]["providers"] = {}
            if self.provider_name not in self.config["models"]["providers"]:
                self.config["models"]["providers"][self.provider_name] = {
                    "baseUrl": self.api_base,
                    "apiKey": self.api_key,
                    "api": "openai-completions"
                }
            
            # 更新模型列表
            self.config["models"]["providers"][self.provider_name]["models"] = processed_models
            
            # 备份并写入
            self.backup_config()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print_error(f"同步失败: {e}")
            return False

    def get_agent_defaults(self, processed_models: List[Dict]) -> (Optional[str], List[str]):
        """
        从现有配置中读取 Agent 默认主模型和可用模型，并根据当前可用模型列表进行过滤。
        """
        available_ids = {self.model_id_with_provider(m['id']) for m in processed_models}

        agents_cfg = self.config.get("agents", {})
        defaults_cfg = agents_cfg.get("defaults", {})

        # 主模型
        model_cfg = defaults_cfg.get("model")
        primary_cfg = model_cfg.get("primary") if isinstance(model_cfg, dict) else None
        default_primary = (
            primary_cfg
            if isinstance(primary_cfg, str) and primary_cfg in available_ids
            else None
        )

        # 可用模型列表
        models_cfg = defaults_cfg.get("models", {})
        default_models: List[str] = []
        if isinstance(models_cfg, dict):
            for model_id in models_cfg.keys():
                if isinstance(model_id, str) and model_id in available_ids:
                    default_models.append(model_id)

        return default_primary, default_models
    
    def update_agent_config(self, 
                           primary_model: Optional[str] = None,
                           agent_models: Optional[List[str]] = None) -> bool:
        """更新 agent 配置"""
        try:
            # 确保 agents 结构存在
            if "agents" not in self.config:
                self.config["agents"] = {}
            if "defaults" not in self.config["agents"]:
                self.config["agents"]["defaults"] = {}
            
            # 设置主模型
            if primary_model:
                if "model" not in self.config["agents"]["defaults"]:
                    self.config["agents"]["defaults"]["model"] = {}
                self.config["agents"]["defaults"]["model"]["primary"] = primary_model
            
            # 设置可用模型列表
            if agent_models:
                if "models" not in self.config["agents"]["defaults"]:
                    self.config["agents"]["defaults"]["models"] = {}
                
                # 为每个模型创建空配置对象
                for model_id in agent_models:
                    self.config["agents"]["defaults"]["models"][model_id] = {}
            
            # 备份并写入
            self.backup_config()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print_error(f"更新失败: {e}")
            return False
    
    def run(self):
        """主流程"""
        print_header("OpenClaw 模型同步工具")
        
        # 1. 加载配置
        if not self.load_config():
            sys.exit(1)
        
        # 2. 选择 provider（如果未指定）
        if not self.provider_name:
            self.provider_name = self.select_provider()
            if not self.provider_name:
                print_error("未选择 provider")
                sys.exit(1)
        else:
            # 验证指定的 provider 是否存在
            providers = self.get_available_providers()
            if self.provider_name not in providers:
                print_error(f"Provider '{self.provider_name}' 不存在")
                print_info(f"可用的 provider: {', '.join(providers)}")
                sys.exit(1)
            print_info(f"使用指定的 provider: {self.provider_name}")
        
        # 3. 加载 provider 的 API 配置
        if not self.load_provider_config():
            sys.exit(1)
        
        # 4. 获取模型
        raw_models = self.fetch_models()
        if not raw_models:
            print_error("无法继续：未获取到模型数据")
            sys.exit(1)
        
        # 5. 处理模型
        processed_models = [self.process_model(m) for m in raw_models]
        
        # 6. 先同步模型列表到 provider
        print_header("同步模型列表")
        print_info(f"将 {len(processed_models)} 个模型同步到 {self.provider_name} provider")
        
        if not self.sync_provider_models(processed_models):
            print_error("同步失败")
            sys.exit(1)
        
        print_success("Provider 模型列表已同步")
        
        # 7. 询问是否配置 agent 默认模型
        try:
            configure_agent = questionary.confirm(
                "是否配置 Agent 默认模型?",
                default=True,
                style=custom_style
            ).ask()
        except KeyboardInterrupt:
            print("\n")
            print_success("模型列表已同步，Agent 配置已跳过")
            sys.exit(0)
        
        if not configure_agent:
            print_success("模型列表已同步，Agent 配置已跳过")
            sys.exit(0)

        # 8. 从现有配置中读取 Agent 默认主模型和可用模型，作为本次交互的默认值
        default_primary, default_agent_models = self.get_agent_defaults(processed_models)

        # 9. 选择主模型
        primary_model = self.select_primary_model(
            processed_models,
            default_primary=default_primary
        )
        
        # 10. 选择 agent 可用模型
        agent_models = self.select_agent_models(
            processed_models,
            default_models=default_agent_models
        )
        
        # 11. 确认更新 agent 配置
        if primary_model or agent_models:
            print_header("确认 Agent 配置")
            if primary_model:
                print_info(f"主模型: {primary_model}")
            if agent_models:
                print_info(f"可用模型: {len(agent_models)} 个")
            
            try:
                confirm = questionary.confirm(
                    "确认更新 Agent 配置?",
                    default=True,
                    style=custom_style
                ).ask()
                
                if not confirm:
                    print_warning("Agent 配置已取消")
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\n")
                print_warning("Agent 配置已取消")
                sys.exit(0)
            
            if self.update_agent_config(primary_model, agent_models):
                print_header("完成")
                print_success("配置更新成功！")
                print_info("请重启 OpenClaw Gateway 以应用更改:")
                print(f"  {Colors.CYAN}openclaw gateway restart{Colors.END}")
            else:
                print_error("更新失败")
                sys.exit(1)
        else:
            print_success("模型列表已同步")
            print_info("请重启 OpenClaw Gateway 以应用更改:")
            print(f"  {Colors.CYAN}openclaw gateway restart{Colors.END}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 模型同步工具")
    parser.add_argument(
        "-c", "--config",
        help="指定配置文件路径 (默认: ~/.openclaw/openclaw.json)",
        default=None
    )
    parser.add_argument(
        "-p", "--provider",
        help="指定 provider 名称 (如 new-api)，不指定则交互式选择",
        default=None
    )
    
    args = parser.parse_args()
    
    cli = ModelSyncCLI(args.config, args.provider)
    cli.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}已取消{Colors.END}")
        sys.exit(0)