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
import threading
from typing import *
import os
import qt, data, functions
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import helpdocs.help_texts as _ht_
import sa_tab.items.item as _sa_tab_items_
import tree_widget.widgets.item_action_btn as _item_action_btn_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import components.sourceanalyzerinterface as _sai_

if TYPE_CHECKING:
    import project.segments.path_seg.treepath_seg as _treepath_seg_


class ClearCacheRootItem(_sa_tab_items_.Root):
    class Status(_sa_tab_items_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ClearCacheRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.action_iconpath = "icons/gen/clean.png"
            self.action_txt = "clear cache"
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
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__(
            name="clear_cache",
            state=ClearCacheRootItem.Status(item=self),
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
            itemActionBtn=_item_action_btn_.ItemActionBtn(owner=self),
        )
        return

    def leftclick_itemActionBtn(self, event: Optional[qt.QEvent]) -> None:
        """"""
        if event is not None:
            super().leftclick_itemActionBtn(event)

        # * Check if busy

        def busy(*args) -> None:
            _ht_.beetle_busy()
            return

        project_status = _sai_.SourceAnalysisCommunicator().get_project_status()
        linker_status = _sai_.SourceAnalysisCommunicator().get_linker_status()
        launch_issues = (
            _sai_.SourceAnalysisCommunicator().get_sa_launch_issues()
        )
        internal_err = _sai_.SourceAnalysisCommunicator().has_internal_error()
        feeder_busy = False
        digester_busy = False

        # $ ERROR
        if (project_status == 2) or (launch_issues is not None) or internal_err:
            # In case of an error, it should be possible to clear the cache, un-
            # less the feeder or digester is busy.
            if feeder_busy or digester_busy:
                busy()
                return

        # $ BUSY
        elif (
            (project_status == 1)
            or (linker_status == 0)
            or (linker_status == 1)
            or feeder_busy
            or digester_busy
        ):
            # Something is busy, so wait.
            busy()
            return

        # $ DONE
        else:
            # No issue, can continue.
            pass

        # * Lock the user mutex.
        assert threading.current_thread() is threading.main_thread()
        if not data.user_lock.acquire(blocking=False):
            _ht_.beetle_busy()
            return

        # * Extract cache location
        projObj = data.current_project
        treepath_seg: _treepath_seg_.TreepathSeg = projObj.get_treepath_seg()
        cache_abspath = f"{projObj.get_proj_rootpath()}/.beetle/.cache"

        # * Delete from hdd
        if (cache_abspath is not None) and os.path.isdir(cache_abspath):
            _fp_.delete_dir(
                dir_abspath=cache_abspath,
                printfunc=print,
                catch_err=True,
                allow_rootpath_deletion=True,
            )

        # * Finish
        assert threading.current_thread() is threading.main_thread()
        _sai_.SourceAnalysisCommunicator().reload_all_files()

        data.user_lock.release()
        return

    def rightclick_itemActionBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemActionBtn(event)
        self.show_contextmenu_itemActionBtn(event)
        return

    def show_contextmenu_itemActionBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemActionBtn = self.get_widget(key="itemActionBtn")
        contextmenu = _toplvl_contextmenu_.ToplvlContextMenu(
            widg=itemActionBtn,
            item=self,
            toplvl_key="itemActionBtn",
            clickfunc=self.contextmenuclick_itemActionBtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemActionBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemActionBtn(key)

        def _help(_key):
            _ht_.sa_clear_cache()
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
