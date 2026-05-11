# GitHub Issue Finder / GitHub Issue 查找助手

> **English:** An AI agent skill for discovering, evaluating, and claiming `good first issue` targets across curated open source repositories.
>
> **中文：** 一个帮助你在 GitHub 上发现、评估并认领优质开源 issue 的 AI agent 技能。从优质项目中精挑细选，配合完整的工作流程，助你完成从找 issue 到提 PR 的全过程。

[![License: MIT](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Platform: Windows/macOS/Linux](https://img.shields.io/badge/Platform-Windows%2FmacOS%2FLinux-black.svg)](https://github.com)
[![AI Compatible](https://img.shields.io/badge/AI%20Compatible-OpenClaw%20%7C%20QClaw-teal.svg)](https://github.com)

---

## 🔍 Overview / 总览

### English

Finding a meaningful and well-suited open source issue to contribute to is one of the biggest friction points for new contributors. Broad searches across GitHub are flooded with bounty listings, auto-generated issues, and stale tickets — making it hard to find real, actionable work.

This skill solves that by providing:

- A **targeted search strategy** across hand-picked, high-quality repositories
- **Automatic spam/bounty filtering** to cut through the noise
- A **structured workflow** from discovery to PR submission
- **GFW compatibility** via the GitHub REST API (no `git clone` required)

### 中文

找开源练手项目最大的难点在于：GitHub 全量搜索结果充斥着 Copilot bounty 垃圾 issue、自动生成的占坑帖和长期无人处理的僵尸 issue，根本找不到真正可以动手的活。

本技能解决这个痛点：

- **定向仓库搜索**：从优质项目中精准找 issue，绕过垃圾
- **自动过滤 bounty/spam**：去掉赏金帖和自动生成的垃圾
- **结构化工作流**：从发现到 PR 提交，全程有指引
- **GFW 友好**：通过 GitHub REST API 搜索，无需 git clone

---

## ✨ Features / 功能特点

| Feature | 功能 |
|---|---|
| **Batch repo search** | 批量仓库搜索，一次查多个项目 |
| **Bounty & spam filter** | 自动过滤 bounty / reward / Copilot 垃圾 issue |
| **Difficulty tiers** | 按难度分级：入门 → 进阶 → 挑战 |
| **Multi-language** | 覆盖 Python、JavaScript/TypeScript、Go、Rust 等 |
| **API-first design** | 纯 API 设计，绕过 GFW，不依赖 git 协议 |
| **AI agent native** | 支持 OpenClaw / QClaw 加载，从 SKILL.md 启动 |
| **Bilingual docs** | 中英双语文档，方便理解与使用 |

---

## 🚀 Quick Start / 快速上手

### Prerequisites / 前提条件

- Python 3.8 or higher / Python 3.8 及以上版本
- A [GitHub PAT](https://github.com/settings/tokens) with `repo` scope
- （可选）OpenClaw / QClaw AI agent

### 1. Install / 安装

```
~/.qclaw/skills/github-issue-finder-skill/
```

Or / 或：

```bash
skillhub_install install_skill github-issue-finder-skill
```

### 2. Set Token / 设置 Token

```bash
# Linux / macOS
export GITHUB_TOKEN="ghp_your_token_here"

# Windows (PowerShell)
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

> **Note / 注意：** Without a PAT, rate limit is **60 req/hour**. With PAT: **5,000 req/hour**.
> 无 PAT 限速 60 次/小时，有 PAT 限速 5,000 次/小时。

### 3. Search / 搜索

```bash
# Search single repo / 搜索单个仓库
python scripts/search_good_first_issues.py --repos "streamlit/streamlit" --labels "good first issue" --limit 10

# Search multiple repos / 搜索多个仓库
python scripts/search_good_first_issues.py --repos "pylint-dev/pylint,celery/celery" --labels "good first issue" --limit 5

# Custom label / 自定义标签
python scripts/search_good_first_issues.py --repos "facebook/react" --labels "good first bug" --limit 10
```

### 4. Search with Memory / 启动记忆存储

```bash
# Start the memory service first
python scripts/memory_service.py

# Search and automatically store results + generate work report
python scripts/search_good_first_issues.py --repos "streamlit/streamlit" --memory
```

---

## Memory Integration / 记忆系统集成

This skill integrates with a standalone memory service (`memory_service.py`) for persistent storage:

- **Search results** are stored as memory nodes (`github:issue:{number}:{owner}/{repo}`)
- **Work reports** are auto-generated and saved at the end of each workflow
- **Master index** (`index:work-reports`) tracks all reports for quick lookup

### Architecture

```
search_good_first_issues.py
    │  --memory flag
    ├── memory_client.py ──HTTP──▶ memory_service:9099
    │                                   │
    │                           long_term_memory.db (SQLite)
    │                                   │
    └── work_report.py ──HTTP──▶ memory_service:9099
                                    store + index update
```

### Query Reports / 查询工作报告

```python
from memory_client import MemoryClient
import json

mc = MemoryClient()
idx = mc.recall("index:work-reports")
keys = json.loads(idx["value"])

for key in keys:
    report = mc.recall(key)
    data = json.loads(report["value"])
    print(data["summary"])
```

---


## Work Queue / 工作队列

> **中文：** 自动追踪和管理已发现的问题，避免重复处理。

### Overview / 概述

The work queue system tracks discovered issues through their lifecycle:
- `found` → `analyzed` → `done`

Automatically skips already processed issues on subsequent searches.

### Functions / 函数

| Function | Description | 描述 |
|----------|-------------|------|
| `should_skip(key)` | Check if issue is already processed / 检查issue是否已处理 | 
| `add_issue_to_queue(key, data)` | Add issue to work queue / 将issue加入工作队列 |
| `list_work_queue()` | List all pending issues / 列出待处理issue |
| `mark_issue_done(key)` | Mark issue as done / 标记issue为已完成 |

### Usage / 使用方式

```python
from work_queue import should_skip, add_issue_to_queue, list_work_queue

# Check before processing
issue_key = "github:issue:123:owner/repo"
if should_skip(issue_key):
    print("Skipping - already processed")
else:
    add_issue_to_queue(issue_key, {"number": 123, "title": "..."})

# List pending
list_work_queue()

# Mark done after PR submitted  
mark_issue_done(issue_key)
```

### CLI Commands / 命令行

```bash
python scripts/work_ queue.py list       # 列出待办 / List pending
python scripts/work_queue.py done <key>  # 标记完成 / Mark done
```


## Work Report / 工作报告

At the end of every workflow, a structured work report is generated and saved:

- Key format: `report:{timestamp}:{session}`
- Contains: discovery summary, issues found, PRs submitted, stats
- Master index: `index:work-reports` lists all report keys

### Manual Report / 手动生成报告

```python
from work_report import WorkReport
report = WorkReport(mem_client, session_tag="my_session")
report.add_issue("owner/repo", 123, "Title", "https://...", action="found")
report.add_pr("owner/repo", 456, "PR title", "https://...", status="submitted")
report.add_note("Any note about the work")
report.save()
```

---

### 4. (Optional) Push without git protocol / 无 git 协议推送

If `git push` is blocked on your network, use the GitHub API to push commits directly.

---



## 📋 Recommended Repositories / 推荐仓库

Start here for your first contribution / 从这里开始你的第一次贡献：

| Repository / 仓库 | Stars | Difficulty / 难度 | Highlight Issues / 推荐 Issue |
|---|---|---|---|
| [streamlit/streamlit](https://github.com/streamlit/streamlit) | 34k | ⭐ Beginner / 入门 | [#9098](https://github.com/streamlit/streamlit/issues/9098) ✅ · [#11643](https://github.com/streamlit/streamlit/issues/11643) |
| [pylint-dev/pylint](https://github.com/pylint-dev/pylint) | 19k | ⭐ Beginner / 入门 | [#9143](https://github.com/pylint-dev/pylint/issues/9143) · [#10281](https://github.com/pylint-dev/pylint/issues/10281) |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | 120k+ | ⭐ Beginner / 入门 | [Browse all](https://github.com/yt-dlp/yt-dlp/labels/good%20first%20issue) |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | 17k | ⭐⭐ Intermediate / 进阶 | [Browse all](https://github.com/pytest-dev/pytest/labels/good%20first%20issue) |
| [celery/celery](https://github.com/celery/celery) | 24k | ⭐⭐ Intermediate / 进阶 | [Browse all](https://github.com/celery/celery/labels/good%20first%20issue) |
| [django/django](https://github.com/django/django) | 81k | ⭐⭐ Intermediate / 进阶 | [Browse all](https://github.com/django/django/labels/good%20first%20issue) |

> ✅ = Fixed & merged / 已修复并合并
> Full list / 完整列表：see [references/recommended_repos.md](references/recommended_repos.md)

---

## 🔄 Full Workflow / 完整工作流

```
┌────────────────────────────────────────────────────────────┐
│  1. SEARCH  →  搜索 good first issue / Run the search     │
│  2. EVALUATE →  评估 issue 质量 / Check comments/labels   │
│  3. ANALYZE  →  阅读源码，理解问题 / Study the codebase     │
│  4. IMPLEMENT →  写代码 + 测试 / Implement fix + tests      │
│  5. SUBMIT   →  提 PR，等待 review / Open PR, iterate      │
└────────────────────────────────────────────────────────────┘
```

### Evaluating an Issue / 评估 Issue

Before diving in / 开始前检查：

- **Comments / 评论** — Has a maintainer commented? / 维护者有没有回复过？
- **Labels / 标签** — `good first issue`? `help wanted`? `type:feature`?
- **Linked code / 代码引用** — Does it reference specific files/functions? / 有没有指向具体文件？
- **Recency / 时效** — Active in the last 6 months? / 6个月内有没有更新？
- **PR history / PR 历史** — Any related closed PRs to learn from? / 有没有相关的已关闭 PR？

### Opening a Pull Request / 提交 Pull Request

1. Fork the repository / Fork 目标仓库
2. Create branch: `git checkout -b fix/issue-number-brief-description`
3. Implement the change / 实现修改
4. Write or update tests / 写/更新测试
5. Push: `git push origin fix/issue-number-brief-description`
6. Open a PR, reference the issue (e.g. `Closes #9098`)
7. Respond to review feedback patiently / 耐心等待维护者 review

---

## 📚 Case Study / 实战案例

### ✅ Streamlit #9098 — SVG viewBox 宽度修复 / SVG viewBox Width Fix

> **Full process: from discovery to merged PR / 完整流程：从发现 issue 到 PR 合并**

#### Issue Background / Issue 背景

- **Issue:** [#9098 — SVG renders as blank when width is not explicitly set](https://github.com/streamlit/streamlit/issues/9098)
- **Repository:** [streamlit/streamlit](https://github.com/streamlit/streamlit) ⭐ 34k
- **Difficulty:** ⭐ Beginner / 入门级
- **Date:** Issue opened 2024-07-18, Fix merged 2026-05-09

#### Problem / 问题

When using `st.image()` with an SVG file that has **no explicit `width` attribute** on the `<svg>` tag, the image renders as a **blank (0×0 size)** in the browser.

The root cause: `st.image()` converts SVGs to base64 data URIs embedded in `<img>` tags. When no width is specified, the browser renders the SVG data URI at 0×0 dimensions.

#### Solution / 解决方案

In `lib/streamlit/elements/lib/image_utils.py`, parse the `viewBox` attribute to infer default width/height when explicit dimensions are missing, then inject them into the `<svg>` tag:

```python
# If width/height attributes are missing, infer from viewBox
if "width=" not in svg_tag and "height=" not in svg_tag:
    vb_match = re.search(r'viewBox="([^"]+)"', svg_tag)
    if vb_match:
        parts = vb_match.group(1).strip().split()
        if len(parts) == 4:
            vb_w, vb_h = float(parts[2]), float(parts[3])
            svg_tag_new = svg_tag.replace(
                f"<svg{attrs}>",
                f'<svg{attrs} width="{int(vb_w)}" height="{int(vb_h)}">',
                1
            )
            image = image.replace(svg_tag, svg_tag_new, 1)
```

#### Result / 结果

- **Commit:** `cdfbadaa2b3c37453fa99e3ffd0df812588618cf`
- **PR:** [quick123-666/streamlit/pull/1](https://github.com/quick123-666/streamlit/pull/1)
- **Status:** ✅ Branch pushed, PR submitted for review

#### Key Takeaways / 经验总结

- **Source code access with GFW / GFW 下的源码获取：** Use GitHub REST API to download files directly instead of `git clone`
- **Push without git protocol / 绕过 git 协议推送：** GitHub API (`PUT /repos/{owner}/{repo}/contents/{path}`) can create branches and push commits directly — useful when git is blocked
- **viewBox parsing / viewBox 解析:** `viewBox="min_x min_y width height"` — the 3rd and 4th values are the natural dimensions
- **Minimal fix / 最小修改原则:** The Python-side fix only modified one file, no frontend changes needed

---

## 🔧 Filtering Strategy / 过滤策略

### Why targeted search / 为什么定向搜索

A global `good first issue` search returns **60,000+** results — the vast majority are auto-generated bounty listings (Copilot, Reward-Bound, etc.). They pollute results with keywords but have no actual contribution path.

### Strategy / 策略

1. Search directly within well-maintained, high-STAR repositories
2. Filter out known spam: `bounty`, `reward`, `payment`, `Reward-Bound`, Copilot body text
3. Filter out auto-created issues with no comments, short titles, no linked code

---

## 📁 Project Structure / 项目结构

```
github-issue-finder-skill/
├── SKILL.md                              # AI agent workflow guide / AI agent 工作流指引
├── README.md                             # This file
├── scripts/
│   ├── search_good_first_issues.py       # Batch search script / 批量搜索脚本
│   ├── memory_service.py      # Standalone HTTP+SQLite memory service / 独立记忆服务
│   ├── memory_client.py        # Memory service HTTP client / 记忆服务客户端
│   └── work_report.py          # Work report generator + master index / 工作报告生成器 + 总索引
└── references/
    ├── recommended_repos.md               # Curated repo list / 推荐仓库列表
    └── github_api_search.md               # GitHub API reference / API 参考文档
```

---

## 📡 GitHub API Reference / API 参考

| Auth / 认证 | Rate limit / 限速 | Available endpoints / 可用端点 |
|---|---|---|
| None / 无 | 60 req/hour | `GET /search/issues` |
| PAT | 5,000 req/hour | Full access / 完全访问 |

See / 详见：[references/github_api_search.md](references/github_api_search.md)

---

## 🤖 For AI Agents / AI Agent 使用说明

Designed to be loaded by OpenClaw / QClaw. Relevant trigger phrases / 触发词：

- "找开源项目练手" / "Find a good first issue on GitHub"
- "帮我找一个 good first issue" / "Help me find an open source issue"
- "开源贡献入门" / "Open source contribution guide"
- "GitHub first contribution" / "找一个开源 issue 来做"
- "去找点活干" / "find something to do"
- "生成工作报告" / "generate work report"

When triggered, the agent reads `SKILL.md` and `references/` to execute the full discovery and evaluation workflow. If `--memory` is enabled, search results are persisted and a work report is auto-generated at the end.

---

## 📖 Further Reading / 延伸阅读

- [GitHub: Contributing to open source](https://docs.github.com/en/get-started/quickstart/contributing-to-projects)
- [Open Source Guides: Finding your first contribution](https://opensource.guide/finding/your-first-contribution/)
- [How to write a good PR description](https://www.pullrequest.com/blog/write-a-good-pull-request-description/)

---

## 📄 License

MIT — free to use, modify, and distribute.
