import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
  raise ValueError("TAVILY_API_KEY is not set. Check your .env file")

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search(query: str, max_results: int = 5) -> list[dict]:
  """Search the web. Returns top results with title, url, and content snippet. Always called first at start of every Qwery iteration.
  """
  try:
    response = client.search(
      query=query,
      max_results=max_results,
      search_depth="advanced",
    )
    results = []
    for item in response.get("results", ""):
      results.append({
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "content": item.get("content", ""),
        "score": item.get("score", 0.0),
      })
    return results
  except Exception as e:
    return [{"error": f"Tavily request failed: {type(e).__name__}"}]
    
def tavily_extract(urls: list[str]) -> list[dict]:
  """Extract full page content from a list of URLs. Called after tavily_search with the top 3 URLs. Accepts a batch of URLs in one call.
  """
  try:
    response = client.extract(urls=urls)
    results = []
    for item in response.get("results", []):
      results.append({
        "url": item.get("url", ""),
        "content": item.get("raw_content", ""),
      })
    return results
  except Exception as e:
    return [{"error": f"Tavily request failed: {type(e).__name__}"}]
    
def tavily_crawl(urls: list[str], max_pages: int = 5) -> list[dict]:
  """Crawl multipage sources identified during extraction. Called when extract reveals a source spans multiple pages (documentation sites, blog series, spec pages).
  """
  try:
    all_results = []
    for url in urls:
      response = client.crawl(
        url=url,
        max_depth=2,
        max_pages=max_pages,
      )
      for item in response.get("results", []):
        all_results.append({
          "url": item.get("url", ""),
          "content": item.get("content", ""),
        })
    return all_results
  except Exception as e:
    return [{"error": f"Tavily request failed: {type(e).__name__}"}]
      