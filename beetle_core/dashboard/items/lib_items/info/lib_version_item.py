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
import tree_widget.widgets.item_richlbl as _cm_richbtn_
import dashboard.items.item as _da_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import dashboard.contextmenus.lib_contextmenu as _lib_contextmenu_
import helpdocs.help_texts as _ht_
import libmanager.libmanager as _libmanager_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class LibversionItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: LibversionItem) -> None:
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
                _da_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args) -> None:
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                version = libobj.get_version()
                if version is None:
                    version = "none"
                proj_relpath = "none"
                lbltext = (
                    "version:".ljust(15, "^")
                    + '<a href="foobar">'
                    + version
                    + "</a>"
                )
                lbltext = lbltext.replace("^", "&nbsp;")
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                self.closedIconpath = "icons/tool_cards/card_version.png"
                self.openIconpath = "icons/tool_cards/card_version.png"
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
        libobj: _libobj_.LibObj,
        rootdir: _da_.Root,
        parent: Union[_da_.Folder, _lib_item_shared_.LibItemShared],
    ) -> None:
        """Create a LibversionItem()-instance for the dashboard, to represent
        the version of a specific library.

        :param libobj: The Lib()-instance that represents the library.
        :param rootdir: The toplevel LIBRARIES dashboard item.
        :param parent: The library item bound to the Lib()-instance: what you
            get when you invoke 'libobj.get_dashboard_item()'
        """
        version = libobj.get_version()
        if version is None:
            version = "none"
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=version,
            state=LibversionItem.Status(item=self),
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
            itemRichLbl=_cm_richbtn_.ItemRichLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _lib_contextmenu_.LibversionContextMenu(
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
        libobj: _libobj_.LibObj = self.get_projSegment()

        def check_update(_key: str) -> None:
            _libmanager_.LibManager().check_for_updates(
                libobj=libobj,
                callback=lambda *a, **k: print("check_for_updates() finished!"),
                callbackArg=None,
            )
            return

        def _help(_key: str) -> None:
            version = libobj.get_version()
            if version is None:
                version = "none"
            name = libobj.get_name()
            if name is None:
                name = "none"
            libpath: Optional[str] = None
            if libobj.get_origin() == "local_abspath":
                libpath = libobj.get_local_abspath()
            elif libobj.get_origin() == "proj_relpath":
                libpath = libobj.get_proj_relpath()
            if libpath is None:
                libpath = "none"
            _ht_.lib_version_help(
                libname=name,
                libversion=version,
                libpath=libpath,
            )
            return

        funcs = {
            "check_update": check_update,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
