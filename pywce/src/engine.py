import logging
from datetime import datetime as dtime
from typing import Dict, Any

from pywce.modules import ISessionManager, history
from pywce.src.constants import SessionConstants
from pywce.src.models import EngineConfig, WorkerJob
from pywce.src.services import Worker, HookService

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: EngineConfig):
        self.config: EngineConfig = config
        self.whatsapp = config.whatsapp

        HookService.register_global_hooks(self.config.global_pre_hooks, self.config.global_post_hooks)

    def _user_session(self, session_id) -> ISessionManager:
        return self.config.session_manager.session(session_id=session_id)

    def verify_webhook(self, mode, challenge, token):
        return self.whatsapp.util.webhook_challenge(mode, challenge, token)

    def process_webhook(self, webhook_data: Dict[str, Any]):
        if not self.whatsapp.util.is_valid_webhook_message(webhook_data):
            _msg = webhook_data if self.config.log_invalid_webhooks is True else "skipping.."
            logger.warning("Invalid webhook message: %s", _msg)
            return

        wa_user = self.whatsapp.util.get_wa_user(webhook_data)
        user_session: ISessionManager = self._user_session(wa_user.wa_id)
        response_model = self.whatsapp.util.get_response_structure(webhook_data)

        if self.config.history_manager:
            current_stage = user_session.get(session_id=wa_user.wa_id, key=SessionConstants.CURRENT_STAGE)
            _content, _metadata = self.whatsapp.util.get_user_input(response_model)
            history_entry = history.History(
                role="user",
                message_type=response_model.typ.name.upper(),
                content=_content,
                metadata=_metadata,
                timestamp=dtime.now().isoformat(),
                stage=current_stage or self.config.start_template_stage
            )
            self.config.history_manager.log_message(wa_user.wa_id, history_entry)

        #  ========= put session defaults ============
        if user_session.get(wa_user.wa_id, SessionConstants.DEFAULT_NAME) is None:
            user_session.save(wa_user.wa_id, SessionConstants.DEFAULT_NAME, wa_user.name)

        if user_session.get(wa_user.wa_id, SessionConstants.DEFAULT_MOBILE) is None:
            user_session.save(wa_user.wa_id, SessionConstants.DEFAULT_MOBILE, wa_user.wa_id)
        # ============= end ====================

        worker = Worker(
            WorkerJob(
                engine_config=self.config,
                payload=response_model,
                user=wa_user
            )
        )
        worker.work()
