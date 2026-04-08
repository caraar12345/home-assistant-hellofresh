"""DataUpdateCoordinator for HelloFresh (UK)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyhellofresh import AuthenticationError, HelloFreshClient, HelloFreshError
from pyhellofresh.models import UpcomingDelivery, WeeklyDelivery

from .const import (
    CONF_CUSTOMER_PLAN_ID,
    CONF_EMAIL,
    CONF_FLARESOLVERR_URL,
    CONF_SUBSCRIPTION_ID,
    DOMAIN,
    UPDATE_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class HelloFreshData:
    """Combined data fetched from HelloFresh."""

    last_delivery: WeeklyDelivery | None
    next_delivery: UpcomingDelivery | None
    next_changeable: UpcomingDelivery | None


class HelloFreshCoordinator(DataUpdateCoordinator[HelloFreshData]):
    """Coordinator that fetches HelloFresh meal data."""

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
        self._customer_plan_id: str = entry.data.get(CONF_CUSTOMER_PLAN_ID, "")

    async def async_shutdown(self) -> None:
        """Close the underlying HTTP session."""
        await self._client.close()

    async def _async_update_data(self) -> HelloFreshData:
        try:
            last_delivery = await self._client.get_last_delivery(self._subscription_id)
            next_delivery = await self._client.get_upcoming_delivery(
                self._subscription_id, self._customer_plan_id
            )

            # Avoid a duplicate menu fetch: if next_delivery hasn't passed its
            # cutoff yet, it is itself the next changeable delivery.
            if next_delivery is not None:
                cutoff = next_delivery.cutoff_date
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=UTC)
                if datetime.now(tz=UTC) < cutoff:
                    next_changeable = next_delivery
                else:
                    next_changeable = await self._client.get_next_changeable_delivery(
                        self._subscription_id, self._customer_plan_id
                    )
            else:
                next_changeable = None

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                "HelloFresh credentials are no longer valid"
            ) from err
        except HelloFreshError as err:
            raise UpdateFailed(f"HelloFresh API error: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error communicating with HelloFresh: {err}") from err

        return HelloFreshData(
            last_delivery=last_delivery,
            next_delivery=next_delivery,
            next_changeable=next_changeable,
        )
