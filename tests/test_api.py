import unittest
from unittest.mock import Mock
from unittest.mock import patch

from requests import RequestException

from porkbun_api_cli.api import PorkbunAPI


class TestPorkbunAPI(unittest.TestCase):

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_success_no_datafield(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "SUCCESS"}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint")

        self.assertEqual(result, None)
        self.assertTrue(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_success_with_datafield(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "SUCCESS", "datafield": "value"}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint", datafield="datafield")

        self.assertEqual(result, "value")
        self.assertTrue(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_invalid_datafield(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "SUCCESS"}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint", datafield="datafield")

        self.assertEqual(result, "invalid response from '/test_endpoint': 'datafield' field not found")
        self.assertFalse(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_failed_request(self, mock_post):
        mock_post.side_effect = RequestException("Connection Error")

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint")

        self.assertEqual(result, "request raised an exception: Connection Error")
        self.assertFalse(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_failed_status(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": "FAILURE", "message": "Invalid request"}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint")

        self.assertEqual(result, "request to '/test_endpoint' failed with 400 HTTP status code")
        self.assertFalse(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_invalid_response_empty(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint")

        self.assertEqual(result, "invalid response from '/test_endpoint': status field not found")
        self.assertFalse(success)

    @patch("porkbun_api_cli.api.requests.post")
    def test_query_api_invalid_response_no_message(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "FAILURE"}
        mock_post.return_value = mock_response

        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result, success = api._query_api("/test_endpoint")

        self.assertEqual(result, "invalid response from '/test_endpoint': no error message provided")
        self.assertFalse(success)

    # Mocking _query_api method for success response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_list_dns_records_success(self, mock_query_api):
        mock_query_api.return_value = ({"record1": "value1", "record2": "value2"}, True)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result = api.list_dns_records("porkbun.com/api")
        self.assertEqual(result, {"record1": "value1", "record2": "value2"})

    # Mocking _query_api method for failure response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_list_dns_records_failure(self, mock_query_api):
        mock_query_api.return_value = ("error message", False)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        with self.assertRaises(RuntimeError) as context:
            api.list_dns_records("some.domain")

        self.assertTrue("list_dns_records failed: error message" in str(context.exception))

    # Mocking _query_api method for success response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_create_record_success(self, mock_query_api):
        mock_query_api.return_value = ("record_id", True)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result = api.create_record("some.domain", {"name": "test", "type": "A", "content": "127.0.0.1"})
        self.assertEqual(result, "record_id")

    def test_create_record_invalid_payload(self):
        for name, args in [
            ('invalid domain', (None, {"name": "test", "type": "A", "content": "127.0.0.1"})),
            ('invalid record', ("some.domain", {"name": "test", "type": "A", "magick": "42"})),
            ('empty record', ("some.domain", {})),
        ]:
            with self.subTest(name):
                with self.assertRaises(RuntimeError) as context:
                    print(*args)
                    PorkbunAPI.create_record(None, *args)

                self.assertTrue("create_record failed: invalid input values" in str(context.exception))

    # Mocking _query_api method for failure response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_create_record_failure(self, mock_query_api):
        mock_query_api.return_value = ("error message", False)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        with self.assertRaises(RuntimeError) as context:
            api.create_record("some.domain", {"name": "test", "type": "A", "content": "127.0.0.1"})

        self.assertTrue("create_record failed: error message" in str(context.exception))

    # Mocking _query_api method for success response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_update_record_success(self, mock_query_api):
        mock_query_api.return_value = (None, True)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result = api.update_record("some.domain", "record_id", {"name": "test", "type": "A", "content": "127.0.0.1"})
        self.assertIsNone(result)

    def test_update_record_invalid_payload(self):
        for name, args in [
            ('invalid domain', (None, "1", {"name": "test", "type": "A", "content": "127.0.0.1"})),
            ('invalid id', ("some.domain", None, {"name": "test", "type": "A", "content": "127.0.0.1"})),
            ('invalid record', ("some.domain", "2", {"name": "test", "type": "A", "magick": "42"})),
            ('empty record', ("some.domain", "3", {})),
        ]:
            with self.subTest(name):
                with self.assertRaises(RuntimeError) as context:
                    print(*args)
                    PorkbunAPI.update_record(None, *args)

                self.assertTrue("update_record failed: invalid input values" in str(context.exception))

    # Mocking _query_api method for failure response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_update_record_failure(self, mock_query_api):
        mock_query_api.return_value = ("error message", False)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        with self.assertRaises(RuntimeError) as context:
            api.update_record("some.domain", "", {"name": "test", "type": "A", "content": "127.0.0.1"})

        self.assertTrue("update_record failed: error message" in str(context.exception))

    # Mocking _query_api method for success response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_get_my_ip_success(self, mock_query_api):
        mock_query_api.return_value = ("mock_ip", True)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        result = api.get_my_ip()
        self.assertEqual(result, "mock_ip")

    # Mocking _query_api method for failure response
    @patch("porkbun_api_cli.api.PorkbunAPI._query_api")
    def test_get_my_ip_failure(self, mock_query_api):
        mock_query_api.return_value = ("error message", False)
        api = PorkbunAPI(apikey="apikey", secretapikey="secretapikey", endpoint="http://porkbun.com/api")
        with self.assertRaises(RuntimeError) as context:
            api.get_my_ip()

        self.assertTrue("get_my_ip failed: error message" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
