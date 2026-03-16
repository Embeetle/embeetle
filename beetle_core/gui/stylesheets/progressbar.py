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
import gui.stylesheets.helper as _h_


def get_unfaded_style(color: str) -> str:
    """Get stylesheet for unfaded progressbar.

    :param color: One of these: ['blue', 'yellow', 'orange', 'green', 'gray'].
    :return: Stylesheet as a string.
    """
    bck_col = _h_.get_gradient(color=color, dark=0, orientation="left-right")
    chunck_col = _h_.get_gradient(color=color, dark=3, orientation="right-left")
    border_col = _h_.get_border_color(color=color)
    text_col = "#2e3436"
    if (color == "gray") or (color == "grey"):
        text_col = "#babdb6"
    stylestr = f"""
        QProgressBar {{
            background: {bck_col};
            border-width: 1px;
            border-style: solid;
            border-color: {border_col};
            border-radius: 4px;
            text-align: center;
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            color: {text_col};
        }}
        QProgressBar::chunk {{
            background: {chunck_col};
            border-radius: 2px;
        }}
    """
    return stylestr


def get_faded_style(color: str) -> str:
    """Get stylesheet for faded progressbar.

    :param color: One of these: ['blue', 'yellow', 'orange', 'green', 'gray'].
    :return: Stylesheet as a string.
    """
    bck_col = _h_.get_gradient(color=color, dark=0, orientation="left-right")
    chunck_col = _h_.get_gradient(
        color=color, dark=3, orientation="right-left", faded=True
    )
    border_col = _h_.get_border_color(color=color)
    text_col = "#2e3436"
    if (color == "gray") or (color == "grey"):
        text_col = "#babdb6"
    stylestr = f"""
        QProgressBar {{
            background: {bck_col};
            border-width: 1px;
            border-style: solid;
            border-color: {border_col};
            border-radius: 4px;
            text-align: center;
            font-weight: bold;
            font-size: {data.get_general_font_pointsize()}pt;
            color: {text_col};
        }}
        QProgressBar::chunk {{
            background: {chunck_col};
            border-radius: 4px;
        }}
    """
    return stylestr


################################################################################


def get_unfaded_thin_style(color: str) -> str:
    """Get stylesheet for unfaded progressbar.

    :param color: One of these: ["blue", "yellow", "orange", "green"].
    :return: Stylesheet as a string.
    """
    bck_col = _h_.get_gradient(color=color, dark=0, orientation="left-right")
    chunck_col = _h_.get_gradient(color=color, dark=3, orientation="right-left")
    border_col = _h_.get_border_color(color=color)
    text_col = "#2e3436"
    if (color == "gray") or (color == "grey"):
        text_col = "#babdb6"
    stylestr = f"""
        QProgressBar {{
            background: {bck_col};
            border-width: 1px;
            border-style: solid;
            border-color: {border_col};
            border-radius: 2px;
            color: {text_col};
        }}
        QProgressBar::chunk {{
            background: {chunck_col};
            border-radius: 2px;
        }}
    """
    return stylestr


def get_faded_thin_style(color: str) -> str:
    """Get stylesheet for faded progressbar.

    :param color: One of these: ['blue', 'yellow', 'orange', 'green', 'gray'].
    :return: Stylesheet as a string.
    """
    bck_col = _h_.get_gradient(color=color, dark=0, orientation="left-right")
    chunck_col = _h_.get_gradient(
        color=color, dark=3, orientation="right-left", faded=True
    )
    border_col = _h_.get_border_color(color=color)
    text_col = "#2e3436"
    if (color == "gray") or (color == "grey"):
        text_col = "#babdb6"
    stylestr = f"""
        QProgressBar {{
            background: {bck_col};
            border-width: 1px;
            border-style: solid;
            border-color: {border_col};
            border-radius: 2px;
            color: {text_col};
        }}
        QProgressBar::chunk {{
            background: {chunck_col};
            border-radius: 2px;
        }}
    """
    return stylestr
