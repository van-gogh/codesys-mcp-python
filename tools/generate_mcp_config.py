import argparse
import json

"""
生成 MCP 客户端可导入的配置 JSON 片段

两种模式：
- module：使用 `python -m mcp_codesys.cli --stdio ...` 方式启动；
- script：使用已安装的脚本入口 `codesys-mcp-tool-py --stdio ...`。
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['module','script'], default='module')
    p.add_argument('--codesys-path', required=True)
    p.add_argument('--codesys-profile', required=True)
    args = p.parse_args()

    if args.mode == 'module':
        cfg = {
            "mcpServers": {
                "codesys_local": {
                    "command": "python",
                    "args": [
                        "-m", "mcp_codesys.cli",
                        "--stdio",
                        "--codesys-path", args.codesys_path,
                        "--codesys-profile", args.codesys_profile
                    ]
                }
            }
        }
    else:
        cfg = {
            "mcpServers": {
                "codesys_local": {
                    "command": "codesys-mcp-tool-py",
                    "args": [
                        "--stdio",
                        "--codesys-path", args.codesys_path,
                        "--codesys-profile", args.codesys_profile
                    ]
                }
            }
        }

    # 打印格式化的 JSON，便于直接复制到 MCP 客户端配置
    print(json.dumps(cfg, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
