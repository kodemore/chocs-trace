from unittest.mock import patch

import requests
import urllib3
from chocs import Application, HttpResponse, HttpRequest, HttpMethod
from httmock import urlmatch, HTTMock

from chocs_middleware.trace import TraceMiddleware
from chocs_middleware.trace.middleware import HttpStrategy


def test_can_support_requests_lib() -> None:
    # given
    app = Application(TraceMiddleware())
    request_called = False

    @urlmatch(netloc=r"(.*\.)?test\.com$")
    def requests_support_mock(url, request):
        nonlocal request_called
        request_called = True

        assert "x-correlation-id" in request.headers
        assert "x-causation-id" in request.headers
        assert "x-request-id" in request.headers

        return "ok"

    @app.get("/test")
    def say_hello(req: HttpRequest) -> HttpResponse:
        response = requests.get("http://test.com/")
        assert response.content == b"ok"

        return HttpResponse("OK")

    # when
    with HTTMock(requests_support_mock):
        app(HttpRequest(HttpMethod.GET, "/test"))

    # then
    assert request_called


def urllib_support_mock(*args, **kwargs):

    headers = kwargs["headers"]
    assert "x-correlation-id" in headers
    assert "x-causation-id" in headers
    assert "x-request-id" in headers

    return urllib3.HTTPResponse("ok")


def test_can_support_urllib() -> None:
    # given
    app = Application(TraceMiddleware(http_strategy=HttpStrategy.URLLIB))

    @app.get("/test")
    def say_hello(req: HttpRequest) -> HttpResponse:
        http = urllib3.PoolManager()
        orig_urlopen = http.urlopen
        http.urlopen = urllib_support_mock
        response = http.request("get", "http://test.com/")
        http.urlopen = orig_urlopen
        assert response.data == "ok"

        return HttpResponse("OK")

    # when
    response = app(HttpRequest(HttpMethod.GET, "/test"))

    # then
    assert response.parsed_body == "OK"
    assert "x-request-id" in response.headers


def test_can_use_prefix_for_id() -> None:
    # given
    app = Application(TraceMiddleware(id_prefix="service-name-"))

    @urlmatch(netloc=r"(.*\.)?test\.com$")
    def requests_support_mock(url, request):

        assert "x-correlation-id" in request.headers
        assert "x-causation-id" in request.headers
        assert "x-request-id" in request.headers
        assert request.headers.get("x-correlation-id")[0:13] == "service-name-"
        assert request.headers.get("x-causation-id")[0:13] == "service-name-"
        assert request.headers.get("x-request-id")[0:13] == "service-name-"

        return "ok"

    @app.get("/test")
    def say_hello(req: HttpRequest) -> HttpResponse:
        requests.get("http://test.com/")
        return HttpResponse("OK")

    # when
    with HTTMock(requests_support_mock):
        response = app(HttpRequest(HttpMethod.GET, "/test"))

    # then
    assert response.headers.get("x-request-id")[0:13] == "service-name-"

