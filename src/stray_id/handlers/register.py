"""Register flow handler — ➕ Добавить."""

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
from stray_id.models.dog import Dog, DogStatus, DogFeature, Location
from stray_id.storage.memory import storage
from stray_id.search.mock import search_service
from stray_id.keyboards.main_menu import get_main_menu, get_location_keyboard
from stray_id.keyboards.features import (
    get_features_keyboard,
    FEATURE_PREFIX,
    FEATURES_DONE,
)


# Conversation states
WAITING_PHOTO = 0
WAITING_LOCATION = 1
WAITING_FEATURES = 2


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '➕ Добавить' button — ask for photo."""
    lang = _get_user_lang(update.effective_user.id)

    # Check if coming from identify flow with pending photo
    if context.user_data.get("pending_photo_id"):
        context.user_data["photo_id"] = context.user_data.pop("pending_photo_id")
        await update.message.reply_text(
            get_text("ask_location", lang),
            reply_markup=get_location_keyboard(lang),
        )
        return WAITING_LOCATION

    await update.message.reply_text(get_text("send_dog_photo", lang))
    return WAITING_PHOTO


async def register_from_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle 'Да, зарегистрировать' from search results."""
    query = update.callback_query
    await query.answer()

    lang = _get_user_lang(update.effective_user.id)

    # Photo already saved in pending_photo_id
    if context.user_data.get("pending_photo_id"):
        context.user_data["photo_id"] = context.user_data.pop("pending_photo_id")
        await query.edit_message_text(get_text("ask_location", lang))
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text("ask_location", lang),
            reply_markup=get_location_keyboard(lang),
        )
        return WAITING_LOCATION

    # No pending photo, ask for one
    await query.edit_message_text(get_text("send_dog_photo", lang))
    return WAITING_PHOTO


async def register_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo received."""
    lang = _get_user_lang(update.effective_user.id)

    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    await update.message.reply_text(
        get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return WAITING_LOCATION


async def register_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location received."""
    lang = _get_user_lang(update.effective_user.id)

    location = update.message.location
    context.user_data["location"] = Location(
        latitude=location.latitude,
        longitude=location.longitude,
    )
    context.user_data["features"] = set()

    await update.message.reply_text(
        get_text("ask_features", lang),
        reply_markup=get_features_keyboard(set(), lang),
    )
    return WAITING_FEATURES


async def toggle_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle feature toggle button."""
    query = update.callback_query
    await query.answer()

    lang = _get_user_lang(update.effective_user.id)
    feature_value = query.data.replace(FEATURE_PREFIX, "")
    feature = DogFeature(feature_value)

    selected: set = context.user_data.get("features", set())
    if feature in selected:
        selected.discard(feature)
    else:
        selected.add(feature)
    context.user_data["features"] = selected

    await query.edit_message_reply_markup(
        reply_markup=get_features_keyboard(selected, lang),
    )
    return WAITING_FEATURES


async def finish_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle ✅ Готово — save dog to database."""
    query = update.callback_query
    await query.answer()

    lang = _get_user_lang(update.effective_user.id)

    # Create dog
    features: set[DogFeature] = context.user_data.get("features", set())

    # Determine status based on ear tag
    status = DogStatus.STERILIZED if DogFeature.EAR_TAG in features else DogStatus.STRAY

    dog = Dog(
        id=0,  # Will be assigned by storage
        photo_file_id=context.user_data["photo_id"],
        location=context.user_data["location"],
        status=status,
        features=list(features),
    )

    # Save to storage
    dog = storage.add_dog(dog)

    # Index in search (for future similarity search)
    # Note: we don't have photo bytes here, just file_id
    # In real implementation, download and index

    # Clear user data
    context.user_data.clear()

    # Send success message
    await query.edit_message_text(
        get_text("dog_registered", lang).format(id=dog.id),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("welcome", lang),
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def _register_filter():
    """Filter for register button text in any language."""
    return filters.Regex(r"^➕")


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_register_filter(), register_start),
        CallbackQueryHandler(register_from_search, pattern="^register_from_search$"),
    ],
    states={
        WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, register_photo),
        ],
        WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, register_location),
        ],
        WAITING_FEATURES: [
            CallbackQueryHandler(toggle_feature, pattern=f"^{FEATURE_PREFIX}"),
            CallbackQueryHandler(finish_registration, pattern=f"^{FEATURES_DONE}$"),
        ],
    },
    fallbacks=[],
)
