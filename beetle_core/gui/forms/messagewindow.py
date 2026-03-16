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

import os
import traceback
import qt
import data
import functions
import gui.templates.baseobject
import iconfunctions
import gui.stylesheets.groupbox
import gui.stylesheets.menu
import gui.stylesheets.textedit


class MessageWindow(qt.QGroupBox, gui.templates.baseobject.BaseObject):
    MAX_LINE_COUNT = 5000

    main_form = None
    text_edit = None

    def __init__(self, parent, main_form) -> None:
        """"""
        qt.QGroupBox.__init__(self, parent)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="Messages",
            icon=iconfunctions.get_qicon("icons/dialog/message.png"),
        )
        self.setParent(parent)
        layout = qt.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.setLayout(layout)

        self.text_edit = qt.QTextBrowser(self._parent)
        self.text_edit.document().setMaximumBlockCount(self.MAX_LINE_COUNT)
        self.text_edit.setReadOnly(True)
        self.text_edit.setOpenLinks(False)
        self.text_edit.anchorClicked.connect(self.__anchor_clicked)
        layout.addWidget(self.text_edit)

        # Update styles
        self.update_variable_settings()

        self.installEventFilter(self)

    def eventFilter(self, object, event):
        # Manual copy
        if event.type() == qt.QEvent.Type.KeyRelease:
            key = event.key()
            key_modifiers = event.modifiers()
            if (
                key == qt.Qt.Key.Key_C
                and key_modifiers == qt.Qt.KeyboardModifier.ControlModifier
            ):
                self.text_edit.copy()

        if event.type() == qt.QEvent.Type.MouseButtonRelease:
            if hasattr(self.main_form, "display"):
                if hasattr(self.main_form.display, "messages_button_reset"):
                    self.main_form.display.messages_button_reset()

        return False

    def __anchor_clicked(self, url_link):
        try:
            functions.open_url(url_link.url())
        except:
            traceback.print_exc()

    def clear(self):
        self.text_edit.document().clear()

    def append(self, text):
        self.text_edit.append(text)
        self.text_edit.ensureCursorVisible()

    def goto_start(self):
        self.text_edit.moveCursor(qt.QTextCursor.MoveOperation.Start)

    def update_variable_settings(self) -> None:
        """"""
        self.setStyleSheet(
            gui.stylesheets.groupbox.get_noborder_style()
            + gui.stylesheets.menu.get_general_stylesheet()
            + gui.stylesheets.textedit.get_default()
        )
        return
