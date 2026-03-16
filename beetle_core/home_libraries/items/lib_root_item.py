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
import functools
import qt, data, functions
import helpdocs.help_texts as _ht_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import home_libraries.items.item as _item_
import dashboard.contextmenus.lib_contextmenu as _lib_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import home_libraries.items.lib_refresh_item as _lib_refresh_item_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class LibCategoryRootItem(_item_.Root):
    """Toplevel item in home tab LIBRARIES.

    It represents a Library category.
    """

    class Status(_item_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: LibCategoryRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/books.png"
            self.openIconpath = "icons/gen/books.png"
            self.lblTxt = "lib?"
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
                _item_.Root.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args) -> None:
                item: LibCategoryRootItem = self.get_item()
                childlist = item.get_childlist()
                if self.has_asterisk():
                    if childlist is None:
                        self.lblTxt = f"*{item.get_name()} (0)"
                    else:
                        self.lblTxt = f"*{item.get_name()} ({len(childlist)-1})"
                else:
                    if childlist is None:
                        self.lblTxt = f"{item.get_name()} (0) "
                    else:
                        self.lblTxt = f"{item.get_name()} ({len(childlist)-1}) "
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

    def __init__(self, libcat: str) -> None:
        """"""
        super().__init__(
            name=libcat,
            state=LibCategoryRootItem.Status(item=self),
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
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
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
                data.libman_wizard.show(category_prefill=self.get_name())
            else:
                data.libman_wizard = _lib_wizard_.LibWizard(
                    parent=None,
                    callback=None,
                    callbackArg=None,
                )
                data.libman_wizard.show(category_prefill=self.get_name())
            return

        def add_library_from_zipfile(_key: str) -> None:
            import wizards.zipped_lib_wizard.zipped_lib_wizard as _zipped_lib_wizard_

            if data.libman_zipwizard is None:
                data.libman_zipwizard = _zipped_lib_wizard_.ZippedLibWizard()
            data.libman_zipwizard.show(
                category_prefill=self.get_name(),
            )
            return

        def refresh_library_list(_key: str) -> None:
            _lib_refresh_item_.do_refresh()
            return

        def _help(_key: str) -> None:
            _ht_.libcat_help(self.get_name())
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
