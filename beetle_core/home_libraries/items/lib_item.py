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
import os
import gui, purefunctions, functions
import bpathlib.file_power as _fp_
import home_libraries.items.item as _item_
import libmanager.libobj as _libobj_
import libmanager.libmanager as _libmanager_
import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
import dashboard.contextmenus.lib_contextmenu as _lib_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

if TYPE_CHECKING:
    import qt
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class LibItem(_item_.Folder, _lib_item_shared_.LibItemShared):
    """Item() in Home Window LIBRARIES tab, representing a specific library."""

    __slots__ = ()

    def __init__(
        self,
        libobj: _libobj_.LibObj,
        rootdir: _item_.Root,
        parent: _item_.Folder,
    ) -> None:
        """"""
        _lib_item_shared_.LibItemShared.__init__(
            self,
            superclass=_item_.Folder,
        )
        _item_.Folder.__init__(
            self,
            rootdir=rootdir,
            parent=parent,
            name=libobj.get_name(),
            state=_lib_item_shared_.Status(
                item=self,
                name=libobj.get_name(),
            ),
            libobj=libobj,
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        _lib_item_shared_.LibItemShared.init_guiVars(self)

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        _lib_item_shared_.LibItemShared.leftclick_itemBtn(self, event)

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.rightclick_itemBtn(self, event)

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.leftclick_itemLbl(self, event)

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.rightclick_itemLbl(self, event)

    def leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.leftclick_itemLineedit(self, event)

    def rightclick_itemLineedit(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.rightclick_itemLineedit(self, event)

    def leftclick_itemImg(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.leftclick_itemImg(self, event)

    def rightclick_itemImg(self, event: qt.QEvent) -> None:
        _lib_item_shared_.LibItemShared.rightclick_itemImg(self, event)

    def refill_children_later(self, callback, callbackArg) -> None:
        _lib_item_shared_.LibItemShared.refill_children_later(
            self, callback, callbackArg
        )

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        _lib_item_shared_.LibItemShared.contextmenuclick_itemBtn(self, key)

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _lib_contextmenu_.LibContextMenu(
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

    def delete_library(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """Delete this library from harddrive and refresh the Home Window
        LIBRARIES tab."""
        libobj: _libobj_.LibObj = self.get_libobj()
        library_abspath = libobj.get_local_abspath()
        css = purefunctions.get_css_tags()
        red = css["red"]
        green = css["green"]
        end = css["end"]

        def start(*args) -> None:
            if library_abspath is None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="INTERNAL ERROR",
                    text=str(
                        f"Embeetle experienced an internal error:<br>"
                        f"{red}libobj.get_local_abspath() is None{end}<br>"
                        f"Please close Embeetle and report this problem.<br>"
                    ),
                )
                finish()
                return
            if not os.path.isdir(library_abspath):
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="PROBLEM",
                    text=str(
                        f"Embeetle could not find the library on your<br>"
                        f"harddrive."
                    ),
                )
                finish()
                return
            success = _fp_.delete_dir(
                dir_abspath=library_abspath,
                printfunc=print,
                catch_err=True,
            )
            if not success:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="PROBLEM",
                    text=str(
                        f"Embeetle couldn{q} delete this folder:<br>"
                        f"{green}{q}{library_abspath}{q}{end}<br>"
                        f"Please check if you have write access here."
                    ),
                )
            finish()
            return

        def finish(*args) -> None:
            _libmanager_.LibManager().refresh(
                origins=["local_abspath"],
                callback=callback,
                callbackArg=None,
            )
            return

        start()
        return
