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
import sys
import qt
import data
import functions


class PopupSplitterHandle(qt.QSplitterHandle):
    def __init__(self, *args, main_form=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.grip_lock = False
        self.main_form = main_form

    def mouseMoveEvent(self, e: qt.QMouseEvent):
        if self.grip_lock:
            # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned
            # object is a QPointF() instead of a QPoint()
            new_y: int = -int(e.position().y())
            self.main_form.popup_box_height += new_y
            self.main_form._popup_box_reposition()
        return super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        self.grip_lock = True
        return super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.grip_lock = False
        return super().mouseReleaseEvent(e)


class PopupSplitter(qt.QSplitter):
    def __init__(self, *args, main_form=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_form = main_form

    def createHandle(self):
        return PopupSplitterHandle(
            qt.Qt.Orientation.Vertical, self, main_form=self.main_form
        )
