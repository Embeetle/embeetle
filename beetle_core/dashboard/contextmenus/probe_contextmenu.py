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
    import project.segments.probe_seg.probe as _probe_
    import dashboard.items.probe_items.probe_items as _probe_items_


class ProbeDeviceContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _probe_items_.ProbeDeviceItem,
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
        probe: _probe_.Probe = item.get_projSegment()

        #! FLASH BOOTLOADER
        probename = probe.get_name().lower().replace(" ", "-").replace("_", "-")
        if (
            (probename == "avr-isp-mkii")
            or (probename == "atmel-ice")
            or (probename == "arduino-as-isp")
        ):
            menu_bootloader = _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Flash bootloader",
                key="flash_bootloader",
                iconpath="icons/chip/flash_bootloader.png",
            )
            self.add_child(menu_bootloader)

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


class ProbeTransportProtocolContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _probe_items_.ProbeTransportProtocolItem,
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
