"""
Context Awareness Gate (CAG) — LLM に質問を丸ごと渡し、
「外部情報が要るか?」を Yes/No で返すユーティリティ。
最初はロジックを stub にしておき、後続コミットで実装 & テストを足す。
"""

from typing import Literal

def need_external_search(question: str) -> Literal[True, False]:
    """
    Return True if we should call retrieval (RAG/Hybrid etc.),
    False if the internal LLM knowledge is sufficient.

    TODO: implement with Anthropic API in a later step.
    """
    # --- stub: always call external search for now ---
    return True
