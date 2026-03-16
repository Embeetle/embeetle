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
import qt, data, threading
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import gui.templates.baseprogressbar as _baseprogressbar_

"""
Decorator for checking underlying C++ object life
"""


def sip_check_method(method):
    def func_wrapper(self, *args, **kwargs):
        if qt.sip.isdeleted(self):
            return
        return method(self, *args, **kwargs)

    return func_wrapper


class ProgbarPopup(_gen_wizard_.GeneralWizard):
    apply_progbar_max_sig = qt.pyqtSignal()
    apply_progbar_val_sig = qt.pyqtSignal()

    def __init__(self, parent: qt.QWidget) -> None:
        super().__init__(parent)
        assert threading.current_thread() is threading.main_thread()
        self.__progbar_max = 100
        self.__progbar_val = 0
        self.__progbar: Optional[_baseprogressbar_.BaseProgressBar] = None
        self.apply_progbar_max_sig.connect(self.apply_progbar_max_slot)
        self.apply_progbar_val_sig.connect(self.apply_progbar_val_slot)
        self.setWindowTitle(f"Dashboard merging files ...")
        self.main_groupbox: Optional[qt.QGroupBox] = None
        self._groupbox_p0: Optional[qt.QGroupBox] = None
        self.init_pages()
        self.resize_and_center()
        self.__progbar.setMaximum(0)
        return

    def init_pages(self) -> None:
        """Initialize all pages."""
        assert threading.current_thread() is threading.main_thread()
        self.main_groupbox = self.create_groupbox(
            text="",
            borderless=True,
            vertical="stack",
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        self.main_groupbox.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.main_layout.addWidget(self.main_groupbox)
        #! Page 0
        self._groupbox_p0 = self.create_groupbox(
            text="",
            borderless=True,
            vertical=True,
            spacing=5,
            margins=(10, 15, 10, 10),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        self._groupbox_p0.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.main_groupbox.layout().addWidget(self._groupbox_p0)
        self.main_groupbox.layout().setCurrentIndex(0)
        self.add_progbar()
        return

    def add_progbar(self) -> None:
        assert threading.current_thread() is threading.main_thread()
        height = 20
        self.__progbar = _baseprogressbar_.BaseProgressBar(
            color="green",
            parent=self._groupbox_p0,
            height=height,
            thin=True,
            faded=True,
        )
        self.__progbar.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Fixed,
        )
        self._groupbox_p0.layout().addWidget(self.__progbar)
        return

    @sip_check_method
    def resize_and_center(self, *args) -> None:
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.setMinimumWidth(300)
        self.setMinimumHeight(int(2.5 * data.get_general_icon_pixelsize()))
        self.center_to_parent()
        return

    def show_next_page(self) -> None:
        return

    def show_prev_page(self) -> None:
        return

    @sip_check_method
    def set_progbar_max(self, maximum):
        if self.__progbar_max == maximum:
            return
        self.__progbar_max = maximum
        self.apply_progbar_max_sig.emit()
        return

    @qt.pyqtSlot()
    def apply_progbar_max_slot(self) -> None:
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        if qt.sip.isdeleted(self.__progbar):
            return
        self.__progbar.setMaximum(self.__progbar_max)
        return

    @sip_check_method
    def set_progbar_val(self, value):
        if self.__progbar_val == value:
            return
        self.__progbar_val = value
        self.apply_progbar_val_sig.emit()
        return

    @qt.pyqtSlot()
    def apply_progbar_val_slot(self) -> None:
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        if qt.sip.isdeleted(self.__progbar):
            return
        self.__progbar.setValue(self.__progbar_val)
        return

    @sip_check_method
    def inc_progbar_val(self, value):
        self.__progbar_val += value
        self.apply_progbar_val_sig.emit()
        return
