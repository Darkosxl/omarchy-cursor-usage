#!/usr/bin/python3
"""Run with python3 check.py; no third-party dependencies."""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "bin"
loader = importlib.machinery.SourceFileLoader("cursor_usage", str(ROOT / "omarchy-agent-usage-cursor"))
spec = importlib.util.spec_from_loader(loader.name, loader)
cursor = importlib.util.module_from_spec(spec)
loader.exec_module(cursor)

summary = {"individualUsage": {"plan": {"used": 131, "limit": 2000, "autoPercentUsed": 0.1511, "apiPercentUsed": 1.4, "totalPercentUsed": 0.2646}},
           "billingCycleEnd": "2026-10-13T08:15:23Z", "membershipType": "pro"}
values = cursor.limits(summary)
assert values[0]["title"] == "Included plan" and values[0]["percent"] == 131 / 2000
assert [w["percent"] for w in values[1:]] == [0.1511 / 100, 1.4 / 100]
for used in (0, 2000, 2500):
    assert cursor.limits({"individualUsage": {"plan": {"used": used, "limit": 2000}}})[0]["percent"] == used / 2000
for bad in (None, {}, {"individualUsage": None}, {"individualUsage": {"plan": []}},
            {"individualUsage": {"plan": {"apiPercentUsed": "nan"}}}):
    try:
        cursor.limits(bad if bad is not None else {})
        raise AssertionError("Malformed limits accepted")
    except cursor.UsageError:
        pass

now = datetime.now().astimezone()
def event(when, model="test-model"):
    return {"timestamp": str(int(when.timestamp() * 1000)), "model": model,
            "tokenUsage": {"inputTokens": 10, "outputTokens": 2, "cacheReadTokens": 20, "cacheWriteTokens": 3}}
stats = cursor.summarize([event(now), event(now - timedelta(days=1)), event(now - timedelta(days=9))], now.date())
assert stats["todayTotalTokens"] == 35
assert stats["recentDays"][-1]["messageCount"] == 35
assert sum(row["messageCount"] for row in stats["recentDays"]) == 70
assert sum(stats["modelUsage"]["test-model"].values()) == 105
assert len(cursor.summarize([], now.date())["recentDays"]) == 7

calls = []
def paged(cookie, path, body):
    calls.append(body["page"])
    return {"usageEventsDisplay": [event(now)], "totalUsageEventsCount": 2}
cursor.request = paged
assert len(cursor.events("", now)) == 2 and calls == [1, 2]

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    cursor.CACHE = home / "cache.json"
    cursor.session_cookie = lambda: "test"
    cursor.request = lambda *args: summary
    cursor.CACHE.write_text(json.dumps(dict(stats, id="cursor")))
    event_calls = []
    def fresh_events(*args):
        event_calls.append(True)
        return [event(now)]
    cursor.events = fresh_events
    result = cursor.collect(limits_only=True)
    assert result["ready"] and event_calls == [True] and result["todayTotalTokens"] == 35
    cursor.events = lambda *args: []
    assert cursor.collect(limits_only=True, force=True)["modelUsage"] == {}
    cursor.request = lambda *args: (_ for _ in ()).throw(cursor.UsageError("offline"))
    result = cursor.collect()
    assert result["usageStatusText"] == "Cursor usage unavailable" and result["modelUsage"] == stats["modelUsage"]
    cursor.CACHE.write_text("broken")
    assert cursor.collect()["ready"] is False

    # Exercise the real wrapper with isolated stand-in executables.
    bindir = home / "plugin/bin"
    stockdir = home / "stock/bin"
    bindir.mkdir(parents=True)
    stockdir.mkdir(parents=True)
    wrapper = bindir / "omarchy-agent-usage-update"
    wrapper.write_text((ROOT / "omarchy-agent-usage-update").read_text())
    collector = bindir / "omarchy-agent-usage-cursor"
    collector.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$HOME/cursor-args"\necho \'{"id":"cursor"}\'\n')
    collector.chmod(0o755)
    stock = stockdir / "omarchy-agent-usage-update"
    stock.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$HOME/stock-args"\nexit "${STOCK_EXIT:-0}"\n')
    stock.chmod(0o755)
    env = dict(os.environ, HOME=str(home), XDG_STATE_HOME=str(home / "state"), OMARCHY_PATH=str(home / "stock"))
    output = home / "state/omarchy/agents/usage/cursor.json"
    for args, wanted in (([], True), (["--force"], True), (["--limits-only", "cursor"], True),
                         (["--except", "cursor"], False), (["codex"], False), (["--except", "claude"], True)):
        output.unlink(missing_ok=True)
        subprocess.run(["bash", str(wrapper), *args], env=env, check=True)
        assert output.exists() == wanted, args
        assert (home / "stock-args").read_text().strip().splitlines() == args
        if wanted:
            assert json.loads(output.read_text())["id"] == "cursor"
            assert (home / "cursor-args").read_text().strip().splitlines() == [a for a in args if a in ("--force", "--limits-only")]
    assert subprocess.run(["bash", str(wrapper), "codex"], env=dict(env, STOCK_EXIT="1")).returncode == 1
    output.write_text('{"id":"cursor","previous":true}')
    collector.write_text('#!/bin/bash\necho invalid\n')
    assert subprocess.run(["bash", str(wrapper), "cursor"], env=env).returncode == 1
    assert json.loads(output.read_text())["previous"] is True

print("PASS: limits, token totals, pagination, cache/failure handling and refresh flag routing")
