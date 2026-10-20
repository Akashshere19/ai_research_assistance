
from unittest.mock import patch
from django.test import SimpleTestCase
from ddgs.exceptions import DDGSException

from services.tools import search_tool


class WebSearchRetryTests(SimpleTestCase):

    @patch("services.tools.search_tool.time.sleep")
    @patch("services.tools.search_tool.DDGS")
    def test_retries_then_succeeds(self, mock_ddgs, mock_sleep):
        mock_ddgs.return_value.text.side_effect = [
            DDGSException("Temporary failure"),
            [{"title": "Example", "href": "https://example.com",
              "body": "Example result"}],
        ]

        result = search_tool.web_search_func("test query")

        self.assertIn("Example", result)
        self.assertEqual(mock_ddgs.return_value.text.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("services.tools.search_tool.time.sleep")
    @patch("services.tools.search_tool.DDGS")
    def test_raises_after_all_attempts_fail(self, mock_ddgs, mock_sleep):
        mock_ddgs.return_value.text.side_effect = DDGSException(
            "Search unavailable"
        )

        with self.assertRaises(DDGSException):
            search_tool.web_search_func("test query")

        self.assertEqual(mock_ddgs.return_value.text.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    
    
    @patch("services.tools.search_tool.time.sleep")
    @patch("services.tools.search_tool.DDGS")
    def test_succeeds_without_retry(self, mock_ddgs, mock_sleep):
        mock_ddgs.return_value.text.return_value = [
            {
                "title": "Example",
                "href": "https://example.com",
                "body": "Example result",
            }
        ]

        result = search_tool.web_search_func("test query")

        self.assertIn("Example", result)
        self.assertEqual(mock_ddgs.return_value.text.call_count, 1)
        mock_sleep.assert_not_called()
    
