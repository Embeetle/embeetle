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


def show_filetree_help(*args) -> None:
    """Help text shown for the dirtree hamburger menu."""
    h = data.get_general_font_height()
    tr = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/tree.png",
        width=h,
    )
    project_tree = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/filetree/project_tree.png",
        width=h * 7,
    )
    filetree_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/file-tree"
    file_selection_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/build/source-file-selection"
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}FILETREE{css['/hx']}
    <p align="left">
        The <b>Filetree</b> is the file explorer for your project:<br>
        {project_tree}<br>
        <br>
        <a href="{filetree_link}" style="color: #729fcf;">Click here</a>
        to read more about the Embeetle {tr} <b>Filetree</b>
    </p>
    <p>
        <a href="{file_selection_link}" style="color: #729fcf;">Click here</a>
        to discover the <b>automatic source file selection</b> mechanism.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/tree.png",
        title_text="FILETREE",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def nonmain_makefile_checkbox_help(name: str) -> None:
    """Help popup shown for the red/green checkbox next to a makefile."""
    h = data.get_general_font_height()
    chbx_g = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/include_chbx/c_files/green.png",
        width=h,
    )
    chbx_r = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/include_chbx/c_files/red.png",
        width=h,
    )
    makefile_relpath = data.current_project.get_treepath_seg().get_relpath(
        "MAKEFILE"
    )
    if makefile_relpath is None:
        makefile_relpath = "None"
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    text = f"""
    {css['h1']}MAKEFILE{css['/hx']}
    <p align="left">
        Embeetle recognized your file {green}'{name}'{end} to be a makefile. However,<br>
        it's not the 'main makefile' of this project. The main makefile is currently<br>
        registered as:<br>
        {tab}{green}&#60;project&#62;/{makefile_relpath}{end}<br>
        You can always change this in the DASHBOARD > PROJECT LAYOUT > MAKEFILE.
    </p>
    <p align="left">
        Many projects use several makefiles for the build: one 'main makefile' and a<br>
        few 'side' makefiles. The {chbx_g} or {chbx_r} box next to such a 'side' makefile<br>
        shows if it's being used or not. In other words, it shows if the main makefile<br>
        referenced/imported the side makefile.
    </p>
    <p align="left">
        <i>Note: The {chbx_g} next to the 'main makefile' should always be green. If not, it<br>
        means the Source Analyzer experienced an error.</i><br>
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/file/file_mk.png",
        title_text="FILETREE",
        text=text,
    )
    return


def main_makefile_checkbox_help(name: str) -> None:
    """Help popup shown for the red/green checkbox next to the main makefile."""
    h = data.get_general_font_height()
    chbx_g = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/include_chbx/c_files/green.png",
        width=h,
    )
    chbx_r = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="icons/include_chbx/c_files/red.png",
        width=h,
    )
    css = purefunctions.get_css_tags()
    green = css["green"]
    end = css["end"]

    text = f"""
    {css['h1']}MAKEFILE{css['/hx']}
    <p align="left">
        Embeetle recognized your file {green}'{name}'{end} to be a makefile. Also,<br>
        this file is registered as the "main makefile" for this project. That means<br>
        Embeetle performs a dry-run on this makefile to start parsing your code.
    </p>
    <p>
        To change the main makefile, go to the DASHBOARD > PROJECT LAYOUT > MAKEFILE.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/file/file_mk.png",
        title_text="MAIN MAKEFILE",
        text=text,
    )
    return


def file_hchbx_help(name: str, parentName: str, feedback: bool) -> None:
    """Helpt dialog shown when user clicks a h-file checkbox."""

    def catch_click(key, parent=None):
        funcs = {"extra_help": show_filetree_help}
        funcs[key]()
        return

    h = data.get_general_font_height()
    w = data.get_general_font_width()
    hf = iconfunctions.get_rich_text_pixmap("icons/file/file_h.png", width=h)
    hbx_g = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/green.png", width=h
    )
    hbx_r = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/red.png", width=h
    )
    hbx = hbx_g if feedback is True else hbx_r
    nm = name
    css = purefunctions.get_css_tags()
    blue = css["blue"]
    end = css["end"]

    text = f"""
    <p align="left">
        This {hbx} checkmark shows you if {hf}{blue}{nm}{end} is actually used or not in the<br>
        compilation. However, clicking this button has no effect.
    </p>
    """
    text += get_hchbx_helptext()
    extra = f"""
    <p align="left">
        For more info <a href="extra_help" style="color: #729fcf;">click here</a>
    </p>
    """
    text += extra
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/include_chbx/h_files/green.png",
        title_text="Ooops",
        text=text,
        text_click_func=catch_click,
    )
    return


def dir_hchbx_help(name: str) -> None:
    """Helpt text shown in a Dialog Box when user clicks a h-file checkbox."""

    def catch_click(key, parent=None):
        funcs = {"extra_help": show_filetree_help}
        funcs[key]()
        return

    h = data.get_general_font_height()
    w = data.get_general_font_width()
    hf = iconfunctions.get_rich_text_pixmap("icons/file/file_h.png", width=h)
    fd = iconfunctions.get_rich_text_pixmap(
        "icons/folder/open/folder.png", width=h
    )
    hbx_g = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/green.png", width=h
    )
    hbx_r = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/red.png", width=h
    )
    nm = name

    text = f"""
    <p align="left">
        Did you try to force the {hf}h-files in this {fd}directory to be in- or excluded in/from<br>
        the compilation?<br>
        Please read on to know why it's impossible to force them directly.
    </p>
    """
    extra = f"""
    <p align="left">
        For more info <a href="extra_help" style="color: #729fcf;">click here</a>
    </p>
    """
    text += get_hchbx_helptext()
    text += extra
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/include_chbx/h_files/green.png",
        title_text="Ooops",
        text=text,
        text_click_func=catch_click,
    )
    return


def get_hchbx_helptext(*args) -> str:
    """Helpt text for when user clicks a h-file checkbox."""
    h = data.get_general_font_height()
    # 1. FILES & FOLDERS
    hf = iconfunctions.get_rich_text_pixmap("icons/file/file_h.png", width=h)
    cf = iconfunctions.get_rich_text_pixmap("icons/file/file_c.png", width=h)
    mkf = iconfunctions.get_rich_text_pixmap("icons/file/file_mk.png", width=h)

    # 3. H-CHECKBOXES
    hbx_g = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/green.png", width=h
    )
    hbx_r = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/red.png", width=h
    )
    magn_b = iconfunctions.get_rich_text_pixmap(
        "icons/include_chbx/h_files/magnifier.png", width=h
    )

    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    <p align="left">
        <b>1. Why you can't click this round 'checkbox'</b><br>
        {tab}Unlike a c-file you can't force an h-file directly to take part in the<br>
        {tab}compilation. Let's consider why.
    </p>
    <p align="left">
        <b>2. The case for {cf}c-files</b><br>
        {tab}You've got a file {cf}{blue}foo.c{end} and you want it to take part in the<br>
        {tab}compilation. You click its checkbox, and Embeetle puts its path in<br>
        {tab}{mkf}{blue}filetree.mk{end}. When compilation starts, the {mkf}{blue}makefile{end}<br>
        {tab}includes {mkf}{blue}filetree.mk{end}, and compiles each and every c-file listed in<br>
        {tab}there - including {cf}{blue}foo.c{end}.
    </p>
    <p align="left">
        <b>3. The case for {hf}h-files</b><br>
        {tab}In contrast, h-files are not compiled directly. You can only provide a list<br>
        {tab}of directories to the compiler, saying:<br>
    <br>
        {tab}<i>Dear compiler, whenever you see a line like:<br>
        {tab} {tab}{green}#include "somefile.h";{end}<br>
        {tab}please use this list to look up the matching h-file.</i><br>
    <br>
        {tab}Providing such list is exactly what Embeetle does. In the file {blue}filetree.mk{end}<br>
        {tab}you\'ll find the list <b>HDIRS</b>. It's given to the {blue}makefile{end} when compilation<br>
        {tab}starts.<br>
        {tab}<br>
        {tab}So if you want an h-file {hf}{blue}foo.h{end} to be used in the compilation, the best you<br>
        {tab}can do is to click on the {magn_b} of its parent folder. Embeetle will put the parent<br>
        {tab}in <b>HDIRS</b>.<br>
        {tab}On the next compilation, this directory is provided to the compiler to look<br>
        {tab}around for h-files. If then, somewhere in a c-file, you put the line:<br>
        {tab} {tab}{green}#include \"foo.h\";{end}<br>
        {tab}this h-file should normally be found and included. Embeetle turns the {hbx_g}<br>
        {tab}checkmark next to {hf}{blue}foo.h{end} green to notify you about that.
    </p>
    """
    return text


def cannot_delete_file(abspath: str) -> None:
    """"""
    h = data.get_general_font_height()
    w = data.get_general_font_width()
    text = f"""
    <p align="left">
        ERROR: Cannot delete file {abspath}.<br>
        Probably you don't have the right file permissions.
    </p>
    """

    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/trash.png",
        title_text="Cannot delete file",
        text=text,
    )
    return


def cannot_rename_file(abspath: str) -> None:
    """"""
    text = f"""
    <p align="left">
        ERROR: Cannot rename file {q}{abspath}{q}.<br>
        Probably you don't have the right file permissions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Cannot rename file",
        text=text,
    )
    return


def cannot_move_file(abspath: str) -> None:
    """"""
    text = f"""
    <p align="left">
        ERROR: Cannot move file {q}{abspath}{q}.<br>
        Probably you don't have the right file permissions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Cannot move file",
        text=text,
    )
    return


def cannot_move_folder(abspath: str) -> None:
    """"""
    text = f"""
    <p align="left">
        ERROR: Cannot move folder {q}{abspath}{q}.<br>
        Probably you don't have the right file permissions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Cannot move folder",
        text=text,
    )
    return


def cannot_delete_dir(abspath: str) -> None:
    """"""
    text = f"""
    <p align="left">
        ERROR: Cannot delete folder {abspath}.<br>
        Probably you don't have the right file permissions.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/trash.png",
        title_text="Cannot delete folder",
        text=text,
    )
    return


def cannot_rename_dir(abspath: str) -> None:
    """"""
    text = f"""
    <p align="left">
        ERROR: Cannot rename folder {abspath}.<br>
        Probably you don't have the right file permissions.<br>
        <br>
        IMPORTANT - Embeetle can now be in a corrupted state!<br>
        Please check your file permissions and restart Embeetle.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/message.png",
        title_text="Cannot rename folder",
        text=text,
    )
    return


# def file_analysis_status(file:_filetree_items_.File) -> None:
#     '''
#     > analysis_status_none = 0    # Analysis not required
#     > analysis_status_waiting = 1 # Analysis scheduled
#     > analysis_status_busy = 2    # Analysis in progress
#     > analysis_status_done = 3    # Analysis done
#     > analysis_status_failed = 4  # Blocking error
#     '''
#     rootid = data.current_project.get_rootid_from_rootpath(
#         rootpath     = file.get_rootdir().get_abspath(),
#         double_angle = True,
#         html_angles  = True,
#     )
#     text:Optional[str] = None
#     css = purefunctions.get_css_tags()
#     tab   = css['tab']
#     blue  = css['blue']
#     green = css['green']
#     end   = css['end']
#     #& Analysis not required
#     if (file.get_state().analysis_state is None) or \
#             (file.get_state().analysis_state == 0):
#         return
#     #& Analysis scheduled or in progress
#     elif (file.get_state().analysis_state == 1) or \
#             (file.get_state().analysis_state == 2):
#         text = f'''
#         {css['h1']}Analysis busy{css['/hx']}
#         <p align="left">
#             The Source Analyzer Engine is currently analyzing source files. This<br>
#             file is currently being analyzed or scheduled to be analyzed soon:<br>
#             {tab}{blue}{q}{rootid}/{file.get_relpath()}{q}{end}<br>
#             <br>
#             Please wait for the analysis to complete. Then you{q}ll enjoy features<br>
#             like {q}click-and-jump{q}, viewing symbol info, ...<br>
#         </p>
#         '''
#     #& Analysis completed
#     elif file.get_state().analysis_state == 3:
#         text = f'''
#         {css['h1']}Analysis completed{css['/hx']}
#         <p align="left">
#             The Source Analyzer Engine completed analysis of this file:<br>
#             {tab}{blue}{q}{rootid}/{file.get_relpath()}{q}{end}<br>
#             <br>
#             This doesn{q}t mean that the file is error-free! It just means that<br>
#             the engine was able to extract all compiler flags and build an in-<br>
#             ternal database of all the file{q}s symbols. You can now enjoy features<br>
#             like {q}click-and-jump{q}, viewing symbol info, ... in this file.<br>
#         </p>
#         '''
#     #& Analysis failed
#     elif file.get_state().analysis_state == 4:
#         text = f'''
#         {css['h1']}Analysis failure{css['/hx']}
#         {css['h2']}What happened?{css['/hx']}
#         <p align="left">
#             The Source Analyzer Engine was unable to analyze this file:<br>
#             {tab}{blue}{q}{rootid}/{file.get_relpath()}{q}{end}<br>
#             <br>
#             This means that features like {q}click-and-jump{q}, viewing symbol info,<br>
#             ... won't work.
#         </p>
#         {css['h2']}Why did this happen?{css['/hx']}
#         <p align="left">
#             Probably there is a problem in your makefile, such that the Source<br>
#             Analyzer was unable to extract the compilation flags for this file.
#         </p>
#         '''
#     if text is not None:
#         gui.dialogs.popupdialog.PopupDialog.ok(
#             icon_path  = 'icons/gen/source_analyzer.png',
#             title_text = 'Analysis status',
#             text       = text,
#         )
#     return
