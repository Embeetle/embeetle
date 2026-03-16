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


def get_default(box_name, no_border=True):
    border = f'1px solid {data.theme["button_border"]}'
    if no_border:
        border = "none"
    style_sheet = f"""
        #{box_name} {{
            font-size: {data.get_general_font_pointsize()}pt;
            font-weight: bold;
            color: {data.theme["fonts"]["default"]["color"]};
            border: {border};
            background-color: {data.theme["fonts"]["default"]["background"]};
            margin: 0px;
            padding: 0px;
        }}
        #{box_name}::title {{
            color: {data.theme["fonts"]["default"]["color"]};
            border: {border};
            background-color: {data.theme["fonts"]["default"]["background"]};
            subcontrol-position: top left;
            padding: 0px;
            left: 0px; top: -6px;
        }}
    """
    return style_sheet
