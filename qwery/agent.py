import os
import json
from datetime import datetime, timezone
import google.generativeai as genai
from dotenv import load_dotenv

from sources.tavily import tavily_search, tavily_extract, tavily_crawl
from sources.hackernews import hn_search, hn_search_recent
from sources.newsapi import fetch_news
from sources.github import github_search_repos, github_get_releases, github_search_issues
from sources.stackoverflow import so_search, so_get_answer
from sources.devto import fetch_community_insights

# LOAD AND CONFIGURE GEMINI
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
  raise ValueError("GOOGLE_API_KEY is not set. Cxheck your .env file.")
  
QWERY_AGENT_MODEL = os.getenv("QWERY_AGENT_MODEL", "gemini-2.5-flash")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 3))

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(QWERY_AGENT_MODEL)

# LOAD QWERY AGENT SYSTEM CONFIG
def load_qwery_config() -> str:
  """Load Qwery Agent's operating instructions from qwery_config.md."""
  config_path = os.path.join(os.path.dirname(__file__), "qwery_config.md")
  with open(config_path, "r", encoding="utf-8") as f:
    return f.read()
    
AGENT_INSTRUCTIONS = load_qwery_config()

# SOURCE REGISTRY MAPPING NAMES TO FUNCTIONS
ENTRY_POINT_SOURCES = {
  "hn_search": hn_search,
  "hn_search_recent": hn_search_recent,
  "fetch_news": fetch_news,
  "github_search_repos": github_search_repos,
  "github_search_issues": github_search_issues,
  "so_search": so_search,
  "fetch_community_insights": fetch_community_insights,
}
FOLLOWUP_SOURCES = {
  "github_get_releases": github_get_releases,
  "so_get_answer": so_get_answer,
}

ROUTING_GUIDE = """
Qwery type -> Source(s) to call
Error/debugging -> so_search, tavily_search
Tool/library comparison -> github_search_repos, fetch_community_insights, tavily_search
"What's trending / latest" -> hn_search_recent, fetch_news
Regulatory / industry / funding -> fetch_news, tavily_search
Release notes / changelog -> github_search_repos (auto-enriches with github_get_releases)
Architecture / design opinions -> fetch_community_insights, tavily_search
General / unclear -> tavily_search
"""

# THE PLANNING STEP 

def plan_search_strategy(query: str, depth: str) -> dict:
  """Ask Gemini which sources to call for this query, based on the routing guide. Returns a list of source function names to execute. 
  Note: tavily_search/extract/crawl run automatically as a pipeline, separate from this routing decision.
  """
  prompt = f"""
{AGENT_INSTRUCTIONS}
  
ROUTING GUIDE (for non-Tavily sources):
{ROUTING_GUIDE}
  
Note: Tavily_search always runs automatically, followed by tavily_extract and conditionally tavily_crawl. Do not include these three in your decision — they are handled separately.
  
Available non-Tavily sources to choose from:
{','.join(ENTRY_POINT_SOURCES.keys())}
  
Query: "{query}"
Depth: {depth}

Decide on which of the available non-Tavily sources (if any) are relevant to this query, based on the routing guide.

Respond with ONLY valid JSON, no other text, in this exact shape:
{{
  "sources": ["source_name1", "source_name2"],
  "reasoning": "one sentence why these sources"
}}
"""
  response = model.generate_content(prompt)
  text = response.text.strip()
  
  if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
      text = text[4:]
  
  try:
    decision = json.loads(text.strip())
    valid_sources = [
      s for s in decision.get("sources", [])
      if s in ENTRY_POINT_SOURCES
    ]
    return {"sources": valid_sources, "reasoning": decision.get("reasoning", "")}
  except json.JSONDecodeError:
    return {"sources": [], "reasoning": "Failed to parse planning response."}
    
# TAVILY PIPELINE    
    
def run_tavily_pipeline(query: str) -> list[dict]:
  """The fixed Tavily pipeline: search -> extract top 3 -> crawl any multipage sources found. Always runs, every iteration, independent of the routing decision.
  """
  findings = []
  
  search_results = tavily_search(query, max_results=5)
  if search_results and "error"in search_results[0]:
    return findings
    
  top_urls = [r["url"] for r in search_results[:3] if r.get("url")]
  if not top_urls:
    return findings
    
  extracted = tavily_extract(top_urls)
  if extracted and "error" in extracted[0]:
    extracted = []
  
  multipage_urls = []
  for item in extracted:
    content = item.get("content", "=")
    if len(contact) > 3000 and any(
      marker in item.get("url","")
      for marker in ["/docs/", "/documentation/", "/guide/", "/blog/"]
    ):
      multipage_urls.append(item["url"])
      
  crawled = []
  if multipage_urls:
    crawled = tavily_crawl(multipage_urls, max_pages=5)
    if crawled and "error" in crawled[0]:
      crawled = []
      
  findings.extend(search_results)
  findings.extend(extracted)
  findings.extend(crawled)
  
# RUNNING THE OTHER SOURCES  
  
def run_selected_sources(source_names: list[str], query: str) -> list[dict]:
  """Run the entry-point sources Gemini selected, then automatically enrich GitHub and Stack Overflow results the same way Tavily enriches search results with extract/crawl.
  """
  findings = []
  
  for name in source_names:
    func = ENTRY_POINT_SOURCES.get(name)
    if func is None:
      continue
    
    result = func(query, max_results = 5)
    
    if isinstance(result, list) and result and "error" in result[0]:
      continue
    
    findings.extend(result if isinstance(result, list) else [result])
    
    if name == "github_search_repos":
      top_repos = [r["name"] for r in result[:2] if r.get("name")]
      for repo_name in top_repos:
        releases = github_get_releases(repo_name, max_results=2)
        if releases and "error" not in releases[0]:
          findings.extend(releases)
    
    if name == "so_search":
      for item in result[:2]:
        question_id = item.get("question_id")
        accepted_id = item.get("accepted_id")
        if question_id:
          answer = so_get_answer(question_id, accepted_id)
          if "error" not in answer:
            findings.append(answer)
            
  return findings   
      
# THE ITERATION LOOP

async def run_research(query: str, depth: str = "deep", max_iterations: int = None) -> dict:
  """Full Qwery Agent research cycle. Plans sources, runs Tavily pipeline + selected sources, evaluates results, iterates if needed, synthesises final output.
  This is what the A2A server calls.
  """
  if max_iterations is None:
    max_iterations = MAX_ITERATIONS
    
  all_findings = []
  iterations_run = 0
  synthesis = ""
  
  for iteration in range(max_iterations):
    iterations_run += 1
    
    tavily_findings = run_tavily_pipeline(query)
    plan = plan_search_strategy(query, depth)
    other_findings = run_selected_sources(plan["sources"], query)
    
    iteration_findings = tavily_findings + other_findings
    all_findings.extend(iteration_findings)
    
    evaluation = evaluate_results(query, all_findings)
    
    if evaluation ["sufficient"]:
      synthesis = synthesise_findings(query, all_findings)
      break
    
    if iteration < max_iterations - 1:
      query = evaluation.get("refined_query", query)
      
  if not synthesis:
    synthesis = synthesise_findings(query, all_findings)
    
  return {
    "query": query,
    "findings": all_findings,
    "synthesis": synthesis,
    "iterations_run": iterations_run,
    "timestamp": datetime.now(timezone.utc).isoformat(),
  }
  
# AGENT DECIDES WHETHER TO ITERATE OR STOP  
  
def evaluate_results(query: str, findings: list[dict]) -> dict:
  """Ask Gemini to evaluate whether the current findings are sufficient to answer the query, or whether another iteration is needed with a refined query.
  """
  findings_summary = json.dumps(findings[:10], indent=2)[:3000]
  
  prompt = f"""
{AGENT_INSTRUCTIONS}

You are evaluating research findings for this query:
"{query}"

Current findings (truncated to first 10, max 3000 chars):
{findings_summary}

Evaluate whether these findings sufficiently answer the query.

Consider:
- Are the sources relevant and credible?
- Is there enough depth and detail to give a complete answer?
- Are there obvious gaps that another search iteration would fill?

Respond with ONLY valid JSON, no other text:
{{
  "sufficient": true or false,
  "reasoning": "one sentence explanation",
  "refined query": "a more targeted query if not sufficient, else repeat original query"
}}
"""

  response = model.generate_content(prompt)
  text = response.text.strip()
  
  if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
      text = text[4:]
      
  try:
    result = json.loads(text.strio())
    return {
      "sufficient": bool(result.get("sufficient", False)),
      "reasoning": result.get("reasoning", ""),
      "refined_query": result.get("refined_query", query),
    }
  except json.JSONDecodeError:
    return {
      "sufficient": False,
      "reasoning": "Failed to parse evaluation response.",
      "refined_query": query,
    }
    
# AGENT WRITES FINAL ANSWER

def synthesise_findings(query: str, findings: list[dict]) -> str:
  """Ask Gemini to synthesise all findings into a clean, direct answer to the original query.
  This is the final output Xoxobot receives as the A2A artifact.
  """
  findings_text = json.dumps(findings, indent=2)[:6000]
  
  prompt = f"""
{AGENT_INSTRUCTIONS}

You have completed research on this query:
"{query}"

All findings gathered:
{findings_text}

Synthesise these findings into a direct, technically precise answer.

Rules:
- Answer the query directly — no preamble, no "based on my research"
- Be specific — include version numbers, dates, names where relevant
- Be honest — a developer reading wants signal, not noise
- Cite sources by URL where they directly support a claim
"""

  response = model.generate_content(prompt)
  return response.text.strip()
  