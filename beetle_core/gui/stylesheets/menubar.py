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


def get_default():
    return """
QMenuBar {{
    background-color: {};
    border: none;
    color: {};
    margin: 0px;
    spacing: 0px;
    padding: 0px;
}}
QMenuBar::item {{
    background-color: transparent;
}}
QMenuBar::item:selected {{
    background-color: {};
}}
    """.format(
        data.theme["menubar_background"],
        data.theme["fonts"]["default"]["color"],
        data.theme["indication"]["hover"],
    )
