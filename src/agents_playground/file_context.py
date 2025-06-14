"""File context management for PR analysis."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
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
        elif 'test/' in path or path.endswith('_test.go'):
            return 'test'
        elif path.startswith('.') or any(name in path for name in ['makefile', 'dockerfile', 'go.mod']):
            return 'build'
        elif path.endswith('.md') or 'docs/' in path:
            return 'doc'
        elif any(core_path in path for core_path in [
            'endpoints/', 'exchange/', 'stored_requests/', 'privacy/', 'currency/', 'config/'
        ]):
            return 'core'
        else:
            return 'other'


class JavaFileClassifier(FileClassifier):
    """Classifier for Java (prebid-server-java) repositories."""
    
    def get_repo_type(self) -> RepoType:
        return RepoType.JAVA
    
    def classify_file(self, file_change: FileChange) -> str:
        """Classify Java files."""
        path = file_change.path.lower()
        
        if ('src/main/java/org/prebid/server/bidder/' in path or
            'src/main/resources/bidder-config/' in path):
            return 'adapter'
        elif 'src/test/' in path or 'test-application.properties' in path:
            return 'test'
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