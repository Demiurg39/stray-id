"""Profile handler — 👤 Профиль (from menu)."""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from stray_id.locales import get_text
from stray_id.models.user import Language
from stray_id.storage.memory import storage
from stray_id.keyboards.main_menu import get_main_menu


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


def _get_profile_keyboard(lang: Language) -> InlineKeyboardMarkup:
    """Profile action buttons."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=get_text("btn_change_language", lang),
            callback_data="change_language",
        )],
    ])


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Профиль' from menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = _get_user_lang(user_id)
    
    all_dogs = storage.get_all_dogs()
    upload_count = len(all_dogs)
    
    lang_display = "Русский 🇷🇺" if lang == Language.RU else "Кыргызча 🇰🇬"
    
    text = (
        f"{get_text('profile_title', lang)}\n\n"
        f"{get_text('profile_language', lang).format(lang=lang_display)}\n"
        f"{get_text('profile_uploads', lang).format(count=upload_count)}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=_get_profile_keyboard(lang),
    )


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language change from profile."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    current_lang = _get_user_lang(user_id)
    
    new_lang = Language.KG if current_lang == Language.RU else Language.RU
    storage.set_user_language(user_id, new_lang)
    
    await query.edit_message_text(
        get_text("language_set", new_lang),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("welcome", new_lang),
        reply_markup=get_main_menu(new_lang),
        parse_mode="Markdown",
    )


# Handlers (now triggered from menu callback)
handler = CallbackQueryHandler(show_profile, pattern="^menu:profile$")
language_handler = CallbackQueryHandler(change_language, pattern="^change_language$")
