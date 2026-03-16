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
import functools
import qt, data
import threading
import gui.templates.baseprogressbar as _bp_
import tree_widget.widgets.item_widget as _cm_widget_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemProgbar(_cm_widget_.ItemWidget, _bp_.BaseProgressBar):
    leftclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    ctrl_leftclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    rightclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    dragstart_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)
    dragenter_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)
    dragleave_signal = qt.pyqtSignal(str, object)  # (key, event)
    dragdrop_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)

    keypress_signal = qt.pyqtSignal(str, object)  # (key, event)
    keyrelease_signal = qt.pyqtSignal(str, object)  # (key, event)
    focusin_signal = qt.pyqtSignal(str, object)  # (key, event)
    focusout_signal = qt.pyqtSignal(str, object)  # (key, event)

    def __init__(
        self,
        owner: _cm_.Item,
        color: str,
    ) -> None:
        """"""
        _bp_.BaseProgressBar.__init__(
            self,
            color=color,
            parent=owner.get_rootdir().get_chassis_body(),
            faded=False,
        )
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemProgbar",
            owner=owner,
        )
        self.setTextVisible(True)
        self.setCursor(qt.QCursor(qt.Qt.CursorShape.PointingHandCursor))
        return

    def showEvent(self, event: qt.QShowEvent) -> None:
        """"""
        super().showEvent(event)
        self.sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        return

    def restyle(self) -> None:
        """"""
        self.sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        return

    def sync_widg(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        ATTENTION: Only runs if self.get_item()._v_layout is not None!
        """
        item = self.get_item()
        if (
            (item is None)
            or (item.is_dead())
            or (item._v_layout is None)
            or qt.sip.isdeleted(self)
        ):
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if refreshlock:
            if not item.acquire_refresh_mutex():
                qt.QTimer.singleShot(
                    10,
                    functools.partial(
                        self.sync_widg,
                        refreshlock,
                        force_stylesheet,
                        callback,
                        callbackArg,
                    ),
                )
                return

        # * Sync self
        if qt.sip.isdeleted(self):
            # Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return
        state = item.get_state()
        if state.progbarMax > 0:
            self.setMaximum(state.progbarMax)
            self.setValue(state.progbarVal)
        else:
            self.setMaximum(100)
            self.setValue(0)
            self.setColor("gray")

        self.choose_style()
        self.setFormat(state.progbarForm)
        w = data.get_general_font_width()
        h = data.get_general_font_height()
        self.setMinimumWidth(w * len(state.progbarForm))
        self.setMaximumWidth(w * len("10000 bytes / 10000 bytes"))
        self.setFixedHeight(h)

        if force_stylesheet:
            self.choose_style()
            self.style().unpolish(self)
            self.style().polish(self)

        # * Finish
        if refreshlock:
            item.release_refresh_mutex()
        if callback is not None:
            callback(callbackArg)
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ItemProgbar() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
