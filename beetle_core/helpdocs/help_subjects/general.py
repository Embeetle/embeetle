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
import qt, data, gui, threading, functions, purefunctions, html, iconfunctions

if TYPE_CHECKING:
    pass

from various.kristofstuff import *


def beetle_busy(*args) -> None:
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
        Please give him a moment.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="Attention!",
        text=text,
    )
    return


def save_failed(explain: str = "") -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/burning_disk.png",
        width=h * 16,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Attention!{css['/hx']}
    <p align="left">
        Saving your Embeetle project failed!<br>
        <br>
        {img1}<br>
        <br>
        {explain}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/save/save_all.png",
        title_text="Save failure!",
        text=text,
    )
    return


def what_kind_of_building() -> Optional[str]:
    """Explain user the difference between inline and shadow building. Then ask
    him what he does.

    :return: 'inline', 'shadow' or None
    """
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/tools/building.png",
        width=h * 10,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    text = f"""
    {css['h1']}How do you build your project?{css['/hx']}
    <p align="left">
        There are - roughly speaking - two ways to build your project: <b>shadow<br>
        building</b> and <b>inline building</b>.<br>
        {img1}<br>
    </p>
    {css['h2']}1. Inline building{css['/hx']}
    <p align="left">
        All build artefacts (object files, elf file, ...) end up among the source<br>
        files. For example: 'foo.o' is built next to 'foo.c'. The result is often<br>
        not so clean. However, the makefile is generally a bit simpler.
    </p>
    {css['h2']}2. Shadow building{css['/hx']}
    <p align = "left">
        With shadow building, the build artefacts (object files, elf file, ...)<br>
        are created in a separate folder. For example, the object file produced<br>
        by compiling {green}'foo/bar.c'{end} will be {green}'build/foo/bar.o'{end}.
    </p>
    <p align = "left">
        {tab}<br>
        What about your makefile?<br>
        {tab}
    </p>
    """
    result = gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
        dialog_type="custom_buttons",
        text=text,
        title_text="How do you build your project?",
        add_textbox=False,
        initial_text=None,
        text_click_func=nop,
        icon_path="icons/gen/build.png",
        selected_text=None,
        modal_style=True,
        icons=None,
        large_text=False,
        buttons=[
            (" INLINE BUILDING ", "inline"),
            (" SHADOW BUILDING ", "shadow"),
        ],
        parent=data.main_form,
    )
    if result is None:
        return None
    if not isinstance(result, tuple):
        return None
    r = result[0]
    if r is None:
        return None
    if not isinstance(r, str):
        return None
    if r == "inline":
        return "inline"
    if r == "shadow":
        return "shadow"
    return None


def do_manual_selection(unicum_name: str, isfile: bool) -> bool:
    """Explain user the difference between toplevel source folder and otherwise.

    Then ask him what applies.
    """
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    css = purefunctions.get_css_tags()
    green = css["green"]
    end = css["end"]

    text = f"""
    <p align="left">
        Autolocation for {green}{unicum_name}{end} failed. Would you like to select the {'file' if isfile else 'folder'}<br>
        yourself?
    </p>
    """
    result = gui.dialogs.popupdialog.PopupDialog.question(
        title_text="Autolocation failed",
        icon_path="icons/dialog/warning.png",
        text=text,
        parent=data.main_form,
    )
    if result == qt.QMessageBox.StandardButton.Yes:
        return True
    return False
