"""Base agent implementations."""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel


class BaseAgent(ABC):
    """Base class for all agents."""
    
    @abstractmethod
    def respond(self, message: str) -> str:
        """Generate a response to a message."""
        pass


class AgentConfig(BaseModel):
    """Configuration for agents."""
    name: str = "Agent"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class SimpleAgent(BaseAgent):
    """A simple demonstration agent."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
    
    def respond(self, message: str) -> str:
        """Generate a simple response."""
        return f"Hello! You said: '{message}'. I'm {self.config.name}!"