from enum import Enum

class MessageTypeEnum(Enum):
    TEXT = 1
    BUTTON = 2
    STICKER = 3
    LOCATION = 4
    IMAGE = 5
    DOCUMENT = 6
    VIDEO = 7
    AUDIO = 8
    REACTION = 9
    UNKNOWN = 10
    UNSUPPORTED = 11
    ORDER = 12
    CONTACTS = 13
    INTERACTIVE = 14

    # interactive inner types
    INTERACTIVE_LIST = 15
    INTERACTIVE_FLOW = 16
    INTERACTIVE_BUTTON = 17

    # others
    MEDIA=18
