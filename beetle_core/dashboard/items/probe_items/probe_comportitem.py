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
import qt, data, functions, traceback, functools
import dashboard.items.item as _da_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import dashboard.contextmenus.probe_comport_contextmenu as _da_probe_comportpopup_
import helpdocs.help_texts as _ht_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

if TYPE_CHECKING:
    import project.segments.probe_seg.probe as _probe_


class ProbeComportItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ProbeComportItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/console/serial_monitor.png"
            self.openIconpath = "icons/console/serial_monitor.png"
            self.lblTxt = "Flash Port "
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
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            probe: _probe_.Probe = item.get_projSegment()
            comport_name = probe.get_comport_name()
            self.set_asterisk(probe.get_state("COMPORT", "asterisk"))
            self.lblTxt = (
                "*Flash Port" if self.has_asterisk() else "Flash Port "
            )
            self.lblTxt = self.lblTxt.ljust(20)
            if comport_name is None:
                self.set_error(True)
            else:
                self.set_error(False)
            self.closedIconpath = "icons/console/serial_monitor.png"
            self.openIconpath = "icons/console/serial_monitor.png"
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            # Enter a codeword to avoid the 'sync_widg()' method in 'item_dropdown.py' syncing this
            # dropdown widget there. We want the Probe()-segment to do all the syncing, on its own
            # initiative!
            self.dropdownSelection = "@externally_refreshed"

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        probe,
        rootdir,
        parent,
    ) -> None:
        """
        :param probe:
        :param rootdir:
        :param parent:
        """
        super().__init__(
            projSegment=probe,
            rootdir=rootdir,
            parent=parent,
            name="comport",
            state=ProbeComportItem.Status(item=self),
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
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemDropdown=_cm_dropdown_.ItemDropdown(owner=self),
        )
        dropdown: _cm_dropdown_.ItemDropdown = self.get_widget("itemDropdown")
        dropdown.selection_changed_from_to.connect(
            self.selection_changed_from_to,
        )
        # The init_guiVars() method runs when the parent opens. Only now the
        # dropdown widget exists. Make sure it syncs properly with the Probe()-
        # segment.
        probe: _probe_.Probe = self.get_projSegment()
        probe.refresh_comport_dropdown("dashboard")
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        super().leftclick_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def selection_changed_from_to(
        self,
        from_comport: str,
        to_comport: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_comport: Original name of comport
        :param to_comport: New name of comport
        """
        probe: _probe_.Probe = self.get_projSegment()
        probe.dropdown_selection_changed_from_to(
            dropdown_src="dashboard",
            from_comport=from_comport,
            to_comport=to_comport,
        )
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_probe_comportpopup_.ProbeComportContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def serial_monitor(_key: str) -> None:
            try:
                console = data.main_form.create_console("Serial Monitor", True)
            except Exception as e:
                data.main_form.display.display_error(traceback.format_exc())
                traceback.print_exc()
            return

        def _help(_key: str) -> None:
            _ht_.probe_comport_help()
            return

        funcs = {
            "serial_monitor": serial_monitor,
            "help": _help,
        }

        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
