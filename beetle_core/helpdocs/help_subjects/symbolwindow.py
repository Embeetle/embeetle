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

import purefunctions, functions, serverfunctions, gui


def symbol_window_hamburger_help(*args) -> None:
    """Help text shown for the symbol window hamburger menu."""
    symbols_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/symbols"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}SYMBOLS{css['/hx']}
    <p align="left">
        This window shows all of the symbols in the currently processed files.<br>
        Use it for quick navigation through symbols. Click on a symbol to set<br>
        focus to the file and line where it is located.
    </p>
    <p align="left">
        <a href="{symbols_link}" style="color: #729fcf;">Click here</a> for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/balls.png",
        title_text="SYMBOLS",
        text=text,
        text_click_func=functions.open_url,
    )
    return
