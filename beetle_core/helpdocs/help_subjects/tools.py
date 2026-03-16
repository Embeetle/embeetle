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
import qt, data, purefunctions, functions, gui, iconfunctions

if TYPE_CHECKING:
    import bpathlib.tool_obj as _tool_obj_

from various.kristofstuff import *


def ask_to_download_tool(
    uid: str,
    beetle_tools_folder: str,
) -> bool:
    """"""
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    <p align="left">
        This tool is not yet on your computer:<br>
        {tab}{blue}{q}{uid}{q}{end}<br>
        <br>
        Click {q}OK{q} to download the tool into this folder:<br>
        {green}{q}{beetle_tools_folder}{q}{end}<br>
    </p>
    """
    ok, _ = gui.dialogs.popupdialog.PopupDialog.ok_cancel(
        icon_path="icons/gen/download.png",
        title_text="Download",
        text=text,
    )
    if ok != qt.QMessageBox.StandardButton.Ok:
        return False
    return True


def tool_on_path(
    toolobj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
) -> None:
    """"""
    unique_id = toolobj.get_unique_id()
    abspath = toolobj.get_abspath()
    name = toolobj.get_version_info("name")
    version = toolobj.get_version_info("version")
    suffix = toolobj.get_version_info("suffix")
    bitness = toolobj.get_version_info("bitness")
    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/tools/tool_on_path.png",
        width=h * 15,
    )
    build = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/build.png",
        width=int(h * 1.5),
    )
    flash = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/chip/flash.png",
        width=int(h * 1.5),
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    orange = css["orange"]
    end = css["end"]

    text = f"""
    {css['h3']}1. What tool is this?{css['/hx']}
    <p align="left">
        This is {name} version {version}{'' if suffix is None else (' ' + suffix)} {bitness}<br>
        The tool was found at the following location:<br>
        {tab}{blue}'{abspath}'{end}<br>
        which is part of your <b>PATH</b> environment variable.<br>
        <br>
        {tab}{tab}{img1}<br>
        The tools available in Embeetle can be managed via the <b>TOOLBOX</b> tab in<br>
        the Embeetle Home Window.
    </p>
    {css['h3']}2. How did Embeetle find this tool?{css['/hx']}
    <p align="left">
        Embeetle looks for tools at the following locations:
    </p>
    <ul>
        <li>
            The beetle_tools folder in '~/.embeetle'.<br>
            This is the default location for tools downloaded from our server.
        </li>
        <li>
            Your command search path, i.e. all folders listed in the <b>PATH</b><br>
            environment variable.
        </li>
        <li>
            Locations that are manually added to Embeetle via the <b>TOOLBOX</b>.
        </li>
    </ul>
    {css['h3']}3. How does Embeetle differentiate between tools?{css['/hx']}
    <p align="left">
        For each tool found, Embeetle extracts a unique ID representing the tool's<br>
        name, version and bitness (64b vs 32b). When you select a tool for use in<br>
        a given project, Embeetle stores this unique ID in the project. The unique<br>
        ID for this {name} tool is:<br>
        {tab}{orange}'{unique_id}'{end}
    </p>
    <p align="left">
        When you open a project, Embeetle checks if tools with matching unique IDs<br>
        are available in the toolbox. If they are not available, Embeetle gives a<br>
        warning and allows you to either download the matching tool from our server<br>
        or select a different one. This way, you will never have unexpected errors<br>
        due to changed tool versions.
    </p>
    <p align="left">
        You can check the currently selected tool versions in the dashboard or at the<br>
        bottom of the file 'dashboard_config.btl' in the '.beetle' folder in your project.
    </p>
    <p align="left">
        The tool's location is not stored in the project. This allows you to open the<br>
        project on a different computer, where the tool may be available at a different<br>
        location, and still be assured that you are using the same tool versions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/info.png",
        title_text="TOOL INFO",
        text=text,
    )
    return


def tool_external(
    toolobj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
) -> None:
    """"""
    unique_id = toolobj.get_unique_id()
    abspath = toolobj.get_abspath()
    name = toolobj.get_version_info("name")
    version = toolobj.get_version_info("version")
    suffix = toolobj.get_version_info("suffix")
    bitness = toolobj.get_version_info("bitness")
    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/tools/tool_on_path.png",
        width=h * 15,
    )
    build = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/build.png",
        width=int(h * 1.5),
    )
    flash = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/chip/flash.png",
        width=int(h * 1.5),
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    orange = css["orange"]
    end = css["end"]

    text = f"""
    {css['h3']}1. What tool is this?{css['/hx']}
    <p align="left">
        This is {name} version {version}{'' if suffix is None else (' ' + suffix)} {bitness}<br>
        The tool was found at the following location:<br>
        {tab}{blue}'{abspath}'{end}<br>
        <br>
        {tab}{tab}{img1}<br>
        The tools available in Embeetle can be managed via the <b>TOOLBOX</b> tab in<br>
        the Embeetle Home Window.
    </p>
    {css['h3']}2. How did Embeetle find this tool?{css['/hx']}
    <p align="left">
        Embeetle looks for tools at the following locations:
    </p>
    <ul>
        <li>
            The beetle_tools folder in '~/.embeetle'.<br>
            This is the default location for tools downloaded from our server.
        </li>
        <li>
            Your command search path, i.e. all folders listed in the <b>PATH</b><br>
            environment variable.
        </li>
        <li>
            Locations that are manually added to Embeetle via the <b>TOOLBOX</b>.
        </li>
    </ul>
    {css['h3']}3. How does Embeetle differentiate between tools?{css['/hx']}
    <p align="left">
        For each tool found, Embeetle extracts a unique ID representing the tool's<br>
        name, version and bitness (64b vs 32b). When you select a tool for use in<br>
        a given project, Embeetle stores this unique ID in the project. The unique<br>
        ID for this {name} tool is:<br>
        {tab}{orange}'{unique_id}'{end}
    </p>
    <p align="left">
        When you open a project, Embeetle checks if tools with matching unique IDs<br>
        are available in the toolbox. If they are not available, Embeetle gives a<br>
        warning and allows you to either download the matching tool from our server<br>
        or select a different one. This way, you will never have unexpected errors<br>
        due to changed tool versions.
    </p>
    <p align="left">
        You can check the currently selected tool versions in the dashboard or at the<br>
        bottom of the file 'dashboard_config.btl' in the '.beetle' folder in your project.
    </p>
    <p align="left">
        The tool's location is not stored in the project. This allows you to open the<br>
        project on a different computer, where the tool may be available at a different<br>
        location, and still be assured that you are using the same tool versions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/info.png",
        title_text="TOOL INFO",
        text=text,
    )
    return
