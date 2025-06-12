# agents/core.py
"""
Multi-agent core with Context-Awareness Gate (CAG) support.

構成
------
USER  →  PRESIDENT  →  BOSS  →  WORKER×N
            ▲                       │
            └──────── CAG 判定 ──────┘
"""

import os
import asyncio
import json
import textwrap
from typing import List

import anthropic
from dotenv import load_dotenv

from agents.context_gate import need_external_search

# ───── 環境設定 ──────────────────────────────────────────────────────────
load_dotenv()
_CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_MODEL  = "claude-3-sonnet-20240229"  # 利用可能モデル ID に合わせてください

# ───── 共通呼び出しヘルパー ───────────────────────────────────────────
async def ask(system: str, user_msg: str, max_tokens: int = 2048) -> str:
    """非同期で Claude を呼び出し text を返す"""
    rsp = await _CLIENT.messages.create(
        model=_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return rsp.content[0].text.strip()


# ───── WORKER ───────────────────────────────────────────────────────────
class Worker:
    """実務担当エージェント"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.sys  = f"{name} は実務担当。指示に簡潔に答えよ。"

    async def run(self, task: str) -> str:
        """CAG を噛ませてタスクを実行"""
        if need_external_search(task):
            # ★ 今は“検索タグ付け”だけ。後続フェーズで Hybrid Retrieval を実装
            task_for_llm = f"[SEARCH NEEDED]\n{task}"
        else:
            task_for_llm = f"[NO SEARCH]\n{task}"

        return await ask(self.sys, task_for_llm)


# ───── BOSS ─────────────────────────────────────────────────────────────
class Boss:
    """複数 WORKER の回答を統合する中間マネージャー"""

    def __init__(self, workers: List[Worker]) -> None:
        self.workers = workers
        self.sys     = "BOSS: WORKER の回答を統合し要点のみ返答せよ。"

    async def run(self, task: str) -> str:
        # WORKER を並列実行
        results = await asyncio.gather(*(w.run(task) for w in self.workers))
        joined  = "\n\n".join(f"{w.name}: {r}" for w, r in zip(self.workers, results))
        # Claude に集約を任せる
        return await ask(
            self.sys,
            f"▼ WORKER 回答\n{joined}\n▲ 上記を統合し 1 つの回答を返せ。"
        )


# ───── PRESIDENT ────────────────────────────────────────────────────────
class President:
    """ユーザー要求をサブタスクに分割し BOSS に投げる経営層"""

    def __init__(self, boss: Boss) -> None:
        self.boss = boss
        self.sys  = "PRESIDENT: 要求を 3〜5 のサブタスクに分割し、結果をまとめて返せ。"

    async def run(self, request: str) -> str:
        # 1. 要求を JSON array へ分解
        subtasks_json = await ask(
            self.sys,
            f"{request}\n---\nJSON array で 3〜5 個に分割して出力せよ。"
        )
        subtasks = json.loads(subtasks_json)

        # 2. 各タスクを BOSS へ依頼
        reports = [await self.boss.run(t) for t in subtasks]
        return "\n\n".join(reports)


# ───── CLI 実行用 ────────────────────────────────────────────────────────
async def main() -> None:
    workers   = [Worker(f"WORKER{i}") for i in range(1, 4)]
    boss      = Boss(workers)
    president = President(boss)

    query = "不動産購入チェックリストを評価し、問題点と改善案を表形式でまとめて"
    final = await president.run(query)
    print(final)


if __name__ == "__main__":
    asyncio.run(main())
