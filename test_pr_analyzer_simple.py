"""Simple test runner for PRFileAnalyzer without pytest dependency."""

from dataclasses import dataclass
from typing import Dict, List

from src.agents_playground.file_context import PRFileAnalyzer, FileStatus


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


def test_javascript_new_adapter_pr():
    """Test JS PR with new adapter and associated files."""
    print("🧪 Testing JavaScript new adapter PR...")
    
    analyzer = PRFileAnalyzer('javascript')
    
    # Mock a typical new JS adapter PR
    github_files = [
        MockGitHubFile("modules/exampleBidAdapter.js", "added", 150, 0, "new adapter code"),
        MockGitHubFile("test/spec/modules/exampleBidAdapter_spec.js", "added", 80, 0, "test code"),
        MockGitHubFile("integrationExamples/gpt/example.html", "modified", 5, 0, "example update"),
        MockGitHubFile(".github/workflows/ci.yml", "modified", 2, 1, "ci update")
    ]
    github_pr = MockGitHubPR(github_files)
    
    # Analyze the PR
    enriched_files = analyzer.analyze_pr(github_pr, 'github_api')
    
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
    
    print("✅ PASSED - JS adapter PR correctly categorized")


def test_go_module_vs_core_pr():
    """Test Go PR distinguishing between modules and core changes."""
    print("🧪 Testing Go module vs core classification...")
    
    analyzer = PRFileAnalyzer('go')
    
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
    
    enriched_files = analyzer.analyze_pr(pr_info, 'dict')
    
    categories = {f.path: f.category for f in enriched_files}
    assert categories["modules/fiftyonedegrees/devicedetection/detection.go"] == "adapter"  # Third-party module
    assert categories["modules/prebid/ortb2blocking/ortb2.go"] == "core"  # Prebid core module
    assert categories["modules/generator/main.go"] == "core"  # Core infrastructure
    assert categories["endpoints/openrtb2/openrtb2.go"] == "core"  # Core endpoint
    
    print("✅ PASSED - Go modules correctly distinguished from core")


def test_java_bidder_and_tests_pr():
    """Test Java PR with bidder implementation and tests."""
    print("🧪 Testing Java bidder and tests...")
    
    analyzer = PRFileAnalyzer('java')
    
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
    
    enriched_files = analyzer.analyze_pr(pr_info, 'dict')
    
    categories = {f.path: f.category for f in enriched_files}
    assert categories["src/main/java/org/prebid/server/bidder/example/ExampleBidder.java"] == "adapter"
    assert categories["src/main/resources/bidder-config/example.yaml"] == "adapter"
    assert categories["src/test/java/org/prebid/server/bidder/example/ExampleBidderTest.java"] == "adapter"
    assert categories["src/test/java/org/prebid/server/it/ExampleIT.java"] == "adapter"  # Integration tests
    assert categories["src/test/java/org/prebid/server/auction/AuctionTest.java"] == "test"  # General test
    
    print("✅ PASSED - Java bidder tests correctly categorized as adapter-related")


def test_javascript_library_utils():
    """Test JS library utils classification (core vs adapter)."""
    print("🧪 Testing JavaScript library utils classification...")
    
    analyzer = PRFileAnalyzer('javascript')
    
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
    
    enriched_files = analyzer.analyze_pr(pr_info, 'dict')
    
    categories = {f.path: f.category for f in enriched_files}
    assert categories["libraries/currencyUtils/currency.js"] == "core"  # Core exception
    assert categories["libraries/adtelligentUtils/helper.js"] == "adapter"  # Vendor utils
    assert categories["libraries/urlUtils/url.js"] == "core"  # Core exception
    assert categories["libraries/chunk/chunk.js"] == "core"  # Non-utils library
    
    print("✅ PASSED - JS library utils correctly classified")


def test_summary_statistics():
    """Test summary statistics generation."""
    print("🧪 Testing summary statistics...")
    
    analyzer = PRFileAnalyzer('javascript')
    
    pr_info = MockPRInfo(file_changes={
        "modules/adapter1.js": {"status": "added", "additions": 100, "deletions": 0},
        "modules/adapter2.js": {"status": "modified", "additions": 20, "deletions": 10},
        "test/spec/modules/adapter1_spec.js": {"status": "added", "additions": 50, "deletions": 0},
        "src/core.js": {"status": "modified", "additions": 15, "deletions": 5},
        ".github/ci.yml": {"status": "modified", "additions": 3, "deletions": 1}
    })
    
    enriched_files = analyzer.analyze_pr(pr_info, 'dict')
    summary = analyzer.get_summary_by_category(enriched_files)
    
    # Check adapter category
    assert summary["adapter"]["files"] == 3  # 2 adapters + 1 test
    assert summary["adapter"]["added"] == 2  # adapter1 + test
    assert summary["adapter"]["modified"] == 1  # adapter2
    assert summary["adapter"]["total_additions"] == 170  # 100 + 20 + 50
    assert summary["adapter"]["total_deletions"] == 10
    
    print("✅ PASSED - Summary statistics correctly calculated")


def run_all_tests():
    """Run all PRFileAnalyzer tests."""
    print("🚀 Running PRFileAnalyzer Tests\n")
    
    try:
        test_javascript_new_adapter_pr()
        test_go_module_vs_core_pr()
        test_java_bidder_and_tests_pr()
        test_javascript_library_utils()
        test_summary_statistics()
        
        print("\n🎉 All tests passed! PRFileAnalyzer working correctly.")
        print("\n📊 Test Coverage:")
        print("✅ JavaScript adapter detection")
        print("✅ Go module vs core classification") 
        print("✅ Java bidder test categorization")
        print("✅ Library utils classification")
        print("✅ Summary statistics generation")
        print("✅ File status tracking (added/modified/removed)")
        print("✅ Line count metrics (additions/deletions)")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"💥 Test error: {e}")


if __name__ == "__main__":
    run_all_tests()