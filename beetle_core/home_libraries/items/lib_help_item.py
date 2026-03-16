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
import helpdocs.help_texts as _ht_
import home_libraries.items.item as _item_
import tree_widget.widgets.item_action_btn as _item_action_btn_

if TYPE_CHECKING:
    import qt


class LibHelpRootItem(_item_.Root):
    """Toplevel item in home tab LIBRARIES to add new libraries."""

    class Status(_item_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: LibHelpRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.action_iconpath = "icons/dialog/help.png"
            self.action_txt = "help"
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
            name="LibHelpRootItem",
            state=LibHelpRootItem.Status(item=self),
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
        super().leftclick_itemActionBtn(event)
        _ht_.libraries_tab_help()
        return

    def rightclick_itemActionBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemActionBtn(event)
        return
