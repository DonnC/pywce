from dataclasses import dataclass


@dataclass(frozen=True)
class SessionConstants:
    EXPIRY = "pywce_expiry"
    CURRENT_STAGE_RETRY_COUNT = "pywce_retry_count"
    PREV_STAGE = "pywce_prev_stage"
    CURRENT_STAGE = "pywce_current_stage"

    # if chatbot has authentication logic, set this to signal user is authenticated
    VALID_AUTH_SESSION = "pywce_auth_session"
    # used to check when last user was authenticated against session expiry timeout
    # in ISO 8601 format
    AUTH_EXPIRE_AT = "pywce_auth_expire_on"

    LAST_ACTIVITY_AT = "pywce_last_activity"

    CURRENT_MSG_ID = "pywce_msg_id"
    CURRENT_DEBOUNCE = "pywce_debounce"

    # if set & exception is encountered / a go back logic is present & user sends a retry message
    # engine will render the latest checkpoint set
    LATEST_CHECKPOINT = "pywce_checkpoint"

    # if its an error message with retry btn, set this & clear it after processing
    DYNAMIC_RETRY = "pywce_dynamic_retry"
    MESSAGE_HISTORY = "pywce_history"

    # set this to enable user external handlers e.g live support / ai agent etc
    EXTERNAL_CHAT_HANDLER = "pywce_ext_handler"
