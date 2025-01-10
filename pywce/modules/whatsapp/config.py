from dataclasses import dataclass


@dataclass
class WhatsAppConfig:
    """
        Store whatsapp configs to use in [WhatsApp] class
    """
    token: str
    phone_number_id: str
    hub_verification_token: str
    version: str = "v21.0"
    flow_version: str = "3"
    flow_action: str = "navigate"

    use_emulator: bool = False
    emulator_url: str = "http://localhost:3000/api/hook-response"
