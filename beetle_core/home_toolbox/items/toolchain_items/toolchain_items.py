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
import qt, data, functions, functools
import bpathlib.tool_obj as _tool_obj_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_img as _cm_img_
import tree_widget.widgets.item_lineedit as _cm_lineedit_
import home_toolbox.items.item as _tm_
import helpdocs.help_texts as _ht_
from various.kristofstuff import *


class ToolchainRootItem(_tm_.Root):
    class Status(_tm_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ToolchainRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = None
            self.openIconpath = None
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """

            def start(*args) -> None:
                if self.get_item() is None:
                    callback(callbackArg) if callback is not None else nop()
                    return
                if refreshlock:
                    if not self.get_item().acquire_refresh_mutex():
                        qt.QTimer.singleShot(
                            10,
                            functools.partial(
                                self.sync_state,
                                refreshlock,
                                callback,
                                callbackArg,
                            ),
                        )
                        return
                _tm_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args) -> None:
                self.lblTxt = (
                    "*Compiler Toolchain"
                    if self.has_asterisk()
                    else "Compiler Toolchain "
                )
                self.closedIconpath = f"icons/tools/compiler_toolchain.png"
                self.openIconpath = f"icons/tools/compiler_toolchain.png"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                (
                    self.get_item().release_refresh_mutex()
                    if refreshlock
                    else nop()
                )
                callback(callbackArg) if callback is not None else nop()
                return

            start()
            return

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__(
            name="ToolchainRootItem",
            state=ToolchainRootItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return


class ToolchainItem(_tm_.Folder):
    class Status(_tm_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ToolchainItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = None
            self.openIconpath = None
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            toolchain_item: ToolchainItem = cast(
                ToolchainItem,
                self.get_item(),
            )
            toolman_obj: _tool_obj_.ToolmanObj = cast(
                _tool_obj_.ToolmanObj,
                toolchain_item.get_toolObj(),
            )
            assert isinstance(toolman_obj, _tool_obj_.ToolmanObj)

            def start(*args) -> None:
                if self.get_item() is None:
                    callback(callbackArg) if callback is not None else nop()
                    return
                if refreshlock:
                    if not self.get_item().acquire_refresh_mutex():
                        qt.QTimer.singleShot(
                            10,
                            functools.partial(
                                self.sync_state,
                                refreshlock,
                                callback,
                                callbackArg,
                            ),
                        )
                        return
                _tm_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self_a,
                    callbackArg=None,
                )
                return

            def sync_self_a(*args) -> None:
                if not toolman_obj.has_version_info():
                    toolman_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                if data.toolman.is_external(toolman_obj):
                    if data.toolman.is_onpath(toolman_obj):
                        toolman_obj.set_info_purple(True)
                        toolman_obj.set_info_blue(False)
                    else:
                        toolman_obj.set_info_purple(False)
                        toolman_obj.set_info_blue(True)
                else:
                    toolman_obj.set_info_purple(False)
                    toolman_obj.set_info_blue(False)
                unique_id: Optional[str] = toolman_obj.get_unique_id()
                unique_id_shortname: Optional[str] = None
                if unique_id is None:
                    unique_id_shortname = "none"
                else:
                    unique_id_shortname: (
                        str
                    ) = toolman_obj.get_unicum().get_unique_id_shortname(
                        unique_id
                    )
                self.set_asterisk(toolman_obj.has_asterisk())
                self.set_relevant(toolman_obj.is_relevant())
                self.set_readonly(toolman_obj.is_readonly())
                self.set_warning(toolman_obj.has_warning())
                self.set_error(toolman_obj.has_error())
                self.set_info_purple(toolman_obj.has_info_purple())
                self.set_info_blue(toolman_obj.has_info_blue())
                assert self.has_asterisk() == False
                assert self.is_relevant() == True
                assert self.is_readonly() == False
                assert self.has_warning() == False
                assert self.has_error() == False
                self.lblTxt = (
                    f"*{unique_id_shortname}"
                    if self.has_asterisk()
                    else f"{unique_id_shortname} "
                )
                # Just showing the version nr is enough for TOOLCHAINs.
                self.lineeditTxt = str(toolman_obj.get_unique_id())
                self.closedIconpath = toolman_obj.get_unique_id_iconpath()
                self.openIconpath = toolman_obj.get_unique_id_iconpath()
                self.imgpath = "icons/dialog/info.png"
                if self.get_item()._v_layout is not None:
                    itemImg = self.get_item().get_widget(key="itemImg")
                    if self.has_info_purple() or self.has_info_blue():
                        itemImg.show()
                    else:
                        itemImg.hide()
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                (
                    self.get_item().release_refresh_mutex()
                    if refreshlock
                    else nop()
                )
                callback(callbackArg) if callback is not None else nop()
                return

            start()
            return

    __slots__ = ()

    def __init__(
        self,
        toolmanObj: _tool_obj_.ToolmanObj,
        rootdir: ToolchainRootItem,
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=rootdir,
            name="ToolchainItem",
            state=ToolchainItem.Status(item=self),
            toolObj=toolmanObj,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj)
        assert isinstance(rootdir, ToolchainRootItem)
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        # itemArrow = None
        # if len(self.get_childlist()) > 0:
        #     itemArrow = _cm_arrow_.ItemArrow(owner=self)
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
            itemImg=_cm_img_.ItemImg(owner=self),
        )

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemImg(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemImg(event)
        toolmanObj: _tool_obj_.ToolmanObj = self.get_toolObj()
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj)
        unique_id: Optional[str] = toolmanObj.get_unique_id()
        abspath: Optional[str] = toolmanObj.get_abspath()
        if unique_id is None:
            return
        if data.toolman.is_external(unique_id):
            if data.toolman.is_onpath(unique_id):
                _ht_.tool_on_path(
                    toolmanObj,
                )
            else:
                _ht_.tool_external(
                    toolmanObj,
                )
        return

    def rightclick_itemImg(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemImg(event)
        toolmanObj: _tool_obj_.ToolmanObj = self.get_toolObj()
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj)
        unique_id: Optional[str] = toolmanObj.get_unique_id()
        abspath: Optional[str] = toolmanObj.get_abspath()
        if unique_id is None:
            return
        if data.toolman.is_external(unique_id):
            if data.toolman.is_onpath(unique_id):
                _ht_.tool_on_path(
                    toolmanObj,
                )
            else:
                _ht_.tool_external(
                    toolmanObj,
                )
        return
