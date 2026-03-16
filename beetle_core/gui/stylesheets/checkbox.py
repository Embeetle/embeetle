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

from typing import *
import data
import functions, iconfunctions

error = iconfunctions.get_icon_abspath(
    "icons/include_chbx/c_files/grey_exclam.png"
)

disabled = iconfunctions.get_icon_abspath("icons/checkbox/disabled.png")
disabled_hover = iconfunctions.get_icon_abspath(
    "icons/checkbox/disabled_hover.png"
)
disabled_pressed = iconfunctions.get_icon_abspath(
    "icons/checkbox/disabled_pressed.png"
)

checked = iconfunctions.get_icon_abspath("icons/checkbox/checked.png")
checked_hover = iconfunctions.get_icon_abspath(
    "icons/checkbox/checked_hover.png"
)
checked_pressed = iconfunctions.get_icon_abspath(
    "icons/checkbox/checked_pressed.png"
)
checked_dark_green = iconfunctions.get_icon_abspath(
    "icons/checkbox/checked_dark_green.png"
)
checked_grey = iconfunctions.get_icon_abspath("icons/checkbox/checked_grey.png")

grey = iconfunctions.get_icon_abspath("icons/checkbox/grey.png")
grey_hover = iconfunctions.get_icon_abspath("icons/checkbox/grey_hover.png")
grey_pressed = iconfunctions.get_icon_abspath("icons/checkbox/grey_pressed.png")
grey_checked = iconfunctions.get_icon_abspath("icons/checkbox/grey_checked.png")
grey_unchecked = iconfunctions.get_icon_abspath(
    "icons/checkbox/grey_unchecked.png"
)

checkdot = iconfunctions.get_icon_abspath("icons/checkbox/checked_dot.png")
checkdot_hover = iconfunctions.get_icon_abspath(
    "icons/checkbox/checked_dot_hover.png"
)
checkdot_pressed = iconfunctions.get_icon_abspath(
    "icons/checkbox/checked_dot_pressed.png"
)

uncheckdot = iconfunctions.get_icon_abspath("icons/checkbox/unchecked_dot.png")
uncheckdot_hover = iconfunctions.get_icon_abspath(
    "icons/checkbox/unchecked_dot_hover.png"
)
uncheckdot_pressed = iconfunctions.get_icon_abspath(
    "icons/checkbox/unchecked_dot_pressed.png"
)


def get_wizard_chbx_stylesheet(size: Tuple[int, int] = (30, 30)) -> str:
    """"""
    chbxStyleSheet = f"""
QCheckBox {{
    spacing: 5px;
}}
QCheckBox::indicator {{
    width: {size[0]}px;
    height: {size[1]}px;
    image: url({error});
}}
QCheckBox::indicator:unchecked:disabled {{
    image: url({disabled});
}}
QCheckBox::indicator:checked {{
    image: url({checked});
}}
QCheckBox::indicator:checked:hover {{
    image: url({checked_hover});
}}
QCheckBox::indicator:checked:pressed {{
    image: url({checked_pressed});
}}
QCheckBox::indicator:unchecked {{
    image: url({grey});
}}
QCheckBox::indicator:unchecked:hover {{
    image: url({grey_hover});
}}
QCheckBox::indicator:unchecked:pressed {{
    image: url({grey_pressed});
}}
    """
    return chbxStyleSheet


def get_checkdot_stylesheet(on: bool = False, size: int = 30) -> str:
    """"""
    _checkdot = checkdot if on else uncheckdot
    _checkdot_hover = checkdot_hover if on else uncheckdot_hover
    _checkdot_pressed = checkdot_pressed if on else uncheckdot_pressed

    stylesheet = f"""
QPushButton {{
    margin: 0px 0px 0px 0px;
    padding: 0px 0px 0px 0px;
    background-color: #00ffffff;
    border-color: #00ffffff;
    border-style: none;
    border-width: 0px;
    border-radius: {int(size/2)}px;
    image: url({_checkdot});
}}

QPushButton:pressed {{
    image: url({_checkdot_pressed});
}}

QPushButton:hover:!pressed {{
    image: url({_checkdot_hover});
}}
    """
    return stylesheet


def get_standard() -> str:
    """"""
    size = data.get_toplevel_menu_pixelsize()
    stylesheet = f"""
QCheckBox {{
    spacing: 1px;
}}

QCheckBox::indicator {{
    width: {size}px;
    height: {size}px;
}}
QCheckBox::indicator:unchecked {{
    image: url({grey});
}}
QCheckBox::indicator:unchecked:hover {{
    image: url({grey_hover});
}}
QCheckBox::indicator:unchecked:pressed {{
    image: url({grey_pressed});
}}


QCheckBox::indicator:checked {{
    image: url({checked});
}}
QCheckBox::indicator:checked:hover {{
    image: url({checked_hover});
}}
QCheckBox::indicator:checked:pressed {{
    image: url({checked_pressed});
}}

QCheckBox::indicator:disabled:unchecked {{
    image: url({grey_unchecked});
}}
QCheckBox::indicator:disabled:checked {{
    image: url({checked_grey});
}}
    """
    return stylesheet


def get_round() -> str:
    """"""
    size = data.get_toplevel_menu_pixelsize()
    stylesheet = f"""
QCheckBox {{
    spacing: 1px;
}}

QCheckBox::indicator {{
    width: {size}px;
    height: {size}px;
}}

QCheckBox::indicator:unchecked {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/unchecked_dot.png")});
}}

QCheckBox::indicator:unchecked:hover {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/unchecked_dot_hover.png")});
}}

QCheckBox::indicator:unchecked:pressed {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/unchecked_dot_pressed.png")});
}}

QCheckBox::indicator:checked {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/checked_dot.png")});
}}

QCheckBox::indicator:checked:hover {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/checked_dot_hover.png")});
}}

QCheckBox::indicator:checked:pressed {{
    image: url({iconfunctions.get_icon_abspath("icons/checkbox/checked_dot_pressed.png")});
}}
    """
    return stylesheet
