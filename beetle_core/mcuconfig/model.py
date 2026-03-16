# Copyright © 2018-2026 Johan Cockx, Matic Kukovec & Kristof Mulier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from enum import Enum, auto, global_enum

from .package import PackageType, Package, packages
from . import expression
from .expression import (
    Expression,
    Always,
    Never,
    And,
    Or,
    Equal,
    Literal,
    Not,
    ExpressionError,
    UndefinedNameError,
    Transaction,
    Symbol,
)
from .error import ConfigError, validate_name
from functools import reduce
from itertools import chain

type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None

# Hack
_callback_level = 0


def _in_callback():
    return False


class Series:
    def __init__(
        self,
        name: str,
        description: str,
        address_unit_bits: int = 8,
    ):
        self.name = name
        self.description = description
        self._peripherals = dict()
        self._clocks = dict()
        self._pad_types = dict()
        self._pads = dict()
        self._parts = dict()
        self._registers: dict[str, Register] = dict()
        self._symbols: dict[str, Symbol] = dict()
        self._signals = dict()
        self._frozen = False
        self._tentative_mappings: set[Mapping] = set()
        self._selectors: set[Symbol] = set()
        self._clock_peripheral = None
        self._focus: Part = None
        self._has_unsaved_changes = False
        self._tentative_changes_active = False
        self._saved_symbols: dict[Symbol, Number] = {}

    @property
    def registers(self) -> Iterable[Register]:
        return self._registers.values()

    def register(self, name: str) -> Register | None:
        return self._registers.get(name)

    @property
    def peripherals(self) -> Iterable[Peripheral]:
        return self._peripherals.values()

    def peripheral(self, name: str) -> Peripheral | None:
        return self._peripherals.get(name)

    @property
    def clock_peripheral(self) -> ClockTree:
        return self._clock_peripheral

    def signal(self, name: str) -> Signal | None:
        if "." in name:
            peripheral_name, signal_name = name.split(".", maxsplit=1)
            peripheral = self.peripheral(peripheral_name)
            if peripheral:
                return peripheral.signal(signal_name)
            for peripheral in self.peripherals:
                if name.startswith(peripheral.name + "_"):
                    signal_name = name[len(peripheral.name + 1) :]
                    signal = peripheral.signal(signal_name)
                    if signal:
                        return signal
        else:
            signals = self._signals.get(name)
            if signals is not None and len(signals) == 1:
                return signals[0]

    @property
    def clocks(self) -> Iterable[Clock]:
        return self._clocks.values()

    def clock(self, name: str) -> Clock | None:
        return self._clocks.get(name)

    @property
    def pad_modes(self) -> Iterable[PadMode]:
        return _pad_modes.values()

    def pad_mode(self, name: str) -> PadMode | None:
        return _pad_mode(name)

    @property
    def pad_kinds(self) -> Iterable[PadKind]:
        return _pad_kinds.values()

    def pad_kind(self, name: str) -> PadKind | None:
        return _pad_kind(name)

    @property
    def pad_types(self) -> Iterable[PadType]:
        return self._pad_types.values()

    def pad_type(self, name: str) -> PadType | None:
        return self._pad_types.get(name)

    @property
    def pads(self) -> Iterable[Pad]:
        return self._pads.values()

    def pad(self, name: str) -> Pad | None:
        return self._pads.get(name)

    @property
    def parts(self) -> Iterable[Part]:
        return self._parts.values()

    def part(self, name: str) -> Part | None:
        return self._parts.get(name)

    @property
    def focus(self) -> Part | None:
        return self._focus

    def lookup(self, name: str) -> Expression | None:
        symbol = self._symbols.get(name)
        if not symbol:
            if name in self._symbols:
                raise UndefinedNameError(f"ambiguous name '{name}'")
        return symbol

    def expression(self, text: str) -> Expression:
        return expression.parse(text, self.lookup)

    def scoped_lookup(self, scopes: set[str]):
        def lookup(name: str) -> Expression | None:
            symbols = [
                symbol
                for symbol in (
                    self.lookup(f"{scope}.{name}") for scope in scopes
                )
                if symbol
            ]
            return symbols[0] if len(symbols) == 1 else self.lookup(name)

        return lookup

    def scoped_expression(self, text: str, scopes: set[str]) -> Expression:
        return expression.parse(text, self.scoped_lookup(scopes))

    def _log(self, text: str):
        try:
            print(f"Expression {text}: {self.expression(text).value}")
        except ExpressionError as error:
            print(f"Expression {text}: {error}")

    def reset(self):
        # print("reset [")
        assert self.frozen
        assert not _in_callback()
        with Transaction():
            for register in self.registers:
                register.reset()
        for peripheral in self.peripherals:
            peripheral._fix_settings_after_reset()
        # print("reset ]")

    @property
    def frozen(self):
        return self._frozen

    def freeze(self):
        """Freeze for structural changes.

        When a series is frozen, it is no longer possible to add or remove
        peripherals, signals (except custom signals) or mappings.
        """
        assert not self.frozen
        if not self._clock_peripheral:
            raise ConfigError(f"Missing clock configuration peripheral")
        for clock in self.clocks:
            clock._finalize()
        for peripheral in self.peripherals:
            peripheral._finalize()
        self._frozen = True
        self.reset()
        for clock in self.clocks:
            clock._animate()
        for peripheral in self.peripherals:
            peripheral._animate()
        self._has_unsaved_changes = False

    def save_symbol_value(self, symbol: Symbol):
        if (
            self.tentative_changes_active
            and self.saved_symbol_value(symbol) is None
        ):
            self._saved_symbols[symbol] = symbol.value

    def saved_symbol_value(self, symbol: Symbol) -> Number | None:
        return self._saved_symbols.get(symbol)

    def begin_tentative_changes(self):
        # print("begin [")
        assert not self.tentative_changes_active
        assert not self._saved_symbols
        self._tentative_changes_active = True
        for selector in self._selectors:
            selector.begin_tentative_changes()
        # print("]")

    def commit_tentative_changes(self):
        # print("commit [")
        assert self.tentative_changes_active
        for mapping in self._tentative_mappings:
            if mapping._state == MappingState.TENTATIVELY_ADDED:
                mapping._state = MappingState.NORMAL
            else:
                assert mapping.state == MappingState.TENTATIVELY_REMOVED
                mapping._state = MappingState.NOT_ACTIVE
            if self._focus:
                self._focus._on_mapping_state(mapping)
        self._tentative_mappings.clear()
        for selector in self._selectors:
            selector.commit_tentative_changes()
        self._tentative_changes_active = False
        self._saved_symbols.clear()
        # TODO: call _on_change() only if there were actual changes.
        # Right now, it is also called when committing a null-change.
        self._on_change()
        # print("]")

    def rollback_tentative_changes(self):
        # print("rollback [")
        assert self.tentative_changes_active
        for selector in self._selectors:
            selector.rollback_tentative_changes()
        for symbol, value in self._saved_symbols.items():
            # print(f"rollback {symbol} to {value}")
            symbol.update(value)
        self._tentative_changes_active = False
        self._saved_symbols.clear()
        # print("]")

    @property
    def tentative_changes_active(self) -> bool:
        return self._tentative_changes_active

    @property
    def has_unsaved_changes(self) -> bool:
        """True iff there are unsaved changed.

        Tentative changes do not count.
        """
        return self._has_unsaved_changes

    def reset_unsaved_changes_flag(self):
        if self._has_unsaved_changes:
            self._has_unsaved_changes = False
            self._on_unsaved_changes()

    def get_data(self) -> JSON:
        """Get json-compatible data for current configuration.

        Usable to save current configuration, to enable reloading it later.
        Resets the unsaved-changes flag.
        """

        def pad_name_if_mapped(signal: CustomSignal) -> str | None:
            pad = signal.pad
            if pad:
                return pad.name

        self.reset_unsaved_changes_flag()
        return {
            "register-values": {
                register.full_name: register.value
                for register in self.registers
                if register.value != register.reset_value
            },
            "custom-signals": [
                {
                    "name": signal.name,
                    "description": signal.description,
                    "peripheral": signal.peripheral.name,
                    "pad": pad_name_if_mapped(signal),
                }
                for signal in self._custom_signals
            ],
            "nominal-values": [
                {
                    "peripheral": peripheral.name,
                    "setting": setting.label,
                    "value": setting.nominal_value,
                }
                for peripheral in self.peripherals
                for setting in peripheral.settings
                if setting.nominal_value != setting.effective_value
            ],
        }

    def set_data(self, data: JSON):
        """Set json-compatible data for current configuration.

        Usable to reload saved configuration. Resets the unsaved-changes flag.

        Data must be in the same format as returned by get_data. Otherwise, an
        exception will be raised and the unsaved-changes flag will be set.
        """
        # print(f"series.set_data [")
        assert not _in_callback()
        had_unsaved_changes = self._has_unsaved_changes
        # Set unsaved-changes flag for two reasons:
        # 1. To make sure that changes while setting data are not reported
        # 2. As a default in case an exception occurs
        self._has_unsaved_changes = True

        def set_custom_signal(
            data: JSON,
            peripheral: Peripheral,
        ) -> CustomSignal:
            name = data["name"]
            signal = peripheral.signal(name)
            description = data["description"]
            if signal:
                assert isinstance(signal, CustomSignal)
                signal.description = description
            else:
                signal = peripheral.add_signal(name, description)
                pad_name = data.get("pad")
                if pad_name:
                    pad = self.pad(pad_name)
                    if pad:
                        signal.map_to_pad(pad)
                else:
                    signal.unmap()
            return signal

        try:
            for name, value in data.get("register-values").items():
                register = self.register(name)
                if register:
                    register.assign(value)

            keep_signals: set[CustomSignal] = set()
            custom_signals_data = data.get("custom-signals")
            if custom_signals_data:
                for cs_data in custom_signals_data:
                    peripheral = self.peripheral(cs_data["peripheral"])
                    name = cs_data["name"]
                    signal = peripheral.signal(name)
                    description = cs_data["description"]
                    if signal:
                        assert isinstance(signal, CustomSignal)
                        signal.description = description
                    else:
                        signal = peripheral.add_signal(name, description)
                        pad_name = cs_data.get("pad")
                        if pad_name:
                            pad = self.pad(pad_name)
                            signal.map_to_pad(pad)
                        else:
                            signal.unmap()
                    keep_signals.add(signal)
            for signal in list(self._custom_signals):
                if signal not in keep_signals:
                    signal.peripheral.remove_signal(signal)

            nominal_values_data = data.get("nominal-values")
            if nominal_values_data:
                for nv_data in nominal_values_data:
                    peripheral = self.peripheral(nv_data["peripheral"])
                    setting = peripheral.setting(nv_data["setting"])
                    value = int(nv_data["value"])
                    setting.select(value)

            self._has_unsaved_changes = False
        except Exception as error:
            raise ConfigError(f"Cannot restore config data: {error}") from error
        finally:
            if self._has_unsaved_changes != had_unsaved_changes:
                self._on_unsaved_changes()
            # print("]")

    @property
    def _custom_signals(self) -> Iterable[CustomSignal]:
        return (
            signal
            for peripheral in self.peripherals
            if peripheral.supports_custom_signals
            for signal in peripheral.signals
            if isinstance(signal, CustomSignal)
        )

    def _on_change(self):
        if not self._has_unsaved_changes and not self.tentative_changes_active:
            self._has_unsaved_changes = True
            self._on_unsaved_changes()

    def _map(
        self,
        signal: Signal,
        pad: Pad,
        predicate: Expression = Always,
        is_altfun: bool = False,
    ):
        assert not self.frozen
        assert predicate.width == 1, predicate
        Mapping(signal, pad, predicate, is_altfun)

    def _add_symbol(self, name: str, symbol: Symbol):
        if name in self._symbols:
            # Remove ambiguous names, unless they are aliases. Aliases are
            # distinct symbols that occupy the same location in memory.
            # Motivation to allow aliases are the CH32V003 registers
            # CHCTLR1_Input and CHCTLR1_Output, which both have a field CC1S and
            # CC2S with the same offset and width.  It is not possible to
            # disambiguate them by prefixing them by the register name, because
            # we want to refer to them in a parametrised way, and CC3S and CC4S
            # are in registers CHCTLR2_Input and CHCTLR1_Output.  Keeping alias
            # names allows us to handle this situation elegantly.
            # Field has priority over register with the same name
            # Motivation: CH32V003 AWUWR register and field
            # Note: duplicate field names within a peripheral do occur: for
            # example, CH32V003 GPIOx has BSHR.BR0 and BCR.BR0
            other = self._symbols[name]
            if other is None:
                # This name has previously been marked as ambiguous; keep it
                # like that.
                pass
            elif symbol.is_alias(other):
                # Keep alias. It doesn't really matter which symbol is in the
                # table: they are equivalent.
                pass
            elif (
                isinstance(other, Register)
                and isinstance(symbol, Field)
                and symbol.register is other
            ):
                # Field has priority over register -> replace
                # Note: fields are always added after registers, so no need to
                # handle the opposite case.
                self._symbols[name] = symbol
            else:
                # Mark as ambiguous
                self._symbols[name] = None
        else:
            self._symbols[name] = symbol

    def _add_register(self, register: Register):
        assert not self.frozen
        if register.full_name in self._registers:
            raise ConfigError(f"Duplicate register '{register}'")
        self._registers[register.full_name] = register

    def _add_field(self, field: Field):
        assert not self.frozen
        self._add_symbol(field.name, field)
        self._add_symbol(f"{field.register.name}.{field.name}", field)
        self._add_symbol(f"{field.register.scope}.{field.name}", field)
        self._add_symbol(f"{field.register.full_name}.{field.name}", field)

    def _add_peripheral(self, peripheral: Peripheral):
        if self._peripherals.get(peripheral.name):
            raise ConfigError(f"duplicate peripheral '{peripheral}'")
        self._peripherals[peripheral.name] = peripheral
        if peripheral.kind == PeripheralKind.CLOCK:
            if self._clock_peripheral:
                raise ConfigError(
                    "conflicting clock configuration peripherals "
                    f"'{self._clock_peripheral}' and '{peripheral}'"
                )
            self._clock_peripheral = peripheral

    def _add_clock(self, clock: Clock):
        if self._clocks.get(clock.name):
            raise ConfigError(f"duplicate clock '{clock}'")
        self._clocks[clock.name] = clock

        class ClockSymbol(Symbol):
            def eval(self) -> int:
                return 100000000

            @property
            def name(self):
                return clock.name

            def __repr__(self):
                return self.name

            def is_alias(self, other):
                return False

        self._add_symbol(clock.name, ClockSymbol())

    def _add_signal(self, signal: Signal):
        signals = self._signals.get(signal.name)
        if signals is None:
            signals = []
            self._signals[signal.name] = signals
        signals.append(signal)

    def _add_pad_type(self, pad_type: PadType):
        assert not self.frozen
        if self._pad_types.get(pad_type.name):
            raise ConfigError(f"duplicate pad type '{pad_type.name}'")
        self._pad_types[pad_type.name] = pad_type

    def _add_pad(self, pad):
        assert not self.frozen
        if self._pads.get(pad.name):
            raise ConfigError(f"duplicate pad '{pad.name}' (mode {pad.mode})")
        self._pads[pad.name] = pad

    def _add_part(self, part):
        assert not self.frozen
        if self._parts.get(part.name):
            raise ConfigError(f"duplicate part '{part.name}'")
        self._parts[part.name] = part

    def _on_unsaved_changes(self):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_unsaved_changes()
            _callback_level -= 1

    def _on_add_signal(self, signal: Signal):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_add_signal(signal)
            _callback_level -= 1

    def _on_remove_signal(self, signal: Signal):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_remove_signal(signal)
            _callback_level -= 1

    def _on_mapping_state(self, mapping: Mapping):
        if (
            mapping.state == MappingState.TENTATIVELY_ADDED
            or mapping.state == MappingState.TENTATIVELY_REMOVED
        ):
            self._tentative_mappings.add(mapping)
        else:
            self._tentative_mappings.discard(mapping)
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_mapping_state(mapping)
            _callback_level -= 1

    def _on_pad_mode_change(self, pad: Pad):
        # print(f"  Change pad {pad} mode to {pad.mode}")
        # print(f"    Mode predicates:")
        # for mode in pad.possible_modes:
        #    print(f"      {mode} when {pad.mode_predicate(mode)}"
        #          f" = {pad.mode_predicate(mode).value}"
        #    )
        assert pad.mode_predicate(pad.mode).value
        # import traceback
        # traceback.print_stack()
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_pad_mode_change(pad)
            _callback_level -= 1

    def _on_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_peripheral_enabled(peripheral, enabled)
            _callback_level -= 1

    def _on_signal_enabled(self, signal: Signal, enabled: bool):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_signal_enabled(signal, enabled)
            _callback_level -= 1

    def _on_signal_mode_compatible(self, signal: Signal, mode: PadMode):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_signal_mode_compatible(signal, mode)
            _callback_level -= 1

    def _on_setting_enabled(self, setting: Setting):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_setting_enabled(setting)
            _callback_level -= 1

    def _on_setting(self, setting: Setting):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_setting(setting)
            _callback_level -= 1

    def _on_clock_input(self, clock: MuxClock):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_clock_input(clock)
            _callback_level -= 1

    def _on_clock_multiplier(self, clock: MultipliedClock):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_clock_multiplier(clock)
            _callback_level -= 1

    def _on_clock_divider(self, clock: DividedClock):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_clock_divider(clock)
            _callback_level -= 1

    def _on_external_clock_mode_change(self, clock: ExternalClock):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_external_clock_mode_change(clock)
            _callback_level -= 1

    def _add_selector(self, selector):
        self._selectors.add(selector)

    def _remove_selector(self, selector):
        self._selectors.remove(selector)

    def _on_add_unmapped_active_signal(self, signal: Signal):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_add_unmapped_active_signal(signal)
            _callback_level -= 1

    def _on_remove_unmapped_active_signal(self, signal: Signal):
        if self._focus:
            global _callback_level
            _callback_level += 1
            self._focus._on_remove_unmapped_active_signal(signal)
            _callback_level -= 1

    def set_focus(self, part: Part):
        # print(f"set focus {part} [")
        assert not self.frozen
        assert not self._focus or self._focus is part, (
            f"cannot simultanuously focus on parts " f"{self._focus} and {part}"
        )
        self._focus = part
        # print(f"] set focus {part}")

    def __repr__(self):
        return self.name


class Bus:
    def __init__(self, series: Series, name: str, clock: Clock):
        # print(f"Bus {name} clock {clock}")
        self._series = series
        self._name = name
        self._clock = clock
        self._peripherals = set()
        clock._add_bus(self)

    @property
    def name(self) -> str:
        return self._name

    @property
    def clock(self) -> Clock:
        return self._clock

    @property
    def peripherals(self) -> Iterable[Peripheral]:
        return self._peripherals

    def _add_peripheral(self, peripheral: Peripheral):
        self._peripherals.add(peripheral)

    def __repr__(self):
        return self.name


class PeripheralKind(Enum):
    OTHER = auto()
    ADC = auto()
    CAN = auto()
    CLOCK = auto()
    CORE = auto()
    DAC = auto()
    DBG = auto()
    ETHERNET = auto()
    GPIO = auto()
    I2C = auto()
    I2S = auto()
    I3C = auto()
    IRDA = auto()
    LIN = auto()
    MEMORY = auto()
    OPAMP = auto()
    QSPI = auto()
    SERIAL = auto()
    SPI = auto()
    TIMER = auto()
    USB = auto()


class Peripheral:
    def __init__(
        self,
        series: Series,
        name: str,
        description: str,
        clocks: {Clock} = set(),
        bus: Bus | None = None,
        peripheral_enable_predicate: Expression = Always,
        clock_enable_predicate: Expression = Always,
        kind: PeripheralKind | None = None,
        scopes: set[str] = set(),
    ):
        validate_name(name)
        if peripheral_enable_predicate.constant_value == 0:
            raise ConfigError(f"{self} peripheral cannot be enabled")
        if clock_enable_predicate.constant_value == 0:
            raise ConfigError(f"{self} clock cannot be enabled")
        self._series = series
        self._name = name
        self.description = description
        self._scopes = scopes
        self._kind = kind or self._guess_kind()
        self._signals = dict()
        self._settings = []
        self._peripheral_enable_predicate = peripheral_enable_predicate
        self._clock_enable_predicate = clock_enable_predicate
        self._enable_predicate = And(
            clock_enable_predicate, peripheral_enable_predicate
        )
        self._bus = bus
        self._clocks = clocks
        self.series._add_peripheral(self)
        for clock in clocks:
            clock._add_peripheral(self)
        if bus:
            bus._add_peripheral(self)

    supports_custom_signals = False

    @property
    def supports_user_defined_signals(self) -> bool:
        """Backward compatibility - use supports_custom_signals"""
        return self.supports_custom_signals

    @property
    def series(self) -> Series:
        return self._series

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> PeripheralKind:
        return self._kind

    @property
    def enable_predicate(self) -> Expression:
        return self._enable_predicate

    @property
    def is_enabled(self) -> bool:
        return bool(self.enable_predicate.value)

    @property
    def can_be_disabled(self) -> bool:
        return not self.enable_predicate.is_constant

    def set_enabled(self, enabled: bool):
        assert not _in_callback()
        return self.enable_predicate.assign(int(enabled))

    def enable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(1)

    def disable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(0)

    @property
    def peripheral_enable_predicate(self) -> Expression:
        return self._peripheral_enable_predicate

    @property
    def clock_enable_predicate(self) -> Expression:
        return self._clock_enable_predicate

    @property
    def clocks(self) -> {Clock}:
        return self._clocks

    @property
    def bus(self) -> Bus | None:
        return self._bus

    def signal(self, name) -> Signal | None:
        return self._signals.get(name)

    @property
    def signals(self) -> Iterable[Signal]:
        return self._signals.values()

    @property
    def has_signals(self) -> bool:
        return bool(self._signals)

    @property
    def enabled_signals(self) -> Iterable[Signal]:
        return (signal for signal in self.signals if signal.is_enabled)

    @property
    def has_enabled_signals(self) -> bool:
        for signal in self.enabled_signals:
            return True
        return False

    @property
    def settings(self) -> Iterable[Setting]:
        return self._settings

    def setting(self, label: str) -> Setting | None:
        for setting in self.settings:
            if setting.label == label:
                return setting

    @property
    def is_configurable(self) -> bool:
        return bool(self._settings) or bool(self._signals)

    def is_usable_for_part(self, part):
        for signal in self.signals:
            if not signal.can_be_disabled and not signal.is_available_for_part(
                part
            ):
                return False
        return True

    def auto_map_enabled_signals(self):
        assert not _in_callback()
        for signal in self.signals:
            if signal.is_enabled:
                signal.auto_map()

    def expression(self, text: str) -> Expression:
        return self.series.scoped_expression(text, self._scopes)

    def _guess_kind(self):
        heuristics = {
            "GPIO": PeripheralKind.GPIO,
            "TIM": PeripheralKind.TIMER,
            "TMR": PeripheralKind.TIMER,
            "ADC": PeripheralKind.ADC,
            "SPI": PeripheralKind.SPI,
            "I2C": PeripheralKind.I2C,
            "CAN": PeripheralKind.CAN,
            "USART": PeripheralKind.SERIAL,
            "UART": PeripheralKind.SERIAL,
            "SYS": PeripheralKind.CORE,
            "PWR": PeripheralKind.CORE,
            "RCC": PeripheralKind.CLOCK,
            "RCM": PeripheralKind.CLOCK,
            "RTC": PeripheralKind.CORE,
            "DBG": PeripheralKind.DBG,
            "USB": PeripheralKind.USB,
            "OTG": PeripheralKind.USB,
            "ETH": PeripheralKind.ETHERNET,
            "LIN": PeripheralKind.LIN,
            "IRDA": PeripheralKind.IRDA,
            "DAC": PeripheralKind.DAC,
            "I3C": PeripheralKind.I3C,
            "I2S": PeripheralKind.I2S,
            "QSPI": PeripheralKind.QSPI,
            "MMC": PeripheralKind.MEMORY,
            "SMC": PeripheralKind.MEMORY,
            "SDIO": PeripheralKind.MEMORY,
            "OPA": PeripheralKind.OPAMP,
        }
        for key, value in heuristics.items():
            if self.name.startswith(key):
                return value
        return PeripheralKind.OTHER

    def _finalize(self):
        self._remove_signals_without_pads()
        for signal in self.signals:
            signal._finalize()

    def _animate(self):
        self.enable_predicate.watch(
            lambda value: self.series._on_peripheral_enabled(self, bool(value))
        )
        for signal in self.signals:
            signal._animate()

    def _remove_signals_without_pads(self):
        self._signals = {
            name: signal
            for name, signal in self._signals.items()
            if signal.has_possible_pads
        }

    def _add_signal(self, signal):
        if signal.name in self._signals:
            raise ConfigError(f"duplicate signal '{signal}'")
        self._signals[signal.name] = signal
        self.series._on_add_signal(signal)

    def _remove_signal(self, signal):
        for mapping in signal.all_mappings:
            if mapping._state != MappingState.NOT_ACTIVE:
                mapping._set_state(MappingState.NOT_ACTIVE)
            mapping._pad._remove_mapping(mapping)
        self.series._on_remove_signal(signal)
        del self._signals[signal.name]

    def _rename_signal(self, signal, name):
        if name != signal._name:
            validate_name(name)
            if name in self._signals:
                raise ConfigError(f"duplicate signal '{name}'")
            del self._signals[signal._name]
            signal._name = name
            self._signals[signal._name] = signal

    def _add_setting(self, setting: Setting):
        self._settings.append(setting)

    def _fix_settings_after_reset(self):
        for setting in self.settings:
            setting._fix_after_reset()

    def __repr__(self):
        return self.name


class SettingKind(Enum):
    LIST = auto()  # List of string values; pull down menu
    FLAG = auto()  # Boolean value, check box
    NUMBER = auto()  # Integer between minimum and maximum


class Setting:
    max_option_length = 30

    def __init__(
        self,
        label: str,
        description: str,
        kind: SettingKind,
        predicate: Expression,
        selector: Expression,
        sel2val: dict[int, int] | None = None,
        options: list[str] | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
    ):
        """Create a setting.

        The value of a setting is always a number.  If the value to be presented
        to the user is a string, then the value is an index into the *options*
        list, which is a list of strings.

        - label is a short (max 50 characters, no line breaks) string intended
                to be used as a label for this setting in a user interface

        - description is a longer string intended as help text or documentation
          for this setting

        - kind is the kind of setting: FLAG, LIST or NUMBER

        - predicate is an expression that is true (1) iff this setting is
                    enabled, given other settings. When this expression is
                    false (0), it can be greyed-out or hidden in the user
                    interface.

        - selector is the expression determining the value selected for this
                  setting.  In some cases, the set of valid values is not
                  contiguous. In such a case, the sel2val dict maps selector
                  values to setting values.

        - sel2val is an optional dict mapping a value of the selector to a value
                  of this setting.
                    - invalid selector values are not present
                    - keys must be valid selector values
                    - values must be a valid index in the list of options
                    - there must be at least one entry for each option
                  The default is a one-to-one mapping: the
                  value of this setting is equal to the selector value.

        - options is a list of short strings, one for each possible value of a
                 LIST setting. It is None for FLAG and NUMBER settings.

        - minimum is the minimum value for a NUMBER setting. It defaults to
                  zero. It is zero for LIST and FLAG settings.

        - maximum is the maximum value for a NUMBER setting. It is equal to the
                  number of values minus one for a LIST or FLAG setting.

        Must be instantiated as a derived class with a self.owner property,
        where self.owner.series is a series.
        """
        assert label, f"No label for {kind} setting: {description}"
        self._label = label
        self.description = description
        self._predicate = predicate
        self._selector = selector
        self._sel2val = sel2val
        self._kind = kind
        if kind == SettingKind.LIST:
            assert minimum is None
            assert maximum is None
            if options:
                for option in options:
                    if len(option) > self.max_option_length:
                        raise ConfigError(
                            f"Option too long (more than "
                            f"{self.max_option_length} characters): '{option}'"
                        )
                    if "\n" in option:
                        raise ConfigError(
                            f"Option cannot contain line breaks: '{option}'"
                        )
            self._options = options
            self._minimum = 0
            self._maximum = len(options) - 1
            if sel2val:
                missing = set(range(len(options))) - set(sel2val.values())
                assert not missing, (
                    f"missing values {missing} for setting {self}"
                    f" options: {options}  sel2val: {sel2val}"
                )
                for key, value in sel2val.items():
                    if value < self.minimum or value > self.maximum:
                        raise ConfigError(
                            f"invalid value {value} for setting '{self}' "
                            f"when {selector} == {key}"
                        )
                    if selector.is_out_of_range(key):
                        raise ConfigError(
                            f"{key} not in range for setting '{self}' "
                            f" selector {selector} "
                            f"with width {selector.width}"
                        )

        elif kind == SettingKind.FLAG:
            assert options is None
            assert sel2val is None
            assert minimum is None
            assert maximum is None
            self._options = None
            self._minimum = 0
            self._maximum = 1
        else:
            assert kind == SettingKind.NUMBER
            assert options is None
            assert sel2val is None
            self._options = None
            assert type(minimum) is int
            assert type(maximum) is int
            assert minimum < maximum
            self._minimum = minimum
            self._maximum = maximum

        self._nominal_value: int = self.effective_value
        self._selector_reset_value = self._selector.value

        def on_enabled(enabled: int):
            # print(f"setting {self} enabled becomes {enabled}")
            self.series._on_setting_enabled(self)

        predicate.watch(on_enabled)

        def on_change(sv: int):
            if self is not Setting._busy:
                self._set_nominal_value(self.effective_value)
            # if self.nominal_value != self.effective_value:
            #    print(f"{self} nominal {self.nominal_value} "
            #          f"effective {self.effective_value}"
            #    )
            if self._nominal_value is not None:
                self.series._on_setting(self)

        selector.watch(on_change)

    @property
    def label(self) -> str:
        return self._label

    @property
    def series(self) -> Series:
        return self.owner.series

    @property
    def kind(self) -> SettingKind:
        return self._kind

    @property
    def options(self) -> list[str]:
        # Dangerous: there can be too many options - to fix
        return (
            self._options
            if self._options
            else [str(i) for i in range(self.minimum, self.maximum + 1)]
        )

    def option(self, option: str) -> int | None:
        if self._options:
            return self._options.index(option)
        try:
            return int(option)
        except:
            return None

    @property
    def current(self) -> str:
        return self._options[self.value] if self._options else str(self.value)

    @property
    def minimum(self) -> int:
        return self._minimum

    @property
    def maximum(self) -> int:
        return self._maximum

    @property
    def is_enabled(self) -> bool:
        return bool(self._predicate.value)

    @property
    def enable_predicate(self) -> Expression:
        return self._predicate

    @property
    def selector(self) -> Expression:
        return self._selector

    @property
    def effective_value(self) -> int | None:
        """Current value of this setting based on selector values.

           - for a LIST, an index into the list of options

           - for a FLAG, 0 for false and 1 for true

           - for a NUMBER, the value of the number

        If this setting is currently not in a valid state, return None.
        """
        value = self._selector.value
        if self._sel2val:
            option = self._sel2val.get(value)
        elif value < self.minimum:
            option = None
        elif value > self.maximum:
            option = None
        else:
            option = round(value)
        return option

    @property
    def value(self) -> int | None:
        return self.nominal_value

    @property
    def nominal_value(self) -> int | None:
        """Nominal value of this setting.

        Usually, the is the same as the effective value. However, when a value
        is set using the select(value) method and the requested value is not
        feasible, the nominal value is equal to the requested value, not the
        effective value. Also, when the effective value becomes invalid, the
        nominal value does not change.
        """
        return self._nominal_value

    def select(self, value: int):
        """Set the nominal value, and effective value if possible."""
        # print(f"select {self} = {value} busy={Setting._busy} [")
        assert not _in_callback()
        assert value >= self.minimum
        assert value <= self.maximum
        busy = Setting._busy
        Setting._busy = self
        self._set_nominal_value(value)
        if self._sel2val:
            # There can be multiple selector values yielding the same option.
            sels = [sel for sel, val in self._sel2val.items() if val == value]
            # Select one arbitrarily
            # We arbitrarily select the smallest selector value.
            sel = min(sels)
            # Mask dontcare bits to avoid unnecessary changes.  If the number of
            # selector values is even, it could be that one or more of its bits
            # are don't care, i.e. do not affect the selected option. We don't
            # want to force the value of a dontcare bit, so create a mask with
            # dontcare bits.
            dontcare = 0
            all = reduce(lambda x, y: x | y, sels, 0)
            bit = 1
            while len(sels) & 1 == 0 and bit <= all:
                if 2 * len({x | bit for x in sels}) == len(sels):
                    dontcare |= bit
                bit <<= 1
            self._selector.assign(sel, ~dontcare)
        else:
            self._selector.assign(value)
        Setting._busy = busy
        # print("]")

    _busy: Setting | None = None

    def _set_nominal_value(self, value):
        if self._nominal_value != value:
            self._nominal_value = value
            self.series._on_change()

    @property
    def is_at_reset_value(self) -> bool:
        return self._selector.value == self._selector_reset_value

    @property
    def has_reserved_values(self):
        """True iff not all selector values are allowed for this setting."""
        return self._sel2val and len(self._sel2val) < (
            1 << self._selector.width
        )

    @property
    def reserved_values(self) -> set[int]:
        return (
            set(range(self.selector.width)) - self._sel2val.keys()
            if self._sel2val
            else set()
        )

    def not_reserved_expression(self):
        """An expression that is true when the value of this setting is valid,
        i.e. not reserved."""
        return (
            expression.Or.join(
                [
                    expression.Equal(
                        self._selector,
                        expression.Literal(value, self._selector.width),
                    )
                    for value in self._sel2val
                ]
            )
            if self._sel2val
            else always
        )

    def _fix_after_reset(self):
        # Remember selector's reset value, to helop decide whether to generate
        # code for this setting.
        self._selector_reset_value = self._selector.value
        # Make sure that the selector matches an option
        # of this setting.  Minimize changes.
        if self._sel2val and self._selector.value not in self._sel2val:
            # We arbitrarily choose the smallest valid selector value.
            option = self._sel2val.get(min(self._sel2val.keys()))
            # print(
            #    f"Fix setting {self}: select option {option}"
            #    f" '{self.option(option)}'"
            #    #f" instead of {self._selector}={self._selector.value}"
            # )
            self.select(option)

    def __repr__(self):
        return f"{self.owner}.'{self.label}'"


class PeripheralSetting(Setting):
    """A peripheral setting is a setting that applies to peripheral.

    - peripheral: the peripheral

    - args: positional arguments for base setting

    - kwargs: keyword arguments for base setting
    """

    def __init__(self, peripheral: Peripheral, *args, **kwargs):
        self._peripheral = peripheral
        super().__init__(*args, **kwargs)
        peripheral._add_setting(self)

    @property
    def peripheral(self):
        return self._peripheral

    @property
    def owner(self):
        return self.peripheral

    @property
    def series(self):
        return self.peripheral.series


class ClockSetting(PeripheralSetting):
    """A clock setting is a setting of the clocktree peripheral.

    - args: positional arguments for base setting

    - kwargs: keyword arguments for base setting
    """

    def __init__(self, clock: Clock, *args, **kwargs):
        self._clock = clock
        super().__init__(
            peripheral=clock.series.clock_peripheral, *args, **kwargs
        )
        clock._add_setting(self)

    @property
    def clock(self):
        return self._clock


class PadKind:
    def __init__(
        self,
        name: str,
        desc: str,
    ):
        self.name = name
        self.desc = desc
        _pad_kinds[name] = self

    def __repr__(self):
        return self.name


# The set of possible pad classes is fixed and independent of the series.
_pad_kinds: Dict[str, PadKind] = {}


def _pad_kind(name: str) -> PadKind:
    return _pad_kinds.get(name)


POWER = PadKind("power", desc="Supply voltage or ground pin")
IN = PadKind("in", desc="Signal input only pin")
IO = PadKind("io", desc="Signal input or output pin")


class Direction(Enum):
    IN = auto()
    OUT = auto()


class PadMode:
    def __init__(
        self,
        name: str,
        desc: str,
        direction: Direction,
    ):
        self.name = name
        self.desc = desc
        self.direction = direction
        _pad_modes[name] = self

    def __repr__(self):
        return self.name


# The set of possible pad modes is fixed and independent of the series.
_pad_modes: Dict[str, PadMode] = {}


def _pad_mode(name: str) -> PadMode:
    return _pad_modes.get(name)


def _all_pad_modes() -> Iterable[PadMode]:
    return _pad_modes.values()


AI = PadMode("AI", direction=Direction.IN, desc="analog input")
FI = PadMode("FI", direction=Direction.IN, desc="floating input")
PU = PadMode("PU", direction=Direction.IN, desc="input with pull-up")
PD = PadMode("PD", direction=Direction.IN, desc="input with pull-down")
PP = PadMode("PP", direction=Direction.OUT, desc="push-pull output")
PP_AF = PadMode(
    "PP-AF",
    direction=Direction.OUT,
    desc="push-pull output (alternate function)",
)
OD = PadMode("OD", direction=Direction.OUT, desc="open-drain output")
OD_AF = PadMode(
    "OD-AF",
    direction=Direction.OUT,
    desc="open-drain output (alternate function)",
)
_default_mode = FI


class PadType:
    def __init__(
        self,
        series: Series,
        name: str,
        desc: str,
        kind: PadKind,
        modes: set[PadMode],
    ):
        self.series: Series = series
        self.name: str = name
        self.desc: str = desc
        self._kind = kind
        self._modes: set[PadMode] = modes
        series._add_pad_type(self)

    @property
    def kind(self) -> PadKind:
        return self._kind

    @property
    def modes(self) -> set[PadMode]:
        return self._modes

    def __repr__(self):
        return self.name


class PadSetting(Setting):
    """A pad setting is a setting that applies to a pad iso a peripheral.

    Availablility of a pad setting may depend on the pad's mode.

    - modes: a list of modes in which this setting is available

    - args: positional arguments for base setting

    - kwargs: keyword arguments for base setting
    """

    def __init__(self, pad: Pad, modes: [PadMode], *args, **kwargs):
        self._pad = pad
        super().__init__(*args, **kwargs)
        self.modes = modes

    @property
    def pad(self):
        return self._pad

    @property
    def owner(self):
        return self.pad

    @property
    def series(self):
        return self.pad.series


class Pad:
    def __init__(
        self,
        name: str,
        type: PadType,
    ):
        # Do not validate pad names. Some power pads have names that are not
        # valid identifiers, like 'VREF+'. If we want to use pad names as
        # identifiers in generated code, we will have to replace invalid chars
        # or add validation.
        # validate_name(name)
        self.name = name
        self._type = type
        self._mappings: set[Mapping] = set()
        self._mode = _default_mode
        self._mode_predicates: Dict[Mode, Expression] = {}
        self.series._add_pad(self)
        self._no_altfun_predicate: Expression = Never
        self._enable_predicate = Always

    @property
    def type(self) -> PadType:
        return self._type

    @property
    def series(self):
        return self.type.series

    @property
    def kind(self) -> PadKind:
        return self.type.kind

    @property
    def pin(self) -> Pin | None:
        """Pin connected to this pad for the focused part."""
        return self.series.focus.pin_for_pad(self)

    def pin_for_part(self, part: Part) -> Pin | None:
        """Pin connected to this pad for a given part."""
        return part.pin_for_pad(self)

    def is_available_for_part(self, part: Part):
        return part.pad_is_available(self)

    @property
    def enable_predicate(self):
        return self._enable_predicate

    def mode_predicate(self, mode: PadMode):
        """Return the mode predicate for the given mode,  or Never.

        The mode predicate of a pad is an expression that is true iff the pad is
        in that mode. If the pad cannot be configured in that mode, the
        predicate is Never.
        """
        return self._mode_predicates.get(mode, Never)

    @property
    def is_power_pad(self) -> bool:
        return self.kind is POWER

    @property
    def mode(self) -> PadMode | None:
        return self._mode

    @property
    def possible_modes(self) -> Iterable[PadMode]:
        return self._mode_predicates.keys()

    @mode.setter
    def mode(self, mode: PadMode):
        # print(f"set {self} mode to {mode}")
        if mode in self.possible_modes:
            self._mode_predicates[mode].assign(1)

    # Backward compatibility
    def set_mode(self, mode: PadMode):
        self.mode = mode

    @property
    def possible_signals(self) -> Iterable[Signal]:
        return (mapping.signal for mapping in self._mappings)

    @property
    def mapped_signals(self) -> Iterable[Signal]:
        return (mapping.signal for mapping in self.active_mappings)

    @property
    def all_mappings(self) -> Iterable[Mapping]:
        return self._mappings

    @property
    def is_mapped(self) -> bool:
        return next(self.active_mappings, None) is not None

    @property
    def active_mappings(self) -> Iterable[Mapping]:
        return (mapping for mapping in self._mappings if mapping.is_active)

    def unmap(self):
        # print(f"unmap {self} [")
        assert not _in_callback()
        # Convert iterator to list because underlying list will change
        for mapping in list(self.active_mappings):
            mapping.withdraw()
        # print("]")

    def _add_mapping(self, mapping: Mapping):
        assert mapping.pad == self, mapping
        self._mappings.add(mapping)

    def _remove_mapping(self, mapping: Mapping):
        assert mapping.pad == self, mapping
        self._mappings.remove(mapping)

    def _set_no_altfun_predicate(self, expression: Expression):
        assert expression.width == 1, expression
        self._no_altfun_predicate = expression

    def _add_setting(self, setting: Setting):
        pass

    def _set_enable(self, enable_predicate: Expression):
        self._enable_predicate = enable_predicate

    def _add_mode_option(self, mode: PadMode, predicate: Expression):
        # print(f"mode predicate for {self} in mode {mode} is {predicate}")
        self._mode_predicates[mode] = predicate

        def on_predicate_change(value):
            # print(f"pad {self} in mode {mode} predicate becomes {value}")
            if value:
                self._on_mode_change(mode)

        predicate.watch_and_init(on_predicate_change)

    def _on_mode_change(self, mode: PadMode):
        if self._mode != mode:
            # print(f"_on_mode_change pad {self} to {mode}")
            self._mode = mode
            self.series._on_pad_mode_change(self)

    def __repr__(self):
        return self.name


class Signal:
    def __init__(
        self,
        peripheral: Peripheral,
        name: str,
        description: str,
        enable_predicate: Expression,
        mode_predicates: {PadMode: Expression} | None,
    ):
        """Create a signal.

        peripheral: the signal's peripheral. When the peripheral is disabled,
                    none of its signals is active, regardless of their enable
                    and mapped predicates.

        name: the signal's name, which needs to be a valid identifier.

        description: a description of the signal's function. This can be a long,
                     multi-line string.

        enable_predicate: optional boolean expression that is true when the
                          signal is active, given that its peripheral is
                          enabled.

        mode_predicates: a dict of which each key is a mode that is compatible
                         with this signal for some configuration of the
                         peripheral. The corresponding value is an expression
                         that is true iff the current configuration of the
                         peripheral allows that mode.

                         A missing dict has a special meaning: it means
                         that this signal ignores pad settings for the pad to
                         which it is mapped, so it does not require any specific
                         pad settings.
        """
        validate_name(name)
        if mode_predicates is not None and not mode_predicates:
            raise ConfigError(f"{self} has no compatible modes")
        if enable_predicate.constant_value == 0:
            raise ConfigError(f"{self} cannot be enabled")
        self._peripheral = peripheral
        self._name: str = name
        self._description: str = description
        self._enable_predicate = enable_predicate
        self._mode_predicates = mode_predicates
        self._mappings: set[Mapping] = set()
        self._mode: PadMode | None = self.preferred_mode
        peripheral._add_signal(self)
        self._register()
        self._output_clock = self.series.clock(name)
        if self._output_clock:
            self._bind_to_clock(self._output_clock)
            self._output_clock._bind_to_signal(self)
        # Auto-mapping needs to be postponed until all mappings have been added
        # so that the mapped predicate can be determined.  See _finalize(self).

    @property
    def series(self) -> Series:
        return self.peripheral.series

    @property
    def peripheral(self) -> Peripheral:
        return self._peripheral

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def output_clock(self) -> Clock | None:
        """The clock that drives this signal,  or None."""
        return self._output_clock

    @property
    def enable_predicate(self) -> Expression:
        return self._enable_predicate

    @property
    def is_enabled(self) -> bool:
        return bool(self.enable_predicate.value)

    @property
    def is_enabled_after_reset(self) -> bool:
        return self._is_enabled_after_reset

    @property
    def can_be_disabled(self) -> bool:
        return not self.enable_predicate.is_constant

    def set_enabled(self, enabled: bool) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(1 if enabled else 0)

    def enable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(1)

    def disable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(0)

    @property
    def requires_pad_configuration(self) -> bool:
        """True iff this signal requires the pad to which is is mapped to be
        configured with a compatible mode.

        Same signals, such as external clock inputs, ignore pad settings and
        will work regardless of the setting. For such signals, this flag will be
        false.
        """
        return self._mode_predicates is not None

    @property
    def requires_enabled_pad(self) -> bool:
        """True iff this signal needs the pad to be enabled to work.

        For most signals, the pad to which they are mapped needs to be enabled.
        A common exception are SWD and JTAG signals, because those must work
        before any firmware has been executed, to support debugging in the early
        stages of the boot process. Another common exception are signals that do
        not require pad configuration.

        For now, we assume that exactly the following signals do not require the
        pad to which they are mapped to be enabled:

         - signals of a DBG peripheral, and

         - signals that do not require pad configuration

        This rule can be refined as needed.
        """
        return (
            self.requires_pad_configuration
            and self.peripheral.kind is not PeripheralKind.DBG
        )

    @property
    def active_predicate(self) -> Expression:
        return self._active_predicate

    @property
    def is_active(self):
        return bool(self.active_predicate.value)

    @property
    def is_unmapped_active(self) -> bool:
        return bool(self._todo_predicate.value)

    @property
    def full_name(self) -> str:
        return f"{self.peripheral.name}.{self.name}"

    @property
    def all_mappings(self) -> Iterable[Mapping]:
        return self._mappings

    @property
    def available_mappings(self) -> Iterable[Mapping]:
        return self.mappings_for_part(self.series.focus)

    @property
    def is_mapped(self) -> bool:
        return next(self.active_mappings, None) is not None

    def is_mapped_to(self, pad: Pad):
        for mapping in self.active_mappings:
            if mapping.pad is pad:
                return True
        return False

    @property
    def active_mappings(self) -> Iterable[Mapping]:
        """Return an iterator over active mappings.

        A mapping is active when its predicate is true and the pad mode is one
        of the modes for this signal with a true predicate.
        """
        return (mapping for mapping in self._mappings if mapping.is_active)

    def mappings_for_part(self, part: Part) -> Iterable[Mapping]:
        return (
            mapping
            for mapping in self.all_mappings
            if mapping.is_available_for_part(part)
        )

    def auto_map(self):
        assert not _in_callback()
        if self.is_mapped:
            # print(f"auto-map {self} is already mapped")
            return
        # print(f"auto-map {self} [")

        # While auto-mapping an already enabled signal, do not change the
        # signal's mode predicates. Changing the mode predicates may have
        # side-effects on the peripheral configuration, which is usually
        # undesirable.
        # If the signal is not enabled yet, freezing mode predicates may
        # limit our options to enable it. When auto-mapping a disabled
        # signal, we assume that the intention is to enable it, which will
        # unavoidably affect the peripheral configuration. So we don't
        # freeze mode predicates in that case.
        # Start a transaction, so that mode predicates will automatically
        # be unfrozen after auto-mapping.
        with Transaction() as transaction:

            if self.is_enabled:
                for mode in self.possible_modes:
                    self.mode_predicate(mode).freeze()

            # Try first without changing mapping predicate, to avoid side-effects
            for mapping in self.available_mappings:
                if mapping.predicate.value and mapping.ok_for_auto_map:
                    mapping.apply()
                    # print(f"] use {mapping}")
                    return

            for mapping in self.all_mappings:
                if mapping.predicate.value:
                    # A mapping predicate for this signal is true, but another
                    # signal is already mapped to that pad, or the pad is not
                    # available for this part. This indicates that the chip
                    # remaps signals in groups, probably using remapping
                    # settings per peripheral. Give up to avoid undesired
                    # side-effects.
                    # print(f"] give up to avoid side-effects")
                    transaction.rollback()
                    return

            # Iterate over sorted list of available mappings, to get
            # reproducable results. Pad names often consist of letters followed
            # by digits. Using our natural sort key considers pins or pads in
            # natural order, often coming up with pins or pads that are close
            # together
            for mapping in sorted(
                self.available_mappings,
                key=lambda mapping: _natural_sort_key(mapping.pin.name),
            ):
                if mapping.ok_for_auto_map:
                    mapping.apply()

                    # print(f"] remap {mapping}")
                    return

        # print(f"  not: {' '.join(str(m.pin) for m in self.available_mappings)}")
        # print(f"] no mapping found")

    def unmap(self):
        # print(f"unmap {self} [")
        assert not _in_callback()
        # Convert iterator to list because underlying list will change
        for mapping in list(self.active_mappings):
            mapping.withdraw()
        # print("]")

    def unmap_pin(self, pin: Pin):
        self.series.focus.unmap(self, pin)

    @property
    def possible_pins(self) -> {Pin}:
        return {pad.pin for pad in self.possible_pads if pad.pin}

    def predicate_for_pin(self, pin: Pin, part: Part) -> Expression:
        """An expression that is true iff this signal is mapped to a given pin
        in the given part."""
        return Or.join(
            [
                mapping._active_predicate
                for mapping in self._mappings
                if part.pin_for_pad(mapping.pad)
            ]
        )

    @property
    def possible_pads(self) -> Iterable[Pad]:
        return (mapping.pad for mapping in self._mappings)

    @property
    def has_possible_pads(self) -> bool:
        return bool(self._mappings)

    def is_mapped_to_pad(self, pad: Pad) -> bool:
        return any(
            mapping.is_active
            for mapping in self._mappings
            if mapping.pad == pad
        )

    @property
    def mapped_pads(self) -> Iterable[Pad]:
        return (mapping.pad for mapping in self.active_mappings)

    def map_to_pad(self, pad: Pad):
        """Map this signal to the given pad only.

        Removes existing mappings to other pads
        """
        assert not _in_callback()
        mapping = self.mapping_for_pad(pad)
        if mapping:
            mapping.apply()

    def mapping_for_pad(self, pad: Pad) -> Mapping | None:
        for mapping in self._mappings:
            if mapping.pad is pad:
                return mapping

    @property
    def mapped_pins(self) -> Iterable[Pin]:
        return {
            mapping.pad.pin
            for mapping in self.active_mappings
            if mapping.pad.pin
        }

    def map_to_pin(self, pin: Pin):
        """Map this signal to the given pin only.

        Removes existing mappings to other pins
        """
        assert not _in_callback()
        mapping = self.mapping_for_pin(pin)
        if mapping:
            mapping.apply()

    def mapping_for_pin(self, pin: Pin) -> Mapping | None:
        for mapping in self._mappings:
            if mapping.pad.pin is pin:
                return mapping

    @property
    def possible_modes(self) -> Iterable[PadMode]:
        """All pad modes potentially compatible with this signal.

        Whether the mode is actually compatible may depend on the configuration
        of the signal's peripheral. See mode_predicate(mode).
        """
        if self.requires_pad_configuration:
            return self._mode_predicates.keys()
        else:
            return _pad_modes.values()

    @property
    def compatible_modes(self) -> Iterable[PadMode]:
        """Pad modes now compatible with this signal.

        Takes into account the current configuration of the signal's peripheral.
        It is possible that there are no compatible modes, meaning that the
        signal is not used in the current configuration.
        """
        if self.requires_pad_configuration:
            return (
                mode
                for mode, predicate in self._mode_predicates.items()
                if predicate.value
            )
        else:
            return _all_pad_modes()

    def is_compatible_mode(self, mode: PadMode) -> bool:
        return bool(self.mode_predicate(mode).value)

    def mode_predicate(self, mode: PadMode) -> Expression:
        if self.requires_pad_configuration:
            return self._mode_predicates.get(mode, Never)
        else:
            return Always

    @property
    def mode(self):
        """The desired mode for pads to which this signal is mapped.

        When a mapping becomes active, it will try to apply the mode to the pad.
        """
        return self._mode

    @mode.setter
    def mode(self, mode: PadMode):
        """Set the desired mode for pads to which this signal is mapped.

        When a mapping becomes active, it will try to apply the mode to the pad.
        """
        assert not _in_callback()
        if self.requires_pad_configuration:
            if self.is_compatible_mode(mode):
                self._mode = mode
                for mapping in self.active_mappings:
                    mapping.pad.mode = mode

    @property
    def preferred_mode(self) -> PadMode | None:
        """The preferred mode for the current peripheral settings."""
        if self.requires_pad_configuration:
            # Prefer mode without pull-up, pull-down or open-drain, so check
            # those modes first
            for mode in [FI, PP, PP_AF, AI, PU, PD, OD, OD_AF]:
                if self.is_compatible_mode(mode):
                    return mode

    def is_available_for_part(self, part: Part) -> bool:
        return any(
            pad.is_available_for_part(part) for pad in self.possible_pads
        )

    def _add_mapping(self, mapping: Mapping):
        assert mapping.signal == self, mapping
        self._mappings.add(mapping)

    def _remove_mapping(self, mapping: Mapping):
        assert mapping.signal == self, mapping
        self._mappings.remove(mapping)

    def _bind_to_clock(self, clock: Clock):
        assert not self.series.frozen
        self._enable_predicate = And(
            self._enable_predicate, clock.enable_predicate
        )

    def _finalize(self):
        """Finalize this signal.

        Computes any predicates that depend on mappings. Once a signal is
        finalized, no more mappings can be added.
        """
        mapped_predicate = Or.join(
            mapping._mapped_predicate for mapping in self.available_mappings
        )
        if (
            self.enable_predicate.is_constant
            and self.peripheral.enable_predicate.is_constant
            and not mapped_predicate.is_constant
        ):
            # Signal and peripheral are always enabled, but the signal can be
            # unmapped.  Unmapping it is most probably the intended way to
            # disable it.
            # To avoid adding it to the todo list (enabled but not mapped) when
            # disabled, set the enable predicate equal to the mapped predicate.
            # To also provide the user with a way to enable or disable it,
            # also generate a setting.
            # print(f"for {self} use mapped predicate as enabled predicate")
            self._enable_predicate = mapped_predicate
            PeripheralSetting(
                peripheral=self.peripheral,
                label=f"Enable {self.name}",
                description=self.description,
                kind=SettingKind.FLAG,
                predicate=Always,
                selector=self.enable_predicate,
            )
        self._active_predicate = And(
            self._enable_predicate, self.peripheral.enable_predicate
        )
        self._todo_predicate = And(
            self._active_predicate, Not(mapped_predicate)
        )
        for mapping in self._mappings:
            mapping._finalize()

    def _animate(self):
        self._is_enabled_after_reset = bool(self.enable_predicate.value)

        # Animate mappings before signals, so auto-mapping of signals reports
        # activated mappings.
        for mapping in self._mappings:
            mapping._animate()

        self.active_predicate.watch_and_init(lambda v: self._on_active(v))

        def on_todo(value):
            # print(f"on_todo {self} becomes {value} [")
            if value:
                self.series._on_add_unmapped_active_signal(self)
            else:
                self.series._on_remove_unmapped_active_signal(self)
            # print("]")

        self._todo_predicate.watch_and_init(on_todo)

        def on_enabled(value):
            # print(f"on_enabled {self} becomes {value} [")
            self.series._on_signal_enabled(self, bool(value))
            # print("]")

        self.enable_predicate.watch(on_enabled)

        if self.requires_pad_configuration:
            # Use aux function to have distinct mode variables in closure!
            def watch_mode(mode, predicate):
                def on_signal_mode_compatible(value: int):
                    # print(f"signal {self} mode compatible becomes {value}")
                    if not value and mode == self.mode:
                        self.mode = self.preferred_mode
                    self.series._on_signal_mode_compatible(self, mode)

                predicate.watch(on_signal_mode_compatible)

            for mode, predicate in self._mode_predicates.items():
                watch_mode(mode, predicate)

    def _on_active(self, value):
        # print(f"_on_active {self} becomes {value} [")
        if value:
            # When a signal becomes active, try to map it to a free pin as a
            # courtesy to the user. A signal can become active as a side
            # effect of enabling a peripheral or by changing a peripheral
            # setting.
            self.auto_map()
        # print("]")

    def _withdraw_mapping(self, mapping: Mapping):
        """Withdraw active mapping for non-custom signal."""
        # print("#### withdraw {mapping} [")
        assert mapping.is_active, mapping

        # Try to withdraw this mapping without affecting the active status of
        # other remappings for the pad or signal.
        # For a chip with per-pad remapping settings, arbitrarily changing the
        # remapping setting for the pad might activate another remapping for the
        # pad, which is to be avoided.
        # For a chip with per-peripheral remapping settings, arbitrarily
        # changing the remapping setting for the peripheral might activate
        # another mapping for the signal and/or other signals of the same
        # peripheral, which is also to be avoided. In all chips with
        # per-peripheral settings examined until now, this approach fail,
        # because all values of the remapping settings yield some mapping.
        # We could generate a predicate that freezes the settings to be left
        # unchanged. This would be a long expression, consisting of an And
        # expression with a lot of NotEqual terms, each of which has a ot of
        # ways to be achieved, but most of which are incompatible. Our
        # current expression code cannot reliably set such an expression.
        # The easier approach is to handle this in the json loading code, where
        # the distinction between per-pad and per-peripheral settings is known.
        # In the case of per-pad settings, we can derive a predicate that is
        # true when no alternate function can be mapped to the pad, regardless
        # of peripheral and signal enable predicates and pad mode. In the case of
        # per-peripheral settings, such a predicate is always false.
        # We call this the pad's no_altfun expression. Succesfully affirming it
        # will remove at most one non-custom expression: the one to be withdraw
        if mapping._is_altfun and mapping.pad._no_altfun_predicate.affirm():
            # Safe withdrawal of pad succeeded
            # print(f"#### ] applied no-altfun predicate "
            #      f"{mapping.pad._no_altfun_predicate}"
            # )
            return

        # If this is an output signal, change the pad mode to an input mode, or
        # a non-AF output mode.  First check other mappings to the same pin for
        # compatible modes.

        # TODO

        # Disable the signal or its peripheral.  Disabling the peripheral might
        # be preferred, because it is easy to undo.  Disabling the signal might
        # change other settings that are not obvious to the user.
        # Note that applying a mapping can enable signals and peripherals. It
        # therefore feels acceptable to disable them if needed when withdrawing
        # a mapping.
        # However, if the signal is mapped elsewhere, then make sure to keep it
        # active (i.e. keep the signal and its peripheral enabled).

        def signal_is_mapped_elsewhere():
            for m in mapping.signal.active_mappings:
                if m is not mapping:
                    return True

        # print(f"#### mapped elsewhere: {signal_is_mapped_elsewhere()}")
        if not signal_is_mapped_elsewhere():
            peripheral = mapping.peripheral
            # print(f"#### can be disabled: {peripheral.can_be_disabled}")
            if peripheral.can_be_disabled:
                peripheral.disable()
                # print(f"#### ] disable peripheral {peripheral}")
                return

        # print("#### ] failed")

    def _register(self):
        self.series._add_signal(self)

    def __repr__(self):
        return self.full_name


class Register:
    def __init__(
        self,
        series: Series,
        scope: str,
        name: str,
        description: str,
        address: int,
        width: int,
        reset_value: int,
        reset_mask: int,
    ):
        validate_name(name)
        self._width = width
        self._series = series
        self._scope = scope
        self._name = name
        self.description = description
        self._address = address
        self._reset_value = reset_value
        self._reset_mask = reset_mask
        self._fields = dict()
        super().__init__()
        series._add_register(self)

    @property
    def name(self) -> str:
        return self._name

    @property
    def scope(self) -> str:
        return self._scope

    @property
    def full_name(self) -> str:
        return f"{self.scope}.{self.name}"

    @property
    def fields(self) -> Iterable[Field]:
        return self._fields.values()

    def field(self, name) -> Field | None:
        return self._fields.get(name)

    @property
    def series(self) -> Series:
        return self._series

    @property
    def address(self) -> int:
        return self._address

    @property
    def width(self) -> int:
        return self._width

    @property
    def reset_value(self) -> int:
        return self._reset_value

    @property
    def reset_mask(self) -> int:
        return self._reset_mask

    def reset(self):
        with Transaction():
            for field in self.fields:
                field.reset()

    @property
    def value(self) -> int:
        value = 0
        for field in self.fields:
            value |= field.value << field.offset
        return value

    def assign(self, value: Number):
        # Aliasing is no longer correctly implemented, so we cannot assign
        # directly to a register.  Assign individual fields instead.
        with Transaction():
            for field in self.fields:
                field.assign(value >> field.offset & ((1 << field.width) - 1))

    def is_alias(self, other):
        return self.address == other.address and self.width == other.width

    def _add_field(self, field):
        if field.name in self._fields:
            raise ConfigError(f"duplicate field name '{field.name}' in {self}")
        self._fields[field.name] = field
        self.series._add_field(field)

    def __repr__(self):
        return self.full_name


class Field(Symbol):
    type = int

    def __init__(
        self,
        register: Register,
        name: str,
        description: str,
        offset: int,
        width: int,
    ):
        validate_name(name)
        self.name = name
        self.description = description
        self.register = register
        self.offset = offset
        self.width = width
        self._value = self.reset_value
        super().__init__()
        register._add_field(self)

    @property
    def series(self) -> Series:
        return self.register.series

    @property
    def address(self):
        return self.register.address

    @property
    def reset_value(self):
        return (self.register.reset_value >> self.offset) & (
            (1 << self.width) - 1
        )

    def reset(self):
        self.try_assign(self.reset_value)

    def is_alias(self, other):
        return (
            self.address == other.address
            and self.offset == other.offset
            and self.width == other.width
        )

    def eval(self) -> Number:
        return self._value

    def update(self, value: Number, mask: int = ~0):
        # print(f"Update {self} from {self.value} to {value} mask {mask}")
        assert not _in_callback()
        mask &= self.mask
        value &= mask
        if value != self.value:
            # print(f"Update {self} from {self.value} to {value} mask {mask}")
            # print(f"update {self} from {self.value} to {value} mask {mask} [")
            self.series.save_symbol_value(self)
            self._value = value
            self.series._on_change()
            # print("]")

    def __repr__(self):
        return f"{self.register}.{self.name}"


class Orientation(Enum):
    RIGHT = auto()
    LEFT = auto()


class ClockLayout:
    """Describes the clock tree routing of a clock signal to its users.

    The (x,y) coordinates set the position where the clock signal is generated
    Each route consists of a list of coordinates representing a polyline.
    Each dot is a position where two or more routes are joined.
    Each tag represent the position and orientation of a tag with the clock name
    used to route the clock to that position without drawing a line.

     - name_extension: how far to push the clock to the left (for RIGHT
       orientation) or right (for LEFT orientation) to make room to display the
       clock name above the line representing the clock signal. If zero, do not
       display the clock name.
    """

    def __init__(
        self,
        x: float,
        y: float,
        orientation: Orientation,
        name_extension: float,
        routes: [[(float, float)]],
        dots: [(float, float)],
        tags: [(float, float, Orientation)],
        sinks: [Sink],
    ):
        self._x = x
        self._y = y
        self._orientation = orientation
        self._name_extension = name_extension
        self._routes = routes
        self._dots = dots
        self._tags = tags
        self._sinks = sinks

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def orientation(self) -> Orientation:
        return self._orientation

    @property
    def name_extension(self) -> float:
        return self._name_extension

    @property
    def routes(self) -> [[(float, float)]]:
        return self._routes

    @property
    def dots(self) -> [(float, float)]:
        return self._dots

    @property
    def tags(self) -> [(float, float, Orientation)]:
        return self._tags

    @property
    def sinks(self) -> [ClockSink]:
        return self._sinks


class ClockSink:
    """A clock sink consumes a clock signal and does not produce one.

    Just like a Clock, a ClockSink is an object in a clock tree diagram.  In
    contrast to a Clock, a ClockSink does not define a clock signal, but links
    an existing clock to a consumer. of that clock.

    The display of a clock sink includes a label, which is a short string that
    identifies the consumer.  It is called the sink's label - and not its name -
    because the label may contain spaces and other characters that are not
    allowed in an identifier.

    Like a clock layout, a clock sink has an (x,y) position and an orientation.
    The (x,y) position is identical to the last point of a route in a clock
    layout. When orientation is RIGHT, the route comes from the left, and the
    label should be displayed to the right of (x,y). When orientation is LEFT,
    the route comes from the right, and the label should be displayed to the
    left of (x,y).
    """

    def __init__(
        self,
        clock: Clock,
        label: str,
        x: float,
        y: float,
        orientation: Orientation,
    ):
        self._clock = clock
        self._label = label
        self._x = x
        self._y = y
        self._orientation = orientation

    @property
    def clock(self) -> Clock:
        return self._clock

    @property
    def series(self) -> Series:
        return self._clock.series

    @property
    def label(self) -> str:
        return self._label

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def orientation(self) -> Orientation:
        return self._orientation


class InternalClockSink(ClockSink):
    """A clock sink representing a group of peripherals sharing a clock.

    To avoid overloading the clock tree diagram, peripherals using a clock
    signal are not shown individually, but grouped.  One example is the group of
    peripherals sharing a bus. Grouping of peripherals is a purely cosmetic
    operation, increasing the compactness of the clock tree. In that sense, it
    is akin to a clock layout object.

    The suggested representation of a clock sink is an arrowhead at the end of
    the incoming route, pointing to the label text. Clock tree layout will
    guarantee free space to display the clock sink of four units high and
    len(label)+3 units wide. This free space is centered around y.  It extends
    to the right of x for RIGHT orientation, and to the left of x for LEFT
    orientation.
    """

    def __init__(
        self,
        clock: Clock,
        label: str,
        x: float,
        y: float,
        orientation: Orientation,
        peripherals: Iterable[Peripheral],
        bus: Bus | None = None,
    ):
        super().__init__(clock, label, x, y, orientation)
        self._peripherals = set(peripherals)
        self._bus = bus

    @property
    def peripherals(self) -> Iterable[Peripheral]:
        return self._peripherals

    @property
    def bus(self) -> Bus | None:
        return self._bus


class ExternalClockSink(ClockSink):
    """A clock signal that is available on a pad of the chip.

    An external clock signal is typically called MCO in microcontroller jargon.

    The suggested representation of a clock sink is a little square on the fat
    line that represents the chip boundary. The square represents a pad. Plus a
    left-pointing arrow and the name of the clock, similar to an internal clock
    sink with LEFT orientation.
    """

    def __init__(
        self,
        clock: Clock,
        label: str,
        y: float,
    ):
        super().__init__(clock, label, self.x, y, Orientation.LEFT)

    x = -3


class Clock:
    """A clock is an object that generates a clock signal.

    It has a name and a description. Derived classes add more details.
    """

    def __init__(
        self,
        series: Series,
        name: str,
        description: str,
        enable_predicate: Expression = Always,
        ready_predicate: Expression = Always,
    ):
        validate_name(name)
        self._series = series
        self._name = name
        self.description = description
        self._settings = []
        self._enable_predicate = enable_predicate
        self._ready_predicate = ready_predicate
        self._users = []
        self._peripherals = []
        self._output_signal = None
        self._busses = set()
        self.series._add_clock(self)
        for clock in self.inputs:
            clock._add_user(self)

    @property
    def series(self) -> Series:
        return self._series

    @property
    def name(self) -> str:
        return self._name

    @property
    def hidden(self) -> bool:
        return self.name.startswith("_")

    @property
    def layout(self) -> ClockLayout:
        return self._layout

    @property
    def busses(self) -> Iterable[Bus]:
        return self._busses

    @property
    def inputs(self) -> [Clock]:
        return []

    @property
    def output_signal(self) -> Signal | None:
        """Output signal driven by this clock, or None."""
        return self._output_signal

    @property
    def enable_predicate(self) -> Expression:
        return self._enable_predicate

    @property
    def is_enabled(self) -> bool:
        return bool(self.enable_predicate.value)

    @property
    def can_be_disabled(self) -> bool:
        return not self.enable_predicate.is_constant

    def set_enabled(self, enabled: bool):
        assert not _in_callback()
        return self.enable_predicate.assign(int(enabled))

    def enable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(1)

    def disable(self) -> bool:
        assert not _in_callback()
        return self.enable_predicate.assign(0)

    @property
    def is_enabled_after_reset(self) -> bool:
        return self._is_enabled_after_reset

    @property
    def ready_predicate(self) -> Expression:
        return self._ready_predicate

    @property
    def users(self) -> Iterable[Clock]:
        return self._users

    @property
    def has_users(self) -> bool:
        return bool(self._users)

    @property
    def peripherals(self) -> Iterable[Peripheral]:
        return self._peripherals

    @property
    def drives_peripherals(self):
        return bool(self._peripherals)

    def _add_user(self, user: Clock):
        assert not self.series.frozen
        self._users.append(user)

    def _add_peripheral(self, peripheral: Peripheral):
        assert not self.series.frozen
        self._peripherals.append(peripheral)

    def _add_settings_to(self, clock: Clock):
        # print(f"# add settings of {self} to {clock}")
        if self.can_be_disabled:
            ClockSetting(
                clock,
                label=f"Enable {clock.name}",
                description=f"Enable {clock.description}",
                kind=SettingKind.FLAG,
                predicate=Always,
                selector=self.enable_predicate,
            )
        if self.output_signal:
            ClockSetting(
                clock,
                label=f"Enable {clock.name}",
                description=f"Enable {clock.description} output",
                kind=SettingKind.FLAG,
                predicate=self.enable_predicate,
                selector=self.output_signal.enable_predicate,
            )
        for subclock in self.inputs:
            if subclock and subclock.hidden:
                subclock._add_settings_to(clock)

    def _add_setting(self, setting: Setting):
        pass

    def _bind_to_signal(self, signal: Signal):
        assert not self.series.frozen
        if self._output_signal:
            raise ConfigError(
                f"More than one signal bound to the {self} clock: "
                f" {self._output_signal} and {signal}"
            )
        self._output_signal = signal

    def _add_bus(self, bus: Bus):
        assert not self.series.frozen
        self._busses.add(bus)

    def _finalize(self):
        if not self.hidden:
            self._add_settings_to(self)

    def _animate(self):
        self._is_enabled_after_reset = bool(self.enable_predicate.value)

    def _set_layout(self, layout: ClockLayout):
        self._layout = layout

    def __repr__(self):
        return self.name


class InternalClock(Clock):
    """An internal clock is generated internally in the microcontroller chip,
    typically using an RC circuit. It is less stable than an external clock
    controlled by a crystal or ceramic oscillator, and typically drifts with
    temperature or other environmental parameters.

    It adds to the base class a frequency (in Hz).
    """

    def __init__(self, frequency: float, *args, **kwargs):
        self.frequency = frequency
        super().__init__(*args, **kwargs)


class ExternalClockMode(Enum):
    XTAL = "XTAL"
    EXTCLK = "EXTCLK"


class ExternalClock(Clock):
    """An external clock is driven by an external component: either a
    crystal/ceramic oscillator or an externally generated clock signal.

    External clocks can have a minimum and a maximum frequency (in Hz). Both are
    optional.

    An external clock also has one or two signals, called xin and xout, which
    are mapped to external pins that connect the clock to an external crystal or
    ceramic oscillator or an external clock signal. "xin" is always required.
    "xout" is only required if the clock *can* be configured to use a crystal or
    ceramic oscillator.  When omitted, the clock can only access an externally
    generated clock signal (EXTCLK mode, bypass predicate is true).

    """

    def __init__(
        self,
        minimum_frequency: float | None = None,
        maximum_frequency: float | None = None,
        bypass_predicate: Expression = Always,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._xin = None
        self._xout = None
        self._minimum_frequency = minimum_frequency
        self._maximum_frequency = maximum_frequency
        self._frequency = maximum_frequency
        self._bypass_predicate = bypass_predicate
        bypass_predicate.watch(
            lambda value: self.series._on_external_clock_mode_change(self)
        )

    @property
    def xin(self) -> Signal:
        assert self._xin
        return self._xin

    @property
    def xout(self) -> Signal | None:
        return self._xout

    @property
    def frequency(self) -> float:
        return self._frequency

    def set_frequency(self, frequency: float):
        assert not _in_callback()
        assert frequency >= self.minimum_frequency
        assert frequency <= self.maximum_frequency
        self._frequency = frequency

    @property
    def minimum_frequency(self) -> Signal:
        return self._minimum_frequency

    @property
    def maximum_frequency(self) -> Signal:
        return self._maximum_frequency

    @property
    def mode(self) -> ExternalClockMode:
        if self._bypass_predicate.value:
            return ExternalClockMode.EXTCLK
        else:
            return ExternalClockMode.XTAL

    def set_mode(self, mode: ExternalClockMode):
        assert not _in_callback()
        self._bypass_predicate.assign(
            0 if mode is ExternalClockMode.XTAL else 1
        )

    @property
    def bypass_predicate(self) -> Expression:
        return self._bypass_predicate

    def _set_xin(self, xin: Signal):
        assert not self.series.frozen
        assert self._xin is None
        self._xin = xin
        xin._bind_to_clock(self)

    def _set_xout(self, xout: Signal):
        assert not self.series.frozen
        assert self._xout is None
        self._xout = xout
        xout._bind_to_clock(self)

    def _finalize(self):
        super()._finalize()
        if not self._xin:
            xin = self.series.signal(self.name)
            if xin:
                self._set_xin(xin)
            else:
                raise ConfigError(f"Missing signal for {self} external clock")


class MuxClock(Clock):
    def __init__(self, selector: Expression, inputs: [Clock], *args, **kwargs):
        self._inputs = inputs
        self._selector = selector
        super().__init__(*args, **kwargs)
        selector.watch(lambda x: self.series._on_clock_input(self))

    @property
    def nr_of_inputs(self) -> int:
        return len(self._inputs)

    @property
    def inputs(self) -> Iterator[Clock]:
        return self._inputs

    def input(self, index: int) -> Clock:
        return self._inputs[index]

    @property
    def value(self) -> int | None:
        value = self.selector.value
        return None if value < 0 or value >= self.nr_of_inputs else value

    @property
    def current(self) -> Clock | None:
        value = self.value
        return None if value is None else self._inputs[value]

    @property
    def selector(self) -> Expression:
        return self._selector

    def select(self, index: int):
        assert not _in_callback()
        self.selector.assign(index)

    def _add_settings_to(self, clock: Clock):
        super()._add_settings_to(clock)
        options = [input.name for input in self.inputs]
        sel2val = {
            sel: val
            for val, (sel, clock) in enumerate(
                (sel, clock) for sel, clock in enumerate(self._inputs) if clock
            )
        }
        predicate = self.enable_predicate
        if clock.output_signal and not clock.has_users:
            predicate = And(predicate, clock.output_signal.enable_predicate)
        ClockSetting(
            clock,
            label=f"Select {clock.name} clock",
            description=f"Select mux input clock {clock.description}",
            kind=SettingKind.LIST,
            predicate=predicate,
            selector=self.selector,
            sel2val=sel2val,
            options=options,
        )


class MultipliedClock(Clock):
    def __init__(
        self,
        input: Clock,
        expression: Expression,
        setting: Setting | None,
        *args,
        **kwargs,
    ):
        self._input = input
        self._expression = expression
        self._setting = setting
        super().__init__(*args, **kwargs)
        if setting:
            self._add_setting(setting)
        expression.watch(lambda x: self.series._on_clock_input(self))

    @property
    def multiplier(self) -> int:
        return self._expression.value

    @property
    def multiplier_expression(self) -> Expression:
        return self._expression

    @property
    def multiplier_setting(self) -> Setting | None:
        return self._setting

    @property
    def input(self) -> Clock:
        return self._input

    @property
    def inputs(self) -> [Clock]:
        return [self.input]


class DividedClock(Clock):
    def __init__(
        self,
        input: Clock,
        expression: Expression,
        setting: Setting | None,
        *args,
        **kwargs,
    ):
        self._input = input
        self._expression = expression
        self._setting = setting
        super().__init__(*args, **kwargs)
        if setting:
            self._add_setting(setting)
        expression.watch(lambda x: self.series._on_clock_input(self))

    @property
    def divider(self) -> int:
        return self._expression.value

    @property
    def divider_expression(self) -> Expression:
        return self._expression

    @property
    def divider_setting(self) -> Setting | None:
        return self._setting

    @property
    def input(self) -> Clock:
        return self._input

    @property
    def inputs(self) -> [Clock]:
        return [self.input]


class MappingState(Enum):
    NOT_ACTIVE = 0
    NORMAL = 1
    TENTATIVELY_ADDED = 2
    TENTATIVELY_REMOVED = 3


class Mapping:
    """A mapping of a signal to a pad under conditions.

    A mapping has a display state for the pin configuration diagram; see
    MappingState above. Some of these states are tentative. Tentative states are
    handled automatically by the Config objects that provides an interface to
    the pin configuration diagram. At the level of a mapping, the only thing
    that matters is whether the mapping is active or not. An active mapping has
    mapping state NORMAL or TENTATIVELY_ADDED. A inactive mapping has mapping
    state NOT_ACTIVE or TENTATIVELY_REMOVED.

    For a mapping to be active, the following conditions must be fulfilled:
     1. The pad (or its port) must be enabled, except for SWD/JTAG peripherals
     2. The pad must be in a mode compatible with the signal
     3. Remapping settings must be correct.
     4. The signal must be enabled.
     5. The signal's peripheral must be enabled.

    If all of these conditions are fulfilled, and the pad is bonded to a pin in
    the current part, the mapping will function as intended. For an input
    signal, the voltage on the pin will affect the operation of the signal's
    peripheral. For an output signal, the signal's peripheral can drive voltage
    on the pin. For the custom signal, it is more accurate to say that the
    voltage on the pin *can* affect the operation of the firmware or that the
    firmware *can* drive the voltage on the pin; whether this actually happens
    depends on the firmware (= application code).

    Whether the pad is bonded to a pin is not something to worry about here;
    this is taken care of by the Part object and the code that reports the
    mapping state to the pin configuration diagram.


    Terminology
    -----------

    A mapping is available when its pad is bonded to a pin in the current part.
    A signal is available when it has at least one available mapping.
    A mapping is active when all five predicates above are true.
    A signal is mapped when at least one mapping for that signal is active.
    A pad is mapped when at least one mapping for that pad is active.
    A pin is mapped when at least one pad bonded to that pin is mapped.


    Signal categories and pad modes
    -------------------------------

    We distinguish between three signal categories. Each is compatible with a set
    of mode settings for a pad.

      - digital input: FI, PU, PD

      - analog input: AI

      - digital output: PP, OD, PP-AF, OD-AF

    In the future, we may find more categories, such as analog output. The above
    three categories cover all cases encountered for now.

    Mappings fall into the same categories as their signal.


    Multiple mappings active for the same pad
    -----------------------------------------

    It is possible that two or more mappings for the same pad are active at the
    same time. This is an unusual situation that normally reflects a
    configuration error.  Such a situation cannot be achieved with the current
    user interface. Currently, whenever you apply a mapping to a pad, all
    existing mappings are automatically withdrawn. It is however still good to
    consider it in case we extend the user interface, for example by allowing
    the user to maually set bit fields.

    We should show a warning in such cases, but not necessarily forbid it, as
    there may be exceptional circumstances in which it makes sense. In other
    words, setting the pad mode to an output mode should not in itself un-apply
    the mapping of an input signal to that pad.

    A pad can be used as input even if it is configured as output. It will read
    the actual voltage on the pin. Especially if the pad is configured in open
    drain mode (OD or OD-AF), this is not necessarily the same as the current
    output signal, so doing this may be useful. To support this case, we can
    consider output modes to be compatible with an input signal. In other words,
    we should consider a mapping of an input signal to be active even if the
    pad is in output mode.

    Although we do say that an (analog or digital) input signal can be mapped to
    a pad in output mode, we should actively change the mode to an input mode
    when applying a mapping of the input signal.

    In contrast, a pad in AI mode cannot be used as digital input, because the
    Schmitt trigger that converts voltage into logic is disabled. Actually, AI
    is a good default mode for unused pins, because disabling the Schmitt
    trigger saves energy.


    Applying and withdrawing a mapping
    ----------------------------------

    To apply a mapping is to assert the five conditions mentioned above, so that
    it becomes active. A mapping can be applied because of a user request in the
    pin configuration diagram. It can also be applied when a peripheral is
    enabled, while the signal itself is already enabled. In the latter case, a
    mapping will be chosen automatically amongst the available mappings for that
    signal, avoiding pads for which another mapping is already applied.

    To withdraw a mapping is the opposite of applying it. A mapping can be
    withdrawn because of a user request in the pin configuration diagram. This
    can either be a direct withdrawal request (like "remove mapping"), or a
    request to map another signal to the pad, or a request to map the signal to
    another pad.


    Pad mode when applying or withdrawing a mapping
    -----------------------------------------------

    When a mapping is applied, we set the pad mode to one of the modes
    compatible with the mapping's signal. Preferred modes are FI, AI and PP. We
    do this whenever the current mapping is not compatible, even if another
    mapping is active on the pad. Maybe the existing mapping will be removed.
    Otherwise, there is a conflict, and it is up to the user to resolve it.

    When the last mapping is removed from a pad, we should not leave the pad in
    an output mode. We should either put it in FI mode (the default after reset)
    or in AI mode (to reduce power consumption by disabling the Schmitt
    trigger). Also provide a UI option to set the mode for unused pads?


    Strategy to withdraw a mapping
    ------------------------------

    At first sight, a mapping can be withdrawn by negating any one of the five
    conditions. However, disabling the signal or its peripheral is usually not
    the best approach. It can have side effects on the peripheral itself as well
    as on other mappings of the same signal. For example, it might be the user's
    intention to move the signal to a different pad/pin. Disabling the pad is
    also not safe: it might disable other pads in the same port as well. Safe
    options are conditions 2 and 3: mode change or remapping.

    If it is the intention to assign another signal to the pad, or to assign the
    signal to another pad, then doing so might be enough to withdraw the current
    mapping, due to the change in mode or remapping. Our strategy can be to
    first apply the new remapping, and then check if the current mapping is
    still active. If not, no further action is required.

    If the signal to be withdrawn is a custom signal, we can always withdraw it
    using the virtual remapping selector.

    Otherwise, if it is an alternate function (= non-custom signal) output and
    there are no other mappings active on the pad, we can (and must) change the
    mode to the default mode for pads without mapping, e.g. FI or AI. This will
    withdraw the current mapping.

    Otherwise, if there are other mappings, and the current mode is not
    compatible with any of these other mappings, we can set the mode to a
    compatible mode. This may or may not withdraw the current mapping.

    Otherwise, this is an alternative function input, or there are other
    mappings requiring a mode that does not withdraw the current mapping. In
    these cases, side-effects cannot be ruled out. We can either give up, or try
    to break one of the remaining conditions:

      - change remapping, which might or might not assign the signal to another
        pad as well as re-assign other signals of the same peripheral. Try it?

      - disable the signal. This might or might not have side effects on the
        peripheral settings.

      - disable the peripheral.

    How far should we go? Applying a mapping can also have these side-effects,
    so it might be acceptable.

    Predicates are always combined from more specific to less specific, to guide
    the order in which they are applied. This is important for example when
    enabling a peripheral also triggers auto-mapping of its active signals. By
    enabling the peripheral last, auto-mapping can be guided by more specific
    settings, instead of overriding them.

    Do not auto-set the pad mode when the mapping predicate becomes true.  The
    mapping predicate may become true during rollback, and rollback should
    restore the original state, not try to be smart and do additional settings.
    """

    def __init__(
        self,
        signal: Signal,
        pad: Pad,
        predicate: Expression = Always,
        is_altfun: bool = False,
    ):
        self._signal = signal
        self._pad = pad
        self._state = MappingState.NOT_ACTIVE
        self._predicate = predicate
        self._is_altfun = is_altfun
        # If the signal requires pad configuration, at least one of the possible
        # pad modes must be a possible mode for the signal. Otherwise, this
        # mapping can never be active, so something is probably wrong.
        if signal.requires_pad_configuration:
            if not (set(signal.possible_modes) & set(pad.possible_modes)):
                raise ConfigError(
                    f"no common modes for {pad} ("
                    f"{', '.join(str(mode) for mode in pad.possible_modes)})"
                    f" and {signal} ("
                    f"{', '.join(str(mode) for mode in signal.possible_modes)})"
                )
            self._mode_predicate = Or.join(
                And(signal.mode_predicate(mode), pad.mode_predicate(mode))
                for mode in signal.possible_modes
            )
        else:
            self._mode_predicate = Always

        self._mapped_predicate = And(self._predicate, self._mode_predicate)
        if signal.requires_enabled_pad:
            self._mapped_predicate = And(
                self._mapped_predicate, pad.enable_predicate
            )
        signal._add_mapping(self)
        pad._add_mapping(self)

    def _finalize(self):
        self._active_predicate = And(
            self._mapped_predicate,
            self.signal.active_predicate,
        )

    def _animate(self):
        def on_active(value: int):
            # print(f"on_active {self}: active becomes {value} [")
            # print(f"{self.signal} is_enabled={self.signal.is_enabled}")
            # Note: a mapping might become inactive and then active again within
            # a single transaction, for example when the signal's mode predicate
            # changes, and we change the pad's mode accordingly. This is
            # necessary for the intended behavior. Example: when changing SPI
            # role from slave to master, we do want to keep the current mapping
            # of the SPI signals.
            if not value:
                # This mapping was de-activated. If the cause was a change
                # in the signal's mode predicate, try to re-activate it.
                if self.signal.is_active and self.predicate.value:
                    # print(f"{self} de-activated due to mode predicate")
                    for mode in self.signal.compatible_modes:
                        # print(f"try to re-activate using {mode}")
                        self.pad.set_mode(mode)
                        if self.is_active:
                            # print("] re-activated")
                            return
                    # print("failed to re-activate")

            # print(f"set state of {signal} to {pad}"
            #      f" tentative={self.series.tentative_changes_active}"
            #      f" from state={self._state}"
            # )
            if value:
                if (
                    not self.series.tentative_changes_active
                    or self._state == MappingState.TENTATIVELY_REMOVED
                ):
                    self._set_state(MappingState.NORMAL)
                elif self._state == MappingState.NOT_ACTIVE:
                    self._set_state(MappingState.TENTATIVELY_ADDED)
            else:
                if (
                    not self.series.tentative_changes_active
                    or self._state == MappingState.TENTATIVELY_ADDED
                ):
                    self._set_state(MappingState.NOT_ACTIVE)
                elif self._state == MappingState.NORMAL:
                    self._set_state(MappingState.TENTATIVELY_REMOVED)
            # print(f"] to state={self._state}")

        self._active_predicate.watch_and_init(on_active)

    @property
    def signal(self) -> Signal:
        return self._signal

    @property
    def peripheral(self) -> Peripheral:
        return self.signal.peripheral

    @property
    def series(self) -> Series:
        assert self.signal.series == self.pad.series
        return self.signal.series

    @property
    def pad(self) -> Pad:
        return self._pad

    @property
    def pin(self) -> Pin | None:
        return self.pad.pin

    def pins_for_part(self, part: Part) -> Iterable[Pin]:
        return part.pins_for_pad(self.pad)

    @property
    def ok_for_auto_map(self) -> bool:
        """True iff this mapping can be used for auto-mapping.

        False if the corresponding pin is already in use.
        """
        if not self.series.focus:
            return False
        if not self.pad.pin:
            return False
        return not any(pad.is_mapped for pad in self.pad.pin.pads)

    @property
    def is_available(self) -> bool:
        return self.pad.is_available_for_part(self.series.focus)

    def is_available_for_part(self, part: Part) -> bool:
        return self.pad.is_available_for_part(part)

    @property
    def state(self) -> MappingState:
        return self._state

    @property
    def predicate(self) -> Expression:
        return self._predicate

    @property
    def mode_predicate(self) -> Expression:
        return self._mode_predicate

    @property
    def is_active(self) -> bool:
        return bool(self._active_predicate.value)

    def apply(self):
        """Apply this mapping.

        Withdraw other mappings for the same signal.
        """
        # print(f"apply {self} [")
        assert not _in_callback()
        self._active_predicate.affirm()
        for mapping in self.signal.active_mappings:
            if mapping is not self:
                mapping.withdraw()
        # print(f"]")

    def withdraw(self):
        """Withdraw (or 'un-apply') this mapping."""
        assert not _in_callback()
        if not self.is_active:
            return
        # Remaining code is different for custom signals,  so delegate to signal
        # print(f"withdraw {self} [")
        self.signal._withdraw_mapping(self)
        # print(f"]")

    def _set_state(self, state: MappingState):
        # print(f"  `-> set state of {self} to {state}")
        self._state = state
        self.series._on_mapping_state(self)

    def __repr__(self):
        return f"{self.signal} on {self.pad} (pin {self.pin})"


class Pin:
    def __init__(self, name: str, part: Part):
        self._name = name
        self._part = part
        self._pads: list[Pad] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def part(self) -> str:
        return self._part

    @property
    def series(self) -> Series:
        return self.part.series

    @property
    def pads(self) -> Iterable[Pad]:
        return self._pads

    @property
    def mode(self) -> PadMode | None:
        active_modes = [
            pad.mode for pad in self.pads if pad.mode is not _default_mode
        ]
        if len(active_modes) > 1:
            return None
        elif len(active_modes) == 1:
            return active_modes[0]
        else:
            return _default_mode

    def _add_pad(self, pad: Pad):
        assert not self.series.frozen
        assert (
            pad not in self._pads
        ), f"duplicate pad {pad} for pin {pin} in {self.part}"
        self._pads.append(pad)

    def __repr__(self):
        return self.name


class Part:
    def __init__(
        self,
        series: Series,
        name: str,
        package: Package,
    ):
        validate_name(name)
        self._series = series
        self._name = name
        self._package = package
        self._pins = {name: Pin(name, self) for name in package.pin_names}
        self._pad2pin = {}
        self._configs: set["Config"] = set()
        series._add_part(self)

    @property
    def series(self) -> Series:
        return self._series

    @property
    def name(self) -> str:
        return self._name

    @property
    def package(self) -> Package:
        return self._package

    @property
    def pins(self) -> Iterable[Pin]:
        return self._pins.values()

    def pin(self, name: str) -> Pin | None:
        """Pin with given name, or None."""
        return self._pins.get(name)

    def pin_mappings(self, pin: Pin) -> Iterable[Mapping]:
        return (
            mapping
            for pad in self.pads_for_pin(pin)
            for mapping in pad.all_mappings
            if mapping.signal.is_available_for_part(self)
            and mapping.peripheral.is_usable_for_part(self)
        )

    def sorted_pin_mappings(self, pin: Pin) -> Iterable[Mapping]:
        return sorted(
            self.pin_mappings(pin),
            key=lambda mapping: (
                mapping.peripheral.name,
                mapping.signal.name,
                mapping.pad.name,
            ),
        )

    def signal_mappings(self, signal: Signal) -> Iterable[Mapping]:
        return (
            mapping
            for mapping in signal.all_mappings
            if self.pin_for_pad(mapping.pad)
        )

    def sorted_signal_mappings(self, signal: Signal) -> Iterable[Mapping]:
        return sorted(
            self.signal_mappings(signal),
            key=lambda mapping: (
                mapping.pad.name,
                mapping.peripheral.name,
                mapping.signal.name,
            ),
        )

    def signal_to_pin_mappings(
        self,
        signal: Signal,
        pin: Pin,
    ) -> Iterable[Mapping]:
        return (
            mapping
            for mapping in self.pin_mappings(pin)
            if mapping.signal == signal
        )

    def unmap(self, signal: Signal, pin: Pin):
        # print(f"unmap {signal} to {pin} [")
        assert not _in_callback()
        # Convert iterator to list because underlying list will change
        for mapping in list(self.signal_to_pin_mappings(signal, pin)):
            mapping.withdraw()
        # print("]")

    def unmap_pin(self, pin: Pin):
        assert not _in_callback()
        # Convert iterator to list because underlying list will change
        for mapping in list(self.pin_mappings(pin)):
            mapping.withdraw()

    def auto_map_active_signals(self):
        """Try to map each enabled signal of an enabled peripheral.

        If a mapping to an unused pin is found,  that mapping will be applied.
        """
        assert not _in_callback()
        for peripheral in self.peripherals:
            if peripheral.is_enabled:
                peripheral.auto_map_enabled_signals()

    @property
    def pads(self) -> Iterable[Pad]:
        """Pads bonded to some pin of this part."""
        return self._pad2pin.keys()

    def pad(self, name: str) -> Pad | None:
        """Pad with given name, if bonded to a pin; otherwise, None."""
        pad = self.series.pad(name)
        if pad and self.pin_for_pad(pad):
            return pad

    def pad_is_available(self, pad: Pad) -> bool:
        """True iff the pad is bonded to a pin in this part."""
        return pad in self._pad2pin

    def pin_for_pad(self, pad: Pad) -> Pin:
        """Pin bonded to the given pad in this part."""
        return self._pad2pin.get(pad)

    def pins_for_pad(self, pad: Pad) -> Iterable[Pin]:
        """All pins bonded to the given pad in this part."""
        return (pin for pin in self.pins if pad in pin.pads)

    def pads_for_pin(self, pin: Pin) -> Iterable[Pad]:
        """Pads (usually 1) bonded to a given pin of this part."""
        assert pin.part == self
        return pin.pads

    def signals_for_pin(self, pin: Pin) -> Iterable[Signal]:
        """Signals that can be mapped to the given pin."""
        return {
            signal
            for pad in self.pads_for_pin(pin)
            for signal in pad.possible_signals
        }

    def is_power_pin(self, pin: Pin) -> bool:
        # We do not expect power pads to be bonded to a pin with other pads,
        # but if it happens, a single non-power pad bonded to the pin makes
        # this a non-power pin.
        for pad in self.pads_for_pin(pin):
            if not pad.is_power_pad:
                return False
        return True

    @property
    def pad_modes(self) -> Iterable[PadMode]:
        return _pad_modes.values()

    def pad_mode(self, name: str) -> PadMode | None:
        return _pad_mode(name)

    @property
    def peripherals(self) -> Iterable[Peripheral]:
        return (
            peripheral
            for peripheral in self.series.peripherals
            if peripheral.is_usable_for_part(self)
        )

    def peripheral(self, name) -> Peripheral | None:
        peripheral = self.series.peripheral(name)
        if peripheral and peripheral.is_usable_for_part(self):
            return peripheral

    @property
    def clocks(self) -> Iterable[Clock]:
        return self.series.clocks

    def clock(self, name) -> Clock | None:
        return self.series.clock(name)

    def lookup(self, name: str) -> Expression | None:
        return self.series.lookup(name)

    def expression(self, text: str) -> Expression:
        def lookup(name):
            return self.lookup(name)

        return expression.parse(text, lookup)

    def reset(self):
        assert self.series.focus is self
        assert not _in_callback()
        self.series.reset()

    def begin_tentative_changes(self):
        return self.series.begin_tentative_changes()

    def commit_tentative_changes(self):
        return self.series.commit_tentative_changes()

    def rollback_tentative_changes(self):
        return self.series.rollback_tentative_changes()

    @property
    def tentative_changes_active(self) -> bool:
        return self.series.tentative_changes_active

    @property
    def has_unsaved_changes(self) -> bool:
        return self.series.has_unsaved_changes

    def reset_unsaved_changes_flag(self):
        self.series.reset_unsaved_changes_flag()

    def _bond(self, pad: Pad, pin: Pin):
        assert not self.series.frozen
        # assert pad not in self._pad2pin, \
        #    f"duplicate pins {self.pin_for_pad(pad)} and {pin} " \
        #    f"for pad {pad} in {self}"
        self._pad2pin[pad] = pin
        pin._add_pad(pad)

    def _add_config(self, config):
        assert self.series.focus is self
        assert self.series.frozen
        self._configs.add(config)
        for pad in self.pads:
            if pad.mode != _default_mode:
                config._on_pad_mode_change(pad)
            for mapping in pad.all_mappings:
                if mapping.state != MappingState.NOT_ACTIVE:
                    config._on_mapping_state(mapping)
        for peripheral in self.series.peripherals:
            if peripheral.is_enabled:
                config._on_peripheral_enabled(peripheral, True)
            for signal in peripheral.signals:
                if signal.is_unmapped_active:
                    config._on_add_unmapped_active_signal(signal)

    def _remove_config(self, config):
        self._configs.remove(config)

    def _on_unsaved_changes(self):
        for config in self._configs:
            config._on_unsaved_changes()

    def _on_add_signal(self, signal: Signal):
        for config in self._configs:
            config._on_add_signal(signal)

    def _on_remove_signal(self, signal: Signal):
        for config in self._configs:
            config._on_remove_signal(signal)

    def _on_mapping_state(self, mapping):
        if mapping.is_available_for_part(self):
            for config in self._configs:
                config._on_mapping_state(mapping)

    def _on_pad_mode_change(self, pad: Pad):
        if pad.is_available_for_part(self):
            for config in self._configs:
                config._on_pad_mode_change(pad)

    def _on_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        if peripheral.is_usable_for_part(self):
            for config in self._configs:
                config._on_peripheral_enabled(peripheral, enabled)

    def _on_signal_enabled(self, signal: Signal, enabled: bool):
        if signal.is_available_for_part(self):
            for config in self._configs:
                config._on_signal_enabled(signal, enabled)

    def _on_signal_mode_compatible(self, signal: Signal, mode: PadMode):
        if signal.is_available_for_part(self):
            for config in self._configs:
                config._on_signal_mode_compatible(signal, mode)

    def _on_setting_enabled(self, setting: Setting):
        for config in self._configs:
            config._on_setting_enabled(setting)

    def _on_setting(self, setting: Setting):
        for config in self._configs:
            config._on_setting(setting)

    def _on_clock_input(self, clock: MuxClock):
        for config in self._configs:
            config._on_clock_input(clock)

    def _on_clock_multiplier(self, clock: MultipliedClock):
        for config in self._configs:
            config._on_clock_multiplier(clock)

    def _on_clock_divider(self, clock: DividedClock):
        for config in self._configs:
            config._on_clock_divider(clock)

    def _on_external_clock_mode_change(self, clock: ExternalClock):
        for config in self._configs:
            config._on_external_clock_mode_change(clock)

    def _on_add_unmapped_active_signal(self, signal: Signal):
        # Do not check is signal is available for part here. This may be called
        # when the signal has just been created and no mappings have been added
        # yet.
        for config in self._configs:
            config._on_add_unmapped_active_signal(signal)

    def _on_remove_unmapped_active_signal(self, signal: Signal):
        if signal.is_available_for_part(self):
            for config in self._configs:
                config._on_remove_unmapped_active_signal(signal)

    def __repr__(self):
        return self.name


class VirtualSelector(Symbol):
    def __init__(self, series: Series, name: str = ""):
        super().__init__()
        self._series = series
        self.name = name
        self._value = self.reset_value
        self._tentative = False
        self._original_value = None

    @property
    def series(self) -> Series:
        return self._series

    reset_value = 0

    def eval(self) -> int:
        return self._value

    def update(self, value: int, mask: int = ~0):
        assert not _in_callback()
        new_value = (self._value & ~mask) | (value & mask)
        if new_value != self._value:
            self.series.save_symbol_value(self)
            if self._tentative and self._original_value is None:
                self._original_value = self._value
            self._value = new_value
            assert self.series.saved_symbol_value(self) == self._original_value

    def begin_tentative_changes(self):
        assert not self._tentative
        self._tentative = True

    def commit_tentative_changes(self):
        assert self._tentative
        self._tentative = False
        self._original_value = None

    def rollback_tentative_changes(self):
        assert self._tentative
        self._tentative = False
        if self._original_value is not None:
            self.assign(self._original_value)
            self._original_value = None

    def __repr__(self):
        return f"(virtual:{self.name})"


class CustomPeripheral(Peripheral):

    def __init__(self, modes: [PadMode], *args, **kwargs):
        self._mode_predicates = {mode: Always for mode in modes}
        super().__init__(*args, **kwargs)

    is_configurable = True
    supports_custom_signals = True

    def add_signal(self, name: str, description: str = "") -> Signal:
        assert not _in_callback()
        signal = CustomSignal(
            peripheral=self,
            name=name,
            description=description,
            mode_predicates=self._mode_predicates,
        )
        self.series._on_change()
        return signal

    def remove_signal(self, signal: Signal):
        assert not _in_callback()
        assert signal in self.signals
        signal._drop()
        self._remove_signal(signal)
        self.series._on_change()


class CustomSignal(Signal):
    def __init__(
        self,
        peripheral: Peripheral,
        name: str,
        description: str,
        mode_predicates: {PadMode: Expression},
    ):
        assert not _in_callback()
        super().__init__(
            peripheral=peripheral,
            name=name,
            description=description,
            enable_predicate=Always,
            mode_predicates=mode_predicates,
        )
        self._selector = VirtualSelector(self.series, name)
        self.series._add_selector(self._selector)
        self._selector.watch(lambda x: self.series._on_change())
        possible_modes = set(self.possible_modes)

        # Add a selector value for each compatible GPIO pin. Selector value 0
        # corresponds to no mapping.
        next_value = 0
        for pad in self.series.pads:
            if set(pad.possible_modes) & possible_modes:
                next_value += 1
                CustomMapping(
                    signal=self,
                    pad=pad,
                    predicate=Equal(self._selector, Literal(next_value)),
                )
        self._finalize()
        self._animate()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name):
        self.peripheral._rename_signal(self, name)

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, description):
        if description != self._description:
            self._description = description
            self.series._on_change()

    @property
    def pad(self):
        pads = list(self.mapped_pads)
        assert len(pads) <= 1
        return pads[0] if pads else None

    def _drop(self):
        self._selector.assign(0)
        self.series._remove_selector(self._selector)

    def _withdraw_mapping(self, mapping: Mapping):
        self._selector.assign(0)

    def _register(self):
        # Custom signals are not registered in the series for lookup-by-name.
        # Lookup-by-name is only used for the global mapping table, when there
        # are no custom signals yet.
        pass

    def _on_active(self, value):
        # Custom signals are always active, but in contrast to normal signals,
        # they should not be auto-mapped when created. They are created from
        # application code calling add_signal, and the application code expects
        # add_signal to return the new signal before potentially trying to do
        # something like auto-mapping. Executing a callback for the signal is
        # auto-mapped while being created may cause unexpected behavior of the
        # application code, including a recursive call to create the custom
        # signal again.
        pass


class CustomMapping(Mapping):
    def withdraw(self):
        assert not _in_callback()
        self.signal._selector.assign(0)


class GPIO(CustomPeripheral):
    def __init__(self, series: Series):
        super().__init__(
            series=series,
            name="GPIO",
            description="General Purpose Input/Output",
            kind=PeripheralKind.GPIO,
            clock=series.clock("AHB1"),
        )


class ClockTree(Peripheral):
    def __init__(self, series: Series, name: str, scopes: set[str]):
        super().__init__(
            series=series,
            name=name,
            description="Clock Tree",
            kind=PeripheralKind.CLOCK,
            scopes=scopes,
        )


def _natural_sort_key(name: str):
    """Get a key for natural sorting by name.

    Pin, pad and peripheral names typically consist of letters followed by
    digits.  We want to sort the letters alphabetically and the numbers
    numerically.
    """
    return (
        "".join(filter(lambda x: not str.isdigit(x), name)),
        int("0" + "".join(filter(str.isdigit, name))),
    )
