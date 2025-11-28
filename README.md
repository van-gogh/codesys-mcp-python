
# 纯 Python MCP 服务器（CODESYS）

这是一个使用纯 Python 实现的 MCP 服务器，面向 CODESYS V3 编程环境。它通过调用 `CODESYS.exe --profile --noUI --runscript` 执行内嵌脚本，实现项目管理、POU 创建、代码读写与编译等自动化操作，并提供标准 MCP 资源与工具端点。

## 功能
- 项目管理：打开、创建、保存、编译。
- POU 管理：创建 Program/FunctionBlock/Function，读写声明与实现代码，创建属性与方法。
- 资源：查询项目状态、遍历项目结构、读取指定 POU/方法/属性代码。

## 目录结构
- `mcp_codesys/`：核心包
  - `cli.py`：命令入口（`--stdio` 启动 MCP，`--dry-run` 展示调用）。
  - `server.py`：MCP 端点注册与调度。
  - `codesys_interop.py`：生成临时脚本、执行 CODESYS 命令并解析结果。
- `pyproject.toml`：项目元数据与脚本入口 `codesys-mcp-tool-py`。
- `LICENSE`：许可证。

## 安装
- 需要 Python ≥3.9。
- 安装依赖：`pip install mcp`。

## 什么是 MCP
- MCP（Model Context Protocol）是一种标准协议，客户端（如 Claude Desktop）通过标准输入输出（stdio）与服务器通信，调用服务器暴露的“工具”和“资源”。
- 本项目是一个 MCP 服务器，通过 `stdio` 与客户端连接；客户端只需在其配置中声明要调用的命令及参数。

## 使用
- 干运行（仅查看将执行的 CODESYS 命令）：
  - 未安装脚本入口：`python -m mcp_codesys.cli --dry-run --codesys-path "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe" --codesys-profile "CODESYS V3.5 SP21"`
  - 已安装脚本入口：`codesys-mcp-tool-py --dry-run --codesys-path "..." --codesys-profile "..."`
- 启动 MCP（stdio）：
  - 未安装脚本入口：`python -m mcp_codesys.cli --stdio --codesys-path "..." --codesys-profile "..."`
  - 已安装脚本入口：`codesys-mcp-tool-py --stdio --codesys-path "..." --codesys-profile "..."`

在 MCP 客户端（如 Claude Desktop）中将命令指向上述之一并传递必要参数即可。

## 配置参数
- `--codesys-path`：`CODESYS.exe` 的完整路径。
- `--codesys-profile`：CODESYS 的 Profile 名称。
- `--workspace`：工作区路径（可选）。
- `--stdio`：以标准输入输出模式运行 MCP。
- `--dry-run`：仅打印将要执行的 CODESYS 命令。

## 在 MCP 客户端中导入配置（JSON）
- 以 Claude Desktop 为例，在其 `settings.json` 的 `mcpServers` 字段中添加：
- 使用 Python 模块方式（无需安装脚本入口）：
```
{
  "mcpServers": {
    "codesys_local": {
      "command": "python",
      "args": [
        "-m", "mcp_codesys.cli",
        "--stdio",
        "--codesys-path", "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe",
        "--codesys-profile", "CODESYS V3.5 SP21"
      ]
    }
  }
}
```
- 使用已安装脚本入口（`pip install -e .` 后可用）：
```
{
  "mcpServers": {
    "codesys_local": {
      "command": "codesys-mcp-tool-py",
      "args": [
        "--stdio",
        "--codesys-path", "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe",
        "--codesys-profile", "CODESYS V3.5 SP21"
      ]
    }
  }
}
```
- 将上述 JSON 片段直接复制到客户端配置文件中即可完成导入。

## 生成配置 JSON（可选）
- 提供辅助脚本 `tools/generate_mcp_config.py`，自动输出可导入的 JSON：
- 示例：
  - `python tools/generate_mcp_config.py --mode module --codesys-path "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe" --codesys-profile "CODESYS V3.5 SP21"`
  - `python tools/generate_mcp_config.py --mode script --codesys-path "..." --codesys-profile "..."`

### 教程（一步一步生成并导入）
- 前提：已安装 Python ≥3.9；本仓库在本机可运行。
- 第1步：在项目根目录打开终端，执行以下其一生成 JSON：
  - 模块方式（无需安装脚本入口）：
    - `python tools/generate_mcp_config.py --mode module --codesys-path "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe" --codesys-profile "CODESYS V3.5 SP21"`
  - 脚本入口方式（已执行 `pip install -e .`）：
    - `python tools/generate_mcp_config.py --mode script --codesys-path "C:\\Program Files\\CODESYS 3.5.21.0\\CODESYS\\Common\\CODESYS.exe" --codesys-profile "CODESYS V3.5 SP21"`
- 第2步：复制终端输出的 JSON 内容。
- 第3步：打开 MCP 客户端的配置文件（例如 Claude Desktop 的 `settings.json`），把 JSON 片段粘贴到 `mcpServers` 字段内。
- 第4步：保存配置并重启 MCP 客户端。

提示：Windows 路径中的反斜杠需要转义为双反斜杠（如 `C:\\Program Files\\...`）。

## 已暴露端点（概览）
- 工具：
  - `open_project(filePath, copyOnLock?, openMode?)`
  - `create_project(filePath, templatePath?, templateName?, deviceId?, deviceName?, deviceVersion?)`
  - `save_project(projectFilePath)`、`compile_project(projectFilePath)`
  - `create_pou(...)`、`set_pou_code(...)`、`create_property(...)`、`create_method(...)`
  - `list_templates()`、`list_devices()`、`add_device_to_project(...)`
  - `deploy_application(projectFilePath)`、`download_and_start(projectFilePath)`
  - `diagnose_path(projectPath, objectPath)`
- 资源：
  - `codesys://project/status`
  - `codesys://project/{+project_path}/structure`
  - `codesys://project/{+project_path}/pou/{+pou_path}/code`
  - `codesys://project/{+project_path}/lock_status`
  - `codesys://project/{+project_path}/diagnose_path/{+object_path}`

## 常见问题与建议
- 路径包含空格时：优先使用 Python 模块或脚本入口方式，避免 `npx`，并确保 `CODESYS.exe` 路径正确。
- 工程并发访问：避免与 IDE 同时操作同一工程；只读任务可启用副本策略。
- 编译结果：后续将提供真实错误/警告计数与列表的返回；当前返回结构已预留。

## 迁移说明
- 已移除 Node/TS 相关文件与目录，项目完全使用 Python 实现。
- 端点已在 `server.py` 中注册，交互逻辑由 `codesys_interop.py` 统一处理。
- 后续将逐步完善脚本模板，实现完整对象查找、代码读写与编译流程。

## 许可证
本项目遵循 MIT 许可证，详见 `LICENSE` 文件。

