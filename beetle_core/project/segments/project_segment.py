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
import components.history as _hi_

# ^                                            SEGMENT                                             ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class Segment(object):
    __slots__ = (
        "dead",
        "__weakref__",
    )

    def __init__(self) -> None:
        """"""
        super().__init__()
        self.dead = False
        return

    def trigger_dashboard_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if callback is not None:
            callback(callbackArg)
        return

    def update_states(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        if callback is not None:
            callback(callbackArg)
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill Segment() twice!")
            self.dead = True
        if callback is not None:
            callback(callbackArg)
        return


# ^                                        PROJECT_SEGMENT                                         ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ProjectSegment(Segment):

    __slots__ = (
        "__history",
        "__is_fake",
    )

    def __init__(self, is_fake: bool) -> None:
        """"""
        super().__init__()
        self.__history = _hi_.History(projsegment=self)
        self.__is_fake = is_fake
        return

    def is_fake(self) -> bool:
        """"""
        return self.__is_fake

    def set_fake(self, fake: bool) -> None:
        """"""
        self.__is_fake = fake

    def get_history(self) -> _hi_.History:
        """"""
        return self.__history

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if callback is not None:
            callback(callbackArg)
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        return ""

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill ProjectSegment() twice!")
            self.dead = True
        self.__history.self_destruct()
        # Supercall not needed. Nothing really happens there.
        # super().self_destruct(...)
        if callback is not None:
            callback(callbackArg)
        return


# ^                                       PROJECT_SUBSEGMENT                                       ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ProjectSubsegment(Segment):

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__()
        pass

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill ProjectSubsegment() twice!")
            self.dead = True
        # Supercall not needed. Nothing really happens there.
        # super().self_destruct(...)
        if callback is not None:
            callback(callbackArg)
        return
