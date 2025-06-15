"""Tests for PRFileAnalyzer - Comprehensive test scenarios for PR file analysis."""

import pytest
from dataclasses import dataclass
from typing import Dict, List
from unittest.mock import Mock

from src.agents_playground.file_context import (
    PRFileAnalyzer, EnrichedFileChange, FileStatus, FileChange
)


@dataclass
class MockPRInfo:
    """Mock PR info object for testing."""
    file_changes: Dict = None
    files: List[str] = None

    def __post_init__(self):
        if self.file_changes is None:
            self.file_changes = {}
        if self.files is None:
            self.files = []


class MockGitHubFile:
    """Mock GitHub file object."""
    def __init__(self, filename: str, status: str, additions: int = 0, deletions: int = 0, patch: str = None):
        self.filename = filename
        self.status = status
        self.additions = additions
        self.deletions = deletions
        self.patch = patch


class MockGitHubPR:
    """Mock GitHub PR object."""
    def __init__(self, files: List[MockGitHubFile]):
        self._files = files
    
    def get_files(self):
        return iter(self._files)


class TestPRFileAnalyzer:
    """Test suite for PRFileAnalyzer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = PRFileAnalyzer()

    def test_javascript_new_adapter_pr(self):
        """Test JS PR with new adapter and associated files."""
        # Mock a typical new JS adapter PR
        github_files = [
            MockGitHubFile("modules/exampleBidAdapter.js", "added", 150, 0, "new adapter code"),
            MockGitHubFile("test/spec/modules/exampleBidAdapter_spec.js", "added", 80, 0, "test code"),
            MockGitHubFile("integrationExamples/gpt/example.html", "modified", 5, 0, "example update"),
            MockGitHubFile(".github/workflows/ci.yml", "modified", 2, 1, "ci update")
        ]
        github_pr = MockGitHubPR(github_files)
        
        # Analyze the PR
        enriched_files = self.analyzer.analyze_pr(github_pr, 'github_api')
        
        # Verify results
        assert len(enriched_files) == 4
        
        # Check categorization
        categories = {f.path: f.category for f in enriched_files}
        assert categories["modules/exampleBidAdapter.js"] == "adapter"
        assert categories["test/spec/modules/exampleBidAdapter_spec.js"] == "adapter"  # Module-specific test
        assert categories["integrationExamples/gpt/example.html"] == "doc"
        assert categories[".github/workflows/ci.yml"] == "build"
        
        # Check file status and metrics
        adapter_file = next(f for f in enriched_files if f.path == "modules/exampleBidAdapter.js")
        assert adapter_file.status == FileStatus.ADDED
        assert adapter_file.additions == 150
        assert adapter_file.deletions == 0

    def test_go_module_vs_core_pr(self):
        """Test Go PR distinguishing between modules and core changes."""
        pr_info = MockPRInfo(file_changes={
            "modules/fiftyonedegrees/devicedetection/detection.go": {
                "status": "added", "additions": 200, "deletions": 0, "patch": "module code"
            },
            "modules/prebid/ortb2blocking/ortb2.go": {
                "status": "modified", "additions": 20, "deletions": 5, "patch": "core module update"
            },
            "modules/generator/main.go": {
                "status": "modified", "additions": 10, "deletions": 2, "patch": "generator update"
            },
            "endpoints/openrtb2/openrtb2.go": {
                "status": "modified", "additions": 15, "deletions": 8, "patch": "core endpoint"
            }
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        
        categories = {f.path: f.category for f in enriched_files}
        assert categories["modules/fiftyonedegrees/devicedetection/detection.go"] == "adapter"  # Third-party module
        assert categories["modules/prebid/ortb2blocking/ortb2.go"] == "core"  # Prebid core module
        assert categories["modules/generator/main.go"] == "core"  # Core infrastructure
        assert categories["endpoints/openrtb2/openrtb2.go"] == "core"  # Core endpoint

    def test_java_bidder_and_tests_pr(self):
        """Test Java PR with bidder implementation and tests."""
        pr_info = MockPRInfo(file_changes={
            "src/main/java/org/prebid/server/bidder/example/ExampleBidder.java": {
                "status": "added", "additions": 300, "deletions": 0, "patch": "bidder impl"
            },
            "src/main/resources/bidder-config/example.yaml": {
                "status": "added", "additions": 25, "deletions": 0, "patch": "bidder config"
            },
            "src/test/java/org/prebid/server/bidder/example/ExampleBidderTest.java": {
                "status": "added", "additions": 150, "deletions": 0, "patch": "unit tests"
            },
            "src/test/java/org/prebid/server/it/ExampleIT.java": {
                "status": "added", "additions": 100, "deletions": 0, "patch": "integration tests"
            },
            "src/test/java/org/prebid/server/auction/AuctionTest.java": {
                "status": "modified", "additions": 5, "deletions": 2, "patch": "general test"
            }
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        
        categories = {f.path: f.category for f in enriched_files}
        assert categories["src/main/java/org/prebid/server/bidder/example/ExampleBidder.java"] == "adapter"
        assert categories["src/main/resources/bidder-config/example.yaml"] == "adapter"
        assert categories["src/test/java/org/prebid/server/bidder/example/ExampleBidderTest.java"] == "adapter"
        assert categories["src/test/java/org/prebid/server/it/ExampleIT.java"] == "adapter"  # Integration tests
        assert categories["src/test/java/org/prebid/server/auction/AuctionTest.java"] == "test"  # General test

    def test_javascript_library_utils_classification(self):
        """Test JS library utils classification (core vs adapter)."""
        pr_info = MockPRInfo(file_changes={
            "libraries/currencyUtils/currency.js": {
                "status": "modified", "additions": 10, "deletions": 5, "patch": "core util"
            },
            "libraries/adtelligentUtils/helper.js": {
                "status": "added", "additions": 50, "deletions": 0, "patch": "vendor util"
            },
            "libraries/urlUtils/url.js": {
                "status": "modified", "additions": 8, "deletions": 2, "patch": "core util"
            },
            "libraries/chunk/chunk.js": {
                "status": "modified", "additions": 15, "deletions": 3, "patch": "non-utils lib"
            }
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        
        categories = {f.path: f.category for f in enriched_files}
        assert categories["libraries/currencyUtils/currency.js"] == "core"  # Core exception
        assert categories["libraries/adtelligentUtils/helper.js"] == "adapter"  # Vendor utils
        assert categories["libraries/urlUtils/url.js"] == "core"  # Core exception
        assert categories["libraries/chunk/chunk.js"] == "core"  # Non-utils library

    def test_build_and_config_files_pr(self):
        """Test PR with various build and configuration files."""
        pr_info = MockPRInfo(file_changes={
            ".github/workflows/test.yml": {
                "status": "modified", "additions": 5, "deletions": 2, "patch": "ci update"
            },
            ".eslintrc.js": {
                "status": "modified", "additions": 3, "deletions": 1, "patch": "lint config"
            },
            "babel.config.js": {
                "status": "added", "additions": 20, "deletions": 0, "patch": "babel config"
            },
            "wdio.conf.js": {
                "status": "modified", "additions": 8, "deletions": 4, "patch": "test config"
            },
            "browsers.json": {
                "status": "modified", "additions": 2, "deletions": 0, "patch": "browser config"
            },
            "README.md": {
                "status": "modified", "additions": 10, "deletions": 3, "patch": "docs update"
            }
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        
        categories = {f.path: f.category for f in enriched_files}
        assert categories[".github/workflows/test.yml"] == "build"
        assert categories[".eslintrc.js"] == "build"
        assert categories["babel.config.js"] == "build"
        assert categories["wdio.conf.js"] == "build"
        assert categories["browsers.json"] == "build"
        assert categories["README.md"] == "doc"

    def test_get_summary_by_category(self):
        """Test summary statistics generation."""
        pr_info = MockPRInfo(file_changes={
            "modules/adapter1.js": {"status": "added", "additions": 100, "deletions": 0},
            "modules/adapter2.js": {"status": "modified", "additions": 20, "deletions": 10},
            "test/spec/modules/adapter1_spec.js": {"status": "added", "additions": 50, "deletions": 0},
            "src/core.js": {"status": "modified", "additions": 15, "deletions": 5},
            ".github/ci.yml": {"status": "modified", "additions": 3, "deletions": 1}
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        summary = self.analyzer.get_summary_by_category(enriched_files)
        
        # Check adapter category
        assert summary["adapter"]["files"] == 3  # 2 adapters + 1 test
        assert summary["adapter"]["added"] == 2  # adapter1 + test
        assert summary["adapter"]["modified"] == 1  # adapter2
        assert summary["adapter"]["total_additions"] == 170  # 100 + 20 + 50
        assert summary["adapter"]["total_deletions"] == 10
        
        # Check core category
        assert summary["core"]["files"] == 1
        assert summary["core"]["modified"] == 1
        assert summary["core"]["total_additions"] == 15
        
        # Check build category
        assert summary["build"]["files"] == 1
        assert summary["build"]["modified"] == 1

    def test_empty_pr(self):
        """Test handling of empty PR."""
        pr_info = MockPRInfo()
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        assert enriched_files == []
        
        summary = self.analyzer.get_summary_by_category(enriched_files)
        assert summary == {}

    def test_unknown_repo_type(self):
        """Test handling of unknown repository type."""
        pr_info = MockPRInfo(file_changes={
            "some/random/file.xyz": {"status": "added", "additions": 10, "deletions": 0}
        })
        
        enriched_files = self.analyzer.analyze_pr(pr_info, 'dict')
        assert len(enriched_files) == 1
        assert enriched_files[0].category == "other"

    def test_mixed_repository_changes(self):
        """Test PR with changes across different categories."""
        github_files = [
            # Adapter changes
            MockGitHubFile("modules/newAdapter.js", "added", 200, 0),
            MockGitHubFile("test/spec/modules/newAdapter_spec.js", "added", 100, 0),
            
            # Core changes  
            MockGitHubFile("src/auction.js", "modified", 25, 8),
            MockGitHubFile("libraries/currencyUtils/currency.js", "modified", 15, 5),
            
            # Build changes
            MockGitHubFile(".github/workflows/build.yml", "modified", 10, 2),
            MockGitHubFile("package.json", "modified", 3, 1),
            
            # Documentation
            MockGitHubFile("docs/getting-started.md", "modified", 20, 5),
            MockGitHubFile("integrationExamples/basic.html", "added", 50, 0)
        ]
        github_pr = MockGitHubPR(github_files)
        
        enriched_files = self.analyzer.analyze_pr(github_pr, 'github_api')
        summary = self.analyzer.get_summary_by_category(enriched_files)
        
        # Verify each category has expected counts
        assert summary["adapter"]["files"] == 2  # adapter + test
        assert summary["core"]["files"] == 2    # auction + currencyUtils
        assert summary["build"]["files"] == 2   # github + package.json
        assert summary["doc"]["files"] == 2     # docs + examples
        
        # Verify status distribution
        assert summary["adapter"]["added"] == 2
        assert summary["core"]["modified"] == 2
        assert summary["build"]["modified"] == 2
        assert summary["doc"]["added"] == 1
        assert summary["doc"]["modified"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])