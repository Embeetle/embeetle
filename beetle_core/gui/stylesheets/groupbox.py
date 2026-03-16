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

##
##  General form used for dialogs
##

import sys
import os
import data
import gui.stylesheets.button
import gui.stylesheets.button as _btn_style_


def get_noborder_style(background_color=None, additional_properties=""):
    """Style used by the for example 'Messages' box."""
    backcolor = data.theme["editor_background"]
    if background_color is not None:
        backcolor = background_color
    style_sheet = f"""
QGroupBox {{
    background-image: none;
    background-color: {backcolor};
    border: none;
    padding: 0px;
    {additional_properties}
}}
    """
    return style_sheet


def get_default(background_transparent=False, no_border=False):
    #    background_color = data.theme["general_background"]
    background_color = data.theme["fonts"]["default"]["background"]
    if background_transparent:
        background_color = "transparent"
    border = f'1px solid {data.theme["button_border"]}'
    if no_border:
        border = "none"
    style_sheet = f"""
QGroupBox {{
    background-image: none;
    background-color: {background_color};
    color: {data.theme["fonts"]["default"]["color"]};
    border: {border};
    padding: 0px;
}}
QGroupBox::title {{
    background-color: transparent;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    margin-left: 2px;
    margin-top: 2px;
}}
    """
    return style_sheet


def get_popup_box():
    style_sheet = f"""
QGroupBox {{
    background-image: none;
    background-color: transparent;
    border: none;
    padding: 0px;
}}
QSplitter {{
    background-color: transparent;
}}
QSplitter::handle {{
    height: 14px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 transparent,
        stop:1 {data.theme["button_border"]}
    );
}}
    """
    return style_sheet
