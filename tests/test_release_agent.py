"""Tests for GitHub Release Analysis Agent."""

import pytest
from unittest.mock import Mock, patch
from dotenv import load_dotenv

from agents_playground.github_release_agent import GitHubReleaseAgent, PRInfo

load_dotenv()


def test_release_agent_initialization():
    """Test that the release agent initializes correctly."""
    agent = GitHubReleaseAgent()
    assert agent.config.name == "GitHubReleaseAnalyzer"
    assert agent.config.model == "gemini-2.0-flash-exp"
    assert agent.github is not None
    assert agent.gemini_agent is not None


def test_pr_info_dataclass():
    """Test PRInfo dataclass creation."""
    pr_info = PRInfo(
        number=123,
        title="Test PR",
        body="Test description",
        author="testuser",
        labels=["bug", "urgent"],
        merged_at=None,
        url="https://github.com/test/repo/pull/123",
        commits_count=3,
        additions=50,
        deletions=10,
        changed_files=5
    )
    
    assert pr_info.number == 123
    assert pr_info.title == "Test PR"
    assert len(pr_info.labels) == 2


def test_categorize_prs():
    """Test PR categorization logic."""
    agent = GitHubReleaseAgent()
    
    prs = [
        PRInfo(1, "feat: Add new feature", "", "user1", ["feature"], None, "", 1, 10, 0, 1),
        PRInfo(2, "fix: Bug fix", "", "user2", ["bug"], None, "", 1, 5, 2, 1),
        PRInfo(3, "docs: Update README", "", "user3", ["documentation"], None, "", 1, 3, 0, 1),
        PRInfo(4, "refactor: Code cleanup", "", "user4", [], None, "", 1, 0, 5, 2),
        PRInfo(5, "Add unit tests", "", "user5", ["test"], None, "", 1, 15, 0, 3),
    ]
    
    categories = agent._categorize_prs(prs)
    
    # Check that categorization works correctly
    assert "Features" in categories
    assert "Bug Fixes" in categories  
    assert "Documentation" in categories
    assert "Refactoring" in categories
    assert "Tests" in categories
    
    # Verify specific categorizations
    feature_pr = next(pr for pr in categories["Features"] if pr.number == 1)
    assert feature_pr.title == "feat: Add new feature"
    
    bug_pr = next(pr for pr in categories["Bug Fixes"] if pr.number == 2)
    assert bug_pr.title == "fix: Bug fix"


def test_extract_pr_numbers_from_commit():
    """Test PR number extraction from commit messages."""
    agent = GitHubReleaseAgent()
    
    # Mock commit object
    mock_commit = Mock()
    mock_commit.commit.message = "Merge pull request #123 from user/branch"
    
    pr_numbers = agent._extract_pr_numbers_from_commit(mock_commit)
    assert 123 in pr_numbers
    
    # Test different patterns
    mock_commit.commit.message = "Fix issue (#456) and resolve PR #789"
    pr_numbers = agent._extract_pr_numbers_from_commit(mock_commit)
    assert 456 in pr_numbers
    assert 789 in pr_numbers


def test_respond_format_validation():
    """Test the respond method input format validation."""
    agent = GitHubReleaseAgent()
    
    # Test invalid format
    response = agent.respond("invalid-format")
    assert "Please provide input in format" in response
    
    # Test valid format (will fail at API level but format is correct)
    with patch.object(agent, 'analyze_release') as mock_analyze:
        mock_analyze.side_effect = Exception("API Error")
        response = agent.respond("owner/repo:v1.0.0")
        assert "Error analyzing release" in response


@pytest.mark.integration
def test_real_github_integration():
    """Integration test with real GitHub API (requires GITHUB_TOKEN)."""
    import os
    
    if not os.getenv("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not available for integration test")
    
    agent = GitHubReleaseAgent()
    
    # Test with a small, known repository and release
    # Using a public repo with a known release
    try:
        # Test format validation first
        response = agent.respond("octocat/Hello-World:test")
        # Should either succeed or fail gracefully
        assert len(response) > 0
    except Exception as e:
        # Expected for non-existent releases, but should not crash
        assert "Error analyzing release" in str(e) or "not found" in str(e).lower()


def test_pr_info_extraction():
    """Test PR information extraction logic."""
    agent = GitHubReleaseAgent()
    
    # Mock PR object
    mock_pr = Mock()
    mock_pr.number = 123
    mock_pr.title = "Test PR"
    mock_pr.body = "This is a test PR"
    mock_pr.user.login = "testuser"
    mock_pr.labels = [Mock(name="bug"), Mock(name="urgent")]
    mock_pr.merged_at = None
    mock_pr.html_url = "https://github.com/test/repo/pull/123"
    mock_pr.commits = 3
    mock_pr.additions = 50
    mock_pr.deletions = 10
    mock_pr.changed_files = 5
    
    pr_info = agent._extract_pr_info(mock_pr)
    
    assert pr_info.number == 123
    assert pr_info.title == "Test PR"
    assert pr_info.author == "testuser"
    assert len(pr_info.labels) == 2
    assert pr_info.commits_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])