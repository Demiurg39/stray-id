"""Start command and language selection handler."""

from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from stray_id.locales import get_text
from stray_id.models.user import Language
from stray_id.storage.memory import storage
from stray_id.keyboards.main_menu import get_main_menu, get_language_keyboard


from stray_id.states import ConversationState


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command — ask for language."""
    await update.message.reply_text(
        get_text("choose_language"),
        reply_markup=get_language_keyboard(),
    )
    return ConversationState.CHOOSING_LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection."""
    text = update.message.text
    user_id = update.effective_user.id

    if "Русский" in text:
        lang = Language.RU
    elif "Кыргызча" in text:
        lang = Language.KG
    else:
        # Unknown, default to Russian
        lang = Language.RU

    storage.set_user_language(user_id, lang)

    # Send welcome message with main menu
    await update.message.reply_text(
        get_text("language_set", lang),
    )
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# Conversation handler for /start
handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ConversationState.CHOOSING_LANGUAGE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                set_language,
            ),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
)
