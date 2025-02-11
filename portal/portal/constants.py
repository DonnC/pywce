class ChatRole:
    ADMIN = "admin"
    USER = "user"

class RequestChatState:
    NEW = "new"
    OPEN = "open"
    CLOSED = "closed"

class PubSubChannel:
    CHANNEL = "webhook:*"
    INCOMING = "webhook:incoming"
    OUTGOING = "webhook:outgoing"

TERMINATION_COMMAND = "/stop"