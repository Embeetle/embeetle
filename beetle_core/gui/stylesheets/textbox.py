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

from . import tooltip


def get_default(no_border=False):
    border = f'border: 1px solid {data.theme["button_border"]};'
    if no_border:
        border = "border: none;"
    placeholder_color = data.theme["fonts"]["default"]["color"].replace(
        "#ff", "#7f"
    )
    style_sheet = f"""
QLineEdit {{
    font-size: {data.get_general_font_pointsize()}pt;
    font-weight: bold;
    color: {data.theme["fonts"]["default"]["color"]};
    {border}
    background-color: {data.theme["dark_background"]};
    margin-left: 0px;
    margin-top: 0px;
    margin-bottom: 0px;
    margin-right: 0px;
    padding: 0px;
}}

QLineEdit[readonly="true"] {{
    background-color: {data.theme["general_background"]};
    color: {data.theme["fonts"]["default"]["color"]};
    font-weight: normal;
}}

QLineEdit[red=true] {{
    color: #cc0000;
}}
QLineEdit[lightred=true] {{
    color: #f47070;
}}
QLineEdit[green=true] {{
    color: #4e9a06;
}}
QLineEdit[autofilled=true] {{
    color: #888a85;
}}

QLineEdit[background_lightred=true] {{
    background-color: #f47070;
}}
QLineEdit[background_green=true] {{
    background-color: #4e9a06;
}}

QLineEdit[showing-placeholder-text=true] {{
    color: {placeholder_color};
}}

QLineEdit:disabled {{
    background-color: {data.theme["dark_background"]};
    color: {data.theme["general_background"]};
    font-weight: normal;
}}
QLineEdit:read-only {{
    background-color: {data.theme["general_background"]};
    color: {data.theme["fonts"]["default"]["color"]};
    font-weight: normal;
}}

{tooltip.get_default()}
    """
    return style_sheet
