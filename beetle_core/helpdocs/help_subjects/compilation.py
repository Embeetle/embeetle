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

from __future__ import annotations
from typing import *
import threading
import qt, data, purefunctions, iconfunctions, gui

if TYPE_CHECKING:
    import gui.dialogs.popupdialog


def cannot_create_builddir(*args) -> None:
    """"""
    text = f"""
    <p>
        There is no build directory. Embeetle tried to create one, but<br>
        failed.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="Oops ...",
        text=text,
    )
    return


def where_is_builddir(*args) -> None:
    """"""
    text = f"""
    <p>
        Where is the build directory? Specify its location in the Dashboard.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="Oops ...",
        text=text,
    )
    return


def beetle_busy_yes_no(question: str) -> bool:
    """"""
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_busy.png",
        width=h * 26,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Attention!{css['/hx']}
    <p align="left">
        The beetle is busy.<br>
        <br>
        {img1}<br>
        <br>
        {question}<br>
    </p>
    """
    reply = gui.dialogs.popupdialog.PopupDialog.question(
        icon_path="icons/dialog/warning.png",
        title_text="Attention!",
        text=text,
    )
    if reply == qt.QMessageBox.StandardButton.Yes:
        return True
    return False
