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

# Features

- Automatic generation and propagation of tracing headers (x-request-id, x-correlation-id, x-causation-id)
- Sentry integration
- More intuitive log formatting options
- Structured logging

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

```python
from chocs import Application, HttpRequest, HttpResponse
from chocs_middleware.trace import TraceMiddleware, Logger

app = Application(TraceMiddleware())


@app.get("/hello")
def say_hello(req: HttpRequest) -> HttpResponse:
    logger = Logger.get("logger_name")
    logger.info("Hello {name}!", name="Bob")  # will output to log stream Hello Bob!
    return HttpResponse("Hello!")
```

### Formatting message

```python
from chocs import Application, HttpRequest, HttpResponse
from chocs_middleware.trace import TraceMiddleware, Logger

app = Application(TraceMiddleware())


@app.get("/hello")
def say_hello(req: HttpRequest) -> HttpResponse:
    logger = Logger.get("logger_name", message_format="[{level}] {tags.request.x-correlation-id} {msg}")
    logger.info("Hello {name}!", name="Bob")  # will output to log stream Hello Bob!
    return HttpResponse("Hello!")
```

#### Available formatting options

| Name | Example value | Description |
|---|:---:|---|
| `{level}` | DEBUG | Log level name |
| `{msg}` | Example message | Log message after interpolation |
| `{log_message}` | Example {name} | Log message before interpolation |
| `{timestamp}` | 2022-03-07T20:06:23.453866 | Time of the logged message |
| `{filename}` | example.py | Name of the python file where message was log |
| `{funcName}` | example_function | Name of the function where message was log |
| `{module}` | example_module | Name of the module where message was log |
| `{pathname}` | example/path | Path name of the file where message was log |
| `{tags.*}` | some value | Custom tag value set by calling `Logger.set_tag` function |


