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
    import tree_widget.widgets.item_arrow as _item_arrow_
    import tree_widget.widgets.item_lbl as _item_lbl_
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemActionInnerBtn(_cm_widget_.ItemWidget, qt.QPushButton):
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
        qt.QPushButton.__init__(self)
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemActionBtn",
            owner=owner,
        )
        return


class ItemActionBtn(_cm_widget_.ItemWidget, qt.QFrame):
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
        """
        :param owner:  The Item()-object owning this ItemActionBtn().
        """
        try:
            qt.QFrame.__init__(
                self,
                owner.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            qt.QFrame.__init__(self)
        # The key 'ItemActionBtn' given here, is saved by the superclass ItemWidget().
        # The moment you create a ContextMenuRoot() instance (so you create a popup),
        # you pass this ItemActionBtn() instance to the ContextMenuRoot()'s set_owner()
        # method. Within that method, the key 'ItemActionBtn' gets saved as the
        # toplevel key for that popup.
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemActionBtn",
            owner=owner,
        )
        self.__btn = ItemActionInnerBtn(owner)
        self.__btn.leftclick_signal.connect(self.leftclick_signal)
        self.__btn.ctrl_leftclick_signal.connect(self.ctrl_leftclick_signal)
        self.__btn.rightclick_signal.connect(self.rightclick_signal)
        self.__btn.dragstart_signal.connect(self.dragstart_signal)
        self.__btn.dragenter_signal.connect(self.dragenter_signal)
        self.__btn.dragleave_signal.connect(self.dragleave_signal)
        self.__btn.dragdrop_signal.connect(self.dragdrop_signal)
        self.__btn.keypress_signal.connect(self.keypress_signal)
        self.__btn.keyrelease_signal.connect(self.keyrelease_signal)
        self.__btn.focusin_signal.connect(self.focusin_signal)
        self.__btn.focusout_signal.connect(self.focusout_signal)

        self.setLayout(qt.QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.__btn)
        self.setProperty("_hover", False)

        # $ Stylesheet
        self.set_normal_stylesheet()
        # self.set_normal_stylesheet() -> there is already a 'self.rescale()'
        # call in the 'bind_guiVars()' method.
        return

    def set_normal_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(
            f"""
            QFrame {{
                margin: 0px;
                padding: 0px;      
                background-color: transparent;
                border: none;
            }}
            QFrame[_hover = true] {{
                background-color: {data.theme['indication']['hover']};
            }}
        """
        )
        self.__btn.setStyleSheet(_btn_style_.get_action_btn_stylesheet())
        return

    def set_blink_stylesheet(self) -> None:
        """"""
        self.setStyleSheet(
            f"""
            QFrame {{
                margin: 0px;
                padding: 0px;      
                background-color: transparent;
                border: none;
            }}
            QFrame[_hover = true] {{
                background-color: {data.theme['indication']['hover']};
            }}
        """
        )
        self.__btn.setStyleSheet(_btn_style_.get_action_btn_blink_stylesheet())
        return

    def setProperty(self, name: str, value: Any) -> bool:
        """"""
        super().setProperty(name, value)
        return self.__btn.setProperty(name, value)

    def repolish(self) -> None:
        """"""
        super().repolish()
        self.__btn.style().unpolish(self.__btn)
        self.__btn.style().polish(self.__btn)
        self.__btn.update()
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
        state = item.get_state()
        iconpath = state.action_iconpath
        for s in state.action_icon_suffixes:
            iconpath = iconpath.replace(".png", f"({s}).png")
        icon = iconfunctions.get_qicon(iconpath)
        if self.__btn.icon() is icon:
            print("icon already set")
        else:
            self.__btn.setIcon(icon)

        # $ 3. Icon size
        outer_size = data.get_general_icon_pixelsize(is_inner=False)
        inner_size = min(
            data.get_general_icon_pixelsize(is_inner=True),
            outer_size - 4,
        )
        self.setFixedHeight(outer_size)
        self.__btn.setIconSize(qt.create_qsize(inner_size - 2, inner_size - 2))

        # $ 4. Set text
        self.__btn.setText(state.action_txt)

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

        self.setProperty("_hover", True)
        self.repolish()

        # $ 1. itemLbl
        lbl: _item_lbl_.ItemLbl = item.get_widget(key="itemLbl")
        if lbl is not None:
            lbl.setProperty("_hover", True)
            lbl.repolish()

        # $ 2. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", True)
            arrow.repolish()

        # #$ 3. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', True)
        #     cchbx.repolish()
        # #$ 4. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', True)
        #     hchbx.repolish()
        # #$ 5. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', True)
        #     hglass.repolish()
        # #$ 6. cfgchbx
        # cfgchbx:_item_chbx_.CfgChbx = item.get_widget(key='cfgchbx')
        # if cfgchbx is not None:
        #     cfgchbx.setProperty('_hover', True)
        #     cfgchbx.repolish()
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
        self.setProperty("_hover", False)
        self.repolish()

        # $ 1. itemLbl
        lbl: _item_lbl_.ItemLbl = item.get_widget(key="itemLbl")
        if lbl is not None:
            lbl.setProperty("_hover", False)
            lbl.repolish()

        # $ 2. itemArrow
        arrow: _item_arrow_.ItemArrow = item.get_widget(key="itemArrow")
        if arrow is not None:
            arrow.setProperty("_hover", False)
            arrow.repolish()

        # #$ 3. cchbx
        # cchbx:Union[_item_chbx_.CDirChbx, _item_chbx_.CFileChbx] = item.get_widget(key='cchbx')
        # if cchbx is not None:
        #     cchbx.setProperty('_hover', False)
        #     cchbx.repolish()
        # #$ 4. hchbx
        # hchbx:Union[_item_chbx_.HDirChbx, _item_chbx_.HFileChbx] = item.get_widget(key='hchbx')
        # if hchbx is not None:
        #     hchbx.setProperty('_hover', False)
        #     hchbx.repolish()
        # #$ 5. hglass
        # hglass:_item_chbx_.HDirGlass = item.get_widget(key='hglass')
        # if hglass is not None:
        #     hglass.setProperty('_hover', False)
        #     hglass.repolish()
        # #$ 6. cfgchbx
        # cfgchbx:_item_chbx_.CfgChbx = item.get_widget(key='cfgchbx')
        # if cfgchbx is not None:
        #     cfgchbx.setProperty('_hover', False)
        #     cfgchbx.repolish()
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
                    f"Trying to kill ItemActionBtn() {q}{self._key}{q} twice!"
                )
            self.dead = True

        def finish(*args) -> None:
            self.__btn.setParent(None)  # noqa
            self.__btn = None
            _cm_widget_.ItemWidget.self_destruct(
                self,
                callback=callback,
                callbackArg=callbackArg,
                death_already_checked=True,
            )
            return

        self.__btn.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return
