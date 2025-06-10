import pytest, asyncio
from agents.core import Worker, Boss

@pytest.mark.asyncio
async def test_worker_echo(monkeypatch):
    async def fake_ask(sys, msg): return "OK"
    monkeypatch.setattr("agents.core.ask", fake_ask)
    w = Worker("W1")
    assert await w.run("dummy") == "OK"

@pytest.mark.asyncio
async def test_boss_aggregates(monkeypatch):
    async def fake_ask(sys, msg): return "SUM"
    monkeypatch.setattr("agents.core.ask", fake_ask)
    boss = Boss([Worker("W1"), Worker("W2")])
    result = await boss.run("task")
    assert result == "SUM"
