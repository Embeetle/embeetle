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
import qt, functions, functools
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_lbl as _cm_lbl_
import dashboard.items.item as _dashboard_items_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class LibnameItem(_dashboard_items_.File):
    class Status(_dashboard_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: LibnameItem) -> None:
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
                _dashboard_items_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args) -> None:
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                name = libobj.get_name()
                if name is None:
                    name = "none"
                lbltext = "name:".ljust(15) + name
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                self.closedIconpath = "icons/tool_cards/card_name.png"
                self.openIconpath = "icons/tool_cards/card_name.png"
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
        libobj: _libobj_.LibObj,
        rootdir: _dashboard_items_.Root,
        parent: Union[
            _dashboard_items_.Folder, _lib_item_shared_.LibItemShared
        ],
    ) -> None:
        """Create a LibnameItem()-instance for the dashboard, to represent the
        name of a specific library.

        :param libobj: The Lib()-instance that represents the library.
        :param rootdir: The toplevel LIBRARIES dashboard item.
        :param parent: The library item bound to the Lib()-instance: what you
            get when you invoke 'libobj.get_dashboard_item()'
        """
        name = libobj.get_name()
        if name is None:
            name = "none"
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=name.lower(),
            state=LibnameItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
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
