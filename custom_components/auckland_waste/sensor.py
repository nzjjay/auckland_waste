"""Sensor platform for Auckland Waste Collection."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AREA_NUMBER,
    DOMAIN,
    WASTE_TYPE_FOOD_WASTE,
    WASTE_TYPE_ICONS,
    WASTE_TYPE_NAMES,
    WASTE_TYPE_RECYCLE,
    WASTE_TYPE_RUBBISH,
)
from .coordinator import AucklandWasteCoordinator, Collection


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Auckland Waste Collection sensors."""
    coordinator: AucklandWasteCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        AucklandWasteSensor(coordinator, entry, WASTE_TYPE_RUBBISH),
        AucklandWasteSensor(coordinator, entry, WASTE_TYPE_RECYCLE),
        AucklandWasteSensor(coordinator, entry, WASTE_TYPE_FOOD_WASTE),
    ]

    async_add_entities(sensors)


class AucklandWasteSensor(CoordinatorEntity[AucklandWasteCoordinator], SensorEntity):
    """Sensor for Auckland Waste Collection."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AucklandWasteCoordinator,
        entry: ConfigEntry,
        waste_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._waste_type = waste_type
        self._area_number = entry.data[CONF_AREA_NUMBER]

        self._attr_unique_id = f"{entry.entry_id}_{waste_type}"
        self._attr_name = WASTE_TYPE_NAMES.get(waste_type, waste_type.title())
        self._attr_icon = WASTE_TYPE_ICONS.get(waste_type, "mdi:delete")

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._area_number)},
            "name": f"Auckland Waste ({self._area_number})",
            "manufacturer": "Auckland Council",
            "model": "Waste Collection",
        }

    @property
    def native_value(self) -> str | None:
        """Return the next collection date."""
        collection: Collection | None = self.coordinator.data.get(self._waste_type)
        if collection is None:
            return None
        return collection.date.strftime("%Y-%m-%d")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        collection: Collection | None = self.coordinator.data.get(self._waste_type)
        if collection is None:
            return {}

        now = datetime.now()
        days_until = (collection.date - now).days

        return {
            "date": collection.date.strftime("%Y-%m-%d"),
            "day_of_week": collection.date.strftime("%A"),
            "formatted_date": collection.date.strftime("%A, %d %B"),
            "days_until": days_until,
            "is_today": days_until == 0,
            "is_tomorrow": days_until == 1,
            "waste_type": self._waste_type,
            "area_number": self._area_number,
        }
