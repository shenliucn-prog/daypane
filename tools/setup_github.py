# -*- coding: utf-8 -*-
"""GitHub 一键部署（本机执行）。

前置：
  - 已把 Personal Access Token 写入 C:/Users/Shen/.workbuddy/binaries/gh/token.txt
  - token 需要 repo + workflow 权限（Device Flow 的 App token 不行）

做四件事：
  1) 建公开仓库 shawn-kanban（已存在则复用）
  2) 设置 origin 并 push main
  3) 手动触发 Render Kindle Screen 工作流
  4) 开启 GitHub Pages（gh-pages 分支，根目录）
最后打印 Kindle 要填的 URL。
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOKEN_FILE = r"C:/Users/Shen/.workbuddy/binaries/gh/token.txt"
REPO_NAME = "shawn-kanban"
WORKFLOW = "render.yml"
API = "https://api.github.com"


def token():
    """读取 token。对 BOM / 换行 / 空格免疫 —— 用记事本粘贴保存也能直接用。
    utf-8-sig 会自动吞掉 BOM；strip() 去掉记事本可能加的换行。"""
    if not os.path.exists(TOKEN_FILE):
        sys.exit("缺少 token 文件: " + TOKEN_FILE)
    with open(TOKEN_FILE, encoding="utf-8-sig") as f:
        t = f.read().strip()
    if not t:
        sys.exit("token 文件为空")
    # 只保留 token 本体：有些编辑器会塞奇怪的不可见字符
    t = "".join(ch for ch in t if ch.isprintable()).strip()
    return t


def api(method, path, payload=None, tok=""):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": "token " + tok,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")}


def ensure_repo(tok, login):
    st, body = api("GET", "/repos/%s/%s" % (login, REPO_NAME), tok=tok)
    if st == 200:
        print("[repo] 已存在: %s" % body["full_name"])
        return body
    st, body = api("POST", "/user/repos", {
        "name": REPO_NAME, "public": True,
        "description": "DayPane — Repurpose a jailbroken Amazon Kindle as an e-ink dashboard with KOReader. Weather, world clocks, markets and daily info. Kindle 改造 / 墨水屏看板.",
    }, tok=tok)
    if st not in (201, 200):
        sys.exit("[repo] 创建失败 %s: %s" % (st, body))
    print("[repo] 已创建: %s" % body["full_name"])
    return body


def push(tok, login):
    url = "https://%s@github.com/%s/%s.git" % (tok, login, REPO_NAME)

    def run(args):
        p = subprocess.run(args, cwd=ROOT, capture_output=True)
        return p.returncode, p.stdout.decode(errors="replace") + p.stderr.decode(errors="replace")

    rc, out = run(["git", "remote", "remove", "origin"])
    rc, out = run(["git", "remote", "add", "origin", url])
    if rc != 0:
        print("[push] add remote:", out.strip())
    rc, out = run(["git", "push", "-u", "origin", "main"])
    print("[push] rc=%d" % rc)
    print(out.strip()[-800:])
    if rc != 0:
        sys.exit("[push] 推送失败")
    # 立刻把带 token 的 remote 换掉，避免明文 token 落在 .git/config
    run(["git", "remote", "set-url", "origin",
         "https://github.com/%s/%s.git" % (login, REPO_NAME)])
    print("[push] remote 已改为不带 token 的形式")


def dispatch(tok, login):
    st, body = api(
        "POST", "/repos/%s/%s/actions/workflows/%s/dispatches" % (login, REPO_NAME, WORKFLOW),
        {"ref": "main"}, tok=tok)
    print("[actions] 触发渲染 rc=%s %s" % (st, "" if st in (204, 201) else body))


def enable_pages(tok, login):
    st, body = api("POST", "/repos/%s/%s/pages" % (login, REPO_NAME),
                   {"source": {"branch": "gh-pages", "path": "/"}}, tok=tok)
    if st in (201, 200, 409):
        print("[pages] 已开启 (branch=gh-pages)")
        return
    print("[pages] rc=%s %s" % (st, body))


def main():
    tok = token()
    st, me = api("GET", "/user", tok=tok)
    if st != 200:
        sys.exit("[auth] 失败 %s: %s" % (st, me))
    login = me["login"]
    print("[auth] login=%s" % login)

    ensure_repo(tok, login)
    push(tok, login)
    dispatch(tok, login)
    enable_pages(tok, login)

    print("\n" + "=" * 58)
    print("Kindle 上要填的云端地址：")
    print("  https://%s.github.io/%s/screen.png" % (login, REPO_NAME))
    print("=" * 58)
    print("Actions 大约 1-2 分钟跑完，之后这个 URL 才有内容。")


if __name__ == "__main__":
    main()
