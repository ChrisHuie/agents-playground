"""Debug GitHub token authentication."""

import os
import requests
from dotenv import load_dotenv


def debug_github_token():
    """Debug GitHub token authentication with detailed output."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("❌ GITHUB_TOKEN not found in environment")
        return
    
    print(f"✅ GITHUB_TOKEN loaded (length: {len(token)})")
    print(f"✅ Token starts with: {token[:4]}...")
    
    # Test different authentication methods
    auth_methods = [
        ("Bearer token", {"Authorization": f"Bearer {token}"}),
        ("Token auth", {"Authorization": f"token {token}"}),
        ("Basic auth", {"Authorization": f"Basic {token}"}),
    ]
    
    for method_name, headers in auth_methods:
        print(f"\n🔍 Testing {method_name}:")
        headers["Accept"] = "application/vnd.github.v3+json"
        headers["User-Agent"] = "agents-playground-test"
        
        try:
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ Success! User: {user_data.get('login')}")
                print(f"   Scopes: {response.headers.get('X-OAuth-Scopes', 'None')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Test rate limiting endpoint (doesn't require auth)
    print(f"\n🔍 Testing rate limit endpoint (no auth required):")
    try:
        response = requests.get("https://api.github.com/rate_limit", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ GitHub API is accessible")
        else:
            print(f"   ❌ GitHub API issue: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Network error: {str(e)}")
    
    return False


if __name__ == "__main__":
    success = debug_github_token()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your GitHub token is a Personal Access Token (PAT)")
        print("2. Check that the token has appropriate scopes (repo, user, etc.)")
        print("3. Verify the token hasn't expired")
        print("4. Try generating a new token at: https://github.com/settings/tokens")