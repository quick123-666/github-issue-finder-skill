#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Service: 轻量级持久化记忆服务
HTTP API + SQLite 后端，供 github-issue-finder-skill 存储和检索知识

Endpoints:
    GET  /health              - 健康检查
    GET  /stats              - 统计信息
    POST /store              - 存储记忆
    POST /recall             - 按 key 精确检索
    POST /search             - 搜索记忆
    POST /link               - 建立记忆间关联
    POST /neighbors          - 查询关联记忆
    POST /boost              - 提升置信度
    POST /delete             - 删除记忆
    POST /export             - 导出记忆
    POST /maintain           - 置信度衰减维护
    POST /log                - 写入操作日志

Usage:
    python memory_service.py [--port 9099] [--db-path memory.db]
    python memory_service.py [--port 9099] [--db-path memory.db] --daemon
"""

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import parse_qs, urlparse


# ── Database Schema ──────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    key      TEXT    PRIMARY KEY,
    value    TEXT    NOT NULL,
    category TEXT    NOT NULL DEFAULT 'fact',
    confidence REAL  NOT NULL DEFAULT 1.0,
    source   TEXT    NOT NULL DEFAULT '',
    tags     TEXT    NOT NULL DEFAULT '[]',
    created  REAL    NOT NULL,
    updated  REAL    NOT NULL,
    weight   REAL    NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS links (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    source   TEXT    NOT NULL,
    target   TEXT    NOT NULL,
    relation TEXT    NOT NULL DEFAULT 'related',
    weight   REAL    NOT NULL DEFAULT 1.0,
    created  REAL    NOT NULL,
    UNIQUE(source, target, relation)
);

CREATE TABLE IF NOT EXISTS logs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       REAL    NOT NULL,
    module   TEXT,
    action   TEXT,
    detail   TEXT
);

CREATE INDEX IF NOT EXISTS idx_mem_category  ON memories(category);
CREATE INDEX IF NOT EXISTS idx_mem_created  ON memories(created);
CREATE INDEX IF NOT EXISTS idx_links_source ON links(source);
CREATE INDEX IF NOT EXISTS idx_links_target  ON links(target);
CREATE INDEX IF NOT EXISTS idx_logs_ts       ON logs(ts);
"""


# ── DB Helpers ────────────────────────────────────────────────────────────────

def get_db(path):
    db = sqlite3.connect(path, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    return db


def now():
    return time.time()


# ── Query Functions ───────────────────────────────────────────────────────────

def mem_get(db, key):
    row = db.execute("SELECT * FROM memories WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    cols = ["key", "value", "category", "confidence", "source", "tags", "created", "updated", "weight"]
    return dict(zip(cols, row))


def mem_search(db, query, mode="hybrid", limit=10, alpha=0.5):
    if not query:
        return []
    terms = [t for t in re.split(r"\W+", query) if t]
    if not terms:
        return []

    rows = db.execute(
        "SELECT * FROM memories WHERE confidence >= 0.1 ORDER BY confidence DESC, updated DESC LIMIT ?",
        (limit * 3,),
    ).fetchall()
    cols = ["key", "value", "category", "confidence", "source", "tags", "created", "updated", "weight"]

    scored = []
    for row in rows:
        d = dict(zip(cols, row))
        score = 0.0
        q_lower = query.lower()

        # exact key match
        if query.lower() in d["key"].lower():
            score += 1.0
        # all terms match value
        if all(t.lower() in d["value"].lower() for t in terms):
            score += 0.8 * len(terms) / len(terms)
        # some terms match
        matched = sum(1 for t in terms if t.lower() in d["value"].lower())
        score += 0.5 * (matched / len(terms))

        if score > 0:
            scored.append((score, d))

    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:limit]]


def mem_neighbors(db, key, relation=None, max_depth=1):
    if max_depth <= 0:
        return []
    result = []
    visited = {key}
    current = {key}

    for _ in range(max_depth):
        next_batch = set()
        placeholders = "?" + ",?" * (len(current) - 1) if len(current) > 1 else "?"
        rows = db.execute(
            f"""SELECT target FROM links
                WHERE source IN ({placeholders})
                {'AND relation = ?' if relation else ''}""",
            list(current) + ([relation] if relation else []),
        ).fetchall()
        for (t,) in rows:
            if t not in visited:
                mem = mem_get(db, t)
                if mem:
                    result.append(mem)
                    visited.add(t)
                    next_batch.add(t)

        rows2 = db.execute(
            f"""SELECT source FROM links
                WHERE target IN ({placeholders})
                {'AND relation = ?' if relation else ''}""",
            list(current) + ([relation] if relation else []),
        ).fetchall()
        for (s,) in rows2:
            if s not in visited:
                mem = mem_get(s)
                if mem:
                    result.append(mem)
                    visited.add(s)
                    next_batch.add(s)

        current = next_batch
        if not current:
            break

    return result


# ── HTTP Handler ─────────────────────────────────────────────────────────────

class MemoryHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _get_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            count = self.server.db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            return self._send(200, {"status": "ok", "stats": {"total_memories": count}})
        if path == "/stats":
            count = self.server.db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            categories = self.server.db.execute(
                "SELECT category, COUNT(*) FROM memories GROUP BY category"
            ).fetchall()
            return self._send(200, {
                "total": count,
                "by_category": dict(categories),
            })
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._get_json()
        db = self.server.db

        if path == "/store":
            key = body.get("key", "")
            value = body.get("value", "")
            if not key:
                return self._send(400, {"error": "key is required"})
            category = body.get("category", "fact")
            confidence = float(body.get("confidence", 1.0))
            source = body.get("source", "")
            tags = json.dumps(body.get("tags", []), ensure_ascii=False)
            weight = float(body.get("weight", 1.0))
            t = now()
            db.execute(
                """INSERT INTO memories (key, value, category, confidence, source, tags, created, updated, weight)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                     value=excluded.value, category=excluded.category,
                     confidence=excluded.confidence, source=excluded.source,
                     tags=excluded.tags, updated=excluded.updated, weight=excluded.weight""",
                (key, value, category, confidence, source, tags, t, t, weight),
            )
            db.commit()
            return self._send(200, {"status": "ok", "key": key})

        if path == "/recall":
            mem = mem_get(db, body.get("key", ""))
            if not mem:
                return self._send(200, {"error": "not found"})
            return self._send(200, mem)

        if path == "/search":
            results = mem_search(db, body.get("query", ""),
                                body.get("mode", "hybrid"),
                                int(body.get("limit", 10)),
                                float(body.get("alpha", 0.5)))
            return self._send(200, {"results": results, "count": len(results)})

        if path == "/link":
            db.execute(
                "INSERT OR REPLACE INTO links (source, target, relation, weight, created) VALUES (?, ?, ?, ?, ?)",
                (body.get("source"), body.get("target"), body.get("relation", "related"),
                 float(body.get("weight", 1.0)), now()),
            )
            db.commit()
            return self._send(200, {"status": "ok"})

        if path == "/neighbors":
            results = mem_neighbors(db, body.get("key", ""),
                                    body.get("relation"), int(body.get("max_depth", 1)))
            return self._send(200, {"results": results})

        if path == "/boost":
            key = body.get("key", "")
            amount = float(body.get("amount", 0.1))
            t = now()
            db.execute("UPDATE memories SET confidence = MIN(1.0, confidence + ?), updated = ? WHERE key = ?",
                       (amount, t, key))
            db.commit()
            return self._send(200, {"status": "ok"})

        if path == "/delete":
            db.execute("DELETE FROM memories WHERE key = ?", (body.get("key", ""),))
            db.execute("DELETE FROM links WHERE source = ? OR target = ?",
                       (body.get("key", ""), body.get("key", "")))
            db.commit()
            return self._send(200, {"status": "ok"})

        if path == "/export":
            category = body.get("category")
            if category:
                rows = db.execute("SELECT * FROM memories WHERE category = ?", (category,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM memories").fetchall()
            cols = ["key", "value", "category", "confidence", "source", "tags", "created", "updated", "weight"]
            return self._send(200, {"memories": [dict(zip(cols, r)) for r in rows]})

        if path == "/maintain":
            half_life = float(body.get("half_life_days", 30.0)) * 86400
            min_conf = float(body.get("min_confidence", 0.1))
            t = now()
            db.execute(
                "UPDATE memories SET confidence = MAX(?, confidence * 0.5 ** ((? - updated) / ?))",
                (min_conf, t, half_life),
            )
            db.commit()
            return self._send(200, {"status": "ok"})

        if path == "/log":
            db.execute("INSERT INTO logs (ts, module, action, detail) VALUES (?, ?, ?, ?)",
                       (now(), body.get("module", ""), body.get("action", ""), body.get("detail", "")))
            db.commit()
            return self._send(200, {"status": "ok"})

        self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        pass  # suppress request logs


# ── Server ───────────────────────────────────────────────────────────────────

class ThreadedHTTPServer(HTTPServer):
    def __init__(self, addr, handler, db):
        super().__init__(addr, handler)
        self.db = db
        self.allow_reuse_address = True


def serve(port, db_path):
    db = get_db(db_path)
    server = ThreadedHTTPServer(("127.0.0.1", port), MemoryHandler, db)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[memory_service] Listening on 127.0.0.1:{port}", file=sys.stderr)
    print(f"[memory_service] DB: {os.path.abspath(db_path)}", file=sys.stderr)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
        print("[memory_service] Shutdown.", file=sys.stderr)


# ── CLI Entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Memory Service")
    parser.add_argument("--port", default=9099, type=int)
    parser.add_argument("--db-path", default="memory.db")
    args = parser.parse_args()
    serve(args.port, args.db_path)
