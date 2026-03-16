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

if TYPE_CHECKING:
    import tree_widget.widgets.item_arrow as _item_arrow_
    import tree_widget.widgets.item_btn as _item_btn_
    import tree_widget.widgets.item_action_btn as _item_action_btn_
    import tree_widget.items.item as _cm_
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class ItemLbl(_cm_widget_.ItemWidget, qt.QPushButton):
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
        owner: Union[_cm_.Item, _lib_item_shared_.LibItemShared],
    ) -> None:
        """"""
        try:
            qt.QPushButton.__init__(
                self,
                owner.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            qt.QPushButton.__init__(self)
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemLbl",
            owner=owner,
        )
        qt.QPushButton.setSizePolicy(
            self,
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Minimum,
        )
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
        # WARNING: This code is similar in 'item_richlbl.py'
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
        self.setStyleSheet(_lbl_style_.get_tree_lbl_stylesheet())
        return

    def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
        """Apply the blink stylesheet to make this label flashy green."""
        super().dragEnterEvent(event)
        self.setProperty("blink_01", False)
        self.setProperty("blink_02", True)
        self.set_blink_stylesheet()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return

    def dragLeaveEvent(self, event: qt.QDragLeaveEvent) -> None:
        """Apply the normal stylesheet."""
        super().dragLeaveEvent(event)
        self.setProperty("blink_01", False)
        self.setProperty("blink_02", False)
        self.set_normal_stylesheet()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return

    def dropEvent(self, event: qt.QDropEvent) -> None:
        """Apply the normal stylesheet."""
        super().dropEvent(event)
        self.setProperty("blink_01", False)
        self.setProperty("blink_02", False)
        self.set_normal_stylesheet()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
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
        text = _state_.lblTxt
        self.setText(text) if self.text() != text else nop()
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

    def enterEvent(self, event: qt.QEvent) -> None:
        """"""
        item = self.get_item()
        if (
            (item is None)
            or (item.is_dead())
            or (item._v_layout is None)
            or qt.sip.isdeleted(self)
        ):
            return

        # $ 1. itemBtn
        btn: _item_btn_.ItemBtn = item.get_widget(key="itemBtn")
        if btn is not None:
            btn.setProperty("_hover", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # $ 2. itemActionBtn
        action_btn: _item_action_btn_.ItemActionBtn = item.get_widget(
            key="itemActionBtn"
        )
        if action_btn is not None:
            action_btn.setProperty("_hover", True)
            action_btn.style().unpolish(action_btn)
            action_btn.style().polish(action_btn)

        # $ 3. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", True)
            arrow.style().unpolish(arrow)
            arrow.style().polish(arrow)

        # #$ 4. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', True)
        #     cchbx.style().unpolish(cchbx)
        #     cchbx.style().polish(cchbx)
        # #$ 5. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', True)
        #     hchbx.style().unpolish(hchbx)
        #     hchbx.style().polish(hchbx)
        # #$ 6. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', True)
        #     hglass.style().unpolish(hglass)
        #     hglass.style().polish(hglass)
        # #$ 7. cfgchbx
        # cfgchbx:_item_chbx_.CfgChbx = item.get_widget(key='cfgchbx')
        # if cfgchbx is not None:
        #     cfgchbx.setProperty('_hover', True)
        #     cfgchbx.style().unpolish(cfgchbx)
        #     cfgchbx.style().polish(cfgchbx)
        return

    def leaveEvent(self, event: qt.QEvent) -> None:
        """"""
        item = self.get_item()
        if (
            (item is None)
            or (item.is_dead())
            or (item._v_layout is None)
            or qt.sip.isdeleted(self)
        ):
            return

        # $ 1. itemBtn
        btn: _item_btn_.ItemBtn = item.get_widget(key="itemBtn")
        if btn is not None:
            btn.setProperty("_hover", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # $ 2. itemActionBtn
        action_btn: _item_action_btn_.ItemActionBtn = item.get_widget(
            key="itemActionBtn"
        )
        if action_btn is not None:
            action_btn.setProperty("_hover", False)
            action_btn.style().unpolish(action_btn)
            action_btn.style().polish(action_btn)

        # $ 3. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", False)
            arrow.style().unpolish(arrow)
            arrow.style().polish(arrow)

        # #$ 4. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', False)
        #     cchbx.style().unpolish(cchbx)
        #     cchbx.style().polish(cchbx)
        # #$ 5. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', False)
        #     hchbx.style().unpolish(hchbx)
        #     hchbx.style().polish(hchbx)
        # #$ 6. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', False)
        #     hglass.style().unpolish(hglass)
        #     hglass.style().polish(hglass)
        # #$ 7. cfgchbx
        # cfgchbx:_item_chbx_.CfgChbx = item.get_widget(key='cfgchbx')
        # if cfgchbx is not None:
        #     cfgchbx.setProperty('_hover', False)
        #     cfgchbx.style().unpolish(cfgchbx)
        #     cfgchbx.style().polish(cfgchbx)
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
                    f"Trying to kill ItemLbl() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
