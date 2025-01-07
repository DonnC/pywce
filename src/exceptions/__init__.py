"""
@author:    DonnC
@created:   01 2025

Engine custom exceptions
"""


class PywceException(Exception):
    def __init__(self, message, data=None):
        super().__init__(message)
        self.message = message
        self.data = data

    def __str__(self):
        return f"[{self.__class__.__str__}] Message: {self.message} | Data: {self.data}"


class EngineInternalException(PywceException):
    def __init__(self, message, data=None):
        super().__init__(message, data)


class TemplateRenderException(PywceException):
    def __init__(self, message):
        super().__init__(message)


class EngineResponseException(PywceException):
    def __init__(self, message, data=None):
        super().__init__(message, data)


class EngineSessionException(PywceException):
    def __init__(self, message):
        super().__init__(message)


class UserSessionValidationException(EngineSessionException):
    def __init__(self, message):
        super().__init__(message)
