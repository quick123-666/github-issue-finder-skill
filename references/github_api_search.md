# GitHub API 搜索指南

## 认证

未认证：每小�?60 次请求�? 
�?PAT token：每小时 5000 次请求�?

```bash
# 方式1：环境变�?
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"

# 方式2：直接传�?
--token "YOUR_GITHUB_TOKEN"
```

设置 `GITHUB_TOKEN` 环境变量，或通过 `--token` 参数传入你的 Fine-Grained PAT�?

## 核心 API

### 单仓库搜�?issues

```
GET https://api.github.com/repos/{owner}/{repo}/issues
?labels=good%20first%20issue
&state=open
&sort=updated
&direction=desc
&per_page=10
```

### 多仓库组合搜索（推荐�?

```
GET https://api.github.com/search/issues
?q=repo:streamlit/streamlit+repo:pylint-dev/pylint+label:"good first issue"+is:issue+is:open
&per_page=20
&sort=updated
```

### 搜索语法

| 关键�?| 说明 | 示例 |
|--------|------|------|
| `repo:owner/name` | 指定仓库 | `repo:streamlit/streamlit` |
| `label:"name"` | 指定标签（空格用 %20 �?+�?| `label:"good first issue"` |
| `is:issue` | �?issue（排�?PR�?| `is:issue` |
| `is:pr` | �?PR | `is:pr` |
| `is:open` | 仅开�?| `is:open` |
| `is:closed` | 已关�?| `is:closed` |
| `author:username` | 某人创建 | `author:octocat` |
| `assignee:username` | 分配给某�?| `assignee:none` |
| `comments:>0` | 有评�?| `comments:>5` |
| `created:>YYYY-MM-DD` | 创建时间 | `created:>2024-01-01` |
| `updated:>YYYY-MM-DD` | 更新时间 | `updated:>2024-06-01` |

## 通过 API 下载仓库文件（绕�?git clone�?

GFW 阻断 git 协议时，�?API 下载单个文件�?

### 获取文件内容
```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
```

响应包含 `content`（base64 编码）和 `download_url`�?

```python
import base64, urllib.request, json

url = "https://api.github.com/repos/streamlit/streamlit/contents/lib/streamlit/elements/lib/image_utils.py"
req = urllib.request.Request(url, headers={"Authorization": "token YOUR_GITHUB_TOKEN", "Accept": "application/vnd.github.v3+json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    content = base64.b64decode(data["content"]).decode("utf-8")
```

### 列出目录文件
```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
```

### 获取分支信息
```
GET https://api.github.com/repos/{owner}/{repo}/branches/{branch}
```

### 创建/更新文件（提�?commit�?
```
PUT https://api.github.com/repos/{owner}/{repo}/contents/{path}

Body:
{
  "message": "commit message",
  "content": "base64_encoded_content",
  "sha": "blob_sha (required for updates)",
  "branch": "branch-name"
}
```

获取现有文件 SHA�?
```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}
```

## 通过 API 创建 commit（模�?git push�?

1. 获取 HEAD commit SHA �?获取 tree SHA �?创建�?blob �?创建 tree �?创建 commit �?更新 branch ref

```python
# 完整流程参�?GitHub API docs:
# https://docs.github.com/en/rest/git/refs
```

## 速率限制

| 场景 | 限制 |
|------|------|
| 未认�?| 60 req/hr |
| 认证（普�?PAT�?| 5000 req/hr |
| 搜索 API（认证） | 30 req/min |
| 单仓�?API | 5000 req/hr |

超过限制：API 返回 `403 Forbidden`，响应头 `X-RateLimit-Remaining: 0`，`Retry-After` 告诉你等多少秒�?

## 注意事项

- API 返回�?issues 包含 PR（GitHub 不区分），需过滤 `"pull_request" not in issue`
- Issues 响应没有 `body` 字段（节省带宽），需要单独请求：`GET /repos/{owner}/{repo}/issues/{number}`
- 多仓库搜�?`repo:` �?`+` 连接，最�?5 个仓�