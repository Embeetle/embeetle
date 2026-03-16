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

import mcuconfig

# Color palette below is originally based on Tango colors
# https://en.wikipedia.org/wiki/Tango_Desktop_Project
# If more colors are needed, check https://icolorpalette.com/tango
color_palette = {
    "Butter 0": "#fce94f",  # Avoid: too similar to Butter 1
    "Orange 0": "#fcaf3e",
    "Chocolate 0": "#e9b96e",
    "Chameleon 0": "#8ae234",  # Avoid: too similar to Chameleon 1
    "Sky Blue 0": "#729fcf",
    "Plum 0": "#ad7fa8",
    "Scarlet Red 0": "#ef2929",
    "Aluminium 0": "#eeeeec",
    "Aluminium Darker 0": "#888a85",
    "Butter 1": "#edd400",
    "Orange 1": "#f57900",
    "Chocolate 1": "#c17d11",
    "Chameleon 1": "#73d116",
    "Sky Blue 1": "#3465a4",
    "Plum 1": "#75507b",
    "Scarlet Red 1": "#cc0000",
    "Aluminium 1": "#d3d7cf",
    "Aluminium Darker 1": "#555753",
    "Butter 2": "#c4a000",
    "Orange 2": "#ce5c00",
    "Chocolate 2": "#8f5902",
    "Chameleon 2": "#4e9a06",
    "Sky Blue 2": "#204a87",
    "Plum 2": "#5c2566",
    "Scarlet Red 2": "#a40000",
    "Aluminium 2": "#babdb6",
    "Aluminium Darker 2": "#2e2426",
}

# Peripheral colors
peripheral_colors = {
    mcuconfig.PeripheralKind.ADC: "Chameleon 1",
    mcuconfig.PeripheralKind.CAN: "Scarlet Red 0",
    mcuconfig.PeripheralKind.CLOCK: "Orange 2",
    mcuconfig.PeripheralKind.CORE: "Chameleon 2",
    mcuconfig.PeripheralKind.DAC: "Plum 2",
    mcuconfig.PeripheralKind.DBG: "Aluminium 2",
    mcuconfig.PeripheralKind.ETHERNET: "Aluminium 1",
    mcuconfig.PeripheralKind.GPIO: "Orange 0",
    mcuconfig.PeripheralKind.I2C: "Plum 0",
    mcuconfig.PeripheralKind.I2S: "Orange 1",
    mcuconfig.PeripheralKind.I3C: "Aluminium 0",
    mcuconfig.PeripheralKind.IRDA: "Sky Blue 2",
    mcuconfig.PeripheralKind.LIN: "Aluminium Darker 0",
    mcuconfig.PeripheralKind.MEMORY: "Sky Blue 0",
    mcuconfig.PeripheralKind.OPAMP: "Plum 1",
    mcuconfig.PeripheralKind.QSPI: "Chocolate 0",
    mcuconfig.PeripheralKind.SERIAL: "Butter 2",
    mcuconfig.PeripheralKind.SPI: "Sky Blue 1",
    mcuconfig.PeripheralKind.TIMER: "Chocolate 1",
    mcuconfig.PeripheralKind.USB: "Chocolate 2",
}


def get_peripheral_type_color(peripheral_type: mcuconfig.PeripheralKind):
    name = peripheral_colors.get(peripheral_type, "Aluminium Darker 2")
    bg_color = color_palette[name]
    return {
        "name": name,
        "color": {
            "fg": get_best_text_color(bg_color),
            "bg": bg_color,
        },
    }


def get_pin_special_color(pin_type: str) -> dict:
    bg_color = pin_special_colors[pin_type]
    return {
        "name": pin_type,
        "color": {
            "fg": get_best_text_color(bg_color),
            "bg": bg_color,
        },
    }


# Special pin color table
pin_special_colors = {
    "power": color_palette["Scarlet Red 1"],  # used to be "#d3320a",
    "pin-mode": color_palette["Butter 1"],  # used to be "#fce94f",
}


def get_best_text_color(color):
    """Determine the best text color for a given background color."""
    return "#000000" if get_luminance(color) > 0.4 else "#ffffff"


def get_luminance(color):
    """Compute the luminance of an RGB color given in '#rrggbb' syntax."""

    # Convert RGB to linear space
    def linear_component(hex_value):
        value = int(hex_value, base=16) / 255.0
        return (
            value / 12.92
            if value <= 0.03928
            else ((value + 0.055) / 1.055) ** 2.4
        )

    # Calculate relative luminance
    r_linear = linear_component(color[1:3])
    g_linear = linear_component(color[3:5])
    b_linear = linear_component(color[5:7])
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
