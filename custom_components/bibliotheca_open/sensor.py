"""Sensors for Bibliotheca Open accounts and loans."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from bibliotheca_open_client import Loan
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .coordinator import AccountData, BibliothecaCoordinator
from .entity import BibliothecaEntity


@dataclass(frozen=True)
class CountDescription:
    key: str
    name: str
    value: Callable[[AccountData], int]


COUNTS = (
    CountDescription("loans", "Loans", lambda data: len(data.loans)),
    CountDescription("overdue", "Overdue loans", lambda data: sum(x.overdue for x in data.loans)),
    CountDescription(
        "renewable",
        "Renewable loans",
        lambda data: sum(x.renewal is not None and x.renewal.renewable for x in data.loans),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BibliothecaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up account sensors and dynamically track active loans."""

    coordinator = entry.runtime_data
    async_add_entities(
        [*(CountSensor(coordinator, item) for item in COUNTS), BalanceSensor(coordinator)]
    )
    loan_entities: dict[str, LoanSensor] = {}

    @callback
    def sync_loans() -> None:
        current = {loan.copy_id: loan for loan in coordinator.data.loans}
        removed = set(loan_entities) - set(current)
        for copy_id in removed:
            entity = loan_entities.pop(copy_id)
            hass.async_create_task(entity.async_remove())
        additions = [
            loan_entities.setdefault(copy_id, LoanSensor(coordinator, copy_id))
            for copy_id in current.keys() - loan_entities.keys()
        ]
        if additions:
            async_add_entities(additions)

    sync_loans()
    entry.async_on_unload(coordinator.async_add_listener(sync_loans))


class CountSensor(BibliothecaEntity, SensorEntity):
    """An aggregate account count."""

    _attr_native_unit_of_measurement = "loans"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: BibliothecaCoordinator, description: CountDescription) -> None:
        super().__init__(coordinator)
        self.description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = (
            f"bibliotheca_open_{slugify(coordinator.entry.title)}_{description.key}"
        )
        self._attr_name = description.name

    @property
    def native_value(self) -> int:
        return self.description.value(self.coordinator.data)


class BalanceSensor(BibliothecaEntity, SensorEntity):
    """The complete account balance."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_name = "Balance"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: BibliothecaCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_balance"
        self._attr_suggested_object_id = (
            f"bibliotheca_open_{slugify(coordinator.entry.title)}_balance"
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.balance is not None

    @property
    def native_value(self) -> Decimal | None:
        balance = self.coordinator.data.balance
        return balance.total.amount if balance else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        balance = self.coordinator.data.balance
        return balance.total.currency if balance else None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        balance = self.coordinator.data.balance
        if balance is None:
            return None
        return {
            "open_fees": str(balance.open_fees.amount),
            "deposits": str(balance.deposits.amount),
        }


class LoanSensor(BibliothecaEntity, SensorEntity):
    """The due date and current status of one active loan."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: BibliothecaCoordinator, copy_id: str) -> None:
        super().__init__(coordinator)
        self.copy_id = copy_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_loan_{copy_id}"
        loan = self.loan
        title = slugify(loan.title)[:80].rstrip("_") if loan else "loan"
        self._attr_suggested_object_id = (
            f"bibliotheca_open_{slugify(coordinator.entry.title)}_{title}_{copy_id}"
        )

    @property
    def loan(self) -> Loan | None:
        return next((x for x in self.coordinator.data.loans if x.copy_id == self.copy_id), None)

    @property
    def available(self) -> bool:
        return super().available and self.loan is not None

    @property
    def name(self) -> str | None:
        return self.loan.title if self.loan else None

    @property
    def native_value(self):
        return self.loan.due_date if self.loan else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        loan = self.loan
        if loan is None:
            return {}
        renewal = loan.renewal
        return {
            "copy_id": loan.copy_id,
            "author": loan.author,
            "media_group": loan.media_group,
            "overdue": loan.overdue,
            "renewable": renewal.renewable if renewal else None,
            "renewal_reason": renewal.reason if renewal else None,
            "renewal_delay": renewal.delay_text if renewal else None,
            "renewal_text": renewal.extend_text if renewal else None,
        }
