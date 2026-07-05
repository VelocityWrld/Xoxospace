import os
import sys
import base64
from telegram import Update
from telegram.ext import ContextTypes
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from xoxobot.agent import run_xoxobot_task, kontext_get_recent_sessions, microgit_list_structure
from dotenv import load_dotenv

load_dotenv()

ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")
ALLOWED_USER_IDS = set(
  int(uid.strip())
  for uid in ALLOWED_USER_IDS_RAW.split(",")
  if uid.strip().isdigit()
)

def is_allowed(user_id: int) -> bool:
  """Check if a Telegram user ID is on the allowlist."""
  return user_id in ALLOWED_USER_IDS
  
# HANDLER 1 — PLAIN TEXT MESSAGES

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Handle plain text messages from allowed users."""
  user_id = update.effective_user.id
  
  if not is_allowed(user_id):
    return
  
  query = update.message.text
  if not query or not query.strip():
    return
  
  await update.message.reply_text("🔍Working on it...")
  
  try:
    response = await run_xoxobot_task(query=query)
    await update.message.reply_text(response)
  except Exception as e:
    await update.message.reply_text(
      f"Something went wrong: {type(e).__name__}. Please try again."
    )
    
# HANDLER 2 — PHOTO AND IMAGE MESSAGES

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Handle image messages — screenshots, daigrams, whiteboards, etc."""
  user_id = update.effective_user.id
  
  if not is_allowed(user_id):
    return
  
  await update.message.reply_text("🔍Reading image, working on it...")
  
  try:
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(file_bytes).decode("utf-8")
    
    caption = update.message.caption or "Describe and analyse this image."
    
    response = await run_xoxobot_task(
      query=caption,
      image_base64=image_base64,
    )
    await update.message.reply_text(response)
    
  except Exception as e:
    await update.message.reply_text(
      f"Image processing failed: {type(e).__name__}. Please try again."
    )
    
# HANDLER 3 — SLASH COMMANDS

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """/start command — welcome message."""
  user_id = update.effective_user.id
  if not is_allowed(user_id):
    return
  await update.message.reply_text(
    "Xoxobot ready.\n\n"
    "Send me a query; text, image or a document path from MicroGit.\n"
    "I answer, research, remember and write down what's necessary."
  )
  
async def handle_recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """/recent show last 5 sessions from Kontext."""
  user_id = update.effective_user.id
  if not is_allowed(user_id):
    return
  
  try:
    result = await kontext_get_recent_sessions(limit=5)
    sessions = result.get("sessions", [])
    
    if not sessions:
      await update.message.reply_text("No recent sessions found.")
      return
    
    lines = []
    for s in sessions:
      lines.append(
        f"•{s.get('timestamp', '')[:10]} — {s.get('query', '')[:80]}"
      )
    await update.message.reply_text("Recent sessions:\n\n" + "\n".join(lines))
    
  except Exception as e:
    await update.message.reply_text(
      f"Could not fetch sessions: {type(e).__name__}"
    )
    
async def handle_structure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """/structure — show MicroGit repo tree."""
  user_id = update.effective_user.id
  if not is_allowed(user_id):
    return
  
  try:
    result = await microgit_list_structure()
    tree = result.get("tree", {})
    
    if not tree:
      await update.message.reply_text("MicroGit repo is empty.")
      return
    
    def format_tree(node: dict, indent: int = 0) -> list[str]:
      lines = []
      for key, value in node.items():
        if key == "__files__":
          for f in value:
            lines.append("  " * indent + f"  📄 {f}")
        else:
          lines.append("  " * indent + f"📁 {key}")
          lines.extend(format_tree(value, indent + 1))
      return lines
      
    tree_lines = format_tree(tree)
    await update.message.reply_text(
      "MicroGit structure: \n\n" + "\n".join(tree_lines)
    )
  
  except Exception as e:
    await update.message.reply_text(f"Could not fetch structure: {type(e).__name__}")