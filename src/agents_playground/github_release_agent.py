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
        # Get file changes and their diffs for better categorization
        files = []
        file_changes = {}  # Store file changes for content analysis
        try:
            pr_files = list(pr.get_files())
            files = [f.filename for f in pr_files]
            
            # Get file changes/diffs for content analysis
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
        
        # Store file changes in PRInfo for content analysis
        pr_info = PRInfo(
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
        
        # Add file changes as custom attribute
        pr_info.file_changes = file_changes
        
        return pr_info
    
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
        """Check if PR introduces a new adapter or module based on file changes and content analysis."""
        if not pr.files or not hasattr(pr, 'file_changes'):
            return False
        
        import re
        
        # Detect repository type based on file patterns
        is_js_repo = any('modules/' in f and f.endswith('.js') for f in pr.files)
        is_go_repo = any('adapters/' in f and f.endswith('.go') for f in pr.files) or \
                     any('static/bidder-info/' in f for f in pr.files) or \
                     any('analytics/' in f for f in pr.files)
        is_java_repo = any('src/main/java/' in f and 'bidder/' in f for f in pr.files) or \
                       any('src/main/resources/bidder-config/' in f for f in pr.files)
        
        # Analyze based on repository type and actual file changes
        if is_js_repo:
            return self._detect_new_js_adapter(pr)
        elif is_go_repo:
            return self._detect_new_go_adapter(pr)
        elif is_java_repo:
            return self._detect_new_java_adapter(pr)
        
        return False
    
    def _detect_new_js_adapter(self, pr: PRInfo) -> bool:
        """Detect new JavaScript adapters/modules based on file creation patterns."""
        import re
        
        # JavaScript pattern: New files in modules/ with specific extensions are always new adapters/modules
        js_adapter_patterns = [
            r'modules/[^/]+BidAdapter\.js$',
            r'modules/[^/]+AnalyticsAdapter\.js$', 
            r'modules/[^/]+RtdProvider\.js$',
            r'modules/[^/]+IdSystem\.js$'
        ]
        
        new_adapter_files = []
        
        for file_path, changes in pr.file_changes.items():
            # Check if this is a new file being added (not modified)
            if changes['status'] == 'added':
                for pattern in js_adapter_patterns:
                    if re.match(pattern, file_path):
                        new_adapter_files.append(file_path)
                        break
        
        # If any new adapter files are being created, it's definitely a new adapter/module
        if new_adapter_files:
            print(f"🆕 New JS adapter found: {len(new_adapter_files)} files created")
            return True
        
        return False
    
    def _detect_new_go_adapter(self, pr: PRInfo) -> bool:
        """Detect new Go adapters based on aliasOf patterns and new file creation."""
        import re
        
        # Pattern 1: Check for aliasOf being added to YAML files (indicates new adapter alias)
        for file_path, changes in pr.file_changes.items():
            if file_path.startswith('static/bidder-info/') and file_path.endswith('.yaml'):
                patch = changes.get('patch', '')
                if patch:
                    # Look for various aliasOf patterns being added
                    alias_patterns = [
                        '+aliasOf:', '+ aliasOf:', '+  aliasOf:',  # Different indentation
                        '+ aliasOf :', '+aliasOf :', '+  aliasOf :'  # With space before colon
                    ]
                    
                    for pattern in alias_patterns:
                        if pattern in patch:
                            print(f"🏷️ New Go alias found: alias configuration in {file_path}")
                            return True
                    
                    # Also check for the creation of new alias files
                    if changes['status'] == 'added' and 'aliasOf' in patch:
                        print(f"🏷️ New Go alias found: alias file created")
                        return True
        
        # Pattern 2: New analytics adapter files being created
        analytics_files = []
        for file_path, changes in pr.file_changes.items():
            if changes['status'] == 'added' and file_path.startswith('analytics/'):
                analytics_files.append(file_path)
        
        # If multiple analytics files are being created, it's a new analytics adapter
        if len(analytics_files) >= 2:
            print(f"🆕 New Go analytics adapter found: {len(analytics_files)} files created")
            return True
        
        # Pattern 3: New bidder adapter files being created (full implementation)
        new_adapter_dirs = set()
        for file_path, changes in pr.file_changes.items():
            if changes['status'] == 'added':
                # Check for new adapter implementation
                match = re.match(r'adapters/([^/]+)/\1\.go$', file_path)
                if match:
                    adapter_name = match.group(1)
                    new_adapter_dirs.add(adapter_name)
                
                # Check for new bidder config
                match = re.match(r'static/bidder-info/([^/]+)\.yaml$', file_path)
                if match:
                    adapter_name = match.group(1)
                    new_adapter_dirs.add(adapter_name)
        
        # If we have new adapter files being created, it's likely a new adapter
        if new_adapter_dirs:
            print(f"🆕 New Go adapter found: {len(new_adapter_dirs)} adapters created")
            return True
        
        return False
    
    def _detect_new_java_adapter(self, pr: PRInfo) -> bool:
        """Detect new Java adapters based on aliases being added and new file creation."""
        import re
        
        # Pattern 1: Check for test-application.properties alias configurations (primary pattern)
        for file_path, changes in pr.file_changes.items():
            if 'test-application.properties' in file_path:
                patch = changes.get('patch', '')
                if patch:
                    # Look for adapter.parent.aliases.alias_name patterns
                    if self._detect_test_properties_alias(patch, file_path):
                        return True
        
        # Pattern 2: Check for aliases being added to YAML bidder-config files
        for file_path, changes in pr.file_changes.items():
            if 'src/main/resources/bidder-config/' in file_path and file_path.endswith('.yaml'):
                patch = changes.get('patch', '')
                if patch and self._detect_yaml_alias_addition(patch, file_path):
                    return True
        
        # Pattern 3: Check for new alias test files being created with content analysis
        for file_path, changes in pr.file_changes.items():
            if changes['status'] == 'added':
                # Check for new test files that might indicate aliases
                if file_path.endswith('Test.java') and ('src/test/java/' in file_path or 'src/test/' in file_path):
                    # Check patch content for alias indicators (not title)
                    patch = changes.get('patch', '')
                    if patch:
                        # Look for alias-specific patterns in test code
                        if self._has_alias_test_patterns(patch, file_path):
                            return True
        
        # Pattern 4: Check for specific file combination patterns that indicate alias
        if self._detect_alias_file_patterns(pr):
            return True
        
        # Pattern 5: New bidder implementation files being created (full adapters)
        new_bidder_files = []
        for file_path, changes in pr.file_changes.items():
            if changes['status'] == 'added':
                # Check for new Java bidder implementation
                if 'src/main/java/org/prebid/server/bidder/' in file_path and 'Bidder.java' in file_path:
                    new_bidder_files.append(file_path)
                
                # Check for new bidder configuration
                elif 'src/main/resources/bidder-config/' in file_path and file_path.endswith('.yaml'):
                    new_bidder_files.append(file_path)
        
        # If multiple new bidder files are being created, it's likely a new adapter (not alias)
        if len(new_bidder_files) >= 2:
            print(f"🆕 New Java adapter found: {len(new_bidder_files)} files created")
            return True
        
        return False
    
    def _is_java_alias_by_title(self, title: str) -> bool:
        """Check if PR title indicates this is a Java alias."""
        import re
        title_lower = title.lower()
        
        # Pattern 1: "New Adapter: [Name] - [Parent] alias"
        if re.match(r'new adapter:\s+\w+\s+-\s+\w+\s+alias', title_lower):
            return True
        
        # Pattern 2: Contains "alias" and parent adapter references
        if 'alias' in title_lower:
            # Common parent adapters in Java server
            parent_adapters = [
                'adkernel', 'admatic', 'limelight', 'limelightdigital', 
                'appnexus', 'rubicon', 'pubmatic', 'openx', 'criteo',
                'smartadserver', 'ix', 'sharethrough', 'sovrn'
            ]
            for parent in parent_adapters:
                if parent in title_lower:
                    return True
        
        # Pattern 3: "Mere alias" phrase
        if 'mere alias' in title_lower:
            return True
        
        # Pattern 4: Title format with alias description
        if (' - ' in title and 'alias' in title_lower) or ('(' in title and 'alias' in title_lower and ')' in title):
            return True
        
        return False
    
    def _detect_yaml_alias_addition(self, patch: str, file_path: str) -> bool:
        """Detect alias additions in YAML bidder-config files."""
        import re
        
        # Pattern 1: Look for aliases section being added
        if re.search(r'^\+\s{4}aliases:\s*$', patch, re.MULTILINE):
            print(f"🏷️ New Java alias found: aliases section added in {file_path}")
            return True
        
        # Pattern 2: Look for new alias entries being added under existing aliases section
        # Format: +      alias-name: (6 spaces indentation)
        alias_name_pattern = re.search(r'^\+\s{6}[\w\-]+:\s*', patch, re.MULTILINE)
        if alias_name_pattern:
            print(f"🏷️ New Java alias found: alias entry added in {file_path}")
            return True
        
        # Pattern 3: Look for alias configuration lines being added
        # Format: +        enabled: false (8+ spaces indentation)
        alias_config_patterns = [
            r'^\+\s{8}enabled:\s*(true|false)\s*$',
            r'^\+\s{8}endpoint:\s*.+$',
            r'^\+\s{8}meta-info:\s*$',
            r'^\+\s{10}maintainer-email:\s*.+$'
        ]
        
        for pattern in alias_config_patterns:
            if re.search(pattern, patch, re.MULTILINE):
                # Additional check: make sure we're in aliases context
                if 'aliases' in patch:
                    print(f"🏷️ New Java alias found: alias configuration in {file_path}")
                    return True
        
        # Pattern 4: Look for simple alias with null value
        # Format: +      alias-name: ~
        if re.search(r'^\+\s{6}[\w\-]+:\s*~\s*$', patch, re.MULTILINE):
            print(f"🏷️ New Java alias found: simple alias entry in {file_path}")
            return True
        
        return False
    
    def _detect_test_properties_alias(self, patch: str, file_path: str) -> bool:
        """Detect alias configurations in test-application.properties files."""
        import re
        
        # Look for adapter.parent.aliases.alias_name patterns
        alias_config_patterns = [
            r'\+adapters\.\w+\.aliases\.\w+\.enabled\s*=\s*true',
            r'\+adapters\.\w+\.aliases\.\w+\.endpoint\s*=',
            r'\+\s*adapters\.\w+\.aliases\.\w+\.enabled\s*=\s*true',
            r'\+\s*adapters\.\w+\.aliases\.\w+\.endpoint\s*='
        ]
        
        for pattern in alias_config_patterns:
            matches = re.findall(pattern, patch, re.IGNORECASE)
            if matches:
                print(f"🏷️ New Java alias found: test configuration in {file_path}")
                return True
        
        # Also check for simpler .aliases. pattern in additions
        if '+' in patch and '.aliases.' in patch:
            lines = patch.split('\n')
            for line in lines:
                if line.startswith('+') and '.aliases.' in line and ('enabled' in line or 'endpoint' in line):
                    print(f"🏷️ New Java alias found: alias configuration in {file_path}")
                    return True
        
        return False
    
    def _has_alias_test_patterns(self, patch: str, file_path: str) -> bool:
        """Check if test file patch contains alias-specific patterns."""
        import re
        
        # Look for alias indicators in test code
        alias_indicators = [
            'alias',
            'Alias',
            'ALIAS',
            'aliasOf',
            'parent.*bidder',
            'bidder.*alias'
        ]
        
        for indicator in alias_indicators:
            if re.search(indicator, patch, re.IGNORECASE):
                print(f"🏷️ New Java alias found: alias test pattern in {file_path}")
                return True
        
        return False
    
    def _detect_alias_file_patterns(self, pr: PRInfo) -> bool:
        """Check for specific file patterns that indicate alias creation."""
        added_files = []
        modified_files = []
        
        for file_path, changes in pr.file_changes.items():
            if changes['status'] == 'added':
                added_files.append(file_path)
            elif changes['status'] == 'modified':
                modified_files.append(file_path)
        
        # Pattern 1: Test file added + test-application.properties modified with alias config
        has_test_file_added = any('Test.java' in f for f in added_files)
        has_test_props_modified = any('test-application.properties' in f for f in modified_files)
        
        if has_test_file_added and has_test_props_modified:
            # Verify the test-application.properties contains alias configuration
            for file_path, changes in pr.file_changes.items():
                if 'test-application.properties' in file_path:
                    patch = changes.get('patch', '')
                    if patch and '.aliases.' in patch:
                        print(f"🏷️ New Java alias found: test file + alias configuration pattern")
                        return True
        
        # Pattern 2: Configuration files modified with alias content (no new bidder files)
        has_alias_config = False
        has_new_bidder_impl = any('src/main/java/org/prebid/server/bidder/' in f and 'Bidder.java' in f for f in added_files)
        
        if not has_new_bidder_impl:  # No new bidder implementation = likely alias
            for file_path, changes in pr.file_changes.items():
                if file_path.endswith('.yaml') or 'test-application.properties' in file_path:
                    patch = changes.get('patch', '')
                    if patch and ('.aliases.' in patch or '+aliases:' in patch):
                        has_alias_config = True
                        break
            
            if has_alias_config:
                print(f"🏷️ New Java alias found: configuration-only alias changes")
                return True
        
        return False
    
    def _has_aliases_context(self, patch: str) -> bool:
        """Check if patch has aliases context (helpful for detecting alias list additions)."""
        lines = patch.split('\n')
        for i, line in enumerate(lines):
            if 'aliases:' in line:
                # Check if there are subsequent lines with list items
                for j in range(i+1, min(i+10, len(lines))):
                    if '+ -' in lines[j] or '+  -' in lines[j]:
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