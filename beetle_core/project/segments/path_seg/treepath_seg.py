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
import threading, os, functools, weakref
import qt, data, functions, purefunctions
import dashboard.items.path_items.treepath_items as _treepath_items_
import project.segments.path_seg.path_seg as _ps_
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import hardware_api.treepath_unicum as _treepath_unicum_
import bpathlib.treepath_obj as _treepath_obj_
import hardware_api.file_generator as _file_generator_
import hardware_api.hardware_api as _hardware_api_
import hardware_api.toolcat_unicum as _toolcat_unicum_

if TYPE_CHECKING:
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
    import project.segments.probe_seg.probe as _probe_
from various.kristofstuff import *

"""
                              ┌────────────────────┐
                              │     PathSeg()      │
                              └────────────────────┘
             ┌──────────────────────────┴─────────────────────────┐
             ↓                                                    ↓
    ╔════════════════════╗                              ┌────────────────────┐
    ║   TreepathSeg()    ║                              │   ToolpathSeg()    │
    ╚════════════════════╝                              └────────────────────┘
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - ...                                                - ...

    Each:                                               Each:
      -> encapsulates a TREEPATH_UNIC() Unicum            -> is a shell for the corresponding ToolmanObj()
      -> holds one TreepathItem() for dashboard           -> holds one ToolpathItem() for dashboard

"""


class TreepathSeg(_ps_.PathSeg):
    @classmethod
    def create_default_TreepathSeg(cls, rootdir_abspath: str) -> TreepathSeg:
        """Create default TreepathSeg()-instance, based on the default paths."""
        pathdict = {}
        for obj in _hardware_api_.HardwareDB().list_treepath_unicums(True):
            assert isinstance(obj, _treepath_unicum_.TREEPATH_UNIC)
            pathdict[obj.get_name()] = f"<project>/{obj.get_default_relpath()}"
        return cls(
            is_fake=False,
            pathdict=pathdict,
        )

    @classmethod
    def create_empty_TreepathSeg(cls, proj_rootpath: str) -> TreepathSeg:
        """Create default TreepathSeg()-instance, based on the default paths."""
        pathdict: Dict[str, Optional[str]] = {}
        for obj in _hardware_api_.HardwareDB().list_treepath_unicums(True):
            assert isinstance(obj, _treepath_unicum_.TREEPATH_UNIC)
            pathdict[obj.get_name()] = None
        return cls(
            is_fake=False,
            pathdict=pathdict,
        )

    @classmethod
    def load(
        cls,
        configcode: Dict[str, str],
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load TreepathSeg()-instance from the given configscript.

        Note: The project_report is not returned, but simply modified here.
        """
        pathdict: Dict[str, Optional[str]] = {}
        for unicum_name in _hardware_api_.HardwareDB().list_treepath_unicums():
            # $ Ignore some Unicum()s
            if unicum_name in (
                "FILETREE_MK",
                "DASHBOARD_MK",
                "BUTTONS_BTL",
            ):
                # These Unicum()s get a special treatment in the TreepathSeg() constructor.
                continue

            # $ Retrieve stored value
            value: Optional[str] = None
            try:
                value = configcode[unicum_name]
            except:
                value = None
            if value is None:
                pathdict[unicum_name] = None
            elif value.lower() in ("none", "null"):
                pathdict[unicum_name] = None
            else:
                if value.startswith("<"):
                    pathdict[unicum_name] = value
                else:
                    purefunctions.printc(
                        "WARNING: Old style project layout value does not define rootid\n",
                        color="warning",
                    )
                    value = "<project>/" + value
                pathdict[unicum_name] = value
            continue

        treepath_seg = cls(
            is_fake=False,
            pathdict=pathdict,
        )
        callback(treepath_seg, callbackArg)
        return

    __slots__ = (
        "_v_intro_wiz_vlyt_ref",
        "_pathdict_",
        "__trigger_dashboard_refresh_mutex",
        "_v_rootItem",
    )

    def __init__(
        self,
        is_fake: bool,
        pathdict: Dict[str, Optional[str]],
    ) -> None:
        """Create new TreepathSeg()-instance, based on the given dictionary.

        NOTE:
        'filetree.mk' and 'dashboard.mk' are given a special treatment to ensure that they are al-
        ways next to the makefile!
        """
        super().__init__(is_fake)
        # Store a weak reference to the vlyt from the Intro Wizard where all 'dashboard' items are
        # displayed. Will only happen if this TreepathSeg() is a fake one.
        self._v_intro_wiz_vlyt_ref: Optional[
            weakref.ReferenceType[qt.QVBoxLayout]
        ] = None

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        #! Fill self._pathdict_
        self._pathdict_: Dict[str, _treepath_obj_.TreepathObj] = {}

        for unicum in _hardware_api_.HardwareDB().list_treepath_unicums(True):
            assert isinstance(unicum, _treepath_unicum_.TREEPATH_UNIC)
            unicum_name: str = unicum.get_name()
            # & Beetle files
            # The .btl files should NOT be extracted from the 'pathdict' parameter. Instead, they
            # get their values from the unicum's default.
            if unicum_name in ("BUTTONS_BTL",):
                self._pathdict_[unicum_name] = _treepath_obj_.TreepathObj(
                    unicum=unicum,
                    root_id="<project>",
                    relpath=unicum.get_default_relpath(),
                    fake=is_fake,
                )
                continue

            # & 'filetree.mk' and 'dashboard.mk'
            # The 'filetree.mk' and 'dashboard.mk' files get a special treatment. They get their
            # values from the makefile location.
            if unicum_name in (
                "FILETREE_MK",
                "DASHBOARD_MK",
            ):
                prefixed_makefile_relpath: Optional[str] = pathdict.get(
                    "MAKEFILE"
                )
                makefile_rootid: Optional[str] = "<project>"
                makefile_relpath: Optional[str] = None
                unicum_relpath: Optional[str] = None
                # $ Makefile not located
                if (prefixed_makefile_relpath is None) or (
                    prefixed_makefile_relpath.lower() == "none"
                ):
                    unicum_relpath = None
                else:
                    makefile_rootid, makefile_relpath = (
                        purefunctions.strip_rootid(prefixed_makefile_relpath)
                    )
                    # $ Makefile located in subfolder
                    if "/" in makefile_relpath:
                        makefile_dir_relpath = os.path.dirname(
                            makefile_relpath
                        ).replace("\\", "/")
                        unicum_relpath = os.path.join(
                            makefile_dir_relpath,
                            unicum_name.lower().replace("_", "."),
                        ).replace("\\", "/")
                    # $ Makefile located toplevel
                    else:
                        unicum_relpath = unicum_name.lower().replace("_", ".")
                # Create the TreepathObj()
                self._pathdict_[unicum_name] = _treepath_obj_.TreepathObj(
                    unicum=unicum,
                    root_id=makefile_rootid,
                    relpath=unicum_relpath,
                    fake=is_fake,
                )
                continue

            # & General
            # All other files.
            prefixed_relpath: Optional[str] = pathdict.get(unicum_name)
            relpath: Optional[str] = None
            rootid: Optional[str] = "<project>"
            if (prefixed_relpath is None) or (
                prefixed_relpath.lower() == "none"
            ):
                relpath = None
            else:
                rootid, relpath = purefunctions.strip_rootid(prefixed_relpath)
            self._pathdict_[unicum_name] = _treepath_obj_.TreepathObj(
                unicum=unicum,
                root_id=rootid,
                relpath=relpath,
                fake=is_fake,
            )
            continue

        #! History
        if not is_fake:
            self.get_history().register_getters(
                BUILD_DIR=lambda: self._pathdict_["BUILD_DIR"].get_doublepath(),
                BIN_FILE=lambda: self._pathdict_["BIN_FILE"].get_doublepath(),
                ELF_FILE=lambda: self._pathdict_["ELF_FILE"].get_doublepath(),
                BOOTLOADER_FILE=lambda: self._pathdict_[
                    "BOOTLOADER_FILE"
                ].get_doublepath(),
                BOOTSWITCH_FILE=lambda: self._pathdict_[
                    "BOOTSWITCH_FILE"
                ].get_doublepath(),
                PARTITIONS_CSV_FILE=lambda: self._pathdict_[
                    "PARTITIONS_CSV_FILE"
                ].get_doublepath(),
                LINKERSCRIPT=lambda: self._pathdict_[
                    "LINKERSCRIPT"
                ].get_doublepath(),
                MAKEFILE=lambda: self._pathdict_["MAKEFILE"].get_doublepath(),
                DASHBOARD_MK=lambda: self._pathdict_[
                    "DASHBOARD_MK"
                ].get_doublepath(),
                FILETREE_MK=lambda: self._pathdict_[
                    "FILETREE_MK"
                ].get_doublepath(),
                GDB_FLASHFILE=lambda: self._pathdict_[
                    "GDB_FLASHFILE"
                ].get_doublepath(),
                OPENOCD_CHIPFILE=lambda: self._pathdict_[
                    "OPENOCD_CHIPFILE"
                ].get_doublepath(),
                OPENOCD_PROBEFILE=lambda: self._pathdict_[
                    "OPENOCD_PROBEFILE"
                ].get_doublepath(),
                PACKPATH=lambda: self._pathdict_["PACKPATH"].get_doublepath(),
                BUTTONS_BTL=lambda: self._pathdict_[
                    "BUTTONS_BTL"
                ].get_doublepath(),
            )
            self.get_history().register_setters(
                BUILD_DIR=lambda p: self._pathdict_["BUILD_DIR"].set_doublepath(
                    p
                ),
                BIN_FILE=lambda p: self._pathdict_["BIN_FILE"].set_doublepath(
                    p
                ),
                ELF_FILE=lambda p: self._pathdict_["ELF_FILE"].set_doublepath(
                    p
                ),
                BOOTLOADER_FILE=lambda p: self._pathdict_[
                    "BOOTLOADER_FILE"
                ].set_doublepath(p),
                BOOTSWITCH_FILE=lambda p: self._pathdict_[
                    "BOOTSWITCH_FILE"
                ].set_doublepath(p),
                PARTITIONS_CSV_FILE=lambda p: self._pathdict_[
                    "PARTITIONS_CSV_FILE"
                ].set_doublepath(p),
                LINKERSCRIPT=lambda p: self._pathdict_[
                    "LINKERSCRIPT"
                ].set_doublepath(p),
                MAKEFILE=lambda p: self._pathdict_["MAKEFILE"].set_doublepath(
                    p
                ),
                DASHBOARD_MK=lambda p: self._pathdict_[
                    "DASHBOARD_MK"
                ].set_doublepath(p),
                FILETREE_MK=lambda p: self._pathdict_[
                    "FILETREE_MK"
                ].set_doublepath(p),
                GDB_FLASHFILE=lambda p: self._pathdict_[
                    "GDB_FLASHFILE"
                ].set_doublepath(p),
                OPENOCD_CHIPFILE=lambda p: self._pathdict_[
                    "OPENOCD_CHIPFILE"
                ].set_doublepath(p),
                OPENOCD_PROBEFILE=lambda p: self._pathdict_[
                    "OPENOCD_PROBEFILE"
                ].set_doublepath(p),
                PACKPATH=lambda p: self._pathdict_["PACKPATH"].set_doublepath(
                    p
                ),
                BUTTONS_BTL=lambda p: self._pathdict_[
                    "BUTTONS_BTL"
                ].set_doublepath(p),
            )
            self.get_history().register_asterisk_setters(
                BUILD_DIR=lambda a: self._pathdict_["BUILD_DIR"].set_asterisk(
                    a
                ),
                BIN_FILE=lambda a: self._pathdict_["BIN_FILE"].set_asterisk(a),
                ELF_FILE=lambda a: self._pathdict_["ELF_FILE"].set_asterisk(a),
                BOOTLOADER_FILE=lambda a: self._pathdict_[
                    "BOOTLOADER_FILE"
                ].set_asterisk(a),
                BOOTSWITCH_FILE=lambda a: self._pathdict_[
                    "BOOTSWITCH_FILE"
                ].set_asterisk(a),
                PARTITIONS_CSV_FILE=lambda a: self._pathdict_[
                    "PARTITIONS_CSV_FILE"
                ].set_asterisk(a),
                LINKERSCRIPT=lambda a: self._pathdict_[
                    "LINKERSCRIPT"
                ].set_asterisk(a),
                MAKEFILE=lambda a: self._pathdict_["MAKEFILE"].set_asterisk(a),
                DASHBOARD_MK=lambda a: self._pathdict_[
                    "DASHBOARD_MK"
                ].set_asterisk(a),
                FILETREE_MK=lambda a: self._pathdict_[
                    "FILETREE_MK"
                ].set_asterisk(a),
                GDB_FLASHFILE=lambda a: self._pathdict_[
                    "GDB_FLASHFILE"
                ].set_asterisk(a),
                OPENOCD_CHIPFILE=lambda a: self._pathdict_[
                    "OPENOCD_CHIPFILE"
                ].set_asterisk(a),
                OPENOCD_PROBEFILE=lambda a: self._pathdict_[
                    "OPENOCD_PROBEFILE"
                ].set_asterisk(a),
                PACKPATH=lambda a: self._pathdict_["PACKPATH"].set_asterisk(a),
                BUTTONS_BTL=lambda a: self._pathdict_[
                    "BUTTONS_BTL"
                ].set_asterisk(a),
            )
            self.get_history().register_refreshfunc(
                self.trigger_dashboard_refresh
            )

        #! Dashboard
        self._v_rootItem: Optional[_treepath_items_.TreepathRootItem] = None
        return

    def clone(self, is_fake: bool = True) -> TreepathSeg:
        """Clone this object.

        Method used by Intro Wizard to populate itself with fake objects.
        """
        pathdict = {
            name: f"{treepathObj.get_rootid()}/{treepathObj.get_relpath()}"
            for name, treepathObj in self._pathdict_.items()
        }
        cloned_treepath_seg = TreepathSeg(
            is_fake=is_fake,
            pathdict=pathdict,
        )
        return cloned_treepath_seg

    def __create_dashboard_mk_if_needed(self, *args) -> None:
        """Create 'dashboard.mk' next to the makefile if it isn't there yet.

        This function gets called:
        > At the end of the Project() constructor (but not anymore)
        > In self.update_states()
        """
        assert not self.is_fake()
        makefile_abspath: Optional[str] = self.get_abspath("MAKEFILE")
        dashboard_mk_abspath: Optional[str] = None

        # * Figure out if it's needed
        if (
            (makefile_abspath is None)
            or (makefile_abspath.lower() == "none")
            or (not os.path.isfile(makefile_abspath))
        ):
            # The makefile is not located or not present. There's no point in
            # generating a 'dashboard.mk'.
            return

        # Obtain the absolute path where 'dashboard.mk' *should* be located.
        # Also make sure that the corresponding PathObj() points to that path.
        # Then figure out if there is already a file present there.
        dashboard_mk_abspath = _pp_.rel_to_abs(
            rootpath=os.path.dirname(makefile_abspath).replace("\\", "/"),
            relpath="dashboard.mk",
        )
        if self.get_abspath("DASHBOARD_MK") != dashboard_mk_abspath:
            self.set_abspath(
                unicum="DASHBOARD_MK",
                abspath=dashboard_mk_abspath,
                history=True,
                refresh=False,
                callback=None,
                callbackArg=None,
            )
        if os.path.isfile(dashboard_mk_abspath):
            # The 'dashboard.mk' file already exists at the expected location!
            # No need to generate one anymore.
            return

        # * Generate 'dashboard.mk'
        # At this point, we know the desired location for 'dashboard.mk' and
        # that one should be generated.
        print(
            f"\nCreating DASHBOARD.MK on the fly: "
            f"{q}{dashboard_mk_abspath}{q}\n"
        )
        text = _file_generator_.get_new_dashboard_mk(
            proj_rootpath=data.current_project.get_proj_rootpath(),
            boardname=data.current_project.get_board().get_name(),
            chipname=data.current_project.get_chip().get_name(),
            probename=data.current_project.get_probe().get_name(),
            toolprefix=data.current_project.get_toolpath_seg().get_compiler_toolchain_prefix(
                absolute=False
            ),
            flashtool_exename=_toolcat_unicum_.TOOLCAT_UNIC(
                "FLASHTOOL"
            ).get_flashtool_exename(
                unique_id=data.current_project.get_toolpath_seg().get_unique_id(
                    "FLASHTOOL"
                )
            ),
            filepaths={
                u: self.get_abspath(u) if self.is_relevant(u) else None
                for u in self.get_treepath_unicum_names()
                if u
                not in (
                    "BUTTONS_BTL",
                    "MAKEFILE",
                    "DASHBOARD_MK",
                    "FILETREE_MK",
                )
            },
            repoints=None,
            version=data.current_project.get_version_seg().get_version_nr(),
        )
        _fp_.make_file(dashboard_mk_abspath)
        with open(
            dashboard_mk_abspath, "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(text)
        return

    def register_history_funcs(self) -> None:
        """"""
        assert not self.is_fake()

    # ^                                      DASHBOARD & INTRO WIZ                                     ^#
    # % ============================================================================================== %#
    # % Methods to show all (relevant) TreepathObj()s on the Dashboard or Intro Wizard through their   %#
    # % TreepathItem().                                                                                %#
    # %                                                                                                %#

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the PROJECT LAYOUT on the dashboard.

        NOTE: Irrelevant ones are not shown anymore.
        """
        assert not self.is_fake()
        self._v_rootItem = _treepath_items_.TreepathRootItem(
            treepath_seg=self,
        )
        data.dashboard.add_root(self._v_rootItem)

        def show_next_entry(
            treepath_obj_iter: Iterator[_treepath_obj_.TreepathObj],
        ) -> None:
            try:
                treepath_obj: _treepath_obj_.TreepathObj = next(
                    treepath_obj_iter
                )
                treepath_obj_name = treepath_obj.get_name()
            except StopIteration:
                finish()
                return
            # 'BUILD_DIR' is already shown by now. Some other entries should simply not be shown in
            # the Dashboard.
            if treepath_obj_name.upper() in (
                "BUILD_DIR",
                "BUTTONS_BTL",
            ):
                show_next_entry(treepath_obj_iter)
                return

            # Irrelevant entries should not be shown either.
            if not treepath_obj.is_relevant():
                show_next_entry(treepath_obj_iter)
                return

            # Determine the right parental item in the Dashboard. Usually it's the TreepathRoot-
            # Item(), since most entries are toplevel. But for some it's the 'BUILD_DIR' Treepath-
            # Item().
            parent_dashboard_item: Optional[
                Union[
                    _treepath_items_.TreepathRootItem,
                    _treepath_items_.TreepathItem,
                ]
            ] = None
            if treepath_obj_name.upper() in (
                "BIN_FILE",
                "ELF_FILE",
                "HEX_FILE",
            ):
                parent_dashboard_item = self._pathdict_[
                    "BUILD_DIR"
                ].get_dashboardItem()
            else:
                parent_dashboard_item = self._v_rootItem
            treepath_obj.create_dashboardItem(
                rootItem=self._v_rootItem,
                parentItem=parent_dashboard_item,
                treepath_seg=self,
            )
            parent_dashboard_item.add_child(
                treepath_obj.get_dashboardItem(),
                alpha_order=False,
                show=True,
                callback=show_next_entry,
                callbackArg=treepath_obj_iter,
            )
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            # Normally the registration of history functions would happen right
            # here. But I need to do it already in the constructor!
            return

        # * Start
        # Create the 'BUILD_DIR' TreepathItem() for the Dashboard. This one is needed before the
        # procedure to add all other entries can even start.
        self._pathdict_["BUILD_DIR"].create_dashboardItem(
            rootItem=self._v_rootItem,
            parentItem=self._v_rootItem,
            treepath_seg=self,
        )
        self._v_rootItem.add_child(
            self._pathdict_["BUILD_DIR"].get_dashboardItem(),
            alpha_order=False,
            show=True,
            callback=show_next_entry,
            callbackArg=iter(self.get_treepath_obj_list()),
        )
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        names: List[str],
        show_all: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the PROJECT LAYOUT on the Intro Wizard, inside the given
        vlyt. Only show those Tree- pathObj()/TreepathItem()-instances that are
        needed.

        NOTE: Irrelevant ones can still be shown if they're listed.
        """
        assert self.is_fake()
        self._v_intro_wiz_vlyt_ref = weakref.ref(vlyt)
        for name, treepath_obj in self._pathdict_.items():
            if name in ("BUTTONS_BTL",):
                # Don't show these ones on the intro wizard
                continue
            if not show_all:
                if name not in names:
                    # The given TreepathObj()/TreepathItem() is not requested
                    continue
            if treepath_obj.get_dashboardItem() is None:
                treepath_obj.create_dashboardItem(
                    rootItem=None,
                    parentItem=None,
                    treepath_seg=self,
                )
                treepath_obj.get_dashboardItem().get_layout().initialize()
            vlyt.addLayout(treepath_obj.get_dashboardItem().get_layout())
            continue
        if callback is not None:
            callback(callbackArg)
        return

    def get_impacted_files(self) -> List[str]:
        """"""
        impacted_files = []

        # Right now, the impacted file is always 'dashboard.mk' for any of the given config files.
        for key in self._pathdict_.keys():
            if self._pathdict_[key].has_asterisk():
                impacted_files.append("DASHBOARD_MK")

        return impacted_files

    def update_states(
        self,  # type: ignore[override]
        withgui: bool = True,
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None,
        probe: Optional[_probe_.Probe] = None,
        project_report: Optional[Dict] = None,
        check_existence: bool = True,
        version: Optional[Union[int, str]] = None,
        delete_nonexisting_paths: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Update the states of all TreepathObj()-instances stored in
        'self._pathdict_'.

        NOTE 1:
        Before, this method was intended to update the states of the corresponding dashboard Tree-
        pathItem()-instances directly, but that required the GUI to be up and running. Therefore,
        the TreepathItem()-instances now sync their own states in their sync_state() methods, pul-
        ling the states from the corresponding TreepathObj()s.

        NOTE 2:
        I added some code to generate a dashboard.mk file on-the-fly if it is not yet present.
        """
        is_fake = self.is_fake()
        if (version is None) or (version == "latest"):
            version = functions.get_latest_makefile_interface_version()
        assert isinstance(version, int)
        if toolpath_seg is None:
            if is_fake:
                toolpath_seg = (
                    data.current_project.intro_wiz.get_fake_toolpath_seg()
                )
            else:
                toolpath_seg = data.current_project.get_toolpath_seg()
        if probe is None:
            if is_fake:
                probe = data.current_project.intro_wiz.get_fake_probe()
            else:
                probe = data.current_project.get_probe()

        # * 1. Set relevances
        # There are two places where the relevances of treepath unicums are applied:
        #   1) Here
        #   2) In 'file_generator.py' if you pass 'None' to the 'filepaths' parameter from the
        #      get_new_dashboard_mk() function.
        # The relevances are determined in 'toolcats.json5', more in particular in the FLASTHOOL
        # category. One exception is then applied based on the 'can_flash_bootloader' field from the
        # probe dictionary.
        # $ Flashtool
        flashtool_uid = toolpath_seg.get_unique_id("FLASHTOOL")
        flashtool_obj = toolpath_seg.get_toolpathObj("FLASHTOOL")
        # Try to determine the 'relevant_list' based on the UID you get from the currently selected
        # flashtool. If no flashtool is selected, try to grab it from the flashtool pointed at by
        # the 'project_report'.
        relevant_list: Optional[List] = None
        if (flashtool_uid is None) or (flashtool_uid.lower() == "none"):
            if project_report:
                relevant_list = _toolcat_unicum_.TOOLCAT_UNIC(
                    "FLASHTOOL"
                ).get_relevant_treepaths(
                    unique_id=project_report["toolpath_report"]["FLASHTOOL"][
                        "proj_uid"
                    ],
                )
        if relevant_list is None:
            relevant_list = flashtool_obj.get_relevant_treepaths()
        for k in self._pathdict_.keys():
            self._pathdict_[k].set_relevant(k in relevant_list)

        # $ Probe...
        if probe.get_probe_dict()["can_flash_bootloader"]:
            self._pathdict_["BOOTLOADER_FILE"].set_relevant(True)
        else:
            self._pathdict_["BOOTLOADER_FILE"].set_relevant(False)

        if not check_existence:
            if callback is not None:
                callback(callbackArg)
            return

        # * 2. Check existence
        if delete_nonexisting_paths:
            for path_obj in self.get_treepath_obj_list():
                assert isinstance(path_obj, _treepath_obj_.TreepathObj)
                if (path_obj.get_name() == "FILETREE_MK") or (
                    path_obj.get_name() == "DASHBOARD_MK"
                ):
                    # Requires special treatment
                    continue
                abspath = path_obj.get_abspath()
                if (abspath is None) or (abspath.lower() == "none"):
                    # User should choose himself to auto/man locate
                    continue
                if path_obj.is_default_fallback():
                    # These are the .btl files and the build artifacts
                    continue
                if not os.path.exists(abspath):
                    # Refresh must be false, because 'update_states()' itself is
                    # part of the refresh function!
                    self.set_abspath(
                        unicum=path_obj.get_unicum(),
                        abspath=None,
                        history=True,
                        refresh=False,
                        with_gui=withgui,
                        callback=None,
                        callbackArg=None,
                    )
                    continue
                continue

        # & Check filetree.mk and dashboard.mk
        makefile_abspath = self.get_abspath("MAKEFILE")
        # $ Makefile location is None
        if (makefile_abspath is None) or (makefile_abspath.lower() == "none"):
            # $ FILETREE_MK
            if (self.get_relpath("FILETREE_MK") is None) or (
                self.get_relpath("FILETREE_MK").lower() == "none"
            ):
                pass
            else:
                self.set_abspath(
                    unicum="FILETREE_MK",
                    abspath=None,
                    history=True,
                    refresh=False,
                    with_gui=withgui,
                    callback=None,
                    callbackArg=None,
                )
            # $ DASHBOARD_MK
            if (self.get_relpath("DASHBOARD_MK") is None) or (
                self.get_relpath("DASHBOARD_MK").lower() == "none"
            ):
                pass
            else:
                self.set_abspath(
                    unicum="DASHBOARD_MK",
                    abspath=None,
                    history=True,
                    refresh=False,
                    with_gui=withgui,
                    callback=None,
                    callbackArg=None,
                )
        # $ Makefile location is a string
        else:
            makefile_dirpath = os.path.dirname(makefile_abspath).replace(
                "\\", "/"
            )
            dashboard_mk_abspath = _pp_.rel_to_abs(
                rootpath=makefile_dirpath,
                relpath="dashboard.mk",
            )
            filetree_mk_abspath = _pp_.rel_to_abs(
                rootpath=makefile_dirpath,
                relpath="filetree.mk",
            )
            # $ FILETREE_MK
            if self.get_abspath("FILETREE_MK") == filetree_mk_abspath:
                pass
            else:
                self.set_abspath(
                    unicum="FILETREE_MK",
                    abspath=filetree_mk_abspath,
                    history=True,
                    refresh=False,
                    with_gui=withgui,
                    callback=None,
                    callbackArg=None,
                )
            # $ DASHBOARD_MK
            if self.get_abspath("DASHBOARD_MK") == dashboard_mk_abspath:
                if not is_fake:
                    self.__create_dashboard_mk_if_needed()
            else:
                self.set_abspath(
                    unicum="DASHBOARD_MK",
                    abspath=dashboard_mk_abspath,
                    history=True,
                    refresh=False,
                    with_gui=withgui,
                    callback=(
                        nop if is_fake else self.__create_dashboard_mk_if_needed
                    ),
                    callbackArg=None,
                )

        # * 3. Set errors and warnings
        if delete_nonexisting_paths:
            for path_obj in self.get_treepath_obj_list():
                assert isinstance(path_obj, _treepath_obj_.TreepathObj)
                # $ 3.1 Makefile
                if path_obj.get_name().lower() == "makefile":
                    mkf = path_obj.get_abspath()
                    if (mkf is None) or (mkf.lower() == "none"):
                        path_obj.set_error(True)
                        if project_report:
                            project_report["treepath_report"]["MAKEFILE"][
                                "error"
                            ] = True
                    else:
                        if os.path.isfile(mkf):
                            path_obj.set_error(False)
                        else:
                            if project_report:
                                project_report["treepath_report"]["MAKEFILE"][
                                    "error"
                                ] = True
                            path_obj.set_error(True)

                # $ 3.2 Relevant files
                elif (
                    hasattr(path_obj, "is_relevant") and path_obj.is_relevant()
                ):
                    if path_obj.is_default_fallback():
                        # Can be generated automatically
                        path_obj.set_error(False)
                        pass
                    else:
                        filepath = path_obj.get_abspath()
                        if (filepath is None) or (filepath.lower() == "none"):
                            path_obj.set_error(True)
                            if project_report:
                                project_report["treepath_report"][
                                    path_obj.get_name().upper()
                                ]["warning"] = True
                        else:
                            if os.path.exists(filepath):
                                path_obj.set_error(False)
                            else:
                                if project_report:
                                    project_report["treepath_report"][
                                        path_obj.get_name().upper()
                                    ]["warning"] = True
                                path_obj.set_error(True)

                # $ 3.3 Irrelevant files
                elif hasattr(path_obj, "is_relevant") and (
                    not path_obj.is_relevant()
                ):
                    path_obj.set_error(False)
                    path_obj.set_warning(False)
                else:
                    # OK
                    pass
        if callback is not None:
            callback(callbackArg)
        return

    def __show_relevant_hide_irrelevant(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show the relevant TreepathObj()s through their TreepathItem()s, and
        hide the irrelevant ones."""
        if (not self.is_fake()) and (self._v_rootItem is None):
            # This can be the case if the dashboard doesn't exist yet, such as at startup when this
            # method is invoked through the Intro Wizard.
            if callback is not None:
                callback(callbackArg)
            return

        treepath_objs_to_hide: List[_treepath_obj_.TreepathObj] = []
        treepath_objs_to_show: List[_treepath_obj_.TreepathObj] = []
        sorted_list = [
            k for k in self._pathdict_.keys() if k not in ("BUTTONS_BTL",)
        ]

        for name, treepath_obj in self._pathdict_.items():
            if name in ("BUTTONS_BTL",):
                # Don't show these ones on the dashboard
                continue
            dashboard_item: _treepath_items_.TreepathItem = cast(
                _treepath_items_.TreepathItem,
                treepath_obj.get_dashboardItem(),
            )

            # * IRRELEVANT
            if not treepath_obj.is_relevant():
                if dashboard_item is None:
                    continue
                treepath_objs_to_hide.append(treepath_obj)
                continue

            # * RELEVANT
            assert treepath_obj.is_relevant()
            if dashboard_item is None:
                treepath_objs_to_show.append(treepath_obj)
            continue

        def hide_next(
            treepath_obj_iter: Iterator[_treepath_obj_.TreepathObj],
        ) -> None:
            "Hide the TreepathItem() from the next irrelevant TreepathObj()"
            try:
                _treepath_obj: _treepath_obj_.TreepathObj = next(
                    treepath_obj_iter
                )
            except StopIteration:
                show_next(iter(treepath_objs_to_show))
                return
            assert not _treepath_obj.is_relevant()
            _treepath_obj.delete_dashboardItem(
                callback=hide_next,
                callbackArg=treepath_obj_iter,
            )
            return

        def show_next(
            treepath_obj_iter: Iterator[_treepath_obj_.TreepathObj],
        ) -> None:
            "Show the TreepathItem() from the next relevant TreepathObj()"
            try:
                _treepath_obj: _treepath_obj_.TreepathObj = next(
                    treepath_obj_iter
                )
            except StopIteration:
                finish()
                return
            assert _treepath_obj.is_relevant()

            # $ Dashboard
            if not self.is_fake():
                _parent_dashboard_item: Optional[
                    Union[
                        _treepath_items_.TreepathRootItem,
                        _treepath_items_.TreepathItem,
                    ]
                ] = None
                if _treepath_obj.get_name().upper() in (
                    "BIN_FILE",
                    "ELF_FILE",
                    "HEX_FILE",
                ):
                    _parent_dashboard_item = self._pathdict_[
                        "BUILD_DIR"
                    ].get_dashboardItem()
                else:
                    _parent_dashboard_item = self._v_rootItem
                assert _parent_dashboard_item is not None
                if _treepath_obj.get_dashboardItem() is None:
                    _treepath_obj.create_dashboardItem(
                        rootItem=self._v_rootItem,
                        parentItem=_parent_dashboard_item,
                        treepath_seg=self,
                    )
                else:
                    assert not _treepath_obj.get_dashboardItem().is_dead()
                _parent_dashboard_item.add_child(
                    _treepath_obj.get_dashboardItem(),
                    alpha_order=sorted_list,
                    show=True,
                    callback=show_next,
                    callbackArg=treepath_obj_iter,
                )
                return

            # $ Intro Wizard
            assert self.is_fake()
            if self._v_intro_wiz_vlyt_ref is None:
                show_next(treepath_obj_iter)
                return
            if _treepath_obj.get_dashboardItem() is None:
                _treepath_obj.create_dashboardItem(
                    rootItem=None,
                    parentItem=None,
                    treepath_seg=self,
                )
                _treepath_obj.get_dashboardItem().get_layout().initialize()
            self._v_intro_wiz_vlyt_ref().addLayout(
                _treepath_obj.get_dashboardItem().get_layout()
            )
            show_next(treepath_obj_iter)
            return

        def finish(*args):
            if callback is not None:
                callback(callbackArg)
            return

        hide_next(iter(treepath_objs_to_hide))
        return

    def trigger_dashboard_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Applies both on Dashboard and Intro Wizard. It will do:

        - update states of one's own TreepathObj()s
        - update states of related segments (none at the moment)
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

        def show_relevant_hide_irrelevant(*args) -> None:
            "Show only the relevant GUI-elements"
            # Only the TreepathItem()s from the relevant TreepathObj()s should be shown. All others
            # should be hidden.
            self.__show_relevant_hide_irrelevant(
                callback=start_refresh,
                callbackArg=None,
            )
            return

        def start_refresh(*args) -> None:
            "Trigger a refresh on all GUI-elements"
            # $ Intro Wizard
            if is_fake:
                name_iter = iter(list(self._pathdict_.keys()))
                refresh_next_treepath_item(name_iter)
                return
            # $ Dashboard
            if (self._v_rootItem is None) or (
                self._v_rootItem._v_emitter is None
            ):
                finish()
                return
            self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                refresh_corresponding_filetree_items,
                None,
            )
            return

        def refresh_next_treepath_item(name_iter: Iterator[str]) -> None:
            "[intro wiz only]"
            assert is_fake
            try:
                name = next(name_iter)
            except StopIteration:
                finish()
                return
            treepath_obj: _treepath_obj_.TreepathObj = self._pathdict_[name]
            treepath_item: Optional[_treepath_items_.TreepathItem] = (
                treepath_obj.get_dashboardItem()
            )

            # For intro wiz items, it's not sure they exist.
            if (treepath_item is None) or (treepath_item._v_emitter is None):
                refresh_next_treepath_item(name_iter)
                return
            treepath_item._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                refresh_next_treepath_item,
                name_iter,
            )
            return

        def refresh_corresponding_filetree_items(*args) -> None:
            "[dashboard only]"
            # DEPRECATED
            assert not is_fake
            check_unsaved_changes()
            return

        def check_unsaved_changes(*args) -> None:
            "[dashboard only]"
            # Show the save button (and 'APPLY DASHBOARD CHANGES' banner) if
            # needed.
            assert not is_fake
            data.dashboard.check_unsaved_changes()
            finish()
            return

        def finish(*args) -> None:
            "Complete refreshing this TreepathSeg()"
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Update own states
        # First update the states of all the TreepathObj()s stored in this
        # TreepathSeg()-instance. Before, this step was intended to update the
        # states of the GUI-elements directly, but that required the GUI to be
        # up and running. Now, the states are stored in the TreepathObj()s and
        # will be pulled by the GUI-elements when they sync themselves. That
        # syncing is triggered in the 'start_refresh()' sub-function, see above.
        self.update_states(
            version=data.current_project.get_makefile_interface_version(),
            callback=show_relevant_hide_irrelevant,
            callbackArg=None,
        )
        return

    # ^                                      GETTERS AND SETTERS                                       ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def get_dashboardItem(
        self,
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
    ) -> _treepath_items_.TreepathItem:
        """Get corresponding TreepathItem() from the 'Project Layout' section in
        the Dashboard."""
        assert not self.is_fake()
        if isinstance(unicum, str):
            return self._pathdict_[unicum].get_dashboardItem()
        return self._pathdict_[unicum.get_name()].get_dashboardItem()

    def in_dashboard_path(self, abspath: str) -> bool:
        """Return True if the given abspath represents an item from the 'Project
        Layout' section in the dashboard.

        In other words, check if it is stored as a TreepathObj() in this
        TreepathSeg().
        """
        assert not self.is_fake()
        for k, v in self._pathdict_.items():
            if abspath in v.get_abspath():
                return True
        return False

    def is_filetree_mk(self, file_abspath: str) -> bool:
        """Return True if the given file abspath points to a valid 'filetree.mk'
        file from this TreepathSeg()-instance."""
        return self.get_abspath("FILETREE_MK") == file_abspath

    def get_relpath(self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]) -> Optional[str]:  # type: ignore[override]
        """"""
        obj = self.get_treepathObj(unicum)
        return obj.get_relpath()

    def get_abspath(self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]) -> Optional[str]:  # type: ignore[override]
        """"""
        obj = self.get_treepathObj(unicum)
        return obj.get_abspath()

    def get_default_relpath(
        self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]
    ) -> Optional[str]:
        """"""
        obj: _treepath_obj_.TreepathObj = self.get_treepathObj(unicum)
        return obj.get_default_relpath()

    def get_default_abspath(
        self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]
    ) -> Optional[str]:
        """"""
        obj = self.get_treepathObj(unicum)
        return obj.get_default_abspath()

    def is_readonly(
        self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]
    ) -> bool:
        """"""
        obj = self.get_treepathObj(unicum)
        return obj.is_readonly()

    def is_relevant(
        self, unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC]
    ) -> bool:
        """"""
        obj = self.get_treepathObj(unicum)
        if hasattr(obj, "is_relevant"):
            return obj.is_relevant()
        return True

    def set_relpath(
        self,  # type: ignore[override]
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
        relpath: Optional[str],
        history: bool,
        refresh: bool = True,
        with_gui: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        # Process inputs
        unicum_name: Optional[str] = None
        if isinstance(unicum, str):
            unicum_name = unicum
        else:
            unicum_name = unicum.get_name()
        abspath: Optional[str] = None
        if relpath is not None:
            treepath_obj = self.get_treepathObj(unicum_name)
            rootpath = treepath_obj.get_rootpath()
            assert rootpath is not None
            abspath = _pp_.rel_to_abs(
                rootpath=rootpath,
                relpath=relpath,
            )
        self.set_abspath(
            unicum=unicum_name,
            abspath=abspath,
            history=history,
            refresh=refresh,
            with_gui=with_gui,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def set_abspath(
        self,  # type: ignore[override]
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
        abspath: Optional[str],
        history: bool,
        refresh: bool = True,
        with_gui: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Split the given 'abspath' in: > 'rootpath' + 'rootid' > 'relpath'
        Then apply this on the requested PathObj().

        NONE:
        If 'abspath' is None, this method will preserve the existing 'rootpath'/'rootid' from the
        PathObj().
        """
        # Process inputs
        unicum_name: Optional[str] = None
        if isinstance(unicum, str):
            unicum_name = unicum
        else:
            unicum_name = unicum.get_name()
        treepath_obj = self.get_treepathObj(unicum_name)
        if (abspath is None) or (abspath.lower() == "none"):
            abspath = None

        #! ==================[ Check if change is needed ]=================== !#
        if abspath == self.get_abspath(unicum_name):
            if callback is not None:
                callback(callbackArg)
            return

        #! =====================[ Figure out rootpath ]====================== !#
        # Figure out to which rootpath the given 'abspath' belongs.
        rootpath: Optional[str] = None
        rootid: Optional[str] = None
        if abspath is None:
            rootpath = treepath_obj.get_rootpath()
            rootid = treepath_obj.get_rootid()
        else:
            for _rootpath in data.current_project.get_all_rootpaths():
                if abspath.startswith(_rootpath):
                    rootpath = _rootpath
                    break
            else:
                purefunctions.printc(
                    f"\nERROR: Invalid call to:\n"
                    f"TreepathSeg().set_abspath(\n"
                    f"    {unicum_name},\n"
                    f"    {abspath},\n"
                    f"    {history},\n"
                    f"    {refresh},\n"
                    f"    {with_gui},\n"
                    f"    {callback},\n"
                    f"    {callbackArg},\n"
                    f")\n"
                    f"The given abspath doesn{q}t fit in any of the toplevel folders:\n"
                    f"{data.current_project.get_all_rootpaths()}\n"
                    f"\n",
                    color="error",
                )
            rootid = data.current_project.get_rootid_from_rootpath(
                rootpath=rootpath,
            )
        assert rootpath is not None
        assert rootid is not None
        is_fake = self.is_fake()

        #! =====================[ Finishing functions ]====================== !#
        # Define here the inner functions that must run after applying the new abspath to the re-
        # quested PathObj().

        def check_history(*args):
            if history and (not is_fake):
                self.get_history().compare_to_baseline(
                    refresh=False,
                    callback=refresh_self,
                    callbackArg=None,
                )
                return
            refresh_self()
            return

        def refresh_self(*args):
            if with_gui and refresh:
                self.trigger_dashboard_refresh(
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args):
            # There was code here to inform the Source Analyzer about a new situation. This has been
            # moved to the save function.
            callback(callbackArg) if callback is not None else nop()
            return

        #! ========================[ Apply abspath ]========================= !#
        # Start here the procedure to apply the new 'abspath' on the requested PathObj().
        if history and (not is_fake):
            self.get_history().push()

        # * Apply
        # Simply apply the new abspath on the PathObj(). That means modifying its 'rootid' and
        # 'relpath'.
        relpath: Optional[str] = None
        if abspath is not None:
            relpath = _pp_.abs_to_rel(rootpath, abspath)
        treepath_obj.set_doublepath(
            (
                rootid,
                relpath,
            )
        )
        if unicum_name not in (
            "MAKEFILE",
            "LINKERSCRIPT",
            "BIN_FILE",
            "ELF_FILE",
        ):
            # There's no need to dive into the corner cases.
            check_history()
            return

        #! =========================[ Corner cases ]========================= !#
        # * 1. 'FILETREE_MK' or 'DASHBOARD_MK'
        # This 'set_abspath()' method won't ever be invoked by a user trying to change the
        # 'filetree.mk' or 'dashboard.mk' locations. Instead, the user will get the 'better
        # together' popup.
        if unicum_name in (
            "FILETREE_MK",
            "DASHBOARD_MK",
        ):
            raise RuntimeError()

        # * 2. 'MAKEFILE'
        # If we're dealing with the makefile, also change the abspaths for 'filetree.mk' and
        # 'dashboard.mk'.
        if unicum_name == "MAKEFILE":
            filetree_mk_treepath_obj = self.get_treepathObj("FILETREE_MK")
            dashboard_mk_treepath_obj = self.get_treepathObj("DASHBOARD_MK")

            # $ Create a path variable for each of them to be filled in soon.
            filetree_mk_relpath: Optional[str] = None
            dashboard_mk_relpath: Optional[str] = None

            # $ Makefile not found / deleted
            # Put the slaves toplevel, in the same root as where the makefile used to be. Remember:
            # even though 'abspath' gets forced to None, the rootid from the makefile PathObj()
            # doesn't change!
            if abspath is None:
                filetree_mk_relpath = "filetree.mk"
                dashboard_mk_relpath = "dashboard.mk"

            # $ Makefile is somewhere
            # Put the slaves next to the new location of the makefile.
            else:
                # Note:
                # 'relpath' here represents the relpath of the makefile.
                if "/" not in relpath:
                    filetree_mk_relpath = "filetree.mk"
                    dashboard_mk_relpath = "dashboard.mk"
                else:
                    filetree_mk_relpath = _pp_.standardize_relpath(
                        f"{os.path.dirname(relpath)}/filetree.mk"
                    )
                    dashboard_mk_relpath = _pp_.standardize_relpath(
                        f"{os.path.dirname(relpath)}/dashboard.mk"
                    )

            # $ Apply
            # Now apply the computed relpaths and the rootid from the makefile on the FILETREE_MK
            # and DASHBOARD_MK PathObj()s.
            filetree_mk_treepath_obj.set_doublepath(
                (
                    rootid,
                    filetree_mk_relpath,
                )
            )
            dashboard_mk_treepath_obj.set_doublepath(
                (
                    rootid,
                    dashboard_mk_relpath,
                )
            )
            check_history()
            return

        # * 3. 'LINKERSCRIPT'
        # Refreshing the memory view is no longer needed here. Johan's SA initiates that now.

        # * 4. 'BIN_FILE', 'ELF_FILE' or 'BUILD_DIR'
        # If we're dealing with one of the binaries, change the others accordingly.
        bin_file_relpath: Optional[str] = None
        elf_file_relpath: Optional[str] = None
        found_binary_name: Optional[str] = None

        # & 4a. 'BIN_FILE'
        if unicum_name == "BIN_FILE":
            # TODO: Check if the BUILD_DIR needs to be moved

            # $ First save the old abspath
            # As we're going to modify the abspath from the elf file, its old one should be stored
            # first.
            elf_file_treepath_obj = self.get_treepathObj("ELF_FILE")
            # Now create a path variable to be filled in soon.
            elf_file_relpath = None

            # $ BIN_FILE not found / deleted
            # This shouldn't happen.
            if abspath is None:
                assert False

            # $ BIN_FILE is somewhere
            # Put the ELF_FILE next to the new location.
            else:
                # Note:
                # 'relpath' here represents the relpath of the BIN_FILE.
                elf_file_relpath = relpath.replace(".bin", ".elf")

            # $ Apply
            # Now apply the computed relpath and the rootid from the BIN_FILE
            # on the ELF_FILE PathObj().
            elf_file_treepath_obj.set_doublepath(
                (
                    rootid,
                    elf_file_relpath,
                )
            )
            check_history()
            return

        # & 4b. 'ELF_FILE'
        if unicum_name == "ELF_FILE":
            # TODO: Check if the BUILD_DIR needs to be moved
            bin_file_treepath_obj = self.get_treepathObj("BIN_FILE")

            # $ Create a path variable to be filled in soon.
            bin_file_relpath = None

            # $ ELF_FILE not found / deleted
            # This shouldn't happen.
            if abspath is None:
                assert False

            # $ ELF_FILE is somewhere
            # Put the BIN_FILE next to the new location.
            else:
                # Note:
                # 'relpath' here represents the relpath of the ELF_FILE.
                bin_file_relpath = relpath.replace(".elf", ".bin")

            # $ Apply
            # Now apply the computed relpath and the rootid from the ELF_FILE on the BIN_FILE
            # PathObj().
            bin_file_treepath_obj.set_doublepath(
                (
                    rootid,
                    bin_file_relpath,
                )
            )
            check_history()
            return

        # & 4c. 'BUILD_DIR'
        if unicum_name == "BUILD_DIR":
            bin_file_treepath_obj = self.get_treepathObj("BIN_FILE")
            elf_file_treepath_obj = self.get_treepathObj("ELF_FILE")

            # $ Create a path variable for each of them to be filled in soon.
            bin_file_relpath = None
            elf_file_relpath = None
            found_binary_name = None

            # $ BUILD_DIR not found / deleted
            # This shouldn't happen.
            if abspath is None:
                assert False

            # $ BUILD_DIR is somewhere
            # Search for binaries
            elif os.path.isdir(abspath):
                for f in os.listdir(abspath):
                    if f.endswith(
                        (
                            ".bin",
                            ".elf",
                            ".hex",
                        )
                    ):
                        found_binary_name = f
                        break

            if found_binary_name is None:
                bin_file_relpath = bin_file_treepath_obj.get_default_relpath()
                elf_file_relpath = elf_file_treepath_obj.get_default_relpath()
            else:
                bin_file_relpath = f"{relpath}/{found_binary_name}"
                elf_file_relpath = f"{relpath}/{found_binary_name}"
                bin_file_relpath = bin_file_relpath.replace(
                    ".elf", ".bin"
                ).replace(".hex", ".bin")
                elf_file_relpath = elf_file_relpath.replace(
                    ".bin", ".elf"
                ).replace(".hex", ".elf")

            # $ Apply
            # Now apply the computed relpaths and the rootid from the BUILD_DIR on the BIN_FILE and
            # ELF_FILE PathObj()s.
            bin_file_treepath_obj.set_doublepath(
                (
                    rootid,
                    bin_file_relpath,
                )
            )
            elf_file_treepath_obj.set_doublepath(
                (
                    rootid,
                    elf_file_relpath,
                )
            )
            check_history()
            return

        check_history()
        return

    def get_treepathObj(
        self,
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
    ) -> _treepath_obj_.TreepathObj:
        """"""
        if isinstance(unicum, str):
            return self._pathdict_[unicum]
        return self._pathdict_[unicum.get_name()]

    def get_treepathObj_from_abspath(
        self,
        abspath: str,
    ) -> Optional[_treepath_obj_.TreepathObj]:
        """This function used to work on relpaths, but that isn't safe anymore.

        TreepathObj()s can now belong to any toplevel folder!
        """
        for k, v in self._pathdict_.items():
            if v.get_abspath() == abspath:
                return v
        return None

    def get_treepath_obj_list(self) -> List[_treepath_obj_.TreepathObj]:
        """"""
        return [v for k, v in self._pathdict_.items()]

    def get_treepath_unicum_names(self) -> List[str]:
        """"""
        return list(self._pathdict_.keys())

    def printout(self, nr: int, *args, **kwargs) -> str:
        """Return the text to be saved into 'dashboard_config.btl'."""
        super().printout(nr)
        lines = [
            f"# {nr}. Project Layout",
        ]
        for k, v in self._pathdict_.items():
            if k in (
                "FILETREE_MK",
                "DASHBOARD_MK",
                "BUTTONS_BTL",
            ):
                # These values must not be stored:
                #  - 'FILETREE_MK' and 'DASHBOARD_MK': They rely on the value of
                #    the makefile.
                #  - '*.BTL': The .btl files get a default value in the load()
                #    function.
                continue
            relpath: Optional[str] = v.get_relpath()
            rootid: Optional[str] = v.get_rootid()
            value: Optional[str] = None
            if (relpath is None) or (relpath.lower() == "none"):
                value = "None"
            else:
                value = f"{rootid}/{relpath}"
            lines.append(f"{k.ljust(20)} = {q}{value}{q}")

        lines.append("")
        return "\n".join(lines)

    # ^                                          AUTOLOCATORS                                          ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def autolocate_or_autogenerate_empty_if_needed(
        self,
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
        history: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Go through this procedure:
            1. Check abspath. If the file/folder exist, stop. Else continue.
            2. Autolocate the file/folder.
            3. If abspath is None or "None", fill in the default abspath.
            4. If the file/folder at abspath exists, stop. Else continue.
            5. All attempts to locate the file/folder have failed. So create an empty one.

        > callback(abspath, callbackArg)
        """

        def start(*args):
            # First check, and autolocate if needed.
            abspath: Optional[str] = self.get_abspath(unicum=unicum)
            abspath_lower: Optional[str] = None
            if abspath is not None:
                abspath_lower = abspath.lower()
            if (
                (abspath is None)
                or (abspath_lower == "none")
                or (not os.path.exists(abspath))
            ):
                self.autolocate(
                    unicum=unicum,
                    force=False,
                    adapt=True,
                    history=history,
                    callback=check,
                    callbackArg=None,
                )
                return
            assert os.path.exists(abspath)
            finish()
            return

        def check(*args):
            # Check again after autolocation.
            abspath: Optional[str] = self.get_abspath(unicum=unicum)
            abspath_lower: Optional[str] = None
            if abspath is not None:
                abspath_lower = abspath.lower()
            if (abspath_lower is None) or (abspath_lower == "none"):
                abspath = _pp_.rel_to_abs(
                    rootpath=data.current_project.get_proj_rootpath(),
                    relpath=unicum.get_default_relpath(),
                )
            if abspath is not None:
                if (abspath_lower != "none") and os.path.exists(abspath):
                    self.set_abspath(
                        unicum=unicum,
                        abspath=abspath,
                        history=True,
                        refresh=False,
                        callback=finish,
                        callbackArg=None,
                    )
                    return
                if abspath_lower != "none":
                    generate(abspath)
                    return
            finish()
            return

        def generate(abspath):
            pathObj = self.get_treepathObj(unicum=unicum)
            if pathObj.is_file():
                _fp_.make_file(abspath)
            else:
                _fp_.make_dir(abspath)
            self.set_abspath(
                unicum=unicum,
                abspath=abspath,
                history=True,
                refresh=False,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            abspath = self.get_abspath(unicum=unicum)
            callback(abspath, callbackArg)
            return

        start()
        return

    def autolocate(
        self,
        unicum: Union[str, _treepath_unicum_.TREEPATH_UNIC],
        force: bool,
        adapt: bool,
        history: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Autolocate the given file/folder. If the file/folder already exists
        and force == False => simply return the existing file/folder.

        :param unicum:   The unicum for which to autolocate.
        :param force:       Autolocation starts with observing the current loc-
                            ation. If something exists there, no need to look
                            further - unless you set this parameter.
        :param adapt:       Adapt the corresponding entry in the dashboard.
        :param history:     Push any changes to the history.

        Return value is given in callback, the absolute path to the found file/folder:

        > callback(abspath, callbackArg)
        """
        if isinstance(unicum, str):
            unicum = _treepath_unicum_.TREEPATH_UNIC(unicum)
        assert isinstance(unicum, _treepath_unicum_.TREEPATH_UNIC)
        #! ------------------[ filetree.mk / dashboard.mk ]------------------ !#
        # Special treatment:
        # Locate the makefile and put filetree.mk/dashboard.mk right next to it!
        if (unicum.get_name() == "FILETREE_MK") or (
            unicum.get_name() == "DASHBOARD_MK"
        ):

            def _finish_(_makefile_abspath_, *args):
                if (_makefile_abspath_ is None) or (
                    _makefile_abspath_.lower() == "none"
                ):
                    callback(None, callbackArg)
                    return
                _makefile_dirpath_ = os.path.dirname(_makefile_abspath_)
                _makefile_dirpath_ = _makefile_dirpath_.replace("\\", "/")
                if unicum.get_name() == "FILETREE_MK":
                    _filetree_mk_abspath_ = _pp_.rel_to_abs(
                        rootpath=_makefile_dirpath_,
                        relpath="filetree.mk",
                    )
                    callback(_filetree_mk_abspath_, callbackArg)
                    return
                if unicum.get_name() == "DASHBOARD_MK":
                    _dashboard_mk_abspath_ = _pp_.rel_to_abs(
                        rootpath=_makefile_dirpath_,
                        relpath="dashboard.mk",
                    )
                    callback(_dashboard_mk_abspath_, callbackArg)
                    return
                assert False
                return

            self.autolocate(
                unicum="MAKEFILE",
                force=False,
                adapt=False,
                history=False,
                callback=_finish_,
                callbackArg=None,
            )
            return
        #! -----------------------[ everything else ]------------------------ !#
        assert unicum.get_name().upper() != "FILETREE_MK"
        assert unicum.get_name().upper() != "DASHBOARD_MK"
        searchpath = data.current_project.get_proj_rootpath()
        unicum_searchpath = unicum.get_dict()["searchpath"].upper()
        if unicum_searchpath != "ROOT":
            if unicum_searchpath == "DOT_BEETLE_DIR":
                searchpath = _pp_.rel_to_abs(
                    rootpath=data.current_project.get_proj_rootpath(),
                    relpath=".beetle",
                )
            else:
                searchpath = self._pathdict_[unicum_searchpath].get_abspath()
        if (
            (searchpath is None)
            or (searchpath.lower() == "none")
            or (not os.path.exists(searchpath))
        ):
            if unicum_searchpath == "BUILD_DIR":
                searchpath = _pp_.rel_to_abs(
                    rootpath=data.current_project.get_proj_rootpath(),
                    relpath="build",
                )
            if not os.path.isdir(searchpath):
                searchpath = None

        isfile = unicum.get_dict()["is_file"]
        validnames = unicum.get_dict()["valid_names"]
        exceptions = unicum.get_dict()["invalid_names"]

        # * CASE 1:
        # - dir/file exists at currently displayed path
        # - force == False
        # =>
        # Simply return the displayed path.
        abspath: Optional[str] = self.get_abspath(unicum=unicum)
        if (
            (abspath is not None)
            and (abspath.lower() != "none")
            and os.path.exists(abspath)
            and (data.current_project.get_proj_rootpath() in abspath)
            and (force == False)
        ):
            callback(abspath, callbackArg)
            return

        # * CASE 2:
        # Displayed path is None or doesn't point to a real dir/file.
        # =>
        # Look around to find the dir/file.
        found_abspath: Optional[str] = None
        if searchpath is not None:
            for i in range(len(validnames)):
                if isfile:
                    found_abspath = _pp_.search_file(
                        searchpath=searchpath,
                        filename=validnames[i],
                        exception=exceptions,
                    )
                else:
                    found_abspath = _pp_.search_dir(
                        searchpath=searchpath,
                        dirname=validnames[i],
                        exception=exceptions,
                    )
                if (found_abspath is not None) and (
                    found_abspath.lower() != "none"
                ):
                    # FOUND !
                    if adapt:

                        def _finish_(_abspath_: str, *args) -> None:  # type: ignore
                            callback(_abspath_, callbackArg)
                            return

                        self.set_abspath(
                            unicum=unicum,
                            abspath=found_abspath,
                            history=history,
                            refresh=False,
                            callback=_finish_,
                            callbackArg=found_abspath,
                        )
                        return
                    callback(found_abspath, callbackArg)
                    return
        assert (found_abspath is None) or (found_abspath.lower() == "none")

        # * CASE 3:
        # Displayed path is None or doesn't point to a real dir/file,
        # Nothing found on disk
        # =>
        # If 'default fallback' active -> keep displayed path, unless 'None' then
        #                                 fallback to default path
        # Else -> explicitely set to 'None'

        # DEFAULT FALLBACK
        if unicum.get_dict()["default_fallback"]:
            # 'None' displayed
            if (abspath is None) or (abspath.lower() == "none"):
                df_abspath = self.get_default_abspath(unicum=unicum)
                if adapt:

                    def _finish_(_abspath_: str, *args) -> None:  # type: ignore
                        callback(_abspath_, callbackArg)
                        return

                    self.set_abspath(
                        unicum=unicum,
                        abspath=df_abspath,
                        history=history,
                        refresh=False,
                        callback=_finish_,
                        callbackArg=df_abspath,
                    )
                    return
                callback(df_abspath, callbackArg)
                return
            # Something displayed
            assert (abspath is not None) and (abspath.lower() != "none")
            callback(abspath, callbackArg)
            return

        # NO FALLBACK
        # 'None' displayed
        if (abspath is None) or (abspath.lower() == "none"):
            callback(None, callbackArg)
            return
        # Something displayed
        assert (abspath is not None) and (abspath.lower() != "none")
        if adapt:

            def _finish_(_abspath_: str, *args) -> None:  # type: ignore
                callback(_abspath_, callbackArg)
                return

            self.set_abspath(
                unicum=unicum,
                abspath=None,
                history=history,
                refresh=False,
                callback=_finish_,
                callbackArg=None,
            )
            return
        callback(None, callbackArg)
        return

    # ^                                             DEATH                                              ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this TreepathSeg()-instance and *all* its representations in the
        Dashboard or Intro Wizard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill TreepathSeg() twice!")
            self.dead = True

        def start(*args) -> None:
            # $ Dashboard
            if not self.is_fake():
                if self._v_rootItem:
                    self._v_rootItem.self_destruct(
                        killParentLink=False,
                        callback=start_killing_treepath_objs,
                        callbackArg=None,
                    )
                    return
                start_killing_treepath_objs()
                return
            # $ Intro Wizard
            start_killing_treepath_objs()
            return

        def start_killing_treepath_objs(*args) -> None:
            kill_next_treepath_obj(iter(list(self._pathdict_.keys())))
            return

        def kill_next_treepath_obj(name_iter: Iterator[str]) -> None:
            # This function kills one TreepathObj() from the 'self._pathdict_'
            # dictionary. If the given TreepathObj() has no more GUI-elements
            # (eg. after self._v_rootItem has been destroyed), their non-GUI
            # elements will be deleted.
            try:
                name = next(name_iter)
            except StopIteration:
                finish()
                return
            treepath_obj: _treepath_obj_.TreepathObj = self._pathdict_[name]
            treepath_obj.self_destruct(
                callback=kill_next_treepath_obj,
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
