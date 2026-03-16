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
from . import tooltip

##
##  Base slider widget stylesheet
##


def get_default(
    hoverable: bool = False,
    transparent: bool = False,
) -> str:
    """"""
    background_color = data.theme["fonts"]["default"]["background"]
    if transparent:
        background_color = "transparent"
    hover_style = ""
    if hoverable:
        hover_style = f"""
            QLabel::hover {{
                background-color: {data.theme['indication']['hover']};
            }}
        """
    return f"""
        QLabel {{
            background-color: {background_color};
            color: {data.theme['fonts']['default']['color']};
        }}
        {hover_style}
        {tooltip.get_default()}
    """


def get_tree_lbl_stylesheet(text_color=None) -> str:
    """
    WARNING:
    The ItemLbl() in Kristof's Tree Widgets are actually QPushButton()s!
    """
    color: str = (
        text_color
        if text_color is not None
        else data.theme["fonts"]["default"]["color"]
    )
    return f"""
        QPushButton {{
            text-align: left;
            background-color: transparent;
            color: {color};
            border: none;
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            margin: 0px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {data.theme['indication']['hover']};
        }}
        QPushButton[_hover = true] {{
            background-color: {data.theme['indication']['hover']};
        }}
    """


def get_tree_lbl_blink_stylesheet(text_color="#2e3436") -> str:
    """Stylesheet for blinking buttons (eg.

    blinking buttons in the dirtree).
    """
    # WARNING: The Cythonizer doesn't like a variable being assigned a
    # string value with the string starting on the next line (using a
    # '= \' for the syntax).
    return (
        get_tree_lbl_stylesheet(text_color)
        + f"""
        QPushButton[blink_01 = true] {{
            background-color: #fffefefe;
        }}
        QPushButton[blink_02 = true] {{
            background-color: #ff8ae234;
        }}
    """
    )


def get_title_stylesheet() -> str:
    """"""
    return str(
        f'    color: {data.theme["fonts"]["default"]["color"]};'
        f"    border: none;"
        f"    padding: 0px;"
        f"    spacing: 0px;"
        f"    margin: 0px;"
        f'    background-color: {data.theme["fonts"]["default"]["background"]};'
    )
