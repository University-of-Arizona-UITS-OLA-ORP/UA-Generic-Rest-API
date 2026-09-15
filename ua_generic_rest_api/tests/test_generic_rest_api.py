import unittest

import requests
import responses

from ua_generic_rest_api import ua_generic_rest_api


class TestRestApi(ua_generic_rest_api.GenericRestApi):
    """Concrete GenericRestApi implementation used for testing."""

    def __init__(self, host="https://api.example.com/"):
        super().__init__(
            host,
            {"Content-Type": "application/json"},
            "page",
        )


class TestGenericRestApi(unittest.TestCase):
    """Core unit tests for GenericRestApi."""

    def setUp(self):
        """Create a fresh API client before each test."""
        self.api = TestRestApi()

    def test_get_no_urls(self):
        """GET should return an empty list when no endpoints are provided."""
        self.assertEqual(self.api.get([]), [])

    @responses.activate
    def test_get_string_endpoint(self):
        """GET should support a single relative endpoint."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities",
            json={"result": "success"},
            status=200,
        )

        result = self.api.get("cities")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status_code, 200)
        self.assertEqual(
            result[0].json(),
            {"result": "success"},
        )

    @responses.activate
    def test_get_multiple_queries(self):
        """GET should append multiple query parameters."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities?limit=1&page=2",
            json={"results": []},
            status=200,
        )

        result = self.api.get(
            "cities",
            {
                "limit": "1",
                "page": "2",
            },
        )

        self.assertEqual(result[0].status_code, 200)

        request_url = responses.calls[0].request.url

        self.assertIn("limit=1", request_url)
        self.assertIn("page=2", request_url)

    @responses.activate
    def test_get_multiple_queries_with_multiple_values(self):
        """GET should support multiple values for one query parameter."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities",
            json={"results": []},
            status=200,
            match_querystring=False,
        )

        self.api.get(
            "cities",
            {
                "country": ["BR", "CA"],
                "limit": "100",
            },
        )

        request_url = responses.calls[0].request.url

        self.assertIn("country=BR", request_url)
        self.assertIn("country=CA", request_url)
        self.assertIn("limit=100", request_url)

    @responses.activate
    def test_batch_get_multiple_endpoints(self):
        """GET should retrieve multiple endpoints."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities",
            json={"name": "cities"},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.example.com/countries",
            json={"name": "countries"},
            status=200,
        )

        result = self.api.get(
            [
                "cities",
                "countries",
            ]
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_multithread_all_pages_with_parameters(self):
        """GET should preserve parameters while adding page numbers."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities?limit=50&page=1",
            json={"page": 1},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.example.com/cities?limit=50&page=2",
            json={"page": 2},
            status=200,
        )

        result = self.api.get(
            "cities",
            parameters={"limit": 50},
            total_pages=2,
        )

        self.assertEqual(len(result), 2)

        requested_urls = {
            call.request.url
            for call in responses.calls
        }

        self.assertIn(
            "https://api.example.com/cities?limit=50&page=1",
            requested_urls,
        )

        self.assertIn(
            "https://api.example.com/cities?limit=50&page=2",
            requested_urls,
        )

    @responses.activate
    def test_get_does_not_mutate_parameters(self):
        """Pagination should not modify the caller's parameters."""
        responses.add(
            responses.GET,
            "https://api.example.com/cities?limit=50&page=1",
            json={},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.example.com/cities?limit=50&page=2",
            json={},
            status=200,
        )

        parameters = {
            "limit": 50,
        }

        self.api.get(
            "cities",
            parameters=parameters,
            total_pages=2,
        )

        self.assertEqual(
            parameters,
            {
                "limit": 50,
            },
        )

    @responses.activate
    def test_get_fail(self):
        """GET should raise HTTPError for unsuccessful responses."""
        responses.add(
            responses.GET,
            "https://api.example.com/missing",
            status=404,
        )

        with self.assertRaises(
            requests.exceptions.HTTPError
        ):
            self.api.get("missing")

    @responses.activate
    def test_put(self):
        """PUT should send a payload to the correct endpoint."""
        responses.add(
            responses.PUT,
            "https://api.example.com/users/1",
            json={"updated": True},
            status=200,
        )

        payload = '{"name": "Tester"}'

        result = self.api.put(
            "users/1",
            payload,
        )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.body,
            payload,
        )

    @responses.activate
    def test_post(self):
        """POST should send a payload to the correct endpoint."""
        responses.add(
            responses.POST,
            "https://api.example.com/users",
            json={"created": True},
            status=201,
        )

        payload = '{"name": "Tester"}'

        result = self.api.post(
            "users",
            payload,
        )

        self.assertEqual(result.status_code, 201)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.body,
            payload,
        )

    @responses.activate
    def test_delete(self):
        """DELETE should send a request to the correct endpoint."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/users/1",
            status=204,
        )

        result = self.api.delete("users/1")

        self.assertEqual(result.status_code, 204)
        self.assertEqual(len(responses.calls), 1)

    def test_query_builder_encodes_special_characters(self):
        """Query builder should properly encode special characters."""
        query = ua_generic_rest_api._query_builder(
            {
                "name": "Smith & Jones",
            }
        )

        self.assertEqual(
            query,
            "?name=Smith+%26+Jones",
        )

    def test_http_414_scrubber_long_url(self):
        """Long URLs should be split into multiple shorter URLs."""
        values = [
            f"value{i}"
            for i in range(1000)
        ]

        query = ua_generic_rest_api._query_builder(
            {
                "country": values,
            }
        )

        endpoint = (
            f"https://api.example.com/cities{query}"
        )

        self.assertGreater(
            len(endpoint),
            2000,
        )

        result = (
            ua_generic_rest_api
            ._http_414_scrubber(
                [endpoint]
            )
        )

        self.assertGreater(
            len(result),
            1,
        )

        for url in result:
            self.assertLessEqual(
                len(url),
                2000,
            )


if __name__ == "__main__":
    unittest.main()