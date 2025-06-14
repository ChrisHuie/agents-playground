"""Modular PR categorization detectors for different types of changes."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class DetectionResult:
    """Result of a detection with additional metadata."""
    detected: bool
    confidence: float = 1.0
    metadata: Dict = None
    reason: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseDetector(ABC):
    """Base class for all category detectors."""
    
    @abstractmethod
    def detect(self, pr_info) -> DetectionResult:
        """Detect if PR belongs to this category."""
        pass
    
    @abstractmethod
    def get_category_name(self) -> str:
        """Get the name of this category."""
        pass


class RepositoryTypeDetector:
    """Utility class to detect repository type based on file patterns."""
    
    @staticmethod
    def detect_repo_type(files: List[str]) -> str:
        """Detect repository type: 'javascript', 'go', 'java', or 'unknown'."""
        if not files:
            return 'unknown'
        
        # JavaScript patterns
        if any('modules/' in f and f.endswith('.js') for f in files):
            return 'javascript'
        
        # Go patterns
        if any(f.endswith('.go') for f in files) or \
           any('static/bidder-info/' in f for f in files):
            return 'go'
        
        # Java patterns
        if any('src/main/java/' in f for f in files) or \
           any('src/main/resources/' in f for f in files):
            return 'java'
        
        return 'unknown'


class NewAdaptersModulesDetector(BaseDetector):
    """Detector for new adapters and modules."""
    
    def get_category_name(self) -> str:
        return "New Adapters & Modules"
    
    def detect(self, pr_info) -> DetectionResult:
        """Detect new adapters/modules based on repo type and file patterns."""
        if not hasattr(pr_info, 'files') or not pr_info.files:
            return DetectionResult(detected=False, reason="No files found")
        
        repo_type = RepositoryTypeDetector.detect_repo_type(pr_info.files)
        
        if repo_type == 'javascript':
            return self._detect_javascript_new_adapter(pr_info)
        elif repo_type == 'go':
            return self._detect_go_new_adapter(pr_info)
        elif repo_type == 'java':
            return self._detect_java_new_adapter(pr_info)
        else:
            return DetectionResult(detected=False, reason=f"Unknown repo type: {repo_type}")
    
    def _detect_javascript_new_adapter(self, pr_info) -> DetectionResult:
        """Detect new JavaScript adapters/modules."""
        js_adapter_patterns = [
            r'modules/[^/]+BidAdapter\.js$',
            r'modules/[^/]+AnalyticsAdapter\.js$', 
            r'modules/[^/]+RtdProvider\.js$',
            r'modules/[^/]+IdSystem\.js$'
        ]
        
        new_adapter_files = []
        
        if hasattr(pr_info, 'file_changes'):
            for file_path, changes in pr_info.file_changes.items():
                if changes.get('status') == 'added':
                    for pattern in js_adapter_patterns:
                        if re.match(pattern, file_path):
                            new_adapter_files.append(file_path)
                            break
        
        if new_adapter_files:
            return DetectionResult(
                detected=True,
                confidence=1.0,
                metadata={'files': new_adapter_files, 'type': 'new_js_adapter'},
                reason=f"New JS adapter files created: {len(new_adapter_files)} files"
            )
        
        return DetectionResult(detected=False, reason="No new JS adapter files found")
    
    def _detect_go_new_adapter(self, pr_info) -> DetectionResult:
        """Detect new Go adapters (including aliases)."""
        # Check for alias configurations first
        alias_result = self._detect_go_alias(pr_info)
        if alias_result.detected:
            return alias_result
        
        # Check for new analytics adapters
        analytics_result = self._detect_go_analytics_adapter(pr_info)
        if analytics_result.detected:
            return analytics_result
        
        # Check for new bidder adapters
        bidder_result = self._detect_go_bidder_adapter(pr_info)
        if bidder_result.detected:
            return bidder_result
        
        return DetectionResult(detected=False, reason="No new Go adapters found")
    
    def _detect_go_alias(self, pr_info) -> DetectionResult:
        """Detect Go adapter aliases."""
        if not hasattr(pr_info, 'file_changes'):
            return DetectionResult(detected=False, reason="No file changes data")
        
        for file_path, changes in pr_info.file_changes.items():
            if file_path.startswith('static/bidder-info/') and file_path.endswith('.yaml'):
                patch = changes.get('patch', '')
                if patch:
                    alias_patterns = [
                        '+aliasOf:', '+ aliasOf:', '+  aliasOf:',
                        '+ aliasOf :', '+aliasOf :', '+  aliasOf :'
                    ]
                    
                    for pattern in alias_patterns:
                        if pattern in patch:
                            return DetectionResult(
                                detected=True,
                                metadata={'file': file_path, 'type': 'go_alias'},
                                reason=f"Go alias configuration found in {file_path}"
                            )
        
        return DetectionResult(detected=False, reason="No Go alias patterns found")
    
    def _detect_go_analytics_adapter(self, pr_info) -> DetectionResult:
        """Detect new Go analytics adapters."""
        if not hasattr(pr_info, 'file_changes'):
            return DetectionResult(detected=False, reason="No file changes data")
        
        analytics_files = []
        for file_path, changes in pr_info.file_changes.items():
            if changes.get('status') == 'added' and file_path.startswith('analytics/'):
                analytics_files.append(file_path)
        
        if len(analytics_files) >= 2:
            return DetectionResult(
                detected=True,
                metadata={'files': analytics_files, 'type': 'go_analytics'},
                reason=f"New Go analytics adapter: {len(analytics_files)} files created"
            )
        
        return DetectionResult(detected=False, reason="Insufficient analytics files for new adapter")
    
    def _detect_go_bidder_adapter(self, pr_info) -> DetectionResult:
        """Detect new Go bidder adapters."""
        if not hasattr(pr_info, 'file_changes'):
            return DetectionResult(detected=False, reason="No file changes data")
        
        new_adapter_dirs = set()
        for file_path, changes in pr_info.file_changes.items():
            if changes.get('status') == 'added':
                # Check for new adapter implementation
                match = re.match(r'adapters/([^/]+)/\1\.go$', file_path)
                if match:
                    new_adapter_dirs.add(match.group(1))
                
                # Check for new bidder config
                match = re.match(r'static/bidder-info/([^/]+)\.yaml$', file_path)
                if match:
                    new_adapter_dirs.add(match.group(1))
        
        if new_adapter_dirs:
            return DetectionResult(
                detected=True,
                metadata={'adapters': list(new_adapter_dirs), 'type': 'go_bidder'},
                reason=f"New Go bidder adapter: {len(new_adapter_dirs)} adapters created"
            )
        
        return DetectionResult(detected=False, reason="No new Go bidder adapters found")
    
    def _detect_java_new_adapter(self, pr_info) -> DetectionResult:
        """Detect new Java adapters (including aliases)."""
        # Check for alias configurations first (most common)
        alias_result = self._detect_java_alias(pr_info)
        if alias_result.detected:
            return alias_result
        
        # Check for new bidder implementations
        bidder_result = self._detect_java_bidder_adapter(pr_info)
        if bidder_result.detected:
            return bidder_result
        
        return DetectionResult(detected=False, reason="No new Java adapters found")
    
    def _detect_java_alias(self, pr_info) -> DetectionResult:
        """Detect Java adapter aliases."""
        if not hasattr(pr_info, 'file_changes'):
            return DetectionResult(detected=False, reason="No file changes data")
        
        # Check test-application.properties for alias configs
        for file_path, changes in pr_info.file_changes.items():
            if 'test-application.properties' in file_path:
                patch = changes.get('patch', '')
                if patch and self._has_java_alias_properties(patch):
                    return DetectionResult(
                        detected=True,
                        metadata={'file': file_path, 'type': 'java_alias_properties'},
                        reason=f"Java alias configuration in {file_path}"
                    )
        
        # Check YAML bidder-config files for alias additions
        for file_path, changes in pr_info.file_changes.items():
            if 'src/main/resources/bidder-config/' in file_path and file_path.endswith('.yaml'):
                patch = changes.get('patch', '')
                if patch and self._has_java_alias_yaml(patch):
                    return DetectionResult(
                        detected=True,
                        metadata={'file': file_path, 'type': 'java_alias_yaml'},
                        reason=f"Java alias YAML configuration in {file_path}"
                    )
        
        return DetectionResult(detected=False, reason="No Java alias patterns found")
    
    def _has_java_alias_properties(self, patch: str) -> bool:
        """Check for Java alias patterns in properties files."""
        alias_patterns = [
            r'\+adapters\.\w+\.aliases\.\w+\.enabled\s*=\s*true',
            r'\+adapters\.\w+\.aliases\.\w+\.endpoint\s*=',
            r'\+\s*adapters\.\w+\.aliases\.\w+\.enabled\s*=\s*true',
            r'\+\s*adapters\.\w+\.aliases\.\w+\.endpoint\s*='
        ]
        
        for pattern in alias_patterns:
            if re.search(pattern, patch, re.IGNORECASE):
                return True
        
        return '+' in patch and '.aliases.' in patch and ('enabled' in patch or 'endpoint' in patch)
    
    def _has_java_alias_yaml(self, patch: str) -> bool:
        """Check for Java alias patterns in YAML files."""
        # Look for aliases section being added
        if re.search(r'^\+\s{4}aliases:\s*$', patch, re.MULTILINE):
            return True
        
        # Look for new alias entries
        if re.search(r'^\+\s{6}[\w\-]+:\s*', patch, re.MULTILINE):
            return True
        
        # Look for alias configuration lines
        alias_config_patterns = [
            r'^\+\s{8}enabled:\s*(true|false)\s*$',
            r'^\+\s{8}endpoint:\s*.+$',
            r'^\+\s{6}[\w\-]+:\s*~\s*$'
        ]
        
        for pattern in alias_config_patterns:
            if re.search(pattern, patch, re.MULTILINE) and 'aliases' in patch:
                return True
        
        return False
    
    def _detect_java_bidder_adapter(self, pr_info) -> DetectionResult:
        """Detect new Java bidder adapters (full implementations)."""
        if not hasattr(pr_info, 'file_changes'):
            return DetectionResult(detected=False, reason="No file changes data")
        
        # Check for existing bidder file modifications (indicates update, not new)
        modified_bidder_files = []
        new_bidder_files = []
        
        for file_path, changes in pr_info.file_changes.items():
            if 'src/main/java/org/prebid/server/bidder/' in file_path and 'Bidder.java' in file_path:
                if changes.get('status') == 'modified':
                    modified_bidder_files.append(file_path)
                elif changes.get('status') == 'added':
                    new_bidder_files.append(file_path)
        
        # If modifying existing bidder files, it's likely an update
        if modified_bidder_files and not new_bidder_files:
            return DetectionResult(detected=False, reason="Existing bidder files modified (update, not new)")
        
        # Count new bidder-related files
        all_new_bidder_files = []
        for file_path, changes in pr_info.file_changes.items():
            if changes.get('status') == 'added':
                if ('src/main/java/org/prebid/server/bidder/' in file_path and 'Bidder.java' in file_path) or \
                   ('src/main/resources/bidder-config/' in file_path and file_path.endswith('.yaml')):
                    all_new_bidder_files.append(file_path)
        
        if len(all_new_bidder_files) >= 2:
            return DetectionResult(
                detected=True,
                metadata={'files': all_new_bidder_files, 'type': 'java_bidder'},
                reason=f"New Java bidder adapter: {len(all_new_bidder_files)} files created"
            )
        
        return DetectionResult(detected=False, reason="Insufficient new bidder files")


class TestingBuildDocsDetector(BaseDetector):
    """Detector for testing, build process, and documentation changes."""
    
    def get_category_name(self) -> str:
        return "Testing / Build Process / Docs Updates"
    
    def detect(self, pr_info) -> DetectionResult:
        """Detect testing, build, or documentation changes."""
        if not hasattr(pr_info, 'files') or not pr_info.files:
            return DetectionResult(detected=False, reason="No files found")
        
        test_build_docs_files = []
        
        for file_path in pr_info.files:
            file_lower = file_path.lower()
            if any(pattern in file_lower for pattern in [
                'src/test/', '/test/', '.test.', '_test.', 'spec/',
                '.github/', 'ci/', '.ci/', 'workflow/', 'pipeline/',
                'dockerfile', 'makefile', 'gulpfile', 'webpack',
                'package.json', 'pom.xml', 'build.gradle', 'go.mod',
                'readme', 'license', '.md', 'docs/', 'documentation/',
                'changelog', 'contributing', '.yml', '.yaml',
                'eslint', 'prettier', '.gitignore', '.editorconfig'
            ]) and not any(exclude in file_lower for exclude in [
                'src/main/java/org/prebid/server/bidder/',
                'modules/', 'adapters/', 'static/bidder-info/'
            ]):
                test_build_docs_files.append(file_path)
        
        if test_build_docs_files:
            return DetectionResult(
                detected=True,
                metadata={'files': test_build_docs_files},
                reason=f"Test/build/docs files found: {len(test_build_docs_files)} files"
            )
        
        return DetectionResult(detected=False, reason="No test/build/docs files found")


class AdapterModuleChangesDetector(BaseDetector):
    """Detector for adapter and module changes (features vs updates)."""
    
    def __init__(self, is_feature: bool = False):
        self.is_feature = is_feature
    
    def get_category_name(self) -> str:
        return "Adapter & Module Features" if self.is_feature else "Adapter & Module Updates"
    
    def detect(self, pr_info) -> DetectionResult:
        """Detect adapter/module changes and determine if feature or update."""
        if not self._is_adapter_or_module_change(pr_info):
            return DetectionResult(detected=False, reason="Not an adapter/module change")
        
        is_new_feature = self._is_new_feature_change(pr_info)
        
        if self.is_feature and is_new_feature:
            return DetectionResult(
                detected=True,
                metadata={'change_type': 'feature'},
                reason="Adapter/module feature (more files added than modified)"
            )
        elif not self.is_feature and not is_new_feature:
            return DetectionResult(
                detected=True,
                metadata={'change_type': 'update'},
                reason="Adapter/module update (more files modified than added)"
            )
        
        return DetectionResult(detected=False, reason=f"Not a {'feature' if self.is_feature else 'update'}")
    
    def _is_adapter_or_module_change(self, pr_info) -> bool:
        """Check if PR affects adapter/module files."""
        if not hasattr(pr_info, 'files') or not pr_info.files:
            return False
        
        for file_path in pr_info.files:
            file_lower = file_path.lower()
            if any(pattern in file_lower for pattern in [
                'modules/', 'adapters/', 'bidder/', 'analytics/',
                'bidderadapter', 'analyticsadapter', 'rtdprovider', 'idsystem',
                'src/main/java/org/prebid/server/bidder/',
                'src/main/resources/bidder-config/',
                'static/bidder-info/'
            ]):
                return True
        
        return False
    
    def _is_new_feature_change(self, pr_info) -> bool:
        """Determine if this is a new feature based on file creation vs modification."""
        if not hasattr(pr_info, 'file_changes') or not pr_info.file_changes:
            return False
        
        added_files = sum(1 for changes in pr_info.file_changes.values() if changes.get('status') == 'added')
        modified_files = sum(1 for changes in pr_info.file_changes.values() if changes.get('status') == 'modified')
        
        return added_files > modified_files


class CoreChangesDetector(BaseDetector):
    """Detector for core system changes (features vs updates)."""
    
    def __init__(self, is_feature: bool = False):
        self.is_feature = is_feature
    
    def get_category_name(self) -> str:
        return "Core Features" if self.is_feature else "Core Updates"
    
    def detect(self, pr_info) -> DetectionResult:
        """Detect core changes and determine if feature or update."""
        if not self._is_core_change(pr_info):
            return DetectionResult(detected=False, reason="Not a core change")
        
        is_new_feature = self._is_new_feature_change(pr_info)
        
        if self.is_feature and is_new_feature:
            return DetectionResult(
                detected=True,
                metadata={'change_type': 'feature'},
                reason="Core feature (more files added than modified)"
            )
        elif not self.is_feature and not is_new_feature:
            return DetectionResult(
                detected=True,
                metadata={'change_type': 'update'},
                reason="Core update (more files modified than added)"
            )
        
        return DetectionResult(detected=False, reason=f"Not a core {'feature' if self.is_feature else 'update'}")
    
    def _is_core_change(self, pr_info) -> bool:
        """Check if PR affects core system files."""
        if not hasattr(pr_info, 'files') or not pr_info.files:
            return False
        
        for file_path in pr_info.files:
            file_lower = file_path.lower()
            if any(pattern in file_lower for pattern in [
                'src/main/java/org/prebid/server/auction',
                'src/main/java/org/prebid/server/cache',
                'src/main/java/org/prebid/server/currency',
                'src/main/java/org/prebid/server/privacy',
                'src/main/java/org/prebid/server/floors',
                'src/main/java/org/prebid/server/deals',
                'src/main/java/org/prebid/server/validation',
                'src/main/java/org/prebid/server/handler',
                'src/auction',
                'src/targeting',
                'src/utils',
                'libraries/',
                'endpoints/',
                'exchange/',
                'stored_requests/',
                'privacy/',
                'currency/',
                'config/',
            ]) and not any(exclude in file_lower for exclude in [
                'bidder/', 'adapters/', 'modules/', 'analytics/',
                'test/', '/test/', '.test.', '_test.', 'spec/',
                '.github/', '.md', 'docs/', 'readme', 'changelog'
            ]):
                return True
        
        return False
    
    def _is_new_feature_change(self, pr_info) -> bool:
        """Determine if this is a new feature based on file creation vs modification."""
        if not hasattr(pr_info, 'file_changes') or not pr_info.file_changes:
            return False
        
        added_files = sum(1 for changes in pr_info.file_changes.values() if changes.get('status') == 'added')
        modified_files = sum(1 for changes in pr_info.file_changes.values() if changes.get('status') == 'modified')
        
        return added_files > modified_files


class OtherDetector(BaseDetector):
    """Fallback detector for uncategorized changes."""
    
    def get_category_name(self) -> str:
        return "Other"
    
    def detect(self, pr_info) -> DetectionResult:
        """Always detects (fallback category)."""
        return DetectionResult(
            detected=True,
            confidence=0.5,
            reason="Fallback category for uncategorized changes"
        )