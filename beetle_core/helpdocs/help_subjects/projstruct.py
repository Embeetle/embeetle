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
import data, purefunctions, functions, gui, iconfunctions, serverfunctions

if TYPE_CHECKING:
    import gui.dialogs.popupdialog

from various.kristofstuff import *


def cannot_rename_rootfolder_dialog(*args) -> None:
    """"""
    h = data.get_general_font_height()
    chip_img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_with_chip.png",
        width=h * 5,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}Rename project{css['/hx']}
    <p align="left">
        You're trying to rename your project?<br>
        We're sorry .. this functionality is not yet supported in the alpha version.<br>
        As a temporary workaround: close Embeetle, rename the project folder in your file<br>
        explorer, and restart Embeetle.<br>
        <br>
        {tab}{tab}{chip_img}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Oops ...",
        text=text,
    )
    return


def cannot_delete_rootfolder_dialog(*args) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/angry_beetle.png",
        width=w * 20,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}Delete project{css['/hx']}
    <p align="left">
        Hey, you're trying to delete the whole project? That's impossible from here. Just<br>
        close Embeetle and delete the project folder.<br>
        <br>
            {tab}{tab}{img}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Oops ...",
        text=text,
    )
    return


def cannot_select_path_outside_project(selected_path: str, *args) -> None:
    """"""
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/dashboard/border_crossing.png",
        width=h * 25,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    end = css["end"]

    external_folders_text = str(
        f"{tab}{red}[no external folders defined]{end}<br>"
    )

    text = f"""
    {css['h1']}Illegal path{css['/hx']}
    <p align="left">
        The path you selected is outside your project:<br>
        {tab}{red}{q}{selected_path}{q}{end}<br>
        <br>
        Make sure you select a path inside your project folder:<br>
        {tab}{green}{q}{data.current_project.get_proj_rootpath()}{q}{end}<br>
        <br>
        Or inside one of the external folders:<br>
        {external_folders_text}<br>
        <br>
        {tab}{tab}{img}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="Illegal path",
        text=text,
    )
    return


def makefiles_together(*args) -> None:
    """"""
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/dashboard/makefiles_together.png",
        width=h * 20,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    <p align="left">
        The files {blue}{q}dashboard.mk{q}{end} and {blue}{q}filetree.mk{q}{end} are always<br>
        together with your main makefile.<br>
        <br>
        {tab}{tab}{img}<br>
        Change the location of your main makefile, and they'll follow along.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/gnu.png",
        title_text="Together is better",
        text=text,
    )
    return


def save_filetree_mk_warning(*args) -> None:
    """Show a warning when the user saves a 'filetree.mk' file in the editor."""
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/filetree/click_checkbox.png",
        width=h * 10,
    )
    selection_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/source-file-selection"
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}Your changes will be lost{css['/hx']}
    <p align="left">
        {red}WARNING{end}<br>
        Embeetle generates this {green}{q}filetree.mk{q}{end} file automatically, overwriting all<br>
        manual changes.
    </p>
    <p align="left">
        Did you intent to add source files to the build, or remove some? Click the<br>
        red and green checkboxes in the Filetree and select {q}Force include{q} or {q}Force<br>
        exclude{q}:<br>
        {img}<br>
    </p>
    <p align="left">
        After doing this, the file will be forced into this {green}{q}filetree.mk{q}{end} or deleted<br>
        from it respectively. <a href="{selection_link}" style="color: #729fcf;">Click here</a> to learn more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="Your changes will be lost",
        text=text,
        text_click_func=functions.open_url,
    )
    return
