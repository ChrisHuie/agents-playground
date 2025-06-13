"""Main entry point for agents playground."""

from agents_playground.agents import SimpleAgent


def main():
    """Run the agents playground."""
    print("🤖 Welcome to the Agents Playground!")
    
    agent = SimpleAgent()
    response = agent.respond("Hello, world!")
    print(f"Agent says: {response}")


if __name__ == "__main__":
    main()