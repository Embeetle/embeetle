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
import qt

if TYPE_CHECKING:
    import tree_widget.chassis.chassis_body as _chassis_body_


class ItemEmitter(qt.QObject):
    # SIGNALS
    # --------
    refresh_sig = qt.pyqtSignal(bool)  # args = (refreshlock)
    refresh_later_sig = qt.pyqtSignal(
        bool, bool, object, object
    )  # args = (refreshlock, callback, callbackArg)
    refresh_recursive_later_sig = qt.pyqtSignal(
        bool, bool, object, object
    )  # args = (refreshlock, force_stylesheet, callback, callbackArg)
    rescale_sig = qt.pyqtSignal(bool)  # args = (refreshlock)
    rescale_later_sig = qt.pyqtSignal(
        bool, object, object
    )  # args = (refreshlock, callback, callbackArg)
    rescale_recursive_later_sig = qt.pyqtSignal(
        bool, object, object
    )  # args = (refreshlock, callback, callbackArg)
    self_destruct_sig = qt.pyqtSignal(
        bool, object, object
    )  # args = (killParentLink, callback, callbackArg)

    # CONNECTIONS
    # ------------
    refresh_connect = qt.pyqtSignal(object)  # args = (func)
    refresh_later_connect = qt.pyqtSignal(object)  # args = (func)
    refresh_recursive_later_connect = qt.pyqtSignal(object)  # args = (func)
    rescale_connect = qt.pyqtSignal(object)  # args = (func)
    rescale_later_connect = qt.pyqtSignal(object)  # args = (func)
    rescale_recursive_later_connect = qt.pyqtSignal(object)  # args = (func)
    self_destruct_connect = qt.pyqtSignal(object)  # args = (func)

    def __init__(
        self,
        parent: Optional[_chassis_body_.ChassisBody],
    ) -> None:
        """"""
        super().__init__(parent=parent)
        return

    def disconnect_signals(self) -> None:
        """"""

        def discon_sig(signal):
            while True:  # Disconnect only breaks one connection at a time,
                try:  # so loop to be safe.
                    signal.disconnect()
                except TypeError:
                    break
            return

        discon_sig(self.refresh_sig)
        discon_sig(self.refresh_later_sig)
        discon_sig(self.refresh_recursive_later_sig)
        discon_sig(self.rescale_sig)
        discon_sig(self.rescale_later_sig)
        discon_sig(self.rescale_recursive_later_sig)
        discon_sig(self.self_destruct_sig)

        discon_sig(self.refresh_connect)
        discon_sig(self.refresh_later_connect)
        discon_sig(self.refresh_recursive_later_connect)
        discon_sig(self.rescale_connect)
        discon_sig(self.rescale_later_connect)
        discon_sig(self.rescale_recursive_later_connect)
        discon_sig(self.self_destruct_connect)
        return

    @qt.pyqtSlot(object)
    def _refresh_connect_(self, func):
        self.refresh_sig.connect(func)

    @qt.pyqtSlot(object)
    def _refresh_later_connect_(self, func):
        self.refresh_later_sig.connect(func)

    @qt.pyqtSlot(object)
    def _refresh_recursive_later_connect_(self, func):
        self.refresh_recursive_later_sig.connect(func)

    @qt.pyqtSlot(object)
    def _rescale_connect_(self, func):
        self.rescale_sig.connect(func)

    @qt.pyqtSlot(object)
    def _rescale_later_connect_(self, func):
        self.rescale_later_sig.connect(func)

    @qt.pyqtSlot(object)
    def _rescale_recursive_later_connect_(self, func):
        self.rescale_recursive_later_sig.connect(func)

    @qt.pyqtSlot(object)
    def _self_destruct_connect_(self, func):
        self.self_destruct_sig.connect(func)
