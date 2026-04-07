"""DataUpdateCoordinator for HelloFresh (UK)."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyhellofresh import AuthenticationError, HelloFreshClient, HelloFreshError
from pyhellofresh.models import WeeklyDelivery

from .const import CONF_EMAIL, CONF_FLARESOLVERR_URL, CONF_SUBSCRIPTION_ID, DOMAIN, UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class HelloFreshCoordinator(DataUpdateCoordinator[WeeklyDelivery]):
    """Coordinator that fetches the current week's HelloFresh meals."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        self.config_entry = entry
        self._client = HelloFreshClient(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            flaresolverr_url=entry.data.get(CONF_FLARESOLVERR_URL),
        )
        self._subscription_id: int = entry.data[CONF_SUBSCRIPTION_ID]

    async def async_shutdown(self) -> None:
        """Close the underlying HTTP session."""
        await self._client.close()

    async def _async_update_data(self) -> WeeklyDelivery:
        try:
            return await self._client.get_current_week_meals(self._subscription_id)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                "HelloFresh credentials are no longer valid"
            ) from err
        except HelloFreshError as err:
            raise UpdateFailed(f"HelloFresh API error: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error communicating with HelloFresh: {err}") from err
