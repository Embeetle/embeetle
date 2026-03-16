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
import traceback, os, functools
import qt, data, purefunctions, functions, gui
import helpdocs.help_texts as _ht_
import sa_tab.items.item as _sa_tab_items_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import tree_widget.widgets.item_img as _cm_item_img_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import components.sourceanalyzerinterface as _sai_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class CPULoadRootItem(_sa_tab_items_.Root):
    class Status(_sa_tab_items_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: CPULoadRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.imgpath = "icons/dialog/help.png"
            self.closedIconpath = "icons/gen/cpu_load.png"
            self.openIconpath = "icons/gen/cpu_load.png"
            self.lblTxt = " concurrency  "
            return

        def __get_dropdown_elements(
            self,
            callback: Callable,
        ) -> None:
            """> callback(dropdown_elements, dropdown_selection)"""
            # & Figure out current selection
            dropdown_selection: Optional[str] = str(
                _sai_.SourceAnalysisCommunicator().get_number_of_workers()
            )
            if dropdown_selection is None:
                dropdown_selection = "0"

            # & Fill dropdown elements
            text_color = "default"
            dropdown_elements: List[Dict] = []
            cpu_count = os.cpu_count()
            if (cpu_count is None) or (not isinstance(cpu_count, int)):
                cpu_count = 30
            if cpu_count == 0:
                cpu_count = 1
            for n in range(cpu_count + 1):
                iconpath = "icons/gen/cpu_load.png"
                dropdown_elements.append(
                    {
                        "name": f"{n}",
                        "widgets": [
                            {
                                "type": "image",
                                "icon-path": iconpath,
                            },
                            {
                                "type": "text",
                                "text": f"{n} threads" if n > 0 else "disable",
                                "color": text_color,
                            },
                        ],
                    }
                )
                continue

            # & Finish
            callback(dropdown_elements, dropdown_selection)
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

            def finish(dropdown_elements, dropdown_selection):
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = " *concurrency "
            else:
                self.lblTxt = " concurrency  "
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                callback=finish,
            )
            return

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__(
            name="nr_of_threads",
            state=CPULoadRootItem.Status(item=self),
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
            itemImg=_cm_item_img_.ItemImg(owner=self),
        )
        dropdown: _cm_dropdown_.ItemDropdown = self.get_widget("itemDropdown")
        dropdown.selection_changed_from_to.connect(
            self.selection_changed_from_to,
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemImg(self, event: Optional[qt.QEvent]) -> None:
        """"""
        _ht_.sa_cpu_cores()
        return

    def selection_changed_from_to(
        self,
        from_nr_of_cores: str,
        to_nr_of_cores: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_nr_of_cores: Original nr of cores selected.
        :param to_nr_of_cores: New nr of cores selected.
        """

        def finish(_selected_cores: int) -> None:
            # Apply the selected amount of cores. If something goes wrong, jump
            # to the 'abort()' function.
            try:
                _sai_.SourceAnalysisCommunicator().set_number_of_workers(
                    _selected_cores
                )
            except:
                abort(True)
                return
            self.refresh_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=None,
                callbackArg=None,
            )
            return

        def abort(has_err: bool) -> None:
            # Do not apply anything, instead refresh this Item() such that the
            # previous selection is shown again. Print an error if requested.
            if has_err:
                purefunctions.printc(
                    f"\nERROR: Cannot set core number from {from_nr_of_cores} to "
                    f"{to_nr_of_cores}!\n",
                    color="error",
                )
                traceback.print_exc()
            self.refresh_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=None,
                callbackArg=None,
            )
            return

        # $ Extract selected nr of cores
        try:
            selected_cores = int(to_nr_of_cores.strip())
        except:
            abort(True)
            return
        assert isinstance(selected_cores, int)

        # $ No cores selected
        if selected_cores == 0:
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                icon_path="icons/dialog/warning.png",
                title_text="Attention!",
                text=str(
                    f"You selected zero cores. Are you intending to shut down the<br>"
                    f"Source Analyzer?<br>"
                ),
            )
            if reply == qt.QMessageBox.StandardButton.Yes:
                # Apply selection
                finish(selected_cores)
                return
            # Ignore selection
            abort(False)
            return

        # $ Cores selected, but no idea how many available
        cpu_count: Optional[int] = os.cpu_count()
        if (cpu_count is None) or (not isinstance(cpu_count, int)):
            # Just accept selection
            finish(selected_cores)
            return
        assert isinstance(cpu_count, int)

        # $ Too many cores selected
        if selected_cores > cpu_count:
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                icon_path="icons/dialog/warning.png",
                title_text="Attention!",
                text=str(
                    f"You only have {cpu_count} cores in your computer. Reserving more threads<br>"
                    f"for the Source Analyzer won{q}t result in any performance benefit.<br>"
                    f"Are you sure you want to continue?<br>"
                ),
            )
            if reply == qt.QMessageBox.StandardButton.Yes:
                # Apply selection
                finish(selected_cores)
                return
            # Ignore selection
            abort(False)
            return

        # * Selection seems okay
        finish(selected_cores)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _toplvl_contextmenu_.ToplvlContextMenu(
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

        def _help(_key):
            self.leftclick_itemImg(None)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
