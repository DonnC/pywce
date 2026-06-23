import asyncio
import json
import os
import subprocess
import sys
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional


def _default_mcp_workspace() -> Path:
    return Path(__file__).resolve().parents[3] / "wce-mcp"


def _default_mcp_python() -> str:
    workspace = _default_mcp_workspace()
    venv_python = workspace / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return "python"


def _default_mcp_url() -> str:
    return "http://127.0.0.1:9000/mcp"


def _ensure_mcp_src_on_path() -> None:
    workspace = _resolve_workspace()
    src_dir = workspace / "src"
    if src_dir.exists():
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


@lru_cache(maxsize=1)
def _inproc_server():
    _ensure_mcp_src_on_path()
    from wce_mcp.server import build_server

    return build_server(_resolve_workspace())


def _resolve_workspace() -> Path:
    return Path(os.getenv("WCE_MCP_WORKSPACE", str(_default_mcp_workspace()))).resolve()


def call_wce_mcp_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    mode = os.getenv("WCE_MCP_MODE", "remote").lower()
    args = arguments or {}

    if mode in {"remote", "http", "sse", "streamable-http"}:
        return _call_remote(name, args)
    if mode == "subprocess":
        return _call_subprocess(name, args)

    server = _inproc_server()
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": "local-call",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": args,
            },
        }
    )
    return response["result"]["content"][0]["json"]


def _call_remote(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    return _run_async(_call_remote_async(name, arguments))


async def _call_remote_async(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    from fastmcp import Client

    url = os.getenv("WCE_MCP_URL", _default_mcp_url())
    async with Client(url) as client:
        result = await client.call_tool(name, arguments)
    if hasattr(result, "data"):
        return result.data
    return result


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    if not loop.is_running():
        return loop.run_until_complete(coro)

    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def runner() -> None:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result["value"] = new_loop.run_until_complete(coro)
        except BaseException as exc:  # pragma: no cover - defensive bridge
            error["value"] = exc
        finally:
            new_loop.close()

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]

    return result.get("value")


def _call_subprocess(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = _resolve_workspace()
    python_bin = os.getenv("WCE_MCP_PYTHON", _default_mcp_python())
    command = [
        python_bin,
        "-m",
        "wce_mcp",
        "--transport",
        "legacy-stdio",
        "--workspace",
        str(workspace),
    ]

    request = {
        "jsonrpc": "2.0",
        "id": "subprocess-call",
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments,
        },
    }

    proc = subprocess.run(
        command,
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=True,
        cwd=str(workspace),
    )
    output = proc.stdout.strip().splitlines()[-1]
    response = json.loads(output)
    return response["result"]["content"][0]["json"]
