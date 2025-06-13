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
    executive_summary: str
    product_summary: str
    developer_summary: str
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
        
        # Initialize Gemini for summary generation
        self.gemini_agent = GeminiAgent(self.config)
    
    def respond(self, message: str, summary_level: str = "executive") -> str:
        """Main interface - accepts multiple input formats."""
        try:
            repo_name, release_tag = self._parse_input(message)
            analysis = self.analyze_release(repo_name, release_tag)
            return self._format_analysis_response(analysis, summary_level)
            
        except Exception as e:
            return f"Error analyzing release: {str(e)}"
    
    def get_executive_summary(self, message: str) -> str:
        """Get executive-level summary only."""
        return self.respond(message, "executive")
    
    def get_product_summary(self, message: str) -> str:
        """Get product-level summary only."""
        return self.respond(message, "product")
    
    def get_developer_summary(self, message: str) -> str:
        """Get developer-level summary only."""
        return self.respond(message, "developer")
    
    def get_all_summaries(self, message: str) -> str:
        """Get all summary levels."""
        return self.respond(message, "all")
    
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
            
            # Generate AI summaries at different levels
            executive_summary = self._generate_executive_summary(repo_name, release_tag, prs, categories)
            product_summary = self._generate_product_summary(repo_name, release_tag, prs, categories)
            developer_summary = self._generate_developer_summary(repo_name, release_tag, prs, categories)
            
            return ReleaseAnalysis(
                repo_name=repo_name,
                release_tag=release_tag,
                release_date=release_date,
                total_prs=len(prs),
                prs=prs,
                executive_summary=executive_summary,
                product_summary=product_summary,
                developer_summary=developer_summary,
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
        """Extract detailed information from a PR."""
        # Get file changes for better categorization
        files = []
        try:
            pr_files = list(pr.get_files())
            files = [f.filename for f in pr_files]
        except Exception as e:
            print(f"⚠️  Could not fetch files for PR #{pr.number}: {e}")
            files = []
        
        return PRInfo(
            number=pr.number,
            title=pr.title,
            body=pr.body or "",
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
    
    def _categorize_prs(self, prs: List[PRInfo]) -> Dict[str, List[PRInfo]]:
        """Categorize PRs based on Prebid-specific patterns."""
        categories = {
            "New Adapters/Modules": [],
            "Core Features": [],
            "Core Updates": [],
            "Adapter/Module Features": [],
            "Adapter/Module Updates": [],
            "Testing/Build Process Updates": [],
            "Other": []
        }
        
        for pr in prs:
            categorized = False
            title_lower = pr.title.lower()
            body_lower = (pr.body or "").lower()
            
            # 1. New Adapters/Modules - Check for new adapter/module creation based on file structure
            if self._is_new_adapter_or_module(pr):
                categories["New Adapters/Modules"].append(pr)
                categorized = True
            
            # 2. Testing/Build Process Updates - Check early for test/build patterns
            elif any(pattern in title_lower for pattern in [
                "test", "testing", "spec", "ci", "workflow", "build",
                "github", "action", "pipeline", "lint", "format",
                "coverage", "benchmark", "validation", "integration"
            ]):
                categories["Testing/Build Process Updates"].append(pr)
                categorized = True
            
            # Check if it's an adapter/module change (contains adapter/bidder name patterns)
            elif self._is_adapter_or_module_change(pr):
                # 4. Adapter/Module Features
                if any(pattern in title_lower for pattern in [
                    "add", "implement", "support", "enable", "feat",
                    "feature", "new", "introduce"
                ]) and not any(pattern in title_lower for pattern in [
                    "fix", "bug", "resolve", "patch", "update", "maintenance"
                ]):
                    categories["Adapter/Module Features"].append(pr)
                    categorized = True
                # 5. Adapter/Module Updates (maintenance, bug fixes, documentation)
                else:
                    update_type = self._get_update_type(pr)
                    categories["Adapter/Module Updates"].append(pr)
                    # Add update type as metadata for better reporting
                    if not hasattr(pr, 'update_type'):
                        pr.update_type = update_type
                    categorized = True
            
            # Core changes (src/ and other critical files)
            elif self._is_core_change(pr):
                # 2. Core Features
                if any(pattern in title_lower for pattern in [
                    "add", "implement", "support", "enable", "feat",
                    "feature", "new", "introduce"
                ]) and not any(pattern in title_lower for pattern in [
                    "fix", "bug", "resolve", "patch", "update", "maintenance"
                ]):
                    categories["Core Features"].append(pr)
                    categorized = True
                # 3. Core Updates (bug fixes, maintenance, documentation)
                else:
                    update_type = self._get_update_type(pr)
                    categories["Core Updates"].append(pr)
                    # Add update type as metadata for better reporting
                    if not hasattr(pr, 'update_type'):
                        pr.update_type = update_type
                    categorized = True
            
            # Fallback categorization
            if not categorized:
                if any(pattern in title_lower for pattern in [
                    "add", "implement", "support", "enable", "feat", "feature"
                ]) and not any(pattern in title_lower for pattern in [
                    "fix", "bug", "resolve", "patch", "update", "maintenance"
                ]):
                    categories["Core Features"].append(pr)
                elif any(pattern in title_lower for pattern in [
                    "fix", "bug", "resolve", "patch", "update", "upgrade",
                    "refactor", "cleanup", "maintenance", "doc", "docs"
                ]):
                    update_type = self._get_update_type(pr)
                    categories["Core Updates"].append(pr)
                    if not hasattr(pr, 'update_type'):
                        pr.update_type = update_type
                else:
                    categories["Other"].append(pr)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _get_update_type(self, pr: PRInfo) -> str:
        """Determine the specific type of update (bugfix, maintenance, documentation, etc.)."""
        title_lower = pr.title.lower()
        body_lower = (pr.body or "").lower()
        
        # Check for security updates first (highest priority)
        if any(pattern in title_lower for pattern in [
            "security", "vulnerability", "cve", "secure"
        ]):
            return "security"
        
        # Check for performance improvements (before refactoring check)
        if any(pattern in title_lower for pattern in [
            "performance", "optimize", "speed", "faster", "efficiency",
            "perf", "latency", "throughput"
        ]) and not any(pattern in title_lower for pattern in [
            "refactor", "cleanup", "clean up", "reorganize", "restructure"
        ]):
            return "performance"
        
        # Check for bug fixes
        if any(pattern in title_lower for pattern in [
            "fix", "bug", "resolve", "patch", "hotfix", "issue"
        ]):
            return "bugfix"
        
        # Check for documentation
        if any(pattern in title_lower for pattern in [
            "doc", "docs", "documentation", "readme", "comment", "javadoc"
        ]):
            return "documentation"
        
        # Check for dependency updates
        if any(pattern in title_lower for pattern in [
            "bump", "upgrade", "dependency", "deps", "version", "update"
        ]) and any(pattern in title_lower for pattern in [
            "to", "from", "v", "version", "bump"
        ]):
            return "dependency update"
        
        # Check for configuration changes
        if any(pattern in title_lower for pattern in [
            "config", "configuration", "setting", "parameter", "option"
        ]):
            return "configuration"
        
        # Check for refactoring/cleanup
        if any(pattern in title_lower for pattern in [
            "refactor", "cleanup", "clean up", "reorganize", "restructure",
            "improve", "simplify"
        ]):
            return "refactoring"
        
        # Check for maintenance tasks
        if any(pattern in title_lower for pattern in [
            "maintenance", "chore", "misc", "general", "housekeeping",
            "routine", "update", "upgrade"
        ]):
            return "maintenance"
        
        # Default to maintenance
        return "maintenance"
    
    def _is_new_adapter_or_module(self, pr: PRInfo) -> bool:
        """Check if PR introduces a new adapter or module based on file structure."""
        if not pr.files:
            return False
        
        new_module_patterns = [
            # New bid adapters
            r'modules/[^/]+BidAdapter\.js$',
            # New analytics adapters  
            r'modules/[^/]+AnalyticsAdapter\.js$',
            # New RTD providers
            r'modules/[^/]+RtdProvider\.js$',
            # New user ID systems
            r'modules/[^/]+IdSystem\.js$',
            # New general modules (but exclude existing known modules)
            r'modules/[^/]+\.js$'
        ]
        
        import re
        
        # Check for new module files being added
        new_modules = set()  # Use set to avoid duplicates
        for file_path in pr.files:
            for pattern in new_module_patterns:
                if re.match(pattern, file_path):
                    # Extract module name from path
                    module_name = file_path.split('/')[-1].replace('.js', '')
                    new_modules.add(module_name)
        
        new_modules = list(new_modules)  # Convert back to list
        
        if not new_modules:
            return False
        
        # Additional validation: check if this looks like a new module introduction
        # Look for patterns that indicate this is adding a NEW module, not modifying existing
        for module_name in new_modules:
            # Check for corresponding documentation file
            doc_files = [f for f in pr.files if f.endswith(f'{module_name}.md')]
            # Check for corresponding test file
            test_files = [f for f in pr.files if module_name.lower() in f.lower() and '_spec.js' in f]
            
            # If we have the main module file and either docs or tests, likely a new module
            if doc_files or test_files:
                return True
            
            # Also check for title patterns that suggest new modules
            title_lower = pr.title.lower()
            if any(pattern in title_lower for pattern in [
                "initial release", "new adapter", "new bidder", "new module",
                "add adapter", "add bidder", "add module"
            ]):
                return True
        
        # For single module file changes, be more strict
        if len(new_modules) == 1:
            title_lower = pr.title.lower()
            
            # First check if title suggests it's NOT a new module
            if any(pattern in title_lower for pattern in [
                "fix", "bug", "update", "improve", "refactor", "patch",
                "enhance", "optimize", "cleanup", "maintain", "adjust"
            ]):
                return False
            
            # Must have significant additions and minimal deletions for new modules
            if pr.additions > 100 and pr.deletions < 20:
                # Check if title suggests it's new
                if any(pattern in title_lower for pattern in [
                    "initial release", "new adapter", "new bidder", "new module",
                    "add adapter", "add bidder", "add module", ": initial"
                ]):
                    return True
            
            # If single module file but doesn't meet criteria, it's not new
            return False
        
        # For multiple module files, likely a new module
        elif len(new_modules) > 1 and pr.additions > pr.deletions * 2:
            return True
        
        return False
    
    def _is_adapter_or_module_change(self, pr: PRInfo) -> bool:
        """Check if PR is related to adapter or module changes."""
        title_lower = pr.title.lower()
        
        # Common adapter/bidder patterns
        adapter_patterns = [
            # Direct adapter mentions
            "adapter", "bidder", "module",
            # Common adapter names (partial list - can be expanded)
            "appnexus", "rubicon", "pubmatic", "openx", "sovrn",
            "sharethrough", "criteo", "amazon", "facebook", "google",
            "smaato", "mobilefuse", "conversant", "ix", "yieldmo",
            "adform", "mejla", "smartadserver", "telaria", "unruly",
            "outbrain", "taboola", "brightcom", "consumable", "emxdigital",
            "gamoshi", "gumgum", "kargo", "lifestreet", "lockerdome",
            "marsmedia", "mgid", "nanointeractive", "oftmedia", "pulsepoint",
            "rhythmone", "sekindo", "vertamedia", "videobyte", "viewdeos",
            "adsystem", "adyoulike", "beintoo", "brightroll", "colossus",
            "concert", "copper6", "cpmstar", "deepintent", "dmx",
            "eplanning", "freewheel", "geniee", "gothamads", "grid",
            "huaweiads", "improvedigital", "inmobi", "justpremium", "kidoz",
            "kubient", "lkqd", "lunamedia", "madvertise", "mediafuse",
            "medianet", "mobfox", "nativeads", "nextmillennium", "nobid",
            "onetag", "openrtb", "orbidder", "phunware", "placementio",
            "pollux", "prebidorg", "projectagora", "pubwise", "quantumdx",
            "quicksand", "realtime", "resetdigital", "rich", "rtbhouse",
            "s2s", "silvermob", "sirdatartd", "smartrtb", "sonobi",
            "spotx", "stroeercore", "synacormedia", "tappx", "telaria",
            "triplelift", "trustedstack", "ucfunnel", "undertone", "valueimpression",
            "vdopia", "visx", "vox", "xandr", "yahoo", "yieldlab", "zeroclickfraud"
        ]
        
        return any(pattern in title_lower for pattern in adapter_patterns)
    
    def _is_core_change(self, pr: PRInfo) -> bool:
        """Check if PR affects core/critical files."""
        title_lower = pr.title.lower()
        body_lower = (pr.body or "").lower()
        
        # Core patterns that indicate changes to critical files
        core_patterns = [
            "src/", "core", "config", "server", "auction", "exchange",
            "cache", "currency", "gdpr", "ccpa", "privacy", "stored",
            "video", "native", "banner", "analytics", "metrics",
            "targeting", "floors", "deals", "pbs", "ortb", "openrtb",
            "host", "account", "endpoint", "handler", "processor",
            "validation", "timeout", "debug", "logging", "startup"
        ]
        
        # Check if it mentions core functionality
        return any(pattern in title_lower or pattern in body_lower for pattern in core_patterns)
    
    def _generate_executive_summary(self, repo_name: str, release_tag: str, prs: List[PRInfo], categories: Dict[str, List[PRInfo]]) -> str:
        """Generate an executive-level AI-powered summary of the release."""
        # Prepare context for Gemini
        context = f"""Analyze this GitHub release and create a comprehensive summary:

Repository: {repo_name}
Release Tag: {release_tag}
Total PRs: {len(prs)}

Categories and PRs:
"""
        
        for category, category_prs in categories.items():
            context += f"\n{category} ({len(category_prs)} PRs):\n"
            for pr in category_prs:
                context += f"- #{pr.number}: {pr.title} by @{pr.author}\n"
                if pr.body and len(pr.body) > 0:
                    # Take first 200 chars of description
                    body_preview = pr.body[:200].replace('\n', ' ').strip()
                    if len(pr.body) > 200:
                        body_preview += "..."
                    context += f"  Description: {body_preview}\n"
        
        # Add statistics
        total_additions = sum(pr.additions for pr in prs)
        total_deletions = sum(pr.deletions for pr in prs)
        total_files = sum(pr.changed_files for pr in prs)
        
        context += f"""
Statistics:
- Lines added: {total_additions:,}
- Lines deleted: {total_deletions:,}
- Files changed: {total_files:,}
- Contributors: {len(set(pr.author for pr in prs))}

Please create a well-structured release summary that includes:
1. Overview of the release
2. Key highlights and major changes
3. Breakdown by category
4. Impact assessment
5. Notable contributors

Make it professional but accessible, suitable for release notes."""
        
        try:
            summary = self.gemini_agent.respond(context)
            return summary
        except Exception as e:
            return f"Could not generate AI summary: {str(e)}\n\nBasic summary: This release includes {len(prs)} pull requests across {len(categories)} categories."
    
    def _generate_product_summary(self, repo_name: str, release_tag: str, prs: List[PRInfo], categories: Dict[str, List[PRInfo]]) -> str:
        """Generate a product-level summary with high-level analysis of each PR."""
        context = f"""Analyze this GitHub release from a PRODUCT MANAGER perspective and provide a detailed analysis of each pull request:

Repository: {repo_name}
Release Tag: {release_tag}
Total PRs: {len(prs)}

For each PR below, provide:
1. User/business impact
2. Feature classification (New Feature/Enhancement/Bug Fix/etc.)
3. Priority/importance level
4. Dependencies or related changes

PRs by Category:
"""
        
        for category, category_prs in categories.items():
            context += f"\n{category} ({len(category_prs)} PRs):\n"
            for pr in category_prs:
                context += f"\n#{pr.number}: {pr.title} by @{pr.author}\n"
                if pr.body and len(pr.body) > 0:
                    body_preview = pr.body[:300].replace('\n', ' ').strip()
                    if len(pr.body) > 300:
                        body_preview += "..."
                    context += f"Description: {body_preview}\n"
                context += f"Stats: +{pr.additions}/-{pr.deletions} lines, {pr.changed_files} files\n"
                if pr.labels:
                    context += f"Labels: {', '.join(pr.labels)}\n"

        context += f"""
Create a PRODUCT-FOCUSED summary that includes:
1. Individual PR analysis with business impact
2. User-facing changes and their significance
3. Feature roadmap implications
4. Risk assessment for each change
5. Dependencies between changes

Make it suitable for product managers and stakeholders who need to understand business impact."""

        try:
            summary = self.gemini_agent.respond(context)
            return summary
        except Exception as e:
            return f"Could not generate product summary: {str(e)}"
    
    def _generate_developer_summary(self, repo_name: str, release_tag: str, prs: List[PRInfo], categories: Dict[str, List[PRInfo]]) -> str:
        """Generate a developer-level summary with technical explanation of each PR."""
        context = f"""Analyze this GitHub release from a DEVELOPER/TECHNICAL perspective and provide detailed technical analysis of each pull request:

Repository: {repo_name}
Release Tag: {release_tag}
Total PRs: {len(prs)}

For each PR below, provide:
1. Technical implementation details
2. Architecture/design changes
3. Code complexity assessment
4. Potential breaking changes
5. Testing implications
6. Performance impact

PRs by Category:
"""
        
        for category, category_prs in categories.items():
            context += f"\n{category} ({len(category_prs)} PRs):\n"
            for pr in category_prs:
                context += f"\n#{pr.number}: {pr.title} by @{pr.author}\n"
                if pr.body and len(pr.body) > 0:
                    body_preview = pr.body[:500].replace('\n', ' ').strip()
                    if len(pr.body) > 500:
                        body_preview += "..."
                    context += f"Description: {body_preview}\n"
                context += f"Technical Stats: +{pr.additions}/-{pr.deletions} lines across {pr.changed_files} files\n"
                context += f"Commits: {pr.commits_count}\n"
                if pr.labels:
                    context += f"Labels: {', '.join(pr.labels)}\n"

        total_additions = sum(pr.additions for pr in prs)
        total_deletions = sum(pr.deletions for pr in prs)
        total_files = sum(pr.changed_files for pr in prs)
        
        context += f"""
Overall Technical Stats:
- Lines added: {total_additions:,}
- Lines deleted: {total_deletions:,}
- Files changed: {total_files:,}
- Contributors: {len(set(pr.author for pr in prs))}

Create a TECHNICAL summary that includes:
1. Individual PR technical analysis
2. Code architecture implications
3. Breaking changes and migration requirements
4. Performance and scalability impact
5. Testing and quality considerations
6. Integration complexity

Make it suitable for developers and technical leads who need to understand implementation details."""

        try:
            summary = self.gemini_agent.respond(context)
            return summary
        except Exception as e:
            return f"Could not generate developer summary: {str(e)}"
    
    def _format_analysis_response(self, analysis: ReleaseAnalysis, summary_level: str = "all") -> str:
        """Format the analysis results for display."""
        response = f"""
🚀 **Release Analysis: {analysis.repo_name} - {analysis.release_tag}**

📊 **Quick Stats:**
- Total PRs: {analysis.total_prs}
- Release Date: {analysis.release_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.release_date else 'Unknown'}
- Categories: {len(analysis.categories)}

📋 **PR Breakdown:**
"""
        
        for category, prs in analysis.categories.items():
            response += f"\n**{category}** ({len(prs)} PRs):\n"
            
            # Group updates by type for better clarity
            if "Updates" in category:
                update_types = {}
                for pr in prs:
                    update_type = getattr(pr, 'update_type', 'maintenance')
                    if update_type not in update_types:
                        update_types[update_type] = []
                    update_types[update_type].append(pr)
                
                for update_type, type_prs in update_types.items():
                    response += f"  *{update_type.title()}* ({len(type_prs)}):\n"
                    for pr in type_prs[:3]:  # Show first 3 PRs per update type
                        response += f"  - #{pr.number}: {pr.title} (@{pr.author})\n"
                    if len(type_prs) > 3:
                        response += f"  - ... and {len(type_prs) - 3} more\n"
            else:
                # Regular display for non-update categories
                for pr in prs[:5]:  # Show first 5 PRs per category
                    response += f"- #{pr.number}: {pr.title} (@{pr.author})\n"
                if len(prs) > 5:
                    response += f"- ... and {len(prs) - 5} more\n"
        
        # Add summaries based on requested level
        if summary_level == "all":
            response += f"\n📋 **Executive Summary:**\n{analysis.executive_summary}"
            response += f"\n\n🎯 **Product Summary:**\n{analysis.product_summary}"
            response += f"\n\n⚙️ **Developer Summary:**\n{analysis.developer_summary}"
        elif summary_level == "executive":
            response += f"\n📋 **Executive Summary:**\n{analysis.executive_summary}"
        elif summary_level == "product":
            response += f"\n🎯 **Product Summary:**\n{analysis.product_summary}"
        elif summary_level == "developer":
            response += f"\n⚙️ **Developer Summary:**\n{analysis.developer_summary}"
        
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