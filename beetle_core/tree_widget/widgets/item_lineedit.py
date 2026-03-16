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
import gui.stylesheets.line_edit as _lineedit_style_
import tree_widget.widgets.item_widget as _cm_widget_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
    import dashboard.items.item as _dashboard_items_
    import tree_widget.items.item as _item_
from various.kristofstuff import *


class ItemLineedit(_cm_widget_.ItemWidget, qt.QLineEdit):
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

    enter_pressed_signal = qt.pyqtSignal(object)  # (event)
    key_pressed_signal = qt.pyqtSignal(object)  # (event)

    def __init__(
        self,
        owner: _cm_.Item,
    ) -> None:
        """"""
        try:
            qt.QLineEdit.__init__(self, owner.get_rootdir().get_chassis_body())
        except Exception as e:
            qt.QLineEdit.__init__(self)

        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemLineedit",
            owner=owner,
        )
        qt.QLineEdit.setSizePolicy(
            self,
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        self.setFont(data.get_general_font())
        self.sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        return

    def set_normal_stylesheet(
        self,
        state: Union[
            _item_.Item.Status,
            _item_.Folder.Status,
            _item_.File.Status,
            _dashboard_items_.Folder.Status,
            _dashboard_items_.File.Status,
        ],
        text: str,
    ) -> None:
        """"""
        text_color: Optional[str] = None
        background_color: Optional[str] = None
        border_color: Optional[str] = None

        # & ===============[ Light theme ]=============== &#
        if not data.theme["is_dark"]:
            # $ General
            # Blue text on gray-ish background:
            text_color = data.theme["fonts"]["blue"]["color"]  # color = #305e98
            background_color = data.theme["form_background"]  # color = #f0f0f0
            border_color = data.theme["button_border"]  # color = #b9cfe8

            # $ Irrelevant
            # Gray text on a gray-ish background
            if hasattr(state, "relevant") and (not state.relevant):
                text_color = data.theme["fonts"]["disabled"][
                    "color"
                ]  # color = #7d7d7d
                background_color = data.theme["fonts"]["disabled"][
                    "background"
                ]  # color = #d2d2d2
                border_color = data.theme["button_border"]  # color = #b9cfe8

            # $ Red
            # Red text on a gray-ish background:
            elif text.lower().strip() == "none":
                text_color = data.theme["fonts"]["red"][
                    "color"
                ]  # color = #c40000
                background_color = data.theme[
                    "form_background"
                ]  # color = #f0f0f0
                border_color = data.theme["button_border"]  # color = #b9cfe8
            # Red text on a red-ish background:
            elif state.has_error():
                text_color = data.theme["fonts"]["red"][
                    "color"
                ]  # color = #c40000
                background_color = "#fcdcdc"
                border_color = "#a40000"

            # $ Blue
            # Blue text on blue-ish background:
            elif hasattr(state, "has_info_blue") and state.has_info_blue():
                text_color = data.theme["fonts"]["blue"][
                    "color"
                ]  # color = #305e98
                background_color = "#d1e0ef"
                border_color = "#204a87"

            # $ Purple
            # Purple text on purple-ish background:
            elif hasattr(state, "has_info_purple") and state.has_info_purple():
                text_color = data.theme["fonts"]["purple"][
                    "color"
                ]  # color = #75507b
                background_color = "#dac5d8"
                border_color = "#5c3566"

        # & ===============[ Dark theme ]=============== &#
        else:
            assert data.theme["is_dark"]
            # $ General
            # White or blue text on gray-ish background:
            text_color = data.theme["fonts"]["blue"]["color"]  # color = #80a9d4
            background_color = data.theme["form_background"]  # color = #242424
            border_color = data.theme["button_border"]  # color = #8b8b8b

            # $ Irrelevant
            # Gray text on a gray-ish background
            if hasattr(state, "relevant") and (not state.relevant):
                text_color = data.theme["fonts"]["disabled"][
                    "color"
                ]  # color = #a0a0a0
                background_color = data.theme["fonts"]["disabled"][
                    "background"
                ]  # color = #d2d2d2
                border_color = data.theme["button_border"]  # color = #8b8b8b

            # $ Red
            # Red text on a gray-ish background:
            elif text.lower().strip() == "none":
                text_color = data.theme["fonts"]["red"][
                    "color"
                ]  # color = #f57979
                background_color = data.theme[
                    "form_background"
                ]  # color = #242424
                border_color = data.theme["button_border"]  # color = #8b8b8b
            # Red text on a red-ish background:
            elif state.has_error():
                text_color = data.theme["fonts"]["red"][
                    "color"
                ]  # color = #f57979
                background_color = "#6b0000"
                border_color = "#a40000"

            # $ Blue
            # Blue text on blue-ish background:
            elif hasattr(state, "has_info_blue") and state.has_info_blue():
                text_color = data.theme["fonts"]["blue"][
                    "color"
                ]  # color = #80a9d4
                background_color = "#183765"
                border_color = "#204a87"

            # $ Purple
            # Purple text on purple-ish background:
            elif hasattr(state, "has_info_purple") and state.has_info_purple():
                text_color = data.theme["fonts"]["purple"][
                    "color"
                ]  # color = #cdb1ca
                background_color = "#45284c"
                border_color = "#5c3566"

        # Apply the colors
        self.setStyleSheet(
            _lineedit_style_.get_line_edit_stylesheet(
                text_color=text_color,
                background_color=background_color,
                border_color=border_color,
            )
        )
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
        """Override this method, such that the one in superclass ItemWidget()
        does not fire!

        That one would start a drag action, which is not what we need here.
        """
        qt.QLineEdit.mouseMoveEvent(self, event)
        return

    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        """Extra signal, only for this widget.

        Fire signal when user hits enter key.
        """
        qt.QLineEdit.keyPressEvent(self, event)
        if (event.key() == qt.Qt.Key.Key_Return) or (
            event.key() == qt.Qt.Key.Key_Enter
        ):
            self.enter_pressed_signal.emit(event)
        else:
            self.key_pressed_signal.emit(event)
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
        !!! CHECK WHY THIS FUNCTION ALWAYS HAS THE FORCE PARAMETER SET TO FALSE !!!
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
        state = item.get_state()

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

        # $ 1. Set text
        if state.lineeditReadOnly:
            self.setReadOnly(True)
            self.setCursor(qt.QCursor(qt.Qt.CursorShape.PointingHandCursor))
        else:
            self.setReadOnly(False)
            self.setCursor(qt.QCursor(qt.Qt.CursorShape.IBeamCursor))
        text = state.lineeditTxt
        if text is None:
            text = "None"
        if self.text() != text:
            self.setText(text)

        # $ 2. Force stylesheet
        # This also sets the text and background colors. Normally, the 'set_normal_stylesheet()'
        # method gets only invoked if the 'force_stylesheet' parameter is True. However, for this
        # widget I make an exception.
        self.set_normal_stylesheet(state=state, text=text)
        self.style().unpolish(self)
        self.style().polish(self)

        # $ 3. Size
        fontMetrics = qt.QFontMetrics(self.font())
        width = fontMetrics.horizontalAdvance("_") * (len(text) + 2)
        width = max(fontMetrics.horizontalAdvance(f"_{text}_"), width)
        h_min = data.get_general_font_height()
        h_max = data.get_general_icon_pixelsize(is_inner=False)
        h_min = min(h_min, h_max)
        self.setMinimumHeight(h_min)
        self.setMaximumHeight(h_max)
        self.adjustSize()
        self.setMinimumWidth(width)

        # $ 4. Tooltip
        # Only set a tooltip if the widget is readonly. Otherwise it's just in your way.
        if state.lineeditReadOnly:
            tooltip = state.tooltip
            if tooltip is not None:
                self.setToolTip(tooltip)
            else:
                self.setToolTip("")
        else:
            self.setToolTip("")

        # * Finish
        if refreshlock:
            item.release_refresh_mutex()
        if callback is not None:
            callback(callbackArg)
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[object] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ItemLineedit() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
