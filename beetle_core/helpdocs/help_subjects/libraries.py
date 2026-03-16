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
import data, purefunctions, functions, gui, iconfunctions
import bpathlib.path_power as _pp_

if TYPE_CHECKING:
    import gui.dialogs.popupdialog

from various.kristofstuff import *


def specific_lib_help(
    libname: str,
    libversion: str,
    libpath: str,
) -> None:
    """Show this help popup for the given library entry in the dashboard."""
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    if not data.is_home:
        if (data.current_project.get_proj_rootpath() in libpath) or (
            libpath.startswith("<project>")
        ):
            if libpath.startswith("<project>"):
                libpath = libpath.replace("<", "&#60;").replace(">", "&#62;")
            else:
                libpath = f"&#60;project&#62;/{libpath}"
            libpath = libpath.replace("//", "/")

    text = ""
    if not data.is_home:
        text = f"""
        {css['h1']}LIBRARY{css['/hx']}
        <p align="left">
            Embeetle discovered the library {green}'{libname}'{end} in your project,<br>
            thanks to the following file:<br>
            {tab}{green}'{libpath}/library.properties{end}'<br>
            This file contains everything Embeetle needs to know about this<br>
            library.
        </p>
        """
    else:
        text = f"""
        {css['h1']}LIBRARY{css['/hx']}
        <p align="left">
            Embeetle stored the library {green}'{libname}'{end} in the library<br>
            cache folder. The properties file can be found at:<br>
            {tab}{green}'{libpath}/library.properties{end}'<br>
            This file contains everything Embeetle needs to know about this<br>
            library.
        </p>
        """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/book.png",
        title_text="LIBRARY",
        text=text,
        text_click_func=nop,
    )
    return


def lib_version_help(
    libname: str,
    libversion: str,
    libpath: str,
) -> None:
    """Show this help popup for the 'version' entry in the given library."""
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    if not data.is_home:
        if (data.current_project.get_proj_rootpath() in libpath) or (
            libpath.startswith("<project>")
        ):
            if libpath.startswith("<project>"):
                libpath = libpath.replace("<", "&#60;").replace(">", "&#62;")
            else:
                libpath = f"&#60;project&#62;/{libpath}"
            libpath = libpath.replace("//", "/")

    text = f"""
    {css['h1']}LIBRARY VERSION{css['/hx']}
    <p align="left">
        Your library {green}'{libname}'{end} has version {red}'{libversion}'{end},<br>
        according to the following file:<br>
        {tab}{green}'{libpath}/library.properties'{end}<br>
    </p>
    <p align="left">
        When you click 'Check for updates', Embeetle will look online if<br>
        a newer version is available. The database Embeetle checks is freely<br>
        available at:<br>
        {tab}{blue}https://downloads.arduino.cc/libraries/library_index.json{end}<br>
    </p>
    <p align="left">
        We are open to add extra database searchpaths. In other words: Embeetle<br>
        could look for libraries also in other online locations. We can even host<br>
        an online library ourselves. Contact us if you have suggestions.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/book.png",
        title_text="LIBRARY VERSION",
        text=text,
        text_click_func=nop,
    )
    return


def most_recent_version(
    libname: str,
    libversion: str,
) -> None:
    """Tell user that his library already has the latest version."""
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_reading_happy.png",
        width=h * 8,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}Most recent version{end}
    <p align="left">
        Your library {blue}{q}{libname}{q}{end} already<br>
        has the latest version:{blue}{q}{libversion}{q}{end}<br>
        &nbsp;<br>
        {tab}{img}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/book.png",
        title_text="LIBRARY VERSION",
        text=text,
        text_click_func=nop,
        parent=data.main_form,
    )
    return


def new_version_available(
    libname: str,
    current_version: str,
    recent_version: str,
    libpath: str,
) -> Optional[str]:
    """Tell user that there is a more recent version available.

    :return: 'upgrade' => user wants to download new library. 'cancel' => user
        ignores. This function should now work for both project and stored
        libraries.
    """
    assert threading.current_thread() is threading.main_thread()

    if not data.is_home:
        if (data.current_project.get_proj_rootpath() in libpath) or (
            libpath.startswith("<project>")
        ):
            if libpath.startswith("<project>"):
                libpath = libpath.replace("<", "&#60;").replace(">", "&#62;")
            else:
                libpath = f"&#60;project&#62;/{libpath}"
            libpath = libpath.replace("//", "/")

    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/newer_library.png",
        width=h * 7,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}A newer version was found{end}
    <p align="left">
        The beetle found a newer version of your library {blue}{q}{libname}{q}{end}:<br>
        {tab}current version: {blue}{q}{current_version}{q}{end}<br>
        {tab}new version: {tab}{blue}{q}{recent_version}{q}{end}<br>
        &nbsp;<br>
        {img}<br>
    </p>
    <p align="left">
        {red}WARNING:{end}<br>
        If you upgrade your library to the newest version, the folder<br>
        {tab}{green}{q}{libpath}{q}{end}<br>
        will be overwritten. All edits to files in that folder will be<br>
        lost!<br>
    </p>
    """
    result = gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
        dialog_type="custom_buttons",
        text=text,
        title_text="LIBRARY VERSION",
        add_textbox=False,
        initial_text=None,
        text_click_func=nop,
        icon_path="icons/gen/book.png",
        selected_text=None,
        modal_style=True,
        icons=None,
        large_text=False,
        buttons=[
            (" CANCEL ", "cancel"),
            (" UPGRADE LIBRARY ", "upgrade"),
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
    if r == "upgrade":
        return "upgrade"
    if r == "cancel":
        return "cancel"
    return None


def libraries_tab_help(*args) -> None:
    """"""
    libcat_help(None)
    return


def libcat_help(libcat: Optional[str]) -> None:
    """Shown for help button at toplevel Library categories in 'LIBRARIES' tab
    in Home Window."""
    h = data.get_general_font_height()
    libcollection_dir = _pp_.rel_to_abs(
        rootpath=data.settings_directory,
        relpath="libraries",
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}LIBRARIES{css['/hx']}
    <p align='left'>
        Every library you use in Embeetle is cached into the folder:<br>
        {green}{q}{libcollection_dir}{q}{end}
    </p>
    <p align='left'>
        You can also add libraries yourself into that folder, such<br>
        that they become available in your Embeetle projects. A valid<br>
        library must have a 'library.properties' file in its toplevel<br>
        folder. The file looks like this:
    </p>
    <p align='left'>
        {tab}{blue}name{end}{red}={end}{green}My library name{end}<br>
        {tab}{blue}version{end}{red}={end}{red}1.1.0{end}<br>
        {tab}{blue}author{end}{red}={end}{green}Author name{end}<br>
        {tab}{blue}maintainer{end}{red}={end}{green}Maintainer name <support@mylibrary.com>{end}<br>
        {tab}{blue}sentence{end}{red}={end}{green}Short description.{end}<br>
        {tab}{blue}paragraph{end}{red}={end}{green}Here comes a longer description of my library.{end}<br>
        {tab}{blue}category{end}{red}={end}{green}Device Control{end}<br>
        {tab}{blue}url{end}{red}={end}{blue}https://www.my-awesome-library.com{end}<br>
        {tab}{blue}architectures{end}{red}={end}{green}avr{end}<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/book.png",
        title_text="LIBRARIES",
        text=text,
        text_click_func=nop,
    )
    return
