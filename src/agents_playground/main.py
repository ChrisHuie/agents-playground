"""Main entry point for agents playground."""

from dotenv import load_dotenv
from agents_playground.agents import GeminiAgent, AgentConfig

# Load environment variables
load_dotenv()


def main():
    """Run the agents playground."""
    print("🤖 Welcome to the Agents Playground with Google Gemini 2.0 Flash!")
    
    try:
        agent = GeminiAgent(AgentConfig(name="Gemini"))
        response = agent.respond("Hello! Please introduce yourself and tell me about your capabilities.")
        print(f"Gemini Agent says: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set GOOGLE_API_KEY in your .env file")


if __name__ == "__main__":
    main()