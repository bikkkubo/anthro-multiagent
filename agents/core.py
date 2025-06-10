# agents/core.py
import os, asyncio, json, textwrap
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-3-opus-2025-06-06"

async def ask(system: str, user_msg: str) -> str:
    """Claude 呼び出し（async）"""
    rsp = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return rsp.content[0].text.strip()

# ---- WORKER ----
class Worker:
    def __init__(self, name: str): self.name, self.sys = name, f"{name} は実務担当。簡潔に答えよ。"
    async def run(self, task: str) -> str: return await ask(self.sys, task)

# ---- BOSS ----
class Boss:
    def __init__(self, workers): self.sys, self.workers = "BOSS: WORKERの回答を統合せよ。", workers
    async def run(self, task: str) -> str:
        results = await asyncio.gather(*(w.run(task) for w in self.workers))
        joined  = "\n\n".join(f"{w.name}: {r}" for w, r in zip(self.workers, results))
        return await ask(self.sys, f"▼\n{joined}\n▲ 上記を要約し1回答にまとめよ。")

# ---- PRESIDENT ----
class President:
    def __init__(self, boss): self.sys, self.boss = "PRESIDENT: 要求を分解しBOSSへ。", boss
    async def run(self, request: str) -> str:
        sub_json = await ask(self.sys, f"{request}\n---\nJSON array で 3~5 に分割せよ")
        subtasks = json.loads(sub_json)
        reports  = [await self.boss.run(t) for t in subtasks]
        return "\n\n".join(reports)

# ---- CLI 実行用 ----
async def main():
    workers = [Worker(f"WORKER{i}") for i in range(1, 4)]
    boss    = Boss(workers)
    prez    = President(boss)
    final   = await prez.run("不動産購入チェックリストを評価し問題点と改善案を表形式でまとめて")
    print(final)

if __name__ == "__main__":
    asyncio.run(main())
