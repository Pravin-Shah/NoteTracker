"""
Telegram Bot for NoteTracker Second Brain.
Supports:
/brain dump <text> - Save a raw thought
/brain ask <question> - Ask your brain a question
/brain ingest - Trigger ingestion manually
/brain lint - Run health check
"""
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Add project root to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.general.utils.brain_ops import add_raw_dump
from apps.general.utils.brain_engine import BrainEngine

load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
DEFAULT_USER_ID = int(os.getenv("DEFAULT_USER_ID", "1"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Brain Bot Active. Use /brain dump, /brain ask, /brain ingest, /brain lint.")

async def brain_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = " ".join(context.args)
    if not content:
        await update.message.reply_text("Usage: /brain dump <your thought>")
        return
    
    try:
        raw_id = add_raw_dump(DEFAULT_USER_ID, content, source_type='telegram')
        await update.message.reply_text(f"✅ Dumped to brain (ID: {raw_id}). It will be processed nightly.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def brain_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("Usage: /brain ask <question>")
        return
    
    await update.message.reply_text("🤔 Thinking...")
    
    try:
        engine = BrainEngine(DEFAULT_USER_ID)
        answer = engine.query(question)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def brain_ingest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Starting ingestion...")
    try:
        engine = BrainEngine(DEFAULT_USER_ID)
        result = engine.ingest()
        await update.message.reply_text(f"✅ {result}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def brain_lint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Running health check...")
    try:
        engine = BrainEngine(DEFAULT_USER_ID)
        result = engine.lint()
        score = result.get('health_score', 0)
        await update.message.reply_text(f"✅ Lint complete. Health Score: {score}/100. Report saved to wiki.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == '__main__':
    if not TOKEN or TOKEN == "your_token_here":
        print("Error: TELEGRAM_TOKEN not set in .env")
        sys.exit(1)

    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('brain', start)) # Alias
    
    # Nested commands under /brain (handled via args for simplicity, or separate handlers)
    application.add_handler(CommandHandler('brain_dump', brain_dump))
    
    # Or more advanced: separate handlers for each sub-command
    # But user asked for /brain dump <thought>
    # To handle /brain dump, we can use a single /brain handler that parses args[0]
    
    async def brain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await start(update, context)
            return
        
        cmd = context.args[0].lower()
        context.args = context.args[1:] # Shift args
        
        if cmd == 'dump':
            await brain_dump(update, context)
        elif cmd == 'ask':
            await brain_ask(update, context)
        elif cmd == 'ingest':
            await brain_ingest(update, context)
        elif cmd == 'lint':
            await brain_lint(update, context)
        else:
            await update.message.reply_text(f"Unknown command: {cmd}. Try dump, ask, ingest, lint.")

    application.add_handler(CommandHandler('brain', brain_handler))
    
    print("Bot is running...")
    application.run_polling()
