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

# Allow relative imports during stand-alone execution
import os

__package__ = __package__ or os.path.basename(os.path.dirname(__file__))
if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .model import (
    Series,
    ClockLayout,
    Orientation,
    ExternalClock,
    InternalClockSink,
    ExternalClockSink,
    MuxClock,
    MultipliedClock,
    DividedClock,
    _natural_sort_key,
)
from .error import ConfigError


def peripheral_groups(clock: Clock) -> {str: {Peripheral}}:
    todo = set(clock.peripherals)
    groups = {}
    for bus in clock.busses:
        bus_peripherals = sorted(
            bus.peripherals, key=lambda p: _natural_sort_key(p.name)
        )
        groups[bus.name] = bus_peripherals
        todo -= set(bus_peripherals)
    for kind in {p.kind for p in todo}:
        peripherals = sorted(
            (p for p in todo if p.kind is kind),
            key=lambda p: _natural_sort_key(p.name),
        )
        groups[" ".join(p.name for p in peripherals)] = peripherals
    return groups


def set_clock_layout(series: Series):
    series_data = _data.get(series.name)
    if not series_data:
        return
    for clock in series.clocks:
        data = series_data.get(clock.name)
        if not data:
            raise ConfigError(
                f"no clock layout data for {series.name} {clock.name}"
            )

        sink_locations: [(str, float, float, Orientation)] = []

        def get_sink_location(label: str):
            for prefix, x, y, orientation in sink_locations:
                if label.startswith(prefix):
                    return x, y, orientation
            print(f"Sink locations: {sink_locations}")
            raise ConfigError(f"no sink location data for {clock}.'{label}'")

        def route(seq):
            label = seq[-1] if type(seq[-1]) is str else None
            if label is not None:
                seq = seq[0:-1]
                sink_locations.append(
                    (
                        label,
                        seq[-1],
                        seq[-2],
                        (
                            Orientation.RIGHT
                            if seq[-1] > seq[-3]
                            else Orientation.LEFT
                        ),
                    )
                )
            x = seq[0]
            y = seq[1]
            points = [(x, y)]
            hor = seq[2] != x
            for p in seq[2 if hor else 3 :]:
                if hor:
                    x = p
                else:
                    y = p
                points.append((x, y))
                hor = not hor
            return points

        routes = []
        dots = set()
        tags = []
        for seq in data:
            if seq[0] == "tag":
                orientation = (
                    Orientation.RIGHT if seq[3] > seq[1] else Orientation.LEFT
                )
                tags.append((seq[1], seq[2], orientation))
                routes.append(route(seq[1:]))
            else:
                dots.add((seq[0], seq[1]))
                routes.append(route(seq))
            if type(seq[-1]) is str:
                label = seq[-1]

        todo = set(clock.peripherals)
        sinks = []

        def add_sink(
            label: str, peripherals: Iterable[Peripheral], bus: Bus | None
        ):
            x, y, orientation = get_sink_location(label)
            sinks.append(
                InternalClockSink(
                    clock=clock,
                    label=label,
                    x=x,
                    y=y,
                    orientation=orientation,
                    peripherals=peripherals,
                    bus=bus,
                )
            )

        for bus in clock.busses:
            label = f"{bus.name} bus"
            add_sink(label, bus.peripherals, bus)
            todo -= set(bus.peripherals)
        for kind in {p.kind for p in todo}:
            peripherals = [p for p in todo if p.kind is kind]
            label = _sink_label(peripherals)
            add_sink(label, peripherals, None)
        x = data[0][0]
        y = data[0][1]
        orientation = Orientation.RIGHT if data[0][2] > x else Orientation.LEFT
        dots.remove((x, y))
        name_extension = (
            len(clock.name) + 1
            if not clock.name.startswith("_")
            and type(clock) in [MuxClock, MultipliedClock, DividedClock]
            and not series.signal(clock.name)
            else 0
        )
        layout = ClockLayout(
            x=x,
            y=y,
            orientation=orientation,
            name_extension=name_extension,
            routes=routes,
            dots=list(dots),
            tags=tags,
            sinks=sinks,
        )
        clock._set_layout(layout)
        if type(clock) is not ExternalClock and series.signal(clock.name):
            print(f"exported clock: {clock} {type(clock).__name__}")
            label = clock.name
            x, y, orientation = get_sink_location(label)
            sinks.append(
                ExternalClockSink(
                    clock=clock,
                    label=label,
                    y=y,
                )
            )

    for peripheral in series.peripherals:
        for clock in peripheral.clocks:
            if peripheral not in (
                p for sink in clock.layout.sinks for p in sink.peripherals
            ):
                raise ConfigError(
                    f"Missing clock layout data for {peripheral} {clock}"
                )


def _sink_label(peripherals: Iterable[Peripheral]) -> str:
    return _compress(
        sorted(
            (p.name for p in peripherals),
            key=_natural_sort_key,
        )
    )


def _compress(names: Iterable[str]):
    parts = []
    base = None
    for name in names:
        new_base = _get_base(name)
        if new_base == base:
            parts.append(f",{name[len(base):]}")
        else:
            if base is None:
                parts.append(name)
            else:
                parts.append(f" {name}")
            base = new_base
    return "".join(parts)


def _get_base(name):
    for i, c in enumerate(reversed(name)):
        if not c.isdigit():
            return name[:-i]
    return name


# Ultimately, we want to generate the clock layout automatically.  For now,
# we derive it manually and write it down in the data below.
# There is a dict with the series name as key and layout data as value. Layout
# data is again a dict, with clock names as key and routing data as value.
# Routing data for a clock describes the routing of that clock to other blocks,
# where blocks are other clocks or clock sinks.
# It consists of a tuple of tuples. Each lowest level tuple describes a line
# segment as a sequence of coordinates. It always starts with an x coordinate
# and alternates between x and y coordinates. In other words:
#   - (tuple[0],tuple[1]) is the starting point
#   - for each additional number tuple[i] with even i, draw a horizontal line
#   - for each additional number tuple[i] with odd i, draw a vertical line
#   - if the last element of the tuple is a string, the end of the line segment
#     is the location of a sink whose label starts with that string
# The first line segment starts from the clock output. Subsequent line segments
# usually start from a point on another line segment and need a bullet at the
# starting point.
# In some cases, a line segment starts with a tag instead of a bullet. This
# happens when the line segment does not start from a point on another line
# segment, but at an arbitrary location in the clock tree diagram.  In those
# cases, the first element of the tuple is the string "tag". The tag is always
# drawn with the clock name as content.
src_x = 14
_data = {
    "APM32F411": {
        "LSECLK": ((src_x, 4, 26), ("tag", 20, 59, 18)),
        "LSICLK": (
            (src_x, 15, 20, 6, 26),  # RTC mux
            (20, 10, 35, "IWDT"),
        ),
        "HSICLK": ((src_x, 26, 65), (17, 26, 17, 36, 18), ("tag", 20, 57, 18)),
        "HSECLK": (
            (src_x, 38, 18),
            (15, 38, 15, 2, 16),
            (15, 28, 65),
            ("tag", 20, 61, 18),
            ("tag", 20, 72, 18),
        ),
        "I2S_CKIN": ((2, 53, 65),),
        "_HSE_RTC": ((24, 2, 25),),
        "RTC": ((33, 4, 35, "RTC"),),
        "SYSCLK": ((76, 28, 84), ("tag", 20, 68, 18)),
        "HCLK": (
            (96, 28, 97, 15, 98),  # HCLK8
            (97, 20, 116, "Core"),  # FCLK/CORE
            (97, 25, 116, "AHB1"),
            (97, 30, 116, "AHB2"),
            (97, 28, 97, 35, 100),  # PCLK1
            (97, 35, 97, 50, 100),  # PCLK2
        ),
        "HCLK8": ((112, 15, 116, "SysTick"),),
        "PCLK1": (
            (114, 35, 128, "APB1"),
            (116, 35, 116, 40, 117),
        ),
        "_PCLK1_TMR": ((125, 40, 128, "TMR2"),),
        "PCLK2": (
            (112, 50, 128, "APB2"),
            (113, 50, 113, 55, 115),  # TMRxCLK
            (113, 55, 113, 60, 115),  # ADC1CLK
            (113, 60, 113, 65, 115),  # ADC1CLK
        ),
        "_PCLK2_TMR": ((123, 55, 128, "TMR1"),),
        "ADC1": ((126, 60, 128, "ADC1"),),
        "ADC2": ((126, 65, 128, "ADC2"),),
        "_PLLsrc": ((22, 37, 25), (24, 37, 24, 49, 25)),
        "_PLL1in": ((33, 37, 35),),
        "_PLL2in": ((33, 49, 35),),
        "_PLL1vco": ((43, 37, 45), (44, 37, 44, 41, 45)),
        "_PLL2vco": ((43, 49, 45),),
        "PLL1CLK": (
            (61, 37, 64, 30, 65),
            ("tag", 20, 63, 18),
            ("tag", 20, 74, 18),
        ),
        "PLL48CLK": (
            (62, 41, 65, 36, 67, "USB_FS"),
            (65, 41, 67, "RNG"),
            (65, 41, 65, 46, 67, "SDIO"),
        ),
        "PLL2CLK": ((61, 49, 64, 51, 65), ("tag", 20, 70, 18)),
        "I2SCLK": ((76, 52, 78, "I2S"),),
        "_MCO1_muxout": ((14, 60, 10),),
        "MCO1": ((2, 60, ExternalClockSink.x, "MCO1"),),
        "_MCO2_muxout": ((14, 71, 10),),
        "MCO2": ((2, 71, ExternalClockSink.x, "MCO2"),),
    },
}


def selftest():
    from .load_json import Index

    print("Selftest for clock_layout")

    part_index = Index()
    root = f"{os.path.dirname(__file__)}/resources/series"
    # part_index.add_file(f"{root}/CH32V003/CH32V00xxx.json5")
    part_index.add_file(f"{root}/APM32F411/chip_config.json5")

    part = part_index.load_part("APM32F411VET6")
    for clock in part.clocks:
        layout = clock.layout
        print(
            f"{clock} {type(clock).__name__}"
            f" at ({layout.x},{layout.y}) {layout.orientation}"
            f" name-extension {clock.layout.name_extension}"
        )
        for route in layout.routes:
            print(f"  polyline: {' '.join(f'({x},{y})' for x,y in route)}")
        for x, y in layout.dots:
            print(f"  dot: ({x},{y})")
        for x, y, orientation in layout.tags:
            print(f"  tag: ({x},{y}) {orientation}")
        for sink in layout.sinks:
            print(f"  sink: {sink.label} {sink.x} {sink.y} {sink.orientation}")


if __name__ == "__main__":
    selftest()
