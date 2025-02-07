class ChatRole:
    ADMIN = "admin"
    USER = "user"

class RequestChatState:
    """
      1   - requesting live support
      0   - acquired communication link
      -1  - no agent available

    """
    NEW = 1
    OPEN = 0
    CLOSED = 2
    OFFLINE = -1

class PubSubChannel:
    CHANNEL = "webhook:*"
    INCOMING = "webhook:incoming"
    OUTGOING = "webhook:outgoing"

TERMINATION_COMMAND = "/stop"