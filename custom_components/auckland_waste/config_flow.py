"""Config flow for Auckland Waste Collection integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .client import fetch_collection_page
from .const import CONF_AREA_NUMBER, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AREA_NUMBER): str,
    }
)


async def validate_area_number(area_number: str) -> bool:
    """Validate that the area number is valid by checking the API."""
    try:
        html = await fetch_collection_page(area_number)
        return "acpl-icon" in html
    except Exception:
        return False


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Auckland Waste Collection."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            area_number = user_input[CONF_AREA_NUMBER].strip()

            # Check if already configured
            await self.async_set_unique_id(f"auckland_waste_{area_number}")
            self._abort_if_unique_id_configured()

            # Validate the area number
            if await validate_area_number(area_number):
                return self.async_create_entry(
                    title=f"Auckland Waste ({area_number})",
                    data={CONF_AREA_NUMBER: area_number},
                )
            else:
                errors["base"] = "invalid_area"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "url": "https://www.aucklandcouncil.govt.nz/rubbish-recycling/rubbish-recycling-collection-days/Pages/collection-day-702.aspx"
            },
        )
