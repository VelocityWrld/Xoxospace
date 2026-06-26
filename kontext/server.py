import os
import chromadb
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
import uvicorn

load_dotenv() #load env variables

KONTEXT_API_KEY = os.getenv("KONTEXT_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./kontext/kontext_store")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2") # 11&12 read config from env, second arguments acts as fallback

client = chromadb.PersistentClient(path=CHROMA_PATH) # creates Chroma client that saves data to disk in given path; the entire DB setup in embedded mode
profile = client.get_or_create_collection("profile", metadata={"hnsw: space": "cosine"})
preferences = client.get_or_create_collection("preferences", metadata={"hnsw: space": "cosine"})
facts = client.get_or_create_collection("facts", metadata={"hnsw: space": "cosine"})
sessions = client.get_or_create_collection("sessions", metadata={"hnsw: space": "cosine"}) #12-15 creates/connects our Chroma collections

collection_map = {
    "sessions": sessions,
    "facts": facts,
    "preferences": preferences,
    "profile": profile
      
    }
class SimpleTokenVerifier(TokenVerifier):
  async def verify_token(self, token: str) -> AccessToken | None:
    if token == KONTEXT_API_KEY:
      return AccessToken(token=token, client_id="xoxobot", scopes=["*"])
    return None
  
mcp = FastMCP(
  "kontext",
  host="0.0.0.0",
  port=int(os.environ.get("PORT", 8000)),
  token_verifier=SimpleTokenVerifier(),
) #creates MCP server instance "kontext"

@mcp.tool() #tool 1 decorator; store_session
def store_session(session_id: str, query: str, outcome: str, sources: list[str]) -> dict:
  """Log a completed task: the query, what happened, and sources used."""
  timestamp = datetime.utcnow().isoformat()
  sessions.add(
    ids=[session_id],
    documents=[f"{query} -> {outcome}"],
    metadatas=[{
      "query": query,
      "outcome": outcome,
      "sources": ",".join(sources),
      "timestamp": timestamp
    }]
  )
  return {"status": "success"}
  
@mcp.tool() #tool 2 decorator; search_memory
def search_memory(query: str, collections: list[str] = None, limit: int = 5) -> dict:
  """Search across memory collections (sessions, facts, preferences, profile) for relevant context."""
  if collections is None:
    collections = ["sessions", "facts", "preferences", "profile"]
      
    
  results = []
  for name in collections:
    col = collection_map.get(name)
    if col is None:
    continue
    found = col.query(query_texts=[query], n_result=limit)
    docs = found.get("documents", [[]])[0]
    metas = found.get("metadatas", [[]])[0]
    distances = found.get("distances", [[]])[0]
    
    for doc, meta, dist in zip(doc, metas, distances):
      results.append({
        "collection": name,
        "content": doc,
        "relevance": 1 - dist,
        "metadata": meta
        
      })
        
  return {"results": results}
  
@mcp.tool() #tool 3 decorator; store_fact
def store_fact(key: str, value: str, tags: list[str] = None) -> dict:
  """Save or update a key-value entry in facts, preference, or profile."""
  if tags is None:
    tags = []
  
  target = collection_map.get(collection)
  if target is None:
    return {"status": "error", "message": f"Unknown collection: {collection}"}
    
  target.add(
    ids=[key],
    documents=[f"{key}: {value}"],
    metadatas=[{
      "key": key,
      "value": value,
      "tags": ",".join(tags)
    }]
  )
  return {"status": "success"}
    
@mcp.tool() #tool 4 decorator; get_recent_sessions
def get_recent_sessions(limit: int = 5) -> dict:
  """Retrieve the most recent stored sessions."""
  all_sessions = sessions.get()
  
  items = []
  for doc_id, meta in zip(all_sessions.get("ids",[]), all_sessions.get("metadatas", [])):
    items.append({
      "session_id": doc_id,
      "query": meta.get("query"),
      "outcome": meta.get("outcome"),
      "sources": meta.get("sources"),
      "timestamp": meta.get("timestamp")
    })
    
  items.sort(key=lambda x: x["timestamp"], reverse=True)
  return {"sessions": items[:limit]}
  
@mcp.tool() #tool 5 decorator; get_preferences
def get_preferences() -> dict:
  """Retrieves all stored user preferences."""
  all_prefs = preferences.get()
  
  prefs = {}
  for meta in all_prefs.get("metadatas", []):
    key = meta.get("key")
    value = meta.get("value")
    if key:
      prefs[key] = value
      
  return {"preferences": prefs}    
# RUN BLOCK  
if __name__ == "__main__":
  mcp.run(transport="streamable-http")