from __future__ import annotations


class _MemoryManager:
    def __init__(self) -> None:
        self.messages = None
        self.shutdown_called = False

    def on_session_end(self, messages):
        self.messages = messages

    def shutdown_all(self):
        self.shutdown_called = True


def _bare_agent(memory_manager: _MemoryManager):
    from run_agent import AIAgent

    agent = AIAgent.__new__(AIAgent)
    agent._memory_manager = memory_manager
    agent.context_compressor = None
    agent.session_id = "test-session"
    return agent


def test_shutdown_memory_provider_defaults_to_session_messages():
    memory = _MemoryManager()
    agent = _bare_agent(memory)
    transcript = [{"role": "user", "content": "remember this"}]
    agent._session_messages = transcript

    agent.shutdown_memory_provider()

    assert memory.messages is transcript
    assert memory.shutdown_called is True


def test_shutdown_memory_provider_preserves_explicit_empty_list():
    memory = _MemoryManager()
    agent = _bare_agent(memory)
    agent._session_messages = [{"role": "user", "content": "ignored"}]
    messages = []

    agent.shutdown_memory_provider(messages)

    assert memory.messages is messages


def test_shutdown_memory_provider_missing_session_messages_uses_empty_list():
    memory = _MemoryManager()
    agent = _bare_agent(memory)

    agent.shutdown_memory_provider()

    assert memory.messages == []
