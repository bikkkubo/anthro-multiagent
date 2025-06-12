"""Context Awareness Gate: 外部検索の要否を LLM に判定させる。"""
from typing import Literal
import os, json, anthropic
from dotenv import load_dotenv

load_dotenv()
_CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_MODEL  = "claude-3-sonnet-20240229"   # 利用可能モデルへ

SYS_PROMPT = (
    "あなたは情報取り込みのゲート。与えられた質問に対し、"
    "『LLMの内部知識だけで十分か (NO_SEARCH)』『外部検索が必要か (SEARCH)』"
    "のいずれかを JSON で返してください。"
)

def need_external_search(question: str) -> Literal[True, False]:
    rsp = _CLIENT.messages.create(
        model=_MODEL,
        max_tokens=10,
        system=SYS_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    try:
        decision = json.loads(rsp.content[0].text.strip())
        return decision.upper() == "SEARCH"
    except Exception:
        # フォールバック：安全側で検索する
        return True
