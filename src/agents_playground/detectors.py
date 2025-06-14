"""Modular PR categorization detectors for different types of changes."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

from .file_context import FileContextManager, FileContext


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
        # Create file context from pr_info
        context_manager = FileContextManager()
        file_context = context_manager.create_file_context(pr_info)
        
        if file_context.repo_type.value == 'javascript':
            return self._detect_javascript_new_adapter(file_context)
        elif file_context.repo_type.value == 'go':
            return self._detect_go_new_adapter(file_context)
        elif file_context.repo_type.value == 'java':
            return self._detect_java_new_adapter(file_context)
        else:
            return DetectionResult(detected=False, reason=f"Unknown repo type: {file_context.repo_type.value}")
    
    def _detect_javascript_new_adapter(self, file_context) -> DetectionResult:
        """Detect new JavaScript adapters/modules and aliases."""
        # First check for aliases (most common in JS)
        alias_result = self._detect_js_alias(file_context)
        if alias_result.detected:
            return alias_result
        
        # Then check for new adapter files
        new_adapter_files = [fc.path for fc in file_context.adapter_files 
                           if fc.status.value == 'added']
        
        if new_adapter_files:
            # Filter for actual adapter patterns
            js_adapter_patterns = [
                r'modules/[^/]+BidAdapter\.js$',
                r'modules/[^/]+AnalyticsAdapter\.js$', 
                r'modules/[^/]+RtdProvider\.js$',
                r'modules/[^/]+IdSystem\.js$'
            ]
            
            actual_adapters = []
            for file_path in new_adapter_files:
                for pattern in js_adapter_patterns:
                    if re.match(pattern, file_path):
                        actual_adapters.append(file_path)
                        break
            new_adapter_files = actual_adapters
        
        if new_adapter_files:
            return DetectionResult(
                detected=True,
                confidence=1.0,
                metadata={'files': new_adapter_files, 'type': 'new_js_adapter'},
                reason=f"New JS adapter files created: {len(new_adapter_files)} files"
            )
        
        return DetectionResult(detected=False, reason="No new JS adapters or aliases found")
    
    def _detect_go_new_adapter(self, file_context) -> DetectionResult:
        """Detect new Go adapters (including aliases)."""
        # Check for alias configurations first
        alias_result = self._detect_go_alias(file_context)
        if alias_result.detected:
            return alias_result
        
        # Check for new analytics adapters
        analytics_result = self._detect_go_analytics_adapter(file_context)
        if analytics_result.detected:
            return analytics_result
        
        # Check for new bidder adapters
        bidder_result = self._detect_go_bidder_adapter(file_context)
        if bidder_result.detected:
            return bidder_result
        
        return DetectionResult(detected=False, reason="No new Go adapters found")
    
    def _detect_go_alias(self, file_context) -> DetectionResult:
        """Detect Go adapter aliases."""
        # Check config files for alias patterns
        for file_change in file_context.config_files:
            if file_change.path.startswith('static/bidder-info/') and file_change.path.endswith('.yaml'):
                patch = file_change.patch or ''
                if patch:
                    alias_patterns = [
                        '+aliasOf:', '+ aliasOf:', '+  aliasOf:',
                        '+ aliasOf :', '+aliasOf :', '+  aliasOf :'
                    ]
                    
                    for pattern in alias_patterns:
                        if pattern in patch:
                            return DetectionResult(
                                detected=True,
                                metadata={'file': file_change.path, 'type': 'go_alias'},
                                reason=f"Go alias configuration found in {file_change.path}"
                            )
        
        return DetectionResult(detected=False, reason="No Go alias patterns found")
    
    def _detect_go_analytics_adapter(self, file_context) -> DetectionResult:
        """Detect new Go analytics adapters."""
        # Check adapter files for analytics patterns
        analytics_files = [fc.path for fc in file_context.adapter_files 
                          if fc.status.value == 'added' and fc.path.startswith('analytics/')]
        
        if len(analytics_files) >= 2:
            return DetectionResult(
                detected=True,
                metadata={'files': analytics_files, 'type': 'go_analytics'},
                reason=f"New Go analytics adapter: {len(analytics_files)} files created"
            )
        
        return DetectionResult(detected=False, reason="Insufficient analytics files for new adapter")
    
    def _detect_go_bidder_adapter(self, file_context) -> DetectionResult:
        """Detect new Go bidder adapters."""
        new_adapter_dirs = set()
        
        # Check added adapter files
        for file_change in file_context.adapter_files:
            if file_change.status.value == 'added':
                # Check for new adapter implementation
                match = re.match(r'adapters/([^/]+)/\1\.go$', file_change.path)
                if match:
                    new_adapter_dirs.add(match.group(1))
        
        # Check added config files
        for file_change in file_context.config_files:
            if file_change.status.value == 'added':
                # Check for new bidder config
                match = re.match(r'static/bidder-info/([^/]+)\.yaml$', file_change.path)
                if match:
                    new_adapter_dirs.add(match.group(1))
        
        if new_adapter_dirs:
            return DetectionResult(
                detected=True,
                metadata={'adapters': list(new_adapter_dirs), 'type': 'go_bidder'},
                reason=f"New Go bidder adapter: {len(new_adapter_dirs)} adapters created"
            )
        
        return DetectionResult(detected=False, reason="No new Go bidder adapters found")
    
    def _detect_js_alias(self, file_context) -> DetectionResult:
        """Detect JavaScript bid adapter aliases."""
        # Look for modifications to BidAdapter files
        for file_change in file_context.adapter_files:
            if (file_change.status.value == 'modified' and 
                'modules/' in file_change.path and 
                'BidAdapter.js' in file_change.path):
                
                patch = file_change.patch or ''
                if patch and self._has_js_alias_patterns(patch, file_change.path):
                    return DetectionResult(
                        detected=True,
                        metadata={'file': file_change.path, 'type': 'js_alias'},
                        reason=f"JS alias addition detected in {file_change.path}"
                    )
        
        return DetectionResult(detected=False, reason="No JS alias patterns found")
    
    def _has_js_alias_patterns(self, patch: str, file_path: str) -> bool:
        """Check for JavaScript alias patterns in BidAdapter patches."""
        # Pattern 1: Adding to ALIASES array with objects
        # { code: 'aliasname', gvlid: 123 }
        if re.search(r'^\+.*\{\s*code:\s*[\'\"][\w-]+[\'\"].*\}', patch, re.MULTILINE):
            return True
        
        # Pattern 2: Adding to aliases property (simple array)
        # aliases: ['alias1', 'alias2']
        if re.search(r'^\+.*aliases:\s*\[.*[\'\"][\w-]+[\'\"].*\]', patch, re.MULTILINE):
            return True
        
        # Pattern 3: Adding individual alias strings to existing array
        # + 'newalias',
        if re.search(r'^\+\s*[\'\"][\w-]+[\'\"]\s*,?\s*$', patch, re.MULTILINE):
            # Additional check: make sure we're in an aliases context
            if 'aliases' in patch.lower() or 'ALIASES' in patch:
                return True
        
        # Pattern 4: Adding to BASE_URLS or ENDPOINTS objects for aliases
        # aliasname: 'https://...',
        if re.search(r'^\+\s*[\w-]+:\s*[\'\"]https?://[^\'\"]+[\'\"]\s*,?\s*$', patch, re.MULTILINE):
            # Check if this is in context of URL mappings
            if any(keyword in patch for keyword in ['BASE_URLS', 'ENDPOINTS', 'endpoints', 'baseUrl']):
                return True
        
        # Pattern 5: Updates to endpoint selection logic for aliases
        # ENDPOINTS[bidderCode] or similar patterns
        if '+' in patch and re.search(r'ENDPOINTS\[.*\]|baseEndpoint.*bidderCode', patch):
            return True
        
        return False
    
    def _detect_java_new_adapter(self, file_context) -> DetectionResult:
        """Detect new Java adapters (including aliases)."""
        # Check for alias configurations first (most common)
        alias_result = self._detect_java_alias(file_context)
        if alias_result.detected:
            return alias_result
        
        # Check for new bidder implementations
        bidder_result = self._detect_java_bidder_adapter(file_context)
        if bidder_result.detected:
            return bidder_result
        
        return DetectionResult(detected=False, reason="No new Java adapters found")
    
    def _detect_java_alias(self, file_context) -> DetectionResult:
        """Detect Java adapter aliases."""
        # Check test files for alias configs (test-application.properties)
        for file_change in file_context.test_files:
            if 'test-application.properties' in file_change.path:
                patch = file_change.patch or ''
                if patch and self._has_java_alias_properties(patch):
                    return DetectionResult(
                        detected=True,
                        metadata={'file': file_change.path, 'type': 'java_alias_properties'},
                        reason=f"Java alias configuration in {file_change.path}"
                    )
        
        # Check config files for YAML bidder-config alias additions
        for file_change in file_context.config_files:
            if 'src/main/resources/bidder-config/' in file_change.path and file_change.path.endswith('.yaml'):
                patch = file_change.patch or ''
                if patch and self._has_java_alias_yaml(patch):
                    return DetectionResult(
                        detected=True,
                        metadata={'file': file_change.path, 'type': 'java_alias_yaml'},
                        reason=f"Java alias YAML configuration in {file_change.path}"
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
    
    def _detect_java_bidder_adapter(self, file_context) -> DetectionResult:
        """Detect new Java bidder adapters (full implementations)."""
        # Check for existing bidder file modifications (indicates update, not new)
        modified_bidder_files = [fc.path for fc in file_context.adapter_files 
                               if fc.status.value == 'modified' and 
                               'src/main/java/org/prebid/server/bidder/' in fc.path and 'Bidder.java' in fc.path]
        
        new_bidder_files = [fc.path for fc in file_context.adapter_files 
                          if fc.status.value == 'added' and 
                          'src/main/java/org/prebid/server/bidder/' in fc.path and 'Bidder.java' in fc.path]
        
        # If modifying existing bidder files, it's likely an update
        if modified_bidder_files and not new_bidder_files:
            return DetectionResult(detected=False, reason="Existing bidder files modified (update, not new)")
        
        # Count new bidder-related files (adapter + config files)
        all_new_bidder_files = []
        all_new_bidder_files.extend(new_bidder_files)
        
        # Add new config files
        config_files = [fc.path for fc in file_context.config_files 
                       if fc.status.value == 'added' and 
                       'src/main/resources/bidder-config/' in fc.path and fc.path.endswith('.yaml')]
        all_new_bidder_files.extend(config_files)
        
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
        # Create file context from pr_info
        context_manager = FileContextManager()
        file_context = context_manager.create_file_context(pr_info)
        
        # Gather all test/build/docs files from categorized context
        test_build_docs_files = []
        test_build_docs_files.extend([fc.path for fc in file_context.test_files])
        test_build_docs_files.extend([fc.path for fc in file_context.build_files])
        test_build_docs_files.extend([fc.path for fc in file_context.doc_files])
        
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
        # Create file context from pr_info
        context_manager = FileContextManager()
        file_context = context_manager.create_file_context(pr_info)
        
        if not self._is_adapter_or_module_change(file_context):
            return DetectionResult(detected=False, reason="Not an adapter/module change")
        
        is_new_feature = self._is_new_feature_change(file_context)
        
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
    
    def _is_adapter_or_module_change(self, file_context: FileContext) -> bool:
        """Check if PR affects adapter/module files."""
        return len(file_context.adapter_files) > 0
    
    def _is_new_feature_change(self, file_context: FileContext) -> bool:
        """Determine if this is a new feature based on file creation vs modification."""
        # Count added vs modified files across all categories
        all_files = (
            file_context.adapter_files + file_context.test_files + file_context.config_files +
            file_context.core_files + file_context.build_files + file_context.doc_files + file_context.other_files
        )
        
        added_files = sum(1 for fc in all_files if fc.status.value == 'added')
        modified_files = sum(1 for fc in all_files if fc.status.value == 'modified')
        
        return added_files > modified_files


class CoreChangesDetector(BaseDetector):
    """Detector for core system changes (features vs updates)."""
    
    def __init__(self, is_feature: bool = False):
        self.is_feature = is_feature
    
    def get_category_name(self) -> str:
        return "Core Features" if self.is_feature else "Core Updates"
    
    def detect(self, pr_info) -> DetectionResult:
        """Detect core changes and determine if feature or update."""
        # Create file context from pr_info
        context_manager = FileContextManager()
        file_context = context_manager.create_file_context(pr_info)
        
        if not self._is_core_change(file_context):
            return DetectionResult(detected=False, reason="Not a core change")
        
        is_new_feature = self._is_new_feature_change(file_context)
        
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
    
    def _is_core_change(self, file_context: FileContext) -> bool:
        """Check if PR affects core system files."""
        return len(file_context.core_files) > 0
    
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