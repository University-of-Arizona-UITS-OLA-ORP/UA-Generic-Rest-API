#!/usr/bin/env python
"""An abstract class that holds get, put, post, delete for any REST api."""
import requests
import concurrent.futures
import asyncio
import abc

from urllib.parse import urlencode
MAX_WORKERS = 10
REQUEST_TIMEOUT = 60

class GenericRestApi(abc.ABC):
    """The object that holds the stache environment variables."""
    @abc.abstractmethod
    def __init__(self, host, header_info, page_query):
        self.host = host
        self.header_info = header_info
        self.page_query = page_query
        self.session = self._setup_session()

    def _setup_session(self):
        """Returns a session set up with class' header_info."""
        session = requests.Session()
        session.verify = True
        # 'header_info' must include auth info and the content type.
        session.headers.update(self.header_info)

        return session

    def get(self, endpoints, parameters=None, total_pages=None):
        """Get the xml(s) of the url_endpoint(s) passed in.

        Arguments:
            endpoints (string or list):
                The ilab REST resource you want to get, with or without the
                core_url.
            parameters (dict):
                A mapping of a query-able name: value. NOTE: queries can only
                be added to a single endpoint.
            total_pages (int):
                If a get is given a total_pages keyword, then get will perform
                a multi-threaded get on all of the pages.

        Returns:
            responses (list):
                A list of all of the requests responses for each endpoint.
        """
        if not endpoints:
            return endpoints
        # If the endpoints is a str of one endpoint, turn it into a list.
        if isinstance(endpoints, str):
            endpoints = [endpoints]

        # Add the base url if it was not included on any requested endpoint.
        for i, endpoint in enumerate(endpoints):
            if self.host not in endpoint:
                endpoints[i] = f"{self.host}{endpoint}"

        # Build endpoint with query if a parameters dict is given.
        if parameters and total_pages is None:
            query = _query_builder(parameters)
            endpoints[0] += query
            endpoints = _http_414_scrubber(endpoints)

        responses = list()

        # Multithread get dissimilar endpoints.
        if len(endpoints) > 1:
            responses = _brute_batch_get(self.session, endpoints)

        # Multithread all pages of resource given the page query and total page
        # number.
        elif total_pages:
            paged_endpoints = list()
            for i in range(1, total_pages + 1):
                if parameters:
                    page_parameters = parameters.copy()
                    page_parameters[self.page_query] = i

                    paged_endpoints.append(
                        endpoints[0] + _query_builder(page_parameters)
                    )
                else:
                    paged_endpoints.append(
                        endpoints[0] + _query_builder({self.page_query: i})
                    )

            responses = _brute_batch_get(
                self.session,
                paged_endpoints
            )

        else:
            response = self.session.get(endpoints[0], timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            responses.append(response)

        return responses

    def put(self, endpoint, payload):
        """Put the payload to the given endpoint, returning the response.

        Arguments:
            url_endpoint (string):
                The ilab REST resource you want to put.
            payload (string):
                The string to put to the specific endpoint.

        Returns:
            response (requests.models.response):
                Holds, among other things, the returned request information.
        """
        if self.host not in endpoint:
            endpoint = self.host + str(endpoint)
        response = self.session.put(endpoint, str(payload), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return response

    def post(self, endpoint, payload):
        """Post the payload to the given endpoint, returning the response.

        Arguments:
            endpoint (string):
                The REST endpoint to which you want to post.
            payload (string):
                The string to post to the specific endpoint.

        Returns:
            response (requests.models.response):
                Holds, among other things, the returned request information.
        """
        if self.host not in endpoint:
            endpoint = self.host + str(endpoint)
        response = self.session.post(endpoint, str(payload), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return response

    def delete(self, endpoint):
        """Delete the given endpoint, returning the response.

        Arguments:
            endpoint (string):
                The REST endpoint which you want deleted.

        Returns:
            response (requests.models.response):
                Holds, among other things, the returned request information."""
        if self.host not in endpoint:
            endpoint = self.host + str(endpoint)
        response = self.session.delete(endpoint)
        response.raise_for_status()

        return response


def _brute_batch_get(session, urls):
    """Returns a list of multithreaded get responses from the given session."""
    return asyncio.run(_get_async(session, urls))


async def _get_async(session, urls):
    """Uses ThreadPoolExecutor to GET the list of uris."""
    def single_get(url):
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    # Set up executor.
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Store futures to gather.
        futures = list()
        for url in urls:
            futures.append(loop.run_in_executor(
                executor,
                single_get,
                url
            ))

        # Return data when completed.
        return await asyncio.gather(*futures)


def _query_builder(parameters):
    """Converts dictionary with queries to an HTTP-compatible query."""
    queries = dict()

    for key in parameters:
        queries.setdefault(key, set())

        if type(parameters[key]) in [list, set]:
            queries[key] = queries[key].union(
                set(parameters[key])
            )
        else:
            queries[key].add(parameters[key])

    query_items = list()

    for key, group in queries.items():
        group = sorted(list(group))

        for value in group:
            query_items.append(
                (key, value)
            )

    return f"?{urlencode(query_items)}"


def _http_414_scrubber(endpoints):
    """Splits long queried urls into many shorter urls."""
    queried_url = endpoints[0]
    base_url = endpoints[0].split('?')[0]
    new_endpoints = list()
    while len(queried_url) > 2000:
        # Find the last '&' before the 2000th character.
        index = queried_url.rfind('&', 0, 2000)
        sub_url = queried_url[0:index]
        new_endpoints.append(sub_url)
        queried_url = f"{base_url}?{queried_url[index + 1:]}"

    if new_endpoints:
        new_endpoints.append(queried_url)
        # Extend with the previous list, so any other urls after the first are
        # still gotten.
        new_endpoints.extend(endpoints[1:])
        # Reset the reference.
        endpoints = new_endpoints

        return new_endpoints

    return endpoints
