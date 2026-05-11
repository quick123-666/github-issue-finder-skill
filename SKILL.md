---
name: github-issue-finder-skill
description: Find good first issues on GitHub for open source contribution. Search curated repos, filter bounty/spam, analyze issue quality, guide users through search to evaluate to PR workflow. Trigger phrases include "find open source project to practice", "good first issue", "find a good first issue on GitHub", "open source contribution starter", "find something to do".
---

# GitHub Issue Finder / GitHub Issue Lookup Assistant

> **English:** Help users find and claim high-quality `good first issue` targets across curated open source repositories. Covers the full workflow from search to evaluation to PR submission.
>
> **Chinese:** Help users discover, evaluate, and claim quality open source issues on GitHub. Search quality projects, filter spam, submit PR. Supports bilingual workflow.

---

## Search Strategy

### Global search is unreliable

A global `good first issue` search on GitHub returns 60,000+ results -- mostly auto-generated Copilot bounty listings and spam.

### Targeted Strategy

Search directly within curated, high-quality repositories. This eliminates 99% of spam.

**Recommended Repositories (by difficulty):**

| Repository | Stars | Difficulty | Good First Issues |
|---|---|---|---|
| [streamlit/streamlit](https://github.com/streamlit/streamlit/labels/good%20first%20issue) | 34k | Beginner | [#9098](https://github.com/streamlit/streamlit/issues/9098) . [#11643](https://github.com/streamlit/streamlit/issues/11643) |
| [pylint-dev/pylint](https://github.com/pylint-dev/pylint/labels/good%20first%20issue) | 19k | Beginner | [#9143](https://github.com/pylint-dev/pylint/issues/9143) . [#10281](https://github.com/pylint-dev/pylint/issues/10281) |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/labels/good%20first%20issue) | 120k | Beginner | various |
| [celery/celery](https://github.com/celery/celery/labels/good%20first%20issue) | 24k | Intermediate | distributed task queue |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest/labels/good%20first%20issue) | 17k | Intermediate | testing framework |
| [django/django](https://github.com/django/django/labels/good%20first%20issue) | 81k | Intermediate | web framework |

Full list: [references/recommended_repos.md](references/recommended_repos.md)

---

## GitHub API Search

**Requires:** `ghp_` PAT token, or anonymous (60 req/hour limit)

```bash
# Search in a single repo
GET https://api.github.com/repos/{owner}/{repo}/issues?labels=good%20first%20issue&state=open&sort=updated&per_page=10
```

**Python script:**
```bash
python scripts/search_good_first_issues.py --repos "streamlit/streamlit,pylint-dev/pylint,celery/celery" --labels "good first issue" --limit 20
```

API details: [references/github_api_search.md](references/github_api_search.md)

---

## Issue Evaluation Criteria

| Do Recommend | Skip |
|---|---|
| Clear bug description or feature request | Contains "bounty" / "reward" / "payment" |
| Maintainer commented or labeled | Auto-created Copilot issue |
| References specific code/files | Many likes but no discussion |
| Updated within 6 months | Closed |
| `difficulty:starter` / `beginner` label | `wontfix` / `duplicate` label |

---

## Workflow

```
0. CONSULT  -> Read references/work_reports/ + references/project_tracker.md
1. SEARCH   -> Run script or browse recommended repos; SKIP any project in `dropped` status
2. EVALUATE -> Check comments, labels, code references
3. ANALYZE  -> Read CONTRIBUTING.md, study relevant source code
4. IMPLEMENT -> Write fix + add/update tests
5. SUBMIT   -> Create PR, reference issue, respond to review
6. ITERATE  -> Fix feedback, re-request review
7. TRACK    -> Update references/project_tracker.md with latest status
   - If attempt >= 3 and still failing -> mark `dropped` and stop
   - If maintainer silent > 14 days -> mark `stalled`
   - If maintainer rejects -> mark `dropped` or `closed`
```

---

## How to Submit a PR / 如何帮用户提交 PR

### 前提条件

- **GitHub Token**: `ghp_your_token_here`（具有 `repo` scope）
- **Fork 用户名**: `quick123-666`
- **API 基础**: 所有操作通过 GitHub REST API 完成，不使用 git 命令行
- **流程**: Fork → Branch → Commit → PR

### 第一步：Fork 仓库

```python
POST https://api.github.com/repos/{upstream_owner}/{repo}/forks
# 自动创建到 quick123-666/{repo}
```

如果 fork 已存在，直接复用，无需重复创建。

### 第二步：创建分支

从 upstream 的默认分支（通常是 `main` 或 `develop`）创建新分支：

```python
# 获取 upstream 分支 SHA
GET https://api.github.com/repos/{upstream_owner}/{repo}/git/refs/heads/{default_branch}

# 在 fork 上创建新分支
POST https://api.github.com/repos/quick123-666/{repo}/git/refs
{
  "ref": "refs/heads/{branch_name}",
  "sha": "{sha_from_upstream}"
}
```

**分支命名规范：** `fix/{issue-keyword}` 或 `feat/{feature-keyword}`（如 `fix/camera-input-size`）

### 第三步：读取原文件

```python
GET https://api.github.com/repos/{upstream_owner}/{repo}/contents/{file_path}?ref={branch}
# 返回 JSON，content 是 base64 编码，需要解码
content = base64.b64decode(resp["content"]).decode("utf-8")
```

### 第四步：修改文件并提交

```python
PUT https://api.github.com/repos/quick123-666/{repo}/contents/{file_path}
{
  "message": "commit message",
  "content": base64.b64encode(new_content.encode()).decode(),
  "sha": "{file_sha}",    # 从 GET 响应中获取
  "branch": "{branch_name}"
}
```

**关键注意：** `sha` 是文件的 blob SHA（从 GET 响应的 `sha` 字段获取），**不是** commit SHA。

### 第五步：提交 PR

```python
POST https://api.github.com/repos/{upstream_owner}/{repo}/pulls
{
  "title": "简短描述性标题",
  "head": "quick123-666:{branch_name}",
  "base": "{default_branch}",
  "body": "PR 描述（包含 issue 引用、改动说明、测试计划）"
}
```

### PR 提交要点

| 项目 | 要求 |
|------|------|
| **标题** | 带前缀 `feat:` / `fix:` / `refactor:` / `chore:` / `test:` |
| **关联 issue** | body 中写 `Closes #N` 或 `Related to #N` |
| **改动说明** | 列出每个改动的文件和目的 |
| **测试计划** | 说明哪些测试通过、新增了什么测试 |
| **CI** | 提交后关注 CI 状态，失败时及时修复 |

### 第六步：处理 Review 反馈

1. 定期检查 PR 上的评论（`GET /repos/{owner}/{repo}/issues/{number}/comments`）
2. 如果是 bot 审查（如 Greptile），根据反馈修改代码并重新提交
3. 在评论区回复 `@{reviewer} please re-review` 或说明改动

### 需要避免的情况

- ❌ 不要使用 git 命令行（可能被墙阻塞）
- ❌ 不要更新 fork 的 git config
- ❌ 不要 force push 到已发布的 PR（使用新增 commit 而非覆盖）
- ❌ 不要为一个 PR 创建多个分支——所有修改在一个分支上累积提交
- ❌ 不要遗漏测试——每个功能改动必须附带测试

---

## Project Tracker / 项目清单

所有参与过的项目必须记录在 `references/project_tracker.md` 中，按项目单独管理状态。

### 清单结构

```markdown
| 项目 | Issues | PRs | CI状态 | 维护者反馈 | 当前状态 | 尝试次数 |
|------|--------|-----|--------|-----------|---------|---------|
| owner/repo | #1, #2 | #3, #4 | ✅ | ✅ 已回复 | active | 2 |
```

### 状态定义

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `active` | 正在跟进 | PR 已提交，等待 review 或修复反馈 |
| `stalled` | 暂停 | PR 提交后超过 7 天无 maintainer 回复 |
| `dropped` | 已放弃 | 尝试 ≥ 3 次仍失败，或 maintainer 明确拒绝 |
| `merged` | 已合并 | PR 被合并到主分支 |
| `closed` | 已关闭（未合并）| PR 被关闭且明确拒绝 |

### 放弃规则

- **尝试 3 次**后问题仍未解决 → 标记 `dropped`
- **超过 14 天**无 maintainer 回复 → 标记 `stalled`，视为 passive drop
- maintainer **明确拒绝**（wontfix / invalid）→ 立即标记 `dropped`
- CI 反复失败且无法解决 → 标记 `dropped` 并记录原因

### 每次操作后必须更新

1. 更新 `references/project_tracker.md` 中的对应项目行
2. 如果某个项目状态变为 `dropped`，在 Workflow 的 SEARCH 步骤跳过该项目
3. 在 session 总结中报告当前所有项目状态

---

This skill integrates with the Long-Term Memory system (memory_service on port 9099):

- `--memory` flag: stores search results as persistent memory nodes
- Each issue is stored with key `github:issue:{number}:{owner}/{repo}`
- Memory tags include the repo name and session tag
- Supports recall via `MemoryClient.search()` for future reference

Start the memory service:
```bash
python src/memory_service.py
```

Search with memory:
```bash
python scripts/search_good_first_issues.py --repos "streamlit/streamlit" --memory
```

---

## Knowledge Base / 知识库

The `references/work_reports/` directory functions as a **living knowledge base**. Past fixes contain patterns and insights that directly apply to new issues.

### Before starting ANY work, you MUST:

1. **Read the index**: `references/work_reports/index.md` — scan for similar repos, patterns, or error types
2. **Read relevant reports**: If the new issue shares a repo, error type, or technology pattern with a past report, read that report fully
3. **Extract applicable patterns**: Identify which "Key Insight" from past reports applies to the current problem
4. **Apply proactively**: Don't make the same mistakes twice — if a past report warns about a trap, avoid it from the start

### Presenting candidates to the user

After searching, format the output using `references/project_listing_template.md`. Group by difficulty (🟢 简单 / 🟡 中等 / 🔴 困难). Exclude already-worked-on projects from the list.

### Example: Knowledge Base in action

| New Issue | Past Report | Pattern to apply |
|-----------|-------------|------------------|
| Any Rust binding error | WireGuard EADDRINUSE | Rust errors come as `RuntimeError`, not `OSError` — catch and convert |
| Any bytes/string manipulation | Multipart newlines | `bytes.splitlines()` is destructive; Python 3.13+ has f-string+bytes pitfalls |
| Any click CLI change | Poetry multiple authors | Use `multiple=True` on click options, not separate flags |
| Any competing PR | pylint JUnit review | Check for existing PRs first; hook-based > modification-based architecture |
| Any proto→Python→frontend change | Streamlit camera_input size | Three-layer pattern: proto fields → both public+internal Python funcs → JS camelCase access; uint32 0 = not set |

### Accumulated Lessons (extracted from all reports)

See [references/work_reports/lessons.md](references/work_reports/lessons.md) for the full list of cross-cutting patterns.

### How to contribute to the knowledge base

**After every PR/analysis workflow, you MUST:**
1. Create a markdown file in `references/work_reports/` with **Problem → Root Cause → Fix → Key Insight**
2. Add relevant keywords/patterns to the report so future lookups can match
3. Update `references/work_reports/index.md`
4. If the insight is cross-cutting (applies beyond this specific repo), add it to `references/work_reports/lessons.md`
5. Update `references/project_tracker.md` — add/update the project row with latest status

---

## Work Report / 工作报告

At the end of every workflow, the skill generates a **work report** and saves it to the memory service with a master index.

### How it works

1. `WorkReport` class collects all work items (issues found, analyzed, PRs submitted, notes)
2. `save()` generates a structured JSON report and stores it as key `report:{timestamp}:{session}`
3. Master index node `index:work-reports` tracks all report keys for fast lookup

### Stored report structure

```json
{
  "date": "2026-05-09",
  "session": "sess_1234567890",
  "summary": "worked on 3 repos; found 5 issues; analyzed 2 issues; submitted 1 PR",
  "items": [
    {"type": "issue", "action": "found", "repo": "streamlit/streamlit", ...},
    {"type": "pr", "action": "submitted", ...}
  ],
  "stats": {
    "total_items": 8,
    "issues_found": 5,
    "issues_analyzed": 2,
    "prs_submitted": 1,
    "repos": ["streamlit/streamlit", "pylint-dev/pylint"]
  }
}
```

### Local file persistence (references/work_reports/)

Work reports are also saved as **markdown files** in `references/work_reports/` for permanent, searchable reference.

**Naming convention:** `YYYY-MM-DD_repo-topic.md`

**Required sections in every report:**

```markdown
# Title

- **Repo:** owner/repo
- **Issue:** [#N](url)
- **PR:** [#N](url)
- **Date:** YYYY-MM-DD

## Problem

What was the issue?

## Root Cause

Why did the bug occur? What was the fundamental mistake?

## Fix

What code was changed? Include key snippets.

## Key Insight

What general lesson can be learned from this fix?
```

**Index:** `references/work_reports/index.md` maintains a table of all reports.

**After every PR/analysis workflow, you MUST:**
1. Create a markdown file in `references/work_reports/`
2. Update `references/work_reports/index.md` with the new entry
3. Update `references/project_tracker.md` with latest status

### Search reports

```python
from memory_client import MemoryClient
mc = MemoryClient()
idx = mc.recall("index:work-reports")  # get all report keys
for key in json.loads(idx["value"]):
    report = mc.recall(key)
    print(report["value"]["summary"])
```

### Manual usage

```python
from work_report import WorkReport
report = WorkReport(mem_client, session_tag="my_session")
report.add_issue("owner/repo", 123, "Title", "https://...", action="found")
report.add_pr("owner/repo", 456, "PR title", "https://...", status="submitted")
report.add_note("Any note about the work")
report.save()
```

---

## GFW / Network Handling

| Problem | Solution |
|---|---|
| `git clone` blocked | Use GitHub REST API to download individual files directly |
| Git push blocked | Use GitHub API to create branches and push commits |
| Browser tools blocked | Use web_fetch or GitHub API instead |
| GitHub API accessible | PAT authentication works fine |

---

## Case Study: Streamlit #9098

**Issue:** `st.image()` displays blank for SVG without explicit width
**Fix:** Parse viewBox to extract width/height and inject into `<svg>` tag
**Result:** PR submitted, pending merge

Key steps:
1. Use API to find #9098
2. Download `lib/streamlit/elements/lib/image_utils.py` via API
3. Root cause: SVG without explicit width -> base64 `<img>` renders 0x0
4. Fix: parse `viewBox="x y w h"` -> inject `<svg width="w" height="h">`
5. Push to fork branch via API (bypass git protocol)
6. PR submitted: https://github.com/quick123-666/streamlit/pull/1

---

## References

- [references/recommended_repos.md](references/recommended_repos.md) - Full curated repo list
- [references/github_api_search.md](references/github_api_search.md) - API syntax, rate limits, auth
- [references/work_reports/index.md](references/work_reports/index.md) - Work reports index
- [references/work_reports/](references/work_reports/) - Individual work report files
- [scripts/search_good_first_issues.py](scripts/search_good_first_issues.py) - Batch search script
- [scripts/memory_client.py](scripts/memory_client.py) - Memory service client
- [scripts/work_report.py](scripts/work_report.py) - Work report generator with master index
