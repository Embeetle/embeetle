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
import qt, data, functions, iconfunctions
import wizards.lib_wizard.filter_widgets.topic_combobox as _topic_combobox_
import gui.stylesheets.button as _btn_style_

if TYPE_CHECKING:
    pass


class TopicGroupBox(qt.QFrame):
    """"""

    new_topic_selected_sig = qt.pyqtSignal()
    btn_clicked_sig = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        hlyt = qt.QHBoxLayout()
        self.setLayout(hlyt)
        self.setStyleSheet(
            """
            QFrame {
                background: transparent;
            }
        """
        )
        self.setContentsMargins(0, 0, 0, 0)
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.setSpacing(0)

        # * QPushButton()
        size = data.get_libtable_icon_pixelsize()
        self.__icon_btn: qt.QPushButton = qt.QPushButton(self)
        self.__icon_btn.setStyleSheet(_btn_style_.get_btn_stylesheet())
        self.__icon_btn.setFixedSize(size, size)
        self.__icon_btn.setIconSize(qt.create_qsize(size, size))
        self.__icon_btn.setIcon(
            iconfunctions.get_qicon("icons/symbols/symbol_kind/type.png")
        )
        self.__icon_btn.clicked.connect(self.btn_clicked_sig)  # type: ignore
        hlyt.addWidget(self.__icon_btn)
        hlyt.addSpacing(5)

        # * Topic Combobox
        self.__topic_combobox: _topic_combobox_.TopicComboBox = (
            _topic_combobox_.TopicComboBox(
                parent=self,
            )
        )
        hlyt.addWidget(self.__topic_combobox)
        self.__topic_combobox.new_topic_selected_sig.connect(
            self.new_topic_selected_sig
        )
        return

    def get_combobox(self) -> _topic_combobox_.TopicComboBox:
        """"""
        return self.__topic_combobox

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill TopicGroupBox() twice!")
            self.__dead = True

        # $ Disconnect signals
        for sig in (
            self.new_topic_selected_sig,
            self.btn_clicked_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        self.layout().removeWidget(self.__icon_btn)
        self.layout().removeWidget(self.__topic_combobox)

        # $ Kill and deparent children
        self.__icon_btn.setParent(None)  # noqa
        self.__topic_combobox.self_destruct()

        # $ Kill leftovers
        functions.clean_layout(self.layout())

        # $ Reset variables
        self.__icon_btn = None
        self.__topic_combobox = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return
