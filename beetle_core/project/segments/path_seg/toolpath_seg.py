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
import os, threading, functools
import qt, data, purefunctions
import dashboard.items.path_items.toolpath_items as _da_toolpath_items_
import project.segments.path_seg.path_seg as _ps_
import bpathlib.path_power as _pp_
import hardware_api.toolcat_unicum as _toolcat_unicum_
import hardware_api.hardware_api as _hardware_api_
import bpathlib.tool_obj as _tool_obj_
import fnmatch as _fn_

if TYPE_CHECKING:
    import project.segments.chip_seg.chip as _chip_
    import project.segments.probe_seg.probe as _probe_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
from various.kristofstuff import *

"""
                              ┌────────────────────┐
                              │     PathSeg()      │
                              └────────────────────┘
             ┌──────────────────────────┴─────────────────────────┐
             ↓                                                    ↓
    ┌────────────────────┐                              ╔════════════════════╗
    │   TreepathSeg()    │                              ║   ToolpathSeg()    ║
    └────────────────────┘                              ╚════════════════════╝
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - ...                                                - ...

    Each:                                               Each:
      -> encapsulates a TREEPATH_UNIC() Unicum            -> is a shell for the corresponding ToolmanObj()
      -> holds one TreepathItem() for dashboard           -> holds one ToolpathItem() for dashboard

"""


class ToolpathSeg(_ps_.PathSeg):
    @classmethod
    def create_default_ToolpathSeg(
        cls,
        chip: _chip_.Chip,
    ) -> ToolpathSeg:
        """Create ToolpathSeg()-instance based on the default tool-unique_ids
        and pass it to the callback."""
        pathdict = {}
        for toolcat_unic in _hardware_api_.HardwareDB().list_toolcat_unicums(
            return_unicums=True
        ):
            assert isinstance(toolcat_unic, _toolcat_unicum_.TOOLCAT_UNIC)
            unique_id = toolcat_unic.get_default_unique_id(
                boardname=None,
                chipname=chip.get_name(),
                probename=None,
            )
            pathdict[toolcat_unic.get_name()] = unique_id
            continue
        return cls(
            is_fake=False,
            pathdict=pathdict,
        )

    @classmethod
    def create_empty_ToolpathSeg(cls) -> ToolpathSeg:
        """Create ToolpathSeg()-instance with empty unique_ids."""
        pathdict: Dict[str, Optional[str]] = {}
        for toolcat_name in _hardware_api_.HardwareDB().list_toolcat_unicums():
            pathdict[toolcat_name] = None
        return cls(
            is_fake=False,
            pathdict=pathdict,
        )

    @classmethod
    def load(
        cls,
        configcode: Optional[Dict[str, str]],
        beetle_tools_abspath: str,
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load ToolpathSeg()-instance from the given configscript.

        NOTES: - The 'project_report' is not returned, but simply modified here.
               - Errors and warnings in the 'project_report' are not set here, but later on in the
                 update_states() method!
        """
        pathdict: Dict[str, Optional[str]] = {}

        def extract_unique_id(catname: str) -> Optional[str]:
            # Extract unique id from 'configcode'
            _unique_id: Optional[str] = None
            if configcode is None:
                return None
            try:
                _unique_id = configcode[catname]
            except:
                if catname.upper() == "FLASHTOOL":
                    try:
                        _unique_id = configcode["FLASH_TOOL"]
                    except:
                        try:
                            _unique_id = configcode["FLASH_DEBUG_SERVER"]
                        except:
                            return None
                else:
                    return None
            if (_unique_id is None) or (_unique_id.lower() in ("none", "null")):
                return None
            return _unique_id

        def fill_project_report(
            remote_toollist: List[Dict[str, str]], *args
        ) -> None:
            if remote_toollist is None:
                project_report["connection_report"]["connection_failed"] = True
            else:
                project_report["remote_toollist"] = remote_toollist
            for (
                _toolcat_name
            ) in _hardware_api_.HardwareDB().list_toolcat_unicums():
                proj_uid = extract_unique_id(_toolcat_name)
                # $ Nothing to search for
                if (proj_uid is None) or (proj_uid.lower() == "none"):
                    project_report["toolpath_report"][_toolcat_name][
                        "proj_uid"
                    ] = None
                    project_report["toolpath_report"][_toolcat_name][
                        "toolman_uid"
                    ] = None
                    project_report["toolpath_report"][_toolcat_name][
                        "remote_uid"
                    ] = None
                    continue
                # $ Built in flash-debug-server
                if _fn_.fnmatch(name=proj_uid, pat="*built*in*"):
                    project_report["toolpath_report"][_toolcat_name][
                        "proj_uid"
                    ] = proj_uid
                    project_report["toolpath_report"][_toolcat_name][
                        "toolman_uid"
                    ] = proj_uid
                    project_report["toolpath_report"][_toolcat_name][
                        "remote_uid"
                    ] = None
                    continue
                # $ proj_uid found in toolman
                if data.toolman.unique_id_exists(
                    proj_uid, bitness_matters=False
                ):
                    project_report["toolpath_report"][_toolcat_name][
                        "proj_uid"
                    ] = proj_uid
                    project_report["toolpath_report"][_toolcat_name][
                        "toolman_uid"
                    ] = data.toolman.get_matching_unique_id(proj_uid)
                    if remote_toollist is not None:
                        found = False
                        for tooldict in remote_toollist:
                            if (
                                tooldict["unique_id"].lower()
                                == proj_uid.lower()
                            ):
                                project_report["toolpath_report"][
                                    _toolcat_name
                                ]["remote_uid"] = tooldict["unique_id"]
                                found = True
                                break
                        if not found:
                            for tooldict in remote_toollist:
                                if (
                                    tooldict["unique_id"].lower()[0:-4] + "_32b"
                                    == proj_uid.lower()
                                ):
                                    project_report["toolpath_report"][
                                        _toolcat_name
                                    ]["remote_uid"] = tooldict["unique_id"]
                                    break
                                if (
                                    tooldict["unique_id"].lower()[0:-4] + "_64b"
                                    == proj_uid.lower()
                                ):
                                    project_report["toolpath_report"][
                                        _toolcat_name
                                    ]["remote_uid"] = tooldict["unique_id"]
                                    break
                # $ proj_uid not found in toolman
                else:
                    project_report["toolpath_report"][_toolcat_name][
                        "proj_uid"
                    ] = proj_uid
                    project_report["toolpath_report"][_toolcat_name][
                        "toolman_uid"
                    ] = None
                    if remote_toollist is not None:
                        found = False
                        for tooldict in remote_toollist:
                            if (
                                tooldict["unique_id"].lower()
                                == proj_uid.lower()
                            ):
                                project_report["toolpath_report"][
                                    _toolcat_name
                                ]["remote_uid"] = tooldict["unique_id"]
                                break
                        if not found:
                            for tooldict in remote_toollist:
                                if (
                                    tooldict["unique_id"].lower()[0:-4] + "_32b"
                                    == proj_uid.lower()
                                ):
                                    project_report["toolpath_report"][
                                        _toolcat_name
                                    ]["remote_uid"] = tooldict["unique_id"]
                                    break
                                if (
                                    tooldict["unique_id"].lower()[0:-4] + "_64b"
                                    == proj_uid.lower()
                                ):
                                    project_report["toolpath_report"][
                                        _toolcat_name
                                    ]["remote_uid"] = tooldict["unique_id"]
                                    break
            # * Finish
            toolpath_seg = cls(
                is_fake=False,
                pathdict=pathdict,
            )
            callback(toolpath_seg, callbackArg)
            return

        # * Start
        for toolcat_name in _hardware_api_.HardwareDB().list_toolcat_unicums():
            unique_id = extract_unique_id(toolcat_name)

            # & CASE: Extracted unique_id is 'None'
            if unique_id is None:
                pathdict[toolcat_name] = None
                project_report["toolpath_report"][toolcat_name][
                    "proj_uid"
                ] = None
                continue

            # & CASE: Extracted unique_id is a string
            # $ Unique_id is builtin flash_tool
            if _fn_.fnmatch(name=unique_id, pat="*built*in*"):
                pathdict[toolcat_name] = unique_id
                project_report["toolpath_report"][toolcat_name][
                    "proj_uid"
                ] = unique_id
                continue

            # $ Extracted unique_id NOT recognized
            if not data.toolman.unique_id_exists(
                unique_id=unique_id,
                bitness_matters=False,
            ):
                # purefunctions.printc(
                #     f'WARNING: Loading Project, unique_id {q}{unique_id}{q} is not recognized\n',
                #     color='warning',
                # )
                # Very common situation (eg. starting new project for which you don't have the tools
                # yet). No need to print a warning each time.
                pathdict[toolcat_name] = None
                project_report["toolpath_report"][toolcat_name][
                    "proj_uid"
                ] = unique_id
                continue

            # $ Extracted unique_id recognized
            found_id = data.toolman.get_matching_unique_id(unique_id)
            pathdict[toolcat_name] = found_id
            project_report["toolpath_report"][toolcat_name][
                "proj_uid"
            ] = unique_id

        # * Download toollist
        # Normally only needed if problems are detected. But at this point, you don't know that yet
        # (eg. mismatch with chip/probe, ...).
        data.toolman.get_remote_beetle_toollist(
            toolcat=None,
            callback=fill_project_report,
        )
        return

    __slots__ = (
        "_pathdict_",
        "_v_rootItem",
        "__trigger_dashboard_refresh_mutex",
    )

    def __init__(
        self,
        is_fake: bool,
        pathdict: Dict[str, Optional[str]],
    ) -> None:
        """Create new ToolpathSeg()-instance, based on the given dictionary.

        Input example:
        --------------
            pathdict['FLASHTOOL'] = 'openocd_0.10.0_dev01138_32b'
                          └→ catname           └→ unique_id
        Stored as:
        ----------
            self._pathdict_['FLASHTOOL'] = <ToolpathObj()>

        Remember, the ToolpathObj() is a shell for the corresponding ToolmanObj()!
        """
        super().__init__(is_fake)

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        #! Variables
        self._pathdict_: Dict[str, Optional[_tool_obj_.ToolpathObj]] = {  # noqa
            "COMPILER_TOOLCHAIN": None,
            "BUILD_AUTOMATION": None,
            "FLASHTOOL": None,
        }
        self._pathdict_["COMPILER_TOOLCHAIN"] = _tool_obj_.ToolpathObj(
            cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"),
            unique_id=pathdict["COMPILER_TOOLCHAIN"],
            is_fake=is_fake,
        )
        self._pathdict_["BUILD_AUTOMATION"] = _tool_obj_.ToolpathObj(
            cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("BUILD_AUTOMATION"),
            unique_id=pathdict["BUILD_AUTOMATION"],
            is_fake=is_fake,
        )
        self._pathdict_["FLASHTOOL"] = _tool_obj_.ToolpathObj(
            cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("FLASHTOOL"),
            unique_id=pathdict["FLASHTOOL"],
            is_fake=is_fake,
        )

        #! History
        if not is_fake:
            self.get_history().register_getters(
                BUILD_AUTOMATION=lambda: self._pathdict_[
                    "BUILD_AUTOMATION"
                ].get_unique_id(),
                COMPILER_TOOLCHAIN=lambda: self._pathdict_[
                    "COMPILER_TOOLCHAIN"
                ].get_unique_id(),
                FLASHTOOL=lambda: self._pathdict_["FLASHTOOL"].get_unique_id(),
            )

            self.get_history().register_setters(
                BUILD_AUTOMATION=lambda p: self._pathdict_[
                    "BUILD_AUTOMATION"
                ].set_unique_id(p),
                COMPILER_TOOLCHAIN=lambda p: self._pathdict_[
                    "COMPILER_TOOLCHAIN"
                ].set_unique_id(p),
                FLASHTOOL=lambda p: self._pathdict_["FLASHTOOL"].set_unique_id(
                    p
                ),
            )

            self.get_history().register_asterisk_setters(
                BUILD_AUTOMATION=lambda a: self._pathdict_[
                    "BUILD_AUTOMATION"
                ].set_asterisk(a),
                COMPILER_TOOLCHAIN=lambda a: self._pathdict_[
                    "COMPILER_TOOLCHAIN"
                ].set_asterisk(a),
                FLASHTOOL=lambda a: self._pathdict_["FLASHTOOL"].set_asterisk(
                    a
                ),
            )
            self.get_history().register_refreshfunc(
                self.trigger_dashboard_refresh
            )

        #! Dashboard
        self._v_rootItem: Optional[_da_toolpath_items_.ToolRootItem] = None

        # Fire the signal to notify Matic's Filetree about a compiler toolchain change.
        if not is_fake:
            data.signal_dispatcher.build_automation_changed_sig.emit(
                self.get_abspath("BUILD_AUTOMATION")
            )
            data.signal_dispatcher.compiler_toolchain_changed_sig.emit(
                self.get_compiler_folderpath()
            )
            data.signal_dispatcher.flashtool_changed_sig.emit(
                self.get_abspath("FLASHTOOL")
            )
        return

    def clone(self, is_fake: bool = True) -> ToolpathSeg:
        """Clone this object.

        Method used by Intro Wizard to populate itself with fake objects.
        """
        pathdict = {
            name: toolpath_obj.get_unique_id()
            for name, toolpath_obj in self._pathdict_.items()
        }
        toolpath_seg = ToolpathSeg(
            is_fake=is_fake,
            pathdict=pathdict,
        )
        return toolpath_seg

    # ! -------------------------------------------- SHOW ON DASHBOARD ------------------------------------------------#
    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        assert not self.is_fake()
        self._v_rootItem = _da_toolpath_items_.ToolRootItem(toolpath_seg=self)

        # * Create a ToolpathItem() for each ToolpathObj()
        self._pathdict_["BUILD_AUTOMATION"].create_dashboardItem(
            rootItem=self._v_rootItem,
            parentItem=self._v_rootItem,
            toolpath_seg=self,
        )
        self._pathdict_["COMPILER_TOOLCHAIN"].create_dashboardItem(
            rootItem=self._v_rootItem,
            parentItem=self._v_rootItem,
            toolpath_seg=self,
        )
        self._pathdict_["FLASHTOOL"].create_dashboardItem(
            rootItem=self._v_rootItem,
            parentItem=self._v_rootItem,
            toolpath_seg=self,
        )

        # * Add them to the ToolRootItem()
        self._v_rootItem.add_child(
            self._pathdict_["BUILD_AUTOMATION"].get_dashboardItem(),
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        self._v_rootItem.add_child(
            self._pathdict_["COMPILER_TOOLCHAIN"].get_dashboardItem(),
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        self._v_rootItem.add_child(
            self._pathdict_["FLASHTOOL"].get_dashboardItem(),
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        data.dashboard.add_root(self._v_rootItem)
        for k, toolpath_obj in self._pathdict_.items():
            toolpath_obj.get_dashboardItem().refill_children_later(
                callback=None,
                callbackArg=None,
            )
        # Normally the registration of history functions would happen
        # right here. But I need to do it already in the constructor!
        callback(callbackArg) if callback is not None else nop()
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        categories: List[str],
        show_all: bool,
        report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the TOOLS on the Intro Wizard, inside the given vlyt.

        Only show those ToolpathObj()/ ToolpathItem()-instances that are needed.
        """
        assert self.is_fake()
        # Create a ToolpathItem() for each ToolpathObj().
        # WARNING: The preselection doesn't happen here. It happens in 'beetle_core/dashboard/items/
        # path_items/toolpath_items.py' -> sync_state()
        # Recently, I also pass the project report to that code location, to prefill the dropdown
        # correctly.

        # & BUILD_AUTOMATION
        if ("BUILD_AUTOMATION" in categories) or show_all:
            self._pathdict_["BUILD_AUTOMATION"].create_dashboardItem(
                rootItem=None,
                parentItem=None,
                toolpath_seg=self,
                report=report,
            )
            self._pathdict_[
                "BUILD_AUTOMATION"
            ].get_dashboardItem().get_layout().initialize()
            vlyt.addLayout(
                self._pathdict_["BUILD_AUTOMATION"]
                .get_dashboardItem()
                .get_layout()
            )

        # & COMPILER_TOOLCHAIN
        if ("COMPILER_TOOLCHAIN" in categories) or show_all:
            self._pathdict_["COMPILER_TOOLCHAIN"].create_dashboardItem(
                rootItem=None,
                parentItem=None,
                toolpath_seg=self,
                report=report,
            )
            self._pathdict_[
                "COMPILER_TOOLCHAIN"
            ].get_dashboardItem().get_layout().initialize()
            vlyt.addLayout(
                self._pathdict_["COMPILER_TOOLCHAIN"]
                .get_dashboardItem()
                .get_layout()
            )

        # & FLASHTOOL
        if ("FLASHTOOL" in categories) or show_all:
            self._pathdict_["FLASHTOOL"].create_dashboardItem(
                rootItem=None,
                parentItem=None,
                toolpath_seg=self,
                report=report,
            )
            self._pathdict_[
                "FLASHTOOL"
            ].get_dashboardItem().get_layout().initialize()
            vlyt.addLayout(
                self._pathdict_["FLASHTOOL"].get_dashboardItem().get_layout()
            )
        if callback is not None:
            callback(callbackArg)
        return

    def get_impacted_files(self) -> List[str]:
        """"""
        impacted_files = []

        # & BUILD_AUTOMATION
        if self._pathdict_["BUILD_AUTOMATION"].has_asterisk():
            pass

        # & COMPILER_TOOLCHAIN
        if self._pathdict_["COMPILER_TOOLCHAIN"].has_asterisk():
            impacted_files.append("DASHBOARD_MK")

        # & FLASHTOOL
        if self._pathdict_["FLASHTOOL"].has_asterisk():
            impacted_files.append("DASHBOARD_MK")
            impacted_files.append("GDB_FLASHFILE")
            impacted_files.append("OPENOCD_CHIPFILE")
            impacted_files.append("OPENOCD_PROBEFILE")

        return impacted_files

    def update_states(
        self,  # type: ignore[override]
        withgui: bool = True,
        chip: Optional[_chip_.Chip] = None,
        probe: Optional[_probe_.Probe] = None,
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Update the states of all ToolpathObj()-instances stored in
        'self._pathdict_'.

        NOTE:
        Before, this method was intended to update the states of the corresponding dashboard
        ToolpathItem()-instances, but that required the GUI to be up and running. Therefore, the
        ToolpathItem()-instances now sync their own states in their sync_state() methods (pulling
        the states from the corresponding ToolpathObj()s).

        :param withgui: [Optional] GUI exists

        :param chip:    [Optional] Chip()-instance, only for polling, to check if toolchain is com-
                        patible.

        :param probe:   [Optional] Probe()-instance, only for polling, to check if flashtool is com-
                        patible.

        :param project_report: [Optional] Report to be filled if given.

        WARNING:
        Most elements of the 'project_report' are not assigned here, but in the load() function.
        """
        projObj = data.current_project
        is_fake: bool = self.is_fake()
        if chip is None:
            if is_fake:
                chip = projObj.intro_wiz.get_fake_chip()
            else:
                chip = projObj.get_chip()
        if probe is None:
            if is_fake:
                probe = projObj.intro_wiz.get_fake_probe()
            else:
                probe = projObj.get_probe()

        # For each category:
        #   - check if tool exists
        #   - check if tool uid is defined
        #   - check compatibility
        compiler_toolchain_err: bool = False
        build_automation_err: bool = False
        flashtool_err: bool = False

        # & COMPILER_TOOLCHAIN
        compiler_toolchain_abspath = self.get_abspath("COMPILER_TOOLCHAIN")
        compiler_toolchain_uid = self.get_unique_id("COMPILER_TOOLCHAIN")
        if (
            (compiler_toolchain_abspath is None)
            or (compiler_toolchain_abspath.lower() == "none")
            or (not os.path.exists(compiler_toolchain_abspath))
        ):
            compiler_toolchain_err = True
        else:
            # Check if uid is defined
            if (compiler_toolchain_uid is None) or (
                compiler_toolchain_uid.lower() == "none"
            ):
                compiler_toolchain_err = True
            else:
                # Check compatibility
                if (chip is None) or (chip.get_name().lower() == "none"):
                    pass
                elif chip.is_compatible_with_compiler_uid(
                    compiler_toolchain_uid
                ):
                    pass
                else:
                    compiler_toolchain_err = True

        if compiler_toolchain_err:
            self.set_error("COMPILER_TOOLCHAIN", True)
            if project_report is not None:
                project_report["toolpath_report"]["COMPILER_TOOLCHAIN"][
                    "error"
                ] = True
        else:
            self.set_error("COMPILER_TOOLCHAIN", False)

        # & BUILD_AUTOMATION
        build_automation_abspath = self.get_abspath("BUILD_AUTOMATION")
        build_automation_uid = self.get_unique_id("BUILD_AUTOMATION")
        if (
            (build_automation_abspath is None)
            or (build_automation_abspath.lower() == "none")
            or (not os.path.exists(build_automation_abspath))
        ):
            build_automation_err = True
        else:
            # Check if uid is defined
            if (build_automation_uid is None) or (
                build_automation_uid.lower() == "none"
            ):
                build_automation_err = True
            else:
                # Check compatibility
                pass

        if build_automation_err:
            self.set_error("BUILD_AUTOMATION", True)
            if project_report is not None:
                project_report["toolpath_report"]["BUILD_AUTOMATION"][
                    "error"
                ] = True
        else:
            self.set_error("BUILD_AUTOMATION", False)

        # & FLASHTOOL
        flash_tool_abspath = self.get_abspath("FLASHTOOL")
        flash_tool_unique_id = self.get_unique_id("FLASHTOOL")
        if (
            (flash_tool_abspath is None)
            or (flash_tool_abspath.lower() == "none")
            or (not os.path.exists(flash_tool_abspath))
        ):
            if (flash_tool_unique_id is None) or (
                flash_tool_unique_id.lower() == "none"
            ):
                flashtool_err = True
            elif _fn_.fnmatch(
                name=flash_tool_unique_id.lower(), pat="*built*in*"
            ):
                pass
            else:
                flashtool_err = True
        else:
            # Check if uid is defined
            if (flash_tool_unique_id is None) or (
                flash_tool_unique_id.lower() == "none"
            ):
                flashtool_err = True
            else:
                # Check probe compatibility
                if (probe is None) or (probe.get_name().lower() == "none"):
                    pass
                elif probe.is_compatible(flash_tool_unique_id):
                    pass
                else:
                    flashtool_err = True
                # Check chip compatibility
                if (chip is None) or (chip.get_name().lower() == "none"):
                    pass
                elif chip.is_compatible_with_flashtool(flash_tool_unique_id):
                    pass
                else:
                    flashtool_err = True

        if flashtool_err:
            self.set_error("FLASHTOOL", True)
            if project_report is not None:
                project_report["toolpath_report"]["FLASHTOOL"]["error"] = True
        else:
            self.set_error("FLASHTOOL", False)

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
        - update states of related segments (chip and probe)
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
        probe: Optional[_probe_.Probe] = None
        chip: Optional[_chip_.Chip] = None
        if is_fake:
            probe = data.current_project.intro_wiz.get_fake_probe()
            chip = data.current_project.intro_wiz.get_fake_chip()
        else:
            probe = data.current_project.get_probe()
            chip = data.current_project.get_chip()

        def update_probe_states(*args) -> None:
            probe.update_states(
                callback=update_chip_states,
                callbackArg=None,
            )
            return

        def update_chip_states(*args) -> None:
            chip.update_states(
                callback=start_refresh,
                callbackArg=None,
            )
            return

        def start_refresh(*args) -> None:
            # & Dashboard
            if not is_fake:
                if (self._v_rootItem is None) or (
                    self._v_rootItem._v_emitter is None
                ):
                    finish()
                    return
                self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                    True,
                    False,
                    check_unsaved_changes_dashboard,
                    None,
                )
                return

            # & Intro Wizard
            assert is_fake
            cat_iter = iter(list(self._pathdict_.keys()))
            refresh_next_toolpath_item(cat_iter)
            return

        def check_unsaved_changes_dashboard(*args) -> None:
            "[dashboard only]"
            assert not is_fake
            data.dashboard.check_unsaved_changes()
            finish()
            return

        def refresh_next_toolpath_item(cat_iter: Iterator[str]) -> None:
            "[intro wiz only]"
            assert is_fake
            # For intro wiz items, it's not sure they exist.
            try:
                toolcat: str = next(cat_iter)
            except StopIteration:
                finish()
                return
            toolpath_obj: _tool_obj_.ToolpathObj = self._pathdict_[toolcat]
            if toolpath_obj is None:
                purefunctions.printc(
                    f"WARNING: No ToolpathObj() for {toolcat}",
                    color="warning",
                )
                refresh_next_toolpath_item(cat_iter)
                return
            toolpath_item: Optional[_da_toolpath_items_.ToolpathItem] = (
                toolpath_obj.get_dashboardItem()
            )
            if (toolpath_item is None) or (toolpath_item._v_emitter is None):
                refresh_next_toolpath_item(cat_iter)
                return
            toolpath_item._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                refresh_next_toolpath_item,
                cat_iter,
            )
            return

        def finish(*args) -> None:
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        self.update_states(
            callback=update_probe_states,
            callbackArg=None,
        )
        return

    def set_error(self, cat_name: str, error: bool) -> None:
        """"""
        if cat_name == "COMPILER_TOOLCHAIN":
            self._pathdict_["COMPILER_TOOLCHAIN"].set_error(error)
        elif cat_name == "BUILD_AUTOMATION":
            self._pathdict_["BUILD_AUTOMATION"].set_error(error)
        elif cat_name == "FLASHTOOL":
            self._pathdict_["FLASHTOOL"].set_error(error)
        else:
            assert False
        return

    def set_warning(self, cat_name: str, warning: bool) -> None:
        """"""
        if cat_name == "COMPILER_TOOLCHAIN":
            self._pathdict_["COMPILER_TOOLCHAIN"].set_warning(warning)
        elif cat_name == "BUILD_AUTOMATION":
            self._pathdict_["BUILD_AUTOMATION"].set_warning(warning)
        elif cat_name == "FLASHTOOL":
            self._pathdict_["FLASHTOOL"].set_warning(warning)
        else:
            assert False
        return

    # ! ------------------------------------------ GETTERS AND SETTERS ------------------------------------------------#
    """
    IMPORTANT NOTE:
        The ToolpathObj() is never None. However, the
        matching ToolmanObj() can be None because:
          - unique_id is None
          - unique_id is not found
        In such case, all getters on the ToolpathObj()
        simply return None.
    
    """

    def get_relpath(self, cat_name: str) -> str:  # type: ignore[override]
        """"""
        raise NotImplementedError()

    def get_abspath(self, cat_name: str) -> str:  # type: ignore[override]
        """"""
        obj = self.get_toolpathObj(cat_name)
        return obj.get_abspath()

    def get_unique_id(self, cat_name: str) -> str:
        """"""
        obj = self.get_toolpathObj(cat_name)
        return obj.get_unique_id()

    def change_unique_id(
        self,
        cat_name: str,
        unique_id: str,
        history: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Change unique_id in ToolpathObj() for given category.

        Also refresh the corresponding dash- board item. Afterwards, refresh the
        whole dashboard to allow error- and warning-signs to propagate.
        """
        is_fake = self.is_fake()
        treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None
        probe: Optional[_probe_.Probe] = None
        if is_fake:
            treepath_seg = (
                data.current_project.intro_wiz.get_fake_treepath_seg()
            )
            probe = data.current_project.intro_wiz.get_fake_probe()
        else:
            treepath_seg = data.current_project.get_treepath_seg()
            probe = data.current_project.get_probe()

        def refresh_toolpath_item(arg: Tuple[str, str]) -> None:
            "Refresh the dashboard item"
            _new_unique_id, _old_unique_id = arg
            _toolpath_obj = self.get_toolpathObj(cat_name)
            toolpath_item: Optional[_da_toolpath_items_.ToolpathItem] = (
                _toolpath_obj.get_dashboardItem()
            )
            if toolpath_item is None:
                refresh_whole_dashboard()
                return
            assert isinstance(
                toolpath_item,
                _da_toolpath_items_.ToolpathItem,
            )
            was_open = toolpath_item.get_state().open
            # 'refresh_children' will be set to True if the childlist (with info
            # items) needs refreshment, eg. if children need to be removed or
            # added.
            refresh_children = False
            if cat_name.lower() == "flash_tool":
                if _new_unique_id is not None:
                    if _fn_.fnmatch(
                        name=_new_unique_id.lower(), pat="*built*in*"
                    ) or _fn_.fnmatch(
                        name=_old_unique_id.lower(), pat="*built*in*"
                    ):
                        refresh_children = True
            if len(toolpath_item.get_childlist()) == 0:
                refresh_children = True

            def kill_children(*args) -> None:
                toolpath_item.kill_children_later(
                    callback=refill_children,
                    callbackArg=None,
                )
                return

            def refill_children(*args) -> None:
                toolpath_item.refill_children_later(
                    callback=refill_finish,
                    callbackArg=None,
                )
                return

            def refill_finish(*args) -> None:
                if was_open and (toolpath_item.get_state().open == False):
                    toolpath_item.open_later(
                        click=False,
                        callback=refresh_whole_dashboard,
                        callbackArg=None,
                    )
                    return
                refresh_whole_dashboard()
                return

            if refresh_children:
                kill_children()
                return
            refresh_whole_dashboard()
            return

        def refresh_whole_dashboard(*args) -> None:
            "Refresh everything in the Dashboard or Intro Wizard"

            # Remember: 'trigger_dashboard_refresh()' also applies on the Intro Wizard.
            def refresh_treepaths(*_args) -> None:
                treepath_seg.trigger_dashboard_refresh(
                    callback=refresh_toolpaths,
                    callbackArg=None,
                )
                return

            def refresh_toolpaths(*_args) -> None:
                # PROBLEM: this function never goes to finish!
                self.trigger_dashboard_refresh(
                    callback=finish,
                    callbackArg=None,
                )
                return

            # * Refresh probe
            probe.trigger_dashboard_refresh(
                callback=refresh_treepaths,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            "Complete toolchange"
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # Apply the new unique_id on the toolpathObj
        # $ Sanitize input
        new_unique_id = unique_id
        old_unique_id = self.get_unique_id(cat_name)
        if (new_unique_id is None) or (new_unique_id.lower() == "none"):
            new_unique_id = "None"
        if (old_unique_id is None) or (old_unique_id.lower() == "none"):
            old_unique_id = "None"
        assert (
            (cat_name == "COMPILER_TOOLCHAIN")
            or (cat_name == "BUILD_AUTOMATION")
            or (cat_name == "FLASHTOOL")
        ), f"category name {q}{cat_name}{q} not recognized"

        # $ Check if change is needed
        if new_unique_id == old_unique_id:
            finish()
            return

        # $ Perform the 'unique_id' change
        if (not is_fake) and history:
            self.get_history().push()
        self.get_toolpathObj(cat_name).set_unique_id(new_unique_id)

        # $ Stop clang engine if needed
        # Policy change: clang engine is not touched until after a dashboard save has applied the
        # change.

        # $ Compare history
        if (not is_fake) and history:
            self.get_history().compare_to_baseline(
                refresh=False,
                callback=refresh_toolpath_item,
                callbackArg=(new_unique_id, old_unique_id),
            )
            return
        refresh_toolpath_item(arg=(new_unique_id, old_unique_id))
        return

    def get_toolpathObj(self, cat_name: str) -> _tool_obj_.ToolpathObj:
        """"""
        if isinstance(cat_name, str):
            return self._pathdict_[cat_name]
        assert False

    # ! DERIVED PATHS  !
    # ! -------------- !
    def get_compiler_abspath(self) -> Optional[str]:
        """"""
        dirpath_or_exepath = self.get_abspath("COMPILER_TOOLCHAIN")
        if (dirpath_or_exepath is None) or (
            dirpath_or_exepath.lower() == "none"
        ):
            return None
        if os.path.isfile(dirpath_or_exepath):
            return dirpath_or_exepath
        elif os.path.isdir(dirpath_or_exepath):
            exepath = data.toolversion_extractor.extract_executable(
                dirpath_or_exepath
            )[1]
            return exepath
        purefunctions.printc(
            f"WARNING: The {q}abspath{q} saved in ToolpathObj() for the "
            f"compiler is {q}{dirpath_or_exepath}{q}. It is not recognized as "
            f"a file or directory. Could it be the toolchain prefix?",
            color="warning",
        )
        return None

    def get_compiler_toolchain_prefix(
        self, absolute: bool = True
    ) -> Optional[str]:
        """"""
        toolchain_prefix = self._pathdict_["COMPILER_TOOLCHAIN"].get_toolprefix(
            absolute
        )
        if (toolchain_prefix is not None) and (not absolute):
            assert "/" not in toolchain_prefix
        if (toolchain_prefix is None) or (toolchain_prefix.lower() == "none"):
            return None
        if os.path.isfile(toolchain_prefix):
            purefunctions.printc(
                f"\nWARNING: The toolchain prefix is registered as: "
                f"{q}{toolchain_prefix}{q}\n"
                f"This is a file!",
                color="warning",
            )
            return None
        return toolchain_prefix

    def get_compiler_folderpath(self) -> Optional[str]:
        """Return the toplevel folder of the toolchain.

        Return None if no toolchain was selected.
        """
        toolchain_abspath = self._pathdict_["COMPILER_TOOLCHAIN"].get_abspath()
        if (toolchain_abspath is None) or (toolchain_abspath.lower() == "none"):
            return None
        if os.path.isfile(toolchain_abspath):
            toolchain_abspath = os.path.dirname(toolchain_abspath).replace(
                "\\", "/"
            )
        if any(toolchain_abspath.endswith(s) for s in ("bin", "bin/")):
            toolchain_abspath = os.path.dirname(toolchain_abspath)
        toolchain_abspath = _pp_.standardize_abspath(toolchain_abspath)
        return toolchain_abspath

    def get_gdb_abspath(self) -> Optional[str]:
        """"""
        compiler_toolchain = self.get_abspath("COMPILER_TOOLCHAIN")
        if (compiler_toolchain is None) or (
            compiler_toolchain.lower() == "none"
        ):
            return None
        gdb_abspath = data.toolversion_extractor.extract_executable(
            dirpath=compiler_toolchain,
            exename="gdb",
        )[1]
        return gdb_abspath

    def get_openocd_scriptspath(self) -> Optional[str]:
        """"""
        openocd_abspath = self.get_abspath("FLASHTOOL")
        if openocd_abspath is None:
            return None
        if "openocd" not in openocd_abspath:
            return None
        if "bin/" in openocd_abspath:
            scripts_abspath = (
                _pp_.standardize_abspath(
                    os.path.dirname(os.path.dirname(openocd_abspath))
                )
                + "/scripts"
            )
        else:
            scripts_abspath = (
                _pp_.standardize_abspath(os.path.dirname(openocd_abspath))
                + "/scripts"
            )
        return scripts_abspath

    # ! OTHER FUNCTIONS  !
    # ! ---------------- !
    def check_if_in_compiler(self, file_abspath: str) -> bool:
        """Check if the given file is located within the compiler."""
        toolchain_abspath = self.get_compiler_folderpath()
        if (toolchain_abspath is None) or (toolchain_abspath.lower() == "none"):
            return False
        file_abspath = _pp_.standardize_abspath(file_abspath)
        if file_abspath.lower().startswith(toolchain_abspath.lower()):
            return True
        return False

    def get_categories(self) -> List[str]:
        """"""
        return [k for k in self._pathdict_.keys()]

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        super().printout(nr)
        lines = [
            f"# {nr}. Tools ",
        ]
        for k, v in self._pathdict_.items():
            lines.append(f"{k.ljust(20)} = {q}{v.get_unique_id()}{q}")
        lines.append("")
        return "\n".join(lines)

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this ToolpathSeg()-instance and *all* its representations in the
        Dashboard or Intro Wizard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill ToolpathSeg() twice!")
            self.dead = True

        def start(*args) -> None:
            # $ Dashboard
            if not self.is_fake():
                if self._v_rootItem:
                    self._v_rootItem.self_destruct(
                        killParentLink=False,
                        callback=start_killing_toolpath_objs,
                        callbackArg=None,
                    )
                    return
                start_killing_toolpath_objs()
                return
            # $ Intro Wizard
            start_killing_toolpath_objs()
            return

        def start_killing_toolpath_objs(*args) -> None:
            kill_next_toolpath_obj(iter(list(self._pathdict_.keys())))
            return

        def kill_next_toolpath_obj(name_iter: Iterator[str]) -> None:
            # This function kills one ToolpathObj() from the 'self._pathdict_'
            # dictionary. If the given ToolpathObj() has no more GUI-elements
            # (eg. after self._v_rootItem has been destroyed), their non-GUI
            # elements will be deleted.
            try:
                name = next(name_iter)
            except StopIteration:
                finish()
                return
            toolpath_obj: _tool_obj_.ToolpathObj = self._pathdict_[name]
            toolpath_obj.self_destruct(
                callback=kill_next_toolpath_obj,
                callbackArg=name_iter,
            )
            return

        def finish(*args) -> None:
            self._v_rootItem = None
            self._pathdict_ = None
            if callback is not None:
                callback(callbackArg)
            return

        super().self_destruct(
            callback=start,
            callbackArg=None,
            death_already_checked=True,
        )
        return
