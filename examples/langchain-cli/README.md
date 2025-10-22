# Caddey LangChain Chat CLI

A command-line chat interface that authenticates with Caddey using OAuth 2.0 Device Code Flow and allows you to interact with a LangChain agent that has access to your Caddey tools.

## Overview

This example demonstrates how to:
- Authenticate with Caddey using OAuth 2.0 Device Code Flow
- Connect to Caddey's MCP (Model Context Protocol) endpoint
- Create a LangChain agent with access to Caddey tools
- Build an interactive chat interface

## Prerequisites

- Python 3.10+
- A Caddey OAuth Client ID (create a **Public** OAuth client in Caddey)
- An OpenRouter API key (get a free key at [https://openrouter.ai/keys](https://openrouter.ai/keys))

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in this directory with your credentials:

```bash
cp .env.example .env
```

3. Edit the `.env` file and add your credentials:

```
CADDEY_CLIENT_ID=your-client-id-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

## Usage

Run the chat CLI:

```bash
python langchain_chat_cli.py
```

The script will:
1. Prompt you to authenticate via OAuth 2.0 Device Code Flow
2. Display a URL and code for you to authorize the application
3. Connect to Caddey's MCP endpoint and fetch available tools
4. Start an interactive chat session where you can use natural language to interact with your Caddey tools

## Features

- **OAuth 2.0 Device Code Flow**: Secure authentication ideal for CLI applications
- **MCP Integration**: Automatic discovery and invocation of Caddey tools
- **Rich Terminal UI**: Beautiful markdown rendering and formatted output
- **Conversation History**: Maintains context across multiple interactions
- **Free LLM**: Uses OpenRouter's free models (no credit card required)

## Example Interactions

```
You: What tools do I have access to?
Assistant: [Lists available Caddey tools]

You: Create a new task called "Review PR"
Assistant: [Uses Caddey tools to create the task]
```

## Troubleshooting

### Missing Environment Variables

If you see an error about missing `CADDEY_CLIENT_ID` or `OPENROUTER_API_KEY`, make sure:
- You've created a `.env` file in this directory
- The `.env` file contains both required variables
- The values are correct (no quotes needed)

### Authentication Issues

If authentication fails:
- Make sure your OAuth client is set to **Public** in Caddey
- Check that you're using the correct client ID
- Verify you completed the authorization in your browser

### Connection Issues

If you can't connect to Caddey's MCP endpoint:
- Check your internet connection
- Verify the Caddey API is accessible
- Make sure your access token is valid (try re-authenticating)

## Learn More

- [Caddey Documentation](https://caddey.ai/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
