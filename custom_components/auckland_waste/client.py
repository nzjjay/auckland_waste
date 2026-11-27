"""HTTP client for Auckland Council collection pages."""
from __future__ import annotations

from curl_cffi.requests import AsyncSession

from .const import API_URL


async def fetch_collection_page(area_number: str) -> str:
    """Fetch a collection page using browser-compatible TLS and headers."""
    # A User-Agent alone is insufficient: the council also checks the TLS
    # fingerprint and returns HTTP 406 to ordinary Python HTTP clients.
    async with AsyncSession(impersonate="chrome", timeout=30) as session:
        response = await session.get(API_URL.format(area_number=area_number))
        response.raise_for_status()
        return response.text
