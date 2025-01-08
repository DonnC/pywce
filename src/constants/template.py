from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateConstants:
    TEMPLATE_TYPE = "type"
    CHECKPOINT = "checkpoint"
    READ_RECEIPT = "ack"

    # boolean: If true or set, skip session processing. Treat it like a quick message, once-off
    SESSION = "session"
    PROP = "prop"
    AUTHENTICATED = "authenticated"
    ON_RECEIVE = "on-receive"
    REPLY_MESSAGE_ID = "message-id"
    ON_GENERATE = "on-generate"
    VALIDATOR = "validator"
    TRANSIENT = "transient"
    ROUTES = "routes"
    DYNAMIC_ROUTER = "router"
    MIDDLEWARE = "middleware"
    TEMPLATE = "template"
    PARAMS = "params"

   # inner template keys
    MESSAGE = "message"
    MESSAGE_TITLE = "title"
    MESSAGE_BODY = "body"
    MESSAGE_FOOTER = "footer"
    MESSAGE_MEDIA_ID = "id"
    MESSAGE_MEDIA_CAPTION = "caption"
    MESSAGE_MEDIA_FILENAME = "filename"
    MESSAGE_BUTTONS = "buttons"
    MESSAGE_SECTIONS = "sections"

