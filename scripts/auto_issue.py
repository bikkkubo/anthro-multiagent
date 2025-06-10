# scripts/auto_issue.py
import os, subprocess, json, anthropic, requests, textwrap, tempfile

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GH_TOKEN          = os.getenv("GH_TOKEN")
REPO              = os.getenv("GITHUB_REPOSITORY")  # 例: bikkkubo/anthro-multiagent
MODEL             = "claude-3-opus-2025-06-06"

def run(cmd): return subprocess.check_output(cmd, shell=True, text=True)

def gather_context():
    diff  = run("git diff --staged --unified=0") or "NO DIFF"
    try:
        test = run("pytest -q")                   # 失敗すると例外
    except subprocess.CalledProcessError as e:
        test = e.output or str(e)
    lint = run("flake8 || true")
    return diff, test, lint

def ask_claude(prompt):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    rsp = client.messages.create(
        model       = MODEL,
        max_tokens  = 1024,
        system      = "あなたは優秀なリリースマネージャー。"
                      "入力を読んで GitHub Issue を JSON(title, body, labels) で返す。",
        messages    = [{"role": "user", "content": prompt}]
    )
    return json.loads(rsp.content[0].text)

def create_issue(issue):
    url  = f"https://api.github.com/repos/{REPO}/issues"
    hdrs = {"Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github+json"}
    r = requests.post(url, json=issue, headers=hdrs, timeout=30)
    r.raise_for_status()
    return r.json()["html_url"]

if __name__ == "__main__":
    diff, test, lint = gather_context()
    prompt = textwrap.dedent(f"""
        ## Git Diff
        ```diff
        {diff}
        ```

        ## Test Result
        ```
        {test}
        ```

        ## Lint
        ```
        {lint}
        ```

        - コミット規約: Conventional Commits
        - Issue は “自動生成” ラベルを必ず含めよ
        - 具体的なタスクを 1 件に絞り、受入基準も本文に書け
    """)
    issue_json = ask_claude(prompt)
    url = create_issue(issue_json)
    print("✅ Created:", url)
