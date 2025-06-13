"""Demo script for Prebid Release Analysis Agent."""

from dotenv import load_dotenv
from agents_playground.prebid_agent import PrebidReleaseAgent, list_prebid_repos, analyze_prebid_latest

# Load environment variables
load_dotenv()


def demo_prebid_shortcuts():
    """Demonstrate Prebid repository shortcuts."""
    print("🏗️ Prebid Release Analysis Agent Demo")
    print("=" * 50)
    
    agent = PrebidReleaseAgent()
    
    # Show available repositories
    print(agent.list_prebid_repos())
    
    print("\n" + "=" * 50)
    print("Choose an option:")
    print("1. Analyze latest release of a Prebid repo")
    print("2. Analyze specific release")
    print("3. Compare two releases")
    print("4. Interactive mode")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        demo_latest_release(agent)
    elif choice == "2":
        demo_specific_release(agent)
    elif choice == "3":
        demo_compare_releases(agent)
    elif choice == "4":
        demo_interactive_mode(agent)
    else:
        print("❌ Invalid choice")


def demo_latest_release(agent):
    """Demo analyzing latest releases."""
    print("\n🚀 Analyzing Latest Releases")
    print("-" * 30)
    
    repo = input("Enter repo shortcut (js, server-go, server-java, ios, android): ").strip()
    
    if repo:
        print(f"\n📊 Analyzing latest {repo} release...")
        try:
            result = agent.respond(repo)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_specific_release(agent):
    """Demo analyzing specific releases."""
    print("\n🎯 Analyzing Specific Release")
    print("-" * 30)
    
    repo = input("Enter repo shortcut (js, server, server-java, ios, android): ").strip()
    tag = input("Enter release tag (e.g., v3.18.0): ").strip()
    
    if repo and tag:
        print(f"\n📊 Analyzing {repo} {tag}...")
        try:
            result = agent.respond(f"{repo}:{tag}")
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_compare_releases(agent):
    """Demo comparing releases."""
    print("\n🔄 Comparing Releases")
    print("-" * 30)
    
    repo = input("Enter repo shortcut (js, server, server-java, ios, android): ").strip()
    tag1 = input("Enter first release tag: ").strip()
    tag2 = input("Enter second release tag: ").strip()
    
    if repo and tag1 and tag2:
        print(f"\n📊 Comparing {repo} {tag1} vs {tag2}...")
        try:
            result = agent.compare_releases(repo, tag1, tag2)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_interactive_mode(agent):
    """Interactive mode for testing different inputs."""
    print("\n🤖 Interactive Prebid Analysis")
    print("-" * 30)
    
    print("Examples:")
    print("- 'js' (latest Prebid.js)")
    print("- 'server:v3.18.0' (specific prebid-server)")
    print("- 'ios v2.1.0' (specific iOS release)")
    print("- 'list' (show available repos)")
    print("- 'quit' (exit)")
    
    while True:
        command = input("\nEnter command: ").strip()
        
        if command.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break
        elif command.lower() == "list":
            print(agent.list_prebid_repos())
        elif command:
            try:
                result = agent.respond(command)
                print(result)
            except Exception as e:
                print(f"❌ Error: {e}")


def demo_quick_examples():
    """Quick examples of different usage patterns."""
    print("🚀 Quick Prebid Examples")
    print("=" * 50)
    
    agent = PrebidReleaseAgent()
    
    examples = [
        ("Latest Prebid.js", "js"),
        ("Specific prebid-server", "server:v3.18.0"),
        ("Latest iOS release", "ios")
    ]
    
    for description, command in examples:
        print(f"\n📊 {description}: '{command}'")
        try:
            # Just show parsing, not full analysis for demo
            repo, tag = agent._parse_prebid_input(command)
            print(f"   → Parsed as: {repo}:{tag}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("🏗️ Prebid Release Analysis Agent")
    print("=" * 50)
    
    mode = input("Choose demo mode:\n1. Interactive demo\n2. Quick examples\n\nEnter choice (1-2): ").strip()
    
    if mode == "1":
        demo_prebid_shortcuts()
    elif mode == "2":
        demo_quick_examples()
    else:
        print("❌ Invalid choice. Running interactive demo...")
        demo_prebid_shortcuts()