"""Regression tests for automatic retries, durable cache, and stale sensors."""
import asyncio
from datetime import datetime, timedelta
from email.utils import format_datetime
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

from curl_cffi.requests.exceptions import HTTPError
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.auckland_waste.const import WASTE_TYPE_RUBBISH
from custom_components.auckland_waste.coordinator import AucklandWasteCoordinator, Collection
from custom_components.auckland_waste.sensor import AucklandWasteSensor


class RecoveryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hass = HomeAssistant("/tmp/aw_test")
        frame.async_setup(self.hass)
        factory = self.enterContext(patch(
            "custom_components.auckland_waste.coordinator.Store"
        ))
        self.store = factory.return_value
        self.store.async_load = AsyncMock(return_value=None)
        self.store.async_save = AsyncMock()
        self.entry = SimpleNamespace(
            entry_id="recovery_test", data={"area_number": "12345"}
        )
        self.coordinator = AucklandWasteCoordinator(self.hass, self.entry)
        self.now = datetime.now(ZoneInfo("Pacific/Auckland"))
        self.future = Collection(self.now + timedelta(days=7), WASTE_TYPE_RUBBISH)
        self.data = {WASTE_TYPE_RUBBISH: self.future}
        self.fetch = self.enterContext(patch.object(
            self.coordinator, "_fetch_collections", new_callable=AsyncMock
        ))

    async def test_backoff_and_cached_dates_then_automatic_recovery(self):
        c = self.coordinator
        c.data = self.data
        c.last_successful_update = self.now
        self.fetch.side_effect = TimeoutError("network timeout")
        for minutes in (15, 30, 60, 120, 240, 360, 360):
            self.assertIs(await c._async_update_data(), self.data)
            self.assertTrue(c.data_stale)
            self.assertEqual(c.last_successful_update, self.now)
            self.assertEqual(c.update_interval, timedelta(minutes=minutes))
        self.store.async_save.assert_not_awaited()
        self.fetch.side_effect = None
        self.fetch.return_value = self.data
        self.assertIs(await c._async_update_data(), self.data)
        self.assertFalse(c.data_stale)
        self.assertIsNone(c.last_error)
        self.assertEqual(c.update_interval, timedelta(hours=12))
        self.store.async_save.assert_awaited_once()

    async def test_failure_without_usable_cache_raises_and_schedules_retry(self):
        for cache in (None, {WASTE_TYPE_RUBBISH: Collection(
            self.now - timedelta(days=1), WASTE_TYPE_RUBBISH
        )}):
            self.coordinator.data = cache
            self.fetch.side_effect = TimeoutError("network timeout")
            with self.assertRaises(UpdateFailed):
                await self.coordinator._async_update_data()
            self.assertTrue(self.coordinator.data_stale)

    async def test_empty_page_is_retried_rather_than_marked_fresh(self):
        self.coordinator.data = self.data
        self.fetch.side_effect = UpdateFailed("No collection dates found")
        self.assertIs(await self.coordinator._async_update_data(), self.data)
        self.assertTrue(self.coordinator.data_stale)
        self.assertEqual(self.coordinator.update_interval, timedelta(minutes=15))

    async def test_retry_after_seconds_and_http_date_are_respected(self):
        c = self.coordinator
        c.data = self.data
        for value in ("7200", format_datetime(self.now + timedelta(hours=3)), "invalid"):
            self.fetch.side_effect = HTTPError("HTTP 429", response=Mock(
                headers={"Retry-After": value}
            ))
            await c._async_update_data()
            if value != "invalid":
                self.assertGreater(c.update_interval, timedelta(minutes=119))

    async def test_restore_cache_excludes_expired_dates(self):
        self.store.async_load.return_value = {
            "collections": {
                "rubbish": self.future.date.isoformat(),
                "recycle": (self.now - timedelta(days=1)).isoformat(),
                "food-waste": None,
            },
            "last_successful_update": self.now.isoformat(),
            "browser_profile": "firefox",
        }
        await self.coordinator.async_restore_data()
        self.assertEqual(self.coordinator.data["rubbish"].date, self.future.date)
        self.assertIsNone(self.coordinator.data["recycle"])
        self.assertTrue(self.coordinator.data_stale)
        self.assertEqual(self.coordinator.last_successful_update, self.now)
        self.assertEqual(self.coordinator.client.browser_profile, "firefox")
        self.fetch.side_effect = TimeoutError()
        self.assertIsNotNone(await self.coordinator._async_update_data())

    async def test_missing_corrupt_or_expired_cache_does_not_break_startup(self):
        for saved in (None, {}, {"collections": "invalid"}, {
            "collections": {"rubbish": (self.now - timedelta(days=2)).isoformat()},
            "last_successful_update": self.now.isoformat(),
        }):
            self.store.async_load.return_value = saved
            await self.coordinator.async_restore_data()
            self.assertIsNone(self.coordinator.data)

    async def test_cache_storage_failure_does_not_discard_live_data(self):
        self.store.async_save.side_effect = OSError("read-only filesystem")
        self.fetch.return_value = self.data
        self.assertIs(await self.coordinator._async_update_data(), self.data)
        self.assertFalse(self.coordinator.data_stale)

    async def test_stale_sensor_retains_date_but_expired_date_is_unavailable(self):
        c = self.coordinator
        c.data = self.data
        c.last_successful_update = self.now
        sensor = AucklandWasteSensor(c, self.entry, WASTE_TYPE_RUBBISH)
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.native_value, self.future.date.strftime("%Y-%m-%d"))
        self.assertTrue(sensor.extra_state_attributes["data_stale"])
        self.assertEqual(sensor.extra_state_attributes[sensor.native_value], "Rubbish")
        c.data = {WASTE_TYPE_RUBBISH: Collection(
            self.now - timedelta(days=1), WASTE_TYPE_RUBBISH
        )}
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)
        self.assertNotIn("date", sensor.extra_state_attributes)

    async def test_cancellation_does_not_change_retry_state(self):
        self.fetch.side_effect = asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):
            await self.coordinator._async_update_data()
        self.assertEqual(self.coordinator.update_interval, timedelta(hours=12))
