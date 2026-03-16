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
import threading, html
import purefunctions, functions, gui

if TYPE_CHECKING:
    pass

from various.kristofstuff import *

# ! BLASPHEMY AT STARTUP  ! #
# ! ===================== ! #

unholy_relpaths: Set = set()


def register_unholy_char(relpath: str) -> None:
    """"""
    global unholy_relpaths
    unholy_relpaths.add(relpath)
    return


def __space_startup_warning() -> None:
    """Show the 'space warning' if spaces have been detected in an opened
    project (but no other unholy characters)."""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Problem!{css['/hx']}
    <p align='left'>
        Spaces are allowed in the path leading up to your project folder, but<br>
        not in the project's file and subfolder-names themselves. Please fix<br>
        the following names:
    </p>
    <p align='left'>
    """
    # * List entries with spaces
    relpaths = list(unholy_relpaths)
    for i in range(len(relpaths)):
        name = relpaths[i].split("/")[-1]
        invalid_chars = purefunctions.get_invalid_chars(name)
        for c in invalid_chars:
            assert c == " "
        length = len(relpaths[i])
        relpath = relpaths[i].replace("&", "&amp;")
        relpath = html.escape(relpath)
        relpaths[i] = (
            f"""{css['tab']}> {css['blue']}{q}{relpath}{q}{css['end']}"""
            + "&nbsp;" * max(0, 30 - length)
        )
    if len(relpaths) > 10:
        relpaths = relpaths[0:9]
        relpaths.append(f"""{css['tab']}> {css['blue']}...{css['end']}""")
    listing = "<br>".join(relpaths) + "<br>"
    text += listing
    text += "</p>"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=f"icons/dialog/stop.png",
        title_text="Spaces in file/foldernames!",
        text=text,
    )
    return


def __blasphemy_startup_warning() -> None:
    """Show the 'blasphemy warning' when unholy characters (and spaces) have
    been detected in an opened project."""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Problem!{css['/hx']}
    <p align='left'>
        Some of your file/foldernames contain illegal characters.
    </p>
    <p align='left'>
    """

    # * List entries with unholy characters
    relpaths = list(unholy_relpaths)
    for i in range(len(relpaths)):
        name = relpaths[i].split("/")[-1]
        invalid_chars = ", ".join(
            [f"{q}{s}{q}" for s in purefunctions.get_invalid_chars(name)]
        )
        invalid_chars = invalid_chars.replace("&", "&amp;")
        invalid_chars = html.escape(invalid_chars)
        length = len(relpaths[i])
        relpath = relpaths[i]  # .replace('&', '&amp;')
        relpath = html.escape(relpath)
        relpaths[i] = str(
            f"""{css['tab']}> {css['blue']}{q}{relpath}{q}{css['end']}"""
            + "&nbsp;" * max(0, 30 - length)
            + f"""{css['tab']}illegal: {css['red']}{invalid_chars}{css['end']}"""
        )
    if len(relpaths) > 10:
        relpaths = relpaths[0:9]
        relpaths.append(f"""{css['tab']}> {css['blue']}...{css['end']}""")
    listing = "<br>".join(relpaths) + "<br>"
    text += listing
    text += "</p>"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=f"icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def blasphemy_startup_warning() -> None:
    """Show the '__blasphemy_startup_warning' or '__space_startup_warning'."""
    for relpath in list(unholy_relpaths):
        name = relpath.split("/")[-1]
        invalid_chars = purefunctions.get_invalid_chars(name)
        for c in invalid_chars:
            if c != " ":
                __blasphemy_startup_warning()
                return
    __space_startup_warning()
    return


# ! BLASPHEMY TRESSPASS WARNINGS  ! #
# ! ============================= ! #


def __refuse_operation_on_blasphemous_directory(relpath: str) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()

    text = f"""
    <p>
        You cannot add files or subfolders to this directory. The directory has
        illegal characters and/or spaces in its name or path. Please note that
        spaces are allowed in the path leading up to your project folder, but
        not in the project's file and subfolder-names themselves.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Problem!",
        text=text,
    )
    return


def __space_tresspass_warning(
    name_or_relpath: str,
    isfile: bool,
    isrelpath: bool,
) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Spaces not allowed!{css['/hx']}
    <p align='left'>
        Spaces are allowed in the path leading up to your project folder, but<br>
        not in the project's file and subfolder-names themselves.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Problem!",
        text=text,
    )
    return


def __blasphemy_tresspass_warning(
    name_or_relpath: str,
    isfile: bool,
    isrelpath: bool,
) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Warning!{css['/hx']}
    <p align='left'>
        You entered a name with illegal characters. Please give it another name.<br>
    </p>
    <p align='left'>
        NOTE:<br>
        Spaces are allowed in the path leading up to your project folder, but<br>
        not in the project's file and subfolder-names themselves.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=f"icons/dialog/stop.png",
        title_text="WARNING!",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def refuse_operation_on_blasphemous_directory(relpath: str):
    """"""
    __refuse_operation_on_blasphemous_directory(relpath)
    return


def blasphemy_tresspass_warning(name: str, isfile: bool) -> None:
    """Show when new filename or subdirname is filled in."""
    invalid_chars = purefunctions.get_invalid_chars(name)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_tresspass_warning(name, isfile, isrelpath=False)
            return
    __space_tresspass_warning(name, isfile, isrelpath=False)
    return


# ! BLASPHEMY EXISTING NAMES/RELPATHS WARNINGS  ! #
# ! =========================================== ! #


def __space_warning(
    name_or_relpath: str,
    isfile: bool,
    isrelpath: bool,
) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Problem!{css['/hx']}
    <p align='left'>
        Spaces are allowed in the path leading up to your project folder, but<br>
        not in the project's file and subfolder-names themselves.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Problem!",
        text=text,
    )
    return


def __blasphemy_warning(
    name_or_relpath: str,
    isfile: bool,
    isrelpath: bool,
) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Warning!{css['/hx']}
    <p align='left'>
        Some of your file/foldernames contain illegal characters.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Problem!",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def blasphemy_name_warning(name: str, isfile: bool) -> None:
    """Show the '__blasphemy_warning' or '__space_warning'."""
    invalid_chars = purefunctions.get_invalid_chars(name)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_warning(name, isfile, isrelpath=False)
            return
    __space_warning(name, isfile, isrelpath=False)
    return


def blasphemy_path_warning(relpath: str, isfile: bool):
    """Show the '__blasphemy_warning' or '__space_warning'."""
    invalid_chars = purefunctions.get_invalid_relpath_chars(relpath)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_warning(relpath, isfile, isrelpath=True)
            return
    __space_warning(relpath, isfile, isrelpath=True)
    return
