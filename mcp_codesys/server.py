import asyncio
import os
from . import __version__
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except Exception:
    # 允许在未安装 mcp SDK 的环境下给出友好提示
    Server = None
from .codesys_interop import run_snippet
import json

"""
MCP 服务器端点注册

职责：
- 创建并启动 MCP 服务器；
- 注册“工具”（可执行动作）与“资源”（只读查询）端点；
- 每个端点内部都委托给 `run_snippet(...)`，由互操作层生成并执行 CODESYS 脚本。
"""

def run_mcp_server(codesys_path: str, codesys_profile: str, workspace: str, timeout: int = 120):
    # SDK 缺失时提示并退出
    if Server is None:
        print("mcp Python SDK not found")
        return 1
    # 创建服务器实例，标识名用于客户端显示
    server = Server("codesys-mcp-python")

    # 内部：将相对路径解析为基于 workspace 的绝对路径
    def _resolve(path: str) -> str:
        if not path:
            return path
        return path if os.path.isabs(path) else os.path.abspath(os.path.join(workspace or os.getcwd(), path))

    # 工具：打开工程（支持锁冲突时的副本策略与打开模式）
    async def open_project(filePath: str, copyOnLock: bool = False, openMode: str = "") -> str:
        return await run_snippet(codesys_path, codesys_profile, "open_project", {"project_file_path": _resolve(filePath), "copy_on_lock": copyOnLock, "open_mode": openMode}, timeout=timeout)

    # 工具：创建工程（支持模板与设备选择）
    async def create_project(filePath: str, templatePath: str = "", templateName: str = "", deviceId: str = "", deviceName: str = "", deviceVersion: str = "") -> str:
        return await run_snippet(codesys_path, codesys_profile, "create_project", {
            "project_file_path": _resolve(filePath),
            "template_path": _resolve(templatePath) if templatePath else "",
            "template_name": templateName,
            "device_id": deviceId,
            "device_name": deviceName,
            "device_version": deviceVersion,
        }, timeout=timeout)

    # 工具：保存工程
    async def save_project(projectFilePath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "save_project", {"project_file_path": _resolve(projectFilePath)}, timeout=timeout)

    # 工具：创建 POU（Program/FunctionBlock/Function）
    async def create_pou(projectFilePath: str, name: str, type: str, language: str, parentPath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "create_pou", {
            "project_file_path": _resolve(projectFilePath),
            "name": name,
            "type": type,
            "language": language,
            "parent_path": parentPath,
        }, timeout=timeout)

    # 工具：写入 POU 声明/实现代码
    async def set_pou_code(projectFilePath: str, pouPath: str, declarationCode: str = "", implementationCode: str = "") -> str:
        return await run_snippet(codesys_path, codesys_profile, "set_pou_code", {
            "project_file_path": _resolve(projectFilePath),
            "pou_path": pouPath,
            "declaration_code": declarationCode,
            "implementation_code": implementationCode,
        }, timeout=timeout)

    # 工具：在 FB 下创建属性
    async def create_property(projectFilePath: str, parentPouPath: str, propertyName: str, propertyType: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "create_property", {
            "project_file_path": _resolve(projectFilePath),
            "parent_pou_path": parentPouPath,
            "property_name": propertyName,
            "property_type": propertyType,
        }, timeout=timeout)

    # 工具：在 FB 下创建方法
    async def create_method(projectFilePath: str, parentPouPath: str, methodName: str, returnType: str = "") -> str:
        return await run_snippet(codesys_path, codesys_profile, "create_method", {
            "project_file_path": _resolve(projectFilePath),
            "parent_pou_path": parentPouPath,
            "method_name": methodName,
            "return_type": returnType,
        }, timeout=timeout)

    # 工具：编译工程（后续将轮询消息管理器并返回错误/警告列表）
    async def compile_project(projectFilePath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "compile_project", {"project_file_path": _resolve(projectFilePath)}, timeout=timeout)

    # 资源：脚本引擎与工程打开状态
    async def project_status() -> str:
        return await run_snippet(codesys_path, codesys_profile, "project_status", {}, timeout=timeout)

    # 资源：工程结构树（递归 children）
    async def project_structure(projectPath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "project_structure", {"project_path": projectPath}, timeout=timeout)

    # 资源：读取 POU/方法/属性的声明与实现
    async def pou_code(projectPath: str, pouPath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "pou_code", {"project_path": projectPath, "pou_path": pouPath}, timeout=timeout)

    # 资源：工程锁状态（用于并发访问诊断）
    async def lock_status(projectPath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "lock_status", {"project_path": projectPath}, timeout=timeout)

    # 工具：枚举可用工程模板
    async def list_templates() -> str:
        return await run_snippet(codesys_path, codesys_profile, "list_templates", {}, timeout=timeout)

    # 工具：枚举可用设备
    async def list_devices() -> str:
        return await run_snippet(codesys_path, codesys_profile, "list_devices", {}, timeout=timeout)

    # 工具：向工程添加设备（后续绑定 active_application）
    async def add_device_to_project(projectFilePath: str, deviceId: str = "", deviceName: str = "", deviceVersion: str = "") -> str:
        return await run_snippet(codesys_path, codesys_profile, "add_device_to_project", {
            "project_file_path": _resolve(projectFilePath),
            "device_id": deviceId,
            "device_name": deviceName,
            "device_version": deviceVersion,
        }, timeout=timeout)

    # 工具：部署应用（创建在线应用、登录等）
    async def deploy_application(projectFilePath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "deploy_application", {"project_file_path": _resolve(projectFilePath)}, timeout=timeout)

    # 工具：下载并启动应用
    async def download_and_start(projectFilePath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "download_and_start", {"project_file_path": _resolve(projectFilePath)}, timeout=timeout)

    # 工具/资源：路径诊断（规范化与候选列表）
    async def diagnose_path(projectPath: str, objectPath: str) -> str:
        return await run_snippet(codesys_path, codesys_profile, "diagnose_path", {"project_path": projectPath, "object_path": objectPath}, timeout=timeout)

    # 资源：健康检查与版本
    async def health() -> str:
        ok = bool(codesys_path and os.path.exists(codesys_path))
        return json.dumps({"ready": ok, "codesys_path": codesys_path, "profile": codesys_profile, "version": __version__})

    async def version() -> str:
        return json.dumps({"version": __version__})

    server.tool("open_project")(open_project)
    server.tool("create_project")(create_project)
    server.tool("save_project")(save_project)
    server.tool("create_pou")(create_pou)
    server.tool("set_pou_code")(set_pou_code)
    server.tool("create_property")(create_property)
    server.tool("create_method")(create_method)
    server.tool("compile_project")(compile_project)
    server.tool("list_templates")(list_templates)
    server.tool("list_devices")(list_devices)
    server.tool("add_device_to_project")(add_device_to_project)
    server.tool("deploy_application")(deploy_application)
    server.tool("download_and_start")(download_and_start)
    server.tool("diagnose_path")(diagnose_path)

    server.resource("codesys://project/status")(project_status)
    server.resource("codesys://project/{+project_path}/structure")(project_structure)
    server.resource("codesys://project/{+project_path}/pou/{+pou_path}/code")(pou_code)
    server.resource("codesys://project/{+project_path}/lock_status")(lock_status)
    server.resource("codesys://project/{+project_path}/diagnose_path/{+object_path}")(diagnose_path)
    server.resource("codesys://health")(health)
    server.resource("codesys://version")(version)

    # 以 stdio 模式启动服务器，等待 MCP 客户端连接
    asyncio.run(stdio_server.run(server))
    return 0
