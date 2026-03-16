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
import bpathlib.path_power as _pp_
import tree_widget.widgets.item_widget as _cm_widget_

if TYPE_CHECKING:
    import tree_widget.widgets.item_arrow as _item_arrow_
    import tree_widget.widgets.item_lbl as _item_lbl_
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemBtn(_cm_widget_.ItemWidget, qt.QPushButton):
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
        """The ItemBtn()-object belongs to an Item()-instance (saved in its
        _v_itemBtn attribute). It is the most important widget of the Item().

        :param owner: The Item()-object owning this ItemBtn().
        """
        try:
            qt.QPushButton.__init__(
                self,
                owner.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            qt.QPushButton.__init__(self)
        # The key 'itemBtn' given here, is saved by the superclass ItemWidget().
        # The moment you create a ContextMenuRoot() instance (so you create a popup),
        # you pass this ItemBtn() instance to the ContextMenuRoot()'s set_owner()
        # method. Within that method, the key 'itemBtn' gets saved as the
        # toplevel key for that popup.
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemBtn",
            owner=owner,
        )
        # $ Movie variables
        self.__moviePlaying: bool = False
        self.__movieLbl: Optional[qt.QLabel] = None
        self.__movie: Optional[qt.QMovie] = None
        self.__moviepath: Optional[str] = None

        # $ Stylesheet
        self.set_normal_stylesheet()
        # self.set_normal_stylesheet() -> there is already a 'self.rescale()'
        # call in the 'bind_guiVars()' method.
        return

    def set_normal_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(_btn_style_.get_btn_stylesheet())
        return

    def set_blink_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(_btn_style_.get_blink_btn_stylesheet())
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
        ATTENTION:
        Only runs if self.get_item()._v_layout is not None!
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
        _state_ = item.get_state()
        iconpath = (
            _state_.openIconpath if _state_.open else _state_.closedIconpath
        )
        for s in _state_.icon_suffixes:
            iconpath = iconpath.replace(".png", f"({s}).png")
        _icon_ = iconfunctions.get_qicon(iconpath)
        if self.icon() is _icon_:
            print("icon already set")
        else:
            self.setIcon(_icon_)

        # $ 3. Icon size
        inner_size = data.get_general_icon_pixelsize(is_inner=True)
        outer_size = data.get_general_icon_pixelsize(is_inner=False)
        self.setFixedSize(outer_size, outer_size)
        self.setIconSize(qt.create_qsize(inner_size, inner_size))

        # $ 4. Movie
        if _state_.busyBtn:
            if self.__movie is None:
                self.setup_movie()
            self.__movie.setScaledSize(
                qt.create_qsize(inner_size - 2, inner_size - 2)
            )
            self.__movieLbl.setFixedWidth(outer_size)
            self.__movieLbl.setFixedHeight(outer_size)
            if not self.__moviePlaying:
                self.__movieLbl.show()
                self.__movie.start()
                self.__moviePlaying = True
        else:
            if self.__moviePlaying:
                self.__movie.stop()
                self.__movieLbl.hide()
                self.__moviePlaying = False

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

        # $ 1. itemLbl
        lbl: _item_lbl_.ItemLbl = item.get_widget(key="itemLbl")
        if lbl is not None:
            lbl.setProperty("_hover", True)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

        # $ 2. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", True)
            arrow.style().unpolish(arrow)
            arrow.style().polish(arrow)

        # #$ 3. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', True)
        #     cchbx.style().unpolish(cchbx)
        #     cchbx.style().polish(cchbx)
        # #$ 4. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', True)
        #     hchbx.style().unpolish(hchbx)
        #     hchbx.style().polish(hchbx)
        # #$ 5. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', True)
        #     hglass.style().unpolish(hglass)
        #     hglass.style().polish(hglass)
        # #$ 6. cfgchbx
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

        # $ 1. itemLbl
        lbl: _item_lbl_.ItemLbl = item.get_widget(key="itemLbl")
        if lbl is not None:
            lbl.setProperty("_hover", False)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

        # $ 2. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", False)
            arrow.style().unpolish(arrow)
            arrow.style().polish(arrow)

        # #$ 3. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', False)
        #     cchbx.style().unpolish(cchbx)
        #     cchbx.style().polish(cchbx)
        # #$ 4. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', False)
        #     hchbx.style().unpolish(hchbx)
        #     hchbx.style().polish(hchbx)
        # #$ 5. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', False)
        #     hglass.style().unpolish(hglass)
        #     hglass.style().polish(hglass)
        # #$ 6. cfgchbx
        # cfgchbx:_item_chbx_.CfgChbx = item.get_widget(key='cfgchbx')
        # if cfgchbx is not None:
        #     cfgchbx.setProperty('_hover', False)
        #     cfgchbx.style().unpolish(cfgchbx)
        #     cfgchbx.style().polish(cfgchbx)
        return

    def setup_movie(self) -> None:
        """"""
        bckground = "#00ffffff"
        self.__moviepath = iconfunctions.get_icon_abspath(
            "icons/loading_animation/hourglass_animation/hourglass.gif"
        )
        self.__moviePlaying = False
        self.__movieLbl = qt.QLabel()
        self.__movieLbl.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bckground};
                border-style: none;
                padding: 0px;
                margin:0px;
            }}
        """
        )
        self.__movie = qt.QMovie(self.__moviepath)
        self.__movie.setCacheMode(qt.QMovie.CacheMode.CacheAll)
        self.__movieLbl.setMovie(self.__movie)
        self.__movieLbl.setParent(self)
        self.__movieLbl.hide()
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
                    f"Trying to kill ItemBtn() {q}{self._key}{q} twice!"
                )
            self.dead = True

        if self.__movie is not None:
            if qt.sip.isdeleted(self.__movie):
                return
            self.__movie.deleteLater()
            self.__movie = None
            self.__movieLbl.setParent(None)  # noqa
            self.__movieLbl.deleteLater()
            self.__movieLbl = None
            self.__moviePlaying = None

        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
