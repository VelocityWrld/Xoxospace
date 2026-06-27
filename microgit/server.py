import os
import base64
import uvicorn
from io import BytesIO
from github import Github, GithubExeception
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import pdfplumber
from docx import Document
from mcp.server.auth.provider import TokenVerifier, AccessToken

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
MICROGIT_API_KEY = os.getenv("MICROGIT_API_KEY")

if not GITHUB_TOKEN:
  raise ValueError("GITHUB_TOKEN is not set. Check your .env file.")
if not GITHUB_OWNER:
  raise ValueError("GITHUB_OWNER is not set. Check your .env file.")
if not GITHUB_REPO:
  raise ValueError("GITHUB_REPO is not set. Check your .env file.")
if not MICROGIT_API_KEY:
  raise ValueError("MICROGIT_API_KEY is not set. Check your .env file.")
  
  MAX_FILE_SIZE = 1*1024*1024 #1MB

g = Github(GITHUB_TOKEN)
repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")

class SimpleTokenVerifier(TokenVerifier):
  async def verify_token(self, token: str) -> AccessToken | None:
    if token == MICROGIT_API_KEY:
      return AcessToken(
        token=token,
        client_id="xoxobot",
        scope=["*"]
      )
    return None
    
mcp = FastMCP(
  "microgit",
  host="0.0.0.0",
  port=int(os.environ.get("PORT", 8001)),
  token_verifier=SimpleTokenVerifier(),
)    

@mcp.tool()
def create_folder(path: str, description: str) -> dict:
  """Create a new folder in the repo by placing a README.md inside it. Path should be topic-based, not generic."""
  try:
    file_path = f"{path}/README.md"
    content = f"# {path}\n\n{description}"
    repo.create_file(
      path=file_path,
      message=f"create: initialise {path} folder",
      content=content,
    )
    return {"status": "success", "path": file_path}
  except GithubException as e:
    return {"status": "error", "message": str(e)}
    
@mcp.tool()
def write_file(path: str, content: str, commit_message: str)-> dict:
  """Create or update a file in the repo. Path must follow naming discipline: folder = topic-based, filename = descriptive subject, no type prefix."""
  try:
    try:
      existing = repo.get_contents(pathi)
      repo.update_file(
        path=path,
        message=commit_message,
        content=content,
        sha=existing.sha,
      )
      action = "updated"
    except GithubException:
      repo.create_file(
        path=path,
        message=commit_message,
        content=content,
      )
      action = "created"
      
    return {
      "status": "success",
      "action": action,
      "path": path,
      "url": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/blob/main/{path}"
    }
  except GithubException as e:
    return {"status": "error", "message": str(e)}
    
@mcp.tool()
def read_file(path: str) -> dict:
  """Read the content of a file from the repo by its path."""
  try:
    file = repo.get_contents(path)
    content = base64.b64decode(file.content).decode("utf-8")
    return {
      "content": content,
      "last_updated": file.last_modified,
    }
  except GithubExeception as e:
    return {"status": "error", "message": str(e)}
    
@mcp.tool()
def read_upload(filename: str) -> dict:
  """Pull a file from /uploads and extract its text content. Supported: .txt,.md, .pdf, .docx. Unsupported: .png, .jpg.mp3 (return error, not silence)."""
  try:
    path = f"uploads/{filename}"
    file = repo.get_content(path)
    
    if file.size > MAX_FILE_SIZE:
      return {
        "status": "error",
        "message": f"{filename} is {file.size//1024}KB – exceeds the 1MB limit " f"for in-memory extraction. Split the file or extract locally."
        
      }
    raw_bytes = base64.b64decode(file.content)
    
    ext = filename.lower().split(".")[-1]
    
    if ext in ("txt", "md"):
      content = raw_bytes.decode("utf-8")
      
    elif ext == "pdf":
      with pdfplumber.open(BytesI0(raw_bytes)) as pdf:
        content = "\n".join(
          page.extract_text() or "" for page in pdf.pages
        )
        
    elif ext == "docx":
      doc = Document(BytesIO(raw_bytes))
      content = "\n".join(
        paragraph.text() or "" for paragraph in doc.paragraphs
        
      )
        
    return {
      "status": "error",
      "message": ".{} files are not supported yet. Supported: .txt, .md, .pdf, .docx".format(ext)
    }
        
      return {
        "status": "success"
        "filename": filename
        "content": content
      }  
      
      
  except GithubException as e:
    return {"status": "error", "message": str(e)}
    
@mcp.tool()
def list_structure() -> dict:
  """Return the full repo tree. Always call this before create_folder to check if a relevant topic folder already exists."""
  try:
    contents = repo.get_git_tree("main", recursive=True)
    tree = {}
    
    for item in contents.tree:
      if item.type == "blob":
        parts = item.part.split("/")
        current = tree
        for part in parts[:-1]:
          if part not in current:
            current[part] = {}
          current = current[part]
        filename = parts[-1]
        if "__files__" not in current:
          current["__files__"] = []
        current["__files__"].append(filename)
    
    return {"tree": tree}    
  
  except GithubException as e:
    return {"status": "error", "message": str(e)}
    
@mcp.tool()
def search_files(query: str) -> dict:
  """Search file contents across the repo using GitHub's native code search. Faster and more scalable than reading files manually. Use before writing new content to check if something related exists."""
  try:
    results = []
    scoped_query = f"{query} repo: {GITHUB_OWNER}/{GITHUB_REPO}"
    found = g.search_code(scoped_query)
    
    for item in found:
      try:
        text_matches = item.text_matches
        excerpts = []
        for match in text_matches:
          fragment = match.get("fragment", "")
          if fragment:
            excerpts.append(fragment)
        excerpt = " ... ".join(excerpts[:3])
      except Exception:
        excerpt = "" 
        
      results.append({
        "path": item.path,
        "excerpt": excerpt,
      })
    
    return {"results": results}
    
  except GithubException as e:
    return {
      "status": "error", 
      "message": f"Search failed: {e.status} {e.data.get('message', '')}"
      
    }
    
  @mcp.tool()
  def delete_file(path: str, commit_message: str, confirmed: bool = False) -> dict:
    """Delete a fike from the repo. IMPORTANT: confirmed must be True before this tool executes. Xoxobot must receive explicit user confirmation in conversation before setting confirmed=True. Never delete autonomously."""
    try:
      if not confirmed:
        return {
          "status": "awaiting_confirmation",
          "message": f"Are you sure you want to delete '{path}'? " f"This cannot be undone. " 
            f"Reply 'yes, delete {path} to confirm."
        }
      
      file = repo.get_contents(path)
      repo.delete_file(
        path=path,
        mesaage=commit_message,
        sha=file.sha
      )
      return {
        "status": "success",
        "path": path,
        "message": f"Deleted {path} with commit: '{commit_message}'"
      }
    
    except GithubException as e:
      return {"status": "error", "message": str(e)}
      
# RUN BLOCK  
if __name__ == "__main__":
  mcp.run(transport="streamable-http")      