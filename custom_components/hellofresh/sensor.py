"""Sensor platform for HelloFresh (UK)."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CUSTOMER_UUID, DOMAIN
from .coordinator import HelloFreshCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HelloFresh sensor from a config entry."""
    coordinator: HelloFreshCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HelloFreshCurrentWeekSensor(coordinator, entry)])


class HelloFreshCurrentWeekSensor(
    CoordinatorEntity[HelloFreshCoordinator], SensorEntity
):
    """Sensor showing the number of meals ordered this week."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "meals"
    _attr_translation_key = "current_week_meals"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HelloFreshCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        customer_uuid = entry.data[CONF_CUSTOMER_UUID]
        self._attr_unique_id = f"hellofresh_{customer_uuid}_current_week_meals"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, customer_uuid)},
            name="HelloFresh",
            manufacturer="HelloFresh",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the number of meals for this week."""
        return len(self.coordinator.data.meals)

    @property
    def extra_state_attributes(self) -> dict:
        """Return meal details as attributes."""
        return {
            "week": self.coordinator.data.week,
            "meals": [
                {
                    "name": meal.name,
                    "headline": meal.headline,
                    "image_url": meal.image_url,
                    "website_url": meal.website_url,
                    "pdf_url": meal.pdf_url,
                    "category": meal.category,
                }
                for meal in self.coordinator.data.meals
            ],
        }
