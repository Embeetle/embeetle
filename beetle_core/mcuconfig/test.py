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
import sys
import os
import textwrap

# Allow relative imports during stand-alone execution
import os

__package__ = __package__ or os.path.basename(os.path.dirname(__file__))
if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from . import *
from .load_json import parameter_selftest, Index


class Label:
    def __init__(self, signal: Signal, pin: Pin):
        self.signal = signal
        self.pin = pin

    def __str__(self):
        return f"{self.signal} on pin {self.pin}"


class MyConfig(Config):

    def __init__(self, part):
        self.active: Set[Label] = set()
        self.todo: Set[Signal] = set()
        self.changed = part.has_unsaved_changes
        super().__init__(part)

    def map(self, signal, pin):
        # print(f"map {signal} to pin {pin} [")
        for mapping in self.part.signal_to_pin_mappings(signal, pin):
            mapping.apply()
            # print("]")
            return
        assert False, f"cannot map {signal} to {pin}"

    def unmap(self, signal, pin):
        # print(f"unmap {signal} from pin {pin} [")
        super().unmap(signal, pin)
        # print("]")

    def on_unsaved_changes(self, changed: bool):
        assert self.changed != changed, changed
        self.changed = changed

    def on_add_mapping(self, signal: Signal, pin: Pin):
        label = Label(signal, pin)
        print(f"config: map {label}")
        self.active.add(label)
        return label

    def on_remove_mapping(self, label: Label):
        print(f"config: unmap {label}")
        if f"{label}" == "SPI1.SCK on pin 30":
            import traceback

            traceback.print_stack()
        assert label in self.active, f"{label}"
        self.active.remove(label)

    def on_mapping_state(self, label: Label, state: MappingState):
        print(f"config: change {label} to {state}")
        assert label in self.active, f"{label} {state}"

    def on_add_unmapped_active_signal(self, signal: Signal):
        print(f"config: add unmapped active signal {signal}")
        assert signal.is_active
        assert not signal.is_mapped
        assert signal not in self.todo
        # assert signal.is_active, signal
        # assert not signal.is_mapped, \
        #    f"{signal} " \
        #    f"enable=({signal.enable_predicate})={signal.is_enabled} " \
        #    f"({signal.peripheral.enable_predicate})="
        #    f"{signal.peripheral.is_enabled}"
        self.todo.add(signal)

    def on_remove_unmapped_active_signal(self, signal: Signal):
        print(f"config: remove unmapped active signal {signal}")
        assert not signal.is_active or signal.is_mapped
        assert signal in self.todo
        self.todo.remove(signal)

    def on_peripheral_enabled(self, peripheral: Peripheral, enabled: bool):
        print(f"config: peripheral {peripheral} enabled={enabled}")

    def on_pad_mode_change(self, pad: Pad):
        print(f"config: pad mode of {pad} changed to {pad.mode}")

    def expect(self, peripheral, signal_pad_pairs):
        expected = {
            (peripheral.signal(sig), self.part.pad(pad).pin)
            for sig, pad in signal_pad_pairs
        }
        actual = {
            (label.signal, label.pin)
            for label in self.active
            if label.signal.peripheral == peripheral
        }

        def map_text(map):
            return "\n".join(
                sorted(f"{signal.full_name} {pin}" for signal, pin in map)
            )

        # print(
        #  f"\nactual:\n{map_text(spi_actual)}\nexpected:\n"
        #  f"{map_text(spi_expected)}"
        # )
        assert actual == expected, (
            f"\nactual:\n{map_text(actual)}\n"
            f"expected:\n{map_text(expected)}"
        )

    def check_todo(self):
        todo = {
            signal
            for peripheral in self.part.peripherals
            for signal in peripheral.signals
            if signal.is_active and not signal.is_mapped
        }
        assert todo == self.todo, (
            f"\n  todo: { ' '.join(str(s) for s in todo)}"
            f"\n  self.todo: { ' '.join(str(s) for s in self.todo)}"
        )


def test0():
    print("\n#### test0 ####")
    part = get("CH32V003F4U6")

    def print_expression(string):
        try:
            expression = part.expression(string)
            print(f"{string} is {expression} ({expression.width})")
        except ExpressionError as error:
            print(f"{string} is invalid: {error}")

    print_expression("AWUCSR")
    print_expression("AWUCSR[10:4]")
    print_expression("AWUEN")
    # Note: the WCH SVD incorrectly sets the IPRIORx register size to 8 and does
    # not specify the four bit fields in each of these registers.
    print_expression("IPRIOR1")
    print_expression("IPRIOR1[3:1]")
    print_expression("STATR_MODE")
    print_expression("PLS")
    print_expression("FOOBAR")


def test1(part: Part):
    print("\n#### test1 ####")
    print(f"Peripherals for part {part}:")
    for peripheral in part.peripherals:
        print(f"  {peripheral.name}: {peripheral.description}")
    print()
    for peripheral in part.peripherals:
        print(
            f"  {peripheral.name}: "
            f"{format_list([s.name for s in peripheral.signals])}"
        )


def test2(part: Part):
    print(f"\n#### test2 #### ({part})")
    part.reset()
    print(f"Pads: {format_list([pad.name for pad in part.pads])}")
    pins = {pad.pin for pad in part.pads}
    print(f"Pins: {format_list([pin.name for pin in part.pins])}")
    for pin in pins:
        pads = part.pads_for_pin(pin)
        signals = {signal for pad in pads for signal in pad.possible_signals}
        print(f"{pin}: {format_list(part.signals_for_pin(pin))}")

    print(f"Peripherals for {part}:")
    for peripheral in part.peripherals:
        print(f"  {peripheral}:")
        for setting in peripheral.settings:
            print(f"    setting {setting}")
            if setting.description:
                print(
                    "\n".join(
                        textwrap.wrap(
                            setting.description,
                            initial_indent="      ",
                            subsequent_indent="      ",
                        )
                    )
                )
        for signal in peripheral.signals:
            if signal.is_available_for_part(part):
                pins = format_list(
                    sorted(signal.possible_pins, key=lambda x: x.name)
                )
                assert pins
                print(f"    {signal.name}: {pins}")


def test3(part):
    print(f"\n#### test3 #### ({part})")
    part.reset()
    config = Config(part)

    print(f"Peripherals with signals for {part.name}:")
    for peripheral in part.peripherals:
        if peripheral.signals:
            print(f"  {peripheral}:")
            print(
                f"    enable='{peripheral.enable_predicate}'"
                f" = {config.is_peripheral_enabled(peripheral)}"
            )
            for setting in peripheral.settings:
                print(f"    setting {setting}")
            for signal in peripheral.signals:
                if signal.is_available_for_part(part):
                    try:
                        enabled = config.is_signal_enabled(signal)
                    except ExpressionError as error:
                        print(f"error: {error}")
                        sys.exit(1)
                        enabled = f"error: {error}"
                    pins = sorted(signal.possible_pins, key=lambda x: x.name)
                    pins_string = " ".join(
                        (
                            f"+{pin}+"
                            if config.is_active_pin_for_signal(signal, pin)
                            else f"{pin}"
                        )
                        for pin in pins
                    )
                    pads_string = " ".join(
                        sorted(
                            [
                                pad.name
                                for pad in config.active_pads_for_signal(signal)
                            ]
                        )
                    )
                    print(
                        f"    {signal.name}: {pins_string}"
                        f" {pads_string}"
                        f" enable='{signal.enable_predicate}'"
                        f" => {enabled}"
                    )
                    for pin in pins:
                        predicate = signal.predicate_for_pin(pin, part)
                        print(
                            f"      on pin {pin} when '{predicate}'"
                            f" => {config.value(predicate)}"
                        )
                else:
                    print(f"    {signal.name}: not available (no pins)")
    config.drop()


def test4():
    part = get("CH32V003F4U6")
    print(f"\n#### test4 #### ({part})")
    part.reset()
    config = Config(part)

    print("remapping OPA.P from pin 3 to pin 1 ...")
    opa = part.peripheral("OPA")
    assert opa
    pos = opa.signal("P")
    assert pos
    assert_equal(pos.possible_pins, pin_set(part, [1, 3]))
    assert_equal(config.active_pins_for_signal(pos), pin_set(part, []))
    opa.enable()
    assert_equal(config.active_pins_for_signal(pos), pin_set(part, [3]))
    assert_equal(config.value("OPAPSEL"), 0)
    config.assign("OPAPSEL", 1)
    assert_equal(config.value("OPAPSEL"), 1)
    assert_equal(config.active_pins_for_signal(pos), pin_set(part, [1]))
    print("remapping OPA.P works correctly")
    print("remove config")
    config.drop()


def test5(part):
    print(f"\n#### test5 #### ({part})")
    part.reset()
    config = Config(part)
    for pin in part.pins:
        print(f"  pin {pin} has {len(list(part.pin_mappings(pin)))} options")
        for mapping in part.pin_mappings(pin):
            print(
                f"    option: {mapping} active={mapping.is_active}"
                f" ({mapping.signal.peripheral} enabled ="
                f" {config.is_peripheral_enabled(mapping.signal.peripheral)})"
            )
            # print(f"tentatively apply {mapping} [")
            assert not config.tentative_changes_active
            config.begin_tentative_changes()
            assert config.tentative_changes_active
            mapping.apply()
            config.rollback_tentative_changes()
            assert not config.tentative_changes_active
            # print("] rolled back")
    config.drop()


def test6():
    print(f"\n#### test6 ####")
    part = get("CH32V003F4U6")
    part.reset()
    for mode in part.pad_modes:
        print(f"mode {mode}: {mode.desc}")
    for pad in part.pads:
        mode_names = " ".join(mode.name for mode in pad.possible_modes)
        print(f"pad {pad} type {pad.type} modes {mode_names}")


def test7(part):
    print(f"\n#### test7 #### ({part})")
    part.reset()
    config = Config(part)
    print(f"Modes for signals:")
    for peripheral in part.peripherals:
        if peripheral.signals:
            print(f"  {peripheral}:")
            for signal in peripheral.signals:
                if signal.is_available_for_part(part):
                    pad_mode_names = " ".join(
                        sorted(
                            [
                                mode.name
                                for mode in config.modes_for_signal_pads(signal)
                            ]
                        )
                    )
                    mode_names = " ".join(
                        sorted([mode.name for mode in signal.possible_modes])
                    )
                    print(
                        f"    {signal}: {pad_mode_names} "
                        f"choose: {mode_names}"
                    )
                else:
                    print(f"    {signal} is not available for {part}")
    config.drop()


def test8():
    print(f"\n#### test8 ####")
    part = get("CH32V003J4M6")
    part.reset()
    config = Config(part)

    tim1 = part.peripheral("TIM1")
    assert tim1
    ch4 = tim1.signal("CH4")
    assert ch4
    print(f"mode options for {ch4}:")
    for mode in ch4.possible_modes:
        print(f"  {mode} when {ch4.mode_predicate(mode)}")
    mode_names = {mode.name for mode in ch4.compatible_modes}
    print(f"CH4 modes for current config of TIM1: {' '.join(mode_names)}")
    assert mode_names == {"PP-AF"}, mode_names
    print(f"set TIM1.CC4S to 0b11")
    config.assign("TIM1.CC4S", 0b11)
    assert config.value("TIM1.CC4S") == 0b11, config.value("TIM1.CC4S")
    mode_names = {mode.name for mode in ch4.compatible_modes}
    print(f"CH4 modes for current config of TIM1: {' '.join(mode_names)}")
    assert mode_names == {"FI"}
    print("modes for TIM1.CC4S react correctly to config changes")
    config.drop()


def names(items):
    return " ".join(item.name for item in items)


def test10():
    print(f"\n#### test10 ####")
    # Create and save an index
    part_index.save("/tmp/config-index.json")
    # Load an index
    index = Index()
    index.load("/tmp/config-index.json")
    assert index._map == part_index._map


def test11(part):
    print(f"\n#### test11 #### ({part})")
    part.reset()

    config = MyConfig(part)
    spi1 = part.peripheral("SPI1")
    print(f"enable {spi1.name} {spi1.enable_predicate}")
    spi1.set_enabled(True)

    pin = part.pin("14")
    print(f"options for pin {pin} ({names(part.pads_for_pin(pin))}):")
    mappings = part.sorted_pin_mappings(pin)
    for index, mapping in enumerate(mappings):
        print(
            f"  option {index}: {mapping.signal} -> {mapping.pad}"
            f" when {mapping.predicate} ({mapping.predicate.value})"
        )
    option_nr = 1
    option = mappings[option_nr]
    print(f"\ntry option {option_nr} {option.predicate}")
    config.expect(
        spi1,
        [
            ("SCK", "PC5"),
            ("MISO", "PC7"),
            ("MOSI", "PC6"),
        ],
    )

    print("apply tentatively")
    config.begin_tentative_changes()
    config.apply_mapping(option)
    print("rollback")
    config.rollback_tentative_changes()
    print("apply tentatively")
    config.begin_tentative_changes()
    config.apply_mapping(option)
    print("commit")
    config.commit_tentative_changes()
    config.expect(
        spi1,
        [
            ("SCK", "PC5"),
            ("MISO", "PC7"),
            ("MOSI", "PC6"),
        ],
    )
    pa1 = part.pad("PA1")
    GPIO = part.peripheral("GPIO")
    assert GPIO
    gpio_pa1 = GPIO.add_signal("pa1")
    print(f"change mode of {pa1} (currently {pa1.mode})")
    expression.trace = True
    for mode in pa1.possible_modes:
        print(f"try mode {mode} {pa1.mode_predicate(mode)}")
        pa1.set_mode(mode)
        assert pa1.mode == mode, pa1.mode
    config.drop()


def test12(part):
    print(f"\n#### test12 #### ({part})")
    part.reset()
    config = MyConfig(part)
    for peri in part.peripherals:
        if peri.can_be_disabled:
            print(f"{peri.name} enabled is {peri.is_enabled}")
            print(f"enable {peri.name}")
            peri.set_enabled(True)
            print(f"disable {peri.name}")
            peri.set_enabled(False)
        else:
            print(f"{peri.name} cannot be disabled")
            assert peri.is_enabled, peri
    config.drop()


def test13():
    print(f"\n#### test13 #### (power pins)")
    for part in [get("CH32V003F4U6"), get("APM32F411VET6")]:
        part.reset()
        print(f"Power pins for part {part} package {part.package}:")
        config = Config(part)
        for pin in part.pins:
            if config.is_power_pin(pin):
                pad_names = " ".join(pad.name for pad in part.pads_for_pin(pin))
                print(f"  {pin} {pad_names}")
        config.drop()


def test14():
    part = get("CH32V003A4M6")
    print(f"\n#### test14 #### ({part})")
    part.reset()
    pin = part.pin("1")
    print(f"options for pin {pin} ({names(part.pads_for_pin(pin))}):")
    mappings = part.sorted_pin_mappings(pin)
    for index, mapping in enumerate(mappings):
        print(
            f"  option {index}: {mapping.signal} -> {mapping.pad}"
            f" when {mapping.predicate} ({mapping.predicate.value})"
        )
    for option_nr in [0, 1, 0]:
        mapping = mappings[option_nr]
        print(f"\napply option {option_nr}")
        mapping.apply()
        assert mapping.pad in mapping.signal.mapped_pads


def test15(part):
    print(f"\n#### test15 #### ({part}) GPIO")
    part.reset()
    config = MyConfig(part)
    GPIO = part.peripheral("GPIO")
    assert GPIO
    assert GPIO.is_configurable
    assert GPIO in part.peripherals
    print("add signal:")
    assert not GPIO.signal("foo")
    foo = GPIO.add_signal("foo", "foo is not bar")
    assert GPIO.signal("foo") == foo
    print(f"configurable peripherals:")
    for peri in part.peripherals:
        if peri.is_configurable:
            print(f"  {peri}:")
            for setting in peri.settings:
                print(f"    setting: {setting}: {setting.label}")
            for signal in peri.signals:
                print(f"    signal: {signal}")

    print(f"other peripherals:")
    for peri in part.peripherals:
        if not peri.is_configurable:
            print(f"  {peri}")

    print("rename signal:")
    foo.name = "bar"
    foo.description = "bar is not foo"
    assert foo.name == "bar"
    assert foo.description == "bar is not foo"
    assert GPIO.signal("foo") is None
    assert GPIO.signal("bar") is foo
    foo.name = "foo"
    assert foo.name == "foo"
    assert GPIO.signal("foo") is foo
    assert GPIO.signal("bar") is None

    print("remove signal:")
    assert GPIO.signal("foo") == foo
    GPIO.remove_signal(foo)
    assert not GPIO.signal("foo")
    assert GPIO.is_configurable
    assert GPIO in part.peripherals
    for signal in GPIO.signals:
        assert False, f"unexpected GPIO signal {signal}"

    config.drop()


def test16():
    part = get("CH32V003A4M6")
    print(f"\n#### test16 #### ({part})")
    part.reset()

    spi1 = part.peripheral("SPI1")
    available = spi1 is not None
    print(f"testing {spi1} available={available}")
    assert not available

    i2c1 = part.peripheral("I2C1")
    print(f"testing {i2c1} available={i2c1 is not None}")
    assert not i2c1.is_enabled, i2c1.enable_predicate
    pin = part.pin("1")
    print(f"mappings for pin {pin}:")
    for mapping in part.sorted_pin_mappings(pin):
        print(f"  mapping: {mapping}")
    mapping = part.sorted_pin_mappings(pin)[0]
    print(f"map {mapping.signal} to {mapping.pad} (pin {mapping.pin})")
    mapping.apply()
    assert i2c1.is_enabled
    i2c1.auto_map_enabled_signals()
    for signal in i2c1.signals:
        active = list(signal.active_mappings)
        print(
            f" {signal} enabled={signal.is_enabled} "
            f"active mappings: "
            f"{' '.join(str(mapping.pin) for mapping in active)}"
        )
        if signal.is_enabled:
            assert active
    assert mapping.pad.is_mapped
    mapping.withdraw()
    assert not mapping.pad.is_mapped

    print("try mapping custom gpio signal")
    GPIO = part.peripheral("GPIO")
    assert GPIO
    foo = GPIO.add_signal("foo", "foo is not bar")
    # Custom signals are not auto-mapped
    assert not foo.is_mapped
    foo.auto_map()
    assert foo.is_mapped
    print(
        f"{foo} auto-mapped to "
        f"{' '.join(str(m.pad) for m in foo.active_mappings)}"
    )
    foo.unmap()
    assert not foo.is_mapped
    print(f"{foo} is unmapped")
    for foo_mapping in foo.mappings_for_part(part):
        print(f"try to apply mapping of {foo} to {foo_mapping.pad}")
        # for mapping in foo.active_mappings:
        #    print(f"  {foo} is mapped to {mapping.pad}")
        assert not foo.is_mapped
        foo_mapping.apply()
        assert foo.is_mapped
        # print(f"try to withdraw mapping of {foo} to {foo_mapping.pad}")
        foo_mapping.withdraw()
        assert not foo.is_mapped
        # print(f"try to re-apply mapping of {foo} to {foo_mapping.pad}")
        foo_mapping.apply()
        assert foo.is_mapped
        # print(f"try to unmap {foo} to pin {part.pin_for_pad(foo_mapping.pad)}")
        part.unmap(foo, foo_mapping.pin)
        assert not foo.is_mapped
    print(f"try to auto-map {foo}")
    part.begin_tentative_changes()
    foo.auto_map()
    assert foo.is_mapped
    part.rollback_tentative_changes()
    assert not foo.is_mapped
    part.begin_tentative_changes()
    foo.auto_map()
    assert foo.is_mapped
    part.commit_tentative_changes()
    assert foo.is_mapped
    for mapping in foo.active_mappings:
        print(f"auto-mapped {foo} to {mapping.pad}")


def test17(part):
    print(f"\n#### test17 #### ({part})")
    part.reset()
    config = MyConfig(part)
    i2c = part.peripheral("I2C1")
    print(f"before: {i2c} enabled={i2c.is_enabled}")
    i2c.enable()
    print(f"after: {i2c} enabled={i2c.is_enabled}")
    config.drop()


def test18():
    part = get("CH32V003A4M6")
    print(f"\n#### test18 #### ({part})")
    part.reset()
    config = MyConfig(part)
    bkin = part.peripheral("TIM1").signal("BKIN")
    pin = part.pin("1")
    for mapping in part.signal_to_pin_mappings(bkin, pin):
        print(f"apply {mapping}")
        mapping.apply()
        assert mapping.pad.is_mapped
        print(f"unmap pad {mapping.pad}")
        mapping.pad.unmap()
        assert not mapping.pad.is_mapped
    config.drop()


def test19():
    part = get("CH32V003A4M6")
    print(f"\n#### test19 #### ({part}) TIMx.CH2 on PC7")
    part.reset()
    config = MyConfig(part)
    PC7 = part.pad("PC7")
    assert PC7.pin == part.pin("6")

    # spill over from test16.
    GPIO = part.peripheral("GPIO")
    foo = GPIO.signal("foo")
    assert foo
    print(f"{foo} mapped={foo.is_mapped} active={foo.is_active}")
    config.check_todo()
    config.unmap(foo, PC7.pin)

    tim1_ch2 = part.peripheral("TIM1").signal("CH2")
    tim2_ch2 = part.peripheral("TIM2").signal("CH2")
    assert (
        not PC7.is_mapped
    ), f"PC7 mapped to {' '.join(str(m.signal) for m in PC7.active_mappings)}"
    assert not tim1_ch2.is_mapped
    assert not tim2_ch2.is_mapped

    config.map(tim1_ch2, PC7.pin)
    config.check_todo()
    assert PC7.is_mapped
    assert tim1_ch2.is_mapped
    assert not tim2_ch2.is_mapped
    config.map(tim2_ch2, PC7.pin)
    config.check_todo()
    assert PC7.is_mapped
    assert tim1_ch2.is_mapped
    assert tim2_ch2.is_mapped
    config.unmap(tim2_ch2, PC7.pin)
    config.check_todo()
    assert PC7.is_mapped
    assert tim1_ch2.is_mapped
    assert not tim2_ch2.is_mapped
    config.unmap(tim1_ch2, PC7.pin)
    config.check_todo()
    assert not PC7.is_mapped
    assert not tim1_ch2.is_mapped
    assert not tim2_ch2.is_mapped
    config.drop()


def test20():
    part = get("APM32F411VET6")
    print(f"\n#### test20 #### ({part})")
    part.reset()
    config = MyConfig(part)
    print("Pads:")
    for pad in part.pads:
        print(
            f"  {pad}: {pad.type} "
            f"pin {' '.join(str(p) for p in part.pins_for_pad(pad))} "
            f"(mode {' '.join(str(mode) for mode in pad.possible_modes)})"
        )
    print("Peripherals:")
    for peripheral in part.series.peripherals:
        print(f"  {peripheral}")
    config.drop()


def test21(part: Part):
    print(f"\n#### test21 #### ({part})")
    part.reset()
    for pin in part.pins:
        if len(list(pin.pads)) > 1:
            print(f"More than one pad: {pin} = {format_list(pin.pads)}")

            def report_modes():
                for pad in pin.pads:
                    print(f"  {pad} mode {pad.mode}")
                print(f"  `-> pin mode: {pin.mode}")

            report_modes()
            pin.pads[0].set_mode(model.PP)
            report_modes()
            pin.pads[1].set_mode(model.PP)
            report_modes()


def test22(part: Part):
    print(f"\n#### test22 #### ({part})")
    part.reset()
    config = MyConfig(part)
    print("Clocks:")
    for clock in part.series.clocks:
        print(
            f"  {clock}: "
            f" ({clock.layout.x},{clock.layout.y})"
            f" dots=[{','.join(str(dot) for dot in clock.layout.dots)}]"
            f" tags=[{','.join(str(tag) for tag in clock.layout.tags)}]"
        )
        for route in clock.layout.routes:
            print(f"    {','.join(str(p) for p in route)}")
    config.drop()


def test23():
    part = get("APM32F411VET6")
    print(f"\n#### test23 #### ({part})  initial mappings")
    part.reset()
    config = MyConfig(part)
    labels = {str(label) for label in config.active}
    assert labels == {
        "DBGMCU.JTRST on pin 90",
        "DBGMCU.JTCK_SWCLK on pin 76",
        "DBGMCU.JTMS_SWDIO on pin 72",
        "DBGMCU.JTDI on pin 77",
        "DBGMCU.JTDO_SWO on pin 89",
    }, f"unexpected initial labels {labels}"
    todos = {str(signal) for signal in config.todo}
    assert not todos, f"unexpected initial todos {todos}"
    config.drop()


def test24():
    part = get("APM32F411VET6")
    print(f"\n#### test24 #### ({part})  change SPI1 mode")
    part.reset()
    config = MyConfig(part)
    print("config loaded")
    SPI1 = part.peripheral("SPI1")
    role = SPI1.setting("Role")
    print(f"{role}: {role.current}")
    role_value = role.value
    SCK = SPI1.signal("SCK")
    MISO = SPI1.signal("MISO")
    MOSI = SPI1.signal("MOSI")
    NSS = SPI1.signal("NSS")
    SCK_pad = part.pad("PA5")
    MISO_pad = part.pad("PA6")
    MOSI_pad = part.pad("PA7")
    NSS_pad = part.pad("PA4")
    print(f"enable {SPI1} [")
    SPI1.enable()
    print(f"]")
    assert role.value == role_value
    assert SCK.is_mapped_to_pad(SCK_pad)
    assert MISO.is_mapped_to_pad(MISO_pad)
    assert MOSI.is_mapped_to_pad(MOSI_pad)
    assert NSS.is_mapped_to_pad(NSS_pad)
    assert SCK_pad.mode == FI
    assert MISO_pad.mode == PP_AF
    assert MOSI_pad.mode == FI
    assert NSS_pad.mode == FI

    print(f"select master mode [")
    role = SPI1.setting("Role")
    assert role.value == 0
    role.select(1)
    print(f"]")
    assert SCK.is_mapped_to_pad(SCK_pad)
    assert MISO.is_mapped_to_pad(MISO_pad)
    assert MOSI.is_mapped_to_pad(MOSI_pad)
    assert SCK_pad.mode == PP_AF
    assert MISO_pad.mode == FI
    assert MOSI_pad.mode == PP_AF
    assert not NSS.is_mapped
    assert not NSS_pad.is_mapped
    assert not NSS in config.todo

    print(f"enable NSS output in master mode [")
    nss_output_enable = SPI1.setting("NSS output enable")
    assert nss_output_enable.value == 0
    nss_output_enable.select(1)
    print(f"]")

    # TODO fix remaining tests
    if True:
        assert NSS.is_mapped_to_pad(NSS_pad)
        assert NSS_pad.mode == PP_AF, NSS_pad.mode

        print(f"set {NSS_pad} to FI mode [")
        NSS_pad.set_mode(FI)
        print(f"] set {NSS_pad} to FI mode")
        assert not NSS.is_mapped
        assert NSS in config.todo
    config.drop()


def test25():
    part = get("APM32F411VET6")
    print(f"\n#### test25 #### ({part})  save/load")
    part.reset()
    part.reset_unsaved_changes_flag()
    assert not part.series.has_unsaved_changes
    config = MyConfig(part)
    print("config loaded")
    assert not config.has_unsaved_changes
    assert not config.changed
    oricfg = config.get_data()
    print(f"original configuration: {oricfg}")
    config.set_data(oricfg)
    assert not config.has_unsaved_changes
    assert not config.changed
    GPIO = part.peripheral("GPIO")
    mysig = GPIO.add_signal("mysig")
    assert config.has_unsaved_changes
    assert config.changed
    assert not mysig.is_mapped
    mysig.auto_map()
    assert mysig.is_mapped
    assert mysig.pad
    print(f"{mysig} mapped to {mysig.pad} (pin {mysig.pad.pin})")
    mysig.map_to_pad(part.pad("PE2"))
    mysig_pad = mysig.pad
    SPI2 = part.peripheral("SPI2")
    SPI2.enable()
    assert config.has_unsaved_changes
    assert config.changed
    newcfg = config.get_data()
    assert not config.has_unsaved_changes
    assert not config.changed
    part.reset()
    assert not mysig.pad
    assert not SPI2.is_enabled
    assert config.has_unsaved_changes
    assert config.changed
    config.set_data(newcfg)
    assert not config.has_unsaved_changes
    assert not config.changed
    print(config.get_data())
    assert mysig.pad == mysig_pad
    assert SPI2.is_enabled
    config.drop()


def test26():
    part = get("APM32F411VET6")
    print(f"\n#### test26 #### ({part})  signal mode")
    part.reset()
    config = MyConfig(part)
    print("config loaded")
    USART1 = part.peripheral("USART1")
    assert USART1
    USART1.enable()
    RX = USART1.signal("RX")
    assert RX
    print(f"{RX} mode={RX.mode}")
    for pad in RX.mapped_pads:
        print(f"{RX} mapped to {pad} mode={pad.mode}")
        assert pad.mode is RX.mode
    RX.mode = PU
    for pad in RX.mapped_pads:
        print(f"{RX} mapped to {pad} mode={pad.mode}")
        assert pad.mode is RX.mode

    SPI1 = part.peripheral("SPI1")
    MISO = SPI1.signal("MISO")
    role = SPI1.setting("Role")
    assert role.value == 0  # slave mode
    assert MISO.mode is PP_AF
    role.select(1)
    assert MISO.mode is FI
    config.drop()


def test27():
    part = get("APM32F411VET6")
    print(f"\n#### test27 #### ({part})  baud rate")
    part.reset()
    part.reset_unsaved_changes_flag()
    assert not part.series.has_unsaved_changes
    config = MyConfig(part)
    USART1 = part.peripheral("USART1")
    baud_rate = USART1.setting("Baud rate")
    assert baud_rate.value == 0
    baud_rate.select(115200)
    print(f"Achieved baud rate: {baud_rate.value}")
    config.drop()


def test28():
    part = get("APM32F411VET6")
    print(f"\n#### test28 #### ({part})  EVENTOUT")
    part.reset()
    part.reset_unsaved_changes_flag()
    assert not part.series.has_unsaved_changes
    Core = part.peripheral("Core")
    EVENTOUT = Core.signal("EVENTOUT")
    PC4 = part.pad("PC4")
    PE2 = part.pad("PE2")
    Enable_EVENTOUT = Core.setting("Enable EVENTOUT")

    def check_EVENTOUT_enabled(enabled: bool):
        print(f"{EVENTOUT} enabled={EVENTOUT.is_enabled}")
        print(f"{EVENTOUT} active mappings:")
        for mapping in EVENTOUT.active_mappings:
            print(f"  {mapping}")
        assert EVENTOUT.is_enabled == enabled

    class SpecialConfig(MyConfig):
        def on_remove_mapping(self, label: Label):
            label.signal.unmap()
            label.signal.map_to_pad(PC4)
            label.signal.unmap()
            label.signal.map_to_pad(PC4)
            print(
                f"remove mapping for {label.signal}"
                f" enabled={label.signal.is_enabled}"
            )
            Enable_EVENTOUT.select(False)
            super().on_remove_mapping(label)

    config = SpecialConfig(part)
    saved_data = {
        "register-values": {
            "GPIOA.ALFH": 30576,
            "GPIOA.MODE": 2819227648,
            "GPIOC.ALFL": 983040,
            "GPIOC.MODE": 512,
            "GPIOD.MODE": 524290,
            "RCM.AHB1CLKEN": 13,
            "RCM.AHB2CLKEN": 64,
            "RCM.BDCTRL": 256,
            "RCM.CTRL": 65664,
            "RCM.PLL1CFG": 608186384,
            "USART1.BR": 868,
            "USART1.CTRL1": 9740,
            "USART1.CTRL3": 512,
            "USART2.CTRL1": 12,
            "USART3.CTRL1": 12,
            "USART6.CTRL1": 12,
        },
        "custom-signals": [],
        "nominal-values": [
            {"peripheral": "USART1", "setting": "Baud rate", "value": 115200}
        ],
    }
    config.set_data(saved_data)
    check_EVENTOUT_enabled(True)
    assert EVENTOUT.is_mapped_to(PC4)
    assert not EVENTOUT.is_mapped_to(PE2)
    config.begin_tentative_changes()
    EVENTOUT.map_to_pad(PE2)
    check_EVENTOUT_enabled(True)
    assert not EVENTOUT.is_mapped_to(PC4)
    assert EVENTOUT.is_mapped_to(PE2)
    config.rollback_tentative_changes()
    check_EVENTOUT_enabled(True)
    assert EVENTOUT.is_mapped_to(PC4)
    assert not EVENTOUT.is_mapped_to(PE2)
    config.drop()


def assert_equal(value, expect):
    assert value == expect, f"got {value} instead of {expect}"


def pin_set(part: Part, pin_nrs: Iterable[int]):
    return {part.pin(str(pin_nr)) for pin_nr in pin_nrs}


part_index = Index()
root = f"{os.path.dirname(__file__)}/resources/series"
part_index.add_file(f"{root}/CH32V003/CH32V00xxx.json5")
part_index.add_file(f"{root}/APM32F411/chip_config.json5")


def load_part(part_name: str) -> Part:
    print(f"load {part_name}")
    show_traceback = True
    if show_traceback:
        part = part_index.load_part(part_name)
    else:
        try:
            part = part_index.load_part(part_name)
        except ConfigError as error:
            print(f"error: {error}")
            sys.exit(1)
    return part


def format_list(xs):
    return " ".join([str(x) for x in xs])


def names(xs):
    return " ".join([x.name for x in xs])


parts = {}


def get(part_name):
    part = parts.get(part_name)
    if part:
        return part
    part = load_part(part_name)
    parts[part_name] = part
    return part


# test11(get('CH32V003F4U6'))
# test15(get('CH32V003A4M6'))
# test22(get('APM32F411VET6'))
# test24()
# test25()
# test27()
# test28()
# sys.exit(0)

parameter_selftest()
expression.selftest()
get("APM32F411VET6")
test0()
test1(get("CH32V003F4P6"))
test2(get("CH32V003F4P6"))
test2(get("CH32V003J4M6"))
test3(get("CH32V003J4M6"))
test3(get("CH32V003F4U6"))
test4()
test5(get("CH32V003F4P6"))
test5(get("CH32V003J4M6"))
test6()
test7(get("CH32V003J4M6"))
test7(get("CH32V003F4U6"))
test8()
test10()
test11(get("CH32V003F4U6"))
test12(get("CH32V003F4U6"))
test13()
test14()
test15(get("CH32V003A4M6"))
test15(get("CH32V003F4P6"))
test16()
test17(get("CH32V003A4M6"))
test18()
test19()
test20()
test21(get("CH32V003J4M6"))
test22(get("APM32F411VET6"))
test23()
test24()
test25()
test26()
test27()
test28()
