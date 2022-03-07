# Chocs-Trace <br> [![PyPI version](https://badge.fury.io/py/chocs-middleware.trace.svg)](https://pypi.org/project/chocs-middleware.trace/) [![CI](https://github.com/kodemore/chocs-trace/actions/workflows/main.yaml/badge.svg)](https://github.com/kodemore/chocs-trace/actions/workflows/main.yaml) [![Release](https://github.com/kodemore/chocs-trace/actions/workflows/release.yml/badge.svg)](https://github.com/kodemore/chocs-trace/actions/workflows/release.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
Http tracing middleware for chocs library. 


# Installation

### Poetry:
```bash
poetry add chocs-middleware.trace
```

### Pip:
```bash
pip install chocs-middleware.trace
```

# Usage

## Support tracing in your responses

```python
from chocs_middleware.trace import TraceMiddleware
from chocs import Application, HttpRequest, HttpResponse

# id_prefix will ensure generated tracing headers to contain your prefix
app = Application(TraceMiddleware(id_prefix="service-name-"))


@app.get("/hello")
def say_hello(req: HttpRequest) -> HttpResponse:
    return HttpResponse("Hello!")  # tracing middleware will automatically attach x-request-id, x-correlation-id, x-causation-id headers to your response

```

## Tracing requests

```python
from chocs_middleware.trace import TraceMiddleware, HttpStrategy
from chocs import Application, HttpRequest, HttpResponse
import requests

# http_strategy will try to detect requests library and use it to add tracing headers in all your requests
# if it fails to detect requests library it will fallback to urllib3
app = Application(TraceMiddleware(http_strategy=HttpStrategy.AUTO))


@app.get("/hello")
def say_hello(req: HttpRequest) -> HttpResponse:
    
    requests.get("http://example.com/test")  # middleware will automatically attach x-correlation-id, x-causation-id and x-request-id headers to your request
    
    return HttpResponse("Hello!")
```

## Using logger

### Formatting message

#### Available properties
