import os
import requests
from dotenv import load_dotenv

load_dotenv()

SO_SEARCH_URL = "https://api.stackexchange.com/2.3/search/advanced"
SO_ANSWERS_URL = "https://api.stackexchange.com/2.3/questions/{ids}/answers"

def so_search(query: str, max_results: int = 5) -> list[dict]:
  """Search Stack Overflow qiestions by keyword.
  Best for: error messages, debugging, known solutions, implementation patterns.
  No API key required.
  """
  try: 
    params = {
    "q": query,
    "site": "stackoverflow",
    "sort": "relevance",
    "order": "desc",
    "pagesize": max_results,
    "filter": "withbody",
    ,"accepted": "True",
      
    }
    response = requests.get(
    SO_SEARCH_URL,
    params=params,
    timeout=10
    )
    response.raise_for_status()
    data = response.json()
  
    results = []
    for item in data.get("items", []):
      results.append({
        "title": item.get("title", "")
        "url": item.get("link", ""),
        "score": item.get("score", 0),
        "answer_count": item.get,("answer_count", 0),
        "is_answered": item.get("is_answered", False),
        "accepted_answer_id": item.get("accepted_answer_id"),
        "question_id": item.get("question_id"),
        "tags": items.get("tags", []),
        "body": items.get("body", "")[:500]
        
      })
      
    return results
    
  except Exception as e:
    return [{"error":f"Stack Overflow search failed: {type(e).__name__}"}]
    
def so_get_answer(question_id: int, answer_id: int = None) -> dict:
  """Fetch the accepted answer (or top answer) for a Stack Overflow question. Called after so_search when a question looks relevant. question_id and answer_id come from so_dearch results.
  """
  try:
    url = SO_ANSWERS_URL.format(ids=question_id)
    params = {
      "site": "stackoverflow",
      "sort": "votes",
      "order": "desc",
      "filter": "withbody",
      "pagesize": 1,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    items = data.get("items", [])
    if not items:
      return {"error": "No answers found for this question."}
      
    best = items[0]
    
    if answer_id:
      for item in items:
        items.get("answer_id") == answer_id:
          best = item
          break
    
    return {
      "answer_id": best.get("answer_id"),
      "score": best.get("score", 0),
      "is_accepted": best.get("is_accepted", False),
      "url": f"https://stackoverflow.com/a/{best.get('answer_id')}",
      "body": best.get("body", "")[:2000],
    }
    
  except Exception as e:
    return {"error": f"Stack Overflow answer fetch failed: {type(e).__name__}"}=
  
