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
import os, pathlib
import qt, data, functions, iconfunctions
import gui.templates.paintedgroupbox
import gui.templates.widgetgenerator

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class ZippedLibGroupbox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    """"""

    clicked_or_enter_sig = qt.pyqtSignal()
    lineedit_tab_pressed_sig = qt.pyqtSignal()

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
    ) -> None:
        """"""
        super().__init__(
            parent=parent,
            name="projstorage",
            text="Select zipped library:",
            info_func=lambda *args: print("info clicked!"),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Maximum,
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(0)

        # * Error flag
        self.__err_flag = False

        # * Info Label
        # A label above the text field to show info and
        # error messages.
        self.__info_lbl = qt.QLabel()
        self.__info_lbl.setText(" ")
        self.__info_lbl.setStyleSheet(
            """
        QLabel {
            margin: 0px;
            padding: 0px;
            background-color: #00ffffff;
            border-style: none;
            text-align: left;
        }
        QLabel[red = true] {
            color: #cc0000;
        }
        """
        )
        self.__info_lbl.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.__info_lbl.setFont(data.get_general_font())
        self.__info_lbl.setMinimumHeight(data.get_general_icon_pixelsize())
        self.layout().addWidget(self.__info_lbl)
        self.__info_lbl.hide()

        # * Lineedit, folder_btn and checkmark
        homedir = str(pathlib.Path.home()).replace("\\", "/")
        hlyt, lineedit, button, checkmark = (
            gui.templates.widgetgenerator.create_file_selection_line(
                parent=self,
                tool_tip="Select zipped library",
                start_directory_fallback=homedir,
                click_func=self.zipfile_selected,
                checkmarkclick_func=self.checkmark_clicked,
                text_change_func=self.zipfile_selected,
                tool_tip_checkmark=None,
            )
        )
        self.__lineedit = lineedit
        self.__file_btn = button
        self.__checkmark = checkmark
        cast(qt.QVBoxLayout, self.layout()).addLayout(hlyt)
        del lineedit, button, checkmark, hlyt
        self.__checkmark.setIcon(
            iconfunctions.get_qicon("icons/dialog/cross.png")
        )
        self.__lineedit.setText(homedir)
        return

    def has_error(self) -> bool:
        return self.__err_flag

    def get_text(self) -> str:
        return self.__lineedit.text()

    def zipfile_selected(self, *args) -> None:
        """The user selected another zipfile, by clicking the file_btn and
        selecting a file.

        OR The user typed a character in the lineedit.
        """

        def set_err_status(err_status):
            self.__err_flag = err_status
            _selection = self.__lineedit.text()
            _selection = _selection.replace("\\", "/")
            if err_status:
                self.__info_lbl.setProperty("red", True)
                self.__info_lbl.style().unpolish(self.__info_lbl)
                self.__info_lbl.style().polish(self.__info_lbl)
                self.__info_lbl.show()
                self.__info_lbl.update()
                if os.path.isfile(_selection):
                    comment = f"Must be a {q}.zip{q} or {q}.7z{q} file"
                    self.__info_lbl.setText(comment)
                    self.__checkmark.setToolTip(comment)
                else:
                    comment = "Zipfile must exist"
                    self.__info_lbl.setText(comment)
                    self.__checkmark.setToolTip(comment)
                self.__checkmark.setIcon(
                    iconfunctions.get_qicon("icons/dialog/cross.png")
                )
                self.__lineedit.setProperty("red", True)
                self.__lineedit.style().unpolish(self.__lineedit)
                self.__lineedit.style().polish(self.__lineedit)
                self.__lineedit.update()
                return
            self.__info_lbl.setText(" ")
            self.__info_lbl.setProperty("red", False)
            self.__info_lbl.style().unpolish(self.__info_lbl)
            self.__info_lbl.style().polish(self.__info_lbl)
            self.__info_lbl.hide()
            self.__info_lbl.update()
            self.__lineedit.setProperty("red", False)
            self.__lineedit.style().unpolish(self.__lineedit)
            self.__lineedit.style().polish(self.__lineedit)
            self.__lineedit.update()
            self.__checkmark.setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            self.__checkmark.setToolTip("Zipfile okay")
            return

        selection = self.__lineedit.text()
        selection = selection.replace("\\", "/")
        if not os.path.isfile(selection):
            set_err_status(True)
            return
        if not (selection.endswith(".zip") or selection.endswith(".7z")):
            set_err_status(True)
            return
        set_err_status(False)
        return

    def checkmark_clicked(self, *args):
        """The user clicked the checkmark next to the file icon."""
        return
