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
from components.decorators import ref
import os, weakref
import qt, data, gui, purefunctions, functions
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.items.item as _cm_
import bpathlib.tool_obj as _tool_obj_
import home_toolbox.contextmenus.toolmanager_contextmenu as _tm_popup_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import os_checker

TYPE_CHECKING = False
if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class Folder(_cm_.Folder):
    __slots__ = ("_toolObjRef",)

    class Status(_cm_.Item.Status):
        __slots__ = ()

        def __init__(self, item: Folder) -> None:
            """"""
            super().__init__(item)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """"""
            _cm_.Item.Status.sync_state(
                self,
                refreshlock,
                callback,
                callbackArg,
            )
            return

    def __init__(
        self,
        rootdir: Root,
        parent: Optional[Folder],
        name: str,
        state: Folder.Status,
        toolObj: Optional[
            Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]
        ] = None,
    ) -> None:
        """"""
        assert isinstance(rootdir, Root) if rootdir is not None else True
        assert isinstance(parent, Folder) if parent is not None else True
        assert isinstance(state, Folder.Status) if state is not None else True
        if toolObj is not None:
            assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
                toolObj, _tool_obj_.ToolpathObj
            )
        self._toolObjRef = weakref.ref(toolObj) if toolObj is not None else None
        if parent is not None:
            depth = parent._depth + 1
        else:
            assert rootdir is self
            assert parent is None
            depth = 0
        state = Folder.Status(self) if state is None else state
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name=name,
            depth=depth,
            state=state,
        )
        return

    def get_state(self) -> Folder.Status:
        return self._state

    @ref
    def get_toolObj(
        self,
    ) -> Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]:
        return self._toolObjRef  # noqa

    def set_toolObj(
        self, toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]
    ):
        self._toolObjRef = None
        self._toolObjRef = weakref.ref(toolObj) if toolObj is not None else None
        return

    def printFiles(self, spacer: str) -> None:
        """Print all items recursively.

        Also mention for each item if the "changed" attribute is True.
        """
        for item in self._childlist:
            if isinstance(item, Folder):
                line = spacer + "> " + item.get_name()
                changed = (
                    " -> changes "
                    if hasattr(item.get_state(), "asterisk")
                    and item.get_state().has_asterisk()
                    else ""
                )
                print(line + changed)
                item.printFiles(spacer + "    ")
            else:
                line = spacer + "- " + item.get_name()
                changed = (
                    " -> changes "
                    if hasattr(item.get_state(), "asterisk")
                    and item.get_state().has_asterisk()
                    else ""
                )
                print(line + changed)
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

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        if self.get_toolObj() is None:
            return
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _tm_popup_.ToolContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
            toolObj=self.get_toolObj(),
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLineedit(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLineedit(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLineedit(event)
        self.show_contextmenu_itemBtn(event)
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def info(_key: str) -> None:
            super(Folder, self).leftclick_itemBtn(None)
            return

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
                        text=str(f"Failed to open:<br> " f"{q}{abspath}{q}"),
                    )
            else:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Problem",
                    text=str(
                        f"The file/folder you look for doesn{q}t exist:<br> "
                        f"{q}{abspath}{q}"
                    ),
                )
            return

        def path(_key: str) -> None:
            return

        def delete(_key: str) -> None:
            unique_id: Optional[str] = self.get_toolObj().get_unique_id()
            if unique_id is None:
                purefunctions.printc(
                    f"ERROR: Cannot delete {q}None{q} tool!",
                    color="error",
                )
                return

            def start(*_args) -> None:
                print("Request to delete tool")
                data.toolman.delete_tool(
                    toolmanObj=self.get_toolObj(),
                    callback=finish,
                    callbackArg=None,
                )
                return

            def finish(success: bool, *_args) -> None:
                if success:
                    data.toolman.send_delete_tool_msg(unique_id)
                return

            start()
            return

        funcs = {
            "info": info,
            "navigate": navigate,
            "path": path,
            "delete": delete,
            "help": nop,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class File(_cm_.File):
    __slots__ = ("_toolObjRef",)

    class Status(_cm_.Item.Status):
        __slots__ = ()

        def __init__(self, item: File) -> None:
            """"""
            super().__init__(item)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """"""
            _cm_.Item.Status.sync_state(
                self,
                refreshlock,
                callback,
                callbackArg,
            )
            return

    def __init__(
        self,
        rootdir: Root,
        parent: Folder,
        name: str,
        state: File.Status,
        toolObj: Optional[
            Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]
        ] = None,
    ) -> None:
        """"""
        # assert isinstance(rootdir, Dir)       if rootdir is not None else True
        # assert isinstance(parent, Dir)        if rootdir is not None else True
        # assert isinstance(state, File.Status) if state is not None else True
        if toolObj is not None:
            assert isinstance(toolObj, _tool_obj_.ToolmanObj) or isinstance(
                toolObj, _tool_obj_.ToolpathObj
            )
        self._toolObjRef = weakref.ref(toolObj) if toolObj is not None else None
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name=name,
            state=state,
        )
        return

    def get_state(self) -> File.Status:
        return self._state

    @ref
    def get_toolObj(
        self,
    ) -> Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]:
        return self._toolObjRef  # noqa

    def set_toolObj(
        self, toolObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj]
    ) -> None:
        """"""
        self._toolObjRef = None
        self._toolObjRef = weakref.ref(toolObj) if toolObj is not None else None
        return


class Root(Folder, _cm_.Root):
    __slots__ = _cm_.Root.get_slots()

    def __init__(
        self,
        name: str,
        state: _cm_.Item.Status,
    ) -> None:
        """For all Dir()- and File()-items in the dirtree, the self._state
        variable gets initialized in the constructors Dir() and File().

        That approach is not possible for the toolmanager.
        """
        _cm_.Root.__init__(
            self,
            abspath=name,
        )
        Folder.__init__(
            self,
            rootdir=self,
            parent=None,
            name=name,
            state=state,
        )
        return

    #! ==========[ IMPLEMENT ABSTRACT METHODS ]========== !#
    def get_relpath(self) -> str:
        return _cm_.Root.get_relpath(self)

    def get_abspath(self) -> str:
        return _cm_.Root.get_abspath(self)

    def set_abspath(self, abspath: str) -> None:
        _cm_.Root.set_abspath(self, abspath)
        return

    def get_parent(self) -> None:
        return _cm_.Root.get_parent(self)

    def set_parent(self, parent) -> None:
        _cm_.Root.set_parent(self, parent)
        return

    def get_rootdir(self) -> Root:
        return _cm_.Root.get_rootdir(self)

    def get_chassis(self):
        return _cm_.Root.get_chassis(self)

    def get_chassis_body(self):
        return _cm_.Root.get_chassis_body(self)

    def get_nr_visible_items(self):
        return _cm_.Root.get_nr_visible_items(self)

    def self_destruct(
        self,
        killParentLink: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        hdd_and_sa_op: bool = False,
        delete_from_hdd: bool = False,
        notify_project: bool = True,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill Item {q}{self._name}{q} twice!"
                )
            self.dead = True
        _cm_.Root.self_destruct(
            self,
            killParentLink=killParentLink,
            callback=callback,
            callbackArg=callbackArg,
            hdd_and_sa_op=hdd_and_sa_op,
            delete_from_hdd=delete_from_hdd,
            notify_project=notify_project,
            superfunc=_cm_.Folder.self_destruct,
            death_already_checked=True,
        )
        return
