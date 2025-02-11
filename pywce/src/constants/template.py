from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateConstants:
    """
    All supported engine template fields

    :var REPLY_MESSAGE_ID: Supports str | bool. Str, the static message id to reply to. Bool, true to tag
                           (reply to) user message when rendering this template.

    :var TEMPLATE_TYPE: the supported engine template type which results in a message to render
    :var READ_RECEIPT: bool - whether to mark user message as read or not
    :var SESSION: bool - If set, skip engine session processing. Treat message like a quick, once-off message.
    :var DYNAMIC_ROUTER: hook - used to determine next route to jump to and skip the configured next route
    :var TRANSIENT: bool - If set, engine skips processing this stage for rendering.
    """

    TEMPLATE_TYPE = "type"
    CHECKPOINT = "checkpoint"
    READ_RECEIPT = "ack"

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
    MESSAGE_URL = "url"
    MESSAGE_MEDIA_CAPTION = "caption"
    MESSAGE_MEDIA_FILENAME = "filename"
    MESSAGE_BUTTONS = "buttons"
    MESSAGE_SECTIONS = "sections"

    # inner, catalog / product keys
    MESSAGE_CATALOG_PRODUCT_ID = "product-id"
    MESSAGE_CATALOG_ID = "catalog-id"
