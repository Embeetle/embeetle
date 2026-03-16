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

from .model import *
from .codegen import *


class Config:

    def __init__(self, part: Part):
        self.part = part
        self._tentative_mappings: set[Mapping]
        self._mapping_handles = {}
        self._labels: Dict[Pair[Signal, Pin], "_Label"] = {}
        self.part._add_config(self)

    def drop(self):
        self.part._remove_config(self)

    @property
    def series(self) -> Series:
        return self.part.series

    def get_data(self) -> dict[Any]:
        """Get json-compatible data for current configuration.

        Usable to save current configuration, to re-load it later. Resets the
        unsaved-changes flag.
        """
        return self.series.get_data()

    def set_data(self, data: dict[Any]):
        """Set json-compatible data for current configuration.

        Usable to reload saved configuration. Resets the unsaved-changes flag.

        Data must be in the same format as returned by get_data. Otherwise, an
        exception will be raised and the unsaved-changes flag will be set.
        """
        self.series.set_data(data)

    def generate_code(self, folder: str):
        """Generate code with current settings in the given folder.

        May overwrite or remove existing files in that folder.
        """
        generate_code(self.part, folder)

    def is_peripheral_enabled(self, peripheral: Peripheral) -> bool:
        return peripheral.is_enabled

    def set_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        peripheral.set_enabled(enabled=enabled)

    def is_signal_enabled(self, signal: Signal) -> bool:
        return signal.is_enabled

    def pin_mappings(self, pin: Pin) -> Iterable[Mapping]:
        return self.part.pin_mappings(pin)

    def sorted_pin_mappings(self, pin: Pin) -> Iterable[Mapping]:
        return self.part.sorted_pin_mappings(pin)

    def signal_mappings(self, signal: Signal) -> Iterable[Mapping]:
        return self.part.signal_mappings(signal)

    def sorted_signal_mappings(self, signal: Signal) -> Iterable[Mapping]:
        return self.part.sorted_signal_mappings(signal)

    def apply_mapping(self, mapping: Mapping):
        mapping.apply()

    def withdraw_mapping(self, mapping: Mapping):
        mapping.withdraw()

    def unmap(self, signal: Signal, pin: Pin):
        self.part.unmap(signal, pin)

    def unmap_pin(self, pin: Pin):
        self.part.unmap_pin(pin)

    def modes_for_signal_pads(self, signal: Signal) -> Set["PadMode"]:
        return {
            mode for pad in signal.mapped_pads for mode in pad.possible_modes
        }

    def value(self, expression: Expression | str) -> int:
        if type(expression) == str:
            expression = self.part.expression(expression)
        return expression.value

    def assign(self, expression: Expression | str, value: int):
        if type(expression) == str:
            expression = self.part.expression(expression)
        expression.assign(value=value)

    @property
    def signals(self):
        return self.part.signals

    def set(self, setting: Setting, value: int):
        assert False, "not implemented yet"

    def active_pins_for_signal(self, signal: Signal):
        return {pad.pin for pad in signal.mapped_pads if pad.pin}

    def is_active_pin_for_signal(self, signal: Signal, pin: Pin):
        return any(
            signal.is_mapped_to_pad(pad) for pad in self.part.pads_for_pin(pin)
        )

    def active_pads_for_signal(self, signal: Signal):
        return signal.mapped_pads

    def is_active_pad_for_signal(self, signal: Signal, pad: Pad):
        return signal.is_mapped_to_pad(pad)

    def is_power_pin(self, pin: Pin):
        return self.part.is_power_pin(pin)

    def begin_tentative_changes(self):
        # print("begin tentative [")
        assert not self.tentative_changes_active
        self.part.begin_tentative_changes()
        # print("]")

    def commit_tentative_changes(self):
        # print("commit tentative [")
        assert self.tentative_changes_active
        self.part.commit_tentative_changes()
        # print("]")

    def rollback_tentative_changes(self):
        # print("rollback tentative [")
        assert self.tentative_changes_active
        self.part.rollback_tentative_changes()
        # print("]")

    @property
    def tentative_changes_active(self) -> bool:
        return self.part.tentative_changes_active

    @property
    def tentative_changes_level(self) -> int:
        return self.part.tentative_changes_level

    @property
    def has_unsaved_changes(self) -> bool:
        """True iff there are unsaved changed.

        Tentative changes do not count.
        """
        return self.series.has_unsaved_changes

    # Callbacks

    def on_unsaved_changes(self, changed: bool):
        """Report a change in the unsaved-changes flag."""
        pass

    def on_add_signal(self, signal: Signal):
        """Update the user interface for a new signal."""
        pass

    def on_remove_signal(self, signal: Signal):
        """Update the user interface for a removed signal."""
        pass

    def on_signal_mapped(self, signal: Signal, pads: Iterable[Pad]):
        """Update the user interface for changed mappings for the signal.

        Can be used for example to update the signal mapping table for each
        peripheral.
        """
        pass

    def on_add_mapping(self, signal: Signal, pin: Pin) -> Any:
        """Show a mapping of signal to pin in the user interface.

        signal: the mapped signal

        pin: the pin number on which to show the mapping

        Return an object of your choice, representing the mapping in the user
        interface. Whatever you return will be passed to remove_mapping and
        set_mapping_state.

        If you are not interested in remove_mapping and set_mapping_state
        callbacks, return None. They will never be called.
        """
        return self.add_mapping(signal, pin)

    def on_remove_mapping(self, mapping):
        """Remove the  mapping in the user interface.

        mapping: the object returned by add_mapping. If you need to know the
        signal or pin of the mapping, store them in the object returned from
        add_mapping.
        """
        self.remove_mapping(mapping)

    def on_mapping_state(self, mapping, state: MappingState):
        """Set the state of an existing mapping.

        mapping: the object returned by add_mapping. If you need to know the
        signal or pin of the mapping, store them in the object returned from
        add_mapping.

        state: the new mapping state,  which can be MappingState.NORMAL,
        MappingState.TENTATIVELY_ADDED or MappingState.TENTATIVELY_REMOVED.
        This is intended to set the display style of the mapping.

        A user interface can decide to postpone displaying the mapping until the
        first call to set_mapping_state. Every call to add_mapping will always
        be followed immediately by a call to set_mapping_state, unless
        add_mapping returns None.

        A user interface that does not use styling can ignore calls to
        set_mapping_state and immediately display the mapping when it is added.
        """
        self.set_mapping_state(mapping, state)

    def on_add_unmapped_active_signal(self, signal: Signal):
        """Add a signal to the todo-list of signals to be mapped to a pin."""
        pass

    def on_remove_unmapped_active_signal(self, signal: Signal):
        """Remove a signal from the todo-list of signals to be mapped to a
        pin."""
        pass

    def on_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        """Set the enabled state of a peripheral.

        Current state is peripheral.is_enabled.
        """
        pass

    def on_signal_enabled(self, signal: Signal, enabled: bool):
        """Set the enabled state of a signal.

        Current state is signal.is_enabled.
        """
        pass

    def on_signal_mode_compatible(
        self, signal: Signal, mode: PadMode, is_compatible: bool
    ):
        """Change whether the mode is compatible with the signal or not.

        This can add/remove/enable/disable the mode in a mode selection menu for
        the signal.
        """
        pass

    def on_setting_enabled(self, setting: Setting, enabled: bool):
        """Set the enabled state of a setting.

        Initial state can be obtained as setting.is_enabled. Any change will be
        reported using this callback.
        """
        pass

    def on_setting(self, setting: Setting, option: int | None):
        """Set option for a setting.

        Option can be None, meaning none of the setting's options has been
        selected.  The initial option can be obtained as setting.value. Any
        change will be reported using this callback.
        """
        pass

    def on_clock_input(self, clock: MuxClock, value: int | None):
        """Set the selected input for a mux clock.

        Value ranges from 0 to #inputs-1, and can be None if the selector has
        reserved values. The initial value can be obtained as clock.value. Any
        change will be reported using this callback.
        """
        pass

    def on_clock_multiplier(
        self, clock: MultipliedClock, multiplier: int | None
    ):
        """Set the multiplier for a multiplied clock (PLL).

        The initial multiplier can be obtained as clock.multiplier. It can be
        None of the selector has reserved values. Any change will be reported
        using this callback.
        """
        pass

    def on_clock_divider(self, clock: DividedClock, divider: int):
        """Set the divider for a divided clock (prescaler).

        The initial divider can be obtained as clock.divider. It can be None if
        the selector has reserved values. Any change will be reported using this
        callback.
        """
        pass

    def on_pad_mode_change(self, pad: Pad):
        pass

    def on_external_clock_mode_change(self, clock: ExternalClock):
        pass

    # Backward compatibility

    def add_mapping(self, signal: Signal, pin: Pin) -> Any:
        pass

    def remove_mapping(self, mapping):
        pass

    def set_mapping_state(self, mapping, state: MappingState):
        pass

    # Private methods

    def _on_unsaved_changes(self):
        # print(f"#### on_unsaved_changes {self.has_unsaved_changes}")
        self.on_unsaved_changes(self.has_unsaved_changes)

    def _on_add_signal(self, signal: Signal):
        # print(f"#### on_add_signal {signal}")
        self.on_add_signal(signal)

    def _on_remove_signal(self, signal: Signal):
        # print(f"#### on_remove_signal {signal}")
        self.on_remove_signal(signal)

    def _on_mapping_state(self, mapping: Mapping):
        pin = mapping.pad.pin
        if pin:
            # print(f"#### on_mapping_state {mapping} {mapping.state} [")
            # import traceback
            # traceback.print_stack()

            signal = mapping.signal
            label = self._labels.get((signal, pin))
            if not label:
                label = _Label(self, pin)
                self._labels[(signal, pin)] = label
            label.update_mapping(mapping)
            if not label.mappings:
                self._labels.pop((signal, pin))
            # print("#### ]")

    def _on_pad_mode_change(self, pad: Pad):
        # print(f"#### on_pad_mode_change {pad} {pad.mode} [")
        self.on_pad_mode_change(pad)
        # print("#### ]")

    def _on_add_unmapped_active_signal(self, signal: Signal):
        # print(f"#### on_add_unmapped_active_signal {signal}")
        self.on_add_unmapped_active_signal(signal)

    def _on_remove_unmapped_active_signal(self, signal: Signal):
        # print(f"#### on_remove_unmapped_active_signal {signal} [")
        self.on_remove_unmapped_active_signal(signal)
        # print("#### ]")

    def _on_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        # print(f"#### on_peripheral_enabled {peripheral} {enabled} [")
        self.on_peripheral_enabled(peripheral, enabled)
        # print("#### ]")

    def _on_signal_enabled(self, signal: Signal, enabled: bool):
        # print(f"#### on_signal_enabled {signal} {enabled} [")
        self.on_signal_enabled(signal, enabled)
        # print("#### ]")

    def _on_signal_mode_compatible(self, signal: Signal, mode: PadMode):
        compatible = signal.is_compatible_mode(mode)
        # print(f"#### on_signal_mode_compatible {signal} {mode} {compatible} [")
        self.on_signal_mode_compatible(signal, mode, compatible)
        # print("#### ]")

    def _on_setting_enabled(self, setting: Setting):
        # print(f"#### on_setting_enabled {setting} {setting.is_enabled} [")
        self.on_setting_enabled(setting, setting.is_enabled)
        # print("#### ]")

    def _on_setting(self, setting: Setting):
        # print(f"#### on_setting {setting} to {setting.value} [")
        self.on_setting(setting, setting.value)
        # print("#### ]")

    def _on_clock_input(self, clock: MuxClock):
        print(f"#### on_clock_input {clock} to {clock.value} [")
        self.on_clock_input(clock, clock.value)
        print("#### ]")

    def _on_clock_multiplier(self, clock: MultipliedClock):
        print(f"#### on_clock_multiplier {clock} to {clock.multiplier} [")
        self.on_clock_multiplier(clock, clock.multiplier)
        print("#### ]")

    def _on_clock_divider(self, clock: DividedClock):
        print(f"#### on_clock_divider {clock} to {clock.divider} [")
        self.on_clock_divider(clock, clock.divider)
        print("#### ]")

    def _on_external_clock_mode_change(self, clock: ExternalClock):
        # print(f"####  on_external_clock_mode_change {clock} {clock.mode} [")
        self.on_external_clock_mode_change(clock)
        # print("#### ]")


class _Label:
    """Represents a label in the user interface,  with a unique handle.

    A label represents all displayed mappings between the same pin and signal,
    in other words all mappings that are not in the NOT_ACTIVE state.

    It must be notified of all state changes of mappings between the pin and
    signal, and in response, it will do the necessary callbacks.

    config: the object on which to do callbacks

    pin: the pin for which mappings are represented

    The signal is derived on the fly from the mappings passed to the label.  The
    pin cannot be derived in this manner, because a pad can be connected to more
    than one pin.
    """

    def __init__(self, config: Config, pin: Pin):
        self.config = config
        self.pin = pin
        self.handle = None
        self.mappings = set()
        self.state = MappingState.NOT_ACTIVE

    def update_mapping(self, mapping):
        # print(f"#### update_mapping for {mapping} {mapping.state}")
        signal = mapping.signal
        if mapping.state != MappingState.NOT_ACTIVE:
            self.mappings.add(mapping)
        # for m in self.mappings:
        #    print(f"   # {m}")
        state = self._compute_state()
        if self.state != state:
            # print(f"   # {self.state} -> {state}")
            active_states = [
                MappingState.NORMAL,
                MappingState.TENTATIVELY_REMOVED,
            ]
            if (self.state in active_states) != (state in active_states):
                # print(f"  ## on_signal_mapped {mapping} [")
                # for m in signal.available_mappings:
                #    print(f"   # {m.pad} {m.state}")
                # for p in signal.mapped_pads:
                #    print(f"   # mapped: {p}")
                self.config.on_signal_mapped(
                    signal,
                    (
                        m.pad
                        for m in signal.available_mappings
                        if m.state in active_states
                    ),
                )
                # print(f"  ]")
            self.state = state
            if self.handle is None:
                self.handle = self.config.on_add_mapping(signal, self.pin)
                # print(f"  ## on_add_mapping {mapping} @{self.handle}")
            if self.handle is not None:
                if state == MappingState.NOT_ACTIVE:
                    # print(f"  ## on_remove_mapping {mapping} @{self.handle}")
                    self.config.on_remove_mapping(self.handle)
                else:
                    # print(
                    #   f"  ## on_mapping_state {state} {mapping} @{self.handle}"
                    # )
                    self.config.on_mapping_state(self.handle, state)
        if mapping.state == MappingState.NOT_ACTIVE:
            self.mappings.discard(mapping)

    def _compute_state(self):
        states = [mapping.state for mapping in self.mappings]
        if MappingState.NORMAL in states:
            return MappingState.NORMAL
        removed = MappingState.TENTATIVELY_REMOVED in states
        added = MappingState.TENTATIVELY_ADDED in states
        if removed and added:
            return MappingState.NORMAL
        if removed:
            return MappingState.TENTATIVELY_REMOVED
        if added:
            return MappingState.TENTATIVELY_ADDED
        return MappingState.NOT_ACTIVE
