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
from components.singleton import Singleton
import qt
import threading
import contextmenu.contextmenu as _contextmenu_

if TYPE_CHECKING:
    pass
nop = lambda *a, **k: None


class ContextMenuLauncher(metaclass=Singleton):
    """LAUNCH A RIGHTCLICK CONTEXT MENU."""

    def __init__(self):
        """"""
        super().__init__()
        self.__contextmenu_mutex = threading.Lock()
        return

    def is_busy(self) -> bool:
        """Is a context menu currently running?"""
        return self.__contextmenu_mutex.locked()

    def launch_contextmenu(
        self,
        contextmenu: _contextmenu_.ContextMenuRoot,
        point: Union[qt.QPoint, qt.QPointF],
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Show the given context menu, then kill it. The callback is invoked
        when the context menu is dead.

        :param contextmenu: The context menu to launch. Must be a ContextMenuRoot() instance.
        :param point:       Point where to launch the context menu.

        The callback is called as soon as the popup is destroyed:

            > callback(callbackArg)
        """
        assert isinstance(contextmenu, _contextmenu_.ContextMenuRoot)
        if not self.__contextmenu_mutex.acquire(blocking=False):
            callback(callbackArg) if callback is not None else nop()
            return

        def finish(*args):
            self.__contextmenu_mutex.release()
            callback(callbackArg) if callback is not None else nop()
            return

        # The exec() method always needs a QPoint(), never a QPointF()!
        if isinstance(point, qt.QPointF):
            contextmenu.exec(point.toPoint())
        else:
            contextmenu.exec(point)
        contextmenu.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return
