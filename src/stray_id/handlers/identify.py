"""Identify flow handler — 📸 Кто это?"""

from datetime import datetime
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
from stray_id.models.dog import Dog, DogStatus, Location
from stray_id.storage.memory import storage
from stray_id.search.mock import search_service
from stray_id.keyboards.main_menu import get_main_menu
from stray_id.keyboards.dog_card import get_dog_card_keyboard, get_not_found_keyboard


# Conversation states
WAITING_PHOTO = 0


def _get_user_lang(user_id: int) -> Language:
    """Get user's language preference."""
    user = storage.get_or_create_user(user_id)
    return user.language


def _format_dog_card(dog: Dog, lang: Language) -> str:
    """Format dog info as text message."""
    lines = []

    # ID and name
    id_line = get_text("dog_card_id", lang).format(id=dog.id)
    if dog.name:
        id_line += " " + get_text("dog_card_name", lang).format(name=dog.name)
    lines.append(id_line)

    # Location
    address = (
        dog.location.address
        or f"{dog.location.latitude:.4f}, {dog.location.longitude:.4f}"
    )
    lines.append(get_text("dog_card_location", lang).format(address=address))

    # Last seen time
    delta = datetime.now() - dog.last_seen_at
    if delta.total_seconds() < 60:
        time_str = get_text("time_just_now", lang)
    elif delta.total_seconds() < 3600:
        n = int(delta.total_seconds() // 60)
        time_str = get_text("time_minutes_ago", lang).format(n=n)
    elif delta.total_seconds() < 86400:
        n = int(delta.total_seconds() // 3600)
        time_str = get_text("time_hours_ago", lang).format(n=n)
    else:
        n = int(delta.days)
        time_str = get_text("time_days_ago", lang).format(n=n)
    lines.append(get_text("dog_card_last_seen", lang).format(time=time_str))

    # Status
    match dog.status:
        case DogStatus.STERILIZED:
            lines.append(get_text("dog_card_status_sterilized", lang))
        case DogStatus.STRAY:
            lines.append(get_text("dog_card_status_stray", lang))
        case DogStatus.LOST:
            lines.append(get_text("dog_card_status_lost", lang))
            if dog.owner_contact:
                lines.append(
                    get_text("dog_card_owner", lang).format(contact=dog.owner_contact)
                )

    # Features
    if dog.features:
        feature_texts = []
        for f in dog.features:
            key = f"features_{f.value}"
            feature_texts.append(get_text(key, lang))
        lines.append(
            get_text("dog_card_features", lang).format(
                features=", ".join(feature_texts)
            )
        )

    return "\n".join(lines)


async def identify_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '📸 Кто это?' button — ask for photo."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text("send_photo", lang))
    return WAITING_PHOTO


async def identify_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo received — search in database."""
    lang = _get_user_lang(update.effective_user.id)

    # Show "searching" message
    searching_msg = await update.message.reply_text(get_text("searching", lang))

    # Get photo bytes
    photo = update.message.photo[-1]  # Largest size
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()

    # Search using ML service
    results = await search_service.search_by_photo(bytes(photo_bytes))

    # Delete searching message
    await searching_msg.delete()

    if results:
        # Found! Show dog card
        dog = storage.get_dog(results[0].dog_id)
        if dog:
            text = _format_dog_card(dog, lang)
            await update.message.reply_photo(
                photo=dog.photo_file_id,
                caption=text,
                reply_markup=get_dog_card_keyboard(dog.id, lang),
            )
            return ConversationHandler.END

    # Not found
    context.user_data["pending_photo_id"] = photo.file_id
    await update.message.reply_text(
        get_text("dog_not_found", lang),
        reply_markup=get_not_found_keyboard(lang),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel button."""
    query = update.callback_query
    await query.answer()

    lang = _get_user_lang(update.effective_user.id)
    await query.edit_message_text(get_text("cancelled", lang))
    return ConversationHandler.END


async def mark_sighting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 📍 Отметить встречу button."""
    query = update.callback_query
    await query.answer()

    # Extract dog_id from callback_data
    dog_id = int(query.data.split(":")[1])
    dog = storage.get_dog(dog_id)

    if dog:
        dog.last_seen_at = datetime.now()
        storage.update_dog(dog)

    lang = _get_user_lang(update.effective_user.id)
    await query.answer(get_text("sighting_recorded", lang), show_alert=True)


# Build the handler
def _identify_filter():
    """Filter for identify button text in any language."""
    return filters.Regex(r"^📸")


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_identify_filter(), identify_start),
    ],
    states={
        WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, identify_photo),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
    ],
)

# Standalone callback handlers
sighting_handler = CallbackQueryHandler(mark_sighting, pattern=r"^sighting:\d+$")
