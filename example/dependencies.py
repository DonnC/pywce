from fastapi import Depends

import pywce


def get_session_manager():
    """
    Get a session manager that can be used to interact with the session.

    You can pass your own ISessionManager implementation here
    :return: ISessionManager implementation
    """
    return pywce.DefaultSessionManager()


def get_whatsapp_instance():
    wa_config = pywce.WhatsAppConfig(
        token="TOKEN",
        phone_number_id="PHONE_NUMBER_ID",
        hub_verification_token="HUB_VERIFICATION_TOKEN",
        use_emulator=True,
    )
    return pywce.WhatsApp(whatsapp_config=wa_config)


def get_engine_instance(
        session_manager: pywce.ISessionManager = Depends(get_session_manager),
        whatsapp: pywce.WhatsApp = Depends(get_whatsapp_instance)
):
    config = pywce.PywceEngineConfig(
        whatsapp=whatsapp,
        templates_dir="templates",
        trigger_dir="triggers",
        start_template_stage="START-MENU",
        session_manager=session_manager
    )
    return pywce.PywceEngine(config=config)
