# THE A2A SERVER
import os
import server
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater, InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.types import AgentCard, AgentCapabilities, AgentInterface, AgentSkill, Part

from agent import run_research

load_dotenv()

QWERY_API_KEY = os.getenv("QWERY_API_KEY")
if not QWERY_API_KEY:
  raise ValueError("QWERY_API_KEY is not set. Check your .env file.")
  
PUBLIC_URL = os.getenv("QWERY_API_KEY", "http://localhost:8002")

AGENT_CARD = AgentCard(
  name="Qwery Engine",
  description=(
    "Stateless research agent. Give it a question, get back structured findings and a synthesised answer. Searches the web, Hacker News, GitHub, Stack Overflow, news sources, and developer communities. No memory between calls."
  ),
  supported_interfaces=[
    AgentInterface(
      protocol_binding="JSONRPC",
      url="{}/api/v1/jsonrpc/".format(PUBLIC_URL),
    ),
  ],
  version="1.0.0",
  default_input_modes=["text/plain"],
  default_output_modes=["text/plain"],
  capabilities=AgentCapabilities(streaming=True),
  skills=[
    AgentSkill(
      id="research",
      name="Research a topic",
      description=(
        "Runs a comprehensive research cycle: web search with full-content extraction, plus relevant developer sources. Iterates up to 3 times. Returns structured findings and a direct synthesis."
      ),
      tags=["research","search","developer-tools"],
      input_modes=["text/plain"],
      output_modes=["text/plain"],
      examples=[
        "What's the latest on LangChain v0.4?",
        "How do I fix CORS error with fetch in JavaScript?",
        "Compare Postgres vs MongoDB for multi-tenant SaaS",
      ],
    )
  ],
)

class QweryExecutor(AgentExecutor):
  """Task lifecycle pattern: Task first (handled internally by TaskUpdater.submit()), then status/artifact events, ending in a terminal state (complete/failed).
  """
  
  async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
    
    query = context.get_user_input()
    if not query or not query.strip():
      await task_updater.failed(
        message=task_updater.new_agent_message(
          parts=[Part(text="Empty query received. Cannot research nothing.")]
        )
      )
      return
    
    await task_updater.submit()
    await task_updater.start_work()
    
    try:
      result = await run_research(query=query, depth="deep")
    except Exception as e:
      await task_updater.failed(
        message=task_updater.new_agent_message(
          parts=[Part(text=f"Research failed: {type(e).__name__}")]
        )
      )
      return
    
    await task_updater.add_artifact(
      parts=[Part(text=result["synthesis"])],
      name="research_synthesis",
      metadata={
      "iterations_run": result["iterations_run"],
      "sources_count": len(result["findings"]),
      "timestamp": result["timestamp"],
      },
    )
    
    await task_updater.complete()
    
  async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
    task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
    await task_updater.failed(
      message=task_updater.new_agent_message(
        parts=[Part(text="Text cancelled by client.")]
      )
    )
    
executor = QweryExecutor()
task_store = InMemoryTaskStore()

request_handler = DefaultRequestHandler(
  agent_executor=executor,
  task_store=task_store,
  agent_card=AGENT_CARD,
)

routes = []
routes.extend(create_agent_card_routes(AGENT_CARD))
routes.extend(create_jsonrpc_routes(request_handler, rpc_url="/api/v1/jsonrpc/"))

app = FastAPI(routes=routes)

@app.middleware("http")
async def verify_api_key(request, call_next):
  if request.url.path == "/.well-known/agent-card.json":
    return await call_next(request)
    
  auth_header = request.headers.get("Authorization", "")
  expected = f"Bearer {QWERY_API_KEY}"
  if auth_header != expected:
    return JSONResponse({"error": "Unauthorized"}, status_code=401)
  
  return await call_next(request)
  
if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8002))
  uvicorn.run(app, host="0.0.0.0", port=port)