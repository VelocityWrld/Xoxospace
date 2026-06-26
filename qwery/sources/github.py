import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
  raise ValueError ("GITHUB_TOKEN is not set. Check your .env file.")

g = Github(GITHUB_TOKEN)

def github_search_repos(query: str, max_results: int = 5) -> list[dict]:
  """Search public GitHub repos by keyword.
  Best for: comparing libraries, checking repo health, finding alternatives to a tool.
  """
  try:
    results = []
    repos = g.search_repositories(
      query=query,
      sort="stars",
      order="desc"
    )
    for repo in repos[:max_results]:
      results.append({
        "name": repo.full_name,
        "url": repo.html_url,
        "description": repo.description or  "",
        "stars": repo.stargazers_count,
        "forks": repo.forks_count,
        "open_issues": repo.open_issues_count,
        "language": repo.language or "",
        "last_updated": str(repo.updated_at),
        "topics": repo.get_topics(),
      })
    return results
    
  except GithubException as e:
    return[{"error": f"GitHub repo search failed: {e.status}"}]
  except Exception as e:
    return[{"error": f"GitHub repo search failed: {type(e).__name__}"}]
    
def github_get_releases(repo_name: str, max_results: int = 3) -> list[dict]:
  """Get the latest releases for a specific repo. 
  Best for: changelog lookups, version comparisons, "what changed in X v2.0" queries.
  repo_name format: "owner/repo" e.g "langchain-ai/langchain"
  """
  try:
    repo = g.get_repo(repo_name)
    releases = repo.get_releases()
    
    results = []
    for release in releases[:max_results]:
      results.append({
        "tag": release.tag_name,
        "name": release.title,
        "url": release.url,
        "published_at": str(release.published_at),
        "body": release.body[:1000] if release.body else "",
      })
    return results
    
  except GithubException as e:
    return [{"error": f"GitHub releases failed: {e.status}"}]
  except Exception as e:
    return [{"error": f"GitHub releases failed: {type(e).__name__}"}]
    
def github_search_issues(query: str, repo_name: str = None, max_results: int = 5) -> list[dict]:
  """Search GitHub issues and PRs.
  Best for: known bugs, error messages, feature requests, checking if a problem is already reported.
  repo_name is optional — searches all public repos if not provided.
  """
  try:
    search_query = query
    if repo_name:
      search_query = f"{query} repo:{repo_name}"
      
    issues = g.search_issues(
      query=search_query,
      sort="relevance",
    )
    
    results = []
    for issue in issues[:max_results]:
      results.append({
        "title": issue.title,
        "url": issue.html_url,
        "state": issue.state,
        "is_pr": issue.pull_request is not None,
        "created_at": str(issue.created_at),
        "comments": issue.comments,
        "body": issue.body[:500] if issue.body else "",
      })
    return results
    
  except GithubException as e:
    return [{"error": f"GitHub issue search failed: {e.status}"}]
  except Exception as e:
    return [{"error": f"GitHub issue search failed: {type(e).__name__}"}]