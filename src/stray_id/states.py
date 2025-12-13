from enum import IntEnum

class ConversationState(IntEnum):
    """Shared conversation states for all handlers."""
    CHOOSING_LANGUAGE = 0
    WAITING_PHOTO = 1
    WAITING_LOCATION = 2
    WAITING_NEW_PHOTO = 3
    WAITING_FEATURES = 4
    WAITING_CONTACT = 5
    WAITING_DECISION = 6
    WAITING_NAME_DECISION = 7
    WAITING_NAME_INPUT = 8
    WAITING_ADD_NAME = 9
