import os
import requests
from dotenv import load_dotenv

load_dotenv()

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"

def hn_search(query: str, max_results: int = 10) -> list[dict]:
  """Search Hacker News stories by relevance. Best for: developer sentiment, tool discussions, ecosystem reactions. No API key required.
  """
  try:
    params = {
      "query": query,
      "tags": "story",
      "hitsPeraPage": max_results,
    }
    response = requests.get(HN_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("hits", []):
      results.append({
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "hn_url": f"https://news.ycombinator.com/item?id={item.get('objectID')}",
        "points": item.get("num_comments", 0),
        "author": item.get("author", ""),
        "created_at": item.get("created_at", ""),
      })
    return results
  
  except Exception as e:
    return [{"error":f"HN search failed: {type(e).__name__}"}]
    
def hn_search(query: str, max_results: int = 10) -> list[dict]:
  """Search Hacker News stories sorted by date(most recent first). Best for: latest releases, breaking news, what shipped this week. No API key required.
  """
  try:
    params = {
      "query": query,
      "tags": "story",
      "hitsPeraPage": max_results,
    }
    response = requests.get(HN_SEARCH_DATE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("hits", []):
      results.append({
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "hn_url": f"https://news.ycombinator.com/item?id={item.get('objectID')}",
        "points": item.get("num_comments", 0),
        "author": item.get("author", ""),
        "created_at": item.get("created_at", ""),
      })
    return results
  
  except Exception as e:
    return [{"error":f"HN recent search failed: {type(e).__name__}"}]    