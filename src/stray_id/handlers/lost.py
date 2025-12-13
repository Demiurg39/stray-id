"""Lost pet flow handler — 🆘 Потеряшка (from menu)."""

from datetime import datetime

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from stray_id.handlers import menu
from stray_id.keyboards.dog_card import get_lost_alert_keyboard
from stray_id.keyboards.main_menu import (
    get_contact_keyboard,
    get_location_keyboard,
    get_main_menu,
    get_cancel_keyboard,
    get_yes_no_keyboard,
)
from stray_id.locales import get_text
from stray_id.models.dog import Dog, DogStatus, Location
from stray_id.models.user import Language
from stray_id.search.mock import search_service
from stray_id.states import ConversationState
from stray_id.storage.memory import storage
from stray_id.utils.geo import get_2gis_link


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


async def lost_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '🆘 Я потерял собаку' from menu."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("lost_ask_photo", lang),
        reply_markup=get_cancel_keyboard(lang),
    )
    return ConversationState.WAITING_PHOTO


async def lost_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo received."""
    lang = _get_user_lang(update.effective_user.id)

    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    await update.message.reply_text(
        get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return ConversationState.WAITING_LOCATION


async def lost_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location received."""
    lang = _get_user_lang(update.effective_user.id)

    location = update.message.location
    context.user_data["location"] = Location(
        latitude=location.latitude,
        longitude=location.longitude,
    )

    # Initialize name as None
    context.user_data["name"] = None

    await update.message.reply_text(
        get_text("ask_name_decision", lang),
        reply_markup=get_yes_no_keyboard(lang),
    )
    return ConversationState.WAITING_NAME_DECISION


async def lost_name_decision(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle name decision (Yes/No)."""
    lang = _get_user_lang(update.effective_user.id)
    text = update.message.text
    
    if text == get_text("btn_yes_name", lang):
        await update.message.reply_text(
            get_text("ask_name_input", lang),
            reply_markup=get_cancel_keyboard(lang),
        )
        return ConversationState.WAITING_NAME_INPUT
    
    # If No (or anything else), proceed to contact
    return await _ask_contact(update, context, lang)


async def lost_name_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle name input."""
    lang = _get_user_lang(update.effective_user.id)
    name = update.message.text
    context.user_data["name"] = name
    
    return await _ask_contact(update, context, lang)


async def _ask_contact(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: Language
) -> int:
    """Ask for contact (shared step)."""
    await update.message.reply_text(
        get_text("ask_owner_contact", lang),
        reply_markup=get_contact_keyboard(lang),
    )
    return ConversationState.WAITING_CONTACT


async def lost_contact_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle contact shared via button."""
    lang = _get_user_lang(update.effective_user.id)

    contact = update.message.contact
    phone = contact.phone_number

    return await _finish_lost_registration(update, context, phone, lang)


async def lost_contact_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact entered as text."""
    lang = _get_user_lang(update.effective_user.id)
    phone = update.message.text

    return await _finish_lost_registration(update, context, phone, lang)


async def _finish_lost_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    phone: str,
    lang: Language,
) -> int:
    """Complete lost pet registration."""

    # First, search in existing database
    if "photo_id" not in context.user_data:
        await update.message.reply_text(
            get_text(
                "error_session_expired", lang
            ),  # You might need to add this key or use a generic one
            reply_markup=get_main_menu(lang),
        )
        return ConversationHandler.END

    photo_id = context.user_data["photo_id"]

    # Try to find dog with ML (mock always returns empty)
    file = await context.bot.get_file(photo_id)
    photo_bytes = await file.download_as_bytearray()
    results = await search_service.search_by_photo(bytes(photo_bytes))

    location: Location = context.user_data["location"]

    if results:
        # Found existing dog — update it with LOST status
        dog = storage.get_dog(results[0].dog_id)
        if dog:
            dog.status = DogStatus.LOST
            dog.owner_contact = phone
            dog.location = location
            dog.last_seen_at = datetime.now()
            # Update name if provided
            if context.user_data.get("name"):
                dog.name = context.user_data.get("name")
            storage.update_dog(dog)

            # Notify user
            await update.message.reply_text(
                get_text("lost_found_in_db", lang),
                parse_mode="Markdown",
            )

            # Send 2GIS link
            gis_url = get_2gis_link(dog.location.latitude, dog.location.longitude)
            await update.message.reply_text(
                f"📍 Последняя геолокация: {gis_url}",
            )

            await update.message.reply_text(
                get_text("lost_registered", lang).format(id=dog.id),
                reply_markup=get_main_menu(lang),
            )

            context.user_data.clear()
            return ConversationHandler.END

    # Not found — create new dog with LOST status
    dog = Dog(
        id=0,
        photo_file_ids=[photo_id],
        location=location,
        status=DogStatus.LOST,
        owner_contact=phone,
        name=context.user_data.get("name"),
    )

    dog = storage.add_dog(dog)
    context.user_data.clear()

    await update.message.reply_text(
        get_text("lost_registered", lang).format(id=dog.id),
        reply_markup=get_main_menu(lang),
    )


async def menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle menu button during conversation."""
    context.user_data.clear()
    await menu.show_menu(update, context)
    return ConversationHandler.END


def _lost_filter():
    return filters.Regex(r"^🆘")


def _cancel_filter():
    return filters.Regex(r"^❌")


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_lost_filter(), lost_start),
    ],
    states={
        ConversationState.WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, lost_photo),
        ],
        ConversationState.WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, lost_location),
        ],
        ConversationState.WAITING_CONTACT: [
            MessageHandler(filters.CONTACT, lost_contact_button),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lost_contact_text),
        ],
        ConversationState.WAITING_NAME_DECISION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, lost_name_decision),
        ],
        ConversationState.WAITING_NAME_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, lost_name_input),
        ],
    },
    fallbacks=[
        MessageHandler(filters.Regex(r"^☰"), menu_fallback),
        MessageHandler(_cancel_filter(), menu_fallback),  # Cancel goes back to menu
    ],
)
