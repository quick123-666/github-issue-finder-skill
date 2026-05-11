#!/usr/bin/env python3
"""
GitHub Good First Issue Searcher
Searches specified repos for good first issues, filters out bounty/spam.

Usage:
    python search_good_first_issues.py --repos "streamlit/streamlit,pylint-dev/pylint"
    python search_good_first_issues.py --repos "django/django" --labels "good first issue" --limit 15
    python search_good_first_issues.py --repos "quick123-666/streamlit" --token "ghp_xxx"
"""

import argparse
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error


def search_repo_issues(owner, repo, labels, state="open", per_page=15, token=None):
    """Search issues in a single repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {
        "labels": labels,
        "state": state,
        "sort": "updated",
        "direction": "desc",
        "per_page": per_page,
    }
    url += "?" + urllib.parse.urlencode(params)

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-oss-practice-skill",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [ERROR] HTTP {e.code} for {owner}/{repo}: {e.reason}")
        return []
    except Exception as e:
        print(f"  [ERROR] {e}")
        return []


def is_bounty_issue(issue):
    """Check if an issue is a bounty/spam issue (Copilot-generated garbage)."""
    title_lower = issue.get("title", "").lower()
    body_lower = (issue.get("body") or "").lower()
    repo_name = issue.get("repository_url", "").lower()

    # Known bounty/spam patterns
    if "bounty" in title_lower and ("reward" in title_lower or "$" in title_lower):
        return True
    if "copilot" in body_lower and "bounty" in body_lower:
        return True
    # Rustchain bounties are a known spam source
    if "rustchain" in repo_name or "scottcjn" in repo_name:
        return True
    # Auto-created Copilot issues often have very short titles
    if (
        len(title_lower) < 20
        and issue.get("comments", 0) == 0
        and "bounty" in body_lower
    ):
        return True
    return False


def format_issue(issue):
    """Format a single issue for display."""
    repo_url = issue.get("repository_url", "")
    repo = repo_url.replace("https://api.github.com/repos/", "")

    lines = []
    lines.append(f"  #{issue['number']}  {issue['title']}")
    lines.append(f"    URL: {issue['html_url']}")
    lines.append(
        f"    [{issue.get('comments', 0)} comments] | Updated: {issue['updated_at'][:10]}"
    )

    labels = [l.get("name", "") for l in issue.get("labels", [])]
    if labels:
        lines.append(f"    Labels: {', '.join(labels)}")

    return "\n".join(lines)


def get_difficulty(issue):
    """Determine issue difficulty from labels and comments."""
    labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
    comments = issue.get("comments", 0)
    title = issue.get("title", "").lower()
    
    # === 高级 (Advanced) ===
    # 高评论数 = 复杂/难点
    if comments >= 20:
        return "advanced"
    
    # 明确的困难 label
    if any(l in labels for l in ["difficulty:hard", "difficulty:advanced"]):
        return "advanced"
    
    # 核心区域 sig/
    if any(l in labels for l in ["sig/"]):
        return "advanced"
    
    # === 入门级 (Beginner) ===
    # 评论少 + 明确 beginner label
    if comments <= 3:
        if any(l in labels for l in ["good first issue", "help wanted", "starter", "difficulty:beginner"]):
            return "beginner"
    
    # === 中级 (Intermediate) ===
    return "intermediate"
    return "intermediate"


def format_list_mode(issues, repos):
    """Format issues in categorized list by difficulty - equal distribution."""
    beginner = []
    intermediate = []
    advanced = []
    
    for issue in issues:
        diff = get_difficulty(issue)
        repo_url = issue.get("repository_url", "")
        repo = repo_url.replace("https://api.github.com/repos/", "")
        
        item = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "repo": repo,
            "comments": issue.get("comments", 0),
        }
        
        if diff == "beginner":
            beginner.append(item)
        elif diff == "intermediate":
            intermediate.append(item)
        else:
            advanced.append(item)
    
    # 一比一比一均衡：每类取相同数量
    min_count = min(len(beginner), len(intermediate), len(advanced))
    if min_count > 0:
        beginner = beginner[:min_count]
        intermediate = intermediate[:min_count]
        advanced = advanced[:min_count]
    
    output = []
    
    if beginner:
        output.append("## 🌱 入门级 (Beginner)")
        output.append("")
        output.append("| Issue | 项目 | 描述 | 评论 |")
        output.append("|-------|------|------|------|")
        for i in beginner:
            title = i["title"][:50] + "..." if len(i["title"]) > 50 else i["title"]
            output.append(f"| [#{i['number']}]({i['url']}) | {i['repo']} | {title} | {i['comments']} |")
        output.append("")
    
    if intermediate:
        output.append("## 🔥 中级 (Intermediate)")
        output.append("")
        output.append("| Issue | 项目 | 描述 | 评论 |")
        output.append("|-------|------|------|------|")
        for i in intermediate:
            title = i["title"][:50] + "..." if len(i["title"]) > 50 else i["title"]
            output.append(f"| [#{i['number']}]({i['url']}) | {i['repo']} | {title} | {i['comments']} |")
        output.append("")
    
    if advanced:
        output.append("## 🚀 高级 (Advanced)")
        output.append("")
        output.append("| Issue | 项目 | 描述 | 评论 |")
        output.append("|-------|------|------|------|")
        for i in advanced:
            title = i["title"][:50] + "..." if len(i["title"]) > 50 else i["title"]
            output.append(f"| [#{i['number']}]({i['url']}) | {i['repo']} | {title} | {i['comments']} |")
        output.append("")
    
    return "\n".join(output)




# ========== REPORT TEMPLATE ==========
# 按此模板格式输出搜索结果
# Follow this template for reporting search results

def format_report(issues_by_level, repos):
    """Format issues according to project listing template"""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("### 🟢 简单（Good First Issue）")
    lines.append("")
    lines.append("| 项目 | Issue | 简述 | 技术栈 |")
    lines.append("|------|-------|------|--------|")
    for issue in issues_by_level.get("beginner", [])[:5]:
        lines.append(f"| {issue.get('repo','')} | [#{issue.get('number','')}]({issue.get('url','')}) | {issue.get('title','')[:30]} | {issue.get('tech_stack','')} |")
    lines.append("")
    lines.append("### 🟡 中等（Help Wanted）")
    lines.append("")
    lines.append("| 项目 | Issue | 简述 | 技术栈 |")
    lines.append("|------|-------|------|--------|")
    for issue in issues_by_level.get("intermediate", [])[:5]:
        lines.append(f"| {issue.get('repo','')} | [#{issue.get('number','')}]({issue.get('url','')}) | {issue.get('title','')[:30]} | {issue.get('tech_stack','')} |")
    lines.append("")
    lines.append("### 🔴 困难（Bug / 复杂 Feature）")
    lines.append("")
    lines.append("| 项目 | Issue | 简述 | 技术栈 |")
    lines.append("|------|-------|------|--------|")
    for issue in issues_by_level.get("advanced", [])[:5]:
        lines.append(f"| {issue.get('repo','')} | [#{issue.get('number','')}]({issue.get('url','')}) | {issue.get('title','')[:30]} | {issue.get('tech_stack','')} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**建议：** 推荐 beginner 级别 #" + str(issues_by_level.get("beginner", [{}])[0].get("number", "")) + " (" + str(issues_by_level.get("beginner", [{}])[0].get("repo", "")) + ")")
    lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Search GitHub for good first issues across multiple repos"
    )
    parser.add_argument(
        "--repos",
        required=True,
        help="Comma-separated list of owner/repo pairs, e.g. 'streamlit/streamlit,pylint-dev/pylint'",
    )
    parser.add_argument(
        "--labels",
        default="good first issue",
        help="Comma-separated label names (default: 'good first issue')",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Max issues per repo (default: 10)"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub PAT token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip bounty/spam filtering",
    )
    parser.add_argument(
        "--list-mode",
        action="store_true",
        default=True,
        help="Output in categorized list format (default: on)",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple output instead of categorized list",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Store results in memory service (requires memory_service running)",
    )
    parser.add_argument(
        "--memory-host",
        default="127.0.0.1",
        help="Memory service host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--memory-port",
        type=int,
        default=9099,
        help="Memory service port (default: 9099)",
    )
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN") or None

    # Connect to memory service if requested
    mem_client = None
    if args.memory:
        try:
            from memory_client import MemoryClient
            mc = MemoryClient(host=args.memory_host, port=args.memory_port)
            if mc.available():
                mem_client = mc
                print(f"[Memory] memory_service connected ({args.memory_host}:{args.memory_port})")
            else:
                print(f"[Memory] memory_service not available, skipping memory storage")
        except Exception as e:
            print(f"[Memory] memory client init failed: {e}")

    repos = [r.strip() for r in args.repos.split(",")]
    print(f"\nSearching {len(repos)} repos for '{args.labels}' issues...\n")

    all_issues = []
    for i, repo in enumerate(repos):
        if "/" not in repo:
            print(f"[SKIP] Invalid format '{repo}', expected owner/repo")
            continue

        owner, repo_name = repo.split("/", 1)
        print(f"[{i+1}/{len(repos)}] {owner}/{repo_name}...", end=" ", flush=True)

        issues = search_repo_issues(owner, repo_name, args.labels, token=token)

        if not args.no_filter:
            issues = [it for it in issues if not is_bounty_issue(it)]

        # Remove pull requests (GitHub issues API returns PRs too)
        issues = [it for it in issues if "pull_request" not in it]

        print(f"found {len(issues)} (filtered from {len(issues) if args.no_filter else 'all'})")
        all_issues.extend(issues)

        if i < len(repos) - 1:
            time.sleep(1)  # Be nice to the API

    if not all_issues:
        print("\nNo issues found.")
        return

    # Sort by updated_at descending
    all_issues.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    display_issues = all_issues[: args.limit * len(repos)]
    
    # Default to list mode, use --simple for old format
    if args.list_mode and not args.simple:
        output = format_list_mode(display_issues, repos)
        print(f"\n{output}")
    else:
        print(f"\n{'='*60}")
        print(f"Total: {len(all_issues)} issues\n")

        import sys
        for issue in display_issues:
            text = format_issue(issue)
            if sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "gb2312", "gb18030"):
                text = text.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
            print(text)
            print()

    # Store in memory service if available
    if mem_client:
        stored = 0
        session_tag = f"github_search_{int(time.time())}"
        for issue in all_issues[: min(20, len(all_issues))]:
            repo_url = issue.get("repository_url", "")
            repo = repo_url.replace("https://api.github.com/repos/", "")
            key = f"github:issue:{issue['number']}:{repo}"
            val = json.dumps({
                "title": issue["title"],
                "url": issue["html_url"],
                "repo": repo,
                "comments": issue.get("comments", 0),
                "updated": issue["updated_at"][:10],
                "labels": [l["name"] for l in issue.get("labels", [])],
            }, ensure_ascii=False)
            r = mem_client.store(
                key=key, value=val, category="skill",
                confidence=0.8, source="github-issue-finder",
                tags=[repo, session_tag, "good-first-issue"],
            )
            if r.get("status") == "ok":
                stored += 1
        mem_client.log("github-issue-finder", "search", f"stored {stored} issues from {len(repos)} repos")
        print(f"\n[Memory] Stored {stored} issues in memory service")

        # Generate and save work report (always at end of workflow)
        try:
            from work_report import WorkReport
            report = WorkReport(mem_client, session_tag=session_tag)
            for issue in all_issues[: min(20, len(all_issues))]:
                repo_url = issue.get("repository_url", "")
                repo = repo_url.replace("https://api.github.com/repos/", "")
                report.add_issue(
                    repo, issue["number"], issue["title"],
                    issue["html_url"], action="found",
                )
            report.add_note(f"Searched {len(repos)} repos with label '{args.labels}'")
            report.save()
        except Exception as e:
            print(f"[WorkReport] Error generating report: {e}")


if __name__ == "__main__":
    main()
