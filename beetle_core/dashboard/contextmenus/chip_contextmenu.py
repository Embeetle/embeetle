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
import dashboard.contextmenus.specific_components.chip_contextmenu_parts as _mc_
import project.segments.chip_seg.chip as _chip_
import hardware_api.chip_unicum as _chip_unicum_

if TYPE_CHECKING:
    import qt
    import dashboard.items.chip_items.chip_items as _chip_items_


class ChipDeviceContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _chip_items_.ChipDeviceItem,
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
        chip: _chip_.Chip = item.get_projSegment()

        #! WEBPAGE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Webpage",
                key="link",
                iconpath="icons/gen/world.png",
            )
        )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return


class ChipMemoryContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _chip_items_.ChipMemoryItem,
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
        _v_memItem: _chip_items_.ChipMemoryItem = item

        #! SECTIONS
        menu_select = _contextmenu_.ContextMenuNode(
            contextmenu_root=self,
            parent=self,
            text="Sections",
            key="select",
            iconpath=None,
        )
        self.add_child(menu_select)
        memregion = _v_memItem.get_projSegment()
        assert isinstance(memregion, _chip_.MemRegion)

        menu_select.set_icon(
            iconpath=(
                "icons/memory/memory_green_many.png"
                if memregion.get_memtype() is _chip_unicum_.MEMTYPE.RAM
                else "icons/memory/memory_orange_many.png"
            )
        )
        longest_name = ""
        for memsection in memregion.get_memsection_list():
            if len(memsection.get_name()) > len(longest_name):
                longest_name = memsection.get_name()
        n = len(longest_name) + 1

        def get_displayed_text(_memsection: _chip_.MemSection) -> str:
            name = _memsection.get_name().ljust(n)
            usage = ""
            if _memsection.get_usage("kb") < 2:
                usage = f"{_memsection.get_usage()} bytes"
            else:
                usage = f'{_memsection.get_usage("kb")} Kb'
            return f"{name} [{usage}]"

        # * SECTIONS > MEMSECTIONS
        for memsection in memregion.get_memsection_list(form="sr"):
            menu_select.add_child(
                _mc_.MemsectionContextMenu(
                    contextmenu_root=self,
                    parent=menu_select,
                    text=get_displayed_text(memsection),
                    key=memsection.get_name(),
                    iconpath=None,
                )
            )
        for memsection in [
            sec
            for sec in memregion.get_memsection_list(form="s")
            if sec not in memregion.get_memsection_list(form="sr")
        ]:
            menu_select.add_child(
                _mc_.MemsectionContextMenu(
                    contextmenu_root=self,
                    parent=menu_select,
                    text=get_displayed_text(memsection),
                    key=memsection.get_name(),
                    iconpath=None,
                )
            )
        for memsection in [
            sec
            for sec in memregion.get_memsection_list(form="r")
            if sec not in memregion.get_memsection_list(form="sr")
        ]:
            menu_select.add_child(
                _mc_.MemsectionContextMenu(
                    contextmenu_root=self,
                    parent=menu_select,
                    text=get_displayed_text(memsection),
                    key=memsection.get_name(),
                    iconpath=None,
                )
            )
        if len(menu_select.get_childlist()) == 0:
            menu_select.add_child(
                _contextmenu_.ContextMenuLeaf(
                    contextmenu_root=self,
                    parent=menu_select,
                    text="None",
                    key="None",
                    iconpath=None,
                )
            )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return
