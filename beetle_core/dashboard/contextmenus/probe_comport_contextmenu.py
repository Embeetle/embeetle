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
import contextmenu.contextmenu as _contextmenu_

if TYPE_CHECKING:
    import qt
    import tree_widget.items.item as _item_


class ProbeComportContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )

        # #! SELECT
        # menu_select = _contextmenu_.ContextMenuNode(
        #     contextmenu_root = self,
        #     parent           = self,
        #     text             = 'Select',
        #     key              = 'select',
        #     iconpath         = 'icons/gen/select.png',
        # )
        # self.add_child(menu_select)
        # #* SELECT > COMPORTS
        # _v_comportItem = item
        # assert isinstance(_v_comportItem, _probe_comportitem_.ProbeComportItem)
        # probe = _v_comportItem.get_projSegment()
        # assert isinstance(probe, _probe_.Probe)
        # temp = functions.list_serial_ports()
        # data.serial_port_data = temp
        # if (temp is None) or \
        #         (len(temp) == 0):
        #     menu_select.add_child(
        #         _contextmenu_.ContextMenuLeaf(
        #             contextmenu_root = self,
        #             parent           = menu_select,
        #             text             = 'None',
        #             key              = 'none',
        #             iconpath         = 'icons/console/serial_monitor.png',
        #         )
        #     )
        # else:
        #     for key in temp.keys():
        #         menu_select.add_child(
        #             _contextmenu_.ContextMenuLeaf(
        #                 contextmenu_root = self,
        #                 parent           = menu_select,
        #                 text             = key,
        #                 key              = key,
        #                 iconpath         = 'icons/console/serial_monitor.png',
        #             )
        #         )

        #! SERIAL MONITOR
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Serial Monitor",
                key="serial_monitor",
                iconpath="icons/console/console.png",
            )
        )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Info",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return
