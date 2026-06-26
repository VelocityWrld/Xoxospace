# MicroGit

GitHub-backed knowledge base MCP server. Reads and writes files
to a real GitHub repo. Stores only what's worth keeping permanently.

## Tools

| Tool | What it does |
|------|-------------|
| write_file | Create or update a file with a commit |
| read_file | Read a file's content |
| create_folder | Create a topic folder |
| list_structure | Return the full repo tree |
| search_files | Search file contents via GitHub code search |
| read_upload | Extract text from /uploads (pdf, docx, txt, md) |
| delete_file | Delete a file — requires confirmed=True |

## Setup

1. Create a GitHub repo (can be private).
2. Generate a fine-grained PAT — Contents read/write, Metadata read,
   scoped to this repo only.
3. Fill in `.env`:
GITHUB_TOKEN=your_token_here
GITHUB_OWNER=your_username
GITHUB_REPO=your_repo_name
MICROGIT_API_KEY=your_shared_secret_here
4. Install dependencies:
pip install -r requirements.txt

## Run
python microgit/server.py

Runs on port 8001 locally. Connect via:
`http://localhost:8001/mcp`

## Part of Xoxospace

Standalone — any MCP-compatible agent can connect to it.
See root [README](../README.md) for the full stack.