"""
@author:    DonnC
@created:   01 2025

Engine custom exceptions
"""


class EngineException(Exception):
    def __init__(self, message, data=None):
        super().__init__(message)
        self.message = message
        self.data = data

    def __str__(self):
        return f"[{self.__class__.__str__}] Message: {self.message} | Data: {self.data}"


class AiException(EngineException):
    def __init__(self, message, data=None):
        super().__init__(message, data)

class EngineClientException(EngineException):
    def __init__(self, message, data=None):
        super().__init__(message, data)

class EngineInternalException(EngineException):
    def __init__(self, message, data=None):
        super().__init__(message, data)

class HookError(EngineInternalException):
    def __init__(self, message, data=None):
        super().__init__(message, data)

class ExtHandlerHookError(EngineInternalException):
    def __init__(self, message, data=None):
        super().__init__(message, data)


class TemplateRenderException(EngineException):
    def __init__(self, message):
        super().__init__(message)


class EngineResponseException(EngineException):
    def __init__(self, message, data=None):
        super().__init__(message, data)


class EngineSessionException(EngineException):
    def __init__(self, message):
        super().__init__(message)


class UserSessionValidationException(EngineSessionException):
    def __init__(self, message):
        super().__init__(message)
