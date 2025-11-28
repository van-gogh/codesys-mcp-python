import os
import json
import tempfile
import subprocess

"""
CODESYS 互操作层

职责：
- 将“动作参数”拼接为可在 CODESYS 内置脚本引擎执行的 Python 脚本；
- 以无界面方式调用 CODESYS 可执行文件（`--noUI --runscript`）；
- 解析标准输出/错误，返回统一 JSON 结构，供 MCP 端点直接使用。
"""

def write_temp_script(content: str) -> str:
    """写入临时脚本文件并返回路径"""
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def _script_prelude() -> str:
    """脚本前导：统一成功/失败输出协议（`SCRIPT_SUCCESS`/`SCRIPT_ERROR`）"""
    return (
        "import sys\n"
        "import json\n"
        "def _ok(payload):\n"
        "    print('SCRIPT_SUCCESS')\n"
        "    print(json.dumps(payload, ensure_ascii=False))\n"
        "    sys.exit(0)\n"
        "def _err(message):\n"
        "    print('SCRIPT_ERROR')\n"
        "    print(str(message))\n"
        "    sys.exit(1)\n"
    )

def build_snippet(name: str, params: dict) -> str:
    """根据动作名称与参数构造可在 CODESYS 中执行的脚本文本

    说明：当前为占位实现，返回结构化结果以便联调。后续将把各动作替换为真实
    CODESYS 脚本逻辑（对象查找、POU 操作、编译轮询、设备绑定等）。
    """
    actions = {
        "open_project": (
            "def _action(p):\n"
            "    _ok({'action':'open_project','params':p})\n"
        ),
        "create_project": (
            "def _action(p):\n"
            "    _ok({'action':'create_project','params':p})\n"
        ),
        "save_project": (
            "def _action(p):\n"
            "    _ok({'action':'save_project','params':p})\n"
        ),
        "create_pou": (
            "def _action(p):\n"
            "    _ok({'action':'create_pou','params':p})\n"
        ),
        "set_pou_code": (
            "def _action(p):\n"
            "    _ok({'action':'set_pou_code','params':p})\n"
        ),
        "create_property": (
            "def _action(p):\n"
            "    _ok({'action':'create_property','params':p})\n"
        ),
        "create_method": (
            "def _action(p):\n"
            "    _ok({'action':'create_method','params':p})\n"
        ),
        "compile_project": (
            "def _action(p):\n"
            "    _ok({'action':'compile_project','params':p,'compile':{'errors':0,'warnings':0}})\n"
        ),
        "project_status": (
            "def _action(p):\n"
            "    _ok({'scripting':True,'project_open':True,'project_name':'Unknown','project_path':p.get('project_path','')})\n"
        ),
        "project_structure": (
            "def _action(p):\n"
            "    _ok({'root':['Application']})\n"
        ),
        "pou_code": (
            "def _action(p):\n"
            "    _ok({'declaration':'','implementation':''})\n"
        ),
        "lock_status": (
            "def _action(p):\n"
            "    _ok({'locked':False,'holder':'','hint':'close IDE or use copyOnLock'})\n"
        ),
        "list_templates": (
            "def _action(p):\n"
            "    _ok({'templates':[]})\n"
        ),
        "list_devices": (
            "def _action(p):\n"
            "    _ok({'devices':[]})\n"
        ),
        "add_device_to_project": (
            "def _action(p):\n"
            "    _ok({'added':True,'device':p})\n"
        ),
        "deploy_application": (
            "def _action(p):\n"
            "    _ok({'deployed':True})\n"
        ),
        "download_and_start": (
            "def _action(p):\n"
            "    _ok({'downloaded':True,'started':True})\n"
        ),
        "diagnose_path": (
            "def _action(p):\n"
            "    _ok({'normalized':'Application/POUs/...','candidates':[]})\n"
        ),
    }
    # 未知动作给出错误
    body = actions.get(name)
    if body is None:
        body = "def _action(p):\n    _err('unknown action')\n"
    payload = json.dumps(params, ensure_ascii=False)
    return _script_prelude() + body + "\n_action(" + payload.replace("\\", "\\\\") + ")\n"

def run_codesys(codesys_path: str, profile: str, script_path: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    """以无界面方式调用 CODESYS 执行脚本

    - 使用列表参数并 `shell=False`，避免路径空格导致的解析问题；
    - 设置 `cwd` 与预置 `PATH`，确保 CODESYS 附带的组件可用。
    """
    if not codesys_path or not os.path.exists(codesys_path):
        return subprocess.CompletedProcess(args=[], returncode=127, stdout="", stderr="CODESYS.exe not found")
    args = [codesys_path, f"--profile={profile}", "--noUI", f"--runscript={script_path}"]
    env = os.environ.copy()
    exe_dir = os.path.dirname(codesys_path)
    env["PATH"] = exe_dir + os.pathsep + env.get("PATH", "")
    return subprocess.run(args, shell=False, cwd=exe_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)

async def run_snippet(codesys_path: str, profile: str, name: str, params: dict, timeout: int | None = None) -> str:
    """执行指定动作并返回统一 JSON 字符串

    返回结构：
    - 成功：`{"success": true, "data": <payload>, "exit_code": 0}`；
    - 失败：`{"success": false, "error": <string>, "exit_code": <code>, "stdout": ..., "stderr": ...}`。
    """
    content = build_snippet(name, params)
    path = write_temp_script(content)
    try:
        try:
            cp = run_codesys(codesys_path, profile, path, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            return json.dumps({"success": False, "error": f"timeout after {e.timeout}s", "exit_code": None})
        out = cp.stdout or ""
        err = cp.stderr or ""
        if "SCRIPT_SUCCESS" in out:
            lines = out.splitlines()
            payload = "{}"
            for i, s in enumerate(lines):
                if s == "SCRIPT_SUCCESS" and i + 1 < len(lines):
                    payload = lines[i + 1]
                    break
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw": payload}
            return json.dumps({"success": True, "data": data, "exit_code": cp.returncode})
        return json.dumps({"success": False, "error": err or out, "exit_code": cp.returncode, "stdout": out, "stderr": err})
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

def dry_run_command(codesys_path: str, profile: str) -> str:
    """返回将执行的 CODESYS 命令串，用于环境与参数检查"""
    return " ".join([codesys_path, f'--profile="{profile}"', '--noUI', '--runscript="TEMP.py"'])
