#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkReport: 工作报告生成�?自动汇总工作记录，保存到记忆服务，维护总索�?可在任何 skill 流程末尾调用

用法:
    from work_report import WorkReport
    report = WorkReport(mem_client, session_tag="my_session")
    report.add_issue("streamlit/streamlit", 9098, "Bug title", "https://github.com/...", action="found")
    report.add_pr("your-username/streamlit", 1, "Fix SVG", "https://github.com/.../pull/1", status="submitted")
    report.save()
"""

import json
import os
import time
from datetime import datetime
from typing import List, Optional


class WorkReport:
    INDEX_KEY = "index:work-reports"
    LOCAL_DIR = os.path.join(
        os.path.dirname(__file__), "..", "references", "work_reports"
    )

    def __init__(self, mem_client, session_tag: Optional[str] = None):
        self.mem = mem_client
        self.session_tag = session_tag or f"sess_{int(time.time())}"
        self.items: List[dict] = []
        self.start_time = datetime.now()

    def add_issue(self, repo: str, number: int, title: str, url: str,
                  action: str = "found"):
        self.items.append({
            "type": "issue",
            "action": action,
            "repo": repo,
            "number": number,
            "title": title,
            "url": url,
        })

    def add_pr(self, repo: str, number: int, title: str, url: str,
               status: str = "submitted"):
        self.items.append({
            "type": "pr",
            "action": status,
            "repo": repo,
            "number": number,
            "title": title,
            "url": url,
        })

    def add_note(self, content: str):
        self.items.append({
            "type": "note",
            "content": content,
        })

    def save(self) -> tuple:
        report = {
            "date": self.start_time.strftime("%Y-%m-%d"),
            "time": self.start_time.isoformat(),
            "session": self.session_tag,
            "summary": self._build_summary(),
            "items": self.items,
            "stats": self._build_stats(),
        }

        ts = self.start_time.strftime("%Y%m%d%H%M%S")
        tag = self.session_tag.replace(":", "_")[:16]
        report_key = f"report:{ts}:{tag}"

        result = self.mem.store(
            key=report_key,
            value=json.dumps(report, ensure_ascii=False),
            category="skill",
            confidence=0.9,
            source="work-report",
            tags=["work-report", self.start_time.strftime("%Y-%m"), self.session_tag],
        )
        if result.get("status") != "ok":
            print(f"[WorkReport] WARNING: store failed: {result}")
            return report_key, report

        self._update_index(report_key)

        self.mem.log("work-report", "save",
                     f"{report_key}: {report['summary']}")

        print(f"[WorkReport] Saved: {report_key}")
        print(f"[WorkReport] Summary: {report['summary']}")
        return report_key, report

    def save_local(self, repo_slug: str) -> str:
        reports_dir = os.path.abspath(self.LOCAL_DIR)
        os.makedirs(reports_dir, exist_ok=True)

        date_str = self.start_time.strftime("%Y-%m-%d")
        filename = f"{date_str}_{repo_slug}.md"
        filepath = os.path.join(reports_dir, filename)

        title = next(
            (i["title"] for i in self.items if i.get("type") in ("issue", "pr")),
            "Work Report"
        )

        lines = [
            f"# {title}",
            "",
            f"- **Date:** {date_str}",
            f"- **Repo:** {repo_slug}",
        ]

        for item in self.items:
            if item["type"] in ("issue", "pr"):
                lines.append(f"- **{'Issue' if item['type']=='issue' else 'PR'}:** [#{item['number']}]({item['url']})")
        lines.append("")

        for item in self.items:
            if item["type"] == "note":
                lines.append(f"> {item['content']}")
                lines.append("")

        lines.append("---")
        lines.append(f"*Summary: {self._build_summary()}*")
        lines.append("")

        content = "\n".join(lines) + "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[WorkReport] Local file saved: {filepath}")
        return filepath

    def _build_summary(self) -> str:
        repos = set()
        found = analyzed = prs = 0
        for it in self.items:
            if it.get("repo"):
                repos.add(it["repo"])
            if it.get("action") == "found":
                found += 1
            if it.get("action") == "analyzed":
                analyzed += 1
            if it.get("type") == "pr":
                prs += 1

        parts = []
        if repos:
            parts.append(f"worked on {len(repos)} repos")
        if found:
            parts.append(f"found {found} issues")
        if analyzed:
            parts.append(f"analyzed {analyzed} issues")
        if prs:
            parts.append(f"submitted {prs} PRs")

        summary = "; ".join(parts) if parts else "no activity recorded"
        return summary

    def _build_stats(self) -> dict:
        return {
            "total_items": len(self.items),
            "issues_found": sum(1 for i in self.items if i.get("action") == "found"),
            "issues_analyzed": sum(1 for i in self.items if i.get("action") == "analyzed"),
            "prs_submitted": sum(1 for i in self.items if i.get("type") == "pr"),
            "repos": list(set(i.get("repo", "") for i in self.items if i.get("repo"))),
        }

    def _update_index(self, new_key: str):
        idx = self.mem.recall(self.INDEX_KEY)
        if idx and "error" not in idx:
            try:
                keys = json.loads(idx.get("value", "[]"))
            except Exception:
                keys = []
        else:
            keys = []

        if new_key not in keys:
            keys.append(new_key)

        self.mem.store(
            key=self.INDEX_KEY,
            value=json.dumps(keys, ensure_ascii=False),
            category="skill",
            confidence=1.0,
            source="work-report",
            tags=["index", "work-reports", "master-index"],
        )
        print(f"[WorkReport] Index now tracks {len(keys)} reports")


if __name__ == "__main__":
    from memory_client import MemoryClient

    mc = MemoryClient()
    if not mc.available():
        print("memory_service not running -- start with: python scripts/memory_service.py")
        exit(1)

    print("=== WorkReport Demo ===\n")
    report = WorkReport(mc, session_tag="demo_run")
    report.add_issue("streamlit/streamlit", 9098, "SVG blank in st.image()",
                     "https://github.com/streamlit/streamlit/issues/9098",
                     action="found")
    report.add_issue("pylint-dev/pylint", 9143, "Add JUnit reporter",
                     "https://github.com/pylint-dev/pylint/issues/9143",
                     action="analyzed")
    report.add_pr("your-username/streamlit", 1, "Fix SVG viewBox parsing",
                  "https://github.com/your-username/streamlit/pull/1",
                  status="submitted")
    report.add_note("Learned about SVG viewBox attribute parsing")
    key, data = report.save()

    print(f"\nReport key: {key}")
    print(f"Report summary: {data['summary']}")
    print(f"Report stats: {data['stats']}")

    idx = mc.recall(WorkReport.INDEX_KEY)
    print(f"\nMaster index: {len(json.loads(idx.get('value', '[]')))} reports tracked")
    print("=== Demo Complete ===")
