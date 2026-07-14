# -*- coding: utf-8 -*-
"""桌宠编号客户端：按设备指纹自动领取/找回；玩家不可手填编号。"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any
from urllib import error, request

# 部署发号服务后在此填默认地址，或用环境变量 VPET_PET_ID_API 覆盖（设置里不可填）
DEFAULT_PET_ID_API_URL = ""
REQUEST_TIMEOUT_SEC = 8.0


class NeedActivationError(RuntimeError):
    """兼容旧异常名；当前策略下客户端不再依赖激活码。"""


def _normalize_api_base(url: str) -> str:
    return (url or "").strip().rstrip("/")


def resolve_pet_id_api_url(app_config: dict | None = None) -> str:
    """仅环境变量 / 内置默认；忽略玩家在配置里手填的地址。"""
    del app_config  # 不可自填
    env = (os.environ.get("VPET_PET_ID_API") or "").strip()
    if env:
        return _normalize_api_base(env)
    return _normalize_api_base(DEFAULT_PET_ID_API_URL)


def device_id_path(data_dir: Path) -> Path:
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local:
        sticky = Path(local) / "VpetAOBA" / "device_id.txt"
        sticky.parent.mkdir(parents=True, exist_ok=True)
        return sticky
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "device_id.txt"


def _windows_machine_guid() -> str | None:
    if os.name != "nt":
        return None
    try:
        out = subprocess.check_output(
            ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        return None
    for line in out.splitlines():
        if "MachineGuid" in line:
            parts = line.strip().split()
            if parts:
                return parts[-1].strip()
    return None


def get_or_create_machine_id(data_dir: Path) -> str:
    """稳定设备指纹：优先 Windows MachineGuid，否则本地持久 UUID。"""
    path = device_id_path(data_dir)
    cached = ""
    if path.exists():
        try:
            cached = path.read_text(encoding="utf-8").strip()
        except Exception:
            cached = ""
    guid = _windows_machine_guid()
    raw = guid or cached or str(uuid.uuid4())
    digest = hashlib.sha256(f"vpet|{raw}".encode("utf-8")).hexdigest()
    if cached != digest:
        try:
            path.write_text(digest, encoding="utf-8")
        except Exception:
            pass
    return digest


def _post_json(api_base: str, path: str, payload: dict) -> dict[str, Any]:
    base = _normalize_api_base(api_base)
    if not base:
        raise RuntimeError("未配置桌宠编号服务地址")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{base}{path}",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Vpet/1.2"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"发号服务 HTTP {exc.code}: {(detail or exc.reason)[:200]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"无法连接发号服务：{exc.reason}") from exc
    if not isinstance(data, dict) or "pet_id" not in data:
        raise RuntimeError("发号服务返回异常")
    pid = int(data["pet_id"])
    if pid < 0:
        raise RuntimeError("发号服务返回非法编号")
    return {
        "pet_id": pid,
        "reclaimed": bool(data.get("reclaimed")),
        "source": str(data.get("source") or ""),
        "raw": data,
    }


def register_pet_id(
    api_base: str,
    *,
    machine_id: str,
    client: str = "vpet",
    app_version: str = "1.2",
) -> dict[str, Any]:
    """自动领取或找回桌宠编号。"""
    if not machine_id:
        raise RuntimeError("缺少设备指纹")
    return _post_json(
        api_base,
        "/v1/register",
        {"machine_id": machine_id, "client": client, "app_version": app_version},
    )


# 兼容旧 import 名
def activate_pet_id(
    api_base: str,
    *,
    machine_id: str,
    activation_code: str = "",
    client: str = "vpet",
    app_version: str = "1.2",
) -> dict[str, Any]:
    del activation_code
    return register_pet_id(api_base, machine_id=machine_id, client=client, app_version=app_version)


def load_activation_code(data_dir: Path, app_config: dict | None = None) -> str:
    """已废弃：不再使用激活码。"""
    del data_dir, app_config
    return ""
