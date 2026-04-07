"""Sensor platform for HelloFresh (UK)."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
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
    """Set up HelloFresh sensors from a config entry."""
    coordinator: HelloFreshCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HelloFreshCurrentWeekSensor(coordinator, entry),
        HelloFreshNextDeliverySensor(coordinator, entry),
    ])


def _device_info(customer_uuid: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, customer_uuid)},
        name="HelloFresh",
        manufacturer="HelloFresh",
        entry_type=DeviceEntryType.SERVICE,
    )


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
        self._attr_device_info = _device_info(customer_uuid)

    @property
    def native_value(self) -> int:
        """Return the number of meals for this week."""
        return len(self.coordinator.data.current_week.meals)

    @property
    def extra_state_attributes(self) -> dict:
        """Return meal details as attributes."""
        data = self.coordinator.data.current_week
        return {
            "week": data.week,
            "meals": [
                {
                    "name": meal.name,
                    "headline": meal.headline,
                    "image_url": meal.image_url,
                    "website_url": meal.website_url,
                    "pdf_url": meal.pdf_url,
                    "category": meal.category,
                }
                for meal in data.meals
            ],
        }


class HelloFreshNextDeliverySensor(
    CoordinatorEntity[HelloFreshCoordinator], SensorEntity
):
    """Sensor showing the next HelloFresh delivery.

    State is the cutoff datetime until the cutoff passes, then the delivery datetime.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "next_delivery"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HelloFreshCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        customer_uuid = entry.data[CONF_CUSTOMER_UUID]
        self._attr_unique_id = f"hellofresh_{customer_uuid}_next_delivery"
        self._attr_device_info = _device_info(customer_uuid)

    @property
    def native_value(self) -> datetime | None:
        """Return cutoff datetime before cutoff; delivery datetime after."""
        delivery = self.coordinator.data.next_delivery
        if delivery is None:
            return None
        now = datetime.now(tz=UTC)
        cutoff = delivery.cutoff_date
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        if now < cutoff:
            return cutoff
        delivery_dt = delivery.delivery_date
        if delivery_dt.tzinfo is None:
            delivery_dt = delivery_dt.replace(tzinfo=UTC)
        return delivery_dt

    @property
    def extra_state_attributes(self) -> dict:
        """Return delivery details and selected meals as attributes."""
        delivery = self.coordinator.data.next_delivery
        if delivery is None:
            return {}
        return {
            "week": delivery.week,
            "status": delivery.status,
            "cutoff_date": delivery.cutoff_date.isoformat(),
            "delivery_date": delivery.delivery_date.isoformat(),
            "meals": [
                {
                    "name": meal.name,
                    "headline": meal.headline,
                    "image_url": meal.image_url,
                    "website_url": meal.website_url,
                    "pdf_url": meal.pdf_url,
                    "category": meal.category,
                }
                for meal in delivery.meals
            ],
        }
