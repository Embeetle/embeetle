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
import qt, functions
import wizards.lib_wizard.filter_widgets.author_linebox as _author_linebox_

if TYPE_CHECKING:
    pass


class AuthorGroupBox(qt.QFrame):
    """"""

    btn_clicked_sig = qt.pyqtSignal()
    lineedit_clicked_sig = qt.pyqtSignal()
    lineedit_return_pressed_sig = qt.pyqtSignal()
    lineedit_tab_pressed_sig = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.setLayout(qt.QHBoxLayout())
        self.setStyleSheet(
            """
            QFrame {
                background: transparent;
            }
        """
        )
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # * AuthorLineBox()
        self.__author_linebox = _author_linebox_.AuthorLineBox(parent=self)
        self.layout().addWidget(self.__author_linebox)

        # * Pass all signals
        self.__author_linebox.btn_clicked_sig.connect(self.btn_clicked_sig)
        self.__author_linebox.lineedit_clicked_sig.connect(
            self.lineedit_clicked_sig
        )
        self.__author_linebox.lineedit_return_pressed_sig.connect(
            self.lineedit_return_pressed_sig
        )
        self.__author_linebox.lineedit_tab_pressed_sig.connect(
            self.lineedit_tab_pressed_sig
        )
        return

    def get_lineedit(self) -> _author_linebox_.AuthorLineBox:
        """"""
        return self.__author_linebox

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill AuthorGroupBox() twice!")
            self.__dead = True

        # $ Disconnect signals
        for sig in (
            self.btn_clicked_sig,
            self.lineedit_clicked_sig,
            self.lineedit_return_pressed_sig,
            self.lineedit_tab_pressed_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        self.layout().removeWidget(self.__author_linebox)

        # $ Kill and deparent children
        self.__author_linebox.self_destruct()

        # $ Kill leftovers
        functions.clean_layout(self.layout())

        # $ Reset variables
        self.__author_linebox = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return
