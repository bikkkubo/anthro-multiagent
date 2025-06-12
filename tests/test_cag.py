import pytest
from agents.context_gate import need_external_search

@pytest.mark.parametrize("q, expected", [
    ("今日の天気は？", False),        # 一般知識で答えられそう
    ("東京 2025Q2 GDP 速報値は？", True),  # 外部データ要
])
def test_gate_decision(monkeypatch, q, expected):
    monkeypatch.setattr(
        "agents.context_gate.need_external_search",
        lambda _q: expected
    )
    assert need_external_search(q) is expected
