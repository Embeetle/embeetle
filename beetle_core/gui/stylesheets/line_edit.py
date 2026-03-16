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
from typing import *
import data


def get_line_edit_stylesheet(
    text_color="#204a87",
    background_color="#aaf9f9f7",
    border_color="#d3d7cf",
) -> str:
    """Stylesheet for 'ItemLineedit()' in Dashboard."""
    return f"""
        QLineEdit {{
            text-align: left;
            background: {background_color};
            color: {text_color};
            border: 1px solid {border_color};
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            padding: 0px 5px 0px 5px;
        }}
        QLineEdit[red = true] {{
            color: {data.theme['fonts']['red']['color']};
        }}
        QLineEdit[gray = true] {{
            color: {data.theme['fonts']['disabled']['color']};
        }}
        QLineEdit[green = true] {{
            color: {data.theme['fonts']['green']['color']};
        }}
    """
