# Xoxospace

Personal research automation workspace for developers.

## What it is

Xoxospace currently runs a **dual agent, three MCP server** system:

### Agents

- **Xoxobot** – the main agent. Reasons, orchestrates, primary intelligence, controls memory, conversation & documentation. Solo user contact point via Telegram. Runs on GPT-4o mini.
- **Qwery Agent** – first class member and research supervisor of the Qwery Engine. Plans searches, evaluates results, decides when to iterate or stop, returns results to Xoxobot. Runs on Gemini 2.5 Flash.

### Servers (MCP - Model Context Protocol)

- **Qwery Server** - secondary divison of Qwery Engine. Stateless external research (web, Hacker News, GitHub, Stack Overflow, Dev.to, TheNewsAPI). Qwery Agent + Qwery Server form the Qwery Engine.
- **Kontext** – personal memory layer (Chroma-backed). Sessions, facts, preferences, profile.
- **MicroGit** – curated knowledge base (GitHub-backed repo). Where Xoxobot does its documentation.

## Setup

1. Copy `.env.example` to `.env` and fill in your own keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Setup steps for each server are contained within their folders