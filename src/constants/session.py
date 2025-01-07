from dataclasses import dataclass


@dataclass(frozen=True)
class SessionConstants:
    EXPIRY = "k_pywce_expiry"
    CURRENT_STAGE_RETRY_COUNT = "k_pywce_retry_count"
    PREV_STAGE = "k_pywce_prev_stage"
    CURRENT_STAGE = "k_pywce_current_stage"

    # if chatbot has authentication logic, set this to signal user is authenticated
    VALID_AUTH_SESSION = "k_pywce_auth_session"
    DYNAMIC_CURRENT_TEMPLATE_BODY = "k_pywce_current_template_body"
    DYNAMIC_NEXT_TEMPLATE_BODY = "k_pywce_next_template_body"

    # used to check against wa_id on authentication hook
    VALID_AUTH_MSISDN = "k_pywce_auth_msisdn"
    LAST_ACTIVITY = "k_pywce_last_activity"
    CURRENT_MSG_ID = "k_pywce_current_msg_id"
    CURRENT_DEBOUNCE = "k_pywce_current_debounce"

    # if set & exception is encountered / a go back logic is present & user sends a retry message
    # engine will render the latest checkpoint set
    LATEST_CHECKPOINT = "k_pywce_latest_checkpoint"

    # if its an error message with retry btn, set this & clear it after processing
    DYNAMIC_RETRY = "k_pywce_dynamic_retry"
    MESSAGE_HISTORY = "k_pywce_message_history"
