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
import qt, data, functions
import gui.templates.paintedgroupbox
import gui.templates.widgetgenerator
import libmanager.libmanager as _libmanager_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class LocalStorageGroupBox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    """"""

    clicked_or_enter_sig = qt.pyqtSignal()
    lineedit_tab_pressed_sig = qt.pyqtSignal()

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        title: Optional[str] = None,
    ) -> None:
        """"""
        if title is None:
            title = "Store downloaded libraries at:"
        super().__init__(
            parent=parent,
            name="localstorage",
            text=title,
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

        # * Lineedit, folder_btn and checkmark
        hlyt, lineedit, button, checkmark = (
            gui.templates.widgetgenerator.create_directory_selection_line(
                parent=self,
                tool_tip="Select folder",
                start_directory_fallback=data.settings_directory,
                click_func=nop,
                checkmarkclick_func=nop,
                text_change_func=nop,
                tool_tip_checkmark="Create folder",
            )
        )
        self.__lineedit = lineedit
        self.__folder_btn = button
        self.__checkmark = checkmark
        self.__sub_lyt = hlyt
        cast(qt.QVBoxLayout, self.layout()).addLayout(hlyt)
        del lineedit, button, checkmark, hlyt
        self.__checkmark.hide()
        self.__folder_btn.setEnabled(False)
        self.__lineedit.setEnabled(False)
        self.__lineedit.setReadOnly(True)

        # * Set default location
        dot_embeetle_libcollection_dir = (
            _libmanager_.LibManager().get_potential_libcollection_folder(
                "dot_embeetle"
            )
        )
        if isinstance(dot_embeetle_libcollection_dir, str):
            self.__lineedit.setText(dot_embeetle_libcollection_dir)
        return

    def get_text(self) -> str:
        """Return text in the QLineEdit().

        Will never return None.
        """
        txt = self.__lineedit.text()
        if not isinstance(txt, str):
            return ""
        return txt

    def self_destruct(
        self,
        death_already_checked: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill LocalStorageGroupBox() twice!"
                )
            self.dead = True

        # $ Disconnect signals
        for sig in (
            self.clicked_or_enter_sig,
            self.lineedit_tab_pressed_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        self.__sub_lyt.removeWidget(self.__lineedit)
        self.__sub_lyt.removeWidget(self.__folder_btn)
        self.__sub_lyt.removeWidget(self.__checkmark)

        # $ Kill and deparent children
        self.__lineedit.setParent(None)  # noqa
        self.__folder_btn.setParent(None)  # noqa
        self.__checkmark.setParent(None)  # noqa

        # $ Kill leftovers
        functions.clean_layout(self.__sub_lyt)
        functions.clean_layout(self.layout())

        # $ Reset variables
        self.__lineedit = None
        self.__folder_btn = None
        self.__checkmark = None
        self.__sub_lyt = None

        # $ Deparent oneself
        gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton.self_destruct(
            self,
            death_already_checked=True,
        )
        return
