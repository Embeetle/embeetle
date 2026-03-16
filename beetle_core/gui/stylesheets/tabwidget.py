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


def get_dynamic_style() -> str:
    """"""
    normal_radius = 0
    normal_window_radius = 0
    normal_border_width = 1

    indicated_radius = 0
    indicated_window_radius = 0
    indicated_border_width = 1

    return f"""
        TabWidget {{
            background-color: {data.theme["fonts"]["default"]["background"]};
            border: none;
        }}
        TabWidget::pane {{
            background-color: {data.theme["editor_background"]};
            border: none;
            top: 0px;
            padding: 0px;
        }}
    """
