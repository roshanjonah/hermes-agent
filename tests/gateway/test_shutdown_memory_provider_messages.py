"""Regression tests for #15165 — gateway session shutdown must invoke the
agent-owned memory shutdown path so providers see the real messages instead
of an empty list.

Before the fix, no-arg ``AIAgent.shutdown_memory_provider()`` invoked
``on_session_end([])`` on every memory provider. Providers with
an empty-guard (Holographic, Hindsight, etc.) exited early and never
persisted the session's facts, so the next gateway start-up surfaced no
memories from the prior conversation.

The fix is that ``AIAgent.shutdown_memory_provider()`` owns the default
transcript lookup. Gateway only calls the public cleanup method.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_dotenv(monkeypatch):
    """gateway.run imports dotenv at module load; stub so tests run bare."""
    fake = types.ModuleType("dotenv")
    fake.load_dotenv = lambda *a, **kw: None
    monkeypatch.setitem(sys.modules, "dotenv", fake)


def _make_runner():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    return runner


# A lightweight stand-in for AIAgent so ``isinstance(..., list)`` correctly
# discriminates between "attribute set to a list" and "attribute absent /
# MagicMock auto-synthesised". Using MagicMock directly for the agent
# would also work for the populated case, but attribute access on a
# MagicMock always yields a child MagicMock — we want a real Python
# object we can shape per-test.
class _FakeAgent:
    def __init__(self, session_messages=None, has_shutdown=True):
        if session_messages is not None:
            self._session_messages = session_messages
        if has_shutdown:
            self.shutdown_memory_provider = MagicMock()
        self.close = MagicMock()


class TestCleanupAgentResourcesInvokesShutdown:
    """_cleanup_agent_resources invokes the agent cleanup contract."""

    def test_agent_with_messages_uses_public_shutdown(self):
        """Real-world path: an agent that ran a turn is cleaned up through
        the public shutdown method."""
        runner = _make_runner()
        transcript = [
            {"role": "user", "content": "remember my dog is named Biscuit"},
            {"role": "assistant", "content": "Got it — Biscuit."},
        ]
        agent = _FakeAgent(session_messages=transcript)

        runner._cleanup_agent_resources(agent)

        agent.shutdown_memory_provider.assert_called_once_with()

    def test_empty_session_uses_public_shutdown(self):
        """An agent that initialised but ran no turns still uses the same
        public shutdown method."""
        runner = _make_runner()
        agent = _FakeAgent(session_messages=[])

        runner._cleanup_agent_resources(agent)

        agent.shutdown_memory_provider.assert_called_once_with()

    def test_missing_attribute_uses_public_shutdown(self):
        """Partial test stubs without session state still shut down cleanly."""
        runner = _make_runner()
        agent = _FakeAgent(session_messages=None)  # attribute not set

        runner._cleanup_agent_resources(agent)

        agent.shutdown_memory_provider.assert_called_once_with()

    def test_mock_agent_uses_public_shutdown(self):
        """MagicMock agents should be cleaned up without inspecting private
        transcript attributes."""
        runner = _make_runner()
        agent = MagicMock()
        # No explicit _session_messages assignment — MagicMock will
        # synthesise one on access.

        runner._cleanup_agent_resources(agent)

        agent.shutdown_memory_provider.assert_called_once_with()

    def test_provider_exception_is_swallowed(self):
        """Provider teardown must be best-effort — a raising
        ``shutdown_memory_provider`` must not prevent ``close()`` from
        running (tool resource leak is worse than a missed memory
        flush)."""
        runner = _make_runner()
        agent = _FakeAgent(session_messages=[{"role": "user", "content": "x"}])
        agent.shutdown_memory_provider.side_effect = RuntimeError("boom")

        # Must not raise.
        runner._cleanup_agent_resources(agent)

        # close() still invoked after the swallowed exception.
        agent.close.assert_called_once()

    def test_none_agent_is_noop(self):
        """Defensive: None agent short-circuits (idle sweeps may
        observe a None entry in the cache during eviction races)."""
        runner = _make_runner()
        # Must not raise.
        runner._cleanup_agent_resources(None)

    def test_agent_without_shutdown_method_is_tolerated(self):
        """An agent without ``shutdown_memory_provider`` (old test
        stub, partial mock) must still have ``close()`` called."""
        runner = _make_runner()
        agent = _FakeAgent(has_shutdown=False)
        # No _session_messages either, to exercise the hasattr guard.

        runner._cleanup_agent_resources(agent)

        agent.close.assert_called_once()
