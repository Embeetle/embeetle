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
import gui.stylesheets.menu


def get_default():
    return f"""
QTextEdit {{
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
    background-color: {data.theme["fonts"]["default"]["background"]}; 
    color: {data.theme["fonts"]["default"]["color"]};
    selection-background-color: {data.theme["fonts"]["selection"]["background"]};
    selection-color: {data.theme["fonts"]["selection"]["color"]};
}}

{gui.stylesheets.menu.get_general_stylesheet()}
    """
