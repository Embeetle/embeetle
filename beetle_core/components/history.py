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
import copy, data
import project.segments.project_segment as _ps_

if TYPE_CHECKING:
    from components.singleton import Unicum
from various.kristofstuff import *


class History(object):
    """Each ProjectSegment() (like Chip(), Probe(), TreepathSeg(), ...) has
    exactly.

    one History()-object. This object stores a couple of "snapshots": dicts with
    key - <Unicum> pairs. Example for Probe() segment:

    SNAPSHOT STORAGE
    ================
                            ┌→ keys
                  ┌         '                                                                                     ┐
    historylist = │ { 'probe_unicum'              : <Unicum>,      { 'probe_unicum'              : <Unicum>,          │
                  │   'transport_protocol_unicum' : <Unicum> }       'transport_protocol_unicum' : <Unicum> }         │
                  └                                                                                               ┘
                    └──────────────────v────────────────────┘   └────────────────────v───────────────────┘
                                 history snapshot                            history snapshot

    Attention!!
        - The historylist for a TreepathSeg()-object contains no <Unicum>
          objects, but strings (relpaths).
        - General objects would not be possible. Only primitives and enums,
          things that can be compared easily with '=='.


    SNAPSHOT PUSH/POP
    =================
    The keys from the history snapshots are the same in the
    getters, setters and asterisk_setters function-collections:

                     ┌→ keys
                     '
    getters = { 'probe_unicum'              : get_probe_unicum(),
                'transport_protocol_unicum' : get_transport_protocol_unicum()  }

    setters = { 'probe_unicum'              : set_probe_unicum(..),
                'transport_protocol_unicum' : set_transport_protocol_unicum(..)  }

    asterisk_setters = { 'probe_unicum'              : _v_deviceItem.get_state().set_asterisk(..),
                         'transport_protocol_unicum' : _v_transportProtocolItem.get_state().set_asterisk(..)  }

    Snapshots are pushed/popped to/from the historylist with the getters() and
    setters().
    """

    def __init__(
        self,
        projsegment: _ps_.ProjectSegment,
    ) -> None:
        """"""
        self.__dead = False
        assert isinstance(projsegment, _ps_.ProjectSegment)
        self.__projsegment = projsegment
        self.__historylist: List[
            Dict[str, Union[Unicum, Tuple[Any, ...], str]]
        ] = []
        self.__baseline: Dict[str, Union[Unicum, Tuple[Any, ...], str]] = {}
        self.__getters: Dict[str, Callable[..., Any]] = {}
        self.__setters: Dict[str, Callable[..., Any]] = {}
        self.__asterisk_setters: Dict[str, Callable[[bool], Any]] = {}
        self.__refreshfunc = nop
        return

    """
    1. INIT
    """

    def register_refreshfunc(self, refreshfunc: Callable) -> None:
        self.__refreshfunc = refreshfunc
        return

    def register_getters(self, **kwargs) -> None:
        for key, func in kwargs.items():
            self.__getters[key] = func
        if len(self.__setters) > 0:
            assert len(self.__getters) == len(self.__setters)
        return

    def register_setters(self, **kwargs) -> None:
        for key, func in kwargs.items():
            self.__setters[key] = func
        if len(self.__getters) > 0:
            assert len(self.__getters) == len(self.__setters)
        return

    def register_asterisk_setters(self, **kwargs) -> None:
        for key, func in kwargs.items():
            self.__asterisk_setters[key] = func
        assert (
            len(self.__getters)
            == len(self.__setters)
            == len(self.__asterisk_setters)
        )
        return

    """
    2. PUSH & POP
    """

    def push(self) -> None:
        """Push the current set of Unicums (or relpaths for the
        TreepathSeg()-object) to history. In other words, take a snapshot and
        add that to the historylist.

            Note 1: The snapshot is a dict, like
                        snap = {
                            'probe_unicum'              : <Unicum>,
                            'transport_protocol_unicum' : <Unicum>,
                        }

            Note 2: The getters are used to get them.

            Note 3: The constructed element/dict is copied
                    through 'copy.deepcopy()'.

        The ProjectSegment()-instance (eg. Probe(), Chip(), ...) is then pushed to the
        self.__projhistory[] list from the Project()-instance. This way, the Project()-instance has
        a list of all segments that recently got changed.
        """
        # print(f'\n{self.__projsegment.__class__.__name__}().get_history().push()')

        # construct element to push
        snap: Dict[str, Union[Unicum, Tuple[Any, ...], str]] = {}
        for key, getfunc in self.__getters.items():
            snap[key] = copy.deepcopy(getfunc())
            continue

        # CASE 1: First push
        if len(self.__historylist) == 0:
            self.__baseline = copy.deepcopy(snap)
            self.__historylist.append(snap)
            data.current_project.push_projhistory(self.__projsegment)
            return
        change = False
        for key, value in snap.items():
            if snap[key] != self.__historylist[-1][key]:
                change = True
        if not change:
            # CASE 2: Nothing to push
            return

        # CASE 3: General push
        self.__historylist.append(snap)
        data.current_project.push_projhistory(self.__projsegment)
        return

    def pop(self) -> None:
        """
        Pop the latest snapshot from history and apply it.
            Note 1: The snapshot is a dict, like
                        snap = { 'probe_unicum'              : <Unicum>,
                                 'transport_protocol_unicum' : <Unicum> }

            Note 2: The setters are used to install the snapshot
                    in the ProjectSegment()-instance.

            Note 3: To cancel the 'copy.deepcopy()' effect,
                    the Unicum's function 'get_unicum_from_name()' is used.
                    No copied Unicum's will hang around in Embeetle!

        """
        if len(self.__historylist) == 0:
            # CASE 1: Nothing to pop
            return
        # CASE 2: General pop
        snap: Dict[str, Union[Unicum, Tuple[Any, ...], str]] = copy.deepcopy(
            self.__historylist[-1]
        )
        for key, setfunc in self.__setters.items():
            if isinstance(snap[key], str):
                setfunc(snap[key])
                continue
            if isinstance(snap[key], tuple):
                setfunc(snap[key])
                continue
            # snap[key] is None
            if snap[key] is None:
                continue
            # snap[key] is an <Unicum>
            _orig_unicum: Unicum = snap[key].__class__.get_unicum_from_name(  # type: ignore
                snap[key].get_name()  # type: ignore
            )
            setfunc(_orig_unicum)
            continue
        del self.__historylist[-1]
        self.compare_to_baseline()
        return

    """
    3. BASELINE
    """

    def compare_to_baseline(
        self,
        refresh=True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Create a temporary snapshot (with the getters) and compare it to the
        baseline snapshot.

        Based on the comparison, add or remove the corresponding asterisk.
        """
        snap: Dict[str, Union[Unicum, Tuple[Any, ...], str]] = (
            {}
        )  # construct snapshot to compare to
        for key, getfunc in self.__getters.items():
            snap[key] = copy.deepcopy(getfunc())
        for key, value in snap.items():
            if key not in self.__baseline:
                self.__baseline[key] = snap[key]
            if snap[key] != self.__baseline[key]:
                self.__asterisk_setters[key](True)
            else:
                self.__asterisk_setters[key](False)
        if refresh:
            self.__refreshfunc(
                callback=callback,
                callbackArg=callbackArg,
            )
            return
        if callback is not None:
            callback(callbackArg)
        return

    def reset_baseline(self, refresh: bool = True) -> None:
        """Create a snapshot (with the getters) and store it as the baseline."""
        snap: Dict[str, Union[Unicum, Tuple[Any, ...], str]] = (
            {}
        )  # construct element to serve as baseline
        for key, getfunc in self.__getters.items():
            snap[key] = copy.deepcopy(getfunc())
        self.__baseline = copy.deepcopy(snap)
        self.compare_to_baseline(
            refresh=refresh,
        )
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """Kill this History()-instance."""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError("Trying to kill History() twice!")
            self.__dead = True
        self.__projsegment = None
        self.__historylist = None
        self.__baseline = None
        self.__getters = None
        self.__setters = None
        self.__asterisk_setters = None
        self.__refreshfunc = None
        return
