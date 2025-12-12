"""Identify flow handler — 📸 Кто это? with integrated registration."""

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
from stray_id.models.dog import Dog, DogStatus, DogFeature, Location
from stray_id.storage.memory import storage
from stray_id.search.mock import search_service
from stray_id.keyboards.main_menu import get_main_menu, get_location_keyboard
from stray_id.keyboards.dog_card import (
    get_dog_card_keyboard, 
    get_not_found_keyboard,
    get_lost_alert_keyboard,
    SEEN_HERE,
    ADD_PHOTO,
)
from stray_id.keyboards.features import get_features_keyboard, FEATURE_PREFIX, FEATURES_DONE


# Conversation states
WAITING_PHOTO = 0
WAITING_LOCATION = 1
WAITING_NEW_PHOTO = 2
WAITING_FEATURES = 3


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
    address = dog.location.address or f"{dog.location.latitude:.4f}, {dog.location.longitude:.4f}"
    lines.append(get_text("dog_card_location", lang).format(address=address))
    
    # Last seen
    lines.append(get_text("dog_card_last_seen", lang).format(
        time=_format_time_ago(dog.last_seen_at, lang)
    ))
    
    # Status with alert for lost dogs
    match dog.status:
        case DogStatus.STERILIZED:
            lines.append(get_text("dog_card_status_sterilized", lang))
        case DogStatus.STRAY:
            lines.append(get_text("dog_card_status_stray", lang))
        case DogStatus.LOST:
            lines.append(get_text("dog_card_status_lost", lang))
            if dog.owner_contact:
                lines.append(get_text("dog_card_owner", lang).format(contact=dog.owner_contact))
    
    # Features
    if dog.features:
        feature_texts = []
        for f in dog.features:
            key = f"features_{f.value}"
            feature_texts.append(get_text(key, lang))
        lines.append(get_text("dog_card_features", lang).format(
            features=", ".join(feature_texts)
        ))
    
    return "\n".join(lines)


async def identify_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '📸 Кто это?' button — ask for photo."""
    lang = _get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text("send_photo", lang))
    return WAITING_PHOTO


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
                text = get_text("lost_alert", lang).format(contact=dog.owner_contact) + "\n\n" + text
                keyboard = get_lost_alert_keyboard(dog, lang)
            else:
                keyboard = get_dog_card_keyboard(dog, lang, show_next=False)
            
            await update.message.reply_photo(
                photo=dog.photo_file_id,
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
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel button."""
    query = update.callback_query
    await query.answer()
    
    lang = _get_user_lang(update.effective_user.id)
    await query.edit_message_text(get_text("cancelled", lang))
    context.user_data.clear()
    return ConversationHandler.END


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '➕ Зарегистрировать' from search results."""
    query = update.callback_query
    await query.answer()
    
    lang = _get_user_lang(update.effective_user.id)
    
    await query.edit_message_text(get_text("ask_location", lang))
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return WAITING_LOCATION


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


async def finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle ✅ Готово — save dog to database."""
    query = update.callback_query
    await query.answer()
    
    lang = _get_user_lang(update.effective_user.id)
    
    features: set[DogFeature] = context.user_data.get("features", set())
    status = DogStatus.STERILIZED if DogFeature.EAR_TAG in features else DogStatus.STRAY
    
    dog = Dog(
        id=0,
        photo_file_id=context.user_data["pending_photo_id"],
        location=context.user_data["location"],
        status=status,
        features=list(features),
    )
    
    dog = storage.add_dog(dog)
    context.user_data.clear()
    
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


async def seen_here(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '📍 Видел здесь' — request location to update."""
    query = update.callback_query
    await query.answer()
    
    dog_id = int(query.data.split(":")[1])
    context.user_data["update_dog_id"] = dog_id
    
    lang = _get_user_lang(update.effective_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("ask_location", lang),
        reply_markup=get_location_keyboard(lang),
    )
    return WAITING_LOCATION


async def update_dog_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    query = update.callback_query
    await query.answer()
    
    dog_id = int(query.data.split(":")[1])
    context.user_data["add_photo_dog_id"] = dog_id
    
    lang = _get_user_lang(update.effective_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("ask_new_photo", lang),
    )
    return WAITING_NEW_PHOTO


async def add_photo_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new photo for existing dog."""
    lang = _get_user_lang(update.effective_user.id)
    
    dog_id = context.user_data.get("add_photo_dog_id")
    if dog_id:
        dog = storage.get_dog(dog_id)
        if dog:
            photo = update.message.photo[-1]
            dog.photo_file_id = photo.file_id
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


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(_identify_filter(), identify_start),
    ],
    states={
        WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, identify_photo),
        ],
        WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, update_dog_location),
        ],
        WAITING_NEW_PHOTO: [
            MessageHandler(filters.PHOTO, add_photo_receive),
        ],
        WAITING_FEATURES: [
            CallbackQueryHandler(toggle_feature, pattern=f"^{FEATURE_PREFIX}"),
            CallbackQueryHandler(finish_registration, pattern=f"^{FEATURES_DONE}$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CallbackQueryHandler(start_registration, pattern="^register_from_search$"),
        CallbackQueryHandler(seen_here, pattern=f"^{SEEN_HERE}"),
        CallbackQueryHandler(add_photo_start, pattern=f"^{ADD_PHOTO}"),
    ],
)
