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

blueShade = [
    "#ffffff",
    "#f9fbfd",
    "#ecf2f9",
    "#e1ebf4",
    "#d5e1f0",
    "#c8d9ec",
    "#b9cfe8",
    "#acc7e3",
    "#9ebdde",  # Hexagon edges
    "#85abd6",
    "#729fcf",  # Tango color 1
    "#6391cd",
    "#5184c8",
    "#4379c2",
    "#3c72bb",
    "#376aae",
    "#3465a4",  # Tango color 2
]

yellowShade = [
    "#ffffff",
    "#fffceb",
    "#fefad9",
    "#fef8c9",
    "#fef7bc",
    "#fef4a7",
    "#fdf295",
    "#fdf086",
    "#fded6f",
    "#fcec64",
    "#fce94f",  # Tango color 1
    "#fce637",
    "#fbe429",
    "#fbe21a",
    "#fadf04",
    "#df00ff",
    "#edd400",  # Tango color 2
]

orangeShade = [
    "#ffffff",
    "#fffbf5",
    "#fef2e2",
    "#feeace",
    "#fde2bb",
    "#fddaa7",
    "#fcd294",
    "#fcca80",
    "#fcc26c",
    "#fcba58",
    "#fcaf3e",  # Tango color 1
    "#ff942d",
    "#ff8a19",
    "#ff850f",
    "#ff8005",
    "#fc7c00",
    "#f57900",  # Tango color 2
]

greenShade = [
    "#ffffff",
    "#f6fdef",
    "#e9fada",
    "#ddf7c5",
    "#d1f4b0",
    "#c5f19b",
    "#b9ee86",
    "#adeb71",
    "#a1e85c",
    "#95e547",
    "#8ae234",  # Tango color 1
    "#8ae234",
    "#87e22e",
    "#81e321",
    "#7bdd1b",
    "#73d216",  # Tango color 2
    "#4e9a06",  # Tango color 3
]

grayShade = [
    "#eeeeec",
    "#eeeeec",
    "#eeeeec",
    "#eeeeec",
    "#d3d7cf",
    "#d3d7cf",
    "#d3d7cf",
    "#d3d7cf",
    "#babdb6",
    "#babdb6",
    "#babdb6",  # Tango color 1
    "#babdb6",
    "#888a85",
    "#888a85",
    "#888a85",
    "#888a85",  # Tango color 2
    "#555753",  # Tango color 3
]

shades = {
    "blue": blueShade,
    "yellow": yellowShade,
    "orange": orangeShade,
    "green": greenShade,
    "gray": grayShade,
    "grey": grayShade,
}


# BACKGROUND COLORS
def get_gradient(
    color="blue",
    dark=0,
    orientation="top-bot",
    faded=False,
) -> str:
    """
    :param color:       One of these: ['blue', 'yellow', 'orange', 'green', 'gray'].
    :param dark:        Number from 0..3. The higher, the darker.
    :param orientation: One of these: ['left-right', 'right-left', 'top-bot', 'bot-top'].
    :param faded:       True or False.
    :return:            Gradient as a string.
    """
    # 1. Color
    shade = shades[color]
    if dark == 0:
        i = [3, 2, 2, 0]
    elif dark == 1:
        i = [5, 4, 3, 0]
    elif dark == 2:
        i = [12, 8, 6, 0]
    elif dark == 3:
        i = [16, 14, 9, 8]
    else:
        i = [3, 2, 2, 0]

    # 2. Orientation
    if orientation == "left-right":
        points = "x1:0, y1:0.5, x2:1, y2:0.5"
    elif orientation == "right-left":
        points = "x1:1, y1:0.5, x2:0, y2:0.5"
    elif orientation == "top-bot":
        points = "x1:0.5, y1:0, x2:0.5, y2:1"
    elif orientation == "bot-top":
        points = "x1:0.5, y1:1, x2:0.5, y2:0"
    else:
        assert False

    # 3. Stops
    if (orientation == "top-bot") or (orientation == "bot-top"):
        stops = (0, 0.499, 0.5, 1)
    elif (orientation == "left-right") or (orientation == "right-left"):
        stops = (0, 0.3, 0.7, 1)
    else:
        assert False

    # 4. Make gradient string
    if not faded:
        gradientstr = f""" QLinearGradient( {points},
            stop: {stops[0]} {shade[i[0]]},
            stop: {stops[1]} {shade[i[1]]},
            stop: {stops[2]} {shade[i[2]]},
            stop: {stops[3]} {shade[i[3]]} )"""
    else:
        gradientstr = f""" QLinearGradient( {points},
            stop: {stops[0]} {"#00000000"},
            stop: {stops[1]} {shade[i[1]]},
            stop: {stops[2]} {shade[i[2]]},
            stop: {stops[3]} {"#00000000"}  )"""

    return gradientstr


def get_border_color(color="blue"):
    """
    :param color: One of these: ['blue', 'yellow', 'orange', 'green', 'gray'].
    :return:      Border color as a string.
    """
    borders = {
        "blue": "#729fcf",
        "yellow": "#c4a000",
        "orange": "#f57900",
        "green": "#4e9a06",
        "gray": "#888a85",
        "grey": "#888a85",
    }
    return borders[color]
