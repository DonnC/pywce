class PywceException(Exception):
    def __init__(self, message, data=None):
        super().__init__(message)
        self.message = message
        self.data = data

    def __str__(self):
        return f"[{self.__class__.__str__}] Message: {self.message} | Data: {self.data}"


class TemplateRenderException(PywceException):
    def __init__(self, message):
        super().__init__(message)
