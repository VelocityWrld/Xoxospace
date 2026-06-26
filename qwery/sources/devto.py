import os
import requests
from dotenv import load_dotenv

load_dotenv()

DEVTO_URL = "https://dev.to/api/articles"
HASHNODE_URL = "https://gql.hashnode.com"

def devto_search(query: str, max_results: int = 5) -> list[dict]:
  """Search Dev.to articles by keyword.
  Best for: architecture opinions, real-world implementation experiences, "how I built X" posts, tool comparisons from practitioners.
  No API key required.
  """
  try:
    params = {
      "q": query,
      "per_page": max_results,
    }
    response = requests.get(
      DEVTO_URL,
      params=params,
      timeout=10
    )
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data:
      results.append({
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "description": item.get("description", ""),
        "tags": item.get("tag_list", []),
        "reactions": item.get("positive_reactions_count", 0),
        "comments": item.get("comment_count", 0),
        "reading_time": item.get("reading_time_minutes", 0),
        "published_at": item.get("published at", ""),
        "author": item.get("user", {}).get("name", ""),
      })
    return results
    
  except Exception as e:
    return [{"error": f"Dev.to search failed: {type(e).__name__}"}]
    
    
def hashnode_search(query: str, max_results: int = 5) -> list[dict]:
  """Search Hashnode posts via GraphQL.
  Best for: technical deep dives, engineering blog posts, startup/product engineering insights.
  """
  try:
    graphql_query = """
    query SearchPosts($query: String!, $first: Int!) {
      searchPostsOfPublication(
        first: $first,
        filter: { query: $query }
      ) {
        edges {
          node {
            title
            url
            brief
            reactionCount
            replyCount
            publishedAt
            tags {
              name
            }
            author {
              name
            }
          }
        }
      }
    }
    """
    payload = {
      "query": graphql_query,
      "variables": {
        "query": query,
        "first": max_results,
      }
    }
    response = requests.post(
      HASHNODE_URL,
      json=payload,
      timeout=10
    )
    response.raise_for_status()
    data = response.json()
    
    edges = (
      data
      .get ("data", {})
      .get("searchPostsOfPublication", {})
      .get("edges", [])
    )
    
    results = []
    for edge in edges:
      node = edge.get("node", {})
      results.append({
        "title": node.get("title", ""),
        "url": node.get("url", ""),
        "description": node.get("brief", ""),
        "tags": [t.get("name") for t in node.get("tags", [])],
        "reactions": node.get("reactionCount", 0),
        "comments": node.get("replyCount", 0),
        "published_at": node.get("publishedAt", ""),
        "author": node.get("author", {}).get("name", ""),
      })
    return results
    
  except Exception as e:
    return[{"error": f"Hashnode search failed: {type(e).__name__}"}]
    
    
def fetch_community_imsights(query: str, max_results: int = 5) -> list[dict]:
  """Fetch developer community insights from Dev.to and Hashnode. Combines results from both platforms into one list.
  Best for: architecture decisions,  tool comparisons, real-world experience reports.
  """
  
  devto_results = devto_search(query, max_results)
  hashnode_results = hashnode_search(query, max_results)
  
  devto_clean = [r for r in devto_results if "error" not in r]
  hashnode_clean = [r for r in hashnode_results if "error" not in r]
  
  combined = devto_clean + hashnode_clean
  
  if not combined:
    errors = devto_results + hashnode_results
    return errors
    
  return combined