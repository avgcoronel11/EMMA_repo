"""Request-scoped logging helpers."""

from contextvars import ContextVar


request_id_context = ContextVar("request_id", default="-")


def get_request_id():
    return request_id_context.get()


def set_request_id(request_id):
    return request_id_context.set(request_id or "-")


def reset_request_id(token):
    request_id_context.reset(token)


class RequestIdFilter:
    def filter(self, record):
        record.request_id = get_request_id()
        return True
