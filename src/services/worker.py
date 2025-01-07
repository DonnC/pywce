from datetime import datetime
from time import time
from typing import List

from engine_logger import get_engine_logger
from modules.session import ISessionManager
from modules.whatsapp import MessageTypeEnum
from src.constants.engine import EngineConstants
from src.constants.session import SessionConstants
from src.exceptions import TemplateRenderException
from src.models import WorkerJob
from src.services.message_processor import MessageProcessor


class Worker:
    """
        main engine worker class

        handles processing a single webhook request, process template
        and send request back to WhatsApp
    """

    def __init__(self, job: WorkerJob):
        self.job = job
        self.payload = job.payload
        self.user = job.user
        self.session_id = self.user.wa_id

        self.session: ISessionManager = job.engine_config.session_manager.session(self.session_id)
        self.logger = get_engine_logger(__name__)

    def __get_message_queue__(self) -> List:
        return self.session.get(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY) or []

    def __append_message_to_queue__(self):
        queue = self.__get_message_queue__()
        queue.append(self.user.msg_id)

        if len(queue) > EngineConstants.MESSAGE_QUEUE_COUNT:
            self.logger.warning("Message queue limit reached, applying FIFO...")
            queue = queue[-EngineConstants.MESSAGE_QUEUE_COUNT:]

        self.session.save(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY, data=queue)

    def __exists_in_queue__(self) -> bool:
        queue_history = self.__get_message_queue__()
        return self.user.msg_id in list(set(queue_history))

    def __is_old_webhook__(self) -> bool:
        webhook_time = datetime.fromtimestamp(float(self.user.timestamp))
        current_time = datetime.now()
        time_difference = abs((current_time - webhook_time).total_seconds())
        return time_difference > self.job.engine_config.webhook_timestamp_threshold_s

    def __processor__(self):
        processor = MessageProcessor(data=self.job)
        processor.setup()
        pass

    def work(self):
        """
        Handles every webhook request

        :return: None
        """

        if self.__is_old_webhook__():
            self.logger.info(f"Skipping webhook request. {self.payload.body} Discarding...")
            return

        if self.job.payload.model == MessageTypeEnum.UNKNOWN or self.job.payload.model == MessageTypeEnum.UNSUPPORTED:
            self.logger.warning(f"Received unknown | unsupported message: {self.user.wa_id}")
            return

        if self.job.engine_config.handle_session_queue:
            if self.__exists_in_queue__():
                self.logger.warning(f"Duplicate message found: {self.payload.body}")
                return

        last_debounce_timestamp = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE)
        current_time = int(time() * 1000)

        if last_debounce_timestamp is None or current_time - last_debounce_timestamp >= self.job.engine_config.debounce_timeout_ms:
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE, data=current_time)

        else:
            self.logger.warning("Message ignored due to debounce..")
            return

        if self.job.engine_config.handle_session_queue:
            self.__append_message_to_queue__()

        try:
            self.__processor__()
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_MSG_ID, data=self.user.msg_id)

        except TemplateRenderException as e:
            self.logger.error("Failed to render template: " + e.message)
            # TODO: generate and send a button message
            #       message: Failed to process your message
            #       buttons: [Retry, Report]
            return
