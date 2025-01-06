from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConstants:
    MESSAGE_QUEUE_COUNT: int = 10