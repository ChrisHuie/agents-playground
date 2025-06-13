"""Demo script for multi-level summary analysis."""

from dotenv import load_dotenv
from agents_playground.prebid_agent import PrebidReleaseAgent

# Load environment variables
load_dotenv()


def demo_summary_levels():
    """Demonstrate different summary levels."""
    print("📊 Multi-Level Release Analysis Demo")
    print("=" * 50)
    
    agent = PrebidReleaseAgent()
    
    # Get repository and release
    print("Available repositories: js, server-go, server-java, ios, android")
    repo_input = input("Enter repository (e.g., 'server-go:v3.18.0' or 'js' for latest): ").strip()
    
    if not repo_input:
        repo_input = "server-go:v3.18.0"  # Default for demo
        print(f"Using default: {repo_input}")
    
    print(f"\n🔍 Analyzing {repo_input}...")
    print("This will generate 3 different summary levels...\n")
    
    try:
        # Get analysis object
        repo_name, release_tag = agent._parse_prebid_input(repo_input)
        analysis = agent.analyze_release(repo_name, release_tag)
        
        print("=" * 80)
        print("📋 EXECUTIVE SUMMARY (High-level overview)")
        print("=" * 80)
        print(analysis.executive_summary)
        
        print("\n" + "=" * 80)
        print("🎯 PRODUCT SUMMARY (Individual PR business impact)")
        print("=" * 80)
        print(analysis.product_summary)
        
        print("\n" + "=" * 80)
        print("⚙️ DEVELOPER SUMMARY (Technical implementation details)")
        print("=" * 80)
        print(analysis.developer_summary)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_specific_summary():
    """Demo getting specific summary levels."""
    print("\n📊 Specific Summary Level Demo")
    print("=" * 50)
    
    agent = PrebidReleaseAgent()
    
    repo_input = input("Enter repository: ").strip() or "server-go:v3.18.0"
    
    print("\nChoose summary level:")
    print("1. Executive (high-level overview)")
    print("2. Product (business impact per PR)")
    print("3. Developer (technical details per PR)")
    print("4. All levels")
    
    choice = input("Enter choice (1-4): ").strip()
    
    try:
        if choice == "1":
            result = agent.get_executive_summary(repo_input)
        elif choice == "2":
            result = agent.get_product_summary(repo_input)
        elif choice == "3":
            result = agent.get_developer_summary(repo_input)
        elif choice == "4":
            result = agent.get_all_summaries(repo_input)
        else:
            result = agent.get_executive_summary(repo_input)
        
        print(f"\n{result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def compare_summary_levels():
    """Compare how different summary levels analyze the same release."""
    print("\n📊 Summary Level Comparison")
    print("=" * 50)
    
    agent = PrebidReleaseAgent()
    
    repo_input = input("Enter repository: ").strip() or "server-go:v3.18.0"
    
    print(f"\n🔍 Comparing summary levels for {repo_input}...")
    
    try:
        # Get analysis
        repo_name, release_tag = agent._parse_prebid_input(repo_input)
        analysis = agent.analyze_release(repo_name, release_tag)
        
        print(f"\n📊 **Analysis Stats:**")
        print(f"- Repository: {analysis.repo_name}")
        print(f"- Release: {analysis.release_tag}")
        print(f"- Total PRs: {analysis.total_prs}")
        print(f"- Categories: {len(analysis.categories)}")
        
        # Executive summary length
        exec_words = len(analysis.executive_summary.split())
        prod_words = len(analysis.product_summary.split())
        dev_words = len(analysis.developer_summary.split())
        
        print(f"\n📏 **Summary Lengths:**")
        print(f"- Executive: {exec_words} words")
        print(f"- Product: {prod_words} words")
        print(f"- Developer: {dev_words} words")
        
        print(f"\n🎯 **Summary Focus:**")
        print("- Executive: Strategic overview, business impact, key highlights")
        print("- Product: Individual PR analysis, user impact, feature roadmap")
        print("- Developer: Technical implementation, architecture, code changes")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Multi-Level Release Analysis")
    print("=" * 50)
    
    mode = input("Choose demo mode:\n1. Full demo (all 3 levels)\n2. Specific level\n3. Compare levels\n\nEnter choice (1-3): ").strip()
    
    if mode == "1":
        demo_summary_levels()
    elif mode == "2":
        demo_specific_summary()
    elif mode == "3":
        compare_summary_levels()
    else:
        print("❌ Invalid choice. Running full demo...")
        demo_summary_levels()