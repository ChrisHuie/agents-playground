"""Tests for agent functionality."""

import pytest
from agents_playground.agents import SimpleAgent, AgentConfig


def test_simple_agent():
    """Test basic SimpleAgent functionality."""
    agent = SimpleAgent()
    response = agent.respond("test message")
    assert "test message" in response
    assert "Agent" in response


def test_agent_config():
    """Test agent configuration."""
    config = AgentConfig(name="TestBot", temperature=0.5)
    agent = SimpleAgent(config)
    response = agent.respond("hello")
    assert "TestBot" in response


def test_agent_config_defaults():
    """Test default agent configuration values."""
    config = AgentConfig()
    assert config.name == "Agent"
    assert config.model == "gpt-3.5-turbo"
    assert config.temperature == 0.7
    assert config.max_tokens is None