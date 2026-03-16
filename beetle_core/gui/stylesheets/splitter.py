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

import os
import data
import functions


def get_transparent_stylesheet():
    margin = 0
    width = data.get_splitter_pixelsize()
    height = data.get_splitter_pixelsize()
    return f"""
QSplitter {{
    background: transparent;
    margin: {margin}px;
}}
QSplitter::handle {{
    background: {data.theme["splitter_handle_background"]};
}}
QSplitter::handle:vertical {{
    background: {data.theme["splitter_handle_background"]};
    height: {height}px;
}}
QSplitter::handle:horizontal {{
    background: {data.theme["splitter_handle_background"]};
    width: {width}px;
}}
QSplitter::handle:hover {{
    background: {data.theme["splitter_handle_hover"]};
}}
QSplitter::handle:vertical:hover {{
    background: {data.theme["splitter_handle_hover"]};
}}
QSplitter::handle:horizontal:hover {{
    background: {data.theme["splitter_handle_hover"]};
}}
QSplitter::handle:vertical:pressed {{
    background: {data.theme["splitter_handle_pressed"]};
}}
QSplitter::handle:horizontal:pressed {{
    background: {data.theme["splitter_handle_pressed"]};
}}
    """
