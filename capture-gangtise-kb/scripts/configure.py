#!/usr/bin/env python3
"""
Gangtise Knowledge Base Skill 配置与凭证管理。

凭证加载优先级：
  1. 环境变量 GANGTISE_ACCESS_KEY / GANGTISE_SECRET_KEY
  2. .env 文件（项目根目录）
  3. config.json（兼容旧配置）
"""
import json
import os
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
CONFIG_FILE = SKILL_ROOT / "config.json"
ENV_FILE = SKILL_ROOT / ".env"

# 环境变量名
ENV_ACCESS_KEY = "GANGTISE_ACCESS_KEY"
ENV_SECRET_KEY = "GANGTISE_SECRET_KEY"


def _load_dotenv() -> dict[str, str]:
    """从 .env 文件解析 KEY=VALUE 对，不引入额外依赖。"""
    result: dict[str, str] = {}
    if not ENV_FILE.exists():
        return result
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value
    except Exception:
        pass
    return result


def _load_config_json() -> dict:
    """从 config.json 加载旧格式配置。"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_credentials() -> tuple[str | None, str | None]:
    """
    获取 API 凭证，按优先级尝试：
      1. 环境变量
      2. .env 文件
      3. config.json
    返回 (access_key, secret_key)。
    """
    # 1. 环境变量
    ak = os.environ.get(ENV_ACCESS_KEY)
    sk = os.environ.get(ENV_SECRET_KEY)
    if ak and sk:
        return ak, sk

    # 2. .env 文件
    dotenv = _load_dotenv()
    ak = dotenv.get(ENV_ACCESS_KEY)
    sk = dotenv.get(ENV_SECRET_KEY)
    if ak and sk:
        return ak, sk

    # 3. config.json（兼容旧配置）
    config = _load_config_json()
    return config.get('ACCESS_KEY'), config.get('SECRET_KEY')


def check_configured() -> bool:
    """检查凭证是否可用。"""
    ak, sk = get_credentials()
    return bool(ak and sk)


def save_config(config: dict) -> bool:
    """保存配置到 config.json（仅供交互式 configure 使用）。"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.chmod(CONFIG_FILE, 0o600)
        return True
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)
        return False


def main():
    print("=" * 60)
    print("Gangtise Knowledge Base - Configuration Setup")
    print("=" * 60)
    print()

    # 先检查环境变量 / .env 是否已配置
    if check_configured():
        ak, _ = get_credentials()
        print(f"已检测到有效凭证（Access Key: {ak[:4]}...）")
        print("如需更新，请修改环境变量或 .env 文件。")
        return

    print("请输入 Gangtise API 凭证。")
    print("获取地址: https://open.gangtise.com")
    print()

    # 交互式输入，写入 .env 文件
    ak = input("Access Key: ").strip()
    sk = input("Secret Key: ").strip()

    if not ak or not sk:
        print("\nError: Both Access Key and Secret Key are required.", file=sys.stderr)
        sys.exit(1)

    # 写入 .env 文件
    try:
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{ENV_ACCESS_KEY}={ak}\n")
            f.write(f"{ENV_SECRET_KEY}={sk}\n")
        os.chmod(ENV_FILE, 0o600)
        print(f"\n凭证已保存到: {ENV_FILE}")
        print("也可直接设置环境变量 GANGTISE_ACCESS_KEY / GANGTISE_SECRET_KEY。")
    except Exception as e:
        print(f"\n保存失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
