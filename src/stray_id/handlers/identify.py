"""Identify flow handler — 📸 Кто это? with integrated registration."""

from datetime import datetime

from telegram import InputMediaPhoto, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from stray_id.handlers import menu
from stray_id.keyboards.dog_card import get_lost_alert_keyboard
from stray_id.keyboards.features import (
    FEATURE_PREFIX,
    FEATURES_DONE,
    get_features_keyboard,
    get_done_keyboard,
)
from stray_id.keyboards.main_menu import (
    get_cancel_keyboard,
    get_dog_actions_keyboard,
    get_location_keyboard,
    get_main_menu,
    get_not_found_keyboard,
)
from stray_id.locales import get_text
from stray_id.models.dog import Dog, DogFeature, DogStatus, Location
from stray_id.models.user import Language
from stray_id.search.mock import search_service
from stray_id.states import ConversationState
from stray_id.storage.memory import storage


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


def _format_time_ago(dt: datetime, lang: Language) -> str:
    delta = datetime.now() - dt
    if delta.total_seconds() < 60:
        return get_text("time_just_now", lang)
    elif delta.total_seconds() < 3600:
        n = int(delta.total_seconds() // 60)
        return get_text("time_minutes_ago", lang).format(n=n)
    elif delta.total_seconds() < 86400:
        n = int(delta.total_seconds() // 3600)
        return get_text("time_hours_ago", lang).format(n=n)
    else:
        n = int(delta.days)
        return get_text("time_days_ago", lang).format(n=n)


def _format_dog_card(dog: Dog, lang: Language) -> str:
    """Format dog info as text message."""
    lines = []

    # Name and ID
    if dog.name:
        lines.append(f"*{dog.name}* {get_text('dog_card_id', lang).format(id=dog.id)}")
    else:
        lines.append(get_text("dog_card_id", lang).format(id=dog.id))

    # Location
    address = (
        dog.location.address
        or f"{dog.location.latitude:.4f}, {dog.location.longitude:.4f}"
    )
    lines.append(get_text("dog_card_location", lang).format(address=address))

    # Last seen
    lines.append(
        get_text("dog_card_last_seen", lang).format(
            time=_format_time_ago(dog.last_seen_at, lang)
        )
    )

    # Status with alert for lost dogs
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
    await update.message.reply_text(
        get_text("send_photo", lang),
        reply_markup=get_cancel_keyboard(lang),
    )
    return ConversationState.WAITING_PHOTO


async def identify_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo received — search in database."""
    lang = _get_user_lang(update.effective_user.id)

    searching_msg = await update.message.reply_text(get_text("searching", lang))

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()

    results = await search_service.search_by_photo(bytes(photo_bytes))

    await searching_msg.delete()

    if results:
        dog = storage.get_dog(results[0].dog_id)
        if dog:
            text = _format_dog_card(dog, lang)

            # Show alert for lost dogs
            if dog.status == DogStatus.LOST and dog.owner_contact:
                text = (
                    get_text("lost_alert", lang).format(contact=dog.owner_contact)
                    + "\n\n"
                    + text
                )
                keyboard = get_lost_alert_keyboard(
                    dog, lang
                )  # Keep inline for alert? Or change? User said "replace all".
                # But alert usually has "Call owner" which is a URL button (inline only).
                # Let's keep inline for Lost Alert for now as it might have URL buttons.
                # Actually, let's use get_dog_actions_keyboard for normal found dogs.
            else:
                keyboard = get_dog_actions_keyboard(lang)

            if len(dog.photo_file_ids) > 1:
                media_group = [InputMediaPhoto(media=pid) for pid in dog.photo_file_ids]
                await update.message.reply_media_group(media=media_group)

                await update.message.reply_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_photo(
                    photo=dog.photo_file_ids[0],
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            context.user_data["found_dog_id"] = dog.id
            return ConversationHandler.END

    # Not found — offer to register
    context.user_data["pending_photo_id"] = photo.file_id
    await update.message.reply_text(
        get_text("dog_not_found", lang),
        reply_markup=get_not_found_keyboard(lang),
    )
    return ConversationState.WAITING_DECISION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel button."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("cancelled", lang),
        reply_markup=get_main_menu(lang),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '➕ Зарегистрировать'."""
    lang = _get_user_lang(update.effective_user.id)

    await update.message.reply_text(
        text=get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return ConversationState.WAITING_LOCATION


async def register_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location received during registration."""
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
    await update.message.reply_text(
        text=get_text("press_done_hint", lang),
        reply_markup=get_done_keyboard(lang),
    )
    return ConversationState.WAITING_FEATURES


async def toggle_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle feature toggle button (callback)."""
    query = update.callback_query
    await query.answer()

    lang = _get_user_lang(update.effective_user.id)
    data = query.data

    # Extract feature value from callback data
    feature_value = data.replace(FEATURE_PREFIX, "")

    # Find which feature was clicked
    clicked_feature = None
    for f in DogFeature:
        if f.value == feature_value:
            clicked_feature = f
            break

    if clicked_feature:
        selected: set = context.user_data.get("features", set())
        if clicked_feature in selected:
            selected.discard(clicked_feature)
        else:
            selected.add(clicked_feature)
        context.user_data["features"] = selected

    await query.edit_message_reply_markup(
        reply_markup=get_features_keyboard(
            context.user_data.get("features", set()), lang
        ),
    )
    return ConversationState.WAITING_FEATURES


async def finish_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle ✅ Готово — save dog to database."""
    # This is now a MessageHandler (Reply Keyboard), so update.message is valid.
    lang = _get_user_lang(update.effective_user.id)

    features: set[DogFeature] = context.user_data.get("features", set())
    status = DogStatus.STERILIZED if DogFeature.EAR_TAG in features else DogStatus.STRAY

    dog = Dog(
        id=0,
        photo_file_ids=[context.user_data["pending_photo_id"]],
        location=context.user_data["location"],
        status=status,
        features=list(features),
    )

    dog = storage.add_dog(dog)
    context.user_data.clear()

    await update.message.reply_text(
        get_text("dog_registered", lang).format(id=dog.id),
    )
    await update.message.reply_text(
        text=get_text("welcome", lang),
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def seen_here(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '📍 Видел здесь' — request location to update."""
    lang = _get_user_lang(update.effective_user.id)

    # Try to get dog ID from feed or identify result
    dog_id = context.user_data.get("current_dog_id") or context.user_data.get(
        "found_dog_id"
    )

    if not dog_id:
        # Should not happen if flow is correct, but safety check
        await update.message.reply_text(
            get_text("error_no_location", lang)
        )  # Or generic error
        return ConversationHandler.END

    context.user_data["update_dog_id"] = dog_id

    await update.message.reply_text(
        text=get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return ConversationState.WAITING_LOCATION


async def update_dog_location(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle location for updating existing dog."""
    lang = _get_user_lang(update.effective_user.id)

    dog_id = context.user_data.get("update_dog_id")
    if dog_id:
        dog = storage.get_dog(dog_id)
        if dog:
            location = update.message.location
            dog.location = Location(
                latitude=location.latitude,
                longitude=location.longitude,
            )
            dog.last_seen_at = datetime.now()
            storage.update_dog(dog)

        context.user_data.pop("update_dog_id", None)
        await update.message.reply_text(
            get_text("sighting_recorded", lang),
            reply_markup=get_main_menu(lang),
        )
        return ConversationHandler.END

    # No update_dog_id means this is new registration
    return await register_location(update, context)


async def add_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '📷 Добавить фото' button."""
    lang = _get_user_lang(update.effective_user.id)

    dog_id = context.user_data.get("current_dog_id") or context.user_data.get(
        "found_dog_id"
    )

    if not dog_id:
        await update.message.reply_text(get_text("error_no_photo", lang))
        return ConversationHandler.END

    context.user_data["add_photo_dog_id"] = dog_id

    await update.message.reply_text(
        text=get_text("ask_new_photo", lang),
        reply_markup=get_cancel_keyboard(lang),
    )
    return ConversationState.WAITING_NEW_PHOTO


async def add_photo_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new photo for existing dog."""
    lang = _get_user_lang(update.effective_user.id)

    dog_id = context.user_data.get("add_photo_dog_id")
    if dog_id:
        dog = storage.get_dog(dog_id)
        if dog:
            photo = update.message.photo[-1]
            if not dog.photo_file_ids:
                dog.photo_file_ids = []
            dog.photo_file_ids.append(photo.file_id)
            dog.last_seen_at = datetime.now()
            storage.update_dog(dog)

        context.user_data.pop("add_photo_dog_id", None)

    await update.message.reply_text(
        get_text("photo_added", lang),
        reply_markup=get_main_menu(lang),
    )
    return ConversationHandler.END


def _identify_filter():
    return filters.Regex(r"^📸")


def _seen_here_filter():
    return filters.Regex(r"^📍")


def _add_photo_filter():
    return filters.Regex(r"^📷")


def _register_filter():
    return filters.Regex(r"^➕")


def _cancel_filter():
    return filters.Regex(r"^❌")


async def menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle menu button during conversation."""
    context.user_data.clear()
    await menu.back_to_main(update, context)
    return ConversationHandler.END


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_identify_filter(), identify_start),
        MessageHandler(_seen_here_filter(), seen_here),
        MessageHandler(_add_photo_filter(), add_photo_start),
    ],
    states={
        ConversationState.WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, identify_photo),
        ],
        ConversationState.WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, update_dog_location),
        ],
        ConversationState.WAITING_NEW_PHOTO: [
            MessageHandler(filters.PHOTO, add_photo_receive),
        ],
        ConversationState.WAITING_FEATURES: [
            MessageHandler(filters.Regex(r"^✅"), finish_registration),
            CallbackQueryHandler(toggle_feature, pattern=f"^{FEATURE_PREFIX}"),
        ],
        ConversationState.WAITING_DECISION: [
            MessageHandler(_cancel_filter(), cancel),
            MessageHandler(_register_filter(), start_registration),
        ],
    },
    fallbacks=[
        MessageHandler(_cancel_filter(), cancel),
        MessageHandler(_register_filter(), start_registration),
        MessageHandler(_seen_here_filter(), seen_here),
        MessageHandler(_add_photo_filter(), add_photo_start),
        MessageHandler(filters.Regex(r"^☰"), menu_fallback),
    ],
)
