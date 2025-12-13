"""Stray ID Bot — entry point."""

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from stray_id.handlers import start, identify, lost, profile, feed, menu

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    log.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    if TOKEN is None:
        log.error("BOT_TOKEN is not set in environment")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).build()

    # Register handlers in order of priority

    # 1. Start conversation (language selection)
    application.add_handler(start.handler)

    # 2. Main flow: Identify with integrated registration
    application.add_handler(identify.conversation_handler)

    # 3. Lost pet flow (from menu)
    application.add_handler(lost.conversation_handler)

    # 4. Feed (🐶 Лента)
    application.add_handler(feed.handler)
    application.add_handler(feed.next_handler)

    # 5. Hamburger menu (🍔 Меню)
    application.add_handler(menu.handler)
    application.add_handler(menu.about_handler)
    application.add_handler(menu.donate_handler)

    # 6. Profile (from menu)
    application.add_handler(profile.handler)
    application.add_handler(profile.language_handler)

    # Error handler
    application.add_error_handler(error_handler)

    log.info("🐕 Stray ID Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
