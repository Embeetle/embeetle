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
import data, purefunctions, functions, gui, iconfunctions

if TYPE_CHECKING:
    import gui.dialogs.popupdialog


def previous_process_busy(*args) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_sorry_01.png",
        width=w * 30,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    <p align='left'>
        The previous process is still busy.<br>
        <br>
        {css['tab']}{css['tab']}{img}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Oops ...",
        text=text,
    )
    return


def cmds_file_not_attached(*args) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_sorry_01.png",
        width=w * 20,
    )
    buildBtn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/build.png",
        width=h + 5,
    )
    cleanBtn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/clean.png",
        width=h + 5,
    )
    flashBtn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/chip/flash.png",
        width=h + 5,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    <p align='left'>
        There is currently no file attached to this console.<br>
    </p>
    <p align='left'>
        Probably Embeetle is still waiting for the background<br>
        parser to finish. After that, Embeetle will attach the<br>
        file with commands to this console.<br>
        Keep an eye on the <b>progressbar</b> at the top, and try<br>
        again when it's finished.<br>
    </p>
    <p align='left'>
        If that doesn't work, then please click again on the<br>
        button that initiated this console, such as:<br>
        {css['tab']}- build button {buildBtn}<br>
        {css['tab']}- clean button {cleanBtn}<br>
        {css['tab']}- flash button {flashBtn}<br>
    </p>
    <p align='left'>
        {css['tab']}{css['tab']}{img} <br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Oops ...",
        text=text,
    )
    return


def cmds_file_not_found(*args) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_sorry_01.png",
        width=w * 30,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    <p align='left'>
        The file from which these commands were taken, cannot be found.<br>
        <br>
        {css['tab']}{css['tab']}{img}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Oops ...",
        text=text,
    )
    return
