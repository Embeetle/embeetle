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
import qt
from typing import *


def get_default(
    font_color_override: Optional[str] = None,
    background_color_override: Optional[str] = None,
) -> str:
    """"""
    # Background
    background_color = data.theme["tool_tip_background"]
    if background_color_override is not None:
        background_color = background_color_override
    tip_palette = data.application.palette()
    tip_palette.setColor(
        qt.QPalette.ColorRole.ToolTipBase, qt.QColor(background_color)
    )
    # Font
    font_color = data.theme["tool_tip_font"]
    if font_color_override is not None:
        font_color = font_color_override
    tip_palette.setColor(
        qt.QPalette.ColorRole.ToolTipText, qt.QColor(font_color)
    )
    qt.QToolTip.setPalette(tip_palette)
    return f"""
        QToolTip {{
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
        }}
    """
