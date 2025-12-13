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
from stray_id.keyboards.main_menu import get_menu_keyboard, get_main_menu


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '🍔 Меню' button — show hamburger menu."""
    lang = _get_user_lang(update.effective_user.id)
    text = get_text("menu_title", lang)
    if not text:
        text = "Menu"
    
    await update.message.reply_text(
        text,
        reply_markup=get_menu_keyboard(lang),
        parse_mode="Markdown",
    )


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'ℹ️ О проекте' button."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("about_text", lang),
        parse_mode="Markdown",
    )


async def show_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '💝 Донаты' button."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("donate_text", lang),
        parse_mode="Markdown",
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '❌ Отмена' (Back) button from menu."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown",
    )


def _menu_filter():
    """Filter for menu button text in any language."""
    return filters.Regex(r"^☰")

def _about_filter():
    return filters.Regex(r"^ℹ️")

def _donate_filter():
    return filters.Regex(r"^💝")

def _back_filter():
    return filters.Regex(r"^❌")


# Handlers
handler = MessageHandler(_menu_filter(), show_menu)
about_handler = MessageHandler(_about_filter(), show_about)
donate_handler = MessageHandler(_donate_filter(), show_donate)
back_handler = MessageHandler(_back_filter(), back_to_main)
