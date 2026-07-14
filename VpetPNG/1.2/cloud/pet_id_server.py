#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌宠编号发号服务（stdlib + sqlite）。

策略：
- 按设备指纹直接分配：首次联网发新号，同机找回
- A 把存档拷给 B：B 本地沿用 A 的编号，服务端不会因拷贝再给 B 新号（B 新机无存档才会领自己的号）

启动：
  python cloud/pet_id_server.py --host 0.0.0.0 --port 8787

接口：
  GET  /health
  POST /v1/register  {"machine_id"} → 自动发号或找回
  POST /v1/activate  兼容旧客户端（无有效码时等同 register）
"""

from __future__ import annotations

import argparse
import json
import secrets
import sqlite3
import string
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "pet_id_store.sqlite3"
_LOCK = threading.Lock()


class NeedActivation(Exception):
    """保留兼容；当前策略下不再用于拒发。"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            machine_id TEXT PRIMARY KEY,
            pet_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            client TEXT,
            app_version TEXT,
            activation_code TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activation_codes (
            code TEXT PRIMARY KEY,
            pet_id INTEGER,
            used_by_machine TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            used_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('next_id', '0')")
    conn.commit()
    return conn


def _next_pet_id(conn: sqlite3.Connection) -> int:
    next_row = conn.execute("SELECT value FROM meta WHERE key = 'next_id'").fetchone()
    pet_id = int(next_row[0] if next_row else 0)
    conn.execute("UPDATE meta SET value = ? WHERE key = 'next_id'", (str(pet_id + 1),))
    return pet_id


def _norm_code(code: str) -> str:
    return "".join(ch for ch in (code or "").upper() if ch.isalnum())


def issue_codes(count: int) -> list[str]:
    """可选：仍可签发激活码（旧流程兼容）。"""
    count = max(1, min(500, int(count)))
    alphabet = string.ascii_uppercase + string.digits
    out: list[str] = []
    with _LOCK:
        conn = _connect()
        try:
            while len(out) < count:
                raw = "".join(secrets.choice(alphabet) for _ in range(12))
                code = f"{raw[:4]}-{raw[4:8]}-{raw[8:12]}"
                try:
                    conn.execute("INSERT INTO activation_codes(code) VALUES (?)", (_norm_code(code),))
                except sqlite3.IntegrityError:
                    continue
                out.append(code)
            conn.commit()
        finally:
            conn.close()
    return out


def register(machine_id: str, *, client: str = "", app_version: str = "") -> dict:
    """按设备指纹发号：已登记则找回，否则分配新桌宠编号。"""
    mid = (machine_id or "").strip().lower()
    if len(mid) < 16:
        raise ValueError("machine_id too short")
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT pet_id FROM devices WHERE machine_id = ?", (mid,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE devices SET last_seen_at = datetime('now'), client = ?, app_version = ? WHERE machine_id = ?",
                    (client or None, app_version or None, mid),
                )
                conn.commit()
                return {"pet_id": int(row[0]), "reclaimed": True, "source": "device"}
            pet_id = _next_pet_id(conn)
            conn.execute(
                """
                INSERT INTO devices(machine_id, pet_id, client, app_version)
                VALUES (?, ?, ?, ?)
                """,
                (mid, pet_id, client or None, app_version or None),
            )
            conn.commit()
            return {"pet_id": pet_id, "reclaimed": False, "source": "auto"}
        finally:
            conn.close()


def activate(
    machine_id: str,
    activation_code: str,
    *,
    client: str = "",
    app_version: str = "",
) -> dict:
    """兼容旧接口：无有效码时等同直接分配。"""
    mid = (machine_id or "").strip().lower()
    code = _norm_code(activation_code)
    if len(mid) < 16:
        raise ValueError("machine_id too short")
    if len(code) < 8:
        return register(mid, client=client, app_version=app_version)
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT pet_id FROM devices WHERE machine_id = ?", (mid,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE devices SET last_seen_at = datetime('now'), client = ?, app_version = ? WHERE machine_id = ?",
                    (client or None, app_version or None, mid),
                )
                conn.commit()
                return {"pet_id": int(row[0]), "reclaimed": True, "source": "device"}

            crow = conn.execute(
                "SELECT pet_id, used_by_machine FROM activation_codes WHERE code = ?",
                (code,),
            ).fetchone()
            if not crow:
                # 码无效：不阻塞，直接发号
                return register(mid, client=client, app_version=app_version)

            existing_pid, used_by = crow
            if used_by and used_by != mid:
                return register(mid, client=client, app_version=app_version)

            if existing_pid is not None:
                pet_id = int(existing_pid)
                reclaimed = True
            else:
                pet_id = _next_pet_id(conn)
                reclaimed = False

            conn.execute(
                """
                UPDATE activation_codes
                SET pet_id = ?, used_by_machine = ?, used_at = datetime('now')
                WHERE code = ?
                """,
                (pet_id, mid, code),
            )
            conn.execute(
                """
                INSERT INTO devices(machine_id, pet_id, client, app_version, activation_code)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mid, pet_id, client or None, app_version or None, code),
            )
            conn.commit()
            return {"pet_id": pet_id, "reclaimed": reclaimed, "source": "activation"}
        finally:
            conn.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "VpetPetId/1.2"

    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _send_json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/health", "/"):
            self._send_json(200, {"ok": True, "service": "vpet-pet-id", "policy": "auto_assign"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(max(0, min(length, 64_000)))
        try:
            data = json.loads(raw.decode("utf-8") if raw else "{}")
        except Exception:
            self._send_json(400, {"error": "invalid_json"})
            return
        if not isinstance(data, dict):
            self._send_json(400, {"error": "invalid_body"})
            return
        try:
            if path == "/v1/register":
                result = register(
                    str(data.get("machine_id") or ""),
                    client=str(data.get("client") or ""),
                    app_version=str(data.get("app_version") or ""),
                )
            elif path == "/v1/activate":
                result = activate(
                    str(data.get("machine_id") or ""),
                    str(data.get("activation_code") or ""),
                    client=str(data.get("client") or ""),
                    app_version=str(data.get("app_version") or ""),
                )
            else:
                self._send_json(404, {"error": "not_found"})
                return
        except NeedActivation:
            # 策略已改为直接分配，理论不会走到这里
            mid = str(data.get("machine_id") or "")
            result = register(mid)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Vpet pet-id auto allocator")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--issue", type=int, default=0, help="签发 N 个兼容激活码后退出")
    args = parser.parse_args()
    if args.issue > 0:
        codes = issue_codes(args.issue)
        print(f"issued {len(codes)} activation codes → {DB_PATH}")
        for c in codes:
            print(c)
        return
    _connect().close()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Vpet pet-id server on http://{args.host}:{args.port}")
    print(f"DB: {DB_PATH}")
    print("POST /v1/register（自动发号）  GET /health")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
