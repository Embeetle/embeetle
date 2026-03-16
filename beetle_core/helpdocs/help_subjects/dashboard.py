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
import os
import qt, data, gui, functions, iconfunctions
import gui.helpers.various
import hardware_api.chip_unicum as _chip_unicum_
import bpathlib.path_power as _pp_
import hardware_api.treepath_unicum as _treepath_unicum_
import purefunctions
import serverfunctions

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import project.segments.chip_seg.chip as _chip_
    import project.segments.board_seg.board as _board_
    import project.segments.probe_seg.probe as _probe_
    import bpathlib.treepath_obj as _treepath_obj_
from various.kristofstuff import *

# ^                      TOPLEVEL DASHBOARD HELP DIALOGS                       ^#
# % ========================================================================== %#
# % Help dialogs for the dashboard itself and all its toplevel entries.        %#
# %                                                                            %#


def dashboard_help(*args) -> None:
    """Help text shown for the dashboard cogging wheel context menu."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    dashboard_img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/dashboard/dashboard_intro.png",
        width=w * 70,
    )
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}DASHBOARD{css['/hx']}
    <p align="left">
        The dashboard gives you an overview on the configurations of your project.<br>
        Practically, this means that the dashboard keeps an eye on all the config<br>
        files:<br>
        {dashboard_img}<br>
        <br>
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/dashboard.png",
        title_text="DASHBOARD",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!================================[ 1. BOARD ]================================!#
def board_help(board: Optional[_board_.Board] = None) -> None:
    """Shown for help button at toplevel 'BOARD' entry in Dashboard.

    Also shown for the Board Device entry.
    """
    if board is None:
        board = data.current_project.get_board()
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    board_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath=board.get_board_dict()["icon"],
        width=h,
    )
    boardname = board.get_board_unicum().get_name()
    board_link = board.get_board_dict()["link"]
    board_link_comment = ""
    if board_link is not None:
        board_link_comment = f"""
        <p>
            <a href={board_link} style="color: #729fcf;">Click here</a> for more information about this particular board<br>
            on our website.<br>
        </p>
        """
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#board"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}BOARD{css['/hx']}
    <p align="left">
        You've selected the {board_icon} <b>{boardname}</b> board.
    </p>
    {board_link_comment}
    <p>
        <a href={dashboard_link} style="color: #729fcf;">Click here</a> for more information about the board section in<br>
        the dashboard.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/board/custom_board.png",
        title_text="BOARD",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!===========================[ 2. MICROCONTROLLER ]===========================!#
def chip_help(chip: Optional[_chip_.Chip] = None) -> None:
    """Shown for help button at toplevel 'MICROCONTROLLER' entry in Dashboard.

    Also shown for the Microcontroller Device entry.
    """
    if chip is None:
        chip = data.current_project.get_chip()
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    chip_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath=chip.get_chip_dict(board=None)["icon"],
        width=h,
    )
    chipname = chip.get_chip_unicum().get_name()
    chip_link = chip.get_chip_dict(board=None)["link"]
    chip_link_comment = ""
    if chip_link is not None:
        chip_link_comment = f"""
        <p align="left">
            <a href="{chip_link}" style="color: #729fcf;">Click here</a> for more information about this particular microcontroller<br>
            on our website.<br>
        </p>
        """
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#chip"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}MICROCONTROLLER{css['/hx']}
    <p align="left">
        You've selected the {chip_icon} <b>{chipname}</b> microcontroller.
    </p>
    {chip_link_comment}
    <p align="left">
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> for more information about the microcontroller section in<br>
        the dashboard.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/chip/chip.png",
        title_text="MICROCONTROLLER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!================================[ 3. PROBE ]================================!#
def probe_help(probe: Optional[_probe_.Probe]) -> None:
    """Shown for help button at probe in Dashboard."""
    if probe is None:
        probe = data.current_project.get_probe()
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    probe_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath=probe.get_probe_dict()["icon"],
        width=h,
    )
    probe_link = probe.get_probe_dict()["link"]
    probe_link_comment = ""
    if (probe_link is not None) and (probe_link.lower() != "none"):
        probe_link_comment = f"""
        <p>
            <a href="{probe_link}" style="color: #729fcf;">Click here</a> for more information about this particular probe<br>
            on our website.<br>
        </p>
        """
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#probe"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}PROBE{css['/hx']}
    <p align="left">
        You're currently using the {probe_icon} <b>{probe.get_name()}</b> probe.
    </p>
    <p>
        A probe is used to flash the code to your microcontroller. The probe can either<br>
        be a separate device, or it can be a part of your microcontroller board.<br>
    </p>
    {probe_link_comment}
    <p>
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> for more information about the probe section in<br>
        the dashboard.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/probe/probe.png",
        title_text="PROBE",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!================================[ 4. TOOLS ]================================!#
def tools_help(*args) -> None:
    """Shown for help button at Tools in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#tools"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}TOOLS{css['/hx']}
    <p align="left">
        In the context of microcontrollers, <b>Tools</b> are programs to build source code into a <br>
        binary/executable and flash it to the microcontroller. They typically run in a console<br>
        (no graphical user interface).<br>
    </p>
    <p>
        But wait a minute. The tools are invoked from your makefile. How on earth can Embeetle know<br>
        - let alone enforce - the tools that are being used? <a href='dashboard_tools' style="color: #729fcf;">Click here</a> to find out.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/tools.png",
        title_text="TOOLS",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!===========================[ 5. PROJECT LAYOUT ]============================!#
def treepaths_help(*args) -> None:
    """Shown for help button at Project Layout in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    config_escape = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/dashboard/config_escape.png",
        width=40 * w,
    )
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#layout"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}PROJECT LAYOUT{css['/hx']}
    <p align="left">
        All the config files (makefile, linkerscript, ...) are somewhere in your project folder.<br>
        But Embeetle needs to know where exactly!<br>
        <br>
        {config_escape}<br>
        <br>
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read how the dashboard keeps track of all the config files.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/tree.png",
        title_text="PROJECT LAYOUT",
        text=text,
        text_click_func=functions.open_url,
    )
    return


#!==============================[ 6. LIBRARIES ]==============================!#
def lib_help(*args) -> None:
    """Shown for help button at toplevel 'Libraries' entry in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    nr_of_libs = data.current_project.get_lib_seg().get_nr_of_libraries()
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    if nr_of_libs == 0:
        text = f"""
            {css['h1']}LIBRARIES{css['/hx']}
            <p align="left">
                Embeetle did not discover any libraries in your project. A<br>
                library must have a {green}'library.properties'{end} file in its toplevel<br>
                folder to be valid and recognized by Embeetle. The file can look<br>
                like this:
            </p>
            <p align="left">
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
    else:
        text = f"""
            {css['h1']}LIBRARIES{css['/hx']}
            <p align="left">
                Embeetle discovered a few libraries in your project:<br>
        """
        for name in data.current_project.get_lib_seg().list_library_names():
            text += f"{tab}- {green}{name}{end}<br>"
        text += "</p>"

    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/books.png",
        title_text="LIBRARIES",
        text=text,
        text_click_func=nop,
    )
    return


# ^                      SPECIFIC DASHBOARD HELP DIALOGS                       ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


def memregion_help(memregion: _chip_.MemRegion) -> None:
    """"""
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#chip"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Memory region {memregion.get_name()}{css['/hx']}
    <p align="left">
        Embeetle parses your linkerscript to discover the memory regions<br>
        defined for the microcontroller. After building, Embeetle attempts to<br>
        determine the memory usage from the elf-file.
    </p>
    <p align="left">
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    """
    iconpath = ""
    if memregion.get_memtype() is _chip_unicum_.MEMTYPE.FLASH:
        iconpath = "icons/memory/memory_orange_many.png"
    else:
        iconpath = "icons/memory/memory_green_many.png"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=iconpath,
        title_text=f"Memory region {memregion.get_name()}",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def memsection_to_clipboard(
    memsection: _chip_.MemSection,
    memregion: _chip_.MemRegion,
    attribute_text: str,
) -> None:
    """Help text shown for a particular memsection."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    clb = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/menu_edit/paste.png",
        width=h + 5,
    )
    memsec_name = memsection.get_name()
    assert attribute_text == f"__attribute__((section({dq}{memsec_name}{dq})))"
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    def catch_click(key, parent=None):
        funcs = {
            "more_info": memsection_help,
        }
        funcs[key](memsection, memregion, attribute_text)
        return

    text = f"""
    <p align="left">
        The following string is added to your clipboard {clb} :<br>
    </p>
    <p align="left">
        {tab}{blue}__attribute__(({end}{red}section({end}{green}&#34;{memsec_name}&#34;{end}{red}){end}{blue})){end}<br>
    </p>
    <p align="left">
        <a href="more_info" style="color: #729fcf;">Click here</a> for how to use it in your code.<br>
    </p>
    """
    iconpath = ""
    if memregion.get_memtype() is _chip_unicum_.MEMTYPE.FLASH:
        iconpath = "icons/memory/memory_orange_many.png"
    else:
        iconpath = "icons/memory/memory_green_many.png"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=iconpath,
        title_text=f"Memory section {memsec_name}",
        text=text,
        text_click_func=catch_click,
    )
    return


def memsection_help(
    memsection: _chip_.MemSection,
    memregion: _chip_.MemRegion,
    attribute_text: str,
) -> None:
    """More info shown for a particular memsection."""
    memsec_name = memsection.get_name()
    css = purefunctions.get_css_tags()
    cb1 = "{"
    cb2 = "}"
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    if (memsection.get_memregion_storage() is memregion) and (
        memsection.get_memregion_runtime() is memregion
    ):
        memsection_def_a = str(
            f"{tab}{cb2} > {red}{memregion.get_name()}{end}<br>"
        )
        memsection_def_b = str(
            f"{red}{memregion.get_name()}{end} memory region.<br>"
        )
    else:
        memsection_def_a = str(
            f"{tab}{cb2} > {red}{memsection.get_memregion_runtime().get_name()}{end} "
            f"AT> {red}{memsection.get_memregion_storage().get_name()}{end}"
            f"<br>"
        )
        memsection_def_b = str(
            f"{red}{memsection.get_memregion_runtime().get_name()}{end} memory "
            f"region, but it{q}s stored in the "
            f"{red}{memsection.get_memregion_storage().get_name()}{end} region"
            f"<br>"
        )

    text = f"""
    <p align="left">
        You{q}ve defined the memory section {green}{memsec_name}{end} in the {red}SECTIONS{cb1}..{cb2}{end}<br>
        part of your linkerscript, like this:<br>
        <br>
        {tab}<b>{green}{memsec_name}{end} :</b><br>
        {tab}{cb1}<br>
        {tab}{tab}*({green}{memsec_name}{end}*);<br>
        {tab}{tab}...<br>
        {memsection_def_a}<br>
    </p>
    <p align="left">
        This means that all code or data belonging to this memory section ends up in the<br>
        {memsection_def_b}<br>
        But how do you know to what sections your code or data belongs to? Normally the<br>
        compiler decides himself. Most code belongs to the {green}.text{end} section, while data is<br>
        mapped on the {green}.data{end} section. Uninitialized data (all zeros at startup) gets mapped<br>
        on the {green}.bss{end} section.<br>
        You're free to define your own memory sections, and you can force the compiler to<br>
        put some code or data in it.<br>
        For example:<br>
        <br>
        {tab}<b>{green}.mysection{end} :</b><br>
        {tab}{cb1}<br>
        {tab}{tab}*({green}.mysection{end}*);<br>
        {tab}{tab}...<br>
        {tab}{cb2} > {red}DTCMRAM{end} AT> {red}FLASH{end}<br>
    </p>
    <p align="left">
        This section ends up in {red}DTCMRAM{end} but is stored in {red}FLASH{end}. To force a variable<br>
        in your code to {green}.mysection{end}, you should add a <i>compiler directive</i> into its declaration:<br>
        <br>
        {tab}{blue}__attribute__(({end}{red}section({end}{green}&#34;.mysection&#34;{end}{red}){end}{blue})){end} {blue}uint32_t{end} myvar;<br>
        <br>
        You can also force a function into {green}.mysection{end}, like so:<br>
        <br>
        {tab}{blue}__attribute__(({end}{red}section({end}{green}&#34;.mysection&#34;{end}{red}){end}{blue})){end} {blue}int{end} myfunc();<br>
        {tab}{cb1}<br>
        {tab}{tab}{green}/* do stuff */{end}<br>
        {tab}{tab}{red}return{end} 1;<br>
        {tab}{cb2}<br>
    </p>
    """
    iconpath = ""
    if memregion.get_memtype() is _chip_unicum_.MEMTYPE.FLASH:
        iconpath = "icons/memory/memory_orange_many.png"
    else:
        iconpath = "icons/memory/memory_green_many.png"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=iconpath,
        title_text=f"Memory section {memsec_name}",
        text=text,
    )
    return


def probe_transport_protocol_help(
    probe: Optional[_probe_.Probe] = None,
) -> None:
    """Shown for help button at Transport Protocol in Dashboard."""
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Transport Protocol{css['/hx']}
    <p align="left">
        Select the transport protocol for your probe. This is the<br>
        communication protocol used between the probe and the<br>
        microcontroller. The incompatible ones are red.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/chip/chip_protocol.png",
        title_text="TRANSPORT PROTOCOL",
        text=text,
    )
    return


def probe_comport_help(*args) -> None:
    """Shown for help button at COM-port in Dashboard."""
    probe = data.current_project.get_probe()
    data.serial_port_data = functions.list_serial_ports()
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    probe_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath=probe.get_probe_dict()["icon"],
        width=h,
    )
    probe_link = probe.get_probe_dict()["link"]
    probe_link_comment = ""
    if (probe_link is not None) and (probe_link.lower() != "none"):
        probe_link_comment = f"""
            <a href="{probe_link}" style="color: #729fcf;">Click here</a> for more information about this particular probe<br>
            on our website.<br>
        """
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    text = f"""
    {css['h1']}PROBE FLASH PORT{css['/hx']}
    <p align="left">
        You're currently using the {probe_icon} <b>{probe.get_name()}</b> probe.<br>
        {probe_link_comment}
    </p>
    """
    # $ No COM-port selected
    if (probe.get_comport_name() is None) or (
        probe.get_comport_name().lower() == "none"
    ):
        text += f"""
        <p align="left">
            You have not selected a Flash Port yet.
        </p>
        """
    # $ COM-port selected and present in dataset
    elif probe.get_comport_name() in data.serial_port_data:
        comport_datastruct = data.serial_port_data[probe.get_comport_name()]
        info = ""
        for key, value in comport_datastruct.items():
            _key_ = key + "&nbsp;" * (14 - len(key))
            info += f"{tab}{_key_}:&nbsp;{green}{value}{end}<br>"
        text += f"""
        <p align="left">
            The selected Flash Port is: {green}{probe.get_comport_name()}{end}<br>
            <br>
            {info}
        </p>
        """

    # $ COM-port selected, but not present in dataset (disconnected)
    else:
        text += f"""
        <p>
            The selected Flash Port is: {green}{probe.get_comport_name()}{end}<br>
            Embeetle can no longer detect this Flash Port. Did you disconnect
            the probe?
        </p>
        """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/console/serial_monitor.png",
        title_text="PROBE FLASH PORT",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def buildautomation_help(*args) -> None:
    """Shown for help button at Tools > Build automation in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    build_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build"
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    download_link = f"{serverfunctions.get_base_url_wfb()}/#embedded-dev/software/dev-tools/downloads#gcc"
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}BUILD AUTOMATION{css['/hx']}
    <p align="left">
        A build automation tool automates the building of your project. The most popular one - and<br>
        currently the only one supported by Embeetle - is <b>GNU Make</b>. It runs commands from recipees<br>
        in the <b>makefile</b> based on which source files have changed.<br>
        <a href="{build_link}" style="color: #729fcf;">Click here</a> for more info about the build procedure in Embeetle.
    </p>
    <p align="left">
        You can download several versions of GNU Make in the <b>TOOLBOX</b> tab in the Home Window.<br>
        By default they end up in the 'beetle_tools' folder in '~/.embeetle'. You<br>
        can also download them directly from several sources on the internet, and then add them<br>
        to Embeetle (The Embeetle <b>TOOLBOX</b> provides a way to assign locally installed tools).<br>
        - {tab}<a href={toolbox_link} style="color: #729fcf;">Click here</a> for more info about the Embeetle <b>TOOLBOX</b><br>
        - {tab}<a href={download_link} style="color: #729fcf;">Click here</a> for more info about where to download GNU Make outside Embeetle.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/build_automation.png",
        title_text="BUILD AUTOMATION",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def toolchain_help(*args) -> None:
    """Shown for help button at Tools > Toolchain in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    build_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build"
    )
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    download_link = f"{serverfunctions.get_base_url_wfb()}/#embedded-dev/software/dev-tools/downloads#gcc"
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}COMPILER TOOLCHAIN{css['/hx']}
    <p align="left">
        As the name indicates, the <b>compiler toolchain</b> is a collection of <b>tools</b> that can be<br>
        chained together to complete a task: building the source code into a binary/executable.<br>
        It consists of a cross-compiler, linker, debugger and other tools.<br>
        <a href="{build_link}" style="color: #729fcf;">Click here</a> for more info about the build procedure in Embeetle.
    </p>
    <p>
        The compiler toolchain must be compatible with your microcontroller. For example: ARM-based<br>
        microcontrollers need a different toolchain from RISC-V based devices.
    </p>
    <p>
        You can download toolchains in the <b>TOOLBOX</b> tab in the Home Window. By default they end<br>
        up in the 'beetle_tools' folder in '~/.embeetle'. You can also download the<br>
        toolchains directly from their official webpages, and then add them to Embeetle (The Embeetle<br>
        <b>TOOLBOX</b> provides a way to assign locally installed tools).<br>
        - {tab}<a href="{toolbox_link}" style="color: #729fcf;">Click here</a> for more info about the Embeetle <b>TOOLBOX</b><br>
        - {tab}<a href="{download_link}" style="color: #729fcf;">Click here</a> for more info about where to download toolchains outside Embeetle.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/tools.png",
        title_text="COMPILER TOOLCHAIN",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def flashtool_help(*args) -> None:
    """Shown for help button at Tools > Flashtool in Dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"
    download_link = f"{serverfunctions.get_base_url_wfb()}/#embedded-dev/software/dev-tools/downloads#gcc"
    flash_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash"
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}FLASHTOOL{css['/hx']}
    <p align="left">
        A <b>flashtool</b> is a program that runs on your computer and serves as an 'interface'<br>
        between the computer and the microcontroller. A debugger (such as GNU GDB) can hook into this<br>
        server and send it a binary to be flashed to the microcontroller. The most popular flash debug<br>
        servers are <b>OpenOCD</b> and <b>PyOCD</b>.<br>
        <a href="{flash_link}" style="color: #729fcf;">Click here</a> for more info about the flash procedure in Embeetle.
    </p>
    <p align="left">
        You can download several versions of OpenOCD or PyOCD in the <b>TOOLBOX</b> tab in the Home Window.<br>
        By default they end up in the 'beetle_tools' folder in '~/.embeetle'. You can<br>
        also download them directly from several sources on the internet, and then add them to Embeetle<br>
        (The Embeetle <b>TOOLBOX</b> provides a way to assign locally installed tools).<br>
        - {tab}<a href="{toolbox_link}" style="color: #729fcf;">Click here</a> for more info about the Embeetle <b>TOOLBOX</b><br>
        - {tab}<a href="{download_link}" style="color: #729fcf;">Click here</a> for more info about where to download OpenOCD/PyOCD outside Embeetle.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/tools/flashtool.png",
        title_text="FLASHTOOL",
        text=text,
        text_click_func=functions.open_url,
    )
    return


# ^                                  WARNINGS                                  ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


def chip_swap_warning(chip: Optional[_chip_.Chip] = None) -> Optional[str]:
    """Show warning when user attempts to swap the chip."""
    if chip is None:
        chip = data.current_project.get_chip()
    chipname = chip.get_chip_unicum().get_name()
    if (chipname is None) or (chipname.lower() == "none"):
        # No need to show a warning. Just continue.
        return "continue"
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    chip_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath=chip.get_chip_dict(board=None)["icon"],
        width=h,
    )
    board_icon = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/board/custom_board.png",
        width=h,
    )
    # Because the none-chip is already filtered above, the link given here should be an existing
    # one.
    chip_link = chip.get_chip_dict(board=None)["link"]
    config_fig = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/dashboard/config_changes.png",
        width=10 * h,
    )
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}MICROCONTROLLER{css['/hx']}
    <p align='left'>
        You're currently working on the {chip_icon} <b>{chipname}</b> microcontroller.<br>
        <a href="{chip_link}" style="color: #729fcf;">Click here</a> for more information about this particular microcontroller<br>
        on our website.<br>
    </p>
    {css['h2']}Changing microcontroller{css['/hx']}
    <p align='left'>
        Before changing the microcontroller, you should realize that Embeetle<br>
        only adapts the config files:<br>
    </p>
    {config_fig}
    <p align='left'>
        Embeetle doesn't touch the source code. You risk to end up with a hybrid<br>
        monster: source code for one chip and config files for another.
    </p>
    {css['h2']}What should I do?{css['/hx']}
    <p align='left'>
        Until we have implemented a better solution, you can do the following:<br>
        <ul>
            <li>
                Click the 'CANCEL' button below to cancel the microcontroller<br>
                switch.<br>
            <li>
                Go back to the Home Window (home-button in top-left corner) and<br>
                create a new project for the microcontroller you want to switch to.<br>
            </li>
            <li>
                Copy your 'user code' from this project into the new project.<br>
            </li>
        </ul>
    </p>
    """

    result = gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
        dialog_type="custom_buttons",
        text=text,
        title_text="WARNING",
        add_textbox=False,
        initial_text=None,
        text_click_func=functions.open_url,
        icon_path="icons/chip/chip.png",
        selected_text=None,
        modal_style=True,
        icons=None,
        large_text=False,
        buttons=[
            (" CANCEL ", "cancel"),
            (" DO IT ANYWAY ", "continue"),
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
    if r == "continue":
        return "continue"
    if r == "cancel":
        return "cancel"
    return None


def cannot_parse_elf_file(elf_abspath: str, error_txt: str) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    chip_img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_with_chip.png",
        width=w * 10,
    )
    clean = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/clean.png",
        width=h + 5,
    )
    build = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/build.png",
        width=h + 5,
    )
    error_txt = error_txt.replace("\n", "<br>")
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    <p align="left">
        Sorry, Embeetle could not parse the elf-file at <br>
        {blue}{elf_abspath}{end} <br>
        <br>
        {tab}{tab}{chip_img} <br>
        <br>
        The beetle advices you to:<br>
        {tab}- Check the .elf filepath in the dashboard <b>Project Layout</b> > BUILD_DIR > ELF_FILE<br>
        {tab}- Clean {clean} and rebuild {build} the project. <br>
        <br>
        Error details: <br>
        <br>
        {red}{error_txt}{end}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Oops ...",
        text=text,
    )
    return


# ^                            DASHBOARD PERMISSION                            ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


def ask_dashboard_permission(
    addperm_dict: Dict,
    delperm_dict: Dict,
    modperm_dict: Dict,
    repperm_dict: Dict,
    title_text: Optional[str],
    callback: Optional[Callable],
) -> None:
    """Ask permission before doing any changes in the config files.

    This function returns the same dictionaries that are given as parameters,
    with the 'permission_granted' booleans filled in: > callback( addperm_dict,
    delperm_dict,       modperm_dict,       repperm_dict, diff_dialog,   )

    If user cancels the dialog, this is returned: > callback(None, None, None,
    None, None)
    """
    diff_dialog: Optional[gui.helpers.various.DiffDialog] = None
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    orange = css["orange"]
    end = css["end"]

    def catch_click(key: str, parent=None):
        def show_differ(_k):
            nonlocal diff_dialog
            if diff_dialog is not None:
                diff_dialog.close()
            cur_cont = modperm_dict[_k][4]
            res_cont = modperm_dict[_k][5]
            diff_dialog = gui.helpers.various.create_standalone_diff(
                parent=parent,
                title="FILE DIFFER",
                icon="icons/gen/computer.png",
                text_1=cur_cont,
                text_2=res_cont,
                text_name_1="Current content",
                text_name_2="Merged content",
            )
            return

        if key.startswith("diff_"):
            show_differ(key.replace("diff_", "", 1))
        return

    projObj = data.current_project
    h = data.get_general_font_height()
    files_to_modify_tuples = []
    files_to_add_tuples = []
    files_to_delete_tuples = []
    files_to_repoint_tuples = []

    for k in addperm_dict.keys():
        treepath_unicum: _treepath_unicum_.TREEPATH_UNIC = (
            _treepath_unicum_.TREEPATH_UNIC(k)
        )
        filepath = addperm_dict[k][0]
        diff = addperm_dict[k][1]
        perm = addperm_dict[k][2]
        assert diff == ""
        txt = filepath.split("/")[-1]
        files_to_add_tuples.append(
            (
                treepath_unicum.get_dict()["icon"].replace(".png", "(add).png"),
                txt,
                False,
                "",
                perm,
            )
        )

    for k in delperm_dict.keys():
        treepath_unicum: _treepath_unicum_.TREEPATH_UNIC = (
            _treepath_unicum_.TREEPATH_UNIC(k)
        )
        filepath = delperm_dict[k][0]
        diff = delperm_dict[k][1]
        perm = delperm_dict[k][2]
        assert diff == ""
        txt = filepath.split("/")[-1]
        files_to_delete_tuples.append(
            (
                treepath_unicum.get_dict()["icon"].replace(".png", "(del).png"),
                txt,
                False,
                "",
                perm,
            )
        )

    for k in modperm_dict.keys():
        treepath_unicum: _treepath_unicum_.TREEPATH_UNIC = (
            _treepath_unicum_.TREEPATH_UNIC(k)
        )
        filepath = modperm_dict[k][0]
        diff = modperm_dict[k][1]
        perm = modperm_dict[k][2]
        confl = modperm_dict[k][3]
        man_mod = modperm_dict[k][6]
        assert diff != ""
        txt = filepath.split("/")[-1]
        if confl:
            err = iconfunctions.get_rich_text_pixmap(
                pixmap_relpath="icons/dialog/warning.png",
                width=h,
            )
            txt += (
                f"&nbsp; &nbsp;&nbsp;&nbsp;{err}&nbsp;{red}Merge conflicts{end}"
            )
        elif man_mod:
            warn = iconfunctions.get_rich_text_pixmap(
                pixmap_relpath="icons/dialog/warning.png",
                width=h,
            )
            txt += f"&nbsp; &nbsp;&nbsp;&nbsp;{warn}&nbsp;{orange}Manual changes{end}"
        files_to_modify_tuples.append(
            (
                treepath_unicum.get_dict()["icon"].replace(
                    ".png", "(merge).png"
                ),
                txt,
                True,
                f'<a href={q}diff_{k}{q} style="color: #729fcf;">{diff}</a>',
                perm,
            )
        )

    for k in repperm_dict.keys():
        treepath_unicum: _treepath_unicum_.TREEPATH_UNIC = (
            _treepath_unicum_.TREEPATH_UNIC(k)
        )
        frompath = repperm_dict[k][0]
        topath = repperm_dict[k][1]
        perm = repperm_dict[k][2]
        rootpath = projObj.get_proj_rootpath()
        if (frompath is None) or (frompath == "None"):
            frompath_rel = f"{q}None{q}"
        else:
            frompath_rel = f"{q}{_pp_.abs_to_rel(rootpath=os.path.dirname(rootpath), abspath=frompath)}{q}"
        if (topath is None) or (topath == "None"):
            topath_rel = f"{q}None{q}"
        else:
            topath_rel = f"{q}{_pp_.abs_to_rel(rootpath=os.path.dirname(rootpath), abspath=topath)}{q}"
        if (frompath_rel == "None") or (frompath_rel == f"{q}None{q}"):
            frompath_rel = f"{red}{frompath_rel}{end}"
        else:
            frompath_rel = f"{blue}{frompath_rel}{end}"
        if (topath_rel == "None") or (topath_rel == f"{q}None{q}"):
            topath_rel = f"{red}{topath_rel}{end}"
        else:
            topath_rel = f"{blue}{topath_rel}{end}"

        txt = f"{green}{treepath_unicum.get_name()}{end}<br>FROM: {frompath_rel}<br>TO: &nbsp;&nbsp;{topath_rel}"
        files_to_repoint_tuples.append(
            (
                treepath_unicum.get_dict()["icon"].replace(".png", "(rep).png"),
                txt,
                False,
                "",
                perm,
            )
        )

    if title_text is None:
        text = f"""
            Embeetle will update the listed config files.<br>
        """
    else:
        text = title_text

    if len(files_to_modify_tuples) == 0:
        files_to_modify_tuples = None
    if len(files_to_add_tuples) == 0:
        files_to_add_tuples = None
    if len(files_to_delete_tuples) == 0:
        files_to_delete_tuples = None
    if len(files_to_repoint_tuples) == 0:
        files_to_repoint_tuples = None

    result, checkbox_data = gui.dialogs.popupdialog.PopupDialog.checkboxes(
        parent=data.main_form,
        text=text,
        title_text="Permission to modify config files",
        icon_path="icons/gen/dashboard(check).png",
        text_click_func=catch_click,
        files_modified_list=files_to_modify_tuples,
        files_added_list=files_to_add_tuples,
        files_deleted_list=files_to_delete_tuples,
        files_repoint_list=files_to_repoint_tuples,
    )
    if result != qt.QMessageBox.StandardButton.Ok:
        callback(None, None, None, None, None)
        return

    for k in addperm_dict.keys():
        filepath = addperm_dict[k][0]
        addperm_dict[k][2] = checkbox_data[filepath.split("/")[-1]]

    for k in delperm_dict.keys():
        filepath = delperm_dict[k][0]
        delperm_dict[k][2] = checkbox_data[filepath.split("/")[-1]]

    for k in modperm_dict.keys():
        filepath = modperm_dict[k][0]
        confl = modperm_dict[k][3]
        man_mod = modperm_dict[k][6]
        txt = filepath.split("/")[-1]
        if confl:
            err = iconfunctions.get_rich_text_pixmap(
                pixmap_relpath="icons/dialog/warning.png",
                width=h,
            )
            txt += (
                f"&nbsp; &nbsp;&nbsp;&nbsp;{err}&nbsp;{red}Merge conflicts{end}"
            )
        elif man_mod:
            warn = iconfunctions.get_rich_text_pixmap(
                pixmap_relpath="icons/dialog/warning.png",
                width=h,
            )
            txt += f"&nbsp; &nbsp;&nbsp;&nbsp;{warn}&nbsp;{orange}Manual changes{end}"
        modperm_dict[k][2] = checkbox_data[txt]

    for k in repperm_dict.keys():
        treepath_unicum = _treepath_unicum_.TREEPATH_UNIC(k)
        frompath = repperm_dict[k][0]
        topath = repperm_dict[k][1]
        rootpath = projObj.get_proj_rootpath()
        if (frompath is None) or (frompath == "None"):
            frompath_rel = f"{q}None{q}"
        else:
            frompath_rel = f"{q}{_pp_.abs_to_rel(rootpath=os.path.dirname(rootpath), abspath=frompath)}{q}"
        if (topath is None) or (topath == "None"):
            topath_rel = f"{q}None{q}"
        else:
            topath_rel = f"{q}{_pp_.abs_to_rel(rootpath=os.path.dirname(rootpath), abspath=topath)}{q}"
        if (frompath_rel == "None") or (frompath_rel == f"{q}None{q}"):
            frompath_rel = f"{red}{frompath_rel}{end}"
        else:
            frompath_rel = f"{blue}{frompath_rel}{end}"
        if (topath_rel == "None") or (topath_rel == f"{q}None{q}"):
            topath_rel = f"{red}{topath_rel}{end}"
        else:
            topath_rel = f"{blue}{topath_rel}{end}"
        txt = f"{green}{treepath_unicum.get_name()}{end}<br>FROM: {frompath_rel}<br>TO: &nbsp;&nbsp;{topath_rel}"
        repperm_dict[k][2] = checkbox_data[txt]

    callback(
        addperm_dict,
        delperm_dict,
        modperm_dict,
        repperm_dict,
        diff_dialog,
    )
    return


def files_modified_info(*args) -> None:
    """"""
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#save"
    css = purefunctions.get_css_tags()
    red = css["red"]
    end = css["end"]

    text = f"""
    {css['h1']}Files to be modified{css['/hx']}
    <p align="left">
        Your dashboard changes have an impact on one or more config files. Embeetle asks you permission<br>
        to modify them.
    </p>
    <p align="left">
        If you know what you're doing, you can check <b>don't touch</b> for some of them. Embeetle will<br>
        then suppose that you modified the given file yourself manually, such that it complies with the<br>
        new dashboard settings. {red}Be careful: if you don't do this right, the dashboard gets out of<br>
        sync with the config files.{end}
    </p>
    <p align="left">
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/file/file_c(merge).png",
        title_text="FILES TO BE MODIFIED",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def files_deleted_info(*args) -> None:
    """"""
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#save"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Files to be deleted{css['/hx']}
    <p align="left">
        Your dashboard changes made one or more config files obsolete. Embeetle asks you permission to<br>
        delete this config file.
    </p>
    <p align="left">
        Maybe you've made some manual changes in that config file. Although it won't be used anymore with<br>
        these new dashboard settings, you would like to keep it for later use (when you'd roll back the<br>
        dashboard settings). In this scenario, you can check <b>don't touch</b>.
    </p>
    <p align="left">
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/trash.png",
        title_text="FILES TO BE DELETED",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def files_added_info(*args) -> None:
    """"""
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#save"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Files to be added{css['/hx']}
    <p align="left">
        Your dashboard changes created the need for a new config file. Embeetle asks your permission to<br>
        generate this config file.<br>
        <br>
        Currently we don't see a reason why you would not grant permission for this. If the generated file<br>
        doesn't fit your needs, you can (in most cases) edit the file as you wish.<br>
        <br>
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/file/file(add).png",
        title_text="FILES TO BE ADDED",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def files_repointed_info(*args) -> None:
    """"""
    dashboard_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/dashboard#save"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Repoints in 'PROJECT LAYOUT'{css['/hx']}
    <p align="left">
        The <b>Project Layout</b> section in the dashboard points to all the relevant config files. Some<br>
        'pointers' are no longer pointing to the right config file. Embeetle asks your permission to<br>
        correct this.
    </p>
    <p align="left">
        <a href="{dashboard_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/file/file(rep).png",
        title_text="FILES TO BE REPOINTED",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def explain_dashboard_permission(*args) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    chip_img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_with_chip.png",
        width=w * 10,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    <p align="left">
        Sorry, this functionality is not yet supported in the alpha version.<br>
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


def dashboard_info(typ: str) -> None:
    """"""
    types = {
        "files_modified": files_modified_info,
        "files_deleted": files_deleted_info,
        "files_added": files_added_info,
        "files_repointed": files_repointed_info,
    }
    if not (typ in types.keys()):
        raise Exception(
            f"[HELP TEXTS - DASHBOARD POPUP] Type {q}{typ}{q} is not defined!"
        )
    return types[typ]()


# ^                           PROJECT LAYOUT ENTRIES                           ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


def show_treepathobj_info(pathobj: _treepath_obj_.TreepathObj) -> None:
    """Show info about a given TreepathObj() in the dashboard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    icon = iconfunctions.get_rich_text_pixmap_middle(
        pathobj.get_closedIconpath(), width=int(h * 1.75)
    )
    f_btl = iconfunctions.get_rich_text_pixmap_middle(
        "icons/file/file_btl(lock).png", width=int(h * 1.75)
    )
    f_bin = iconfunctions.get_rich_text_pixmap_middle(
        "icons/file/file_bin.png", width=int(h * 1.75)
    )
    f_elf = iconfunctions.get_rich_text_pixmap_middle(
        "icons/file/file_elf.png", width=int(h * 1.75)
    )
    d_btl = iconfunctions.get_rich_text_pixmap_middle(
        "icons/folder/closed/beetle.png", width=int(h * 1.75)
    )
    d = iconfunctions.get_rich_text_pixmap_middle(
        "icons/folder/closed/folder.png", width=int(h * 1.75)
    )
    d_bld = iconfunctions.get_rich_text_pixmap_middle(
        "icons/folder/closed/build.png", width=int(h * 1.75)
    )
    d_src = iconfunctions.get_rich_text_pixmap_middle(
        "icons/folder/closed/magnifier.png", width=int(h * 1.75)
    )
    clean = iconfunctions.get_rich_text_pixmap_middle(
        "icons/gen/clean.png", width=int(h * 1.75)
    )
    build = iconfunctions.get_rich_text_pixmap_middle(
        "icons/gen/build.png", width=int(h * 1.75)
    )
    flash = iconfunctions.get_rich_text_pixmap_middle(
        "icons/chip/flash.png", width=int(h * 1.75)
    )

    chbx_01 = iconfunctions.get_rich_text_pixmap_middle(
        "icons/include_chbx/c_files/green_lock.png", width=h
    )
    chbx_02 = iconfunctions.get_rich_text_pixmap_middle(
        "icons/include_chbx/c_files/red_lock.png", width=h
    )

    locate_linkerscript = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_linkerscript.png", width=16 * h
    )
    locate_makefile = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_makefile.png", width=16 * h
    )
    locate_binfile = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_binfile.png", width=16 * h
    )
    locate_elffile = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_elffile.png", width=16 * h
    )
    locate_gdbflashcmds = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_gdbflashcmds.png", width=16 * h
    )
    locate_openocdchipcfg = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_openocdchipcfg.png", width=16 * h
    )
    locate_openocdprobecfg = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_openocdprobecfg.png", width=16 * h
    )

    locate_binfile_dialog = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_binfile_dialog.png", width=20 * h
    )
    locate_elffile_dialog = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/locate_elffile_dialog.png", width=20 * h
    )
    microcontroller_segment_01 = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/microcontroller_segment_mem_empty.png", width=20 * h
    )
    microcontroller_segment_02 = iconfunctions.get_rich_text_pixmap(
        "figures/dashboard/microcontroller_segment.png", width=20 * h
    )

    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    orange = css["orange"]
    end = css["end"]

    text = f"""
        {css['h1']}{icon} {pathobj.get_name()}{css['/hx']}
    """

    #! BUTTONS_BTL
    if pathobj.get_name() == "BUTTONS_BTL":
        text += f"""
        <p align="left" style="margin-bottom:30px;">
            The {f_btl}<b>buttons.btl</b> file contains the definitions for<br>
            all buttons in the toplevel toolbar (eg. clean {clean}, build {build},<br>
            flash {flash}, ...). You can add buttons in this file. Choose a<br>
            name, assign it an icon and a makefile target.<br>
        </p>
        """

    #! BUILD_DIR
    if pathobj.get_name() == "BUILD_DIR":
        text += f"""
        <p align="left" style="margin-bottom:30px;">
            The {d_bld}<b>build</b> folder is where your build output should end up:<br>
            the .bin and .elf files. Embeetle expects to find them here.<br>
        </p>
        <p align="left" style="margin-bottom:30px;">
            We encourage <i>shadow building</i>, which means that all build output<br>
            ends up in a dedicated <b>build</b> folder - cleanly separated from your<br>
            source code. But you're not obligated to do this.
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/makefile#shadow' style="color: #729fcf;">Click here</a> for<br>
            more info about shadow building.
        </p>
        """

    #! BIN_FILE
    if pathobj.get_name() == "BIN_FILE":
        text += f"""
        <p align="left" style="margin-bottom:0px;">
            The {f_bin}<b>.bin</b> file is your binary output. Embeetle located this file<br>
            at:
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on BUILD > BIN FILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_binfile}
        </p>
        <p align="left">
            Select the binary file in the popup window. If the binary file doesn't exist<br>
            yet, just navigate to the desired folder (eg. 'build/'), type the name of the<br>
            binary file and hit enter:<br>
        </p>
        <p align="left">
            {locate_binfile_dialog}
        </p>
        <p align="left" style="margin-bottom:30px;">
            After clicking the save button in the dashboard, Embeetle will propose to modify<br>
            the 'dashboard.mk' file, such that its variable 'ELF_FILE' corresponds to<br>
            the new name you've chosen.<br>
        </p>
        """

    #! ELF_FILE
    if pathobj.get_name() == "ELF_FILE":
        text += f"""
        <p align="left" style="margin-bottom:0px;">
            The {f_elf}<b>.elf</b> file is your binary output (with debug symbols included).<br>
            Embeetle located this file at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on BUILD > ELF FILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_elffile}
        </p>
        <p align="left">
            Select the elf file in the popup window. If the elf file doesn't exist<br>
            yet, just navigate to the desired folder (eg. 'build/'), type the name of the<br>
            elf file and hit enter:<br>
        </p>
        <p align="left">
            {locate_elffile_dialog}
        </p>
        <p align="left" style="margin-bottom:30px;">
            After clicking the save button in the dashboard, Embeetle will propose to modify<br>
            the 'dashboard.mk' file, such that its variable 'ELF_FILE' corresponds to<br>
            the new name you've chosen.<br>
        </p>
        """

    #! LINKERSCRIPT
    if pathobj.get_name() == "LINKERSCRIPT":
        text += f"""
        <p align="left" style="margin-bottom:30px;">
            The linkerscript maps all code and data to the FLASH and RAM<br>
            memories on your microcontroller.
        </p>

        {css['h2']}1. Linkerscript location{css['/hx']}
        <p align="left">
            Embeetle located your linkerscript at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on the LINKERSCRIPT and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_linkerscript}
        </p>
        <p align="left">
            Note: some projects have multiple linkerscripts, but there is always<br>
            a 'main' one. Embeetle only needs to locate the main one.
        </p>
        <p align="left">
            The (relative) path to the linkerscript you selected gets stored in:
        </p>
        <p align="center">
            {f_btl}{blue}{data.current_project.get_proj_rootpath()}/.beetle/dashboard_config.btl{end}
        </p>
        <p align="left" style="margin-bottom:30px;">
            So it's part of the project.
        </p>
        {css['h2']}2. Usage in Embeetle{css['/hx']}
        <p align="left">
            Embeetle parses your linkerscript to figure out the memory regions<br>
            (eg. FLASH, CCRAM, RAM, ...) and sections (eg. .data, .bss, ...).<br>
            They get displayed in the MICROCONTROLLER section in the dashboard:<br>
        </p>
        <p>
            {microcontroller_segment_01}
        </p>
        <p align="left">
            After parsing the linkerscript, Embeetle tries to parse the .elf<br>
            file (if available) to display how much of each memory region<br>
            is in use:<br>
        </p>
        <p>
            {microcontroller_segment_02}
        </p>
        <p align="left">
            Make sure Embeetle knows where to find your linkerscript and<br>
            .elf file!<br>
        </p>
        """

    #! MAKEFILE
    if pathobj.get_name() == "MAKEFILE":
        text += f"""
        <p align="left" style="margin-bottom:30px;">
            The makefile contains all instructions to compile and link your<br>
            project into a binary file.
        </p>

        {css['h2']}1. Makefile location{css['/hx']}
        <p align="left">
            The makefile plays a central role in Embeetle. Therefore, it is<br>
            very important that Embeetle knows where to find your main(*)<br>
            makefile in the project!
        </p>
        <p align="left">
            Embeetle located your makefile at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on the MAKEFILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_makefile}
        </p>
        <p align="left">
            <small>
                (*) Some projects have multiple makefiles, but there is always<br>
                a 'main' one. Embeetle only needs to locate the main one.
            </small>
        </p>
        <p align="left">
            The (relative) path to the makefile you selected gets stored in:
        </p>
        <p align="center">
            {f_btl}{blue}{data.current_project.get_proj_rootpath()}/.beetle/dashboard_config.btl{end}
        </p>
        <p align="left" style="margin-bottom:30px;">
            So it's part of the project.
        </p>
        
        {css['h2']}2. Usage in Embeetle{css['/hx']}
        <p align="left">
            Once Embeetle knows where to find your makefile, it gets used<br>
            for:<br>
            <br>
            {tab}- <b>The toolbar buttons:</b> each toolbar button, such as<br>
            {tab}&nbsp;&nbsp;{clean} clean, {build} build and {flash} flash runs a target<br>
            {tab}&nbsp;&nbsp;from the makefile.<br>
            <br>
            {tab}- <b>The source analyzer:</b> the source code analyzer runs<br>
            {tab}&nbsp;&nbsp;the makefile in {blue}--dry-run{end} mode and analyzes its<br>
            {tab}&nbsp;&nbsp;output to know exactly what flags you use to compile<br>
            {tab}&nbsp;&nbsp; each source file.
        </p>

        {css['h2']}3. Further reading{css['/hx']}
        <p align="left">
            Read more about the makefile on our website:
        </p>
        <ul>
            <li>
                <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build' style="color: #729fcf;">Disover the build system in Embeetle</a>
            </li>
            <li>
                <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/makefile' style="color: #729fcf;">Learn
                more about the default makefile we provide<br>
                for Embeetle projects</a>
            </li>
            <li>
                <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-open/arbitrary-makefile-project' style="color: #729fcf;">See
                how you can modify your makefile<br>
                such that it cooperates properly with Embeetle</a>
            </li>
        </ul>
        """

    #! DASHBOARD_MK
    if pathobj.get_name() == "DASHBOARD_MK":
        text += f"""
        {css['h2']}1. What is dashboard.mk?{css['/hx']}
        <p align="left" style="margin-bottom:30px;">
            The {icon}<b>dashboard.mk</b> file is the output file from the dashboard,<br>
            written in makefile syntaxis. Include it in your makefile and use the<br>
            defined variables, such as:<br>
            &nbsp;&nbsp;- {green}TARGET_CFLAGS{end}<br>
            &nbsp;&nbsp;- {green}TARGET_SFLAGS{end}<br>
            &nbsp;&nbsp;- {green}ELF_FILE{end}<br>
            &nbsp;&nbsp;- {green}GDB_FLASHFLAGS{end}<br>
            &nbsp;&nbsp;- ...<br>
            <br>
            Do this consistently to ensure that the dashboard remains in sync with<br>
            your project.
        </p>
        <p align="left">
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/makefile/dashboard-mk' style="color: #729fcf;">Click here</a>
            to learn more about this file.
        </p>
        <p align="left">
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-open/arbitrary-makefile-project' style="color: #729fcf;">Click here</a>
            to learn how you can include this<br>
            file into your makefile.
        </p>
        {css['h2']}2. Can I edit dashboard.mk?{css['/hx']}
        <p align="left">
            Feel free to edit, but be careful. This file is impacted by almost every<br>
            dashboard setting. Embeetle proposes a merged content when you save the<br>
            dashboard (applying a three-way-merge mechanism). If you made small edits,<br>
            this usually won't be a problem. Structural changes on the other hand can<br>
            cause merge conflicts.
        </p>
        <p align="left">
            <a href='{serverfunctions.get_base_url_wfb()}/#contact' style="color: #729fcf;">Contact us</a>
            if dashboard.mk doesn't meet your expectations. This file (especially<br>
            the compilation flags) represents Embeetle's knowledge of what is required to<br>
            compile, link and flash the code for the target processor. We encourage you to<br>
            contact us if you don't like this file, so we can make proper changes.
        </p>
        """

    #! FILETREE_MK
    if pathobj.get_name() == "FILETREE_MK":
        text += f"""
        {css['h2']}1. What is filetree.mk?{css['/hx']}
        <p align="left" style="margin-bottom:30px;">
            The {icon}<b>filetree.mk</b> file is the output file from the filetree,<br>
            written in makefile syntaxis. It lists all the C, C++ and assembly files<br>
            that should be compiled. This listing is based on the judgement from<br>
            the Embeetle source analyzer (source code parser), and can easily be<br>
            overridden by locking the red/green checkmarks {chbx_02}/{chbx_01} in the filetree.<br>
            <br>
            Your makefile should include this <b>filetree.mk</b> file and use its<br>
            defined variables, such as:<br>
            &nbsp;&nbsp;- {green}CFILES{end}<br>
            &nbsp;&nbsp;- {green}CXXFILES{end}<br>
            &nbsp;&nbsp;- {green}SFILES{end}<br>
            &nbsp;&nbsp;- {green}HDIRS{end}<br>
            Do this consistently to ensure that the red/green checkmarks in the filetree<br>
            remain in sync with your project.
        </p>
        <p align="left">
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/source-file-selection' style="color: #729fcf;">Click here</a>
            to learn more about Embeetle's automatic source file selection<br>
            mechanism.
        </p>
        <p align="left">
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-open/arbitrary-makefile-project' style="color: #729fcf;">Click here</a>
            to learn how you can include this file into your makefile, such<br>
            that the automatic source file selection mechanism works properly!
        </p>
        {css['h2']}2. Can I edit filetree.mk?{css['/hx']}
        <p>
            Don't edit, your changes will be overwritten. This file is merely<br>
            a list of source files and h-directories. If you want to manage<br>
            these manually, then you should ignore this file and maintain a<br>
            list yourself - either directly in the makefile or in some other<br>
            file you include in the makefile.
        </p>
        """

    #! GDB_FLASHFILE
    if pathobj.get_name() == "GDB_FLASHFILE":
        text += f"""
        <p align="left">
            The {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file contains all the GDB commands that<br>
            should execute when you click the {flash} flash button.<br>
        </p>

        {css['h2']}1. Location{css['/hx']}
        <p align="left">
            Embeetle located the file at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on GDB_FLASHFILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_gdbflashcmds}
        </p>

        {css['h2']}2. Practical details{css['/hx']}
        <p align="left">
            Please remember how the flash button (and other buttons) from the<br>
            toolbar work: they invoke a makefile target. By default, the flash<br>
            button invokes the 'flash' target.<br>
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash' style="color: #729fcf;">Click here</a>
            to review how flashing usually(*) happens in Embeetle.
        </p>
        <p align="left">
            <small>
                (*) Eventually, the flashing procedure depends on the implementation<br>
                of the flash target in your makefile. The webpage explains how our<br>
                <i>default</i> makefile flash target is implemented.
            </small>
        </p>
        <p align="left">
            In the (default) makefile flash target, the {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file<br>
            plays an important role. Its default implementation is explained in<br>
            great details
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash/gdbinit' style="color: #729fcf;">on this page</a>.
        </p>
        """

    #! OPENOCD_CHIPFILE
    if pathobj.get_name() == "OPENOCD_CHIPFILE":
        text += f"""
        <p align="left">
            The {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file is an OpenOCD configuration file<br>
            that defines the microcontroller. It should be handed to OpenOCD when it launches,<br>
            which normally happens when you click the {flash} button.
        </p>

        {css['h2']}1. Location{css['/hx']}
        <p align="left">
            Embeetle located the file at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on OPENOCD_CHIPFILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_openocdchipcfg}
        </p>

        {css['h2']}2. Practical details{css['/hx']}
        <p align="left">
            Please remember how the flash button (and other buttons) from the<br>
            toolbar work: they invoke a makefile target. By default, the flash<br>
            button invokes the 'flash' target.<br>
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash' style="color: #729fcf;">Click here</a>
            to review how flashing usually(*) happens in Embeetle.
        </p>
        <p align="left">
            <small>
                (*) Eventually, the flashing procedure depends on the implementation<br>
                of the flash target in your makefile. The webpage explains how our<br>
                <i>default</i> makefile flash target is implemented.
            </small>
        </p>
        <p align="left">
            In the (default) makefile flash target, the {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file<br>
            plays an important role. Its default implementation is explained in<br>
            great details
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash/flash-tools/openocd#openocd-chip' style="color: #729fcf;">on this page</a>.
        </p>
        """

    #! OPENOCD_PROBEFILE
    if pathobj.get_name() == "OPENOCD_PROBEFILE":
        text += f"""
        <p align="left">
            The {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file is an OpenOCD configuration file<br>
            that defines the flash/debug probe. It should be handed to OpenOCD when it launches,<br>
            which normally happens when you click the {flash} button.
        </p>

        {css['h2']}1. Location{css['/hx']}
        <p align="left">
            Embeetle located the file at:
        </p>
        <p align="center">
            {icon}{blue}{pathobj.get_relpath()}{end}
        </p>
        <p align="left">
            If this is incorrect, click in the dashboard on OPENOCD_PROBEFILE and<br>
            'select' in the context menu:
        </p>
        <p align="left">
            {locate_openocdprobecfg}
        </p>

        {css['h2']}2. Practical details{css['/hx']}
        <p align="left">
            Please remember how the flash button (and other buttons) from the<br>
            toolbar work: they invoke a makefile target. By default, the flash<br>
            button invokes the 'flash' target.<br>
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash' style="color: #729fcf;">Click here</a>
            to review how flashing usually(*) happens in Embeetle.
        </p>
        <p align="left">
            <small>
                (*) Eventually, the flashing procedure depends on the implementation<br>
                of the flash target in your makefile. The webpage explains how our<br>
                <i>default</i> makefile flash target is implemented.
            </small>
        </p>
        <p align="left">
            In the (default) makefile flash target, the {icon}<b>{pathobj.get_relpath().split('/')[-1]}</b> file<br>
            plays an important role. Its default implementation is explained in<br>
            great details
            <a href='{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/flash/flash-tools/openocd#openocd-probe' style="color: #729fcf;">on this page</a>.
        </p>
        """

    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=pathobj.get_closedIconpath(),
        title_text=pathobj.get_name(),
        text=text,
        text_click_func=functions.open_url,
    )
    return
