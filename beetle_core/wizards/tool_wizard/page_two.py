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
import qt, data, purefunctions, functions, serverfunctions, gui, iconfunctions
import hardware_api.toolcat_unicum as _toolcat_unicum_
import bpathlib.tool_obj as _tool_obj_
import helpdocs.help_texts as _ht_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import wizards.tool_wizard.new_tool_wizard as _wiz_

from various.kristofstuff import *


def init_p2(self: _wiz_.NewToolWizard) -> None:
    """Initialize page 2.

    ╔══_groupbox_p2═════════╗ ║ ┌─_groupbox_p2r0──┐   ║ ║ │                 │ ║
    ║ └─────────────────┘   ║ ║ ┌─_groupbox_p2r1──┐   ║ ║ │                 │ ║
    ║ └─────────────────┘   ║ ╚═══════════════════════╝
    """

    def create_groupbox_p2r0():
        if self.toolcat is _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"):
            is_executable = False
        else:
            is_executable = True
        self._groupbox_p2r0 = self.create_info_groupbox(
            parent=self._groupbox_p2,
            text="Tool executable:" if is_executable else "Tool directory:",
            vertical=True,
            info_func=(
                _ht_.tool_executable_help
                if is_executable
                else _ht_.tool_directory_help
            ),
            spacing=5,
            margins=(5, 5, 5, 5),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        self._groupbox_p2r0.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self._groupbox_p2.layout().addWidget(self._groupbox_p2r0)

        # * Directory or file selection
        if self.toolcat is _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"):
            # $ Directory
            hlyt, lineedit, button, checkmark = (
                self.create_directory_selection_line(
                    parent=self._groupbox_p2r0,
                    tool_tip="Foobar",
                    start_directory_fallback=data.user_directory,
                    click_func=lambda *args: update_p2(self, "dir_btn", *args),
                    checkmarkclick_func=lambda *args: print("clicked"),
                    text_change_func=lambda *args: update_p2(
                        self, "dir_lineedit", *args
                    ),
                )
            )
        else:
            # $ File
            hlyt, lineedit, button, checkmark = self.create_file_selection_line(
                parent=self._groupbox_p2r0,
                tool_tip="Foobar",
                start_directory_fallback=data.user_directory,
                click_func=lambda *args: update_p2(self, "file_btn", *args),
                checkmarkclick_func=lambda *args: print("clicked"),
                text_change_func=lambda *args: update_p2(
                    self, "file_lineedit", *args
                ),
            )
        self._groupbox_p2r0.layout().addLayout(hlyt)
        self._widgets_p2r0["lineedit"] = lineedit
        self._widgets_p2r0["button"] = button
        self._widgets_p2r0["checkmark"] = checkmark

        # * Warning label
        hlyt, button, lbl = self.create_warning_line(
            parent=self._groupbox_p2r0,
            text="Foobar warning!",
            click_func=lambda *args: print("warning!"),
        )
        self._groupbox_p2r0.layout().addLayout(hlyt)
        self._widgets_p2r0["warning_btn"] = button
        self._widgets_p2r0["warning_lbl"] = lbl
        button.hide()
        lbl.hide()
        return

    def create_groupbox_p2r1():
        self._groupbox_p2r1 = self.create_info_groupbox(
            parent=self._groupbox_p2,
            text="Tool info:",
            vertical=True,
            info_func=_ht_.tool_info_help,
            spacing=5,
            margins=(5, 5, 5, 5),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        self._groupbox_p2r1.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self._groupbox_p2.layout().addWidget(self._groupbox_p2r1)
        self._groupbox_p2.layout().addStretch(10)
        # * Info labels
        cards = [
            "name",
            "unique_id",
            "version",
            "build_date",
            "bitness",
            "location",
            "toolprefix",
        ]
        # $ name
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_name_purple.png",
            tool_tip="Tool name",
            text="name".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("name"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["name_btn"] = btn
        self._widgets_p2r1["name_lbl"] = lbl
        self._widgets_p2r1["name_lineedit"] = lineedit

        # $ unique_id
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_name_purple.png",
            tool_tip="Tool unique ID",
            text="unique id".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("unique_id"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["unique_id_btn"] = btn
        self._widgets_p2r1["unique_id_lbl"] = lbl
        self._widgets_p2r1["unique_id_lineedit"] = lineedit

        # $ version
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_version_purple.png",
            tool_tip="Tool version",
            text="version".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("version"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["version_btn"] = btn
        self._widgets_p2r1["version_lbl"] = lbl
        self._widgets_p2r1["version_lineedit"] = lineedit

        # $ build_date
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_date_purple.png",
            tool_tip="Tool build date",
            text="build date".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("build_date"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["build_date_btn"] = btn
        self._widgets_p2r1["build_date_lbl"] = lbl
        self._widgets_p2r1["build_date_lineedit"] = lineedit

        # $ bitness
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_32b_purple.png",
            tool_tip="Tool bitness (32b or 64b)",
            text="bitness".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("bitness"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["bitness_btn"] = btn
        self._widgets_p2r1["bitness_lbl"] = lbl
        self._widgets_p2r1["bitness_lineedit"] = lineedit

        # $ location
        hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
            parent=self._groupbox_p2r1,
            icon_path="icons/tool_cards/card_location_purple.png",
            tool_tip="Tool location",
            text="location".ljust(12),
            click_func=lambda *args: self.info_btn_clicked("location"),
            text_change_func=lambda *args: print("text changed"),
        )
        lineedit.setReadOnly(True)
        self._groupbox_p2r1.layout().addLayout(hlyt)
        self._widgets_p2r1["location_btn"] = btn
        self._widgets_p2r1["location_lbl"] = lbl
        self._widgets_p2r1["location_lineedit"] = lineedit

        # $ toolprefix
        if self.toolcat is _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"):
            hlyt, btn, lbl, lineedit = self.create_btn_lbl_lineedit(
                parent=self._groupbox_p2r1,
                icon_path="icons/tool_cards/card_toolprefix_purple.png",
                tool_tip="Tool prefix",
                text="TOOLPREFIX".ljust(12),
                click_func=lambda *args: self.info_btn_clicked("toolprefix"),
                text_change_func=lambda *args: print("text changed"),
            )
            lineedit.setReadOnly(True)
            self._groupbox_p2r1.layout().addLayout(hlyt)
            self._widgets_p2r1["toolprefix_btn"] = btn
            self._widgets_p2r1["toolprefix_lbl"] = lbl
            self._widgets_p2r1["toolprefix_lineedit"] = lineedit
        return

    create_groupbox_p2r0()
    create_groupbox_p2r1()
    self.next_button.setEnabled(False)
    return


def update_p2(self: _wiz_.NewToolWizard, reason: str, *args) -> None:
    """
    Update page 2 based on reason:
        - 'dir_btn'
        - 'dir_lineedit'
    """

    def clean_info_lines(*_args) -> None:
        self._widgets_p2r1["name_lineedit"].setText("")
        self._widgets_p2r1["unique_id_lineedit"].setText("")
        self._widgets_p2r1["version_lineedit"].setText("")
        self._widgets_p2r1["build_date_lineedit"].setText("")
        self._widgets_p2r1["bitness_lineedit"].setText("")
        self._widgets_p2r1["location_lineedit"].setText("")
        if self.toolcat is _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"):
            self._widgets_p2r1["toolprefix_lineedit"].setText("")
        return

    def set_info_lines_color(color: str) -> None:
        assert isinstance(color, str)
        lineedits = (
            self._widgets_p2r1["name_lineedit"],
            self._widgets_p2r1["unique_id_lineedit"],
            self._widgets_p2r1["version_lineedit"],
            self._widgets_p2r1["build_date_lineedit"],
            self._widgets_p2r1["bitness_lineedit"],
            self._widgets_p2r1["location_lineedit"],
            self._widgets_p2r1["toolprefix_lineedit"],
        )
        if color == "red":
            for line in lineedits:
                if line is not None:
                    line.setProperty("red", True)
                    line.setProperty("lightred", False)
                    line.setProperty("green", False)
        elif color == "lightred":
            for line in lineedits:
                if line is not None:
                    line.setProperty("red", False)
                    line.setProperty("lightred", True)
                    line.setProperty("green", False)
        elif color == "green":
            for line in lineedits:
                if line is not None:
                    line.setProperty("red", False)
                    line.setProperty("lightred", False)
                    line.setProperty("green", True)
        else:
            assert False
        for line in lineedits:
            if line is not None:
                line.style().unpolish(line)
                line.style().polish(line)
                line.update()
        return

    def check_toolmanObj(
        toolmanObj: Optional[_tool_obj_.ToolmanObj],
        *_args,
    ) -> None:
        # & CASE 1: No tool found
        if toolmanObj is None:
            clean_info_lines()
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/warning.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: No tool found at this location!"
            )
            return
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj)

        # & CASE 2: Tool in <beetle_tools> folder
        if data.beetle_tools_directory in toolmanObj.get_abspath():
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/warning.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: The tools in the 'beetle_tools' folder are<br>"
                f"always parsed and added at startup. No need to add<br>"
                f"them manually."
            )
            return

        # & CASE 3: Wrong category
        if toolmanObj.get_category().lower() != self.toolcat.get_name().lower():
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/warning.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: The tool you selected is a <i>{toolmanObj.get_category().replace('_', ' ')}</i> tool,<br>"
                f"not a <i>{self.toolcat.get_name().replace('_', ' ')}</i> tool!"
            )
            return

        # & CASE 4: Tool already exists
        if data.toolman.unique_id_exists(toolmanObj.get_unique_id()):
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/warning.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: You already have this tool at the following location:<br>"
                f"<i>{q}{data.toolman.get_abspath(toolmanObj.get_unique_id())}{q}</i>"
            )
            return
        self._widgets_p2r0["checkmark"].setIcon(
            iconfunctions.get_qicon("icons/dialog/checkmark.png")
        )
        self._widgets_p2r0["warning_btn"].hide()
        self._widgets_p2r0["warning_lbl"].hide()
        self.next_button.setEnabled(True)
        set_info_lines_color("green")
        return

    def file_btn(*_args) -> None:
        "User clicked file button"
        file_abspath = _args[0]
        if (
            (file_abspath is None)
            or (file_abspath.lower() == "none")
            or (file_abspath.strip() == "")
        ):
            clean_info_lines()
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            self._widgets_p2r0["warning_btn"].hide()
            self._widgets_p2r0["warning_lbl"].hide()
            return

        assert self._widgets_p2r0["lineedit"].text() == file_abspath
        if not os.path.isfile(file_abspath):
            clean_info_lines()
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: File not found."
            )
            return

        data.toolman.add_tool(
            dirpath_or_exepath=file_abspath,
            wiz=self,
            callback=check_toolmanObj,
            callbackArg=None,
        )
        return

    def file_lineedit(*_args) -> None:
        "User typed in file lineedit"
        file_btn(self._widgets_p2r0["lineedit"].text())
        return

    def dir_btn(*_args) -> None:
        "User clicked directory button"
        dir_abspath = _args[0]
        if (
            (dir_abspath is None)
            or (dir_abspath.lower() == "none")
            or (dir_abspath.strip() == "")
        ):
            clean_info_lines()
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            self._widgets_p2r0["warning_btn"].hide()
            self._widgets_p2r0["warning_lbl"].hide()
            return
        assert self._widgets_p2r0["lineedit"].text() == dir_abspath
        if not os.path.isdir(dir_abspath):
            clean_info_lines()
            self.next_button.setEnabled(False)
            set_info_lines_color("lightred")
            self._widgets_p2r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            self._widgets_p2r0["warning_btn"].show()
            self._widgets_p2r0["warning_lbl"].show()
            self._widgets_p2r0["warning_lbl"].setText(
                f"WARNING: Directory not found."
            )
            return
        data.toolman.add_tool(
            dirpath_or_exepath=dir_abspath,
            wiz=self,
            callback=check_toolmanObj,
            callbackArg=None,
        )
        return

    def dir_lineedit(*_args) -> None:
        "User typed in directory lineedit"
        dir_btn(self._widgets_p2r0["lineedit"].text())
        return

    def not_known_reason(*_args) -> None:
        if self.toolcat is _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"):
            dir_lineedit(self._widgets_p2r0["lineedit"].text())
        else:
            file_lineedit(self._widgets_p2r0["lineedit"].text())
        return

    funcs = {
        "file_btn": file_btn,
        "file_lineedit": file_lineedit,
        "dir_btn": dir_btn,
        "dir_lineedit": dir_lineedit,
        "none": not_known_reason,
    }
    funcs[reason](*args)
    return


def info_btn_clicked(
    self: _wiz_.NewToolWizard,
    name: str,
    *args,
) -> None:
    """"""
    h = data.get_general_font_height()
    folder = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/folder.png",
        width=int(1.5 * h),
    )
    value = self._widgets_p2r1[f"{name}_lineedit"].text()
    css = purefunctions.get_css_tags()
    toolbox_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/toolbox"

    if (value is None) or (value == ""):
        text = f"""
        {css['h1']}TOOL INFO{css['/hx']}
        <p align="left">
            After analyzing your tool, Embeetle prints out everything it can extract.<br>
            If this fails, close Embeetle and have a look at the tool in your file<br>
            explorer. Does it have permissive read and execute rights?
        </p>
        <p align="left">
            <a href="{toolbox_link}" style="color: #729fcf;">Click here</a> for more information.
        </p>
        """
    else:
        text = f"""
        {css['h1']}TOOL INFO{css['/hx']}
        <p align="left">
            Embeetle analyzed the tool you selected:<br>
            {name} = {value}
        </p>
        <p align="left">
            <a href="{toolbox_link}" style="color: #729fcf;">Click here</a> for more information.
        </p>
        """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/info.png",
        title_text="TOOL INFO",
        text=text,
        text_click_func=functions.open_url,
    )
    return
