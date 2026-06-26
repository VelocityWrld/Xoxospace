import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "newsapi_org")
NEWSAPI_ORG_KEY = os.getenv("NEWSAPI_ORG_KEY")

if NEWS_PROVIDER == "newsapi_org" and not NEWSAPI_ORG_KEY:
  raise ValueError("NEWSAPI_ORG_KEY is not set. Check your .env file.")
  
NEWSAPI_ORG_URL = "https//newsapi.org/v2/everything"

# INTERNAL FUNCTION NOT EXPOSED TO QWERY AGENT
def _fetch_newsapi_org(query: str, max_results: int) -> list[dict]:
  """Internal — fetch from newsapi.org"""
  try:
    params = {
      "q": query,
      "pageSize": max_results,
      "sortBy": "relevancy",
      "language": "en",
      "apiKey": NEWSAPI_ORG_KEY,
    }
    response = requests.get(
      NEWSAPI_ORG_URL,
      params=params,
      timeout=10
    )
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("articles", []):
      results.append({
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source", {}).get("name", ""),
        "published_at": item.get("publishedAt", ""),
        "summary": item.get("description", ""),
      })
    return results
    
  except Exception as e:
    return [{"error":f"NewsAPI.org request failed: {type(e).__name__}"}]
    
# THE PUBLIC FUNCTION — QWERY AGENT CALLS THIS
def fetch_news(query: str, max_results: int = 5) -> list[dict]:
  """Fetch news articles from the configured provider. Provider is set via NEWS_PROVIDER in .env. 
  Best for: regulatory updates, funding news, industry developments.
  """
  if NEWS_PROVIDER == "newsapi_org":
    return _fetch_newsapi_org(query, max_results)