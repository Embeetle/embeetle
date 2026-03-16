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
import qt, data
import functions, functools
import helpdocs.help_texts as _ht_
import sa_tab.items.item as _sa_tab_items_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_img as _cm_item_img_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

if TYPE_CHECKING:
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
    import bpathlib.tool_obj as _tool_obj_


class DependencyRootItem(_sa_tab_items_.Root):
    class Status(_sa_tab_items_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: DependencyRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.imgpath = "icons/dialog/help.png"
            self.closedIconpath = "icons/gen/balls.png"
            self.openIconpath = "icons/gen/balls.png"
            self.lblTxt = " source analyzer dependencies "
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
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = " *source analyzer dependencies"
            else:
                self.lblTxt = " source analyzer dependencies "

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__(
            name="dependency",
            state=DependencyRootItem.Status(item=self),
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
            itemImg=_cm_item_img_.ItemImg(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
        return

    def rightclick_itemLbl(self, event):
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemImg(self, event: Optional[qt.QEvent]) -> None:
        """"""
        super().leftclick_itemImg(event)
        _ht_.sa_dependencies()
        return

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QEvent, qt.QMouseEvent]
    ) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _toplvl_contextmenu_.ToplvlContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
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

        def _help(_key: str) -> None:
            self.leftclick_itemImg(None)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class BuildFolderItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: BuildFolderItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/folder/closed/build.png"
            self.openIconpath = "icons/folder/closed/build.png"
            self.lblTxt = "build folder ".ljust(19)
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
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            treepath_seg = data.current_project.get_treepath_seg()
            treepath_obj = treepath_seg.get_treepathObj("BUILD_DIR")
            self.set_asterisk(treepath_obj.has_asterisk())
            self.set_relevant(treepath_obj.is_relevant())
            self.set_readonly(treepath_obj.is_readonly())
            self.set_warning(treepath_obj.has_warning())
            self.set_error(treepath_obj.has_error())
            self.set_info_purple(treepath_obj.has_info_purple())
            self.set_info_blue(treepath_obj.has_info_blue())
            if self.has_asterisk():
                self.lblTxt = "*build folder".ljust(19)
            else:
                self.lblTxt = "build folder ".ljust(19)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[DependencyRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="build_folder_item",
            state=BuildFolderItem.Status(item=self),
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
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        data.dashboard.go_to_item(
            abspath=f"TreepathRootItem/BUILD_DIR",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        data.dashboard.go_to_item(
            abspath=f"TreepathRootItem/BUILD_DIR",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key: str) -> None:
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class MakefileItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: MakefileItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/file/file_mk.png"
            self.openIconpath = "icons/file/file_mk.png"
            self.lblTxt = "makefile ".ljust(19)
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
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            treepath_seg = data.current_project.get_treepath_seg()
            treepath_obj = treepath_seg.get_treepathObj("MAKEFILE")
            self.set_asterisk(treepath_obj.has_asterisk())
            self.set_relevant(treepath_obj.is_relevant())
            self.set_readonly(treepath_obj.is_readonly())
            self.set_warning(treepath_obj.has_warning())
            self.set_error(treepath_obj.has_error())
            self.set_info_purple(treepath_obj.has_info_purple())
            self.set_info_blue(treepath_obj.has_info_blue())
            if self.has_asterisk():
                self.lblTxt = "*makefile".ljust(19)
            else:
                self.lblTxt = "makefile ".ljust(19)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[DependencyRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="makefile_item",
            state=MakefileItem.Status(item=self),
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
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        data.dashboard.go_to_item(
            abspath=f"TreepathRootItem/MAKEFILE",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        data.dashboard.go_to_item(
            abspath=f"TreepathRootItem/MAKEFILE",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key: str) -> None:
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class BuildAutomationItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: BuildAutomationItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/tools/build_automation.png"
            self.openIconpath = "icons/tools/build_automation.png"
            self.lblTxt = "build folder ".ljust(19)
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
            item: BuildAutomationItem = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            # $ ToolpathSeg()
            # A segment of the Project()-instance. The ToolpathSeg() keeps track of the tools. It is
            # represented in the dashboard through the ToolRootItem().
            toolpath_seg: _toolpath_seg_.ToolpathSeg = (
                data.current_project.get_toolpath_seg()
            )

            # $ ToolpathObj()
            # The ToolpathSeg() keeps one ToolpathObj() per category. Each
            # of them is represented in the dashboard by a ToolpathItem().
            # Remember: the ToolpathObj() is just a shell. It only stores
            # the 'unique_id' and the 'cat_unicum'. It will always look for
            # the matching ToolmanObj() to return vital info.
            toolpath_obj: _tool_obj_.ToolpathObj = toolpath_seg.get_toolpathObj(
                cat_name="BUILD_AUTOMATION",
            )

            # $ ToolmanObj()
            # The Toolmanager()-singleton keeps a ToolmanObj() per tool it
            # finds.
            toolman_obj: _tool_obj_.ToolmanObj = (
                toolpath_obj.get_matching_toolmanObj()
            )
            if toolman_obj is not None:
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

            # & Set status stuff
            self.set_asterisk(toolpath_obj.has_asterisk())
            self.set_relevant(toolpath_obj.is_relevant())
            self.set_readonly(toolpath_obj.is_readonly())
            self.set_warning(toolpath_obj.has_warning())
            self.set_error(toolpath_obj.has_error())
            self.set_info_purple(toolpath_obj.has_info_purple())
            self.set_info_blue(toolpath_obj.has_info_blue())
            assert self.is_relevant() == True
            assert self.is_readonly() == False
            category = toolpath_obj.get_category().replace("_", " ").ljust(16)
            category_title = category.lower().title()

            # & Button
            self.closedIconpath = toolpath_obj.get_closedIconpath()
            self.openIconpath = toolpath_obj.get_openIconpath()

            # & Label
            if self.has_asterisk():
                self.lblTxt = str("*" + category_title + " ")
            else:
                self.lblTxt = str(category_title + "  ")
            self.lblTxt = self.lblTxt.ljust(19)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[DependencyRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="build_automation_item",
            state=BuildAutomationItem.Status(item=self),
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
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        data.dashboard.go_to_item(
            abspath=f"ToolRootItem/BUILD_AUTOMATION",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        data.dashboard.go_to_item(
            abspath=f"ToolRootItem/BUILD_AUTOMATION",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class CompilerToolchainItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: CompilerToolchainItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/tools/compiler_toolchain.png"
            self.openIconpath = "icons/tools/compiler_toolchain.png"
            self.lblTxt = "compiler toolchain ".ljust(19)
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
            item: CompilerToolchainItem = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            # $ ToolpathSeg()
            # A segment of the Project()-instance. The ToolpathSeg() keeps track of the tools. It is
            # represented in the dashboard through the ToolRootItem().
            toolpath_seg: _toolpath_seg_.ToolpathSeg = (
                data.current_project.get_toolpath_seg()
            )

            # $ ToolpathObj()
            # The ToolpathSeg() keeps one ToolpathObj() per category. Each
            # of them is represented in the dashboard by a ToolpathItem().
            # Remember: the ToolpathObj() is just a shell. It only stores
            # the 'unique_id' and the 'cat_unicum'. It will always look for
            # the matching ToolmanObj() to return vital info.
            toolpath_obj: _tool_obj_.ToolpathObj = toolpath_seg.get_toolpathObj(
                cat_name="COMPILER_TOOLCHAIN",
            )

            # $ ToolmanObj()
            # The Toolmanager()-singleton keeps a ToolmanObj() per tool it
            # finds.
            toolman_obj: _tool_obj_.ToolmanObj = (
                toolpath_obj.get_matching_toolmanObj()
            )
            if toolman_obj is not None:
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

            # & Set status stuff
            self.set_asterisk(toolpath_obj.has_asterisk())
            self.set_relevant(toolpath_obj.is_relevant())
            self.set_readonly(toolpath_obj.is_readonly())
            self.set_warning(toolpath_obj.has_warning())
            self.set_error(toolpath_obj.has_error())
            self.set_info_purple(toolpath_obj.has_info_purple())
            self.set_info_blue(toolpath_obj.has_info_blue())
            assert self.is_relevant() == True
            assert self.is_readonly() == False
            category = toolpath_obj.get_category().replace("_", " ").ljust(16)
            category_title = category.lower().title()

            # & Button
            self.closedIconpath = toolpath_obj.get_closedIconpath()
            self.openIconpath = toolpath_obj.get_openIconpath()

            # & Label
            if self.has_asterisk():
                self.lblTxt = str("*" + category_title + " ")
            else:
                self.lblTxt = str(category_title + "  ")
            self.lblTxt = self.lblTxt.ljust(19)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[DependencyRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="compiler_toolchain_item",
            state=CompilerToolchainItem.Status(item=self),
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
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        data.dashboard.go_to_item(
            abspath=f"ToolRootItem/COMPILER_TOOLCHAIN",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        data.dashboard.go_to_item(
            abspath=f"ToolRootItem/COMPILER_TOOLCHAIN",
            callback1=None,
            callbackArg1=None,
            callback2=None,
            callbackArg2=None,
        )
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key: str) -> None:
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
