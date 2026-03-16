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
import qt, data, functools, functions
import dashboard.items.item as _da_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import dashboard.contextmenus.lib_contextmenu as _lib_contextmenu_
import helpdocs.help_texts as _ht_
import project.segments.lib_seg.lib_seg as _lib_seg_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class LibSegRootItem(_da_.Root):
    """
    Toplevel item in dashboard: 'Libraries'.
    """

    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: LibSegRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/books.png"
            self.openIconpath = "icons/gen/books.png"
            self.lblTxt = "Libraries"
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
                _da_.Root.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args) -> None:
                lib_seg = cast(
                    _lib_seg_.LibSeg,
                    self.get_item().get_projSegment(),
                )
                if self.has_asterisk():
                    self.lblTxt = (
                        f"*Libraries ({lib_seg.get_nr_of_libraries()})"
                    )
                else:
                    self.lblTxt = (
                        f"Libraries ({lib_seg.get_nr_of_libraries()}) "
                    )
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

    def __init__(self, libseg: _lib_seg_.LibSeg) -> None:
        """"""
        super().__init__(
            projSegment=libseg,
            name="libseg",
            state=LibSegRootItem.Status(item=self),
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

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _lib_contextmenu_.ToplvlLibContextMenu(
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

        def download_library(_key: str) -> None:
            import wizards.lib_wizard.lib_wizard as _lib_wizard_

            if (
                (data.libman_wizard is not None)
                and (not data.libman_wizard.is_dead())
                and (not qt.sip.isdeleted(data.libman_wizard))
            ):
                data.libman_wizard.raise_()
            else:
                data.libman_wizard = _lib_wizard_.LibWizard(
                    parent=None,
                    callback=None,
                    callbackArg=None,
                )
                data.libman_wizard.show()
            return

        def add_library_from_zipfile(_key: str) -> None:
            import wizards.zipped_lib_wizard.zipped_lib_wizard as _zipped_lib_wizard_

            if data.libman_zipwizard is None:
                data.libman_zipwizard = _zipped_lib_wizard_.ZippedLibWizard()
            data.libman_zipwizard.show()
            return

        def refresh_library_list(_key: str) -> None:
            data.current_project.get_lib_seg().trigger_dashboard_refresh(
                callback=None,
                callbackArg=None,
            )
            return

        def _help(_key: str) -> None:
            _ht_.lib_help()
            return

        funcs = {
            "download_library": download_library,
            "add_library_from_zipfile": add_library_from_zipfile,
            "refresh": refresh_library_list,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
