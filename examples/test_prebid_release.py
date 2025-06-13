"""Test script for analyzing the prebid-server v3.18.0 release."""

from dotenv import load_dotenv
from agents_playground.github_release_agent import GitHubReleaseAgent

# Load environment variables
load_dotenv()


def test_prebid_release():
    """Test analysis of prebid-server v3.18.0 release."""
    print("🚀 Testing GitHub Release Analysis with prebid-server v3.18.0")
    print("=" * 60)
    
    agent = GitHubReleaseAgent()
    
    # Test all supported input formats
    test_formats = [
        "prebid/prebid-server:v3.18.0",
        "prebid/prebid-server v3.18.0", 
        "https://github.com/prebid/prebid-server/releases/tag/v3.18.0"
    ]
    
    print("🔍 Testing input format parsing:")
    for i, input_format in enumerate(test_formats, 1):
        try:
            repo, tag = agent._parse_input(input_format)
            print(f"{i}. ✅ '{input_format}' -> {repo}:{tag}")
        except Exception as e:
            print(f"{i}. ❌ '{input_format}' -> Error: {e}")
    
    print(f"\n📊 Analyzing prebid-server v3.18.0 release...")
    print("This may take a moment to fetch and analyze all PRs...\n")
    
    try:
        # Use the URL format as an example
        url = "https://github.com/prebid/prebid-server/releases/tag/v3.18.0"
        analysis = agent.respond(url)
        print(analysis)
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        print("\n💡 Possible issues:")
        print("- Check that your GITHUB_TOKEN is set in .env")
        print("- Verify the release exists at the GitHub URL")
        print("- Ensure you have internet connectivity")


if __name__ == "__main__":
    test_prebid_release()