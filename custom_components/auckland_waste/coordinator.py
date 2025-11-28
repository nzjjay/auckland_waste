"""Data update coordinator for Auckland Waste Collection."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    CONF_AREA_NUMBER,
    DOMAIN,
    HEADERS,
    UPDATE_INTERVAL_HOURS,
    WASTE_TYPE_FOOD_WASTE,
    WASTE_TYPE_RECYCLE,
    WASTE_TYPE_RUBBISH,
)

_LOGGER = logging.getLogger(__name__)


class Collection:
    """Represents a waste collection."""

    def __init__(self, date: datetime, waste_type: str) -> None:
        """Initialize a collection."""
        self.date = date
        self.waste_type = waste_type


def parse_date(date_str: str) -> datetime | None:
    """Parse a date string like 'Wednesday, 8 October' to a datetime object."""
    try:
        # Remove the day name if present
        if "," in date_str:
            date_str = date_str.split(",", 1)[1].strip()

        # Try to parse with current year first
        current_year = datetime.now().year

        # Parse "8 October" format
        parsed = datetime.strptime(f"{date_str} {current_year}", "%d %B %Y")

        # If the date is in the past by more than a week, assume it's next year
        if parsed < datetime.now() - timedelta(days=7):
            parsed = datetime.strptime(f"{date_str} {current_year + 1}", "%d %B %Y")

        return parsed
    except ValueError as e:
        _LOGGER.error("Error parsing date '%s': %s", date_str, e)
        return None


class AucklandWasteCoordinator(DataUpdateCoordinator):
    """Coordinator for Auckland Waste Collection data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.area_number = entry.data[CONF_AREA_NUMBER]
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Collection | None]:
        """Fetch data from Auckland Council."""
        try:
            return await self._fetch_collections()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def _fetch_collections(self) -> dict[str, Collection | None]:
        """Fetch collection data from Auckland Council website."""
        url = API_URL.format(area_number=self.area_number)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    raise UpdateFailed(
                        f"Error fetching data: HTTP {response.status}"
                    )
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        collections: dict[str, Collection | None] = {
            WASTE_TYPE_RUBBISH: None,
            WASTE_TYPE_RECYCLE: None,
            WASTE_TYPE_FOOD_WASTE: None,
        }

        # Each collection line looks like:
        # <p class="mb-0 lead"><span ...><i class="acpl-icon rubbish"></i>...<b>Wednesday, 8 October</b></span></p>
        for p in soup.find_all("p", class_="mb-0 lead"):
            icon = p.find("i", class_=lambda x: x and "acpl-icon" in x if x else False)
            date_tag = p.find("b")

            if not icon or not date_tag:
                continue

            # Extract type (e.g. "rubbish", "recycle", "food-waste")
            classes = icon.get("class", [])
            waste_type = None
            for c in classes:
                if c != "acpl-icon":
                    waste_type = c
                    break

            # Extract date
            date_str = date_tag.text.strip()
            if not waste_type or not date_str:
                continue

            collection_date = parse_date(date_str)
            if collection_date is None:
                continue

            # Store the collection if it's a known type
            if waste_type in collections:
                # Only update if this is the next upcoming collection
                existing = collections[waste_type]
                if existing is None or collection_date < existing.date:
                    collections[waste_type] = Collection(collection_date, waste_type)

        _LOGGER.debug("Fetched collections: %s", collections)
        return collections
