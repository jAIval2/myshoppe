class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


def require(condition, code, message, status=409):
    if not condition:
        raise DomainError(code, message, status)
