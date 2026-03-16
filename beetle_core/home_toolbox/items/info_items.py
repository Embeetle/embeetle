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
import datetime, os, traceback
import qt, data, purefunctions, functions, gui, functools
import fnmatch as _fn_
import bpathlib.tool_obj as _tool_obj_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_lbl as _cm_lbl_
import home_toolbox.items.item as _tm_
import home_toolbox.contextmenus.info_items_contextmenu as _tm_info_popup_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import tree_widget.items.item as _cm_
import os_checker

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class UniqueIDNameItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: UniqueIDNameItem) -> None:
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
            unique_id_name_item: UniqueIDNameItem = cast(
                UniqueIDNameItem,
                self.get_item(),
            )
            if unique_id_name_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    unique_id_name_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                if (
                    (tool_obj.get_category() == "FLASHTOOL")
                    and (tool_obj.get_unique_id() is not None)
                    and _fn_.fnmatch(
                        name=tool_obj.get_unique_id().lower(),
                        pat="*built*in*",
                    )
                ):
                    lbltext = f"{'name:'.ljust(11)} built_in"
                else:
                    lbltext = f"{'name:'.ljust(11)} {tool_obj.get_version_info('name')}"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/symbols/occurrence_kind/name_purple.png"
                    )
                    self.openIconpath = (
                        "icons/symbols/occurrence_kind/name_purple.png"
                    )
                else:
                    self.closedIconpath = (
                        "icons/symbols/occurrence_kind/name.png"
                    )
                    self.openIconpath = "icons/symbols/occurrence_kind/name.png"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            start()
            return

    __slots__ = ()

    def __init__(
        self,
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="UniqueIDNameItem",
            state=UniqueIDNameItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
        )
        # assert isinstance(rootdir, _tm_.Root)
        # assert isinstance(parent, _tm_.Dir)
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

    # def self_destruct(self,
    #                   killParentLink:bool=True,
    #                   callback:Optional[Callable]=None,
    #                   callbackArg:Any=None,
    #                   death_already_checked:bool=False,
    #                   ) -> None:
    #     print(f'UniqueIDNameItem().self_destruct(callback = {callback})')
    #     raise RuntimeError()
    #     super().self_destruct(
    #         killParentLink        = killParentLink,
    #         callback              = callback,
    #         callbackArg           = callbackArg,
    #         death_already_checked = death_already_checked,
    #     )
    #     return


class UniqueIDItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: UniqueIDItem) -> None:
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
            unique_id_item: UniqueIDItem = cast(
                UniqueIDItem,
                self.get_item(),
            )
            if unique_id_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    unique_id_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                lbltext = f"{'unique id:'.ljust(11)} {tool_obj.get_unique_id()}"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/symbols/occurrence_kind/name_purple.png"
                    )
                    self.openIconpath = (
                        "icons/symbols/occurrence_kind/name_purple.png"
                    )
                else:
                    self.closedIconpath = (
                        "icons/symbols/occurrence_kind/name.png"
                    )
                    self.openIconpath = "icons/symbols/occurrence_kind/name.png"
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
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="UniqueIDItem",
            state=UniqueIDItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
        )
        # assert isinstance(rootdir, _tm_.Root)
        # assert isinstance(parent, _tm_.Dir)
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
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


class VersionItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: VersionItem) -> None:
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
            version_item: VersionItem = cast(
                VersionItem,
                self.get_item(),
            )
            if version_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    version_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                version = tool_obj.get_version_info("version")
                suffix = tool_obj.get_version_info("suffix")
                if suffix is not None:
                    lbltext = f"{'version:'.ljust(11)} {version} ({suffix})"
                else:
                    lbltext = f"{'version:'.ljust(11)} {version}"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/tool_cards/card_version_purple.png"
                    )
                    self.openIconpath = (
                        "icons/tool_cards/card_version_purple.png"
                    )
                else:
                    self.closedIconpath = "icons/tool_cards/card_version.png"
                    self.openIconpath = "icons/tool_cards/card_version.png"
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
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="VersionItem",
            state=VersionItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
        )
        # assert isinstance(rootdir, _tm_.Root)
        # assert isinstance(parent, _tm_.Dir)
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
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


class BuilddateItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: BuilddateItem) -> None:
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
            builddate_item: BuilddateItem = cast(
                BuilddateItem,
                self.get_item(),
            )
            if builddate_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    builddate_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                date: Optional[Union[str, datetime.datetime]] = (
                    tool_obj.get_version_info("date")
                )
                if date is None:
                    lbltext = f"{'build date:'.ljust(11)} none"
                elif isinstance(date, str):
                    # This case normally shouldn't occur
                    print(f"WARNING: received build date of type str")
                    lbltext = f"{'build date:'.ljust(11)} {date}"
                else:
                    lbltext = (
                        f"{'build date:'.ljust(11)} {date.strftime('%d %b %Y')}"
                    )
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/tool_cards/card_date_purple.png"
                    )
                    self.openIconpath = "icons/tool_cards/card_date_purple.png"
                else:
                    self.closedIconpath = "icons/tool_cards/card_date.png"
                    self.openIconpath = "icons/tool_cards/card_date.png"
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
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="BuilddateItem",
            state=BuilddateItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
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


class BitnessItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: BitnessItem) -> None:
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
            bitness_item: BitnessItem = cast(
                BitnessItem,
                self.get_item(),
            )
            if bitness_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    bitness_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                bitness = tool_obj.get_version_info("bitness")
                if bitness is None:
                    lbltext = f"{'bitness:'.ljust(11)} none"
                else:
                    lbltext = f"{'bitness:'.ljust(11)} {bitness}"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    if bitness == "32b":
                        self.closedIconpath = (
                            "icons/tool_cards/card_32b_purple.png"
                        )
                        self.openIconpath = (
                            "icons/tool_cards/card_32b_purple.png"
                        )
                    else:
                        self.closedIconpath = (
                            "icons/tool_cards/card_64b_purple.png"
                        )
                        self.openIconpath = (
                            "icons/tool_cards/card_64b_purple.png"
                        )
                else:
                    if bitness == "32b":
                        self.closedIconpath = "icons/tool_cards/card_32b.png"
                        self.openIconpath = "icons/tool_cards/card_32b.png"
                    else:
                        self.closedIconpath = "icons/tool_cards/card_64b.png"
                        self.openIconpath = "icons/tool_cards/card_64b.png"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            start()
            return

    __slots__ = ()

    def __init__(
        self,
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="BitnessItem",
            state=BitnessItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
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


class LocationItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: LocationItem) -> None:
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
            location_item: LocationItem = cast(
                LocationItem,
                self.get_item(),
            )
            if location_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    location_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                location = tool_obj.get_abspath()
                if (location is None) or (location.lower() == "none"):
                    lbltext = f"{'location:'.ljust(11)} none"
                else:
                    if data.beetle_tools_directory in location:
                        location = location.replace(
                            data.beetle_tools_directory,
                            "<beetle-tools>",
                            1,
                        )
                    lbltext = f"{'location:'.ljust(11)} '{location}'"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/tool_cards/card_location_purple.png"
                    )
                    self.openIconpath = (
                        "icons/tool_cards/card_location_purple.png"
                    )
                else:
                    self.closedIconpath = "icons/tool_cards/card_location.png"
                    self.openIconpath = "icons/tool_cards/card_location.png"
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
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: Union[_tm_.Folder, _cm_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="LocationItem",
            state=LocationItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
        )
        # assert isinstance(rootdir, _tm_.Root)
        # assert isinstance(parent, _tm_.Dir)
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _tm_info_popup_.LocationContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
            toolmanObj=self.get_toolObj(),
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def navigate(_key: str) -> None:
            abspath = self.get_toolObj().get_abspath()
            if os.path.isfile(abspath) or os.path.isdir(abspath):
                abspath = abspath.replace("/", os.sep)

                try:
                    if os_checker.is_os("windows"):
                        purefunctions.subprocess_popen_without_startup_info(
                            f"explorer /select,{dq}{abspath}{dq}",
                            shell=False,
                        )
                    else:
                        if os.path.isfile(abspath):
                            purefunctions.subprocess_popen_without_startup_info(
                                ["xdg-open", os.path.dirname(abspath)]
                            )
                        else:
                            purefunctions.subprocess_popen_without_startup_info(
                                ["xdg-open", abspath]
                            )
                except Exception as e:
                    gui.dialogs.popupdialog.PopupDialog.ok(
                        icon_path="icons/dialog/stop.png",
                        title_text="Problem",
                        text=str(f"Failed to open:<br> " f"'{abspath}'"),
                    )
                    traceback.print_exc()
            else:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Problem",
                    text=f"The file/folder you look for doesn{q}t exist:<br> "
                    f"{q}{abspath}{q}",
                )
            return

        def path(_key: str) -> None:
            return

        funcs = {
            "navigate": navigate,
            "path": path,
            "help": nop,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class ToolprefixItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: ToolprefixItem) -> None:
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
            toolprefix_item: ToolprefixItem = cast(
                ToolprefixItem,
                self.get_item(),
            )
            if toolprefix_item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            tool_obj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj] = (
                cast(
                    Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
                    toolprefix_item.get_toolObj(),
                )
            )
            if tool_obj is None:
                if callback is not None:
                    callback(callbackArg)
                return

            def start(*args) -> None:
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
                if not tool_obj.has_version_info():
                    tool_obj.refresh_version_info(
                        callback=sync_self_b,
                        callbackArg=None,
                    )
                    return
                sync_self_b()
                return

            def sync_self_b(*args) -> None:
                toolprefix = tool_obj.get_toolprefix()
                if (toolprefix is None) or (toolprefix.lower() == "none"):
                    lbltext = f"{'TOOLPREFIX:'.ljust(11)} none"
                elif data.beetle_tools_directory in toolprefix:
                    toolprefix = toolprefix.replace(
                        data.beetle_tools_directory, "<beetle-tools>"
                    )
                    lbltext = f"{'TOOLPREFIX:'.ljust(11)} '{toolprefix}'"
                else:
                    tool_abspath = tool_obj.get_abspath()
                    if os.path.isfile(tool_abspath):
                        tool_abspath = os.path.dirname(tool_abspath).replace(
                            "\\", "/"
                        )
                    toolprefix = toolprefix.replace(
                        tool_abspath,
                        "<tool-folder>",
                        1,
                    )
                    lbltext = f"{'TOOLPREFIX:'.ljust(11)} '{toolprefix}'"
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                if data.toolman.is_external(tool_obj):
                    self.closedIconpath = (
                        "icons/tool_cards/card_toolprefix_purple.png"
                    )
                    self.openIconpath = (
                        "icons/tool_cards/card_toolprefix_purple.png"
                    )
                else:
                    self.closedIconpath = "icons/tool_cards/card_toolprefix.png"
                    self.openIconpath = "icons/tool_cards/card_toolprefix.png"
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
        toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
        rootdir: _tm_.Root,
        parent: _tm_.Folder,
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="ToolprefixItem",
            state=ToolprefixItem.Status(item=self),
            toolObj=toolObj,
        )
        assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
            toolObj, _tool_obj_.ToolpathObj
        )
        # assert isinstance(rootdir, _tm_.Root)
        # assert isinstance(parent, _tm_.Dir)
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
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
