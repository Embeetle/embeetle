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
import qt, data, gui, functions
import bpathlib.file_power as _fp_
import dashboard.items.item as _da_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import libmanager.libobj as _libobj_
import dashboard.contextmenus.lib_contextmenu as _lib_contextmenu_
import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_

if TYPE_CHECKING:
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class LibItem(_da_.Folder, _lib_item_shared_.LibItemShared):
    """Item() in dashboard, representing a LibObj()-instance (a specific
    library)."""

    __slots__ = ()

    def __init__(
        self,
        libobj: _libobj_.LibObj,
        rootdir: _da_.Root,
        parent: _da_.Folder,
    ) -> None:
        """"""
        _lib_item_shared_.LibItemShared.__init__(
            self,
            superclass=_da_.Folder,
        )
        _da_.Folder.__init__(
            self,
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=libobj.get_name(),
            state=_lib_item_shared_.Status(
                item=self,
                name=libobj.get_name(),
            ),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def get_libobj(self) -> _libobj_.LibObj:
        return cast(
            _libobj_.LibObj,
            self.get_projSegment(),
        )

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

    # def leftclick_itemImg(self, event:QEvent) -> None:
    #     _lib_item_shared_.LibItemShared.leftclick_itemImg(self, event)
    # def rightclick_itemImg(self, event:QEvent) -> None:
    #     _lib_item_shared_.LibItemShared.rightclick_itemImg(self, event)
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
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Delete the library from the harddrive, as well as the corresponding
        LibObj() and this LibItem()."""
        libobj = cast(
            _libobj_.LibObj,
            self.get_projSegment(),
        )
        library_abspath = libobj.get_proj_abspath()
        del libobj
        success = _fp_.delete_dir(library_abspath)
        if not success:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="INTERNAL ERROR",
                text=f"""
                    Embeetle was unable to delete the folder:<br>
                    {q}{library_abspath}{q}<br>
                """,
            )
            # Refresh still needed, don't quit yet!

        # Refresh all LibSeg()-instances from the Dashboard. This should also trigger the Lib-
        # Manager()'s database to be refreshed. The LibObj()-instance extracted above should be
        # destroyed during that action, as well as this LibItem() tied to it.
        data.current_project.refresh_all_lib_segs(
            skip_if_busy=False,
            callback=callback,
            callbackArg=callbackArg,
        )
        return
