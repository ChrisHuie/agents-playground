"""GitHub Release Analysis Agent - Analyzes PRs in releases and generates summaries."""

import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from dotenv import load_dotenv
from github import Github, Repository, PullRequest, GitCommit
from markdown import markdown
from lxml import html

from agents_playground.agents import BaseAgent, AgentConfig, GeminiAgent
from agents_playground.detectors import (
    NewAdaptersModulesDetector,
    TestingBuildDocsDetector,
    AdapterModuleChangesDetector,
    CoreChangesDetector,
    OtherDetector
)

load_dotenv()


@dataclass
class PRInfo:
    """Information about a Pull Request."""
    number: int
    title: str
    body: str
    author: str
    labels: List[str]
    merged_at: Optional[datetime]
    url: str
    commits_count: int
    additions: int
    deletions: int
    changed_files: int
    files: List[str] = None  # List of changed file paths


@dataclass
class ReleaseAnalysis:
    """Analysis results for a release."""
    repo_name: str
    release_tag: str
    release_date: Optional[datetime]
    total_prs: int
    prs: List[PRInfo]
    categories: Dict[str, List[PRInfo]]


class GitHubReleaseAgent(BaseAgent):
    """Agent that analyzes GitHub releases and generates PR summaries."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig(
            name="GitHubReleaseAnalyzer",
            model="gemini-2.0-flash-exp",
            temperature=0.3  # More consistent for analysis
        )
        
        # Initialize GitHub client
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        self.github = Github(github_token)
        
    
    def respond(self, message: str) -> str:
        """Main interface - accepts multiple input formats."""
        try:
            repo_name, release_tag = self._parse_input(message)
            analysis = self.analyze_release(repo_name, release_tag)
            return self._format_analysis_response(analysis)
            
        except Exception as e:
            return f"Error analyzing release: {str(e)}"
    
    def _parse_input(self, message: str) -> tuple[str, str]:
        """Parse different input formats to extract repo and tag."""
        message = message.strip()
        
        # Handle GitHub release URL format
        if "github.com" in message and "/releases/tag/" in message:
            # Extract from URL like: https://github.com/prebid/prebid-server/releases/tag/v3.18.0
            import re
            match = re.search(r'github\.com/([^/]+/[^/]+)/releases/tag/([^/?#]+)', message)
            if match:
                repo_name = match.group(1)
                release_tag = match.group(2)
                return repo_name, release_tag
            else:
                raise ValueError("Could not parse GitHub release URL")
        
        # Handle repo:tag format
        elif ":" in message:
            repo_name, release_tag = message.split(":", 1)
            return repo_name.strip(), release_tag.strip()
        
        # Handle space-separated format
        elif " " in message:
            parts = message.split()
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
            else:
                raise ValueError("Please provide repo and tag separated by space")
        
        else:
            raise ValueError("""
Please provide input in one of these formats:
- owner/repo:tag (e.g., 'prebid/prebid-server:v3.18.0')
- owner/repo tag (e.g., 'prebid/prebid-server v3.18.0') 
- GitHub URL (e.g., 'https://github.com/prebid/prebid-server/releases/tag/v3.18.0')
""")
    
    def analyze_release(self, repo_name: str, release_tag: str) -> ReleaseAnalysis:
        """Analyze a specific release and return comprehensive analysis."""
        try:
            repo = self.github.get_repo(repo_name)
            print(f"📊 Analyzing release {release_tag} for {repo_name}...")
            
            # Get release information
            release = repo.get_release(release_tag)
            release_date = release.created_at
            
            # Get commits between previous release and this release
            prs = self._get_prs_in_release(repo, release_tag)
            
            print(f"📋 Found {len(prs)} PRs in release {release_tag}")
            
            # Categorize PRs
            categories = self._categorize_prs(prs)
            
            return ReleaseAnalysis(
                repo_name=repo_name,
                release_tag=release_tag,
                release_date=release_date,
                total_prs=len(prs),
                prs=prs,
                categories=categories
            )
            
        except Exception as e:
            raise Exception(f"Failed to analyze release: {str(e)}")
    
    def _get_prs_in_release(self, repo: Repository, release_tag: str) -> List[PRInfo]:
        """Get all PRs included in a specific release."""
        prs = []
        
        try:
            # Get the release
            release = repo.get_release(release_tag)
            target_commitish = release.target_commitish or "main"
            
            # Get all releases to find the previous one
            releases = list(repo.get_releases())
            current_release_index = None
            
            for i, rel in enumerate(releases):
                if rel.tag_name == release_tag:
                    current_release_index = i
                    break
            
            if current_release_index is None:
                raise Exception(f"Release {release_tag} not found")
            
            # Get previous release for comparison
            previous_release = None
            if current_release_index < len(releases) - 1:
                previous_release = releases[current_release_index + 1]
            
            # Get commits between releases
            if previous_release:
                # Compare between previous release and current release
                comparison = repo.compare(previous_release.tag_name, release.tag_name)
                commits = list(comparison.commits)
            else:
                # If no previous release, get all commits up to this release
                commits = list(repo.get_commits(sha=target_commitish))[:50]  # Limit to recent commits
            
            print(f"🔍 Analyzing {len(commits)} commits...")
            
            # Find PRs associated with these commits
            pr_numbers = set()
            for commit in commits:
                # Look for PR references in commit messages
                pr_refs = self._extract_pr_numbers_from_commit(commit)
                pr_numbers.update(pr_refs)
            
            # Get detailed PR information
            for pr_number in pr_numbers:
                try:
                    pr = repo.get_pull(pr_number)
                    if pr.merged:
                        pr_info = self._extract_pr_info(pr)
                        prs.append(pr_info)
                except Exception as e:
                    print(f"⚠️  Could not fetch PR #{pr_number}: {e}")
                    continue
            
            return prs
            
        except Exception as e:
            raise Exception(f"Error getting PRs for release: {str(e)}")
    
    def _extract_pr_numbers_from_commit(self, commit: GitCommit) -> List[int]:
        """Extract PR numbers from commit messages."""
        import re
        
        pr_numbers = []
        message = commit.commit.message
        
        # Look for patterns like "Merge pull request #123" or "(#123)"
        patterns = [
            r'Merge pull request #(\d+)',
            r'\(#(\d+)\)',
            r'#(\d+)',
            r'PR #(\d+)',
            r'pull request #(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                pr_numbers.append(int(match))
        
        return list(set(pr_numbers))  # Remove duplicates
    
    def _extract_pr_info(self, pr: PullRequest) -> PRInfo:
        """Extract detailed information from a PR focusing on code changes."""
        # Get file changes and their diffs for code analysis
        files = []
        file_changes = {}  # Store file changes for content analysis
        try:
            pr_files = list(pr.get_files())
            files = [f.filename for f in pr_files]
            
            # Get file changes/diffs for code analysis
            for f in pr_files:
                file_changes[f.filename] = {
                    'status': f.status,  # 'added', 'modified', 'removed'
                    'additions': f.additions,
                    'deletions': f.deletions,
                    'patch': f.patch if hasattr(f, 'patch') else None
                }
        except Exception as e:
            print(f"⚠️  Could not fetch files for PR #{pr.number}: {e}")
            files = []
            file_changes = {}
        
        # Create PRInfo without reading PR body - focus on code only
        pr_info = PRInfo(
            number=pr.number,
            title=pr.title,
            body="",  # Don't read PR descriptions
            author=pr.user.login,
            labels=[label.name for label in pr.labels],
            merged_at=pr.merged_at,
            url=pr.html_url,
            commits_count=pr.commits,
            additions=pr.additions,
            deletions=pr.deletions,
            changed_files=pr.changed_files,
            files=files
        )
        
        # Add file changes as custom attribute for code analysis
        pr_info.file_changes = file_changes
        
        return pr_info
    
    def _categorize_prs(self, prs: List[PRInfo]) -> Dict[str, List[PRInfo]]:
        """Categorize PRs using modular detector system."""
        # Initialize detectors in priority order
        detectors = [
            NewAdaptersModulesDetector(),
            TestingBuildDocsDetector(),
            AdapterModuleChangesDetector(is_feature=True),   # Adapter & Module Features
            AdapterModuleChangesDetector(is_feature=False),  # Adapter & Module Updates
            CoreChangesDetector(is_feature=True),            # Core Features
            CoreChangesDetector(is_feature=False),           # Core Updates
            OtherDetector()  # Fallback
        ]
        
        categories = {}
        
        for pr in prs:
            categorized = False
            
            # Try each detector in priority order
            for detector in detectors:
                result = detector.detect(pr)
                if result.detected:
                    category_name = detector.get_category_name()
                    
                    if category_name not in categories:
                        categories[category_name] = []
                    
                    categories[category_name].append(pr)
                    
                    # Add detection metadata to PR for debugging/reporting
                    pr.detection_result = result
                    
                    categorized = True
                    break
            
            # Should never happen since OtherDetector always detects
            if not categorized:
                if "Other" not in categories:
                    categories["Other"] = []
                categories["Other"].append(pr)
        
        # Remove empty categories and return
        return {k: v for k, v in categories.items() if v}
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def _format_analysis_response(self, analysis: ReleaseAnalysis) -> str:
        """Format the analysis results for console display with detection details."""
        response = f"""
🚀 Release Analysis: {analysis.repo_name} - {analysis.release_tag}

📊 Quick Stats:
- Total PRs: {analysis.total_prs}
- Release Date: {analysis.release_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.release_date else 'Unknown'}
- Categories: {len(analysis.categories)}

📋 PR Breakdown:
"""
        
        for category, prs in analysis.categories.items():
            response += f"\n{category} ({len(prs)} PRs):\n"
            
            # Display PRs with detection details
            for pr in prs:
                pr_line = f"- #{pr.number}: {pr.title} (@{pr.author})"
                
                # Add detection metadata if available
                if hasattr(pr, 'detection_result') and pr.detection_result.metadata:
                    metadata = pr.detection_result.metadata
                    if 'type' in metadata:
                        pr_line += f" [{metadata['type']}]"
                    elif 'change_type' in metadata:
                        pr_line += f" [{metadata['change_type']}]"
                
                response += pr_line + "\n"
        
        # Add contributors section
        contributors = list(set(pr.author for pr in analysis.prs))
        if contributors:
            response += f"\n🙏 Contributors ({len(contributors)}):\n"
            response += f"{', '.join([f'@{contributor}' for contributor in sorted(contributors)])}\n"
        
        return response
# Convenience functions for direct usage
def analyze_github_release(repo_name: str, release_tag: str) -> ReleaseAnalysis:
    """Convenience function to analyze a GitHub release."""
    agent = GitHubReleaseAgent()
    return agent.analyze_release(repo_name, release_tag)


def quick_release_summary(repo_name: str, release_tag: str) -> str:
    """Quick function to get a formatted release summary."""
    agent = GitHubReleaseAgent()
    analysis = agent.analyze_release(repo_name, release_tag)
    return agent._format_analysis_response(analysis)