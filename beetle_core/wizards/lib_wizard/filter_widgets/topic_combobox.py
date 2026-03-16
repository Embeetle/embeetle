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
import qt, data
import functions
import gui.helpers.advancedcombobox as _advancedcombobox_

if TYPE_CHECKING:
    pass


class TopicComboBox(qt.QFrame):
    """"""

    new_topic_selected_sig = qt.pyqtSignal()
    TOPIC_LIST = (
        "All",
        "Communication",
        "Data Processing",
        "Data Storage",
        "Device Control",
        "Display",
        "Other",
        "Sensors",
        "Signal Input/Output",
        "Timing",
        "Uncategorized",
    )

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        self.__lyt = qt.QHBoxLayout(self)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        size = data.get_libtable_icon_pixelsize()
        self.__combobox: _advancedcombobox_.AdvancedComboBox = (
            _advancedcombobox_.AdvancedComboBox(
                parent=self,
                image_size=size,
            )
        )
        self.__combobox.setContentsMargins(0, 0, 0, 0)
        self.__lyt.addWidget(self.__combobox)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setSpacing(0)
        # $ Initialize combobox
        text_color = "default"
        for v in TopicComboBox.TOPIC_LIST:
            new_item = {
                "name": v,
                "widgets": [
                    {
                        "type": "text",
                        "text": v,
                        "color": text_color,
                    },
                ],
            }
            self.__combobox.add_item(new_item)
        self.__combobox.set_selected_name(TopicComboBox.TOPIC_LIST[0])
        padding_left = int(size / 5)
        self.__combobox.setStyleSheet(
            f"""
            QGroupBox {{
                background-color: #00ffffff;
                border-color: #9ebdde;
                border-width: 1px;
                border-style: solid;
            }}
            QGroupBox:hover {{
                background-color: #77d5e1f0;
            }}
            QGroupBox:focus {{
                color: #ffffff;
            }}
            QLabel {{
                padding-left: {padding_left}px;            
            }}
        """
        )
        self.__combobox.selection_changed.connect(self.elementchange_func)
        return

    @qt.pyqtSlot()
    def elementchange_func(self) -> None:
        """"""
        topic = self.__combobox.get_selected_item_name()
        self.new_topic_selected_sig.emit()
        return

    def get_combobox(self) -> _advancedcombobox_.AdvancedComboBox:
        """"""
        return self.__combobox

    def get_selected_text(self) -> str:
        """"""
        return self.__combobox.get_selected_item_name()

    def set_selected_text(self, category: str) -> None:
        """"""
        if category is None:
            category = "All"
        if category == "Signal Input-Output":
            category = "Signal Input/Output"
        assert category in TopicComboBox.TOPIC_LIST
        self.__combobox.set_selected_name(category)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill TopicComboBox() twice!")
            self.__dead = True

        # $ Disconnect signals
        try:
            self.new_topic_selected_sig.disconnect()
        except:
            pass

        # $ Remove child widgets
        self.__lyt.removeWidget(self.__combobox)

        # $ Kill and deparent children
        self.__combobox.self_destruct()

        # $ Kill leftovers
        functions.clean_layout(self.__lyt)

        # $ Reset variables
        self.__combobox = None
        self.__lyt = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return
