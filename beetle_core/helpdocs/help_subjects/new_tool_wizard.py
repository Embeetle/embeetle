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
import os_checker
from various.kristofstuff import *


def tool_source_help(*args) -> None:
    """Help text shown for 'Tool source:'."""
    h = data.get_general_font_height()
    cloud = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/download.png",
        width=int(1.5 * h),
    )
    local = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/computer_local.png",
        width=int(1.5 * h),
    )
    css = purefunctions.get_css_tags()
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"

    text = f"""
    {css['h1']}TOOL SOURCE{css['/hx']}
    <p align="left">
        Click {cloud} <b>Download</b> to download a tool from the Embeetle<br>
        server.
    </p>
    <p align="left">
        Click {local} <b>Locate</b> to locate an existing tool on your harddrive.
    </p>
    <p align="left">
        <a href="{toolbox_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/root.png",
        title_text="TOOL SOURCE",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def select_tool_help(toolcat: str) -> None:
    """Help text shown for 'Select tool:'."""
    h = data.get_general_font_height()
    cloud = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/download.png",
        width=int(1.5 * h),
    )
    local = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/computer_local.png",
        width=int(1.5 * h),
    )
    launch_problems_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/download/problems-launching-on-windows"
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}SELECT TOOL{css['/hx']}
    <p align="left">
        The dropdown menu shows all available tools on our server<br>
        for the category:<br>
        {tab}{q}{blue}{toolcat}{end}{q}
    </p>
    <p align="left">
        In case of connection issues: Check your antivirus software. It might<br>
        be blocking Embeetle.
        <a href="{launch_problems_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/toolbox.png",
        title_text="SELECT TOOL",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def tool_parent_directory_help(*args) -> None:
    """Help text shown for 'Tool's parent directory:'."""
    h = data.get_general_font_height()
    fd = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=int(1.5 * h),
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}TOOL'S PARENT DIRECTORY{css['/hx']}
    <p align="left">
        Tell us in what folder you want the tool to end up. We recommend to put<br>
        it here:<br>
        {tab}{fd} {blue}{data.beetle_tools_directory}{end}<br>
        That's the default folder for all Embeetle tools. But feel free to put<br>
        it elsewhere.
    </p>
    <p align="left">
        It could be that the tool you're downloading already exists. In that case,<br>
        the existing tool will be deleted and replaced with the download.
    </p>
    <p align="left">
        <a href="{toolbox_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/folder.png",
        title_text=f"TOOL{q}S PARENT DIRECTORY",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def tool_executable_help(*args) -> None:
    """Help text shown for 'Tool executable:'."""
    h = data.get_general_font_height()
    folder = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=int(1.5 * h),
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}TOOL EXECUTABLE{css['/hx']}
    <p align="left">
        Tell us where the tool's executable is located. Embeetle will analyze<br>
        it.<br>
    </p>
    <p align="left">
        <a href="{toolbox_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/tools.png",
        title_text="TOOL EXECUTABLE",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def tool_directory_help(*args) -> None:
    """Help text shown for 'Tool directory:'."""
    h = data.get_general_font_height()
    folder = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=int(1.5 * h),
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}TOOL DIRECTORY{css['/hx']}
    <p align="left">
        Tell us where the tool's toplevel directory is located. Embeetle will analyze<br>
        it.<br>
    </p>
    <p>
        <a href="{toolbox_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/tools.png",
        title_text="TOOL DIRECTORY",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def tool_info_help(*args) -> None:
    """Help text shown for 'Tool info:'."""
    h = data.get_general_font_height()
    folder = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=int(1.5 * h),
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}TOOL INFO{css['/hx']}
    <p align="left">
        After analyzing your tool, Embeetle prints out everything it can extract<br>
        here. If this fails, close Embeetle and have a look at the tool in your<br>
        file explorer. Does it have permissive read and execute rights?
    </p>
    <p>
        <a href="{toolbox_link}" style="color: #729fcf;">Click here</a>
        for more information.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/tools.png",
        title_text="TOOL INFO",
        text=text,
        text_click_func=functions.open_url,
    )
    return
