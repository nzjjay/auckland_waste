"""Regression tests for the council's browser-compatible HTTP transport."""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from custom_components.auckland_waste.client import fetch_collection_page
from custom_components.auckland_waste.config_flow import validate_area_number
from custom_components.auckland_waste.const import API_URL


class CollectionClientTests(IsolatedAsyncioTestCase):
    """Verify browser impersonation, resource cleanup, and failure handling."""

    async def test_browser_transport_returns_html(self):
        response = Mock(text="<html>collection data</html>")
        with patch(
            "custom_components.auckland_waste.client.AsyncSession"
        ) as factory:
            session = factory.return_value.__aenter__.return_value
            session.get = AsyncMock(return_value=response)

            self.assertEqual(
                await fetch_collection_page("12345"), response.text
            )

            factory.assert_called_once_with(impersonate="chrome", timeout=30)
            session.get.assert_awaited_once_with(
                API_URL.format(area_number="12345")
            )
            response.raise_for_status.assert_called_once_with()
            factory.return_value.__aexit__.assert_awaited_once()

    async def test_http_error_is_not_returned_as_html(self):
        response = Mock(text="<html>406 error</html>")
        response.raise_for_status.side_effect = RuntimeError("HTTP 406")
        with patch(
            "custom_components.auckland_waste.client.AsyncSession"
        ) as factory:
            factory.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=response
            )
            with self.assertRaisesRegex(RuntimeError, "HTTP 406"):
                await fetch_collection_page("12345")
            factory.return_value.__aexit__.assert_awaited_once()

    async def test_timeout_closes_session(self):
        with patch(
            "custom_components.auckland_waste.client.AsyncSession"
        ) as factory:
            factory.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutError
            )
            with self.assertRaises(TimeoutError):
                await fetch_collection_page("12345")
            factory.return_value.__aexit__.assert_awaited_once()

    async def test_setup_uses_shared_client(self):
        with patch(
            "custom_components.auckland_waste.config_flow.fetch_collection_page",
            new_callable=AsyncMock,
        ) as fetch:
            fetch.return_value = '<i class="acpl-icon rubbish"></i>'
            self.assertTrue(await validate_area_number("12345"))
            fetch.assert_awaited_once_with("12345")
            fetch.return_value = "<html>No collection data</html>"
            self.assertFalse(await validate_area_number("12345"))
            fetch.side_effect = TimeoutError
            self.assertFalse(await validate_area_number("12345"))
