# 🏗️ Prebid Release Analysis Agent

Step-by-step guide for analyzing Prebid repository releases with AI-powered summaries.

## 🚀 Quick Setup

### 1. Configure Environment
Make sure your `.env` file has:
```bash
GITHUB_TOKEN=your_github_personal_access_token
GOOGLE_API_KEY=your_gemini_api_key
```

### 2. Run the Demo
```bash
cd agents-playground
uv run python examples/prebid_demo.py
```

## 📊 Available Prebid Repositories

| Shortcut | Repository | Description |
|----------|------------|-------------|
| `js` | prebid/Prebid.js | JavaScript header bidding library |
| `server-go` | prebid/prebid-server | Go-based Prebid Server |
| `server-java` | prebid/prebid-server-java | Java-based Prebid Server |
| `ios` | prebid/prebid-mobile-ios | iOS mobile SDK |
| `android` | prebid/prebid-mobile-android | Android mobile SDK |

## 🎯 Usage Examples

### Analyze Latest Releases
```python
from agents_playground.prebid_agent import PrebidReleaseAgent

agent = PrebidReleaseAgent()

# Get latest release automatically
result = agent.respond("js")          # Latest Prebid.js
result = agent.respond("server-go")   # Latest prebid-server  
result = agent.respond("ios")         # Latest iOS SDK
```

### Analyze Specific Releases
```python
# Using colon format
result = agent.respond("server-go:v3.18.0")

# Using space format  
result = agent.respond("js 9.49.1")
result = agent.respond("android 3.0.2")
```

### List Available Repositories
```python
print(agent.list_prebid_repos())
```

## 📋 Step-by-Step Demo Instructions

### Option 1: Interactive Demo
1. Run: `uv run python examples/prebid_demo.py`
2. Choose option 1: "Interactive demo"
3. Select from the menu:
   - Option 1: Analyze latest release
   - Option 2: Analyze specific release
   - Option 3: Compare two releases
   - Option 4: Interactive mode

### Option 2: Direct Commands
```bash
# Quick examples
uv run python -c "
from agents_playground.prebid_agent import PrebidReleaseAgent
agent = PrebidReleaseAgent()

# Analyze latest Prebid.js
print(agent.respond('js'))
"
```

## 🔧 Command Reference

### Basic Commands
- `js` → Latest Prebid.js release
- `server-go` → Latest prebid-server release
- `server-go:v3.18.0` → Specific prebid-server version
- `ios v3.0.2` → Specific iOS SDK version

### Advanced Usage
```python
# Compare releases
agent.compare_releases("server-go", "v3.17.0", "v3.18.0")

# Analyze latest
agent.analyze_latest("js")

# List repos with latest versions
agent.list_prebid_repos()

# Multi-level summaries
agent.get_executive_summary("server-go:v3.18.0")    # High-level overview
agent.get_product_summary("server-go:v3.18.0")      # Business impact per PR
agent.get_developer_summary("server-go:v3.18.0")    # Technical details per PR
agent.get_all_summaries("server-go:v3.18.0")        # All 3 levels
```

## 📊 Multi-Level Summary Analysis

The agent provides 3 different analysis levels for different audiences:

### 📋 Executive Summary
- **Audience**: C-level, leadership, stakeholders
- **Focus**: Strategic overview, business impact, key highlights
- **Length**: Concise, 1-2 paragraphs
- **Content**: Overall release theme, major changes, impact assessment

### 🎯 Product Summary  
- **Audience**: Product managers, business analysts
- **Focus**: Individual PR business impact, feature analysis
- **Length**: Detailed, covers each PR individually
- **Content**: User impact, feature classification, roadmap implications

### ⚙️ Developer Summary
- **Audience**: Engineers, technical leads, architects
- **Focus**: Technical implementation details, code changes
- **Length**: Comprehensive technical analysis
- **Content**: Architecture changes, breaking changes, performance impact

### 📋 Demo Multi-Level Analysis
```bash
uv run python examples/multi_level_summary_demo.py
```

## 🐛 Troubleshooting

1. **Check environment**:
   ```bash
   cat .env | grep GITHUB_TOKEN
   ```

2. **Test connection**:
   ```bash
   uv run python -c "from agents_playground.prebid_agent import list_prebid_repos; print(list_prebid_repos())"
   ```

3. **Common issues**:
   - Missing GitHub token → Add `GITHUB_TOKEN` to `.env`
   - Invalid shortcut → Use: js, server-go, server-java, ios, android
   - Release not found → Check the tag exists on GitHub