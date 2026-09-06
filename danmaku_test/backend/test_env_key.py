"""测试 backend/.env 中的 DeepSeek API key 是否可用。

用法：
    python test_env_key.py
    python test_env_key.py --env-file .env

退出码：
    0 - key 有效
    1 - key 缺失或无效
    2 - 网络、配置或依赖错误
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


KEY_NAME = "DEEPSEEK_API_KEY"
DEFAULT_BASE_URL = "https://api.deepseek.com"


def load_env_file(path: Path) -> dict[str, str]:
    """读取简单的 KEY=VALUE .env 文件，不打印任何 value。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            print(f"警告：忽略 {path.name} 第 {line_number} 行（缺少 '='）。")
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[name] = value
    return values


def get_key(env_file: Path, key_name: str) -> str:
    # 与常见 dotenv 行为一致：系统环境变量优先于 .env。
    file_values = load_env_file(env_file)
    return os.getenv(key_name, file_values.get(key_name, "")).strip()


def test_key(api_key: str, base_url: str, timeout: float) -> int:
    try:
        import requests
    except ImportError:
        print("错误：缺少 requests，请先安装 backend/requirement.txt 中的依赖。")
        return 2

    url = f"{base_url.rstrip('/')}/models"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.RequestException as error:
        print(f"网络错误：{error.__class__.__name__}: {error}")
        return 2

    if response.status_code == 200:
        print(f"有效：{KEY_NAME} 可以访问 DeepSeek API。")
        return 0
    if response.status_code in (401, 403):
        print(f"无效：{KEY_NAME} 未通过鉴权（HTTP {response.status_code}）。")
        return 1
    if response.status_code == 429:
        print("暂时无法判断：API 返回 HTTP 429，key 可能有效但请求受限。")
        return 2

    print(f"暂时无法判断：API 返回 HTTP {response.status_code}。")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="测试 DeepSeek API key 是否有效")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(__file__).with_name(".env"),
        help=".env 文件路径，默认是脚本同目录下的 .env",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API 地址，默认是 {DEFAULT_BASE_URL}",
    )
    parser.add_argument("--timeout", type=float, default=15, help="请求超时时间（秒）")
    args = parser.parse_args()

    api_key = get_key(args.env_file, KEY_NAME)
    if not api_key:
        print(f"缺失：没有找到 {KEY_NAME}（检查系统环境变量或 {args.env_file}）。")
        return 1

    return test_key(api_key, args.base_url, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
