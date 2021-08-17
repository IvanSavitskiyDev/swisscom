from enum import Enum


class HttpMethod(Enum):
    POST = "POST"
    DELETE = "DELETE"


class RequestState(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    FAIL = "FAIL"
