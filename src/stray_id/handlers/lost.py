"""Lost pet flow handler — 🆘 Потеряшка."""

from telegram import Update
from telegram.ext import (
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from stray_id.locales import get_text
from stray_id.models.user import Language
from stray_id.models.dog import Dog, DogStatus, Location
from stray_id.storage.memory import storage
from stray_id.keyboards.main_menu import get_main_menu, get_location_keyboard


# Conversation states
WAITING_PHOTO = 0
WAITING_LOCATION = 1
WAITING_CONTACT = 2


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


async def lost_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '🆘 Потеряшка' button."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("lost_description", lang),
        parse_mode="Markdown",
    )
    await update.message.reply_text(get_text("send_dog_photo", lang))
    return WAITING_PHOTO


async def lost_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo received."""
    lang = _get_user_lang(update.effective_user.id)

    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    await update.message.reply_text(
        get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return WAITING_LOCATION


async def lost_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location received."""
    lang = _get_user_lang(update.effective_user.id)

    location = update.message.location
    context.user_data["location"] = Location(
        latitude=location.latitude,
        longitude=location.longitude,
    )

    await update.message.reply_text(
        get_text("ask_owner_contact", lang),
        reply_markup=get_main_menu(lang),  # Remove location keyboard
    )
    return WAITING_CONTACT


async def lost_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact info received — save lost pet."""
    lang = _get_user_lang(update.effective_user.id)

    contact = update.message.text

    dog = Dog(
        id=0,
        photo_file_id=context.user_data["photo_id"],
        location=context.user_data["location"],
        status=DogStatus.LOST,
        owner_contact=contact,
    )

    dog = storage.add_dog(dog)
    context.user_data.clear()

    await update.message.reply_text(
        get_text("lost_registered", lang).format(id=dog.id),
        reply_markup=get_main_menu(lang),
    )
    return ConversationHandler.END


def _lost_filter():
    """Filter for lost button text in any language."""
    return filters.Regex(r"^🆘")


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_lost_filter(), lost_start),
    ],
    states={
        WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, lost_photo),
        ],
        WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, lost_location),
        ],
        WAITING_CONTACT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, lost_contact),
        ],
    },
    fallbacks=[],
)
