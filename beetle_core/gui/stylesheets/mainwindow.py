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
import gui.stylesheets.combobox
import gui.stylesheets.console
import gui.stylesheets.inputeditor
import gui.stylesheets.debugger
import gui.stylesheets.frame
import gui.stylesheets.groupbox
import gui.stylesheets.tabwidget
import gui.stylesheets.tabbar
import gui.stylesheets.progressbar
import gui.stylesheets.statusbar
import gui.stylesheets.textbox
import gui.stylesheets.scrollarea
import gui.stylesheets.scrollbar
import gui.stylesheets.textedit
import gui.stylesheets.splitter
import gui.stylesheets.table
import gui.stylesheets.tooltip
import gui.stylesheets.treewidget
import gui.stylesheets.menubar
import gui.stylesheets.toolbar


def get_default():
    style_sheet = """
#Form {{
    background-color: {};
    background-image: url({});
    border: none;
}}
QStatusBar::item {{
    border: none;
}}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
        """.format(
        data.theme["form_background"],
        iconfunctions.get_icon_abspath(data.theme["form_background_file"]),
        gui.stylesheets.tooltip.get_default(),
        gui.stylesheets.statusbar.get_default(),
        gui.stylesheets.button.get_toolbutton(),
        gui.stylesheets.tabwidget.get_dynamic_style(),
        gui.stylesheets.tabbar.get_scrollbutton_style(),
        # Tab-widget tab-bar scroll buttons
        gui.stylesheets.button.get_tab_scroll_stylesheet(
            "#TabScrollLeft",
            "icons/arrow/triangle/triangle_left.png",
            "icons/arrow/triangle/triangle_full_left.png",
        ),
        gui.stylesheets.button.get_tab_scroll_stylesheet(
            "#TabScrollRight",
            "icons/arrow/triangle/triangle_right.png",
            "icons/arrow/triangle/triangle_full_right.png",
        ),
        gui.stylesheets.button.get_tab_scroll_stylesheet(
            "#TabScrollDown",
            "icons/arrow/triangle/triangle_down.png",
            "icons/arrow/triangle/triangle_full_down.png",
        ).replace(
            "border-style: solid;", "border-style: solid; border-left: 0px;"
        ),
        # Search-bar
        gui.stylesheets.button.get_tab_scroll_stylesheet(
            "#SearchBarNextButton",
            "icons/arrow/triangle/triangle_down.png",
            "icons/arrow/triangle/triangle_full_down.png",
            border=False,
        ),
        # Menubar
        gui.stylesheets.menubar.get_default(),
        # Toolbar
        gui.stylesheets.toolbar.get_default(),
        # Tree-widget
        gui.stylesheets.treewidget.get_default(),
        # Scroll areas
        gui.stylesheets.scrollarea.get_default(),
        # Scrollbars
        gui.stylesheets.scrollbar.get_general(),
        # Textboxes
        gui.stylesheets.textbox.get_default(),
        # Debugger
        gui.stylesheets.debugger.get_default(),
        # TextEdit
        gui.stylesheets.textedit.get_default(),
        # Splitter
        gui.stylesheets.splitter.get_transparent_stylesheet(),
        # Table
        gui.stylesheets.table.get_default_style(),
        gui.stylesheets.console.get_default(),
        gui.stylesheets.inputeditor.get_default(),
        # Combobox
        gui.stylesheets.combobox.get_default(),
    )
    return style_sheet
