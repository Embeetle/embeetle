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
import threading
import tree_widget.items.item as _cm_

if TYPE_CHECKING:
    import qt

from various.kristofstuff import *


class Folder(_cm_.Folder):
    __slots__ = ()

    class Status(_cm_.Item.Status):
        __slots__ = ()

        def __init__(self, item: Folder) -> None:
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
        rootdir: Folder,
        parent: Optional[Folder],
        name: str,
        state: Folder.Status,
    ) -> None:
        assert isinstance(rootdir, Folder) if rootdir is not None else True
        assert isinstance(parent, Folder) if parent is not None else True
        assert isinstance(state, Folder.Status) if state is not None else True
        if parent is not None:
            depth = parent._depth + 1
        else:
            assert rootdir is self
            assert parent is None
            depth = 0
        super().__init__(rootdir, parent, name, depth, state)
        return

    def get_state(self) -> Folder.Status:
        return self._state

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        if len(self.get_childlist()) > 0:
            self.toggle_open()
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

        That approach is not possible for the dashboard and console.
        """
        _cm_.Root.__init__(self, abspath=name)
        Folder.__init__(
            self,
            rootdir=self,
            parent=None,
            name=name,
            state=state,
        )

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

    def get_chassis_body(self):
        raise RuntimeError()

    def get_chassis(self):
        raise RuntimeError()

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
