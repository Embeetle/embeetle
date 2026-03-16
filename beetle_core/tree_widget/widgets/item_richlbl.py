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
import qt, data
import gui.stylesheets.label as _lbl_style_
import tree_widget.widgets.item_widget as _cm_widget_
import gui.helpers.buttons as _buttons_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemRichLbl(_cm_widget_.ItemWidget, _buttons_.RichTextPushButton):
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

    def __init__(self, owner: _cm_.Item) -> None:
        """"""
        try:
            _buttons_.RichTextPushButton.__init__(
                self,
                owner.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            _buttons_.RichTextPushButton.__init__(self)
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemRichLbl",
            owner=owner,
        )
        _buttons_.RichTextPushButton.setSizePolicy(
            self,
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Minimum,
        )
        self._blinking = False
        self.__blinkstop_callback = None
        self.__blinkstop_callbackArg = None
        self.sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        return

    def set_normal_stylesheet(self) -> None:
        """"""
        _state_ = self.get_item().get_state()
        text = _state_.lblTxt

        # $ Choose text color
        # WARNING: This code is similar in 'item_lbl.py'
        text_color = data.theme["fonts"]["default"]["color"]
        if text.startswith("."):
            text_color = data.theme["fonts"]["disabled"]["color"]
        if hasattr(_state_, "has_info"):
            if _state_.has_info_purple():
                text_color = data.theme["fonts"]["purple"]["color"]
        if hasattr(_state_, "has_error"):
            if _state_.has_error():
                text_color = data.theme["fonts"]["red"]["color"]
        if hasattr(_state_, "relevant"):
            if not _state_.relevant:
                text_color = data.theme["fonts"]["disabled"]["color"]
        if "APPLY DASHBOARD" in text:
            text_color = data.theme["fonts"]["default"]["color"]

        # $ Apply stylesheet
        self.setStyleSheet(
            _lbl_style_.get_tree_lbl_stylesheet(
                text_color=text_color,
            )
        )
        outer_size = data.get_general_icon_pixelsize(is_inner=False)
        self.setFixedHeight(outer_size)
        return

    def set_blink_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(_lbl_style_.get_tree_lbl_blink_stylesheet())
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
        _state_ = item.get_state()

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

        # $ 2. Set text
        text = _state_.richLblTxt
        if (text is None) or (text == ""):
            text = _state_.lblTxt
        if self.text() != text:
            self.setText(text)
        self.set_normal_stylesheet()

        # $ 3. Tooltip
        tooltip = _state_.tooltip
        if tooltip is not None:
            self.setToolTip(tooltip)

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
                    f"Trying to kill ItemRichLbl() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
