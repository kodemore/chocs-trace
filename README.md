# Chocs-OpenApi <br> [![PyPI version](https://badge.fury.io/py/chocs-middleware.openapi.svg)](https://pypi.org/project/chocs-middleware.openapi/) [![CI](https://github.com/kodemore/chocs-openapi/actions/workflows/main.yaml/badge.svg)](https://github.com/kodemore/chocs-openapi/actions/workflows/main.yaml) [![Release](https://github.com/kodemore/chocs-openapi/actions/workflows/release.yml/badge.svg)](https://github.com/kodemore/chocs-openapi/actions/workflows/release.yml) [![codecov](https://codecov.io/gh/kodemore/chocs-openapi/branch/main/graph/badge.svg?token=GWMTNY5G0N)](https://codecov.io/gh/kodemore/chocs-openapi) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
OpenApi middleware for chocs library.

Newest OpenAPI Specification (v.3.x) can be easily integrated into Chocs through application's middleware. 
Validation is performed via [JsonSchema Draft-7.0 specification](https://json-schema.org) and all commonly 
used features are supported.

## Features

Open api integration can be used to:
- validate request's body
- validate request's path parameters
- validate request's headers
- validate request's query parameters
- validate request's cookies  
- generate dtos from openapi file

## Installation

With pip,
```shell
pip install chocs-middleware.openapi
```
or through poetry
```shell
poetry add chocs-middleware.openapi
```

# Usage

## Using your OpenAPI file

Chocs can read json and yaml files, this example will cover yaml usage although the only difference is the file extension.

```python
import chocs
from chocs_middleware.openapi import OpenApiMiddleware
from os import path

# absolute path to file containing open api documentation; yaml and json files are supported
openapi_filename = path.join(path.dirname(__file__), "/openapi.yml")

# instantiating application and passing open api middleware
app = chocs.Application(OpenApiMiddleware(openapi_filename, validate_body=True, validate_query=True))

# the registered route must correspond to open api route within `path` section.
# if request body is invalid the registered controller will not be invoked
@app.post("/pets")
def create_pet(request: chocs.HttpRequest) -> chocs.HttpResponse:
  ...
  return chocs.HttpResponse(status=200)
```
Complete integration example can be [found here](./examples/input_validation_with_open_api/openapi.yml)

> Keep in mind registered route has to match 1:1 the specified route inside `paths` section inside your OpenApi documentation

## Validating request body

Below is very simple schema to validate request body of a `POST /pet` request. Request body is required, should be valid json request and contain the following properties:
- name (string)
- tags (array of string)
- id (optional string)

`openapi.yml`
```yaml
openapi: "3.0.0"
info:
  version: "1.0.0"
  title: "Pet Store"
paths:
  /pets:
    post:
      description: Creates a new Pet
      requestBody:
        description: Pet
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Pet"
      responses:
        200:
          description: "Success"
components:
  schemas:
    Pet:
      type: object
      required:
        - name
        - tag
      properties:
        id:
          type: integer
        name:
          type: string
        tag:
          type: array
          items:
            type: string
```

`app.py`
```python
import chocs
from chocs_middleware.openapi import OpenApiMiddleware
from os import path

openapi_filename = path.join(path.dirname(__file__), "/openapi.yml")
app = chocs.Application(OpenApiMiddleware(openapi_filename, validate_body=True))

@app.post("/pets")
def create_pet(request: chocs.HttpRequest) -> chocs.HttpResponse:
  pet = request.parsed_body # here we will get valid pet
  return chocs.HttpResponse(status=200)

chocs.serve(app)
```

`create_pet` controller will be only invoked if request contains valid body. Pet's data can be accessed through `request.parsed_body` which is a dict-like object.

## Json schema support

Chocs uses JSON Schema to validate your open api definitions with full draft-7 support and almost complete 2019-09 standard support. 
This means you can use almost every feature described on the [understanding json schema](https://json-schema.org/understanding-json-schema/reference/index.html) webpage. 
The webpage is a great resource full of examples and detailed descriptions around JSON Schema. 


> There are some caveats around `allOf` validator:
> - all object schemas inside `allOf` definition are automatically composed into a single object definition
> - when combining string validators make sure format validator is the last validator in the pipeline otherwise validation might fail due to string casting

