# UA-Generic-Rest-Api

Provides basic REST API Implementation for GET, PUT, and POST, and DELETE.

## Motivation

Was designed to remove similarities among REST API implementations by creating a generic REST API that classes can be extended and override for specific needs.

## Features

- GET - Implementation of GET which can single GET, batch GET, single GET with query, and GET every page on a paginated endpoint.
  - Batch gets with queries are unavailable as there is no way to give each get a unique query. Because of this the feature was not included.
- PUT - Basic implementation of PUT which puts the payload to the given endpoint.
- POST - Basic implementation of POST which posts the payload to the given endpoint.
- DELETE - Basic implementation of DELETE which deletes the given endpoint.

## Code Example

```python
from ua_generic_rest_api import GenericRestApi

class SpecificRestApi(GenericRestApi):
    # Replace '...' with any other initialization arguments.
    def __init__(self, ...):
        # host, header_info, page_query, and page_tag are site specific.
        # Set them to your own values.
        super().__init__(host, header_info, page_query, page_tag=page_tag)

    # Can override GET, PUT, POST, or DELETE here.
```

- host - The base url for the endpoint that is to be gotten.
- header_info - Any information to be added to a request header such as Authorization or Content-Type.
  - Should be in the form of a dictionary, such as {"Authorization": None, "Content-Type": "text/xml"}.
- page_query - The tag to use when querying for specific pages.
  - For example, for sites queried with the tag "?page=", page_query should be "page".
- page_tag - The tag name of paginated endpoints to search for when getting data.
  - For sites paginated with the tag "page", page_tag should be "page".

## Installation

```bash
pip install ua-generic-rest-api
pip install -r requirements.txt
```

## Tests

- Tests are only necessary when wanting to make changes to the module.
- Run from root of repo

```bash
python -m unittest ua_generic_rest_api.tests.test_generic_rest_api
```

## Credits

[sterns1](sterns1@github.com)
[EtienneThompson](EtienneThompson@github.com)

## License

MIT
