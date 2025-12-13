"""Feed handler — 🐶 Лента (StrayVinchi mode)."""

from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import (
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram import InputMediaPhoto

from stray_id.locales import get_text
from stray_id.models.user import Language
from stray_id.models.dog import Dog, DogStatus
from stray_id.storage.memory import storage
from stray_id.keyboards.dog_card import get_dog_card_keyboard
from stray_id.keyboards.main_menu import get_feed_keyboard, get_main_menu
from stray_id.utils.geo import format_distance
from stray_id.handlers import menu


def _get_user_lang(user_id: int) -> Language:
    user = storage.get_or_create_user(user_id)
    return user.language


def _format_time_ago(dt: datetime, lang: Language) -> str:
    """Format time as 'X ago'."""
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


def _format_dog_card(
    dog: Dog, 
    lang: Language,
    user_location: Optional[tuple[float, float]] = None,
) -> str:
    """Format dog info for feed card."""
    lines = []
    
    # Name and ID
    if dog.name:
        lines.append(f"*{dog.name}* {get_text('dog_card_id', lang).format(id=dog.id)}")
    else:
        lines.append(get_text("dog_card_id", lang).format(id=dog.id))
    
    # Location
    address = dog.location.address or f"{dog.location.latitude:.4f}, {dog.location.longitude:.4f}"
    location_line = get_text("dog_card_location", lang).format(address=address)
    
    # Add distance if user location available
    if user_location:
        from stray_id.utils.geo import calculate_distance
        dist = calculate_distance(
            user_location[0], user_location[1],
            dog.location.latitude, dog.location.longitude,
        )
        location_line += " " + get_text("dog_card_distance", lang).format(
            distance=format_distance(dist)
        )
    
    lines.append(location_line)
    
    # Status
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
    
    # Last seen
    lines.append(get_text("dog_card_last_seen", lang).format(
        time=_format_time_ago(dog.last_seen_at, lang)
    ))
    
    return "\n".join(lines)


async def _send_dog_card(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dog: Dog,
    lang: Language,
    show_next: bool = True,
) -> None:
    """Send a dog card message with photo and buttons."""
    text = _format_dog_card(dog, lang)
    # In feed mode, we don't show Next button in inline keyboard anymore
    keyboard = get_dog_card_keyboard(dog, lang, show_next=False)
    
    # Check if this is a lost dog - show alert
    if dog.status == DogStatus.LOST and dog.owner_contact:
        text = get_text("lost_alert", lang).format(contact=dog.owner_contact) + "\n\n" + text
    
    if update.callback_query:
        # Edit existing message (from Next button)
        await update.callback_query.edit_message_media(
            media=None,  # Can't edit media in this simple way
        )
        # Just send new message instead
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=dog.photo_file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        # Store current dog ID for actions
        context.user_data["current_dog_id"] = dog.id
        
        if len(dog.photo_file_ids) > 1:
            media_group = [InputMediaPhoto(media=pid) for pid in dog.photo_file_ids]
            await update.message.reply_media_group(media=media_group)
            
            await update.message.reply_text(
                text=text,
                reply_markup=get_feed_keyboard(lang),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_photo(
                photo=dog.photo_file_id,
                caption=text,
                reply_markup=get_feed_keyboard(lang),
                parse_mode="Markdown",
            )


async def feed_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '🐶 Лента' button — show first dog."""
    lang = _get_user_lang(update.effective_user.id)
    
    dogs = storage.get_all_dogs()
    
    if not dogs:
        await update.message.reply_text(get_text("feed_empty", lang))
        return
    
    # Store current index in user_data
    context.user_data["feed_index"] = 0
    
    await _send_dog_card(update, context, dogs[0], lang, show_next=False)


async def feed_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '➡️ Дальше' button — show next dog."""
    lang = _get_user_lang(update.effective_user.id)
    dogs = storage.get_all_dogs()
    
    if not dogs:
        await update.message.reply_text(get_text("feed_empty", lang))
        return
    
    # Get and increment index
    current_index = context.user_data.get("feed_index", 0)
    next_index = current_index + 1
    
    if next_index >= len(dogs):
        # End of feed
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text("feed_end", lang),
            reply_markup=get_main_menu(lang),
        )
        context.user_data["feed_index"] = 0
        return
    
    context.user_data["feed_index"] = next_index
    dog = dogs[next_index]
    
    await _send_dog_card(update, context, dog, lang, show_next=False)


async def feed_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '☰ Меню' button in feed — exit to main menu."""
    context.user_data.pop("feed_index", None)
    await menu.show_menu(update, context)


async def feed_2gis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle '🌍 2GIS' button."""
    lang = _get_user_lang(update.effective_user.id)
    dog_id = context.user_data.get("current_dog_id")
    
    if not dog_id:
        return
        
    dog = storage.get_dog(dog_id)
    if not dog:
        return
        
    link = get_2gis_link(dog.location.latitude, dog.location.longitude)
    await update.message.reply_text(
        f"{get_text('btn_2gis', lang)}: {link}",
        disable_web_page_preview=True,
    )


def _feed_filter():
    """Filter for feed button text in any language."""
    return filters.Regex(r"^🐶")


# Handlers
handler = MessageHandler(_feed_filter(), feed_start)
next_handler = MessageHandler(filters.Regex(r"^➡️"), feed_next)
exit_handler = MessageHandler(filters.Regex(r"^☰"), feed_exit)
gis_handler = MessageHandler(filters.Regex(r"^🌍"), feed_2gis)
