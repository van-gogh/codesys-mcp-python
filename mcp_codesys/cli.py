import argparse
import os
import sys
from .server import run_mcp_server
from .codesys_interop import dry_run_command

"""
命令行入口（CLI）

用途：
- 以两种模式运行本服务器：
  1) `--stdio`：作为 MCP 服务器，通过标准输入输出与 MCP 客户端握手；
  2) `--dry-run`：不真正启动 CODESYS，仅打印将要执行的命令，便于检查环境与参数。

参数：
- `--codesys-path`：CODESYS.exe 的绝对路径；
- `--codesys-profile`：CODESYS 的 Profile 名称；
- `--workspace`：工作区目录（可选）；
- `--stdio`：启动 MCP stdio 模式；
- `--dry-run`：仅打印命令行。
"""

def main():
    # 解析命令行参数
    p = argparse.ArgumentParser()
    p.add_argument("--codesys-path", default="")
    p.add_argument("--codesys-profile", default="")
    p.add_argument("--workspace", default="")
    p.add_argument("--stdio", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args()

    # stdio 模式：启动 MCP 服务器
    if args.stdio:
        # 环境变量回退
        codesys_path = args.codesys_path or os.environ.get("CODESYS_PATH", "")
        codesys_profile = args.codesys_profile or os.environ.get("CODESYS_PROFILE", "")
        return run_mcp_server(codesys_path, codesys_profile, args.workspace, timeout=args.timeout)

    # dry-run 模式：打印即将执行的 CODESYS 调用命令
    if args.dry_run:
        codesys_path = args.codesys_path or os.environ.get("CODESYS_PATH", "")
        codesys_profile = args.codesys_profile or os.environ.get("CODESYS_PROFILE", "")
        print(dry_run_command(codesys_path, codesys_profile))
        return 0

    # 默认不做任何操作，保持返回码 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
