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

import data, purefunctions, functions, gui, iconfunctions, serverfunctions


def editor_help(*args) -> None:
    """Help text shown for the editor."""
    h = data.get_general_font_height()
    ed = iconfunctions.get_rich_text_pixmap_middle(
        "icons/menu_edit/edit.png",
        width=int(1.5 * h),
    )
    editor_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/editor"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}EDITOR{css['end']}
    <p align="left">
        The {ed} <b>EDITOR</b> is where your hands type words.
    </p>
    <p align="left">
        <a href="{editor_link}" style="color: #729fcf;">Click here</a> for more information.
    </p>
    
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/menu_edit/edit.png",
        title_text="EDITOR",
        text=text,
        text_click_func=functions.open_url,
    )
    return
