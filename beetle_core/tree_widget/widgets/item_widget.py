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
import traceback, weakref, threading, functools
import qt, data, purefunctions, iconfunctions

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
    import tree_widget.widgets.item_lbl as _item_lbl_
from various.kristofstuff import *


class ItemWidget(object):
    cache = []
    "leftclick_signal       = pyqtSignal(str, object)"  # (key, event)
    "ctrl_leftclick_signal  = pyqtSignal(str, object)"  # (key, event)
    "rightclick_signal      = pyqtSignal(str, object)"  # (key, event)
    "dragstart_signal       = pyqtSignal(str, object, str)"  # (key, event, mimetxt)
    "dragenter_signal       = pyqtSignal(str, object, str)"  # (key, event, mimetxt)
    "dragleave_signal       = pyqtSignal(str, object)"  # (key, event)
    "dragdrop_signal        = pyqtSignal(str, object, str)"  # (key, event, mimetxt)
    "keypress_signal        = pyqtSignal(str, object)"  # (key, event)
    "keyrelease_signal      = pyqtSignal(str, object)"  # (key, event)
    "focusin_signal         = pyqtSignal(str, object)"  # (key, event)
    "focusout_signal        = pyqtSignal(str, object)"  # (key, event)

    def __del__(self) -> None:
        """"""
        ItemWidget.cache.remove(self)

    def __init__(
        self,
        key: str,
        owner: _cm_.Item,
    ) -> None:
        """"""
        self.dead = False
        self._key = key
        self._ownerRef = weakref.ref(owner)
        self._dragStartPosition = None
        self.setContextMenuPolicy(qt.Qt.ContextMenuPolicy.CustomContextMenu)  # type: ignore
        self.setAcceptDrops(True)  # type: ignore

        # $ Blink variables
        self._blinking: bool = False
        self._blinkstop_callback: Optional[Callable] = None
        self._blinkstop_callbackArg: Any = None

        # self.destroyed.connect(lambda: print('<<< ItemWidget() destroyed >>>'))

        ItemWidget.cache.append(self)
        return

    def get_item(self) -> Optional[_cm_.Item]:
        """"""
        if self._ownerRef is None:
            return None
        return self._ownerRef()

    def set_key(self, key: str) -> None:
        """"""
        self._key = key
        return

    def get_key(self) -> str:
        """"""
        return self._key

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        """"""
        super().mousePressEvent(event)  # type: ignore
        event.ignore()
        self._dragStartPosition = event.position().toPoint()
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseReleaseEvent(self, event: qt.QMouseEvent) -> None:
        """"""
        super().mouseReleaseEvent(event)  # type: ignore
        # event.ignore()

        if event.button() == qt.Qt.MouseButton.LeftButton:
            if event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier:
                self.ctrl_leftclick_signal.emit(self._key, event)  # type: ignore
                return
            self.leftclick_signal.emit(self._key, event)  # type: ignore
            return

        if event.button() == qt.Qt.MouseButton.RightButton:
            self.rightclick_signal.emit(self._key, event)  # type: ignore
            return
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
        """"""
        try:
            super().mouseMoveEvent(event)  # type: ignore
        except:
            pass
        # event.accept()
        if event.buttons() == qt.Qt.MouseButton.NoButton:
            return
        if self._dragStartPosition is None:
            return
        # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned object is a
        # QPointF() instead of a QPoint()
        if (
            event.position().toPoint() - self._dragStartPosition
        ).manhattanLength() < qt.QApplication.startDragDistance():
            return
        iconpath = self.get_item().get_state().closedIconpath
        if (iconpath is None) or (iconpath.strip() == ""):
            iconpath = self.get_item().get_state().action_iconpath
        drag = qt.QDrag(self)  # type: ignore
        drag.setPixmap(
            iconfunctions.get_qpixmap(
                pixmap_relpath=iconpath,
                width=int(data.get_general_icon_pixelsize() * 0.85),
                height=int(data.get_general_icon_pixelsize() * 0.85),
            )
        )
        mimeData = qt.QMimeData()
        mimeData.setText(self.get_item().get_abspath())
        drag.setMimeData(mimeData)
        self.dragstart_signal.emit(self._key, event, mimeData.text())  # type: ignore
        dropAction = drag.exec(
            qt.Qt.DropAction.CopyAction | qt.Qt.DropAction.MoveAction
        )
        return

    @qt.pyqtSlot(qt.QDragEnterEvent)
    def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
        event.acceptProposedAction()
        # event.accept()
        super().dragEnterEvent(event)  # type: ignore
        # if event.mimeData().hasFormat('text/plain'):
        self.dragenter_signal.emit(self._key, event, event.mimeData().text())  # type: ignore
        return

    @qt.pyqtSlot(qt.QDragLeaveEvent)
    def dragLeaveEvent(self, event: qt.QDragLeaveEvent) -> None:
        event.accept()
        super().dragLeaveEvent(event)  # type: ignore
        self.dragleave_signal.emit(self._key, event)  # type: ignore
        return

    @qt.pyqtSlot(qt.QDropEvent)
    def dropEvent(self, event: qt.QDropEvent) -> None:
        event.acceptProposedAction()
        # event.accept()
        super().dropEvent(event)  # type: ignore
        # if event.mimeData().hasFormat('text/plain'):
        self.dragdrop_signal.emit(self._key, event, event.mimeData().text())  # type: ignore
        return

    @qt.pyqtSlot(qt.QKeyEvent)
    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        """"""
        event.accept()
        super().keyPressEvent(event)  # type: ignore
        self.keypress_signal.emit(self._key, event)  # type: ignore
        return

    @qt.pyqtSlot(qt.QKeyEvent)
    def keyReleaseEvent(self, event: qt.QKeyEvent) -> None:
        """"""
        event.accept()
        super().keyReleaseEvent(event)  # type: ignore
        self.keyrelease_signal.emit(self._key, event)  # type: ignore
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusInEvent(self, event: qt.QFocusEvent) -> None:
        """"""
        event.accept()
        super().focusInEvent(event)  # type: ignore
        self.focusin_signal.emit(self._key, event)  # type: ignore
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusOutEvent(self, event: qt.QFocusEvent) -> None:
        """"""
        event.accept()
        super().focusOutEvent(event)  # type: ignore
        self.focusout_signal.emit(self._key, event)  # type: ignore
        return

    def sync_widg(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        ATTENTION:
        Only runs if self.get_item()._v_layout is not None!

        ATTENTION:
        Before, this function had the following code:

            if self.get_item().get_state().forcePolish:
                self.style().unpolish(self)
                self.style().polish(self)
                self.update()
                self.get_item().get_state().forcePolish = False

        Now not anymore. Probably because of the different way icons are given
        to the buttons?

        WARNING:
        I don't invoke this method anymore in:
            - item_btn.py
            -
        """
        assert threading.current_thread() is threading.main_thread()
        assert isinstance(self, qt.QWidget)
        if callback is not None:
            callback(callbackArg)
        return

    def repolish(self) -> None:
        """"""
        self.style().unpolish(self)  # type: ignore
        self.style().polish(self)  # type: ignore
        self.update()  # type: ignore
        return

    def set_normal_stylesheet(self, *args, **kwargs) -> None:
        """"""
        raise NotImplementedError()
        return

    def set_blink_stylesheet(self) -> None:
        """"""
        raise NotImplementedError()
        return

    def update_style(self, *args, **kwargs) -> None:
        """"""
        try:
            self.set_normal_stylesheet()
        except:
            pass
        return

    def blink(
        self,
        itemlbl: Optional[_item_lbl_.ItemLbl] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """
        Make this ItemWidget() - probably it's an ItemBtn() - blink, along with
        the ItemLbl() if given.
        """
        # $ Apply stylesheet
        # Apply the blink stylesheet on the ItemBtn() - and the ItemLbl() if
        # given. Then set the stylesheet properties.
        try:
            self._blinking = True
            self.setProperty("blink_01", True)  # type: ignore
            self.setProperty("blink_02", False)  # type: ignore
            self.set_blink_stylesheet()
            self.repolish()
            if itemlbl is not None:
                itemlbl._blinking = True
                itemlbl.setProperty("blink_01", True)
                itemlbl.setProperty("blink_02", False)
                itemlbl.set_blink_stylesheet()
                itemlbl.repolish()
        except Exception:
            # wrapped C/C++ object deleted
            traceback.print_exc()
            self.__blink_finish(
                itemlbl,
                callback,
                callbackArg,
            )
            return

        # $ Launch blink method
        # Launch the method to start blinking. This method will invoke itself
        # until the cntr has reached zero.
        qt.QTimer.singleShot(
            150,
            functools.partial(
                self.__blink_next,
                6,
                itemlbl,
                callback,
                callbackArg,
            ),
        )
        return

    def __blink_next(
        self,
        cntr: int,
        itemlbl: Optional[_item_lbl_.ItemLbl],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        # $ Stop if requested
        # The 'self._blinking' attribute is off if the 'blink_stop()' method
        # has been invoked! Immediately stop blinking and make a shortcut to the
        # finish.
        if not self._blinking:
            self.__blink_finish(
                itemlbl,
                callback,
                callbackArg,
            )
            return

        # $ Perform the blink operation
        try:
            self.setProperty("blink_01", not self.property("blink_01"))  # type: ignore
            self.setProperty("blink_02", not self.property("blink_02"))  # type: ignore
            self.repolish()
            if itemlbl is not None:
                itemlbl.setProperty(
                    "blink_01", not itemlbl.property("blink_01")
                )
                itemlbl.setProperty(
                    "blink_02", not itemlbl.property("blink_02")
                )
                itemlbl.repolish()
        except Exception:
            # wrapped C/C++ object deleted
            traceback.print_exc()
            self.__blink_finish(
                itemlbl,
                callback,
                callbackArg,
            )
            return

        # $ Relaunch method
        # Relaunch this method for the next blink operation, unless the cntr has
        # reached zero.
        if cntr > 0:
            qt.QTimer.singleShot(
                150,
                functools.partial(
                    self.__blink_next,
                    cntr - 1,
                    itemlbl,
                    callback,
                    callbackArg,
                ),
            )
            return
        self.__blink_finish(
            itemlbl,
            callback,
            callbackArg,
        )
        return

    def __blink_finish(
        self,
        itemlbl: Optional[_item_lbl_.ItemLbl],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        self._blinking = False
        if itemlbl is not None:
            itemlbl._blinking = False
        try:
            self.set_normal_stylesheet()
            self.repolish()
            if itemlbl is not None:
                itemlbl.set_normal_stylesheet()
                itemlbl.repolish()
        except Exception:
            # wrapped C/C++ object deleted
            traceback.print_exc()
            pass

        # Invoke the callback that was given at the invocation of the 'blink()'
        # method.
        if callback is not None:
            callback(callbackArg)

        # If blinking was interrupted through the 'blink_stop()' method, invoke
        # the callback given to that method as well.
        blinkstop_callback = self._blinkstop_callback
        blinkstop_callbackArg = self._blinkstop_callbackArg
        self._blinkstop_callback = None
        self._blinkstop_callbackArg = None
        if blinkstop_callback is not None:
            blinkstop_callback(blinkstop_callbackArg)
        return

    def blink_stop(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if self._blinkstop_callback is not None:
            purefunctions.printc(
                f"\nERROR: blink_stop() was invoked twice!\n",
                color="error",
            )
            assert False
        self._blinkstop_callbackArg = callbackArg
        self._blinkstop_callback = callback
        self._blinking = False
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
                    f"Trying to kill ItemWidget() {q}{self._key}{q} twice!"
                )
            self.dead = True

        # $ Disconnect signals
        # To disconnect all signals, I used to do that in a loop. But new insights revealed this is
        # not needed.
        for sig, sigtxt in (
            (self.leftclick_signal, "leftclick_signal"),  # type: ignore
            (self.ctrl_leftclick_signal, "ctrl_leftclick_signal"),  # type: ignore
            (self.rightclick_signal, "rightclick_signal"),  # type: ignore
            (self.dragstart_signal, "dragstart_signal"),  # type: ignore
            (self.dragenter_signal, "dragenter_signal"),  # type: ignore
            (self.dragleave_signal, "dragleave_signal"),  # type: ignore
            (self.dragdrop_signal, "dragdrop_signal"),  # type: ignore
            (self.keypress_signal, "keypress_signal"),  # type: ignore
            (self.keyrelease_signal, "keyrelease_signal"),  # type: ignore
            (self.focusin_signal, "focusin_signal"),  # type: ignore
            (self.focusout_signal, "focusout_signal"),  # type: ignore
        ):
            try:
                sig.disconnect()
            except:
                purefunctions.printc(
                    f"\nERROR: Cannot disconnect signal {q}{sigtxt}{q} from ItemWidget() "
                    f"{q}{self._key}{q}\n",
                    color="error",
                )
                pass

        self._key = None
        self._ownerRef = None
        try:
            self.hide()  # type: ignore
            self.setParent(None)  # type: ignore
            self.deleteLater()  # type: ignore
        except:
            traceback.print_exc()
        if callback is not None:
            callback(callbackArg)
        return
