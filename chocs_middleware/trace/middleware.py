from enum import Enum
from typing import Callable

from chocs import HttpRequest, HttpResponse
from gid import Guid
from chocs.middleware import Middleware, MiddlewareHandler
from functools import update_wrapper


IdFactory = Callable[[], str]


def create_guid() -> str:
    return str(Guid())


class HttpStrategy(Enum):
    AUTO = "auto"
    URLLIB = "urllib"
    REQUESTS = "requests"


class TraceMiddleware(Middleware):
    def __init__(self, id_factory: IdFactory = create_guid, http_strategy: HttpStrategy = HttpStrategy.AUTO) -> None:
        self.generate_id = id_factory
        self._http_strategy = http_strategy
        self._use_http = False
        if self._http_strategy != HttpStrategy.AUTO:
            self._use_http = True

        self._use_sentry = False

        self.detect_http_strategy()
        self.detect_sentry()

    def detect_http_strategy(self):
        if self._http_strategy != HttpStrategy.AUTO:
            return

        try:
            import requests

            self._use_http = True
            self._http_strategy = HttpStrategy.REQUESTS
        except ImportError:
            ...  # ignore

        if not self._use_http:
            try:
                import urllib3
                self._use_http = True
                self._http_strategy = HttpStrategy.URLLIB
            except ImportError:
                ...  # ignore

    def detect_sentry(self):
        try:
            import sentry_sdk
            self._use_sentry = True
        except ImportError:
            ...  # ignore

    def handle(self, request: HttpRequest, next: MiddlewareHandler) -> HttpResponse:

        request_id = str(request.headers.get("x-request-id")) or self.generate_id()
        correlation_id = str(request.headers.get("x-correlation-id")) or request_id
        causation_id = str(request.headers.get("x-causation-id")) or request_id

        if "x-request-id" not in request.headers:
            request.headers["x-request-id"] = request_id
        if "x-correlation-id" not in request.headers:
            request.headers["x-correlation-id"] = correlation_id
        if "x-causation-id" not in request.headers:
            request.headers["x-causation-id"] = causation_id

        if self._use_sentry:
            from sentry_sdk import set_tag
            set_tag("http.request_id", request_id)
            set_tag("http.correlation_id", correlation_id)
            set_tag("http.causation_id", causation_id)

        if self._use_http and self._http_strategy == HttpStrategy.REQUESTS:
            from requests import api
            original_request = api.request

            # replace requests.request function to attach extra headers
            def wrapped_request(method, url, **kwargs):
                if "headers" not in kwargs:
                    kwargs["headers"] = {}

                kwargs["headers"]["x-request-id"] = self.generate_id()
                kwargs["headers"]["x-causation-id"] = request_id
                kwargs["headers"]["x-correlation-id"] = correlation_id

                return original_request(method, url, **kwargs)

            api.request = update_wrapper(wrapped_request, original_request)

        if self._use_http and self._http_strategy == HttpStrategy.URLLIB:
            from urllib3.request import RequestMethods
            original_request = RequestMethods.request

            def wrapped_request(self_, method, url, fields=None, headers=None, **urlopen_kw):
                if not headers:
                    headers = {}

                headers["x-request-id"] = self.generate_id()
                headers["x-causation-id"] = request_id
                headers["x-correlation-id"] = correlation_id

                return original_request(self_, method, url, fields, headers, **urlopen_kw)

            RequestMethods.request = update_wrapper(wrapped_request, original_request)

        return next(request)
