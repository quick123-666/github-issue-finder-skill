#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemoryClient: 记忆服务 HTTP 客户�?�?skill 脚本调用 memory_service �?REST API
"""

import json
import urllib.request
import urllib.parse
import urllib.error


class MemoryClient:
    def __init__(self, host="127.0.0.1", port=9099, timeout=5):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout

    def _post(self, path, body=None):
        url = self.base_url + path
        data = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            return {"error": f"memory_service_unavailable: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def _get(self, path):
        url = self.base_url + path
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            return {"error": f"memory_service_unavailable: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def store(self, key, value, category="fact", confidence=1.0, source="", tags=None):
        return self._post("/store", {
            "key": key, "value": value, "category": category,
            "confidence": confidence, "source": source, "tags": tags,
        })

    def recall(self, key):
        return self._post("/recall", {"key": key})

    def search(self, query, mode="hybrid", limit=10, alpha=0.5):
        return self._post("/search", {
            "query": query, "mode": mode,
            "limit": limit, "alpha": alpha,
        })

    def link(self, source, target, relation="related", weight=1.0):
        return self._post("/link", {
            "source": source, "target": target,
            "relation": relation, "weight": weight,
        })

    def neighbors(self, key, relation=None, max_depth=1):
        return self._post("/neighbors", {
            "key": key, "relation": relation, "max_depth": max_depth,
        })

    def boost(self, key, amount=0.1):
        return self._post("/boost", {"key": key, "amount": amount})

    def delete(self, key):
        return self._post("/delete", {"key": key})

    def export(self, category=None):
        return self._post("/export", {"category": category})

    def maintain(self, half_life_days=30.0, min_confidence=0.1):
        return self._post("/maintain", {
            "half_life_days": half_life_days,
            "min_confidence": min_confidence,
        })

    def health(self):
        return self._get("/health")

    def stats(self):
        return self._get("/stats")

    def log(self, module="", action="", detail=""):
        return self._post("/log", {
            "module": module, "action": action, "detail": detail,
        })

    def available(self) -> bool:
        try:
            resp = self.health()
            return resp.get("status") == "ok"
        except Exception:
            return False


def demo():
    mc = MemoryClient()
    if not mc.available():
        print("[MemoryClient] memory_service 未运�?(127.0.0.1:9099)")
        print("请先运行: python src/memory_service.py")
        return
    print("[MemoryClient] 连接成功")
    info = mc.health()
    print(f"  stats: {info.get('stats', {})}")


if __name__ == "__main__":
    demo()
