"""Prebid Release Analysis Agent - Specialized for Prebid repositories."""

import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

from agents_playground.github_release_agent import GitHubReleaseAgent, AgentConfig

load_dotenv()


class PrebidReleaseAgent(GitHubReleaseAgent):
    """Specialized agent for analyzing Prebid repository releases."""
    
    PREBID_REPOS = {
        "js": "prebid/Prebid.js",
        "server": "prebid/prebid-server", 
        "server-java": "prebid/prebid-server-java",
        "ios": "prebid/prebid-mobile-ios",
        "android": "prebid/prebid-mobile-android"
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or AgentConfig(
            name="PrebidReleaseAnalyzer",
            model="gemini-2.0-flash-exp",
            temperature=0.3
        ))
    
    def respond(self, message: str) -> str:
        """Enhanced interface for Prebid repositories with shortcuts and latest tag support."""
        try:
            repo_name, release_tag = self._parse_prebid_input(message)
            analysis = self.analyze_release(repo_name, release_tag)
            return self._format_analysis_response(analysis)
            
        except Exception as e:
            return f"Error analyzing Prebid release: {str(e)}"
    
    def _parse_prebid_input(self, message: str) -> tuple[str, str]:
        """Parse Prebid-specific input formats."""
        message = message.strip()
        
        # Handle Prebid shortcuts
        if message in self.PREBID_REPOS:
            # Just repo shortcut - get latest release
            repo_name = self.PREBID_REPOS[message]
            release_tag = self._get_latest_release_tag(repo_name)
            return repo_name, release_tag
        
        # Handle shortcut with tag (e.g., "js:v8.0.0" or "server v3.18.0")
        for separator in [":", " "]:
            if separator in message:
                parts = message.split(separator, 1)
                if len(parts) == 2:
                    shortcut, tag = parts[0].strip(), parts[1].strip()
                    if shortcut in self.PREBID_REPOS:
                        repo_name = self.PREBID_REPOS[shortcut]
                        return repo_name, tag
        
        # Fall back to parent parsing for URLs and full repo names
        return super()._parse_input(message)
    
    def _get_latest_release_tag(self, repo_name: str) -> str:
        """Get the latest release tag for a repository."""
        try:
            repo = self.github.get_repo(repo_name)
            latest_release = repo.get_latest_release()
            return latest_release.tag_name
        except Exception as e:
            raise ValueError(f"Could not get latest release for {repo_name}: {str(e)}")
    
    def list_prebid_repos(self) -> str:
        """List available Prebid repository shortcuts."""
        result = "🏗️ **Available Prebid Repository Shortcuts:**\n\n"
        
        for shortcut, repo in self.PREBID_REPOS.items():
            try:
                latest_tag = self._get_latest_release_tag(repo)
                result += f"- **{shortcut}**: {repo} (latest: {latest_tag})\n"
            except Exception:
                result += f"- **{shortcut}**: {repo} (latest: unknown)\n"
        
        result += "\n**Usage Examples:**\n"
        result += "- `js` - Analyze latest Prebid.js release\n"
        result += "- `server:v3.18.0` - Analyze specific prebid-server release\n"
        result += "- `ios v2.1.0` - Analyze specific iOS release\n"
        
        return result
    
    def analyze_latest(self, repo_shortcut: str) -> str:
        """Analyze the latest release of a Prebid repository."""
        if repo_shortcut not in self.PREBID_REPOS:
            available = ", ".join(self.PREBID_REPOS.keys())
            return f"Unknown repository shortcut '{repo_shortcut}'. Available: {available}"
        
        return self.respond(repo_shortcut)
    
    def compare_releases(self, repo_shortcut: str, tag1: str, tag2: str) -> str:
        """Compare two releases of the same Prebid repository."""
        if repo_shortcut not in self.PREBID_REPOS:
            available = ", ".join(self.PREBID_REPOS.keys())
            return f"Unknown repository shortcut '{repo_shortcut}'. Available: {available}"
        
        try:
            analysis1 = self.analyze_release(self.PREBID_REPOS[repo_shortcut], tag1)
            analysis2 = self.analyze_release(self.PREBID_REPOS[repo_shortcut], tag2)
            
            return self._format_comparison(analysis1, analysis2)
            
        except Exception as e:
            return f"Error comparing releases: {str(e)}"
    
    def _format_comparison(self, analysis1, analysis2) -> str:
        """Format a comparison between two releases."""
        result = f"""
🔄 **Release Comparison: {analysis1.repo_name}**

📊 **{analysis1.release_tag} vs {analysis2.release_tag}**

**Stats Comparison:**
- PRs: {analysis1.total_prs} vs {analysis2.total_prs} ({analysis2.total_prs - analysis1.total_prs:+d})
- Categories: {len(analysis1.categories)} vs {len(analysis2.categories)}

**{analysis1.release_tag} Categories:**
"""
        for category, prs in analysis1.categories.items():
            result += f"- {category}: {len(prs)} PRs\n"
        
        result += f"\n**{analysis2.release_tag} Categories:**\n"
        for category, prs in analysis2.categories.items():
            result += f"- {category}: {len(prs)} PRs\n"
        
        return result


# Convenience functions for direct usage
def analyze_prebid_latest(repo_shortcut: str) -> str:
    """Quick function to analyze latest release of a Prebid repo."""
    agent = PrebidReleaseAgent()
    return agent.analyze_latest(repo_shortcut)


def list_prebid_repos() -> str:
    """Quick function to list available Prebid repositories."""
    agent = PrebidReleaseAgent()
    return agent.list_prebid_repos()


def analyze_prebid_release(repo_shortcut: str, tag: str = None) -> str:
    """Quick function to analyze a Prebid release."""
    agent = PrebidReleaseAgent()
    if tag:
        return agent.respond(f"{repo_shortcut}:{tag}")
    else:
        return agent.respond(repo_shortcut)