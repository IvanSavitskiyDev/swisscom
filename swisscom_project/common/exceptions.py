class BaseError(Exception):
    def get_status_code(self) -> int:
        return 400

    def get_message(self) -> str:
        return str(self)


class HostRespondingError(BaseError):
    pass


class RollBackOperationError(BaseError):
    pass
