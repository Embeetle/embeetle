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
import threading, functools

import iconfunctions
import qt, data
import tree_widget.widgets.item_widget as _cm_widget_
import bpathlib.path_power as _pp_
import gui.stylesheets.button as _btn_style_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemChbx(_cm_widget_.ItemWidget, qt.QPushButton):
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
        key: Optional[str] = None,
    ) -> None:
        """"""
        if key is None:
            key = "itemChbx"
        qt.QPushButton.__init__(self, owner.get_rootdir().get_chassis_body())
        _cm_widget_.ItemWidget.__init__(
            self,
            key=key,
            owner=owner,
        )
        self.set_normal_stylesheet()

        # Setup movie
        self._moviePlaying: bool = False
        self._movieLbl: Optional[qt.QLabel] = None
        self._movie: Optional[qt.QMovie] = None
        return

    def set_normal_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(_btn_style_.get_btn_stylesheet())
        return

    def setup_movie(self) -> None:
        """"""
        moviepath = iconfunctions.get_icon_abspath(
            "icons/loading_animation/hourglass_animation/hourglass.gif"
        )
        self._moviePlaying = False
        self._movieLbl = qt.QLabel()
        self._movieLbl.setStyleSheet(
            f"""
            QLabel {{
                background-color: #00ffffff;
                border-style: none;
                padding: 0px;
                margin:0px;
            }}
        """
        )
        self._movie = qt.QMovie(moviepath)
        self._movieLbl.setMovie(self._movie)
        self._movieLbl.setParent(self)
        self._movieLbl.hide()
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

        # $ 1. Force stylesheet
        if force_stylesheet:
            self.set_normal_stylesheet()
            self.style().unpolish(self)
            self.style().polish(self)

        # $ 2. Set icon
        # Is done in the child method

        # $ 3. Icon size
        inner_size = data.get_general_icon_pixelsize(is_inner=True)
        outer_size = data.get_general_icon_pixelsize(is_inner=False)
        w_inner = int(0.6 * inner_size)
        if self._moviePlaying:
            w_inner = int(0.8 * inner_size)
        self.setFixedSize(int(0.6 * outer_size), outer_size)
        self.setIconSize(qt.create_qsize(w_inner, inner_size))

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
                    f"Trying to kill ItemChbx() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
