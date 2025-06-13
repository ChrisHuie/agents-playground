"""Base agent implementations."""

import os
from abc import ABC, abstractmethod
from typing import Optional

import google.generativeai as genai
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
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    provider: str = "gemini"  # gemini, openai, or anthropic


class GeminiAgent(BaseAgent):
    """Google Gemini 2.0 Flash agent implementation."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.config.model)
    
    def respond(self, message: str) -> str:
        """Generate a response using Gemini."""
        try:
            response = self.model.generate_content(
                message,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"


class SimpleAgent(BaseAgent):
    """A simple demonstration agent."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
    
    def respond(self, message: str) -> str:
        """Generate a simple response."""
        return f"Hello! You said: '{message}'. I'm {self.config.name}!"