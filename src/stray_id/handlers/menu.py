"""Hamburger menu handler — 🍔 Меню."""

from telegram import Update
from telegram.ext import (
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from stray_id.locales import get_text
from stray_id.models.user import Language
from stray_id.storage.memory import storage
from stray_id.keyboards.main_menu import get_hamburger_menu, get_main_menu


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '🍔 Меню' button — show hamburger menu."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("menu_title", lang),
        reply_markup=get_hamburger_menu(lang),
        parse_mode="Markdown",
    )


async def menu_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'О проекте' menu item."""
    query = update.callback_query
    await query.answer()
    
    lang = _get_user_lang(update.effective_user.id)
    await query.edit_message_text(
        get_text("about_text", lang),
        parse_mode="Markdown",
    )


async def menu_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Донаты' menu item."""
    query = update.callback_query
    await query.answer()
    
    lang = _get_user_lang(update.effective_user.id)
    await query.edit_message_text(
        get_text("donate_text", lang),
        parse_mode="Markdown",
    )


def _menu_filter():
    """Filter for menu button text in any language."""
    return filters.Regex(r"^🍔")


# Handlers
handler = MessageHandler(_menu_filter(), show_menu)
about_handler = CallbackQueryHandler(menu_about, pattern="^menu:about$")
donate_handler = CallbackQueryHandler(menu_donate, pattern="^menu:donate$")
