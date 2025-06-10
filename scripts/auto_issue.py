#!/usr/bin/env python3
"""
Create a GitHub Issue automatically when tests fail.

ENV VARS (必要):
- ANTHROPIC_API_KEY : Claude 用 API キー
- GH_TOKEN          : GitHub Personal Access Token
- GITHUB_REPOSITORY : "owner/repo"（GitHub Actions が自動付与）
"""
import os
import sys
import json
import textwrap
import subprocess
import requests
import anthropic

# ---------- 環境変数 ----------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GH_TOKEN          = os.getenv("GH_TOKEN")
REPO              = os.getenv("GITHUB_REPOSITORY")           # 例: bikkkubo/anthro-multiagent
MODEL             = "claude-3-opus-20240229"

if not all([ANTHROPIC_API_KEY, GH_TOKEN, REPO]):
    sys.exit("❌ Missing required environment variables.")

# ---------- ユーティリティ ----------
def run(cmd: str) -> str:
    """シェルコマンドを実行し stdout+stderr を文字列で返す"""
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

def gather_context() -> str:
    """diff, テスト結果, lint を 1 本の文字列にまとめる"""
    diff  = run("git diff --unified=0") or "NO DIFF"
    tests = run("pytest -q || true")          # 失敗しても続行
    lint  = run("flake8 || true")
    return textwrap.dedent(f"""
    ## Git Diff
    ```diff
    {diff}
    ```

    ## Test Result
    ```
    {tests}
    ```

    ## Lint
    ```
    {lint}
    ```
    """)

def ask_claude(prompt: str) -> dict:
    """Claude で Issue の title / body / labels を JSON 生成"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    rsp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=("あなたは優秀なリリースマネージャー。"
                "入力を読み、GitHub Issue に使う "
                "JSON で {title:str, body:str, labels:list[str]} を返せ。"),
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(rsp.content[0].text)

def create_issue(issue: dict) -> str:
    """GitHub REST API v3 で Issue を作成し URL を返す"""
    url  = f"https://api.github.com/repos/{REPO}/issues"
    hdrs = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.post(url, json=issue, headers=hdrs, timeout=30)
    r.raise_for_status()
    return r.json()["html_url"]

# ---------- メイン ----------
if __name__ == "__main__":
    context = gather_context()
    issue   = ask_claude(context + "\n- Issue には 'auto-generated' ラベルを必ず付けよ。")
    url     = create_issue(issue)
    print(f"✅ Issue created: {url}")
