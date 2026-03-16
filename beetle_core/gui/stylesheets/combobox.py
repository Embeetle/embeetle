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

import data
import functions
import iconfunctions


def get_default(
    background_transparent: bool = False,
    no_border: bool = False,
) -> str:
    """"""
    background_color = data.theme["fonts"]["default"]["background"]
    color = data.theme["fonts"]["default"]["color"]
    if background_transparent:
        background_color = "transparent"
    border = f'1px solid {data.theme["dropdown_border"]}'
    if no_border:
        border = "none"
    arrow_image = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_down.png"
    )
    arrow_size = int(data.get_general_icon_pixelsize() * 0.8)
    padding = (2 * data.get_global_scale()) ** 2
    style_sheet = f"""
QComboBox {{
    background-color: {background_color};
    color: {color};
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
    border: {border};
    border-radius: 0px;
    padding: 0px;
}}
QComboBox:disabled {{
    background-color: {data.theme["fonts"]["disabled"]["background"]};
    color: {data.theme["fonts"]["disabled"]["color"]};
}}

QComboBox::drop-down {{
    background-color: transparent;
}}
QComboBox::down-arrow {{
    background-color: transparent;
    image: url({arrow_image});
    width: {arrow_size}px;
    height: {arrow_size}px;
    padding-right: {padding}px;
}}
    """
    return style_sheet
