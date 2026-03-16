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
from components.singleton import Unicum
import traceback, threading, functools
import qt, functions, data, purefunctions
import dashboard.items.probe_items.probe_items as _da_probe_items_
import dashboard.items.probe_items.probe_comportitem as _da_probe_comportitem_
import project.segments.project_segment as _ps_
import hardware_api.probe_unicum as _probe_unicum_
import hardware_api.hardware_api as _hardware_api_
import fnmatch as _fn_

if TYPE_CHECKING:
    import gui.helpers.advancedcombobox as _advanced_combobox_
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
from various.kristofstuff import *


class Probe(_ps_.ProjectSegment):
    @classmethod
    def create_default_Probe(cls, probe_unicum: _probe_unicum_.PROBE) -> Probe:
        """Create a default Probe()-instance for the given 'probe_unicum'."""
        assert probe_unicum is not None
        return cls(
            is_fake=False,
            probe_unicum=probe_unicum,
            transport_protocol_unicum=None,  # Default one will be selected
            previous_comport_name=None,
        )

    @classmethod
    def create_empty_Probe(cls) -> Probe:
        """Create an empty Probe()-instance."""
        return cls.create_default_Probe(_probe_unicum_.PROBE("NONE"))

    @classmethod
    def load(
        cls,
        configcode: Optional[Dict[str, str]],
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load Probe()-object from the relevant part in the config file.

        Note: The project_report is not returned but simply modified here.
        """
        probe_unicum: Optional[_probe_unicum_.PROBE] = None
        transport_protocol_unicum: Optional[
            _probe_unicum_.TRANSPORT_PROTOCOL
        ] = None
        previous_comport_name: Optional[str] = None

        # & Extract probe unicum
        # $ Figure out name
        probe_name = None
        if configcode is None:
            probe_name = "none"
            purefunctions.printc(
                f"WARNING: Probe().load() got configcode parameter None\n",
                color="warning",
            )
        else:
            try:
                probe_name = configcode["probe_name"]
            except:
                try:
                    probe_name = configcode["probe"]
                except:
                    probe_name = "none"
                    purefunctions.printc(
                        f"WARNING: The {q}dashboard_config.btl{q} file does not define a probe\n",
                        color="warning",
                    )
        if (probe_name is None) or (probe_name.lower() in ("none", "null")):
            probe_name = "none"
        if probe_name.lower() == "arduino_standard":
            probe_name = "usb_to_uart_converter"

        # $ Construct unicum
        try:
            probe_unicum = _probe_unicum_.PROBE(probe_name)
        except Exception:
            probe_unicum = _probe_unicum_.PROBE("none")
            purefunctions.printc(
                f"WARNING: Embeetle does not recognize probe {q}{probe_name}{q}\n",
                color="warning",
            )

        # & Extract transport protocol unicum
        # $ Figure out name
        transport_protocol_name = None
        if configcode is None:
            transport_protocol_name = "none"
        else:
            try:
                transport_protocol_name = configcode["transport_protocol"]
            except KeyError:
                try:
                    transport_protocol_name = configcode[
                        "transport_protocol_name"
                    ]
                except KeyError:
                    transport_protocol_name = "none"
                    purefunctions.printc(
                        f"WARNING: The {q}dashboard_config.btl{q} file does not define the "
                        f"transport protocol\n",
                        color="warning",
                    )
        if probe_unicum.get_name().lower() == "usb_to_uart_converter":
            transport_protocol_name = "uart"

        # $ Construct unicum
        try:
            transport_protocol_unicum = _probe_unicum_.TRANSPORT_PROTOCOL(
                transport_protocol_name
            )
        except KeyError:
            transport_protocol_unicum = _probe_unicum_.TRANSPORT_PROTOCOL(
                "none"
            )
            purefunctions.printc(
                f"WARNING: Embeetle does not recognize transport protocol "
                f"{q}{transport_protocol_name}{q}\n",
                color="warning",
            )

        # & Extract previous comport name
        previous_comport_name = None
        if configcode is None:
            previous_comport_name = None
        else:
            try:
                previous_comport_name = configcode["COM_port"]
            except KeyError:
                previous_comport_name = None
        if previous_comport_name is not None:
            if previous_comport_name.lower() in ("none", "null"):
                previous_comport_name = None

        # & Finish
        assert probe_unicum is not None
        assert transport_protocol_unicum is not None
        probe = cls(
            is_fake=False,
            probe_unicum=probe_unicum,
            transport_protocol_unicum=transport_protocol_unicum,
            previous_comport_name=previous_comport_name,
        )
        callback(probe, callbackArg)
        return

    __slots__ = (
        "__probe_unicum",
        "__transport_protocol_unicum",
        "__chosen_comport_datastruct",
        "__previous_comport_name",
        "__state_dict",
        "_v_rootItem",
        "_v_deviceItem",
        "_v_transportProtocolItem",
        "_v_comportItem",
        "__trigger_dashboard_refresh_mutex",
    )

    def __init__(
        self,
        is_fake: bool,
        probe_unicum: _probe_unicum_.PROBE,
        transport_protocol_unicum: Optional[_probe_unicum_.TRANSPORT_PROTOCOL],
        previous_comport_name: Optional[str],
    ) -> None:
        """A Probe()-instance represents the programmer/debug probe. It contains
        info like the TRANSPORT_PROTOCOL (the communication protocol between the
        probe and the microcontroller), ...

        :param probe_unicum: Unicum-instance, (eg. PROBE('stlink-v2') ), holds
            the official name and iconpath.
        :param transport_protocol_unicum: Unicum-instance, protocol for
            communication between probe and chip.
        """
        super().__init__(is_fake)

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        # & Variables
        assert probe_unicum is not None
        if transport_protocol_unicum is None:
            transport_protocol_list = probe_unicum.get_probe_dict()[
                "transport_protocols"
            ]
            if (transport_protocol_list is None) or (
                len(transport_protocol_list) == 0
            ):
                default_transport_protocol_name = "custom"
            else:
                default_transport_protocol_name = transport_protocol_list[0]
            transport_protocol_unicum = _probe_unicum_.TRANSPORT_PROTOCOL(
                default_transport_protocol_name
            )
        assert transport_protocol_unicum is not None
        self.__probe_unicum = probe_unicum
        self.__transport_protocol_unicum = transport_protocol_unicum
        self.__chosen_comport_datastruct: Optional[Dict[str, str]] = None
        self.__previous_comport_name: Optional[str] = previous_comport_name
        self.__state_dict = {
            "DEVICE": {
                "error": False,
                "warning": False,
                "asterisk": False,
            },
            "TRANSPORT_PROTOCOL": {
                "error": False,
                "warning": False,
                "asterisk": False,
            },
            "COMPORT": {
                "error": False,
                "warning": False,
                "asterisk": False,
            },
        }

        # & History
        if not is_fake:
            self.get_history().register_getters(
                probe_unicum=self.get_probe_unicum,
                transport_protocol_unicum=self.get_transport_protocol_unicum,
                comport_name=self.get_comport_name,
            )
            self.get_history().register_setters(
                probe_unicum=self.set_probe_unicum,
                transport_protocol_unicum=self.set_transport_protocol_unicum,
                comport_name=self.set_comport_name,
            )
            self.get_history().register_asterisk_setters(
                probe_unicum=self.set_probe_asterisk,
                transport_protocol_unicum=self.set_transport_protocol_asterisk,
                comport_name=self.set_comport_asterisk,
            )
            self.get_history().register_refreshfunc(
                self.trigger_dashboard_refresh,
            )

        # & Dashboard
        self._v_rootItem: Optional[_da_probe_items_.ProbeRootItem] = None
        self._v_deviceItem: Optional[_da_probe_items_.ProbeDeviceItem] = None
        self._v_transportProtocolItem: Optional[
            _da_probe_items_.ProbeTransportProtocolItem
        ] = None
        self._v_comportItem: Optional[
            _da_probe_comportitem_.ProbeComportItem
        ] = None
        return

    def get_probe_unicum(self) -> _probe_unicum_.PROBE:
        """Access the PROBE()-Unicum."""
        return self.__probe_unicum

    def get_transport_protocol_unicum(
        self,
    ) -> _probe_unicum_.TRANSPORT_PROTOCOL:
        """Access the TRANSPORT_PROTOCOL()-Unicum."""
        return self.__transport_protocol_unicum

    def set_probe_unicum(self, probe_unicum: _probe_unicum_.PROBE) -> None:
        """Swap the PROBE()-Unicum."""
        assert isinstance(probe_unicum, _probe_unicum_.PROBE)
        self.__probe_unicum = probe_unicum
        return

    def set_transport_protocol_unicum(
        self,
        transport_protocol_unicum: _probe_unicum_.TRANSPORT_PROTOCOL,
    ) -> None:
        """Swap the TRANSPORT_PROTOCOL()-Unicum."""
        assert isinstance(
            transport_protocol_unicum, _probe_unicum_.TRANSPORT_PROTOCOL
        )
        self.__transport_protocol_unicum = transport_protocol_unicum
        return

    def get_name(self) -> str:
        """Get the name of the PROBE()-Unicum."""
        return self.__probe_unicum.get_name()

    def get_transport_protocol_name(self) -> str:
        """Get the name of the TRANSPORT_PROTOCOL()-Unicum."""
        return self.__transport_protocol_unicum.get_name()

    def get_probe_dict(self) -> Dict[str, Any]:
        """Access the json-dictionary from the PROBE()-Unicum."""
        return self.__probe_unicum.get_probe_dict()

    def clone(self, is_fake: bool = True) -> Probe:
        """Clone this object.

        Method used by Intro Wizard to populate itself with fake objects.
        """
        cloned_probe = Probe(
            is_fake=is_fake,
            probe_unicum=self.__probe_unicum,
            transport_protocol_unicum=self.__transport_protocol_unicum,
            previous_comport_name=None,
        )
        return cloned_probe

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show this Probe()-instance on the dashboard.

        In fact, only the toplevel item is shown. But the child items are
        instantiated and added to the toplevel item. They get shown when the
        user clicks on the toplevel item.
        """
        assert not self.is_fake()
        self._v_rootItem = _da_probe_items_.ProbeRootItem(probe=self)
        self._v_deviceItem = _da_probe_items_.ProbeDeviceItem(
            probe=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_transportProtocolItem = (
            _da_probe_items_.ProbeTransportProtocolItem(
                probe=self,
                rootdir=self._v_rootItem,
                parent=self._v_rootItem,
            )
        )
        self._v_rootItem.add_child(
            self._v_deviceItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        self._v_rootItem.add_child(
            self._v_transportProtocolItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        data.dashboard.add_root(self._v_rootItem)

        # & Check for error
        toolpath_seg: _toolpath_seg_.ToolpathSeg = (
            data.current_project.get_toolpath_seg()
        )
        toolpath_seg.set_error(
            "FLASHTOOL",
            not self.is_compatible(toolpath_seg.get_unique_id("FLASHTOOL")),
        )
        callback(callbackArg) if callback is not None else nop()
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the PROBE on the Intro Wizard, inside the given vlyt."""
        assert self.is_fake()
        self._v_deviceItem = _da_probe_items_.ProbeDeviceItem(
            probe=self,
            rootdir=None,
            parent=None,
        )
        self._v_deviceItem.get_layout().initialize()
        vlyt.addLayout(self._v_deviceItem.get_layout())

        self._v_transportProtocolItem = (
            _da_probe_items_.ProbeTransportProtocolItem(
                probe=self,
                rootdir=None,
                parent=None,
            )
        )
        self._v_transportProtocolItem.get_layout().initialize()
        vlyt.addLayout(self._v_transportProtocolItem.get_layout())
        return

    def get_impacted_files(self) -> List[str]:
        """"""
        impacted_files = []
        if self.__state_dict["DEVICE"]["asterisk"]:
            impacted_files.append("DASHBOARD_MK")
            impacted_files.append("OPENOCD_PROBEFILE")
            impacted_files.append("GDB_FLASHFILE")
            impacted_files.append("BUTTONS_BTL")

        if self.__state_dict["TRANSPORT_PROTOCOL"]["asterisk"]:
            impacted_files.append("OPENOCD_PROBEFILE")

        return impacted_files

    def get_state(self, obj: str, errtype: str) -> bool:
        """"""
        return self.__state_dict[obj][errtype]

    def update_states(
        self,
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """The states no longer get pushed directly to the GUI elements.

        Instead, I store them locally in the Probe()-instance. The GUI elements
        pull them when syncing.
        """
        device_err = (self.get_name() is None) or (
            self.get_name().lower() == "none"
        )
        transport_protocol_err = not self.is_compatible(
            self.get_transport_protocol_unicum(),
        )
        self.__state_dict["DEVICE"]["error"] = device_err
        self.__state_dict["TRANSPORT_PROTOCOL"][
            "error"
        ] = transport_protocol_err
        if project_report is not None:
            project_report["probe_report"]["DEVICE"]["error"] = device_err
            project_report["probe_report"]["TRANSPORT_PROTOCOL"][
                "error"
            ] = transport_protocol_err

        if callback is not None:
            callback(callbackArg)
        return

    def trigger_dashboard_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Applies both on Dashboard and Intro Wizard. It will do:

        - update own states
        - update states of related segments (toolpath_seg)
        - refresh own's widgets
        """
        if not self.__trigger_dashboard_refresh_mutex.acquire(blocking=False):
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.trigger_dashboard_refresh,
                    callback,
                    callbackArg,
                ),
            )
            return
        is_fake = self.is_fake()
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None
        if is_fake:
            toolpath_seg = (
                data.current_project.intro_wiz.get_fake_toolpath_seg()
            )
        else:
            toolpath_seg = data.current_project.get_toolpath_seg()

        def update_toolpath_states(*args) -> None:
            # Update states of the ToolpathSeg(), then go to the next function depending on some
            # factors.
            next_func: Optional[Callable] = None
            next_arg: Optional[bool] = None

            # & Dashboard
            if not is_fake:
                if self._v_rootItem is None:
                    next_func = finish
                elif self.__probe_unicum.get_probe_dict()["needs_serial_port"]:
                    next_func = show_comport
                else:
                    next_func = hide_comport

            # & Intro Wizard
            else:
                next_func = start_refresh
                next_arg = False

            # & Both
            toolpath_seg.update_states(
                callback=next_func,
                callbackArg=next_arg,
            )
            return

        def hide_comport(*args) -> None:
            "[dashboard only]"
            assert not is_fake
            try:
                data.main_form.serial_port.setVisible(False)  # type: ignore
            except:
                traceback.print_exc()
            if self._v_comportItem is None:
                start_refresh(True)
                return
            self._v_comportItem.self_destruct(
                killParentLink=True,
                callback=start_refresh,
                callbackArg=True,
            )
            return

        def show_comport(*args) -> None:
            "[dashboard only]"
            assert not is_fake
            try:
                data.main_form.serial_port.setVisible(True)  # type: ignore
            except:
                traceback.print_exc()
            if self.__chosen_comport_datastruct is None:
                # Try to set the COM-port to the previously selected one, if possible. Otherwise,
                # take the first available one. This method does not do any refreshment!
                self.set_comport_name(comport_name=self.__previous_comport_name)
            if self._v_comportItem is not None:
                start_refresh(False)
                return
            self._v_comportItem = _da_probe_comportitem_.ProbeComportItem(
                probe=self,
                rootdir=self._v_rootItem,
                parent=self._v_rootItem,
            )
            self._v_rootItem.add_child(
                self._v_comportItem,
                alpha_order=False,
                show=True,
                callback=start_refresh,
                callbackArg=False,
            )
            return

        def start_refresh(comport_item_killed: bool, *args) -> None:
            if comport_item_killed:
                self._v_comportItem = None

            # & Dashboard
            # Refresh the root item recursively
            if not is_fake:
                if self._v_comportItem is not None:
                    self.refresh_comport_dropdown("dashboard")
                    self.refresh_comport_dropdown("toolbar")
                # The COM-port in the Serial Monitor must refresh regardless of the COM-port
                # existence in the Dashboard and Toolbar.
                self.refresh_comport_dropdown("console")
                if (self._v_rootItem is None) or (
                    self._v_rootItem._v_emitter is None
                ):
                    finish()
                    return
                self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                    True,
                    False,
                    finish,
                    None,
                )
                return

            # & Intro Wizard
            # Just refresh the device item and the transport protocol item, but
            # it's not sure they exist.
            assert is_fake
            if (self._v_deviceItem is None) or (
                self._v_deviceItem._v_emitter is None
            ):
                refresh_transport_item()
                return
            self._v_deviceItem._v_emitter.refresh_later_sig.emit(
                True,
                False,
                refresh_transport_item,
                None,
            )
            return

        def refresh_transport_item(*args) -> None:
            "[intro wiz only]"
            assert is_fake
            if (self._v_transportProtocolItem is None) or (
                self._v_transportProtocolItem._v_emitter is None
            ):
                finish()
                return
            self._v_transportProtocolItem._v_emitter.refresh_later_sig.emit(
                True,
                False,
                finish,
                None,
            )
            return

        def finish(*args) -> None:
            # & Intro Wizard
            if is_fake:
                self.__trigger_dashboard_refresh_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return

            # & Dashboard
            if data.dashboard is not None:
                data.dashboard.check_unsaved_changes()
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        self.update_states(
            callback=update_toolpath_states,
            callbackArg=None,
        )
        return

    def set_probe_asterisk(self, on: bool) -> None:
        """"""
        self.__state_dict["DEVICE"]["asterisk"] = on
        return

    def set_transport_protocol_asterisk(self, on: bool) -> None:
        """"""
        self.__state_dict["TRANSPORT_PROTOCOL"]["asterisk"] = on
        return

    def set_comport_asterisk(self, on: bool) -> None:
        """"""
        # Never set asterisks for a changed COM-port!
        # self.__state_dict['COMPORT']['asterisk'] = on
        return

    def is_compatible_with_flashtool(self, uid: str) -> bool:
        """Check if this particular instance is compatible with the given
        flashtool unique id.

        Let the custom-probe always be compatible (otherwise all flashtools get
        colored red in the dropdown if you have no probe selected).
        """
        if (self.get_name().lower() == "custom") or (
            self.get_name().lower() == "none"
        ):
            return True
        if (
            (uid is None)
            or (uid.lower() == "none")
            or (uid.lower() == "custom")
        ):
            return False
        assert isinstance(uid, str)
        patterns = self.__probe_unicum.get_probe_dict().get(
            "flashtool_patterns"
        )
        if patterns is None:
            _hardware_api_.HardwareDB().reset()
            return self.is_compatible_with_flashtool(uid)
        for p in patterns:
            if _fn_.fnmatch(name=uid, pat=p):
                return True
        return False

    def is_compatible(
        self, unicum_or_str: Union[_probe_unicum_.TRANSPORT_PROTOCOL, str]
    ) -> bool:
        """
        Check if this probe is compatible with the given parameter: either a tool unique_id or a
        transport protocol.
        """
        assert (
            isinstance(unicum_or_str, _probe_unicum_.TRANSPORT_PROTOCOL)
            or isinstance(unicum_or_str, str)
            or unicum_or_str is None
        )

        # $ 'unicum_or_str' is None
        if unicum_or_str is None:
            return False
        if isinstance(unicum_or_str, _probe_unicum_.TRANSPORT_PROTOCOL) and (
            unicum_or_str.get_name().lower() == "none"
        ):
            return False
        if isinstance(unicum_or_str, str) and (unicum_or_str.lower() == "none"):
            return False

        # $ This probe is None
        if (self.get_probe_unicum() is None) or (
            self.get_name().lower() == "none"
        ):
            # If this probe is None, then this probe must be colored red, not all the other parts in
            # the dashboard!
            return True

        # $ 'unicum_or_str' is a string
        # Called from TOOLS section, 'unicum_or_str' is a unique_id like: 'openocd_nuvoton_0.10.0_
        # dev00465_32b'. Compatibility of selected tool with probe is tested here.
        if isinstance(unicum_or_str, str):
            unicum_or_str = (
                unicum_or_str.lower().replace(" ", "-").replace("_", "-")
            )
            return self.is_compatible_with_flashtool(uid=unicum_or_str)

        # $ 'unicum_or_str' is an unicum
        # Local call. Test compatibility between probe and transport protocol.
        else:
            unicum_or_str = (
                unicum_or_str.get_name()
                .lower()
                .replace(" ", "-")
                .replace("_", "-")
            )
            compatible_tps = [
                e.lower().replace(" ", "-").replace("_", "-")
                for e in self.__probe_unicum.get_probe_dict()[
                    "transport_protocols"
                ]
            ]
            for tp in compatible_tps:
                if tp == unicum_or_str:
                    return True
                continue
        return False

    def change(
        self,
        e: Union[
            Unicum, _probe_unicum_.PROBE, _probe_unicum_.TRANSPORT_PROTOCOL
        ],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Change probe or transport protocol and trigger a dashboard refresh.

        Also the corresponding ToolpathSeg() and TreepathSeg() get refreshed.
        Works for both the Dashboard and the Intro Wizard.
        """
        is_fake = self.is_fake()
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None
        treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None
        if is_fake:
            toolpath_seg = (
                data.current_project.intro_wiz.get_fake_toolpath_seg()
            )
            treepath_seg = (
                data.current_project.intro_wiz.get_fake_treepath_seg()
            )
        else:
            toolpath_seg = data.current_project.get_toolpath_seg()
            treepath_seg = data.current_project.get_treepath_seg()

        def refresh_self(*args):
            self.trigger_dashboard_refresh(
                callback=refresh_toolpath,
                callbackArg=None,
            )
            return

        def refresh_toolpath(*args):
            toolpath_seg.trigger_dashboard_refresh(
                callback=refresh_treepath,
                callbackArg=None,
            )
            return

        def refresh_treepath(*args):
            treepath_seg.trigger_dashboard_refresh(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        if (self.__probe_unicum == e) or (
            self.__transport_protocol_unicum == e
        ):
            finish()
            return
        if not is_fake:
            self.get_history().push()
        if isinstance(e, _probe_unicum_.PROBE):
            self.__probe_unicum = e
        elif isinstance(e, _probe_unicum_.TRANSPORT_PROTOCOL):
            self.__transport_protocol_unicum = e
        else:
            print(f"e = {e.get_name()}")
            assert False
        if not is_fake:
            self.get_history().compare_to_baseline(
                refresh=False,
                callback=refresh_self,
                callbackArg=None,
            )
            return
        refresh_self()
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        assert not self.is_fake()
        super().printout(nr)
        lines = [
            f"# {nr}. Probe ",
            f"probe_name         = {q}{self.__probe_unicum.get_name()}{q}",
            f"transport_protocol = {q}{self.get_transport_protocol_name()}{q} # Protocol for communication between Probe and Microcontroller.",
        ]
        if self.get_comport_name() is not None:
            lines.append(
                f"COM_port           = {q}{self.get_comport_name()}{q}"
            )
        lines.append("")
        return "\n".join(lines)

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Probe()-instance and *all* its representations in the
        Dashboard or Intro Wizard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill Probe() twice!")
            self.dead = True

        def start(*args) -> None:
            # $ Dashboard
            if not self.is_fake():
                if self._v_rootItem:
                    self._v_rootItem.self_destruct(
                        killParentLink=False,
                        callback=finish,
                        callbackArg=None,
                    )
                    return
                finish()
                return
            # $ Intro Wizard
            if self._v_deviceItem:
                self._v_deviceItem.self_destruct(
                    killParentLink=False,
                    callback=kill_tp_item,
                    callbackArg=None,
                )
                return
            kill_tp_item()
            return

        def kill_tp_item(*args) -> None:
            "[fake only]"
            assert self.is_fake()
            if self._v_transportProtocolItem:
                self._v_transportProtocolItem.self_destruct(
                    killParentLink=False,
                    callback=kill_comport_item,
                    callbackArg=None,
                )
                return
            kill_comport_item()
            return

        def kill_comport_item(*args) -> None:
            "[fake only]"
            assert self.is_fake()
            if self._v_comportItem:
                self._v_comportItem.self_destruct(
                    killParentLink=False,
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            self._v_rootItem = None
            self._v_deviceItem = None
            self._v_transportProtocolItem = None
            self._v_comportItem = None
            if callback is not None:
                callback(callbackArg)
            return

        super().self_destruct(
            callback=start,
            callbackArg=None,
            death_already_checked=True,
        )
        return

    # ^                                            COMPORTS                                            ^#
    # % ============================================================================================== %#
    # % COM-ports                                                                                      %#
    # %                                                                                                %#

    def get_comport_name(self) -> Optional[str]:
        """Get the name of the chosen COM-port (eg.

        'COM4').
        """
        assert not self.is_fake()
        if self.__chosen_comport_datastruct is None:
            return None
        return self.__chosen_comport_datastruct["name"]

    def set_comport_name(self, comport_name: Optional[str]) -> None:
        """Try to set the comport from this Probe()-segment to the given name.
        If the COM-port doesn't exist, just take the first available one.

        WARNING:
        This method does NOT invoke any refreshes!
        """
        assert not self.is_fake()
        if (comport_name is None) or (comport_name.lower() == "none"):
            self.__chosen_comport_datastruct = None
            return

        # * Acquire serial data
        serial_port_data = data.serial_port_data
        if serial_port_data is None:
            serial_port_data = functions.list_serial_ports()
            if (serial_port_data is None) or (len(serial_port_data) == 0):
                serial_port_data = None
            data.serial_port_data = serial_port_data
        if (serial_port_data is None) or (len(serial_port_data) == 0):
            self.__chosen_comport_datastruct = None
            return

        # * Make choice
        # Prefer the given name.
        values_view = serial_port_data.values()
        for serial_port_dict in values_view:
            if (
                ("name" in serial_port_dict)
                and (serial_port_dict["name"] is not None)
                and (serial_port_dict["name"].lower() == comport_name.lower())
            ):
                self.__chosen_comport_datastruct = serial_port_dict
                break
        else:
            value_iterator = iter(values_view)
            try:
                first_value = next(value_iterator)
                self.__chosen_comport_datastruct = first_value
            except Exception:
                self.__chosen_comport_datastruct = None
        return

    def dropdown_selection_changed_from_to(
        self,
        dropdown_src: str,
        from_comport: str,
        to_comport: str,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """One of the dropdown widgets has been used. This is a central function
        to handle them all.

        :param dropdown_src: 'toolbar', 'dashboard', 'console'
        :param from_comport: eg. 'COM4'
        :param to_comport: eg. 'COM5'
        """
        purefunctions.printc(
            f"dropdown_selection_changed_from_to(\n"
            f"    dropdown_src = {dropdown_src},\n"
            f"    from_comport = {from_comport},\n"
            f"    to_comport   = {to_comport},\n"
            f")\n"
        )
        # * Sanitize input
        if (from_comport is None) or (from_comport.lower() == "none"):
            from_comport = "NONE"
        if (to_comport is None) or (to_comport.lower() == "none"):
            to_comport = "NONE"

        # * Check source
        # & TOOLBAR
        if dropdown_src == "toolbar":
            # $ Invocation:
            # qt.QAction() instance named 'toolbar_serial_monitor' in 'mainwindow.py' calls a local
            # function named 'toolbar_serial_monitor_clicked()'. This calls the following function
            # 'toolbar_comport_selection_changed_from_to()' in 'functions.py' which then calls this
            # function here.
            pass
        # & DASHBOARD
        elif dropdown_src == "dashboard":
            # $ Invocation:
            # 'selection_changed_from_to()' function in `probe_comportitem.py` calls this function
            # here.
            pass

        # & SERIAL CONSOLE
        elif dropdown_src == "console":
            # $ Invocation:
            # The method 'comport_selection_changed()' from the SerialConsole()-instance calls this
            # function here.
            pass
            # $ Handle everything here
            # We don't want the COM-port selection in the serial console to mess with the Probe()-
            # segment. Potentially, there even is no COM-port selector at all in this Probe()! So
            # do everything right here.
            combobox = data.serial_console.get_comport_dropdown()
            if to_comport.lower() == "refresh":
                data.serial_port_data = functions.list_serial_ports()
                try:
                    combobox.set_selected_name(from_comport)
                except:
                    traceback.print_exc()
            # $ Compare to baseline refreshes everything
            # Compare the current Probe() state to the history baseline, which also invokes the
            # 'Probe().trigger_dashboard_refresh()' method, which in turn invokes the method
            # 'Probe().refresh_comport_dropdown()' three times (see method below), passing it the
            # names 'dashboard', 'toolbar' and 'console' respectively. Hence, all COM-port dropdown
            # widgets get refreshed!

            # $ Special case 1:
            # This Probe()-instance has no COM-port. In other words, the 'Probe()._v_comportItem'
            # variable is empty. Therefore, this 'dropdown_selection_changed_from_to()' method must
            # have been invoked by the Serial Monitor.
            # The 'Probe().trigger_dashboard_refresh()' calls 'Probe().refresh_comport_dropdown()'
            # just one time for this particular case, only passing it the 'console' name. It won't
            # pass the names 'dashboard' and 'toolbar', as they don't have this widget.

            # $ Special case 2:
            # The refresh turns out to eliminate the selected COM-port from the Dashboard and
            # Toolbar. It will just work.
            self.get_history().compare_to_baseline(
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # $ UNKNOWN SOURCE
        else:
            raise RuntimeError()

        # * No switch
        # The user clicked the same COM-port that was already selected.
        if from_comport == to_comport:
            # Compare to baseline, which refreshes everything (see explanation above for the SERIAL
            # CONSOLE).
            self.get_history().compare_to_baseline(
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # * Switch
        # The user clicked a new COM-port, or the 'refresh' option.
        # $ REFRESH
        # If the user requests a refresh, just refill the serial port data in the data module. Then
        # try to go back to the previous selection.
        if to_comport.lower() == "refresh":
            data.serial_port_data = functions.list_serial_ports()
            to_comport = from_comport
        # $ OTHER COM-PORT
        else:
            # Only push to history if the selection is not 'refresh'.
            self.get_history().push()
        # $ PERFORM SWITCH AND REFRESH
        # Perform the switch operation.
        self.set_comport_name(to_comport)
        # Compare to baseline, which refreshes everything (see explanation above for the SERIAL
        # CONSOLE).
        self.get_history().compare_to_baseline(
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def refresh_comport_dropdown(self, dropdown_name: str) -> None:
        """
        :param dropdown_name:  'toolbar', 'dashboard', 'console'

        Refresh a specific dropdown widget, such that it shows:
            - All COM-ports attached to the computer.
            - The currently active COM-port as stored in this Probe()-segment.
        """
        combobox: Optional[_advanced_combobox_.AdvancedComboBox] = None

        # $ TOOLBAR
        if dropdown_name == "toolbar":
            combobox = data.serial_port_combobox

        # $ DASHBOARD
        elif dropdown_name == "dashboard":
            if self._v_comportItem is not None:
                combobox = cast(
                    "_advanced_combobox_.AdvancedComboBox",
                    self._v_comportItem.get_widget("itemDropdown"),
                )

        # $ SERIAL CONSOLE
        elif dropdown_name == "console":
            if data.serial_console is None:
                return
            combobox = data.serial_console.get_comport_dropdown()

        # $ UNKNOWN SOURCE
        else:
            raise RuntimeError()

        if combobox is None:
            # Nothing to refresh
            return

        # & 1. Delete all
        combobox.clear()

        # & 2. Set elements
        dropdown_elements, dropdown_selection = (
            self.__get_comport_dropdown_elements(
                dropdown_name=dropdown_name,
            )
        )
        for e in dropdown_elements:
            try:
                combobox.add_item(
                    item=e,
                    do_update=False,
                )
            except Exception as e:
                traceback.print_exc()
            continue
        if dropdown_selection is not None:
            try:
                combobox.set_selected_name(dropdown_selection)
            except Exception as e:
                traceback.print_exc()

        # & 3. Set size
        if dropdown_name == "dashboard":
            combobox.set_minimum_height(
                max(
                    data.get_general_font_height(),
                    data.get_general_icon_pixelsize(is_inner=False),
                )
            )
        elif dropdown_name == "toolbar":
            combobox.set_minimum_height(
                max(
                    data.get_general_font_height(),
                    data.get_toolbar_pixelsize(),
                )
            )
        combobox.adjust_size()
        return

    def __get_comport_dropdown_elements(
        self,
        dropdown_name: str,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        :param dropdown_name:  'toolbar', 'dashboard', 'console'

        Define the dropdown elements and the current selected one, to be imposed on the given drop-
        down widget.

        NOTE:
        The current selection will always be set to 'self.get_comport_name()', unless we're dealing
        with the dropdown widget from the serial console. For that one, the current selection should
        just be whatever it was.

        :return dropdown_elements, dropdown_selection
        """
        # * Fill dropdown elements
        dropdown_elements: List[Dict] = []

        # $ Refresh the serial port data only if there is nothing cached
        serial_port_data = data.serial_port_data
        if serial_port_data is None:
            serial_port_data = functions.list_serial_ports()
            if (serial_port_data is None) or (len(serial_port_data) == 0):
                serial_port_data = None
            data.serial_port_data = serial_port_data

        # $ Build the 'dropdown_elements' dictionary
        black_color = "default"
        red_color = "red"
        blue_color = "blue"
        if (serial_port_data is None) or (len(serial_port_data) == 0):
            dropdown_elements.append(
                {
                    "name": "NONE",
                    "widgets": [
                        {
                            "type": "text",
                            "text": "NONE",
                            "color": red_color,
                        },
                    ],
                }
            )
        else:
            for key in serial_port_data.keys():
                dropdown_elements.append(
                    {
                        "name": key,
                        "widgets": [
                            {
                                "type": "text",
                                "text": key,
                                "color": black_color,
                            },
                        ],
                    }
                )
                continue
        dropdown_elements.append(
            {
                "name": "refresh",
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": "icons/dialog/refresh.png",
                    },
                    {
                        "type": "text",
                        "text": f" refresh ",
                        "color": blue_color,
                    },
                ],
            },
        )

        # * Define current selection
        # $ Figure out what the current selection should be
        dropdown_selection: Optional[str] = None
        comport_name: Optional[str] = None
        if dropdown_name == "console":
            combobox = data.serial_console.get_comport_dropdown()
            dropdown_selection = combobox.get_selected_item_name()
            if (
                (dropdown_selection is None)
                or (dropdown_selection.lower() == "none")
                or (dropdown_selection.lower() == "empty")
            ):
                # Do the same as for the dropdown widgets in Dashboard and Tool-
                # bar.
                comport_name = self.get_comport_name()
                if (
                    (comport_name is None)
                    or (comport_name.lower() == "none")
                    or (comport_name.lower() == "empty")
                ):
                    dropdown_selection = "NONE"
                else:
                    dropdown_selection = comport_name
        else:
            comport_name = self.get_comport_name()
            if (
                (comport_name is None)
                or (comport_name.lower() == "none")
                or (comport_name.lower() == "empty")
            ):
                dropdown_selection = "NONE"
            else:
                dropdown_selection = comport_name

        # $ Compare with what is in the elements
        for e in dropdown_elements:
            if e["name"] == dropdown_selection:
                break
        else:
            # No hit!
            # This is a dangerous situation. Changing the current selection is
            # needed, but can unsync the stored one in this Probe()-segment!
            dropdown_selection = dropdown_elements[0]["name"]

            def finish(*args) -> None:
                self.get_history().compare_to_baseline()
                return

            if dropdown_name == "toolbar":
                # We only want to push to history once, for this particular edge
                # case. The Dashboard widget can be dead, not the Toolbar wid-
                # get.
                self.get_history().push()
            # Set the comport name for this Probe()-segment. Then trigger a
            # baseline comparison for the history.
            self.set_comport_name(dropdown_selection)
            qt.QTimer.singleShot(200, finish)

        return dropdown_elements, dropdown_selection
