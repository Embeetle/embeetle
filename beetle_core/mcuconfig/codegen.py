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

# Allow relative imports during stand-alone execution
import os

__package__ = __package__ or os.path.basename(os.path.dirname(__file__))
if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .model import *


def generate_code(part: Part, folder: str):
    print(f"generate code at {folder}")
    CodeGen(part, folder)


class CodeGen:
    def __init__(self, part: Part, folder: str):
        self.indent: str = "    "
        self.prefix: str = ""
        self.pending_intro: str = ""
        self.done: set[Field] = set()
        self.folder = folder
        self.generate_header()
        with open(f"{folder}/system_init.c", "w") as file:
            self.file = file
            self.generate_code(part)

    def generate_header(self):
        with open(f"{self.folder}/system_init.h", "w") as file:
            file.write(
                "/* Generated file - do not edit */\n"
                "\n"
                "void system_init(void);\n"
            )

    def generate_code(self, part: Part):
        self.write(
            "/* Generated file - do not edit */\n"
            "\n"
            '#include "system_init.h"\n'
            '#include "registers.h"\n'
            "\n"
            "void system_init(void)\n"
            "{"
        )
        self.inc_indent()
        self.init_clocks(part)
        self.enable_pads(part)
        self.init_peripherals(part)
        self.unmap_peripherals(part)
        self.dec_indent()
        self.write("}")

    def init_clocks(self, part: Part):
        target_clocks = {
            # Clocks driving a peripheral
            clock
            for clock in part.clocks
            if clock.drives_peripherals
        } | {
            # Output clocks
            clock
            for clock in part.clocks
            if clock.output_signal
        }

        enabled: {Clock} = set()

        def enable(clock: Clock):
            nonlocal enabled
            if clock in enabled:
                return
            enabled.add(clock)
            if type(clock) is MuxClock:
                current = clock.current
                if current:
                    enable(current)
            else:
                for c in clock.inputs:
                    enable(c)
            # print(f"enable {clock}")

        for clock in target_clocks:
            enable(clock)
        for clock in part.clocks:
            self.init_clock(clock)

    def init_clock(self, clock: Clock):
        with self.intro_comment(f"\n{clock}: {clock.description}"):
            if type(clock) is InternalClock:
                pass
            elif type(clock) is ExternalClock:
                self.init_expression(clock.bypass_predicate)
            elif type(clock) is MuxClock:
                with self.intro_comment(f"use {clock.current}"):
                    self.init_expression(clock.selector)
            elif type(clock) is MultipliedClock:
                pass
            elif type(clock) is DividedClock:
                pass
            self.init_expression(clock.enable_predicate)
            if (
                clock.is_enabled
                and not clock.is_enabled_after_reset
                and not clock.ready_predicate.is_always_true
            ):
                self.write(f"while (!{_field_expr(clock.ready_predicate)});")

    def enable_pads(self, part: Part):
        with self.intro_comment("\nEnable GPIO ports:"):
            pads = (
                mapping.pad
                for peripheral in part.peripherals
                if peripheral.is_enabled
                for signal in peripheral.enabled_signals
                if signal.requires_enabled_pad
                for mapping in signal.active_mappings
            )
            for pad in sorted(pads, key=lambda pad: pad.name):
                self.init_expression(pad.enable_predicate)

    def init_peripherals(self, part: Part):
        for peripheral in sorted(part.peripherals, key=lambda p: p.name):
            if peripheral.is_enabled:
                self.init_peripheral(peripheral)

    def init_peripheral(self, peripheral: Peripheral):
        with self.intro_comment(f"\n{peripheral}: {peripheral.description}"):
            with self.intro_comment(f"Enable {peripheral} peripheral clock"):
                self.init_expression(peripheral.clock_enable_predicate)
            # Map signals before emitting settings, so that the mapping is
            # documented even when the enable expression is identical to the
            # mapped expression (e.g. permanently enabled signals such as
            # EVENTOUT).
            for signal in peripheral.enabled_signals:
                self.init_signal(signal)
            for setting in peripheral.settings:
                self.init_setting(setting)
            with self.intro_comment(f"Enable {peripheral} peripheral"):
                self.init_expression(peripheral.peripheral_enable_predicate)

    def unmap_peripherals(self, part: Part):
        for peripheral in part.peripherals:
            if peripheral.is_enabled:
                with self.intro_comment(f"\n{peripheral}:"):
                    for signal in peripheral.signals:
                        if (
                            signal.is_enabled_after_reset
                            and not signal.is_enabled
                        ):
                            with self.intro_comment(f"disable {signal}"):
                                self.init_expression(signal.enable_predicate)

    def init_setting(self, setting: Setting):
        if not setting.is_at_reset_value:
            value = setting.current
            if setting.effective_value != setting.nominal_value:
                value += f" ({setting.effective_value} effective)"
            with self.intro_comment(f"{setting.label} = {value}"):
                self.init_expression(setting.selector)

    def init_signal(self, signal: Signal):
        for mapping in signal.active_mappings:
            self.init_active_mapping(mapping)
        with self.intro_comment(
            f"{'En' if signal.is_enabled else 'Dis'}able {signal.name}"
        ):
            self.init_expression(signal.enable_predicate)

    def init_active_mapping(self, mapping: Mapping):
        with self.intro_comment(
            f"{mapping.signal} on {mapping.pad} (pin {mapping.pin})"
            f" mode {mapping.pad.mode}"
        ):
            self.init_mapping(mapping)

    def init_mapping(self, mapping: Mapping):
        self.init_expression(mapping.predicate)
        self.init_expression(mapping.mode_predicate)

    def init_expression(self, expression: Expression):
        # Assume that symbols in expression are all fields
        for symbol in sorted(expression.relevant_symbols, key=lambda x: x.name):
            # Expressions can contain virtual selectors as well as fields.
            if isinstance(symbol, Field):
                self.init_field(symbol)

    def init_field(self, field: Field):
        if not field in self.done and field.value != field.reset_value:
            self.done.add(field)
            self.write(f"{_field_expr(field)} = {_field_value(field)};")

    def comment(self, text):
        prefix = self.prefix
        self.prefix = prefix + "// "
        self.write(text)
        self.prefix = prefix

    def inc_indent(self):
        self.prefix += self.indent

    def dec_indent(self):
        self.prefix = self.prefix[: -len(self.indent)]

    def intro_comment(self, text: str):
        return self.intro(_indent("// ", text))

    def intro(self, text: str):
        return self.Intro(self, text)

    class Intro:
        def __init__(self, codegen, text: str):
            self.codegen = codegen
            self.text = text

        def __enter__(self):
            self.codegen.pending_intro += self.text

        def __exit__(self, *args):
            if self.codegen.pending_intro:
                self.codegen.pending_intro = self.codegen.pending_intro[
                    : -len(self.text)
                ]

    def write(self, code: str):
        self.file.write(_indent(self.prefix, self.pending_intro + code))
        self.pending_intro = ""


def _field_expr(field: Field) -> str:
    return f"{field.register.scope}_{field.register.name}bits.{field.name}"


def _field_value(field: Field) -> str:
    return f"{_binary(field.value, field.width)}"


def _binary(value: int, width: int) -> str:
    return f"0b{value:0{width}b}"


def _indent(prefix: str, text: str) -> str:
    return (prefix + text.replace("\n", "\n" + prefix) + "\n").replace(
        prefix + "\n", "\n"
    )


if __name__ == "__main__":
    from load_json import load_part
    from .config import *

    def test(project_path: str, part_name: str):
        chip_config_json = f"{project_path}/.beetle/chip_config.json5"
        part = load_part(chip_config_json, part_name)
        print(f"\nGenerate code for {part_name} in {project_path}")
        part.reset()
        USART1 = part.peripheral("USART1")
        USART1.enable()
        USART1.setting("Baud rate").select(115200)
        SPI2 = part.peripheral("SPI2")
        SPI2.enable()
        SPI2.setting("Role").select(1)
        GPIO = part.peripheral("GPIO")
        LED3 = GPIO.add_signal("LED3")
        PE5 = part.pad("PE5")
        LED3.map_to_pad(PE5)
        PE5.set_mode(PP)
        HSECLK = part.clock("HSECLK")
        assert not HSECLK.is_enabled
        HSECLK.enable()
        assert HSECLK.is_enabled
        HSICLK = part.clock("HSICLK")
        assert HSICLK.is_enabled
        HSICLK.disable()
        assert not HSICLK.is_enabled
        SYSCLK = part.clock("SYSCLK")
        assert SYSCLK.current is HSICLK
        SYSCLK.select(SYSCLK.index("HSECLK"))
        assert SYSCLK.current is HSECLK
        # generate_code(part, f"{project_path}/source/chipconfig")
        config = Config(part)
        config.generate_code(f"{project_path}/source/chipconfig")

        MCO1_clk = part.clock("MCO1")
        print(f"clock {MCO1_clk} enable={MCO1_clk.enable_predicate}")
        MCO1_sig = part.peripheral("RCM").signal("MCO1")
        print(f"signal {MCO1_sig} enable={MCO1_sig.enable_predicate}")

    test(f"{os.environ['HOME']}/work/apm32f411vc-tiny-codegen", "APM32F411VET6")
