# Kontext

Personal memory MCP server. Stores and retrieves sessions, facts,
preferences, and profile via ChromaDB semantic search.

## Tools

| Tool | What it does |
|------|-------------|
| store_session | Log a completed task |
| search_memory | Semantic search across all collections |
| store_fact | Save or update a fact, preference, or profile entry |
| get_recent_sessions | Retrieve last N sessions |
| get_preferences | Retrieve all stored preferences |

## Setup

1. Copy `.env.example` to `.env` in project root and fill in:

CHROMA_PATH=./kontext/kontext_store
EMBEDDING_MODEL=all-MiniLM-L6-v2
KONTEXT_API_KEY=your_shared_secret_here

2. Install dependencies:
pip install -r requirements.txt

## Run 
python kontext/server.py

Runs on port 8000 locally. Connect via:
`http://localhost:8000/mcp`

## Part of Xoxospace

Standalone — any MCP-compatible agent can connect to it.
See root [README](../README.md) for the full stack.