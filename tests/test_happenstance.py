import os
import unittest
from unittest.mock import Mock, patch

from career_agent import happenstance


class HappenstanceTests(unittest.TestCase):
    def setUp(self):
        self.previous_key = os.environ.get("HAPPENSTANCE_API_KEY")
        os.environ["HAPPENSTANCE_API_KEY"] = "test-key"

    def tearDown(self):
        if self.previous_key is None:
            os.environ.pop("HAPPENSTANCE_API_KEY", None)
        else:
            os.environ["HAPPENSTANCE_API_KEY"] = self.previous_key

    @patch("career_agent.happenstance.requests.request")
    def test_create_search_uses_authorized_api_payload(self, request_mock):
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "id": "search-123",
            "url": "https://happenstance.ai/search/search-123",
        }
        request_mock.return_value = response

        result = happenstance.create_network_search(
            "Python hiring managers in Hyderabad",
            include_my_connections=True,
            include_friends_connections=False,
        )

        self.assertEqual(result["id"], "search-123")
        args, kwargs = request_mock.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "https://api.happenstance.ai/v1/search")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["text"], "Python hiring managers in Hyderabad")
        self.assertTrue(kwargs["json"]["include_my_connections"])

    def test_empty_search_is_rejected_before_api_call(self):
        with self.assertRaises(ValueError):
            happenstance.create_network_search("   ")

    def test_flatten_search_results_maps_mutual_connections(self):
        rows = happenstance.flatten_search_results({
            "mutuals": [{"index": 0, "name": "Shared connection"}],
            "results": [{
                "name": "Alex Example",
                "current_title": "Engineering Manager",
                "current_company": "Example Tech",
                "weighted_traits_score": 4.5,
                "summary": "Leads a backend team",
                "socials": {
                    "linkedin_url": "https://linkedin.com/in/alex-example",
                    "happenstance_url": "https://happenstance.ai/person/alex",
                },
                "mutuals": [{"index": 0}],
            }],
        })
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Example Tech")
        self.assertEqual(rows[0]["mutuals"], "Shared connection")
        self.assertEqual(rows[0]["relevance_score"], 4.5)


if __name__ == "__main__":
    unittest.main()
