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
import functools
import threading
from typing import *
import qt
import data, purefunctions
import dashboard.items.lib_items.lib_root_item as _da_lib_root_item_
import project.segments.project_segment as _ps_
import libmanager.libmanager as _libmanager_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class LibSeg(_ps_.ProjectSegment):
    """This LibSeg()-instance holds a LibObj() for each library in the current
    project.

    In turn, each LibObj()-instance has a get_dashboard_item() method to return
    its LibItem()-instance, which can be shown on the dashboard.
    """

    @classmethod
    def create_default_LibSeg(cls) -> LibSeg:
        """Create a default LibSeg()-object."""
        return cls(False)

    @classmethod
    def create_empty_LibSeg(cls) -> LibSeg:
        """Create a default LibSeg()-object."""
        return cls.create_default_LibSeg()

    @classmethod
    def load(
        cls,
        configcode: Optional[Dict[str, str]],
        rootpath: str,
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Note: The project_report is not returned, but simply modified here.
        """
        lib_seg = cls(False)
        callback(lib_seg, callbackArg)
        return

    __slots__ = (
        "__update_states_already_ran",
        "_v_rootItem",
        "__trigger_dashboard_refresh_mutex",
    )

    def __init__(self, is_fake: bool) -> None:
        """A LibSeg()-object holds the libraries."""
        super().__init__(is_fake)
        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        self.__update_states_already_ran = False
        self._v_rootItem: Optional[_da_lib_root_item_.LibSegRootItem] = None
        return

    def clone(self, is_fake: bool = True) -> LibSeg:
        """Clone this object."""
        cloned_lib_seg = LibSeg(is_fake)
        return cloned_lib_seg

    def is_dashboard_refresh_running(self) -> bool:
        return self.__trigger_dashboard_refresh_mutex.locked()

    def get_nr_of_libraries(self) -> Optional[int]:
        """Get how many libraries exist in the current project."""
        return _libmanager_.LibManager().get_nr_of_proj_libs()

    def list_library_names(self) -> Optional[List[str]]:
        """List the names of all libraries in the current project."""
        return _libmanager_.LibManager().list_proj_libs_names()

    def get_libobj_by_name(self, libname: str) -> Optional[_libobj_.LibObj]:
        """Get the LibObj()-instance by giving its name."""
        return _libmanager_.LibManager().get_libobj_from_merged_libs(
            libname=libname,
            libversion=None,
            origins=[
                "proj_relpath",
            ],
        )

    """
    1. Dashboard
    """

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show the LibSegRootItem() on the dashboard, and all the LibItem()
        instances (one per library).

        Unlike the other dashboard-segments, the 'update_states()' method should
        run *before* 'show_on_dashboard()'. A safety measure is taken in this
        method.
        """

        def start(*args):
            if not self.__update_states_already_ran:
                self.update_states(
                    project_report=None,
                    callback=start_adding,
                    callbackArg=None,
                )
                return
            start_adding()
            return

        def start_adding(*args):
            assert self.__update_states_already_ran
            self._v_rootItem = _da_lib_root_item_.LibSegRootItem(
                libseg=self,
            )
            libobjs_to_be_added_list = (
                _libmanager_.LibManager().list_proj_libobjs()
            )
            add_next(iter(libobjs_to_be_added_list))
            return

        def add_next(libobj_iter):
            try:
                libobj: _libobj_.LibObj = next(libobj_iter)
            except StopIteration:
                finish()
                return
            self._v_rootItem.add_child(
                child=libobj.get_dashboard_item(self),
                alpha_order=False,
                show=False,
                callback=add_next,
                callbackArg=libobj_iter,
            )
            return

        def finish(*args):
            data.dashboard.add_root(self._v_rootItem)
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return

    def update_states(
        self,  # type: ignore[override]
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """
        This LibSeg() shows all the project LibObj()s - stored in the LibManager() database - on the
        dashboard.

        So this 'update_states()' function should update their 'states', without necessarily pushing
        anything to the GUI. However, some GUI stuff is already handled by the LibManager()'s
        refresh() method for practical reasons. Other GUI stuff is handled in 'trigger_dashboard_
        refresh()' - see next method.
        """

        def finish(*args):
            self.__update_states_already_ran = True
            if callback is not None:
                qt.QTimer.singleShot(
                    20,
                    functools.partial(
                        callback,
                        callbackArg,
                    ),
                )
            return

        if not _libmanager_.LibManager().is_initialized(["proj_relpath"]):
            _libmanager_.LibManager().initialize(
                libtable=None,
                progbar=None,
                origins=["proj_relpath"],
                callback=finish,
                callbackArg=None,
            )
            return
        _libmanager_.LibManager().refresh(
            origins=["proj_relpath"],
            callback=finish,
            callbackArg=None,
        )
        return

    def trigger_dashboard_refresh(
        self,  # type: ignore[override]
        also_refresh_database: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[object] = None,
    ) -> None:
        """
        After 'update_states()' has run, lots of things are actually already pushed to the GUI - see
        explanation at 'refresh_proj_libs()' in 'libmanager.py'.

        The only things still to do:
            - Add invisible LibObj()s to the dashboard.
            - Refresh all dashboard items in the LIBRARIES section.
        """
        if not self.__trigger_dashboard_refresh_mutex.acquire(blocking=False):
            # Unlike the other Project Segments, this mutex won't attempt a re-entry after 100ms.
            purefunctions.printc(
                "\nWARNING: Attempt to re-enter the trigger_dashboard_refresh() "
                "function has been blocked.\n",
                color="warning",
            )
            if callback is not None:
                callback(callbackArg)
            return

        def start_adding(*args) -> None:
            libobjs_to_be_added_list = [
                libobj
                for libobj in _libmanager_.LibManager().list_proj_libobjs()
                if libobj.get_dashboard_item(self)
                not in self._v_rootItem.get_childlist()
            ]
            add_next(iter(libobjs_to_be_added_list))
            return

        def add_next(libobjs_to_be_added: Iterator[_libobj_.LibObj]) -> None:
            try:
                libobj = next(libobjs_to_be_added)
            except StopIteration:
                refresh_dashboard()
                return
            self._v_rootItem.add_child(
                child=libobj.get_dashboard_item(self),
                alpha_order=True,
                show=True,
                callback=add_next,
                callbackArg=libobjs_to_be_added,
            )
            return

        def refresh_dashboard(*args) -> None:
            if (self._v_rootItem is None) or (
                self._v_rootItem._v_layout is None
            ):
                finish()
                return
            self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                False,
                False,
                finish,
                None,
            )
            return

        def finish(*args) -> None:
            data.dashboard.check_unsaved_changes()
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        if self._v_rootItem is None:
            finish()
            return
        if also_refresh_database:
            self.update_states(
                callback=start_adding,
                callbackArg=None,
            )
            return
        start_adding()
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        super().printout(nr)
        return ""

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this LibSeg()-instance and *all* its representations in the
        Dashboard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill LibSeg() twice!")
            self.dead = True
        assert not self.is_fake()

        def start(*args) -> None:
            if self._v_rootItem:
                self._v_rootItem.self_destruct(
                    killParentLink=False,
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            self._v_rootItem = None
            if callback is not None:
                callback(callbackArg)
            return

        super().self_destruct(
            callback=start,
            callbackArg=None,
            death_already_checked=True,
        )
        return
