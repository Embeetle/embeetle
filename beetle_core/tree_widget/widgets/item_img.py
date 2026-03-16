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
import functools, threading
import qt, data, iconfunctions
import gui.stylesheets.button as _btn_style_
import tree_widget.widgets.item_widget as _cm_widget_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_

from various.kristofstuff import *


class ItemImg(_cm_widget_.ItemWidget, qt.QPushButton):
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
        """The ItemImg()-object belongs to an Item()-instance (saved in its
        _v_widgets['itemImg'] attribute).

        :param owner: The Item()-object owning this ItemBtn().
        """
        try:
            qt.QPushButton.__init__(
                self,
                owner.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            qt.QPushButton.__init__(self)
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemImg",
            owner=owner,
        )
        # Set style
        self.__prev_imgpath = ""
        self.setProperty("open", False)
        self.setProperty("closed", False)
        # self.set_normal_stylesheet() -> there is already a 'self.rescale()' call in the
        # 'bind_guiVars()' method.
        return

    """-------------------------------------------------------------------"""
    """ 1. ITEMIMG-ONLY STUFF                                             """
    """-------------------------------------------------------------------"""

    def is_stylesheet_uptodate(self) -> bool:
        """"""
        imgpath = self.get_item().get_state().imgpath
        if imgpath != self.__prev_imgpath:
            return False
        return True

    def set_normal_stylesheet(self) -> None:
        """"""
        imgpath = self.get_item().get_state().imgpath
        self.__prev_imgpath = imgpath
        self.setStyleSheet(_btn_style_.get_btn_stylesheet())
        return

    """-------------------------------------------------------------------"""
    """ 2. SYNCHRONIZATIONS                                               """
    """-------------------------------------------------------------------"""

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
        if item.get_state().open:
            self.setProperty("open", True)
            self.setProperty("closed", False)
        else:
            self.setProperty("open", False)
            self.setProperty("closed", True)
        imgpath = item.get_state().imgpath
        _icon_ = iconfunctions.get_qicon(imgpath)
        if self.icon() is _icon_:
            print("icon already set")
        else:
            self.setIcon(_icon_)

        # $ 3. Icon size
        inner_size = data.get_general_icon_pixelsize(is_inner=True)
        outer_size = data.get_general_icon_pixelsize(is_inner=False)
        self.setFixedSize(
            int(outer_size * 1.2),
            outer_size,
        )
        self.setIconSize(
            qt.create_qsize(inner_size, inner_size),
        )
        if not self.is_stylesheet_uptodate():
            self.set_normal_stylesheet()

        # * Finish
        if refreshlock:
            item.release_refresh_mutex()
        if callback is not None:
            callback(callbackArg)
        return

    """-------------------------------------------------------------------"""
    """ 3. DEATH                                                          """
    """-------------------------------------------------------------------"""

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
                    f"Trying to kill ItemImg() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
