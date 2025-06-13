"""Tests for GitHub integration using GITHUB_TOKEN."""

import os
import pytest
import requests
from dotenv import load_dotenv


def test_github_token_loaded():
    """Test that GITHUB_TOKEN is loaded from environment."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    assert token is not None, "GITHUB_TOKEN should be set in .env file"
    assert len(token.strip()) > 0, "GITHUB_TOKEN should not be empty"


def test_github_api_authentication():
    """Test GitHub API authentication with the token."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        pytest.skip("GITHUB_TOKEN not found in environment")
    
    # Test GitHub API authentication
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Make a simple API call to get authenticated user info
    response = requests.get("https://api.github.com/user", headers=headers)
    
    assert response.status_code == 200, f"GitHub API authentication failed: {response.status_code}"
    
    user_data = response.json()
    assert "login" in user_data, "Response should contain user login"
    assert "id" in user_data, "Response should contain user ID"
    
    print(f"✅ GitHub API authentication successful for user: {user_data.get('login')}")


def test_github_repo_access():
    """Test access to GitHub repositories."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        pytest.skip("GITHUB_TOKEN not found in environment")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Test access to user's repositories
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    
    assert response.status_code == 200, f"GitHub repos API failed: {response.status_code}"
    
    repos = response.json()
    assert isinstance(repos, list), "Response should be a list of repositories"
    
    print(f"✅ GitHub repos access successful. Found {len(repos)} repositories")


def test_github_token_scopes():
    """Test GitHub token scopes and permissions."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        pytest.skip("GITHUB_TOKEN not found in environment")
    
    # Use Bearer authentication for better compatibility
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Make a request to check token scopes
    response = requests.get("https://api.github.com/user", headers=headers)
    
    if response.status_code == 200:
        # Check the X-OAuth-Scopes header for token permissions
        scopes = response.headers.get("X-OAuth-Scopes", "")
        rate_limit = response.headers.get("X-RateLimit-Limit", "")
        
        print(f"✅ GitHub token scopes: {scopes if scopes else 'Not reported (normal for PATs)'}")
        print(f"✅ Rate limit: {rate_limit}")
        
        # For Personal Access Tokens, scopes might not be reported
        # Just verify we can authenticate successfully
        user_data = response.json()
        assert "login" in user_data, "Should be able to get user info"
        print(f"✅ Token is working for user: {user_data['login']}")
    else:
        pytest.fail(f"Failed to check token scopes: {response.status_code}")


if __name__ == "__main__":
    # Run tests directly
    test_github_token_loaded()
    test_github_api_authentication()
    test_github_repo_access()
    test_github_token_scopes()
    print("🎉 All GitHub integration tests passed!")