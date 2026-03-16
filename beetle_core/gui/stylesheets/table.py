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


def get_default_style():
    border_width = 1
    padding = 0
    spacing = 0
    return f"""
QTableView QLineEdit {{
    background: {data.theme["indication"]["selection"]};
    border: 1px solid {data.theme["table_grid"]};
    color: {data.theme["fonts"]["default"]["color"]};
}}

QTableView {{
    background-color: {data.theme["fonts"]["default"]["background"]};
    color: {data.theme["fonts"]["default"]["color"]};
    selection-background-color: {data.theme["indication"]["selection"]};
    border: {border_width}px solid {data.theme["table_grid"]};
    border-collapse: collapse;
    gridline-color: {data.theme["table_grid"]};
    padding: {padding}px;
    spacing: {spacing}px;
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
}}
QTableView QTableCornerButton::section {{
    background: {data.theme["fonts"]["default"]["background"]};
    border: none;
}}

QTableView::item {{
    border: none;
    color: {data.theme["fonts"]["default"]["color"]};
}}
QTableView::item:selected {{
    background-color: {data.theme["indication"]["selection"]};
    color: {data.theme["fonts"]["default"]["color"]};
}}
QTableView::item:disabled {{
    background-color: {data.theme["fonts"]["disabled"]["background"]};
    color: {data.theme["fonts"]["disabled"]["color"]};
}}

QHeaderView {{
    background-color: {data.theme["table_header"]};
    color: {data.theme["fonts"]["default"]["color"]};
}}
QHeaderView::section {{
    border-style: none;
    border-right: 1px solid {data.theme["table_grid"]};
    border-bottom: 1px solid {data.theme["table_grid"]};
    background-color: {data.theme["table_header"]};
    color: {data.theme["fonts"]["default"]["color"]};
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
}}
    """


def get_library_style():
    stylestr = get_default_style()
    stylestr += """
QTableWidget {
    background-color: #ffffff;
    color: #000000;
}
QTableWidget::item:hover {
    background-color: #d5e1f0;
}
QTableWidget::item:focus {
    background-color: #729fcf;
    color:#000000;
}
QTableWidget::item:focus:hover {
    background-color: #427bc3;
    color: #ffffff;
}
    """
    return stylestr
