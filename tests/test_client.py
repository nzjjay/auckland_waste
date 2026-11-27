"""Regression tests for browser recovery and bounded council requests."""
import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from curl_cffi.requests.exceptions import HTTPError

from custom_components.auckland_waste.client import (
    BROWSER_PROFILES,
    CollectionClient,
    CollectionPageError,
    fetch_collection_page,
)
from custom_components.auckland_waste.config_flow import validate_area_number
from custom_components.auckland_waste.const import API_URL

HTML = '<i class="acpl-icon rubbish"></i>'


def response(status=200, text=HTML):
    """Build an HTTP response with real status exception behavior."""
    result = Mock(status_code=status, text=text)
    if status >= 400:
        result.raise_for_status.side_effect = HTTPError(
            f"HTTP {status}", response=result
        )
    return result


class CollectionClientTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.factory = self.enterContext(patch(
            "custom_components.auckland_waste.client.AsyncSession"
        ))
        self.sleep = self.enterContext(patch(
            "custom_components.auckland_waste.client.asyncio.sleep",
            new_callable=AsyncMock,
        ))

    def sessions(self, *results):
        sessions = []
        for result in results:
            context = MagicMock()
            session = context.__aenter__.return_value
            session.get = AsyncMock(
                side_effect=result if isinstance(result, BaseException) else None,
                return_value=result,
            )
            sessions.append(context)
        self.factory.side_effect = sessions
        return sessions

    async def test_browser_transport_returns_html(self):
        contexts = self.sessions(response())
        self.assertEqual(await fetch_collection_page("12345"), HTML)
        self.factory.assert_called_once_with(impersonate="chrome", timeout=15)
        contexts[0].__aenter__.return_value.get.assert_awaited_once_with(
            API_URL.format(area_number="12345")
        )
        contexts[0].__aexit__.assert_awaited_once()

    async def test_blocked_profile_recovers_and_remembers_working_profile(self):
        contexts = self.sessions(response(406), response(), response())
        client = CollectionClient()
        self.assertEqual(await client.fetch("12345"), HTML)
        self.assertEqual(client.browser_profile, "safari")
        self.assertEqual(await client.fetch("12345"), HTML)
        self.assertEqual(
            [call.kwargs["impersonate"] for call in self.factory.call_args_list],
            ["chrome", "safari", "safari"],
        )
        for context in contexts:
            context.__aexit__.assert_awaited_once()
        self.sleep.assert_awaited_once_with(1)

    async def test_all_profiles_blocked_stops_after_three_attempts(self):
        self.sessions(*(response(403) for _ in BROWSER_PROFILES))
        with self.assertRaises(HTTPError):
            await fetch_collection_page("12345")
        self.assertEqual(self.factory.call_count, 3)
        self.assertEqual(self.sleep.await_count, 2)

    async def test_transient_server_error_recovers(self):
        self.sessions(response(503), response())
        self.assertEqual(await fetch_collection_page("12345"), HTML)
        self.assertEqual(self.factory.call_count, 2)

    async def test_empty_or_challenge_page_tries_another_profile(self):
        self.sessions(response(text="<html>Access denied</html>"), response())
        self.assertEqual(await fetch_collection_page("12345"), HTML)

    async def test_no_collection_page_fails_after_bounded_attempts(self):
        self.sessions(*(response(text="<html>Empty</html>") for _ in BROWSER_PROFILES))
        with self.assertRaises(CollectionPageError):
            await fetch_collection_page("12345")
        self.assertEqual(self.factory.call_count, 3)

    async def test_permanent_error_and_rate_limit_are_not_retried(self):
        for status in (404, 429):
            with self.subTest(status=status):
                self.factory.reset_mock()
                contexts = self.sessions(response(status))
                with self.assertRaises(HTTPError):
                    await fetch_collection_page("12345")
                self.factory.assert_called_once()
                contexts[0].__aexit__.assert_awaited_once()
        self.sleep.assert_not_awaited()

    async def test_timeout_can_recover_and_closes_each_session(self):
        contexts = self.sessions(TimeoutError(), response())
        self.assertEqual(await fetch_collection_page("12345"), HTML)
        for context in contexts:
            context.__aexit__.assert_awaited_once()

    async def test_cancellation_is_not_retried(self):
        contexts = self.sessions(asyncio.CancelledError())
        with self.assertRaises(asyncio.CancelledError):
            await fetch_collection_page("12345")
        self.factory.assert_called_once()
        contexts[0].__aexit__.assert_awaited_once()

    async def test_overall_timeout_bounds_requests(self):
        contexts = self.sessions(response())

        async def wait_forever(*args, **kwargs):
            await asyncio.Event().wait()

        contexts[0].__aenter__.return_value.get.side_effect = wait_forever
        real_timeout = asyncio.timeout
        with patch(
            "custom_components.auckland_waste.client.asyncio.timeout",
            side_effect=lambda _: real_timeout(0.01),
        ):
            with self.assertRaises(TimeoutError):
                await fetch_collection_page("12345")
        self.factory.assert_called_once()
        contexts[0].__aexit__.assert_awaited_once()

    async def test_setup_uses_shared_client(self):
        with patch(
            "custom_components.auckland_waste.config_flow.fetch_collection_page",
            new_callable=AsyncMock,
        ) as fetch:
            fetch.return_value = HTML
            self.assertTrue(await validate_area_number("12345"))
            fetch.assert_awaited_once_with("12345")
            fetch.return_value = "<html>No collection data</html>"
            self.assertFalse(await validate_area_number("12345"))
            fetch.side_effect = TimeoutError
            self.assertFalse(await validate_area_number("12345"))
