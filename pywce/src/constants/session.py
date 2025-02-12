from dataclasses import dataclass


@dataclass(frozen=True)
class SessionConstants:
    EXPIRY = "kexpiry"
    CURRENT_STAGE_RETRY_COUNT = "kretry_count"
    PREV_STAGE = "kprev_stage"
    CURRENT_STAGE = "kcurrent_stage"

    # if chatbot has authentication logic, set this to signal user is authenticated
    VALID_AUTH_SESSION = "kauth_session"
    DYNAMIC_CURRENT_TEMPLATE_BODY = "kcurrent_template_body"
    DYNAMIC_NEXT_TEMPLATE_BODY = "knext_template_body"

    # used to check against wa_id on authentication hook
    VALID_AUTH_MSISDN = "kauth_msisdn"

    # used to check when last user was authenticated against session expiry timeout
    # in ISO 8601 format
    AUTH_EXPIRE_AT = "kauth_expire_on"
    LAST_ACTIVITY_AT = "klast_activity"

    CURRENT_MSG_ID = "kcurrent_msg_id"
    CURRENT_DEBOUNCE = "kcurrent_debounce"

    # if set & exception is encountered / a go back logic is present & user sends a retry message
    # engine will render the latest checkpoint set
    LATEST_CHECKPOINT = "klatest_checkpoint"

    # if its an error message with retry btn, set this & clear it after processing
    DYNAMIC_RETRY = "kdynamic_retry"
    MESSAGE_HISTORY = "kmessage_history"

    # set this to enable user live session
    LIVE_SUPPORT = "k_live_support"