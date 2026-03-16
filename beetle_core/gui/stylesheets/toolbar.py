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
import iconfunctions


def get_default() -> str:
    stylesheet = f"""
QToolBar {{
    background: {data.theme["form_background"]};
    color: {data.theme["fonts"]["default"]["color"]};
    border: none;
}}
QToolBar QToolButton {{
    background: transparent;
    color: {data.theme["fonts"]["default"]["color"]};
    border: none;
}}
QToolBar QToolButton:hover {{
    background: {data.theme["indication"]["hover"]};
}}
QToolBar QToolButton:disabled {{
    color: {data.theme["fonts"]["disabled"]["color"]};
}}
QToolBar::separator {{
    background: transparent;
    width: 1px;
    margin: 2px;
}}
    """
    return stylesheet
