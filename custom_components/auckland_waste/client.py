"""HTTP client for Auckland Council collection pages."""
from __future__ import annotations

import asyncio
import logging

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException

from .const import API_URL


_LOGGER = logging.getLogger(__name__)
BROWSER_PROFILES = ("chrome", "safari", "firefox")
RETRYABLE_STATUSES = {403, 406, 408, 500, 502, 503, 504}


class CollectionPageError(Exception):
    """The server returned a page without collection information."""


class CollectionClient:
    """Try alternate browser profiles and remember the one that works."""

    def __init__(self, preferred_profile: str = "chrome") -> None:
        self._profile_index = (
            BROWSER_PROFILES.index(preferred_profile)
            if preferred_profile in BROWSER_PROFILES else 0
        )

    @property
    def browser_profile(self) -> str:
        """Return the preferred browser profile."""
        return BROWSER_PROFILES[self._profile_index]

    async def fetch(self, area_number: str) -> str:
        """Make at most three attempts, with a total budget of 50 seconds."""
        async with asyncio.timeout(50):
            for attempt in range(len(BROWSER_PROFILES)):
                index = (self._profile_index + attempt) % len(BROWSER_PROFILES)
                profile = BROWSER_PROFILES[index]
                status = None
                try:
                    # A fresh session also discards any rejected cookies.
                    async with AsyncSession(impersonate=profile, timeout=15) as session:
                        response = await session.get(
                            API_URL.format(area_number=area_number)
                        )
                        status = response.status_code
                        response.raise_for_status()
                        if "acpl-icon" not in response.text:
                            raise CollectionPageError(
                                "No collection information found on council page"
                            )
                        self._profile_index = index
                        return response.text
                except (RequestException, TimeoutError, CollectionPageError) as err:
                    # Do not retry permanent errors or hammer a rate-limited site.
                    if isinstance(err, RequestException) and status is not None:
                        if status not in RETRYABLE_STATUSES:
                            raise
                    if attempt == len(BROWSER_PROFILES) - 1:
                        raise
                    _LOGGER.debug("Request with %s failed; trying another profile", profile)
                    await asyncio.sleep(attempt + 1)
        raise CollectionPageError("Unable to retrieve collection information")


async def fetch_collection_page(area_number: str) -> str:
    """Fetch a collection page with automatic browser recovery during setup."""
    return await CollectionClient().fetch(area_number)
