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
| `server` | prebid/prebid-server | Go-based Prebid Server |
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
result = agent.respond("server")      # Latest prebid-server  
result = agent.respond("ios")         # Latest iOS SDK
```

### Analyze Specific Releases
```python
# Using colon format
result = agent.respond("server:v3.18.0")

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
- `server` → Latest prebid-server release
- `server:v3.18.0` → Specific prebid-server version
- `ios v3.0.2` → Specific iOS SDK version

### Advanced Usage
```python
# Compare releases
agent.compare_releases("server", "v3.17.0", "v3.18.0")

# Analyze latest
agent.analyze_latest("js")

# List repos with latest versions
agent.list_prebid_repos()
```

## 📊 Example Output
```
🚀 Release Analysis: prebid/prebid-server - v3.18.0

📊 Quick Stats:
- Total PRs: 18
- Release Date: 2025-06-05 19:27:05
- Categories: 4

📋 PR Breakdown:
**Features** (5 PRs):
- #4320: MobileFuse: Add usersync info (@dtbarne)
- #4201: New Adapter: Netaddiction - Admatic alias (@bakicam)
...

🤖 AI-Generated Summary:
This release focuses on expanding bidder coverage and improving 
existing adapter functionality...
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
   - Invalid shortcut → Use: js, server, server-java, ios, android
   - Release not found → Check the tag exists on GitHub