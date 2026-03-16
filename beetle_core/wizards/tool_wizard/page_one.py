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
import threading
import purefunctions
import data
import qt
import iconfunctions
import helpdocs.help_texts as _ht_
import wizards.tool_wizard.new_tool_wizard as _wiz_
from various.kristofstuff import *
import os_checker

if TYPE_CHECKING:
    import gui.helpers.buttons as _buttons_


def init_p1(self: _wiz_.NewToolWizard, server_toollist: List[Dict]) -> None:
    """Initialize page 1.

    ╔══_groupbox_p1══════════╗ ║ ┌─_groupbox_p1r0──┐    ║ ║ │                 │
    ║ ║ └─────────────────┘    ║ ║ ┌─_groupbox_p1r1──┐    ║ ║ │ │    ║ ║
    └─────────────────┘    ║ ╚════════════════════════╝
    """
    assert threading.current_thread() is threading.main_thread()

    def create_groupboxes(*args) -> None:
        # $ ROW 0
        self._groupbox_p1r0 = self.create_info_groupbox(
            parent=self._groupbox_p1,
            text="Select tool:",
            vertical=True,
            info_func=lambda *_args: _ht_.select_tool_help(
                self.toolcat.get_name()
            ),
            spacing=5,
            margins=(5, 5, 5, 5),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r0.layout()).setAlignment(
            qt.Qt.AlignmentFlag.AlignTop
        )
        cast(qt.QVBoxLayout, self._groupbox_p1.layout()).addWidget(
            self._groupbox_p1r0
        )

        # $ ROW 1
        self._groupbox_p1r1 = self.create_info_groupbox(
            parent=self._groupbox_p1,
            text=f"Tool{q}s parent directory:",
            vertical=True,
            info_func=_ht_.tool_parent_directory_help,
            spacing=5,
            margins=(5, 5, 5, 5),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r1.layout()).setAlignment(
            qt.Qt.AlignmentFlag.AlignTop
        )
        cast(qt.QVBoxLayout, self._groupbox_p1.layout()).addWidget(
            self._groupbox_p1r1
        )
        cast(qt.QVBoxLayout, self._groupbox_p1.layout()).addStretch(10)
        if server_toollist is None:
            server_error()
            return
        if len(server_toollist) == 0:
            empty_error()
            return
        fill_groupbox_p1r0()
        return

    def fill_groupbox_p1r0(*args) -> None:
        elements = []
        for _tooldict_ in server_toollist:
            elements.append((_tooldict_["iconpath"], _tooldict_["unique_id"]))
        hlyt, combobox, checkmark = self.create_dropdown_line(
            parent=self._groupbox_p1r1,
            tool_tip="Foobar",
            elements=elements,
            elementchange_func=lambda *_args: update_p1(
                self, "combobox", *_args
            ),
            checkmarkclick_func=lambda *_args: print("checkmark clicked"),
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r0.layout()).addLayout(hlyt)
        self._widgets_p1r0["combobox"] = combobox
        self._widgets_p1r0["checkmark"] = checkmark
        fill_groupbox_p1r1()
        return

    def fill_groupbox_p1r1(*args) -> None:
        hlyt: Optional[qt.QHBoxLayout] = None
        lineedit: Optional[qt.QLineEdit] = None
        button: Optional[Union[_buttons_.CustomPushButton, qt.QPushButton]] = (
            None
        )
        checkmark: Optional[_buttons_.CustomPushButton] = None
        hlyt, lineedit, button, checkmark = (
            self.create_directory_selection_line(
                parent=self._groupbox_p1r1,
                tool_tip="Foobar",
                start_directory_fallback=data.beetle_tools_directory,
                click_func=lambda *_args: update_p1(self, "dir_btn", *_args),
                checkmarkclick_func=lambda *_args: print("clicked"),
                text_change_func=lambda *_args: update_p1(
                    self, "dir_lineedit", *_args
                ),
            )
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r1.layout()).addLayout(hlyt)
        self._widgets_p1r1["lineedit"] = lineedit
        self._widgets_p1r1["button"] = button
        self._widgets_p1r1["checkmark"] = checkmark

        # & Warning label
        hlyt, button, lbl = self.create_warning_line(
            parent=self._groupbox_p1r1,
            text="WARNING: ",
            click_func=lambda *_args: print("warning!"),
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r1.layout()).addLayout(hlyt)
        self._widgets_p1r1["warning_btn"] = button
        self._widgets_p1r1["warning_lbl"] = lbl
        finish()
        return

    def empty_error(*args) -> None:
        hlyt, button, lbl = self.create_warning_line(
            parent=self._groupbox_p1r1,
            text=str(
                f"OOPS: It seems like there are no {self.toolcat.get_name()}<br>"
                f"tools for {os_checker.get_os()} on the Embeetle server.<br>"
            ),
            click_func=lambda *_args: print("warning!"),
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r0.layout()).addLayout(hlyt)
        self._widgets_p1r0["warning_btn"] = button
        self._widgets_p1r0["warning_lbl"] = lbl
        self._groupbox_p1r1.hide()
        abort()
        return

    def server_error(*args) -> None:
        hlyt, button, lbl = self.create_warning_line(
            parent=self._groupbox_p1r1,
            text=str(
                f"ERROR: Cannot connect to the Embeetle Server.<br>"
                f"Check your internet connection and antivirus/<br>"
                f"firewall, then restart this wizard. If that<br>"
                f'doesn"t help, restart Embeetle.<br>'
            ),
            click_func=lambda *_args: print("warning!"),
        )
        cast(qt.QVBoxLayout, self._groupbox_p1r0.layout()).addLayout(hlyt)
        self._widgets_p1r0["warning_btn"] = button
        self._widgets_p1r0["warning_lbl"] = lbl
        self._groupbox_p1r1.hide()
        abort()
        return

    def finish(*args) -> None:
        update_p1(self, "combobox")
        return

    def abort(*args) -> None:
        return

    if self._page_1_initialized:
        if (server_toollist is None) or (len(server_toollist) == 0):
            abort()
        else:
            finish()
        return
    self._page_1_initialized = True
    create_groupboxes()
    return


def update_p1(self: _wiz_.NewToolWizard, reason: str, *args) -> None:
    """
    Update page 1 based on reason:
        - 'combobox'
        - 'dir_btn'
        - 'dir_lineedit'
    """
    assert threading.current_thread() is threading.main_thread()

    def combobox(*_args):
        unique_id = self._widgets_p1r0["combobox"].get_selected_item_name()
        # print(f'\nunique_ide = {unique_id} , exists = {data.toolman.unique_id_exists(unique_id)}\n')

        # & Combobox tool already exists
        if data.toolman.unique_id_exists(unique_id):
            self._widgets_p1r0["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            self._widgets_p1r1["warning_btn"].show()
            self._widgets_p1r1["warning_btn"].setIcon(
                iconfunctions.get_qicon("icons/dialog/warning.png")
            )
            self._widgets_p1r1["warning_lbl"].show()
            self._widgets_p1r1["warning_lbl"].setText(
                "WARNING: You already have this tool. Click FINISH to<br>"
                "replace your local copy with a fresh one from the<br>"
                "server."
            )
            abspath = data.toolman.get_abspath(unique_id)
            assert abspath is not None
            self._widgets_p1r1["lineedit"].setReadOnly(True)
            self._widgets_p1r1["lineedit"].setText(abspath)
            self._widgets_p1r1["button"].setEnabled(False)
            self._widgets_p1r1["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            # self._groupbox_p1r1.modify_title('Tool already exists:')
            self.next_button.setEnabled(True)
            return

        # & Combobox tool is new
        self._widgets_p1r0["checkmark"].setIcon(
            iconfunctions.get_qicon("icons/dialog/checkmark.png")
        )
        self._widgets_p1r1["warning_btn"].hide()
        self._widgets_p1r1["warning_lbl"].hide()
        self._widgets_p1r1["lineedit"].setReadOnly(False)
        self._widgets_p1r1["lineedit"].setText(f"{data.beetle_tools_directory}")
        self._widgets_p1r1["button"].setEnabled(True)
        self._widgets_p1r1["checkmark"].setIcon(
            iconfunctions.get_qicon("icons/dialog/checkmark.png")
        )
        # self._groupbox_p1r1.modify_title(f'Tool{q}s parent directory:')
        self.next_button.setEnabled(True)
        return

    def dir_btn(*_args) -> None:
        dir_abspath = _args[0]
        if dir_abspath is None:
            return
        assert self._widgets_p1r1["lineedit"].text() == dir_abspath
        if os.path.isdir(dir_abspath):
            recommended_dirpath = f"{data.beetle_tools_directory}"
            self._widgets_p1r1["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            if dir_abspath == recommended_dirpath:
                self._widgets_p1r1["warning_btn"].hide()
                self._widgets_p1r1["warning_lbl"].hide()
                pass
            elif self._widgets_p1r1["lineedit"].isReadOnly():
                # Path set by combobox
                # -> combobox in control of warning msg
                pass
            else:
                self._widgets_p1r1["warning_btn"].show()
                self._widgets_p1r1["warning_btn"].setIcon(
                    iconfunctions.get_qicon("icons/dialog/message.png")
                )
                self._widgets_p1r1["warning_lbl"].show()
                self._widgets_p1r1["warning_lbl"].setText(
                    f"We recommend to store all your embeetle tools in:<br>"
                    f"<span style={dq}color:#4e9a06{dq}>{q}{recommended_dirpath}{q}</span><br>"
                )
            self.next_button.setEnabled(True)
        else:
            self._widgets_p1r1["checkmark"].setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            self.next_button.setEnabled(False)
        return

    def dir_lineedit(*_args) -> None:
        dir_btn(self._widgets_p1r1["lineedit"].text())
        return

    funcs = {
        "combobox": combobox,
        "dir_btn": dir_btn,
        "dir_lineedit": dir_lineedit,
    }
    funcs[reason](*args)
    return
