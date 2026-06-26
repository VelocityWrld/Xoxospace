# Qwery Engine

Stateless A2A research agent. Give it a question, get back
structured findings and a synthesised answer. No memory between calls.

## Sources

| Source | Purpose |
|--------|---------|
| Tavily | Web search + full-content extraction + crawl |
| Hacker News | Developer pulse and community sentiment |
| NewsAPI | Industry, regulatory, and funding news |
| GitHub | Repos, releases, issues |
| Stack Overflow | Debugging and known solutions |
| Dev.to + Hashnode | Practitioner opinions and deep dives |

## Internal structure
Qwery Engine
├── Qwery Agent (Gemini 2.5 Flash) — plans, evaluates, synthesises
└── Qwery Server — executes searches across 6 sources

## Setup

1. Fill in `.env`:
GOOGLE_API_KEY=your_google_ai_studio_key
QWERY_AGENT_MODEL=gemini-2.5-flash
TAVILY_API_KEY=your_tavily_key
NEWSAPI_ORG_KEY=your_newsapi_key
GITHUB_TOKEN=your_github_token
MAX_ITERATIONS=3
QWERY_API_KEY=your_shared_secret_here
QWERY_PUBLIC_URL=http://localhost:8002

2. Install dependencies: 
pip install -r requirements.txt

## Run
python qwery/server.py

Runs on port 8002 locally. Agent Card at:
`http://localhost:8002/.well-known/agent-card.json`

## Part of Xoxospace

Standalone — any A2A-compatible agent can connect to it.
See root [README](../README.md) for the full stack.