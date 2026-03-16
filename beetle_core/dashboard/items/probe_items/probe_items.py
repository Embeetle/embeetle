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
import traceback, functools
import qt, functions, data
import hardware_api.hardware_api as _hardware_api_
import dashboard.items.item as _da_
import project.segments.probe_seg.probe as _probe_
import hardware_api.probe_unicum as _probe_unicum_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import tree_widget.widgets.item_lbl as _cm_lbl_
import dashboard.contextmenus.toplvl_contextmenu as _da_toplvl_popup_
import dashboard.contextmenus.probe_contextmenu as _da_probe_popup_
import helpdocs.help_texts as _ht_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

# ^                                        PROBE ROOT ITEM                                         ^#
# % ============================================================================================== %#
# % ProbeRootItem()                                                                                %#
# %                                                                                                %#


class ProbeRootItem(_da_.Root):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ProbeRootItem) -> None:
            super().__init__(item=item)
            self.lblTxt = "Probe "
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
            item: ProbeRootItem = self.get_item()

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
            self.lblTxt = "*Probe" if self.has_asterisk() else "Probe "
            probe: _probe_.Probe = self.get_item().get_projSegment()
            self.closedIconpath: str = probe.get_probe_dict()["icon"]
            self.openIconpath: str = probe.get_probe_dict()["icon"]
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        probe: _probe_.Probe,
    ) -> None:
        """"""
        super().__init__(
            projSegment=probe,
            name="probe",
            state=ProbeRootItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent):
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_toplvl_popup_.ToplvlContextMenu(
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
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            _ht_.probe_help(self.get_projSegment())
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                       PROBE DEVICE ITEM                                        ^#
# % ============================================================================================== %#
# % ProbeDeviceItem()                                                                              %#
# %                                                                                                %#


class ProbeDeviceItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ProbeDeviceItem) -> None:
            """"""
            super().__init__(item=item)
            self.lblTxt = "Probe "
            self.lblTxt = self.lblTxt.ljust(20)
            return

        def __get_dropdown_elements(
            self,
            probe: _probe_.Probe,
            callback: Callable,
        ) -> None:
            """> callback(dropdown_elements, dropdown_selection)"""
            # * Figure out current selection
            dropdown_selection: Optional[str] = None
            cur_mf = probe.get_probe_dict()["manufacturer"]
            if cur_mf is None:
                dropdown_selection = "NONE"
            else:
                dropdown_selection = f"{cur_mf}/{probe.get_name()}"

            # * Fill dropdown elements
            text_color = "default"
            dropdown_elements: List[Dict] = []
            for mf in _hardware_api_.HardwareDB().list_manufacturers(
                for_probes=True
            ):
                if "other" in mf:
                    continue
                if dropdown_selection is None:
                    dropdown_selection = mf
                try:
                    iconpath = (
                        _hardware_api_.HardwareDB().get_manufacturer_dict(mf)[
                            "icon"
                        ]
                    )
                except:
                    # Manufacturer not known (or deactivated)
                    continue
                dropdown_elements.append(
                    {
                        "name": mf,
                        "widgets": [
                            {
                                "type": "image",
                                "icon-path": iconpath,
                            },
                            {
                                "type": "text",
                                "text": mf,
                                "color": text_color,
                            },
                        ],
                    }
                )
                subitems = []
                for p in _hardware_api_.HardwareDB().list_probes(
                    manufacturer_list=[
                        mf,
                    ],
                    return_unicums=True,
                ):
                    assert isinstance(p, _probe_unicum_.PROBE)
                    subitems.append(
                        {
                            "name": f"{mf}/{p.get_name()}",
                            "widgets": [
                                {
                                    "type": "image",
                                    "icon-path": p.get_probe_dict()["icon"],
                                },
                                {
                                    "type": "text",
                                    "text": p.get_name(),
                                    "color": text_color,
                                },
                            ],
                        }
                    )
                if len(subitems) > 0:
                    dropdown_elements[-1]["subitems"] = subitems
                continue

            # * Finish
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

            def finish(dropdown_elements, dropdown_selection) -> None:
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            probe: _probe_.Probe = item.get_projSegment()
            self.set_asterisk(probe.get_state("DEVICE", "asterisk"))
            self.lblTxt = (
                "*Device".ljust(20)
                if self.has_asterisk()
                else "Device ".ljust(20)
            )
            self.closedIconpath = probe.get_probe_dict()["icon"]
            self.openIconpath = probe.get_probe_dict()["icon"]
            self.set_error(probe.get_state("DEVICE", "error"))
            self.set_warning(probe.get_state("DEVICE", "warning"))
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                probe=probe,
                callback=finish,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        probe: _probe_.Probe,
        rootdir: Optional[ProbeRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """Create ProbeDeviceItem()-instance."""
        super().__init__(
            projSegment=probe,
            rootdir=rootdir,
            parent=parent,
            name="device",
            state=ProbeDeviceItem.Status(item=self),
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
        from_probename: str,
        to_probename: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_probename: Original probe name
        :param to_probename: New probe name
        """
        old_probename = from_probename.split("/")[-1]
        new_probename = to_probename.split("/")[-1]
        if old_probename == new_probename:
            return
        probe_unicum = _probe_unicum_.PROBE(new_probename)
        if probe_unicum is None:
            return
        probe: _probe_.Probe = self.get_projSegment()
        probe.change(
            probe_unicum,
            callback=None,
            callbackArg=None,
        )
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_probe_popup_.ProbeDeviceContextMenu(
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
        probe: _probe_.Probe = cast(_probe_.Probe, self.get_projSegment())
        if not probe.is_fake():
            super().contextmenuclick_itemBtn(key)

        def flash_bootloader(_key: str) -> None:
            assert not probe.is_fake()
            try:
                console = data.main_form.create_console("FLASH_BOOTLOADER")
                import project.makefile_target_executer as _executioner_

                _executioner_.MakefileTargetExecuter().execute_makefile_targets(
                    console=console,
                    target="flash_bootloader",
                    callback=None,
                    callbackArg=None,
                )
            except Exception as e:
                data.main_form.display.display_error(traceback.format_exc())
                traceback.print_exc()
            return

        def link(_key: str) -> None:
            url = probe.get_probe_dict()["link"]
            if (url is None) or (url.lower() == "none") or (url.strip() == ""):
                return
            functions.open_url(url)
            return

        def _help(_key: str) -> None:
            _ht_.probe_help(probe)
            return

        funcs = {
            "flash_bootloader": flash_bootloader,
            "link": link,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                 PROBE TRANSPORT PROTOCOL ITEM                                  ^#
# % ============================================================================================== %#
# % ProbeTransportProtocolItem()                                                                   %#
# %                                                                                                %#


class ProbeTransportProtocolItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ProbeTransportProtocolItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/chip/chip_protocol.png"
            self.openIconpath = "icons/chip/chip_protocol.png"
            self.lblTxt = "Transport Protocol "
            return

        def __get_dropdown_elements(
            self,
            probe: _probe_.Probe,
            callback: Callable,
        ) -> None:
            """> callback(dropdown_elements, dropdown_selection)"""
            # * Figure out current selection
            dropdown_selection = probe.get_transport_protocol_name()

            # * Fill dropdown elements
            text_color = "default"
            red_color = "red"
            dropdown_elements: List[Dict] = []
            for tp_unicum in _hardware_api_.HardwareDB().list_tps(
                return_unicums=True
            ):
                assert isinstance(tp_unicum, _probe_unicum_.TRANSPORT_PROTOCOL)
                tp_name = tp_unicum.get_name()
                tp_color = text_color
                if not probe.is_compatible(tp_unicum):
                    tp_color = red_color
                dropdown_elements.append(
                    {
                        "name": tp_name,
                        "widgets": [
                            {
                                "type": "text",
                                "text": tp_name,
                                "color": tp_color,
                            },
                        ],
                    }
                )
                continue

            # * Finish
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

            def finish(dropdown_elements, dropdown_selection) -> None:
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            probe: _probe_.Probe = item.get_projSegment()
            self.set_asterisk(probe.get_state("TRANSPORT_PROTOCOL", "asterisk"))
            self.lblTxt = (
                "*Transport Protocol"
                if self.has_asterisk()
                else "Transport Protocol "
            )
            self.lblTxt = self.lblTxt.ljust(20)
            self.closedIconpath = "icons/chip/chip_protocol.png"
            self.openIconpath = "icons/chip/chip_protocol.png"
            self.set_error(probe.get_state("TRANSPORT_PROTOCOL", "error"))
            self.set_warning(probe.get_state("TRANSPORT_PROTOCOL", "warning"))
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                probe=probe,
                callback=finish,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        probe: _probe_.Probe,
        rootdir: Optional[ProbeRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """Create ProbeTransportProtocolItem()-instance."""
        super().__init__(
            projSegment=probe,
            rootdir=rootdir,
            parent=parent,
            name="transport_protocol",
            state=ProbeTransportProtocolItem.Status(item=self),
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
        from_tp_name: str,
        to_tp_name: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_tp_name: Previous Transport Protocol name
        :param to_tp_name: New Transport Protocol name
        """
        if from_tp_name == to_tp_name:
            return
        tp_unicum = _probe_unicum_.TRANSPORT_PROTOCOL(to_tp_name)
        if tp_unicum is None:
            return
        probe: _probe_.Probe = self.get_projSegment()
        probe.change(
            tp_unicum,
            callback=None,
            callbackArg=None,
        )
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_probe_popup_.ProbeTransportProtocolContextMenu(
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
        probe: _probe_.Probe = cast(_probe_.Probe, self.get_projSegment())
        if not probe.is_fake():
            super().contextmenuclick_itemBtn(key)

        def _help(_key):
            _ht_.probe_transport_protocol_help(probe)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
