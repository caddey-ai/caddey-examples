"""
Caddey LangChain Chat CLI

A command-line chat interface that authenticates with Caddey using OAuth 2.0 Device Code Flow
and allows you to interact with a LangChain agent that has access to your Caddey tools.

Prerequisites:
- Python 3.10+
- pip install langchain>=1.0 langchain-mcp-adapters langchain-openai openai requests python-dotenv rich

Usage:
    1. Create a .env file in this directory with:
       CADDEY_CLIENT_ID=your-client-id
       OPENROUTER_API_KEY=your-openrouter-api-key

    2. Run the script:
       python langchain_chat_cli.py

Notes:
- Get a free OpenRouter API key at https://openrouter.ai/keys
"""

import os
import sys
import time
import asyncio
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

# Load environment variables from .env file if present
load_dotenv()

# Create console for rich output
console = Console()

# OAuth endpoints
DEVICE_URL = "https://auth.caddey.ai/realms/caddey/protocol/openid-connect/auth/device"
TOKEN_URL = "https://auth.caddey.ai/realms/caddey/protocol/openid-connect/token"
MCP_URL = "https://api.caddey.ai/mcp"


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 70)
    print("🚀  Caddey LangChain Chat CLI")
    print("=" * 70 + "\n")


def authenticate():
    """
    Authenticate using OAuth 2.0 Device Code Flow.

    Returns:
        str: Access token
    """
    client_id = os.getenv("CADDEY_CLIENT_ID")
    if not client_id:
        print("❌ Error: CADDEY_CLIENT_ID not found.")
        print("\nPlease create a .env file in this directory with:")
        print("  CADDEY_CLIENT_ID=your-client-id")
        print("  OPENROUTER_API_KEY=your-openrouter-api-key")
        sys.exit(1)

    # Step 1: Request device code
    device_response = requests.post(
        DEVICE_URL,
        data={"client_id": client_id},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if device_response.status_code != 200:
        print(f"❌ Error requesting device code: {device_response.text}")
        sys.exit(1)

    device_data = device_response.json()
    device_code = device_data["device_code"]
    user_code = device_data["user_code"]
    verification_uri = device_data["verification_uri_complete"]
    interval = device_data.get("interval", 5)

    # Step 2: Display instructions to user
    print("=" * 70)
    print("🔐  Authentication Required")
    print("=" * 70 + "\n")
    print("   To sign in, open this URL in your browser:\n")
    print(f"    👉  {verification_uri}\n")
    print(f"    Or visit: {device_data['verification_uri']}")
    print(f"    And enter code: {user_code}\n")
    print("=" * 70)
    print("⏳  Waiting for authentication...\n")

    # Step 3: Poll for token
    while True:
        time.sleep(interval)

        token_response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if token_response.status_code == 200:
            token_data = token_response.json()
            print("✅ Logged in successfully! Token acquired.\n")
            return token_data["access_token"]
        elif token_response.status_code == 400:
            error = token_response.json().get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
                continue
            else:
                print(f"❌ Authentication error: {error}")
                sys.exit(1)
        else:
            print(f"❌ Unexpected error: {token_response.text}")
            sys.exit(1)


async def create_agent(access_token: str):
    """
    Create a LangChain agent connected to Caddey MCP.

    Args:
        access_token: OAuth access token

    Returns:
        tuple: (agent, tools)
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_agent

    # Check for OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found.")
        print("\nPlease create a .env file in this directory with:")
        print("  CADDEY_CLIENT_ID=your-client-id")
        print("  OPENROUTER_API_KEY=your-openrouter-api-key")
        print("\nGet a free OpenRouter API key at: https://openrouter.ai/keys")
        sys.exit(1)

    # Use OpenRouter free credits for gpt-4o-mini
    model_name = "openai/gpt-4o-mini"

    print(f"🤖 Using OpenRouter ({model_name})")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1"
    )

    print("🔧 Connecting to Caddey MCP endpoint...")

    # Connect to Caddey MCP endpoint
    mcp = MultiServerMCPClient({
        "caddey": {
            "transport": "streamable_http",
            "url": MCP_URL,
            "headers": {"Authorization": f"Bearer {access_token}"}
        }
    })

    # Get available tools from Caddey
    print("🔧 Fetching available tools from Caddey...")
    tools = await mcp.get_tools()
    print(f"✅ Found {len(tools)} tools available!\n")

    # Create agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a helpful assistant with access to Caddey tools. Use the available tools to help users accomplish their tasks. Be concise and friendly."
    )

    return agent, tools


async def chat_loop(agent):
    """
    Run interactive chat loop.

    Args:
        agent: LangChain agent
    """
    print("=" * 70)
    print("💬  Chat Interface Ready! (Ctrl+C to exit)")
    print("=" * 70 + "\n")

    conversation_history = []

    while True:
        try:
            # Get user input
            user_input = input("💬 You: ").strip()

            if not user_input:
                continue

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_input})

            # Invoke agent
            print("\n🤔  Thinking...\n")

            try:
                result = await agent.ainvoke({"messages": conversation_history})
            except Exception as invoke_error:
                print(f"⚠️  Error: {invoke_error}\n")
                conversation_history.pop()
                print("-" * 70 + "\n")
                continue

            # Extract response from result
            response = ""
            if "messages" in result and len(result["messages"]) > 0:
                for msg in reversed(result["messages"]):
                    if hasattr(msg, 'type') and msg.type == 'ai':
                        response = msg.content if hasattr(msg, 'content') else ""
                        break

            # Handle empty responses
            if not response or not response.strip():
                print("⚠️  No response generated. Please try again.\n")
                conversation_history.pop()
            else:
                # Add assistant response to conversation history
                conversation_history.append({"role": "assistant", "content": response})

                # Display response with markdown formatting
                print("🤖  Assistant:\n")
                md = Markdown(response)
                console.print(md)
                print()
            
            print("-" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("👋  Thanks for using Caddey Chat CLI!")
            print("=" * 70 + "\n")
            break
        except Exception as e:
            print(f"\n❌  Error: {e}\n")
            print("-" * 70 + "\n")


async def main():
    """Main entry point."""
    print_banner()

    # Step 1: Authenticate
    access_token = authenticate()

    # Step 2: Create agent
    try:
        agent, _ = await create_agent(access_token)
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        sys.exit(1)

    # Step 3: Start chat loop
    await chat_loop(agent)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("👋  Thanks for using Caddey Chat CLI!")
        print("=" * 70 + "\n")
        sys.exit(0)
