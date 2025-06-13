# 📊 GitHub Release Analysis Agent Examples

This directory contains examples and documentation for using the GitHub Release Analysis Agent - a powerful tool that analyzes GitHub repository releases, extracts all pull requests included in the release, and generates comprehensive AI-powered summaries.

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup**: Make sure you have your GitHub token configured in `.env`:
```bash
GITHUB_TOKEN=your_github_personal_access_token
GOOGLE_API_KEY=your_gemini_api_key  # For AI summaries
```

2. **Install Dependencies**: All required packages should already be installed via `uv sync`

### Basic Usage

```python
from agents_playground.github_release_agent import GitHubReleaseAgent

# Initialize the agent
agent = GitHubReleaseAgent()

# Analyze a release (format: "owner/repo:release_tag")
analysis = agent.respond("microsoft/vscode:1.80.0")
print(analysis)
```

## 📋 Available Examples

### 1. Interactive Demo (`release_analysis_demo.py`)

**What it does**: Provides multiple ways to interact with the release analysis agent

**How to run**:
```bash
cd agents-playground
uv run python examples/release_analysis_demo.py
```

**Features**:
- **Guided Demo**: Choose from popular repositories with known releases
- **Quick Demo**: Fast analysis of a sample repository  
- **Interactive Mode**: Analyze any repository/release combination

**Example interaction**:
```
🚀 GitHub Release Analysis Agent Demo

Select a repository and release to analyze:
1. microsoft/vscode - 1.80.0
2. facebook/react - v18.2.0
3. nodejs/node - v20.0.0
4. python/cpython - v3.11.0
5. Enter custom repo:tag

Enter your choice (1-5): 1

🔍 Analyzing microsoft/vscode release 1.80.0...
```

### 2. Programmatic Usage Examples

#### Simple Analysis
```python
from agents_playground.github_release_agent import GitHubReleaseAgent

agent = GitHubReleaseAgent()

# Basic analysis
result = agent.respond("facebook/react:v18.2.0")
print(result)
```

#### Detailed Analysis Object
```python
from agents_playground.github_release_agent import analyze_github_release

# Get the full analysis object
analysis = analyze_github_release("nodejs/node", "v20.0.0")

print(f"Repository: {analysis.repo_name}")
print(f"Release: {analysis.release_tag}")
print(f"Total PRs: {analysis.total_prs}")
print(f"Categories: {list(analysis.categories.keys())}")

# Access individual PRs
for category, prs in analysis.categories.items():
    print(f"\n{category} ({len(prs)} PRs):")
    for pr in prs[:3]:  # Show first 3 PRs
        print(f"  - #{pr.number}: {pr.title} by @{pr.author}")
```

#### Quick Summary
```python
from agents_playground.github_release_agent import quick_release_summary

# Get formatted summary string
summary = quick_release_summary("microsoft/typescript", "v5.0.0")
print(summary)
```

## 🔧 Advanced Usage

### Custom Configuration

```python
from agents_playground.github_release_agent import GitHubReleaseAgent
from agents_playground.agents import AgentConfig

# Custom configuration for more creative summaries
config = AgentConfig(
    name="DetailedAnalyzer",
    model="gemini-2.0-flash-exp",
    temperature=0.1,  # More deterministic
    max_tokens=2000   # Longer summaries
)

agent = GitHubReleaseAgent(config)
analysis = agent.respond("kubernetes/kubernetes:v1.28.0")
```

### Batch Analysis

```python
from agents_playground.github_release_agent import GitHubReleaseAgent

agent = GitHubReleaseAgent()

# Analyze multiple releases
repos_and_tags = [
    ("microsoft/vscode", "1.80.0"),
    ("facebook/react", "v18.2.0"),
    ("nodejs/node", "v20.0.0")
]

for repo, tag in repos_and_tags:
    print(f"\n{'='*50}")
    print(f"Analyzing {repo} - {tag}")
    print('='*50)
    
    try:
        result = agent.respond(f"{repo}:{tag}")
        print(result)
    except Exception as e:
        print(f"❌ Error analyzing {repo}:{tag} - {str(e)}")
```

### Error Handling

```python
from agents_playground.github_release_agent import GitHubReleaseAgent

agent = GitHubReleaseAgent()

def safe_analyze(repo_tag):
    """Safely analyze a release with error handling."""
    try:
        result = agent.respond(repo_tag)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Usage
result = safe_analyze("nonexistent/repo:v1.0.0")
if result["success"]:
    print(result["data"])
else:
    print(f"Analysis failed: {result['error']}")
```

## 📊 Understanding the Output

### Analysis Structure

The agent provides rich analysis data:

```python
analysis = analyze_github_release("repo/name", "v1.0.0")

# Basic info
analysis.repo_name          # "repo/name"  
analysis.release_tag        # "v1.0.0"
analysis.release_date       # datetime object
analysis.total_prs          # Total number of PRs

# Detailed PR data  
analysis.prs               # List of PRInfo objects
analysis.categories        # Dict of categorized PRs
analysis.summary           # AI-generated summary
```

### PR Categories

PRs are automatically categorized based on labels and titles:

- **Features**: New functionality, enhancements
- **Bug Fixes**: Bug fixes, patches, hotfixes  
- **Documentation**: Docs updates, README changes
- **Refactoring**: Code cleanup, style changes
- **Tests**: Test additions, test improvements
- **Dependencies**: Dependency updates, version bumps
- **Other**: Everything else

### PR Information

Each PR includes comprehensive metadata:

```python
pr = analysis.prs[0]
print(f"#{pr.number}: {pr.title}")
print(f"Author: @{pr.author}")
print(f"Labels: {pr.labels}")
print(f"URL: {pr.url}")
print(f"Stats: +{pr.additions}/-{pr.deletions} lines, {pr.changed_files} files")
```

## 🎯 Best Practices

### 1. Choose Appropriate Releases

- **Stable releases** work best (avoid pre-releases for cleaner results)
- **Recent releases** have better GitHub API data
- **Well-maintained repos** with good PR practices give better categorization

### 2. Handle Large Releases

For repositories with many PRs per release:

```python
# Use pagination-friendly approach
agent = GitHubReleaseAgent()

# Set longer timeout for large releases
import os
os.environ["REQUEST_TIMEOUT"] = "300"  # 5 minutes

result = agent.respond("kubernetes/kubernetes:v1.28.0")
```

### 3. API Rate Limiting

- The agent respects GitHub API rate limits
- With authentication: **5000 requests/hour**
- Monitor usage for batch operations

### 4. Error Scenarios

Common issues and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Release not found" | Invalid tag name | Check release tags on GitHub |
| "Repository not found" | Typo in repo name | Verify owner/repo format |
| "Bad credentials" | Invalid GitHub token | Check GITHUB_TOKEN in .env |
| "Rate limit exceeded" | Too many requests | Wait or use authenticated token |

## 🔍 Example Repositories to Try

Here are some repositories with interesting releases to analyze:

### Frontend Frameworks
- `facebook/react:v18.2.0` - Major React release
- `vuejs/vue:v3.3.0` - Vue.js updates
- `angular/angular:16.0.0` - Angular major version

### Backend & APIs  
- `nodejs/node:v20.0.0` - Node.js LTS release
- `microsoft/dotnet:v7.0.0` - .NET release
- `golang/go:go1.21.0` - Go language release

### Developer Tools
- `microsoft/vscode:1.80.0` - VS Code monthly release
- `microsoft/typescript:v5.0.0` - TypeScript major version
- `git/git:v2.41.0` - Git version control

### Large Projects
- `kubernetes/kubernetes:v1.28.0` - Container orchestration
- `elastic/elasticsearch:v8.8.0` - Search engine
- `apache/kafka:3.5.0` - Streaming platform

## 🐛 Troubleshooting

### Common Issues

1. **Module Import Errors**
```bash
# Make sure you're in the project directory
cd agents-playground
uv run python examples/release_analysis_demo.py
```

2. **API Authentication**
```bash
# Check your .env file has the token
cat .env | grep GITHUB_TOKEN
```

3. **Network Timeouts**
```python
# For large releases, increase timeout
import requests
requests.adapters.DEFAULT_TIMEOUT = 300
```

4. **Memory Issues with Large Releases**
```python
# Limit PR analysis for very large releases
# The agent automatically handles this, but you can monitor
```

### Getting Help

- **Check logs**: The agent prints progress messages
- **Verify permissions**: Ensure your GitHub token can access the repository
- **Test with small repos**: Start with smaller releases to verify setup
- **API limits**: Monitor GitHub API rate limit headers

## 🚀 Next Steps

Once you're comfortable with basic usage:

1. **Integrate with CI/CD**: Automate release analysis in your workflows
2. **Custom categorization**: Modify `_categorize_prs()` for your specific needs  
3. **Export capabilities**: Add PDF/HTML export functionality
4. **Webhook integration**: Trigger analysis on new releases automatically
5. **Multi-repo analysis**: Compare releases across related repositories

Happy analyzing! 🎉