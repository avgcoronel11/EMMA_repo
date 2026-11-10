"""Shared middleware for request tracing."""

import uuid

from backend.apps.compartido.logging_context import reset_request_id, set_request_id


class RequestIdMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or uuid.uuid4().hex
        request.request_id = request_id
        token = set_request_id(request_id)

        try:
            response = self.get_response(request)
            response[self.response_header] = request_id
            return response
        finally:
            reset_request_id(token)
