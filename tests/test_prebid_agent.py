"""Tests for Prebid Release Analysis Agent."""

import pytest
from unittest.mock import Mock, patch
from dotenv import load_dotenv

from agents_playground.prebid_agent import PrebidReleaseAgent

load_dotenv()


def test_prebid_agent_initialization():
    """Test that the Prebid agent initializes correctly."""
    agent = PrebidReleaseAgent()
    assert agent.config.name == "PrebidReleaseAnalyzer"
    assert len(agent.PREBID_REPOS) == 5
    assert "js" in agent.PREBID_REPOS
    assert "server-go" in agent.PREBID_REPOS


def test_prebid_repo_shortcuts():
    """Test Prebid repository shortcuts mapping."""
    agent = PrebidReleaseAgent()
    
    expected_repos = {
        "js": "prebid/Prebid.js",
        "server-go": "prebid/prebid-server", 
        "server-java": "prebid/prebid-server-java",
        "ios": "prebid/prebid-mobile-ios",
        "android": "prebid/prebid-mobile-android"
    }
    
    assert agent.PREBID_REPOS == expected_repos


def test_prebid_input_parsing():
    """Test parsing of Prebid-specific input formats."""
    agent = PrebidReleaseAgent()
    
    # Mock the latest release fetching
    with patch.object(agent, '_get_latest_release_tag') as mock_latest:
        mock_latest.return_value = "v8.0.0"
        
        # Test shortcut only (should get latest)
        repo, tag = agent._parse_prebid_input("js")
        assert repo == "prebid/Prebid.js"
        assert tag == "v8.0.0"
    
    # Test shortcut with colon format
    repo, tag = agent._parse_prebid_input("server-go:v3.18.0")
    assert repo == "prebid/prebid-server"
    assert tag == "v3.18.0"
    
    # Test shortcut with space format
    repo, tag = agent._parse_prebid_input("ios v2.1.0")
    assert repo == "prebid/prebid-mobile-ios"
    assert tag == "v2.1.0"


def test_invalid_shortcut():
    """Test handling of invalid shortcuts."""
    agent = PrebidReleaseAgent()
    
    with pytest.raises(ValueError):
        agent._parse_prebid_input("invalid_shortcut")


def test_list_prebid_repos():
    """Test listing of Prebid repositories."""
    agent = PrebidReleaseAgent()
    
    with patch.object(agent, '_get_latest_release_tag') as mock_latest:
        mock_latest.return_value = "v1.0.0"
        
        result = agent.list_prebid_repos()
        
        assert "Available Prebid Repository Shortcuts" in result
        assert "js" in result
        assert "server-go" in result
        assert "Usage Examples" in result


def test_analyze_latest():
    """Test analyzing latest release."""
    agent = PrebidReleaseAgent()
    
    # Test invalid shortcut
    result = agent.analyze_latest("invalid")
    assert "Unknown repository shortcut" in result
    
    # Test valid shortcut (mock the actual analysis)
    with patch.object(agent, 'respond') as mock_respond:
        mock_respond.return_value = "Mocked analysis"
        
        result = agent.analyze_latest("js")
        assert result == "Mocked analysis"
        mock_respond.assert_called_once_with("js")


def test_compare_releases():
    """Test release comparison functionality."""
    agent = PrebidReleaseAgent()
    
    # Test invalid shortcut
    result = agent.compare_releases("invalid", "v1.0.0", "v2.0.0")
    assert "Unknown repository shortcut" in result
    
    # Test valid comparison (mock the analysis)
    with patch.object(agent, 'analyze_release') as mock_analyze:
        mock_analysis1 = Mock()
        mock_analysis1.repo_name = "prebid/Prebid.js"
        mock_analysis1.release_tag = "v7.0.0"
        mock_analysis1.total_prs = 10
        mock_analysis1.categories = {"Features": [], "Bug Fixes": []}
        
        mock_analysis2 = Mock()
        mock_analysis2.repo_name = "prebid/Prebid.js"
        mock_analysis2.release_tag = "v8.0.0"
        mock_analysis2.total_prs = 15
        mock_analysis2.categories = {"Features": [], "Bug Fixes": [], "Tests": []}
        
        mock_analyze.side_effect = [mock_analysis1, mock_analysis2]
        
        result = agent.compare_releases("js", "v7.0.0", "v8.0.0")
        
        assert "Release Comparison" in result
        assert "v7.0.0 vs v8.0.0" in result
        assert "10 vs 15 (+5)" in result


@pytest.mark.integration
def test_real_prebid_integration():
    """Integration test with real Prebid repositories."""
    import os
    
    if not os.getenv("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not available for integration test")
    
    agent = PrebidReleaseAgent()
    
    # Test getting latest release tag (should not fail)
    try:
        latest_tag = agent._get_latest_release_tag("prebid/prebid-server")
        assert latest_tag is not None
        assert len(latest_tag) > 0
    except Exception as e:
        pytest.fail(f"Failed to get latest release: {e}")


def test_convenience_functions():
    """Test convenience functions."""
    from agents_playground.prebid_agent import analyze_prebid_latest, list_prebid_repos, analyze_prebid_release
    
    # Mock the actual analysis to avoid API calls
    with patch('agents_playground.prebid_agent.PrebidReleaseAgent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # Test analyze_prebid_latest
        mock_agent.analyze_latest.return_value = "Latest analysis"
        result = analyze_prebid_latest("js")
        assert result == "Latest analysis"
        
        # Test list_prebid_repos
        mock_agent.list_prebid_repos.return_value = "Repo list"
        result = list_prebid_repos()
        assert result == "Repo list"
        
        # Test analyze_prebid_release with tag
        mock_agent.respond.return_value = "Analysis with tag"
        result = analyze_prebid_release("server", "v3.18.0")
        assert result == "Analysis with tag"
        mock_agent.respond.assert_called_with("server:v3.18.0")
        
        # Test analyze_prebid_release without tag
        mock_agent.respond.return_value = "Analysis without tag"
        result = analyze_prebid_release("js")
        assert result == "Analysis without tag"
        mock_agent.respond.assert_called_with("js")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])