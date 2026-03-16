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


def show_diagnostics_help(*args) -> None:
    """"""
    h = data.get_general_font_height()
    cap_image = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/gear.png",
        width=h,
    )
    more_image = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/dialog/add.png",
        width=h,
    )
    diagnostics_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/diagnostics"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}DIAGNOSTICS{css['/hx']}
    <p align="left">
        This window shows all of the diagnostic messages from source analysis.<br>
    <p>
        <a href="{diagnostics_link}" style="color: #729fcf;">Click here</a> for more information about the <b>Diagnostics</b> window.
    </p>
    
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/stethoscope.png",
        title_text="DIAGNOSTICS",
        text=text,
        text_click_func=functions.open_url,
    )
    return
