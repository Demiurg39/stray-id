"""Stray ID Bot — entry point."""

import logging
import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from stray_id.handlers import start, identify, register, lost, profile

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")


def main() -> None:
    if TOKEN is None:
        log.error("BOT_TOKEN is not set in environment")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers in order of priority
    # 1. Start conversation (language selection)
    application.add_handler(start.handler)

    # 2. Main flows (ConversationHandlers)
    application.add_handler(identify.conversation_handler)
    application.add_handler(register.conversation_handler)
    application.add_handler(lost.conversation_handler)

    # 3. Profile (simple message handler)
    application.add_handler(profile.handler)
    application.add_handler(profile.language_handler)

    # 4. Standalone callback handlers
    application.add_handler(identify.sighting_handler)

    log.info("🐕 Stray ID Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
