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
import gui.stylesheets.scrollbar
import gui.stylesheets.table
import gui.stylesheets.tooltip


def get_default(background_transparent=False, no_border=True):
    background_color = data.theme["fonts"]["default"]["background"]
    if background_transparent:
        background_color = "transparent"
    border = f'1px solid {data.theme["button_border"]}'
    if no_border:
        border = "none"
    border = "none"
    style_sheet = f"""
QFrame {{
    background-color: {background_color};
    border: {border};
}}
{gui.stylesheets.tooltip.get_default()}
    """
    return style_sheet


def get_symbols_window():
    background_color = data.theme["fonts"]["default"]["background"]
    border = f'1px solid {data.theme["button_border"]}'
    style_sheet = f"""
QFrame {{
    background-color: {background_color};
    border: none;
}}
#SymbolStack {{
    /*
    border-top: {border};
    */
}}
{gui.stylesheets.tooltip.get_default()}
    """
    return style_sheet


def get_memoryview():
    background_color = data.theme["fonts"]["default"]["background"]
    border = f'1px solid {data.theme["button_border"]}'
    style_sheet = f"""
QFrame {{
    background-color: {background_color};
    border: none;
}}

{gui.stylesheets.tooltip.get_default()}
    """
    return style_sheet


def get_popup(background_transparent=False, no_border=True):
    background_color = data.theme["fonts"]["default"]["background"]
    if background_transparent:
        background_color = "transparent"
    border = f'1px solid {data.theme["button_border"]}'
    if no_border:
        border = "none"
    style_sheet = f"""
QFrame {{
    background-color: {background_color};
    border: {border};
}}
{gui.stylesheets.tooltip.get_default()}
    """
    return style_sheet
