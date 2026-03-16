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

import qt
import data
import functions
import gui.templates.basemenu
import gui.stylesheets.combobox


class SimpleComboBox(qt.QComboBox):
    user_index_changed_signal = qt.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_style()

        self._user_interacting = False
        self.currentIndexChanged.connect(self._on_index_changed)

    def wheelEvent(self, event):
        # Ignore the wheel event for this combo box
        event.ignore()
        # Propagate the event to the parent widget
        self.parent().wheelEvent(event)

    def showPopup(self):
        self._user_interacting = True

        def choose(index):
            def inner(*args):
                self.__choose_item(index)

            return inner

        # Create menu
        menu = gui.templates.basemenu.BaseMenu(self)
        for i in range(self.count()):
            new_action = qt.QAction(self.itemText(i), menu)
            new_action.triggered.connect(choose(i))
            menu.addAction(new_action)
        # Show the menu
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def hidePopup(self):
        # Once the popup is hidden, user interaction is done
        super().hidePopup()
        self._user_interacting = False

    def _on_index_changed(self, index):
        if self._user_interacting:
            self.user_index_changed_signal.emit(index)

    def __choose_item(self, index):
        chosen_font = self.itemText(index)
        self.setCurrentIndex(index)

    def get_current_width(self):
        icon_width = data.get_general_icon_pixelsize()
        text_width = functions.get_text_width(self.currentText())
        padding = int(4 * data.get_global_scale())
        return icon_width + text_width + padding

    def update_style(self):
        self.setStyleSheet(gui.stylesheets.combobox.get_default())
