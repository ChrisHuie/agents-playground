# 🤖 Agents Playground

A comprehensive toolkit for experimenting with AI agents using Python. This project provides a structured foundation for building, testing, and deploying AI agents with support for multiple AI providers including OpenAI and Anthropic.

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Installation

1. **Clone and setup the project:**
```bash
git clone <your-repo-url>
cd agents-playground
```

2. **Install dependencies:**
```bash
uv sync
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run your first agent:**
```bash
uv run python -m agents_playground.main
```

## 📁 Project Structure

```
agents-playground/
├── src/agents_playground/          # Main package directory
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # Entry point and demo
│   ├── agents.py                   # Base agent classes
│   ├── examples/                   # Example agent implementations
│   └── utils/                      # Helper utilities
├── tests/                          # Test files
├── .env.example                    # Environment template
├── pyproject.toml                  # Project configuration
└── README.md                       # This file
```

### Key Components

- **`agents.py`**: Contains base classes and interfaces for all agents
- **`main.py`**: Entry point with demonstration code
- **`examples/`**: Ready-to-use agent implementations
- **`utils/`**: Shared utilities and helpers

## 🎯 Creating Your First Agent

### Step 1: Basic Agent Structure

Every agent inherits from the `BaseAgent` class:

```python
from agents_playground.agents import BaseAgent, AgentConfig

class MyFirstAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig(name="MyFirstAgent")
    
    def respond(self, message: str) -> str:
        return f"Echo: {message}"
```

### Step 2: Using AI Models

Here's how to create an agent that uses OpenAI:

```python
import os
from openai import OpenAI
from agents_playground.agents import BaseAgent, AgentConfig

class OpenAIAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def respond(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": message}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content
```

### Step 3: Running Your Agent

```python
# Create and run your agent
agent = OpenAIAgent(AgentConfig(
    name="ChatBot",
    model="gpt-3.5-turbo",
    temperature=0.7
))

response = agent.respond("Hello, how are you?")
print(f"Agent: {response}")
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
# Required for OpenAI agents
OPENAI_API_KEY=your_openai_api_key_here

# Required for Anthropic agents  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional configurations
DEFAULT_MODEL=gpt-3.5-turbo
TEMPERATURE=0.7
MAX_TOKENS=1000
```

### Agent Configuration

Use the `AgentConfig` class to customize your agents:

```python
from agents_playground.agents import AgentConfig

config = AgentConfig(
    name="MySpecialAgent",
    model="gpt-4",
    temperature=0.3,  # More deterministic responses
    max_tokens=500    # Shorter responses
)
```

## 📚 Agent Examples

### 1. Simple Echo Agent

```python
from agents_playground.agents import BaseAgent

class EchoAgent(BaseAgent):
    def respond(self, message: str) -> str:
        return f"You said: {message}"

# Usage
agent = EchoAgent()
print(agent.respond("Hello!"))  # Output: You said: Hello!
```

### 2. OpenAI Chat Agent

```python
import os
from openai import OpenAI
from agents_playground.agents import BaseAgent, AgentConfig

class ChatAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = []
    
    def respond(self, message: str) -> str:
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Get AI response
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.conversation_history,
            temperature=self.config.temperature
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to history
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []

# Usage
agent = ChatAgent(AgentConfig(name="ChatBot", temperature=0.8))
print(agent.respond("What's the weather like?"))
print(agent.respond("What about tomorrow?"))  # Maintains context
```

### 3. Anthropic Claude Agent

```python
import os
from anthropic import Anthropic
from agents_playground.agents import BaseAgent, AgentConfig

class ClaudeAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig(model="claude-3-sonnet-20240229")
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def respond(self, message: str) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens or 1000,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

# Usage  
agent = ClaudeAgent(AgentConfig(name="Claude"))
print(agent.respond("Explain quantum computing in simple terms"))
```

### 4. Specialized Task Agent

```python
import os
from openai import OpenAI
from agents_playground.agents import BaseAgent, AgentConfig

class CodeReviewAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig(name="CodeReviewer")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """You are an expert code reviewer. 
        Analyze the provided code and give constructive feedback on:
        - Code quality and style
        - Potential bugs or issues  
        - Performance improvements
        - Best practices"""
    
    def respond(self, code: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Please review this code:\n\n```\n{code}\n```"}
            ],
            temperature=0.3  # More deterministic for code review
        )
        return response.choices[0].message.content

# Usage
agent = CodeReviewAgent()
code_to_review = """
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total
"""
print(agent.respond(code_to_review))
```

### 5. Multi-Model Agent

```python
import os
from openai import OpenAI
from anthropic import Anthropic
from agents_playground.agents import BaseAgent, AgentConfig

class MultiModelAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def respond(self, message: str, provider: str = "openai") -> str:
        if provider.lower() == "openai":
            return self._openai_response(message)
        elif provider.lower() == "anthropic":
            return self._anthropic_response(message)
        else:
            raise ValueError("Provider must be 'openai' or 'anthropic'")
    
    def _openai_response(self, message: str) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content
    
    def _anthropic_response(self, message: str) -> str:
        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text
    
    def compare_responses(self, message: str) -> dict:
        """Get responses from both providers for comparison"""
        return {
            "openai": self.respond(message, "openai"),
            "anthropic": self.respond(message, "anthropic")
        }

# Usage
agent = MultiModelAgent()
responses = agent.compare_responses("What is artificial intelligence?")
print("OpenAI Response:", responses["openai"])
print("Anthropic Response:", responses["anthropic"])
```

## 🛠️ Advanced Usage

### LangChain Integration

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from agents_playground.agents import BaseAgent, AgentConfig

class LangChainAgent(BaseAgent):
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.llm = ChatOpenAI(
            model_name=self.config.model,
            temperature=self.config.temperature
        )
    
    def respond(self, message: str) -> str:
        response = self.llm([HumanMessage(content=message)])
        return response.content
```

### FastAPI Web Service

```python
from fastapi import FastAPI
from pydantic import BaseModel
from agents_playground.agents import OpenAIAgent, AgentConfig

app = FastAPI(title="Agents Playground API")

class ChatRequest(BaseModel):
    message: str
    agent_name: str = "default"

class ChatResponse(BaseModel):
    response: str
    agent_name: str

# Initialize agents
agents = {
    "default": OpenAIAgent(AgentConfig(name="DefaultBot")),
    "creative": OpenAIAgent(AgentConfig(name="CreativeBot", temperature=0.9)),
    "precise": OpenAIAgent(AgentConfig(name="PreciseBot", temperature=0.1))
}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent = agents.get(request.agent_name, agents["default"])
    response = agent.respond(request.message)
    return ChatResponse(response=response, agent_name=request.agent_name)

# Run with: uvicorn agents_playground.api:app --reload
```

## 🧪 Testing

Run tests with:

```bash
uv run pytest
```

Create test files in the `tests/` directory:

```python
# tests/test_agents.py
import pytest
from agents_playground.agents import SimpleAgent, AgentConfig

def test_simple_agent():
    agent = SimpleAgent()
    response = agent.respond("test message")
    assert "test message" in response
    assert "Agent" in response

def test_agent_config():
    config = AgentConfig(name="TestBot", temperature=0.5)
    agent = SimpleAgent(config)
    response = agent.respond("hello")
    assert "TestBot" in response
```

## 📦 Development

### Adding New Dependencies

```bash
# Add runtime dependencies
uv add package-name

# Add development dependencies  
uv add --dev package-name
```

### Code Quality

Run code formatting and linting:

```bash
# Format code
uv run black src/

# Sort imports
uv run isort src/

# Lint code
uv run flake8 src/

# Type checking
uv run mypy src/
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Errors**: Make sure your `.env` file has the correct API keys
2. **Import Errors**: Ensure you're running commands with `uv run`
3. **Model Access**: Some models require special access or higher API tiers

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 License

This project is licensed under the ISC License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

Happy agent building! 🚀