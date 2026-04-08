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
        HelloFreshLastDeliverySensor(coordinator, entry),
        HelloFreshNextDeliverySensor(coordinator, entry),
        HelloFreshNextChangeableSensor(coordinator, entry),
    ])


def _device_info(customer_uuid: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, customer_uuid)},
        name="HelloFresh",
        manufacturer="HelloFresh",
        entry_type=DeviceEntryType.SERVICE,
    )


def _meal_attrs(meal) -> dict:
    return {
        "name": meal.name,
        "headline": meal.headline,
        "image_url": meal.image_url,
        "website_url": meal.website_url,
        "pdf_url": meal.pdf_url,
        "category": meal.category,
    }


class HelloFreshLastDeliverySensor(
    CoordinatorEntity[HelloFreshCoordinator], SensorEntity
):
    """Sensor showing meals from the most recently delivered box."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "meals"
    _attr_translation_key = "last_delivery"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HelloFreshCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        customer_uuid = entry.data[CONF_CUSTOMER_UUID]
        self._attr_unique_id = f"hellofresh_{customer_uuid}_last_delivery"
        self._attr_device_info = _device_info(customer_uuid)

    @property
    def native_value(self) -> int | None:
        """Return the number of meals in the last delivery."""
        delivery = self.coordinator.data.last_delivery
        if delivery is None:
            return None
        return len(delivery.meals)

    @property
    def extra_state_attributes(self) -> dict:
        """Return week and meal details."""
        delivery = self.coordinator.data.last_delivery
        if delivery is None:
            return {}
        return {
            "week": delivery.week,
            "meals": [_meal_attrs(m) for m in delivery.meals],
        }


class HelloFreshNextDeliverySensor(
    CoordinatorEntity[HelloFreshCoordinator], SensorEntity
):
    """Sensor showing when the next HelloFresh delivery will arrive."""

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
        """Return the delivery datetime."""
        delivery = self.coordinator.data.next_delivery
        if delivery is None:
            return None
        dt = delivery.delivery_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt

    @property
    def extra_state_attributes(self) -> dict:
        """Return delivery details and selected meals."""
        delivery = self.coordinator.data.next_delivery
        if delivery is None:
            return {}
        return {
            "week": delivery.week,
            "status": delivery.status,
            "cutoff_date": delivery.cutoff_date.isoformat(),
            "delivery_date": delivery.delivery_date.isoformat(),
            "meals": [_meal_attrs(m) for m in delivery.meals],
        }


class HelloFreshNextChangeableSensor(
    CoordinatorEntity[HelloFreshCoordinator], SensorEntity
):
    """Sensor showing the next delivery that can still be changed.

    State is the cutoff datetime — the deadline for making changes.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "next_changeable_delivery"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HelloFreshCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        customer_uuid = entry.data[CONF_CUSTOMER_UUID]
        self._attr_unique_id = f"hellofresh_{customer_uuid}_next_changeable_delivery"
        self._attr_device_info = _device_info(customer_uuid)

    @property
    def native_value(self) -> datetime | None:
        """Return the cutoff datetime (deadline to change the order)."""
        delivery = self.coordinator.data.next_changeable
        if delivery is None:
            return None
        cutoff = delivery.cutoff_date
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        return cutoff

    @property
    def extra_state_attributes(self) -> dict:
        """Return delivery details and currently selected meals."""
        delivery = self.coordinator.data.next_changeable
        if delivery is None:
            return {}
        return {
            "week": delivery.week,
            "cutoff_date": delivery.cutoff_date.isoformat(),
            "delivery_date": delivery.delivery_date.isoformat(),
            "meals": [_meal_attrs(m) for m in delivery.meals],
        }
