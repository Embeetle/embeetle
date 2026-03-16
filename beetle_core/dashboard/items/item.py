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
import weakref
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.items.item as _cm_
import project.segments.project_segment as _ps_

TYPE_CHECKING = False
if TYPE_CHECKING:
    pass

from various.kristofstuff import *


class Folder(_cm_.Folder):
    __slots__ = ("_projSegmentRef",)

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
        projSegment: Any,
        rootdir: Optional[Root],
        parent: Optional[Folder],
        name: str,
        state: Folder.Status,
    ) -> None:
        """

        :param projSegment: eg. _chip_.Chip()
                                _chip_.MemRegion()
                                _toolpath_seg_.ToolpathSeg()
                                _tool_obj_.ToolpathObj()
                                _treepath_seg_.TreepathSeg()
                                _treepath_obj_.TreepathObj()
                                _probe_.Probe()
                                _board_.Board()

        :param rootdir: Root() instance
        :param parent:  Folder() instance
        :param name:    str
        :param state:   Folder.Status() instance
        """
        # assert isinstance(rootdir, Folder) if rootdir is not None else True
        # assert isinstance(parent, Folder)  if parent is not None else True
        if parent is not None:
            depth = parent._depth + 1
        else:
            if rootdir is not None:
                assert rootdir is self
            depth = 0
        state = Folder.Status(self) if state is None else state
        super().__init__(
            rootdir,
            parent,
            name,
            depth,
            state,
        )
        self._projSegmentRef = (
            weakref.ref(projSegment) if projSegment is not None else None
        )
        return

    def get_state(self) -> Folder.Status:
        return self._state

    @ref
    def get_projSegment(self) -> Any:
        return self._projSegmentRef  # noqa

    def set_projSegment(self, projSegment: _ps_.ProjectSegment):
        self._projSegmentRef = None
        self._projSegmentRef = (
            weakref.ref(projSegment) if projSegment is not None else None
        )
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
        """Only used by general Dashboard Folder (no longer in use right now)"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return


class File(_cm_.File):
    __slots__ = ("_projSegmentRef",)

    class Status(_cm_.Item.Status):
        __slots__ = ()

        def __init__(self, item: File) -> None:
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
        projSegment: Union[_ps_.ProjectSegment, _ps_.ProjectSubsegment],
        rootdir: Root,
        parent: Folder,
        name: str,
        state: File.Status,
    ) -> None:
        """"""
        if projSegment is not None:
            assert isinstance(projSegment, _ps_.ProjectSegment) or isinstance(
                projSegment, _ps_.ProjectSubsegment
            )
        super().__init__(rootdir, parent, name, state)
        self._projSegmentRef = (
            weakref.ref(projSegment) if projSegment is not None else None
        )
        return

    def get_state(self) -> File.Status:
        return self._state

    @ref
    def get_projSegment(self) -> Any:
        return self._projSegmentRef  # noqa

    def set_projSegment(self, projSegment):
        self._projSegmentRef = None
        self._projSegmentRef = (
            weakref.ref(projSegment) if projSegment is not None else None
        )
        return


class Root(Folder, _cm_.Root):
    __slots__ = _cm_.Root.get_slots()

    def __init__(
        self,
        projSegment: Any,
        name: str,
        state: _cm_.Item.Status,
    ) -> None:
        """For all Dir()- and File()-items in the dirtree, the self._state
        variable gets initialized in the constructors Dir() and File().

        That approach is not possible for the dashboard.
        """
        _cm_.Root.__init__(
            self,
            abspath=name,
        )
        Folder.__init__(
            self,
            projSegment=projSegment,
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
