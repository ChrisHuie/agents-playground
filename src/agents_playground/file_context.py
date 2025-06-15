"""File context management for PR analysis."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class FileStatus(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"


class RepoType(Enum):
    JAVASCRIPT = "javascript"
    GO = "go"
    JAVA = "java"
    IOS = "ios"
    ANDROID = "android"
    UNKNOWN = "unknown"


@dataclass
class FileChange:
    """Represents a single file change."""
    path: str
    status: FileStatus
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


@dataclass
class FileContext:
    """Context object containing categorized file changes for a specific repo type."""
    repo_type: RepoType
    adapter_files: List[FileChange]  # For server repos, modules for mobile
    test_files: List[FileChange]
    config_files: List[FileChange]
    core_files: List[FileChange]
    build_files: List[FileChange]
    doc_files: List[FileChange]
    other_files: List[FileChange]


class FileClassifier(ABC):
    """Abstract base class for repo-specific file classifiers."""
    
    @abstractmethod
    def classify_file(self, file_change: FileChange) -> str:
        """Classify a file into a category (adapter, test, config, etc.)."""
        pass
    
    @abstractmethod
    def get_repo_type(self) -> RepoType:
        """Get the repository type this classifier handles."""
        pass


class JavaScriptFileClassifier(FileClassifier):
    """Classifier for JavaScript (Prebid.js) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.JAVASCRIPT
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify JavaScript files."""
        path = file_change.path.lower()
        
        if 'modules/' in path and any(suffix in path for suffix in [
            'bidadapter.js', 'analyticsadapter.js', 'rtdprovider.js', 'idsystem.js'
        ]):
            return 'adapter'
        elif 'test/spec/modules/' in path:
            return 'adapter'  # Module/adapter-specific tests
        elif 'test/' in path or path.endswith('.spec.js'):
            return 'test'
        elif path.startswith('.') or any(name in path for name in [
            'webpack', 'gulp', 'package.json', 'karma', 'babel',
            'wdio', 'eslint', 'browsers.json'
        ]):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path or 'integrationexamples/' in path:
            return 'doc'
        elif 'libraries/' in path:
            # Check if it's a Utils or Constants file
            if any(suffix in path for suffix in ['utils', 'constants']):
                # Core exceptions - these Utils/Constants are core functionality
                core_exceptions = [
                    'currencyutils', 'fpdutils', 'gptutils', 'ortb2utils', 
                    'sizeutils', 'transformparamsutils', 'urlutils', 'xmlutils'
                ]
                if any(exception in path for exception in core_exceptions):
                    return 'core'
                else:
                    return 'adapter'  # All other Utils/Constants are adapter-related
            else:
                return 'core'  # Non-Utils/Constants libraries are core
        elif 'src/' in path:
            return 'core'
        else:
            return 'other'


class GoFileClassifier(FileClassifier):
    """Classifier for Go (prebid-server) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.GO
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify Go files."""
        path = file_change.path.lower()
        
        if 'adapters/' in path or 'static/bidder-info/' in path or 'analytics/' in path:
            return 'adapter'
        elif 'modules/' in path:
            # Extract what comes after modules/
            module_path = path.split('modules/', 1)[1]
            # Core infrastructure directories
            if any(core_dir in module_path for core_dir in ['prebid/', 'generator/', 'moduledeps/']):
                return 'core'
            # If it has a subdirectory (contains /) it's a third-party module
            elif '/' in module_path:
                return 'adapter'  # Third-party modules with subdirectories
            else:
                return 'core'  # Top-level module files (like modules.go)
        elif 'test/' in path or path.endswith('_test.go'):
            return 'test'
        elif path.startswith('.') or any(name in path for name in ['makefile', 'dockerfile', 'go.mod']):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path:
            return 'doc'
        else:
            return 'core'  # Everything else not in adapters/analytics/modules is core


class JavaFileClassifier(FileClassifier):
    """Classifier for Java (prebid-server-java) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.JAVA
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify Java files."""
        path = file_change.path.lower()
        
        if ('src/main/java/org/prebid/server/bidder/' in path or
            'src/main/resources/bidder-config/' in path or
            'src/test/java/org/prebid/server/bidder/' in path or
            'src/test/java/org/prebid/server/it/' in path):
            return 'adapter'  # Bidder implementations, configs, and adapter-specific tests
        elif 'src/test/' in path or 'test-application.properties' in path:
            return 'test'  # General tests
        elif path.startswith('.') or any(name in path for name in ['pom.xml', 'dockerfile']):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path:
            return 'doc'
        elif 'src/main/java/org/prebid/server/' in path and 'bidder/' not in path:
            return 'core'
        else:
            return 'other'


class iOSFileClassifier(FileClassifier):
    """Classifier for iOS (prebid-mobile-ios) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.IOS
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify iOS files."""
        path = file_change.path.lower()
        
        # iOS modules/SDKs (using adapter category for consistency)
        if any(module_path in path for module_path in [
            'prebidrenderingapi/', 'prebidobjc/', 'prebidmobile/',
            'sources/', 'frameworks/', '.framework/', 'modules/'
        ]) and any(ext in path for ext in ['.swift', '.m', '.h']):
            return 'adapter'  # Mobile modules
        elif any(test_path in path for test_path in [
            'test/', 'tests/', 'uitest', 'unittests/', '.xctest'
        ]):
            return 'test'
        elif any(config_file in path for config_file in [
            'info.plist', 'podfile', '.podspec', 'project.pbxproj', 'scheme'
        ]):
            return 'config'
        elif path.startswith('.') or any(build_file in path for build_file in ['fastfile', '.yml', '.yaml', 'makefile']):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path or 'documentation/' in path:
            return 'doc'
        elif any(core_path in path for core_path in [
            'prebidrenderingapi/core', 'prebidmobile/core', 'sources/core'
        ]):
            return 'core'
        else:
            return 'other'


class AndroidFileClassifier(FileClassifier):
    """Classifier for Android/Kotlin (prebid-mobile-android) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.ANDROID
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify Android/Kotlin files."""
        path = file_change.path.lower()
        
        # Android modules/SDKs (using adapter category for consistency)
        if any(module_path in path for module_path in [
            'prebidrenderingapi/', 'prebidobjc/', 'prebidmobile/',
            'src/main/java/', 'src/main/kotlin/', 'modules/', 'library/'
        ]) and any(ext in path for ext in ['.java', '.kt', '.xml']):
            return 'adapter'  # Mobile modules
        elif any(test_path in path for test_path in [
            'src/test/', 'src/androidtest/', 'test/', 'tests/', 'uitest/'
        ]):
            return 'test'
        elif any(config_file in path for config_file in [
            'build.gradle', 'gradle.properties', 'androidmanifest.xml', 
            'proguard', 'gradle-wrapper'
        ]):
            return 'config'
        elif path.startswith('.') or any(build_file in path for build_file in [
            '.yml', '.yaml', 'makefile', 'fastfile', 'gemfile'
        ]):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path or 'documentation/' in path:
            return 'doc'
        elif any(core_path in path for core_path in [
            'prebidrenderingapi/core', 'prebidmobile/core', 'src/main/java/org/prebid/mobile/core'
        ]):
            return 'core'
        else:
            return 'other'


class FileContextManager:
    """Manages file context creation and classification."""
    
    def __init__(self):
        self.classifiers = {
            RepoType.JAVASCRIPT: JavaScriptFileClassifier(),
            RepoType.GO: GoFileClassifier(),
            RepoType.JAVA: JavaFileClassifier(),
            RepoType.IOS: iOSFileClassifier(),
            RepoType.ANDROID: AndroidFileClassifier()
        }
    
    def detect_repo_type(self, files: List[str]) -> RepoType:
        """Detect repository type based on file patterns."""
        if not files:
            return RepoType.UNKNOWN
        
        # JavaScript patterns
        if any('modules/' in f and f.endswith('.js') for f in files):
            return RepoType.JAVASCRIPT
        
        # Go patterns
        if any(f.endswith('.go') for f in files) or any('static/bidder-info/' in f for f in files):
            return RepoType.GO
        
        # Java server patterns
        if any('src/main/java/org/prebid/server/' in f for f in files):
            return RepoType.JAVA
        
        # iOS patterns
        if any(f.endswith(('.swift', '.m', '.h')) for f in files) or \
           any('ios' in f.lower() or '.xcodeproj' in f or '.podspec' in f for f in files):
            return RepoType.IOS
        
        # Android patterns
        if any(f.endswith(('.kt', '.java')) for f in files) or \
           any('android' in f.lower() or 'build.gradle' in f for f in files):
            return RepoType.ANDROID
        
        return RepoType.UNKNOWN
    
    def create_file_context(self, pr_info) -> FileContext:
        """Create a FileContext from PR info."""
        # Extract file changes
        file_changes = []
        if hasattr(pr_info, 'file_changes') and pr_info.file_changes:
            for path, change_info in pr_info.file_changes.items():
                file_changes.append(FileChange(
                    path=path,
                    status=FileStatus(change_info.get('status', 'modified')),
                    additions=change_info.get('additions', 0),
                    deletions=change_info.get('deletions', 0),
                    patch=change_info.get('patch')
                ))
        
        # Detect repo type
        repo_type = self.detect_repo_type([fc.path for fc in file_changes])
        
        # Classify files
        categorized_files = {
            'adapter': [],  # For mobile: modules/SDKs
            'test': [],
            'config': [],
            'core': [],
            'build': [],
            'doc': [],
            'other': []
        }
        
        if repo_type in self.classifiers:
            classifier = self.classifiers[repo_type]
            for file_change in file_changes:
                category = classifier.classify_file(file_change)
                categorized_files[category].append(file_change)
        else:
            categorized_files['other'] = file_changes
        
        return FileContext(
            repo_type=repo_type,
            adapter_files=categorized_files['adapter'],  # Mobile: modules/SDKs
            test_files=categorized_files['test'],
            config_files=categorized_files['config'],
            core_files=categorized_files['core'],
            build_files=categorized_files['build'],
            doc_files=categorized_files['doc'],
            other_files=categorized_files['other']
        )


@dataclass
class EnrichedFileChange(FileChange):
    """FileChange with additional context categorization."""
    category: str = 'other'  # adapter, core, test, build, doc, config, other


class PRFileAnalyzer:
    """Professional-grade PR file analysis with modular extraction and categorization."""
    
    def __init__(self, repo_type: str):
        """
        Initialize analyzer for a specific repository type.
        
        Args:
            repo_type: Repository type ('javascript', 'go', 'java', 'ios', 'android')
        """
        self.repo_type = RepoType(repo_type)
        self.context_manager = FileContextManager()
        self.classifier = self.context_manager.classifiers.get(self.repo_type)
        
        if not self.classifier:
            raise ValueError(f"Unsupported repository type: {repo_type}")
    
    def analyze_pr(self, pr_source, source_type: str = 'github_api') -> List[EnrichedFileChange]:
        """
        Analyze PR files in two phases:
        1. Extract raw file changes (path, status, additions, deletions, patch)
        2. Enrich with contextual categorization (adapter, core, test, etc.)
        
        Args:
            pr_source: GitHub PR object, dict, or other PR source
            source_type: 'github_api', 'dict', 'git_diff'
        
        Returns:
            List of EnrichedFileChange objects with both file metrics and categorization
        """
        # Phase 1: Extract raw file changes
        raw_files = self._extract_file_changes(pr_source, source_type)
        
        if not raw_files:
            return []
        
        # Phase 2: Enrich with categorization
        return self._enrich_with_categorization(raw_files)
    
    def _extract_file_changes(self, pr_source, source_type: str) -> List[FileChange]:
        """Extract raw file changes with status and metrics."""
        if source_type == 'github_api':
            return self._extract_from_github_api(pr_source)
        elif source_type == 'dict':
            return self._extract_from_dict(pr_source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _extract_from_github_api(self, github_pr) -> List[FileChange]:
        """Extract from GitHub API PR object."""
        file_changes = []
        try:
            for file_obj in github_pr.get_files():
                file_changes.append(FileChange(
                    path=file_obj.filename,
                    status=FileStatus(file_obj.status),
                    additions=file_obj.additions,
                    deletions=file_obj.deletions,
                    patch=getattr(file_obj, 'patch', None)
                ))
        except Exception as e:
            print(f"⚠️  Error extracting from GitHub API: {e}")
        return file_changes
    
    def _extract_from_dict(self, pr_info) -> List[FileChange]:
        """Extract from dictionary/existing format."""
        file_changes = []
        
        if hasattr(pr_info, 'file_changes') and pr_info.file_changes:
            for path, change_info in pr_info.file_changes.items():
                file_changes.append(FileChange(
                    path=path,
                    status=FileStatus(change_info.get('status', 'modified')),
                    additions=change_info.get('additions', 0),
                    deletions=change_info.get('deletions', 0),
                    patch=change_info.get('patch')
                ))
        
        return file_changes
    
    def _enrich_with_categorization(self, raw_files: List[FileChange]) -> List[EnrichedFileChange]:
        """Enrich raw file changes with contextual categorization."""
        if not raw_files:
            return []
        
        # Categorize each file using the pre-configured classifier
        enriched_files = []
        for file_change in raw_files:
            category = self.classifier.classify_file(file_change)
            enriched_files.append(EnrichedFileChange(
                path=file_change.path,
                status=file_change.status,
                additions=file_change.additions,
                deletions=file_change.deletions,
                patch=file_change.patch,
                category=category
            ))
        
        return enriched_files
    
    def get_summary_by_category(self, enriched_files: List[EnrichedFileChange]) -> Dict[str, Dict[str, int]]:
        """Get summary statistics grouped by category."""
        summary = {}
        
        for file_change in enriched_files:
            category = file_change.category
            if category not in summary:
                summary[category] = {
                    'files': 0, 'added': 0, 'modified': 0, 'removed': 0,
                    'total_additions': 0, 'total_deletions': 0
                }
            
            summary[category]['files'] += 1
            summary[category][file_change.status.value] += 1
            summary[category]['total_additions'] += file_change.additions
            summary[category]['total_deletions'] += file_change.deletions
        
        return summary