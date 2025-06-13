"""Demo script for GitHub Release Analysis Agent."""

from dotenv import load_dotenv
from agents_playground.github_release_agent import GitHubReleaseAgent, quick_release_summary

# Load environment variables
load_dotenv()


def demo_release_analysis():
    """Demonstrate release analysis capabilities."""
    print("🚀 GitHub Release Analysis Agent Demo\n")
    
    # Example repositories and releases to analyze
    examples = [
        ("microsoft/vscode", "1.80.0"),
        ("facebook/react", "v18.2.0"),
        ("nodejs/node", "v20.0.0"),
        ("python/cpython", "v3.11.0"),
    ]
    
    agent = GitHubReleaseAgent()
    
    print("Select a repository and release to analyze:")
    for i, (repo, tag) in enumerate(examples, 1):
        print(f"{i}. {repo} - {tag}")
    print("5. Enter custom repo:tag")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice in ["1", "2", "3", "4"]:
        repo_name, release_tag = examples[int(choice) - 1]
    elif choice == "5":
        custom = input("Enter repo:tag (e.g., owner/repo:v1.0.0): ").strip()
        if ":" not in custom:
            print("❌ Invalid format. Use owner/repo:tag")
            return
        repo_name, release_tag = custom.split(":", 1)
    else:
        print("❌ Invalid choice")
        return
    
    print(f"\n🔍 Analyzing {repo_name} release {release_tag}...")
    print("This may take a moment...\n")
    
    try:
        # Use the agent to analyze the release
        response = agent.respond(f"{repo_name}:{release_tag}")
        print(response)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Tips:")
        print("- Make sure the repository and release tag exist")
        print("- Check that your GITHUB_TOKEN has appropriate permissions")
        print("- Some repositories may have many PRs, which can take time to analyze")


def demo_quick_analysis():
    """Demonstrate quick analysis function."""
    print("🚀 Quick Release Analysis Demo\n")
    
    # Analyze a smaller repository for faster demo
    repo_name = "anthropics/claude-code"  # Example - replace with actual repo
    release_tag = "v1.0.0"  # Example - replace with actual tag
    
    print(f"📊 Quick analysis of {repo_name} release {release_tag}:")
    
    try:
        summary = quick_release_summary(repo_name, release_tag)
        print(summary)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Note: Using example repo that may not exist. Try with a real repository.")


def demo_interactive_mode():
    """Interactive mode for testing different repositories."""
    print("🤖 Interactive GitHub Release Analysis\n")
    
    agent = GitHubReleaseAgent()
    
    while True:
        print("\nOptions:")
        print("1. Analyze a release (format: owner/repo:tag)")
        print("2. Exit")
        
        choice = input("\nWhat would you like to do? ").strip()
        
        if choice == "1":
            repo_input = input("Enter repository and tag (owner/repo:tag): ").strip()
            if not repo_input:
                continue
                
            print(f"\n🔍 Analyzing {repo_input}...")
            try:
                response = agent.respond(repo_input)
                print(response)
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
        elif choice == "2":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    print("🚀 GitHub Release Analysis Agent")
    print("=" * 50)
    
    demo_mode = input("Choose demo mode:\n1. Guided demo\n2. Quick demo\n3. Interactive mode\n\nEnter choice (1-3): ").strip()
    
    if demo_mode == "1":
        demo_release_analysis()
    elif demo_mode == "2":
        demo_quick_analysis()
    elif demo_mode == "3":
        demo_interactive_mode()
    else:
        print("❌ Invalid choice. Running guided demo...")
        demo_release_analysis()