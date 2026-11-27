"""Data update coordinator for Auckland Waste Collection."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
import logging

from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CollectionClient
from .const import (
    CONF_AREA_NUMBER,
    DOMAIN,
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
        nz_tz = ZoneInfo("Pacific/Auckland")
        now = datetime.now(nz_tz)

        # Remove the day name if present
        if "," in date_str:
            date_str = date_str.split(",", 1)[1].strip()

        # Try to parse with current year first
        current_year = now.year

        # Parse "8 October" format
        parsed = datetime.strptime(f"{date_str} {current_year}", "%d %B %Y").replace(tzinfo=nz_tz)

        # If the date is in the past by more than a week, assume it's next year
        if parsed < now - timedelta(days=7):
            parsed = datetime.strptime(f"{date_str} {current_year + 1}", "%d %B %Y").replace(tzinfo=nz_tz)

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
        self.client = CollectionClient()
        self.data_stale = True
        self.last_successful_update: datetime | None = None
        self.last_error: str | None = None
        self._failure_count = 0
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Collection | None]:
        """Fetch data from Auckland Council."""
        try:
            collections = await self._fetch_collections()
        except Exception as err:
            self.data_stale = True
            self.last_error = str(err) or type(err).__name__
            self._failure_count += 1
            minutes = min(15 * 2 ** min(self._failure_count - 1, 5), 360)
            self.update_interval = timedelta(minutes=minutes)
            # Respect Retry-After on rate limits and temporary service outages.
            response = getattr(err, "response", None)
            if response is not None:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        seconds = float(retry_after)
                    except ValueError:
                        try:
                            seconds = (
                                parsedate_to_datetime(retry_after)
                                - datetime.now(ZoneInfo("UTC"))
                            ).total_seconds()
                        except (ValueError, TypeError, OverflowError):
                            seconds = 0
                    if seconds > self.update_interval.total_seconds():
                        self.update_interval = timedelta(seconds=min(seconds, 86400))
            if self.data and any(self.is_upcoming(c) for c in self.data.values()):
                _LOGGER.warning(
                    "Collection refresh failed (%s); using cached dates and retrying in %s",
                    err, self.update_interval,
                )
                return self.data
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if self._failure_count:
            _LOGGER.info("Collection updates recovered using %s", self.client.browser_profile)
        self._failure_count = 0
        self.update_interval = timedelta(hours=UPDATE_INTERVAL_HOURS)
        self.data_stale = False
        self.last_error = None
        self.last_successful_update = datetime.now(ZoneInfo("Pacific/Auckland"))
        try:
            await self._store.async_save({
                "collections": {
                    waste_type: c.date.isoformat() if c is not None else None
                    for waste_type, c in collections.items()
                },
                "last_successful_update": self.last_successful_update.isoformat(),
                "browser_profile": self.client.browser_profile,
            })
        except OSError:
            _LOGGER.warning("Could not save collection cache", exc_info=True)
        return collections

    @staticmethod
    def is_upcoming(collection: Collection | None) -> bool:
        """Never present an expired cached date as an upcoming collection."""
        return collection is not None and collection.date.date() >= datetime.now(
            ZoneInfo("Pacific/Auckland")
        ).date()

    async def async_restore_data(self) -> None:
        """Restore unexpired cached dates before the first network refresh."""
        try:
            saved = await self._store.async_load()
            if not saved:
                return
            self.client = CollectionClient(saved.get("browser_profile", "chrome"))
            restored = {}
            for waste_type in (WASTE_TYPE_RUBBISH, WASTE_TYPE_RECYCLE, WASTE_TYPE_FOOD_WASTE):
                value = saved["collections"].get(waste_type)
                collection = Collection(datetime.fromisoformat(value), waste_type) if value else None
                restored[waste_type] = collection if self.is_upcoming(collection) else None
            last_update = datetime.fromisoformat(saved["last_successful_update"])
            if any(c is not None for c in restored.values()):
                self.data = restored
                self.last_successful_update = last_update
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            _LOGGER.warning("Could not restore collection cache; fetching fresh data", exc_info=True)

    async def _fetch_collections(self) -> dict[str, Collection | None]:
        """Fetch collection data from Auckland Council website."""
        html = await self.client.fetch(self.area_number)

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

        if all(c is None for c in collections.values()):
            raise UpdateFailed("No collection dates found on council page")

        _LOGGER.debug("Fetched collections: %s", collections)
        return collections
