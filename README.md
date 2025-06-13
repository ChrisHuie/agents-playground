# 🤖 Agents Playground

A comprehensive toolkit for experimenting with AI agents using Python. This project provides a structured foundation for building, testing, and deploying AI agents with support for multiple AI providers including **Google Gemini 2.0 Flash**, OpenAI, and Anthropic.

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


## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
# Required for Google Gemini agents (default)
GOOGLE_API_KEY=your_google_api_key_here

# Required for OpenAI agents
OPENAI_API_KEY=your_openai_api_key_here

# Required for Anthropic agents  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional configurations
DEFAULT_MODEL=gemini-2.0-flash-exp
TEMPERATURE=0.7
MAX_TOKENS=1000
```

### Agent Configuration

Use the `AgentConfig` class to customize your agents:

```python
from agents_playground.agents import AgentConfig

config = AgentConfig(
    name="MySpecialAgent",
    model="gemini-2.0-flash-exp",
    temperature=0.3,  # More deterministic responses
    max_tokens=500,   # Shorter responses
    provider="gemini"
)
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