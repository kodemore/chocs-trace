from enum import Enum
from functools import update_wrapper
from typing import Callable, Dict

from chocs import HttpRequest, HttpResponse
from chocs.middleware import Middleware, MiddlewareHandler
from gid import Guid

from chocs_middleware.trace.logger import Logger

IdFactory = Callable[[], str]


def create_guid() -> str:
    return str(Guid())


class HttpStrategy(Enum):
    AUTO = "auto"
    URLLIB = "urllib"
    REQUESTS = "requests"


_orig_request: Dict[HttpStrategy, Callable] = {}


def _restore_orig_request() -> None:
    if HttpStrategy.URLLIB in _orig_request:
        from urllib3.request import RequestMethods

        RequestMethods.request = _orig_request[HttpStrategy.URLLIB]  # type: ignore

    if HttpStrategy.REQUESTS in _orig_request:
        from requests import api

        api.request = _orig_request[HttpStrategy.REQUESTS]  # type: ignore


class TraceMiddleware(Middleware):
    def __init__(
        self, id_factory: IdFactory = create_guid, id_prefix: str = "", http_strategy: HttpStrategy = HttpStrategy.AUTO
    ) -> None:
        self.generate_id = lambda: id_prefix + id_factory()
        self._http_strategy = http_strategy
        self._use_http = False
        if self._http_strategy != HttpStrategy.AUTO:
            self._use_http = True

        self._use_sentry = False

        self.detect_http_strategy()
        self.detect_sentry()

        # In case middleware is instantiated multiple times we should reset the state
        _restore_orig_request()

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

        # Retrieve values from headers
        request_id = str(self.generate_id())
        correlation_id = str(request.headers.get("x-correlation-id", request_id))
        causation_id = str(request.headers.get("x-causation-id", request_id))

        # Update headers when needed
        request.headers["x-request-id"] = request_id

        if "x-correlation-id" not in request.headers:
            request.headers["x-correlation-id"] = correlation_id
        if "x-causation-id" not in request.headers:
            request.headers["x-causation-id"] = causation_id

        request_tag = {
            "method": str(request.method),
            "path": str(request.path),
            "route": str(request.route.route),
        }

        Logger.set_tag("request", request_tag)
        Logger.set_tag("x-request-id", request_id)
        Logger.set_tag("x-correlation-id", correlation_id)
        Logger.set_tag("x-causation-id", causation_id)

        # Populate sentry tags
        if self._use_sentry:
            from sentry_sdk import set_tag

            set_tag("request", request_tag)
            set_tag("x-request-id", request_id)
            set_tag("x-correlation-id", correlation_id)
            set_tag("x-causation-id", causation_id)

        # Automatically add extra headers to requests library
        if self._use_http and self._http_strategy == HttpStrategy.REQUESTS:
            from requests import api
            from urllib3.request import RequestMethods

            if HttpStrategy.REQUESTS not in _orig_request:
                _orig_request[HttpStrategy.REQUESTS] = api.request
            # We have to store urllib request as it is used by requests
            if HttpStrategy.URLLIB not in _orig_request:
                _orig_request[HttpStrategy.URLLIB] = RequestMethods.request

            # Revert to the original method in case some override
            RequestMethods.request = _orig_request[HttpStrategy.URLLIB]  # type: ignore

            # Replace requests.request function to attach extra headers
            def wrapped_request(method, url, **kwargs):
                if "headers" not in kwargs:
                    kwargs["headers"] = {}

                kwargs["headers"]["x-causation-id"] = request_id
                kwargs["headers"]["x-correlation-id"] = correlation_id

                return _orig_request[HttpStrategy.REQUESTS](method, url, **kwargs)

            # Override the request function only once
            if api.request != wrapped_request:
                api.request = update_wrapper(wrapped_request, _orig_request[HttpStrategy.REQUESTS])  # type: ignore

        # Automatically add extra headers to urllib library
        if self._use_http and self._http_strategy == HttpStrategy.URLLIB:
            from urllib3.request import RequestMethods

            if HttpStrategy.URLLIB not in _orig_request or _orig_request[HttpStrategy.URLLIB] is None:
                _orig_request[HttpStrategy.URLLIB] = RequestMethods.request

            def urllib_wrapped_request(self_, method, url, fields=None, headers=None, **urlopen_kw):
                if not headers:
                    headers = {}

                headers["x-causation-id"] = request_id
                headers["x-correlation-id"] = correlation_id

                return _orig_request[HttpStrategy.URLLIB](self_, method, url, fields, headers, **urlopen_kw)

            # Override the request function only once
            if RequestMethods.request != urllib_wrapped_request:
                RequestMethods.request = update_wrapper(urllib_wrapped_request, _orig_request[HttpStrategy.URLLIB])  # type: ignore

        response = next(request)
        response.headers.set("x-request-id", request_id)

        return response
