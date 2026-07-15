import math
import json
import string
import unittest
import requests
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
from ua_generic_rest_api import ua_generic_rest_api

HOST = "https://test-api.example.com/v1/"
class TestRestApi(ua_generic_rest_api.GenericRestApi):
    def __init__(self, host, content_type):
        super().__init__(host, content_type, "page")

def make_response(
    *,
    status_code=200,
    body=None,
    url=HOST,
    content_type="application/json",
):
    """Create a requests.Response suitable for mocked API calls."""
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response.headers["Content-Type"] = content_type

    if isinstance(body, (dict, list)):
        response._content = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        response._content = body.encode("utf-8")
    elif body is None:
        response._content = b""
    else:
        response._content = body

    response.encoding = "utf-8"
    return response


def paginated_get_response(url, *args, **kwargs):
    """Return deterministic paginated JSON based on the requested URL."""
    query = parse_qs(urlparse(url).query)

    page = int(query.get("page", ["1"])[0])
    limit = int(query.get("limit", ["2"])[0])

    found = 6
    first_index = (page - 1) * limit
    last_index = min(first_index + limit, found)

    results = [
        {
            "id": index + 1,
            "code": f"C{index + 1}",
            "country": "BR" if index % 2 == 0 else "CA",
        }
        for index in range(first_index, last_index)
    ]

    return make_response(
        url=url,
        body={
            "meta": {
                "page": page,
                "limit": limit,
                "found": found,
            },
            "results": results,
        },
    )
class TestGenericRestApi(unittest.TestCase):
    def setUp(self):
        self.json_api = TestRestApi(
            HOST,
            {"Content-Type": "application/json"},
        )

    def test_get_no_urls(self):
        assert self.json_api.get([]) == []

    @patch.object(requests.Session, "get")
    def test_get_string_and_list(self, mock_get):
        mock_get.return_value = make_response(
            body={"results": [{"id": 1}]},
            url=f"{HOST}cities",
        )

        string_response = self.json_api.get(f"{HOST}cities")
        list_response = self.json_api.get([f"{HOST}cities"])
        assert string_response[0].text == list_response[0].text

    @patch.object(requests.Session, "get")
    def test_get_endpoint_with_and_without_host(self, mock_get):
        mock_get.return_value = make_response(
            body={"results": [{"code": "US"}]},
            url=f"{HOST}countries",
        )

        with_host = self.json_api.get(f"{HOST}countries")
        without_host = self.json_api.get("countries")
        assert with_host[0].text == without_host[0].text

        requested_urls = [
            call.args[0]
            for call in mock_get.call_args_list
        ]

        self.assertEqual(requested_urls, [f"{HOST}countries", f"{HOST}countries"])

    @patch.object(requests.Session, "get")
    def test_get_multiple_queries(self, mock_get):
        mock_get.side_effect = paginated_get_response

        response = self.json_api.get(
            f"{HOST}cities",
            {
                "limit": "1",
                "page": "2",
            },
        )
        response_json = response[0].json()
        self.assertEqual(response_json["meta"]["page"], 2)
        self.assertEqual(response_json["meta"]["limit"], 1)
        self.assertEqual(len(response_json["results"]), 1)

    @patch.object(requests.Session, "get")
    def test_get_multiple_queries_with_multiple_values(self, mock_get):
        mock_get.side_effect = paginated_get_response

        response = self.json_api.get(
            f"{HOST}cities",
            {
                "country": ["BR", "CA"],
                "limit": "6",
            },
        )

        requested_url = mock_get.call_args.args[0]
        requested_query = parse_qs(urlparse(requested_url).query)

        self.assertEqual(requested_query["country"], ["BR", "CA"])
        self.assertEqual(requested_query["limit"], ["6"])

        response_json = response[0].json()
        for entry in response_json["results"]:
            self.assertIn(entry["country"], ["BR", "CA"])

    @patch.object(requests.Session, "get")
    def test_batch_get_with_multiple_queries(self, mock_get):
        mock_get.side_effect = paginated_get_response

        response = self.json_api.get(
            [f"{HOST}cities"],
            {
                "limit": "1",
                "page": "2",
            },
        )

        response_json = response[0].json()

        self.assertEqual(response_json["meta"]["page"], 2)
        self.assertEqual(len(response_json["results"]), 1)

    @patch.object(requests.Session, "get")
    def test_batch_get_more_than_max_pool_threads(self, mock_get):
        mock_get.side_effect = paginated_get_response

        number_of_urls = 25
        urls = [
            f"{HOST}countries?limit=1&page={page}"
            for page in range(1, number_of_urls + 1)
        ]

        responses = self.json_api.get(urls)

        self.assertEqual(len(responses), number_of_urls)
        self.assertEqual(mock_get.call_count, number_of_urls)

    @patch.object(requests.Session, "get")
    def test_multithread_all_pages_without_existing_parameters(self, mock_get):
        mock_get.side_effect = paginated_get_response

        total_pages = 3

        responses = self.json_api.get(
            f"{HOST}cities",
            total_pages=total_pages,
        )

        self.assertEqual(len(responses), total_pages)

        pages = sorted(
            response.json()["meta"]["page"]
            for response in responses
        )

        self.assertEqual(pages, [1, 2, 3])

        number_of_results = sum(
            len(response.json()["results"])
            for response in responses
        )

        self.assertEqual(number_of_results, 6)

    @patch.object(requests.Session, "get")
    def test_multithread_all_pages_with_existing_parameters(self, mock_get):
        mock_get.side_effect = paginated_get_response

        total_pages = 3
        limit = 2

        responses = self.json_api.get(
            f"{HOST}cities",
            parameters={"limit": limit},
            total_pages=total_pages,
        )

        self.assertEqual(len(responses), total_pages)

        for response in responses:
            self.assertEqual(response.json()["meta"]["limit"], limit)

    @patch.object(requests.Session, "get")
    def test_get_xml_format(self, mock_get):
        xml_body = """<?xml version="1.0" encoding="UTF-8"?>
        <response>
            <result>success</result>
        </response>
        """

        mock_get.return_value = make_response(
            body=xml_body,
            url=f"{HOST}data.xml",
            content_type="application/xml",
        )

        xml_api = TestRestApi(
            HOST,
            {"Content-Type": "application/xml"},
        )

        response = xml_api.get("data.xml")

        self.assertEqual(response[0].status_code, 200)
        self.assertIn("<result>success</result>", response[0].text)

    @patch.object(requests.Session, "get")
    def test_get_fail(self, mock_get):
        mock_get.return_value = make_response(
            status_code=500,
            body={"message": "Server error"},
            url=f"{HOST}failure",
        )

        with self.assertRaises(requests.exceptions.HTTPError):
            self.json_api.get("failure")

    @patch.object(requests.Session, "get")
    def test_get_url_too_long(self, mock_get):
        countries = []
        for letter_one in string.ascii_uppercase:
            for letter_two in string.ascii_uppercase:
                for letter_three in string.ascii_uppercase:
                    countries.append(letter_one + letter_two)
                    countries.append(letter_one + letter_two + letter_three)

        parameters = {"country": countries[:10000]}

        def mock_get_response(url, *args, **kwargs):
            return make_response(
                status_code=200,
                body={"results": []},
                url=url,
            )

        mock_get.side_effect = mock_get_response

        responses = self.json_api.get(
            "cities",
            parameters=parameters,
        )

        self.assertGreater(len(responses), 0)
        self.assertGreater(mock_get.call_count, 1)

        for response in responses:
            self.assertEqual(response.status_code, 200)

    @patch.object(requests.Session, "put")
    def test_put_endpoint_with_and_without_host(self, mock_put):
        mock_put.return_value = make_response(
            body={"updated": True},
            url=f"{HOST}items/1",
        )

        payload = json.dumps({"name": "Updated"})

        with_host = self.json_api.put(
            f"{HOST}items/1",
            payload,
        )
        without_host = self.json_api.put(
            "items/1",
            payload,
        )

        self.assertEqual(with_host.text, without_host.text)

        requested_urls = [
            call.args[0]
            for call in mock_put.call_args_list
        ]

        self.assertEqual(
            requested_urls,
            [
                f"{HOST}items/1",
                f"{HOST}items/1",
            ],
        )

    @patch.object(requests.Session, "post")
    def test_post(self, mock_post):
        mock_post.return_value = make_response(
            status_code=201,
            body={"id": 1},
            url=f"{HOST}items",
        )

        response = self.json_api.post(
            "items",
            json.dumps({"name": "Created"}),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 1)
        mock_post.assert_called_once()

    @patch.object(requests.Session, "delete")
    def test_delete(self, mock_delete):
        mock_delete.return_value = make_response(
            status_code=204,
            url=f"{HOST}items/1",
        )

        response = self.json_api.delete("items/1")

        self.assertEqual(response.status_code, 204)
        mock_delete.assert_called_once_with(f"{HOST}items/1")
