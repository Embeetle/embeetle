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
import threading, re
import qt, data, purefunctions, functions, gui, settings, iconfunctions, serverfunctions
import helpdocs.help_subjects.license as _li_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


def new_project(parent: qt.QWidget) -> None:
    """Help text shown for 'New project' in home window."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    proj_img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/new_proj_01.png",
        width=h * 20,
    )
    wrn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/dialog/warning.png",
        width=h,
    )
    blky = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/folder/closed/blinky.png",
        width=h + 5,
    )
    rtimp = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/folder/closed/root_import.png",
        width=h + 5,
    )
    home_window_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window"
    )
    project_anatomy_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/project-anatomy"
    blinky_proj_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/create-project"
    import_proj_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
    css = purefunctions.get_css_tags()

    text = f"""
        {css['h1']}New Embeetle project{css['/hx']}
        <p align="left">
            {proj_img}<br>
            <br>
            For more information on how you start a new project,
            <a href="{home_window_link}" style="color: #729fcf;">click here</a>.<br>
            <br>
        </p>
        
        {css['h3']}1. What is an Embeetle project?{css['/hx']}
        <p align="left">
            An Embeetle project is nothing more than a folder with a fixed structure.<br>
            Any folder with that structure can be recognized by Embeetle as a valid <br>
            project.<br>
            <a href="{project_anatomy_link}" style="color: #729fcf;">Click here</a> to read more.<br> </p>
        </p>
        
        {css['h3']}2. {blky} Blink LED project.{css['/hx']}
        <p align="left">
            <a href="{blinky_proj_link}" style="color: #729fcf;">Click here</a> to read more.<br>
        </p>
        
        {css['h3']}3. {rtimp} Import from Pin Configurator.{css['/hx']}
        <p align="left">
            <a href="{import_proj_link}" style="color: #729fcf;">Click here</a> to read more.<br>
        </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        title_text="NEW PROJECT",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def import_from_library(parent: qt.QWidget) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    book = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/gen/book.png",
        width=h,
    )
    img_01 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/library_sample_proj_01.png",
        width=25 * h,
    )
    img_02 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/library_sample_proj_02.png",
        width=25 * h,
    )
    img_03 = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/library_sample_proj_03.png",
        width=25 * h,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text_basic = f"""
    {css['h1']}Import sample project from library{css['/hx']}
    <p align='left'>
        To import a sample project from a library, go to the <b>Libraries</b> tab,<br>
        choose a library, right click on it and select one of its sample projects.<br>
        <br>
        <a href='info' style="color: #729fcf;">Click here</a> for more info and screenshots to help you.<br>
    </p>
    """

    text_advanced = f"""
    {css['h1']}Import sample project from library{css['/hx']}
    <p align='left'>
        To import a sample project from a library, go to the <b>Libraries</b> tab<br>
        and choose a library:<br>
        <br>
        {tab}{img_01}<br>
    </p>
    <p align='left'>
        Right-click on the library and choose a sample project to import:<br>
        <br>
        {tab}{img_02}<br>
    </p>
    <p align='left'>
        If you don't have the library yet, first download it:<br>
        <br>
        {tab}{img_03}<br>
    </p>
    """
    basic_popup = None

    def catch_click(key, parent=None):  # noqa
        if key.startswith("http"):
            print(f"open url {key}")
            functions.open_url(key)
            return
        basic_popup.close()
        gui.dialogs.popupdialog.PopupDialog.ok(
            title_text="IMPORT FROM LIBRARY",
            text=text_advanced,
            text_click_func=catch_click,
            parent=parent,
        )
        return

    basic_popup = gui.dialogs.popupdialog.PopupDialog.ok(
        title_text="IMPORT FROM LIBRARY",
        text=text_basic,
        text_click_func=catch_click,
        parent=parent,
        non_blocking=True,
    )
    basic_popup.show()
    return


def import_from_pin_configurator(parent: qt.QWidget) -> None:
    """Help text shown for 'Import project from pin configurator' in home
    window."""
    import_from_pin_config_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window"
    )
    import_manually_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Import project{css['/hx']}
    <br>
    {css['h3']}1. Import from pin configurator{css['/hx']}
    <p align="left">
        Most microcontroller vendors provide free software to configure the pins of your chip visually.<br>
        The output of such <b>pin configurator</b> is a 'project' - a folder containing all the source<br>
        code (C, C++ and assembly) for the chip.<br>
        We at Embeetle have built an importer for such projects. <a href="{import_from_pin_config_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    {css['h3']}2. Manual import{css['/hx']}
    <p align="left">
        Perhaps you want to import a project from some other IDE. Or even a project with a completely custom<br>
        structure. We don't have an automated solution for that yet. But we help you to do it manually.<br>
        <a href="{import_manually_link}" style="color: #729fcf;">Click here</a> to read more.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        title_text="IMPORT PROJECT",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def open_existing_project(parent: qt.QWidget) -> None:
    """Help text shown for 'Open project' in home window."""
    h = data.get_general_font_height()
    open_btn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=h + 5,
    )
    filetree_fig = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/filetree/dirtree_collapsed.png",
        width=7 * h,
    )
    proj_struct_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/project-anatomy"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Open project{css['/hx']}
    <p align="left">
        To open an existing Embeetle project, simply click on {open_btn}<b>Open project</b> and<br>
        select the folder that contains the project. Remember, you should click the top-level<br>
        folder of the project.<br>
        In this example, that would be <b>my_project</b>:<br>
        <br>
        {filetree_fig}<br>
        <br>
        For more info on the Embeetle project structure, <a href="{proj_struct_link}" style="color: #729fcf;">Click here</a><br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        title_text="OPEN PROJECT",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def open_recent_project(parent: qt.QWidget) -> None:
    """Help text shown for 'Recent projects' in home window."""

    h = data.get_general_font_height()
    w = data.get_general_font_width()
    open_btn = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=h + 5,
    )
    nr = settings.SettingsFileManipulator.max_number_of_recent_files
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Recent projects{css['/hx']}
    <p align="left">
        Embeetle keeps a list of the most recent projects you opened. The list is maximally {nr}<br>
        entries long. Projects that no longer exist get kicked out the list.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        title_text="RECENT PROJECTS",
        text=text,
        parent=parent,
    )
    return


# 2   P r o j e c t    c r e a t i o n    i n f o
####################################################


def project_microcontroller_selection(parent: qt.QWidget) -> None:
    """
    TODO: Implement
    """
    text = "Kristof, add a description here!"
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/chip/chip.png",
        title_text=f"PROJECT{q}S MICROCONTROLLER SELECTION",
        text=text,
        parent=parent,
    )


def project_parent_directory_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Project's parent directory' in 'New Project
    Options'."""
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/stmicro/choose_project_directory.png",
        width=h * 25,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}Project's parent directory{css['/hx']}
    <p align="left">
        The <b>project's parent directory</b> is where your project will be created. Beware,<br>
        your project itself is also a directory. Don't mix up the two. This figure clarifies<br>
        everything.<br>
        {img}<br>
        <br>
        So if you got a folder <b>embeetle_projects</b> in which you create the project<br>
        <b>my_project</b>, then:<br>
        <br>
        {tab}- <b>embeetle_projects</b> is the project's <span style="color:'#cc0000';">parent</span> directory.<br>
        {tab}- <b>my_project</b> is the project directory,<br>
        {tab}{tab}{tab}{tab}&nbsp;also called the project "root folder".<br>
        {tab}- <b>my_project</b> is also the name of the project.<b>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/folder.png",
        title_text=f"PROJECT{q}S PARENT DIRECTORY",
        text=text,
        parent=parent,
    )
    return


def project_name_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Project name' in 'New Project Options'."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/stmicro/choose_project_name.png",
        width=h * 25,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    end = css["end"]

    text = f"""
    {css['h1']}Project name{css['/hx']}
    <p align="left">
        When you click OK, a new folder will be created with the name you entered here.<br>
        If that folder already exists, its content will be erased and overwritten.<br>
        <br>
        {img}<br>
        <br>
        So if you got a folder <b>embeetle_projects</b> in which you create the project<br>
        <b>my_project</b>, then:<br>
        <br>
        {tab}- <b>my_project</b> is the <b>name</b> of your project.<br>
        {tab}- <b>my_project</b> is also the project directory,<br>
        {tab}{tab}{tab}{tab}&nbsp;sometimes called the project 'root folder'.<br>
        {tab}- <b>embeetle_projects</b> is the project's {red}parent{end} directory.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/root.png",
        title_text="PROJECT NAME",
        text=text,
        parent=parent,
    )
    return


def project_board_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Board' in 'New Project Options'."""
    new_hardware_link = f"{serverfunctions.get_base_url_wfb()}/#supported-hardware/support-new-hardware"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Board{css['/hx']}
    <p align="left">
        Select the board you want to work with.
    </p>
    {css['h2']}1. Custom board{css['/hx']}
    <p align="left">
        We've prepared some sample projects for <b>custom boards</b>. These projects<br>
        are configured with minimal assumptions made about the board.
    </p>
    {css['h2']}2. Development board{css['/hx']}
    <p align="left">
        Most microcontroller vendors provide low-cost development boards for their<br>
        microcontrollers, so you can get started quickly. These boards typically<br>
        have an on-board <b>flash/debug probe</b>.<br>
    </p>
    {css['h2']}3. Support new hardware{css['/hx']}
    <p align="left">
        If your board is not in the list,
        <a href="{new_hardware_link}" style="color: #729fcf;">Click here</a> to read what you<br>
        can do.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/board/custom_board.png",
        title_text="BOARD",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def project_chip_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Microcontroller' in new project wizard."""
    hardware_overview_link = (
        f"{serverfunctions.get_base_url_wfb()}/#supported-hardware/overview"
    )
    contact_link = f"{serverfunctions.get_base_url_wfb()}/#contact"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Microcontroller{css['/hx']}
    <p align="left">
        Select a microcontroller from the list of supported ones.<br>
        <a href="{hardware_overview_link}" style="color: #729fcf;">Click here</a> to read more.<br>
        <br>
        If your microcontroller is not in the list, please
        <a href="{contact_link}" style="color: #729fcf;">contact us</a>.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/chip/chip.png",
        title_text="MICROCONTROLLER",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def project_vendor_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Vendor' in new project wizard."""
    hardware_overview_link = (
        f"{serverfunctions.get_base_url_wfb()}/#supported-hardware/overview"
    )
    contact_link = f"{serverfunctions.get_base_url_wfb()}/#contact"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Vendor{css['/hx']}
    <p align="left">
        Select a vendor from the list of supported ones.<br>
        <a href="{hardware_overview_link}" style="color: #729fcf;">Click here</a> to read more.<br>
        <br>
        If you want to use a microcontroller from a non-supported vendor,<br>
        please <a href="{contact_link}" style="color: #729fcf;">contact us</a>.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/logo/beetle_face.png",
        title_text="VENDOR",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def project_table_help(parent: qt.QWidget) -> None:
    """Help text shown for 'Project table' in new project wizard."""
    h = data.get_general_font_height()
    three_dots = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/home_window/three_dots.png",
        width=h * 30,
    )
    arbitrary_mk_proj_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-open/arbitrary-makefile-project"
    css = functions.get_css_tags()

    text = f"""
    {css['h1']}Sample projects{css['/hx']}
    <p align="left">
        Select a sample project from the list. Don't forget to click the three<br>
        dots at the right to see more info about the projects:<br>
        <br>
        {three_dots}
    </p>
    <p align="left">
        If there is nothing suitable, you can always open an arbitrary makefile-<br>
        based project. <a href="{arbitrary_mk_proj_link}" style="color: #729fcf;">Click here</a>
        to read more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/logo/beetle_face.png",
        title_text="Sample projects",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def project_probe_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Probe' in 'New Project Options'."""
    probe_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embedded-dev/hardware/probes"
    )
    contact_link = f"{serverfunctions.get_base_url_wfb()}/#contact"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Probe{css['/hx']}
    <p align="left">
        Select a probe from the list of supported ones. <a href="{probe_link}" style="color: #729fcf;">Click here</a> to read more.<br>
        <br>
        If your probe is not in the list, please <a href="{contact_link}" style="color: #729fcf;">contact us</a>.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/probe/probe.png",
        title_text="PROBE",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def project_type_info(parent: qt.QWidget) -> None:
    """Help text shown for 'Project type' in 'New Project Options'."""
    blinky_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/create-project"
    pin_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Project type{css['/hx']}
    <p align="left">
        Choose <b>Blinky</b> if you want a full functional project that makes the LEDs on your<br>
        board blink. This is possible, even if you have a custom board (but probably you'll have<br>
        to make a few adjustments in your software). <a href="{blinky_link}" style="color: #729fcf;">Click here</a> to read more.
    </p>
    <p align="left">
        Choose <b>Import</b> if you want to import from the pin configurator (eg. CubeMX for<br>
        STMicro, NuTool-PinConfigure for Nuvoton, ...). This will close down the current "New<br>
        Project Wizard" and bring you into the "Import Wizard". <a href="pin" style="color: #729fcf;">Click here</a> to read<br>
        more.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/root.png",
        title_text="PROJECT TYPE",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


# 3   P r o j e c t    i m p o r t    i n f o
################################################


def cubemx_project_directory(parent: qt.QWidget) -> None:
    """Help text shown for "CubeMX project directory" in CubeMX import
    wizard."""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    cubemx_projstruct = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/import_wizard/cubemx_projstruct.png",
        width=28 * w,
    )
    proj_import_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}CubeMX project directory{css['/hx']}
    <p align="left">
        Select the folder corresponding to the CubeMX project. A CubeMX project folder should<br>
        look like this:<br>
        <br>
        {cubemx_projstruct}<br>
        <br>
        <a href="{proj_import_link}" style="color: #729fcf;">Click here</a> for more info on importing from a pin configurator.<br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/folder/closed/folder.png",
        title_text="CUBEMX PROJECT DIRECTORY",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return


def cubemx_project_replace_or_keep(parent: qt.QWidget) -> None:
    """Help text shown for "Import type" in CubeMX import wizard."""
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Import type{css['/hx']}
    <p align="left">
        <b>Replace</b><br>
        Overwrite your CubeMX project with an Embeetle project. Warning: the original CubeMX<br>
        project is gone!
    </p>
    <p align="left">
        <b>Keep</b><br>
        Keep the original CubeMX project untouched. Generate the Embeetle project in another<br>
        place.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/logo/cubemx.png",
        title_text="CUBEMX PROJECT DIRECTORY",
        text=text,
        parent=parent,
    )
    return


def about(parent: qt.QWidget) -> None:
    """About Embeetle."""
    origthread = qt.QThread.currentThread()
    rem_version: Optional[str] = None
    rem_builddate: Optional[str] = None

    def start(*args):
        assert qt.QThread.currentThread() is origthread
        serverfunctions.get_remote_embeetle_version(callback=get_version)
        return

    def get_version(v: Optional[str], *args):
        assert qt.QThread.currentThread() is origthread
        nonlocal rem_version, rem_builddate
        rem_version = v
        if (v is None) or (v.lower() == "none"):
            rem_version = "none"
            rem_builddate = "none"
            show_dialog()
            return
        serverfunctions.get_remote_embeetle_builddate(callback=get_builddate)
        return

    def get_builddate(b: Optional[str], *args):
        assert qt.QThread.currentThread() is origthread
        nonlocal rem_builddate
        if (b is None) or (b.lower() == "none"):
            b = "none"
        rem_builddate = b
        show_dialog()
        return

    def show_dialog(*args):
        assert qt.QThread.currentThread() is origthread

        def catch_click(key, *_args, **kwargs):
            # For most links in the dialog, actual webpages must be shown. For
            # the href="license", no webpage must be shown. So I can't simply
            # replace this 'catch_click()' method with 'functions.open_url()'.
            f = {
                "home": f"{serverfunctions.get_base_url_wfb()}",
                "chip": (
                    f"{serverfunctions.get_base_url_wfb()}/#embedded-dev/hardware"
                ),
                "book": (
                    f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual"
                ),
                "license": _li_.show_license,
            }
            if isinstance(f[key], str) and f[key].startswith("http"):
                functions.open_url(f[key])
            else:
                if key == "license":
                    f[key](
                        parent=data.main_form,
                        txt=functions.get_license_text(),
                        typ="ok",
                    )
            return

        h = data.get_general_font_height()
        about_fig = iconfunctions.get_rich_text_pixmap(
            "figures/beetle/beetle_with_chip.png", width=5 * h
        )
        home = iconfunctions.get_rich_text_pixmap("icons/gen/home.png", width=h)
        chip = iconfunctions.get_rich_text_pixmap(
            "icons/chip/chip.png", width=h
        )
        book = iconfunctions.get_rich_text_pixmap("icons/gen/book.png", width=h)
        lic = iconfunctions.get_rich_text_pixmap(
            "icons/gen/certificate.png", width=h
        )
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]
        cur_version = (
            functions.get_embeetle_version().ljust(15).replace(" ", "&nbsp;")
        )
        cur_builddate = (
            functions.get_embeetle_builddate().ljust(15).replace(" ", "&nbsp;")
        )

        text = f"""
        {css['h1']}Embeetle IDE{css['/hx']}
        <p align="left">
            version: {green}{cur_version}{end}{tab}latest version: {green}{rem_version}{end}<br>
            date:{tab}{green}{cur_builddate}{end}{tab}latest date:{tab}{green}{rem_builddate}{end}<br>
            <br>
            {about_fig}<br>
            <br>
            {home} <a href="home" style="color: #729fcf;">{serverfunctions.get_base_url_wfb()}</a><br>
            {chip} <a href="chip" style="color: #729fcf;">{serverfunctions.get_base_url_wfb()}/#embedded-dev/hardware</a><br>
            {book} <a href="book" style="color: #729fcf;">{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual</a><br>
            <br>
            {lic} <a href="license" style="color: #729fcf;">Click here</a> to read the Embeetle license.<br>
        </p>
        """
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/logo/embeetle.png",
            title_text="ABOUT EMBEETLE",
            text=text,
            text_click_func=catch_click,
            parent=parent,
        )
        return

    start()
    return


def already_up_to_date(parent: qt.QWidget) -> None:
    """Shown when user clicks on help button when Embeetle is already up-to-
    date."""
    h = data.get_general_font_height()
    about_fig = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_with_chip.png",
        width=5 * h,
    )
    cur_version = (
        functions.get_embeetle_version().ljust(15).replace(" ", "&nbsp;")
    )
    cur_builddate = (
        functions.get_embeetle_builddate().ljust(15).replace(" ", "&nbsp;")
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    text = f"""
    {css['h1']}Embeetle up-to-date{css['/hx']}
    <p align="left">
        version: {green}{cur_version}{end}<br>
        date:{tab}{green}{cur_builddate}{end}<br>
        <br>
        {about_fig}<br>
        <br>
        Your current Embeetle version is the latest one.<br>
        <br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/logo/embeetle.png",
        title_text="EMBEETLE VERSION",
        text=text,
        parent=parent,
    )
    return


########################################################################################################################
#                                                    M A T I C                                                         #
########################################################################################################################
"""
Home window
"""


def home_window_info(parent: qt.QWidget, typ: str) -> None:
    """"""
    types = {
        "new_project": new_project,
        "import_project": import_from_pin_configurator,
        "open_project": open_existing_project,
        "recent_projects": open_recent_project,
        "update_disabled": already_up_to_date,
        "update_available": (
            lambda parent: gui.dialogs.popupdialog.PopupDialog.ok(  # noqa
                title_text="REFRESH",
                text="UPDATE AVAILABLE",
                parent=parent,
            )
        ),
        "update_error": (
            lambda parent: gui.dialogs.popupdialog.PopupDialog.ok(  # noqa
                title_text="REFRESH",
                text="UPDATE ERROR",
                parent=parent,
            )
        ),
    }
    if not (typ in types.keys()):
        raise Exception(
            f"[HELP TEXTS - HOME WINDOW] Type {q}{typ}{q} is not defined!"
        )
    types[typ](parent)
    return


def home_window_release_notes() -> Tuple[str, Callable]:
    """"""

    def catch_click(*args, **kwargs):
        functions.open_url(
            f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/release-notes"
        )
        return

    return (
        'Please read the release notes <a href="release_notes" style="color: #729fcf;">here</a>.',
        catch_click,
    )


def updated() -> str:
    """"""
    return "Embeetle is up-to-date"


"""
Project creation dialogs
"""


def project_creation_info(
    parent: qt.QWidget,
    typ: str,
) -> None:
    """"""
    types = {
        "project_microcontroller_selection": project_microcontroller_selection,
        "project_directory": project_parent_directory_info,
        "project_name": project_name_info,
        "board": project_board_info,
        "vendor": project_vendor_info,
        "chip": project_chip_info,
        "probe": project_probe_info,
        "project_type": project_type_info,
        "os": nop,
        "project_table": project_table_help,
    }
    if not (typ in types.keys()):
        raise Exception(
            f"[HELP TEXTS - PROJECT CREATION] Type {q}{typ}{q} is not defined!"
        )
    types[typ](parent)
    return


def project_import_info(
    parent: qt.QWidget,
    typ: str,
    vendor: str,
) -> Optional[str]:
    """"""
    if vendor == "arduino":
        types = {
            "input_directory": cubemx_project_directory,
            "input_type": cubemx_project_replace_or_keep,
            "project_directory": project_parent_directory_info,
            "project_name": project_name_info,
            "project_name_already_exists": (
                f"Project name is valid, but the directory already exists!"
            ),
            "project_name_error": f"Project name is NOT valid!",
            "project_name_ok": f"Project name is valid.",
            "project_directory_valid": (
                f"Project{q}s parent directory is valid."
            ),
            "project_directory_invalid": (
                f"Project{q}s parent directory is NOT valid!"
            ),
            "project_directory_no_write_permission": (
                f"Project{q}s parent directory does not have write permissions!"
            ),
        }
    else:
        types = {
            "input_directory": cubemx_project_directory,
            "input_type": cubemx_project_replace_or_keep,
            "project_directory": project_parent_directory_info,
            "project_name": project_name_info,
            "project_name_already_exists": (
                f"Project name is valid, but the directory already exists!"
            ),
            "project_name_error": f"Project name is NOT valid!",
            "project_name_ok": f"Project name is valid.",
            "project_directory_valid": (
                f"Project{q}s parent directory is valid."
            ),
            "project_directory_invalid": (
                f"Project{q}s parent directory is NOT valid!"
            ),
            "project_directory_no_write_permission": (
                f"Project{q}s parent directory does not have write permissions!"
            ),
        }
    if not (typ in types.keys()):
        raise Exception(
            f"[HELP TEXTS - PROJECT IMPORT] Type {q}{typ}{q} is not defined!"
        )
    if callable(types[typ]):
        return types[typ](parent)
    elif isinstance(types[typ], str):
        return types[typ]
    return


def show_info_field(
    projname: str,
    microcontroller: str,
    info_content: str,
    parent: qt.QWidget,
) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    info_content = info_content.replace("\n", "<br>")
    info_content = info_content.replace(
        "Microcontroller:", "<b>Microcontroller:</b>"
    )
    info_content = info_content.replace("Board:", "<b>Board:</b>")
    info_content = info_content.replace("Link:", "<b>Link:</b>")
    info_content = info_content.replace("Info:", "<b>Info:</b>")
    info_content = info_content.replace("Note:", "<b>Note:</b>")
    try:
        p = re.compile(r"https[\w:\/.#-]+")
        for m in p.finditer(info_content):
            _url_ = m.group(0)
            info_content = info_content.replace(
                _url_, f'<a href="{_url_}" style="color: #729fcf;">{_url_}</a>'
            )
    except Exception as e:
        purefunctions.printc(
            "WARNING: Could not make url clickable!",
            color="warning",
        )
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/filetree/project_tree.png",
        width=h * 10,
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    end = css["end"]

    text = f"""
    {css['h1']}{projname}{end}
    <p align="left">
        Project: {projname}<br>
        <br>
        {tab}{tab}{img}
    </p>
    <p align="left">
        {info_content}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/info.png",
        title_text="Project Info",
        text=text,
        text_click_func=functions.open_url,
        parent=parent,
    )
    return
