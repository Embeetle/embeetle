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
import os, re, threading, functools
import qt, data, purefunctions, functions, gui, iconfunctions
import project.segments.project_segment as _ps_
import dashboard.items.version_items.version_items as _da_version_items_
import bpathlib.path_power as _pp_

if TYPE_CHECKING:
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class VersionSeg(_ps_.ProjectSegment):
    @classmethod
    def create_default_Version(
        cls, version_nr: Optional[Union[str, int]]
    ) -> VersionSeg:
        """Create a default Version()-instance."""
        if (version_nr is None) or (version_nr == -1):
            version_nr = functions.get_latest_makefile_interface_version()
        return cls(
            is_fake=False,
            version_nr=version_nr,
        )

    @classmethod
    def create_empty_Version(
        cls, version_nr: Optional[Union[str, int]]
    ) -> VersionSeg:
        """Create an empty Version()-instance."""
        return cls.create_default_Version(version_nr)

    @classmethod
    def load(
        cls,
        relevant_filepaths: Optional[Dict[str, str]],
        with_engine: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load Version()-object from the relevant files in the project.

        NOTES:
        The version nr and project type are extracted directly from the given dictionary with rel-
        evant filepaths.
        """

        def finish(
            _version_nr: Optional[Union[str, int]], _apply: bool
        ) -> None:
            # By now, the version nr has been figured out, as well as a flag to indicate if the ver-
            # sion still needs to be applied on some files. Create the VersionSeg()-instance and re-
            # turn it in the callback.
            if _version_nr is None:
                _version_nr = functions.get_latest_makefile_interface_version()
            _version_seg = cls(
                is_fake=False,
                version_nr=_version_nr,
            )
            _version_seg.set_version_needs_to_be_applied(_apply)
            callback(
                _version_seg,
                callbackArg,
            )
            return

        # $ No files given
        if relevant_filepaths is None:
            purefunctions.printc(
                f"WARNING: VersionSeg().load() got {q}relevant_filepaths{q} parameter None",
                color="warning",
            )
            finish(None, False)
            return

        # $ Relevant files given
        # The following function extracts the makefile versions from the given files. It also com-
        # pares them and shows a popup-warning if there's a mismatch.
        cls.__determine_makefile_interface_version(
            rootpath=relevant_filepaths["proj_rootpath"],
            makefile_abspath=relevant_filepaths["makefile_abspath"],
            dashboard_mk_abspath=relevant_filepaths["dashboard_mk_abspath"],
            filetree_mk_abspath=relevant_filepaths["filetree_mk_abspath"],
            with_engine=with_engine,
            callback=finish,
        )
        return

    __slots__ = (
        "__version_nr",
        "__version_needs_to_be_applied",
        "_v_rootItem",
        "_v_typeItem",
        "_v_nrItem",
        "_v_repairItem",
        "_v_upgradeItem",
        "__trigger_dashboard_refresh_mutex",
    )

    def __init__(
        self,
        is_fake: bool,
        version_nr: Optional[Union[str, int]],
    ) -> None:
        """"""
        super().__init__(is_fake)

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        # $ Version nr
        self.__version_nr: Optional[int] = None
        if (version_nr is None) or (version_nr == "latest"):
            self.__version_nr = (
                functions.get_latest_makefile_interface_version()
            )
        else:
            assert isinstance(version_nr, int)
            self.__version_nr = version_nr

        # $ Version needs to be applied
        self.__version_needs_to_be_applied = False

        # $ Dashboard
        self._v_rootItem: Optional[_da_version_items_.VersionRootItem] = None
        self._v_typeItem: Optional[_da_version_items_.ProjectTypeItem] = None
        self._v_nrItem: Optional[_da_version_items_.VersionNrItem] = None
        self._v_repairItem: Optional[_da_version_items_.RepairItem] = None
        self._v_upgradeItem: Optional[_da_version_items_.VersionUpgradeItem] = (
            None
        )
        return

    def get_version_nr(self) -> int:
        """"""
        return self.__version_nr

    def set_version_nr(self, version_nr: Optional[Union[int, str]]) -> None:
        """"""
        if (version_nr is None) or (version_nr == "latest"):
            self.__version_nr = (
                functions.get_latest_makefile_interface_version()
            )
        else:
            assert isinstance(version_nr, int)
            self.__version_nr = version_nr
        return

    def set_version_needs_to_be_applied(self, apply: bool) -> None:
        """Set a flag to indicate if the version nr still needs to be applied on
        the current project."""
        self.__version_needs_to_be_applied = apply

    def get_version_needs_to_be_applied(self) -> bool:
        """Check if the version nr still needs to be applied on the current pro-
        ject."""
        return self.__version_needs_to_be_applied

    def clone(self, is_fake: bool = True) -> VersionSeg:
        """Clone this object."""
        cloned_version = VersionSeg(
            is_fake=is_fake,
            version_nr=None,
        )
        return cloned_version

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show this Version()-instance on the dashboard.

        Only the toplevel item is shown, but the child items are instantiated
        and added to the toplevel item. They get shown when the user clicks on
        the toplevel one.
        """
        assert not self.is_fake()
        self._v_rootItem = _da_version_items_.VersionRootItem(version=self)
        data.dashboard.add_root(self._v_rootItem)
        self._v_typeItem = _da_version_items_.ProjectTypeItem(
            version=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_rootItem.add_child(
            self._v_typeItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        self._v_nrItem = _da_version_items_.VersionNrItem(
            version=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_rootItem.add_child(
            self._v_nrItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        self._v_repairItem = _da_version_items_.RepairItem(
            version=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_rootItem.add_child(
            self._v_repairItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        if (
            self.__version_nr
            < functions.get_latest_makefile_interface_version()
        ):
            self._v_upgradeItem = _da_version_items_.VersionUpgradeItem(
                version=self,
                rootdir=self._v_rootItem,
                parent=self._v_rootItem,
            )
            self._v_rootItem.add_child(
                self._v_upgradeItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
        # self.get_history().register_getters(
        #     chip_unicum = self.get_board_unicum,
        # )
        # self.get_history().register_setters(
        #     chip_unicum = self.set_board_unicum,
        # )
        # self.get_history().register_asterisk_setters(
        #     chip_unicum = self._v_viewItem.get_state().set_asterisk,
        # )
        # self.get_history().register_refreshfunc(
        #     self.trigger_dashboard_refresh,
        # )
        if callback is not None:
            callback(callbackArg)
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the Version on the Intro Wizard, inside the given vlyt."""
        assert self.is_fake()
        self._v_nrItem = _da_version_items_.VersionNrItem(
            version=self,
            rootdir=None,
            parent=None,
        )
        self._v_nrItem.get_layout().initialize()
        vlyt.addLayout(self._v_nrItem.get_layout())
        if callback is not None:
            callback(callbackArg)
        return

    def update_states(
        self,  # type: ignore[override]
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
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
        - update states of related segments (chip)
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

        def hide_or_show_upgrade_item(*args) -> None:
            # Hide the upgrade item if the version is already the latest one.
            latest_v: int = functions.get_latest_makefile_interface_version()

            # $ SHOW
            if (self.__version_nr < latest_v) and (self._v_upgradeItem is None):
                self._v_upgradeItem = _da_version_items_.VersionUpgradeItem(
                    version=self,
                    rootdir=self._v_rootItem,
                    parent=self._v_rootItem,
                )
                self._v_rootItem.add_child(
                    self._v_upgradeItem,
                    alpha_order=False,
                    show=True,
                    callback=refresh_root_recursive,
                    callbackArg=None,
                )
                return

            # $ HIDE
            elif (self.__version_nr >= latest_v) and (
                self._v_upgradeItem is not None
            ):
                self._v_upgradeItem.self_destruct(
                    killParentLink=True,
                    callback=refresh_root_recursive,
                    callbackArg=None,
                )
                return

            refresh_root_recursive()
            return

        def refresh_root_recursive(*args) -> None:
            "[dashboard only]"
            if is_fake:
                refresh_type_item()
                return
            assert not is_fake
            if self._v_rootItem and self._v_rootItem._v_emitter:
                self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                    True,
                    False,
                    finish,
                    None,
                )
                return
            finish()
            return

        def refresh_type_item(*args) -> None:
            "[intro wiz only]"
            assert is_fake
            if self._v_typeItem and self._v_typeItem._v_emitter:
                self._v_typeItem._v_emitter.refresh_later_sig.emit(
                    True,
                    False,
                    refresh_nr_item,
                    None,
                )
                return
            refresh_nr_item()
            return

        def refresh_nr_item(*args) -> None:
            "[intro wiz only]"
            assert is_fake
            if self._v_nrItem and self._v_nrItem._v_emitter:
                self._v_nrItem._v_emitter.refresh_later_sig.emit(
                    True,
                    False,
                    refresh_repair_item,
                    None,
                )
                return
            refresh_repair_item()
            return

        def refresh_repair_item(*args) -> None:
            "[intro wiz only]"
            assert is_fake
            if self._v_repairItem and self._v_repairItem._v_emitter:
                self._v_repairItem._v_emitter.refresh_later_sig.emit(
                    True,
                    False,
                    refresh_upgrade_item,
                    None,
                )
                return
            refresh_upgrade_item()
            return

        def refresh_upgrade_item(*args) -> None:
            "[intro wiz only]"
            assert is_fake
            if self._v_upgradeItem and self._v_upgradeItem._v_emitter:
                self._v_upgradeItem._v_emitter.refresh_later_sig.emit(
                    True,
                    False,
                    finish,
                    None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            if data.dashboard:
                data.dashboard.check_unsaved_changes()
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Update own states
        self.update_states(
            callback=hide_or_show_upgrade_item,
            callbackArg=None,
        )
        return

    def change_version(
        self,
        new_version: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Change version and trigger a dashboard refresh.

        Works for both the Dash- board and the Intro Wizard.
        """
        raise RuntimeError()
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        super().printout(nr)
        project_type = "makefile"
        lines = [
            f"# {nr}. Version ",
            f"project_type = {q}{project_type}{q}",
            f"project_version = {q}{self.get_version_nr()}{q}",
            f"",
        ]
        return "\n".join(lines)

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Version()-instance and *all* its representations in the
        Dash- board or Intro Wizard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill VersionSeg() twice!")
            self.dead = True

        def start(*args) -> None:
            # TODO: Implement
            if callback is not None:
                callback(callbackArg)
            return

        super().self_destruct(
            callback=start,
            callbackArg=None,
            death_already_checked=True,
        )
        return

    # ^                     MAKEFILE INTERFACE HELP FUNCTIONS                      ^#
    # % ========================================================================== %#
    # % Extract makefile interface versions from files and show popups in case of  %#
    # % mismatches.                                                                %#
    # %                                                                            %#

    def show_project_type_info(self) -> None:
        """Show a popup with the current project type."""
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]
        text = f"""
        <p align='left'>
            Your project is makefile-based. This means that a makefile is<br>
            used to manage the clean, build and flash procedures.<br>
            <br>
            Right now, makefile-based projects are the only ones you can open<br>
            in Embeetle.
        </p>
        """
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/gen/certificate.png",
            title_text="Project type",
            text=text,
        )
        return

    def show_extracted_version_nrs(self) -> None:
        """Show a popup with all the extracted version nrs."""
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]
        treepath_seg: _treepath_seg_.TreepathSeg = (
            data.current_project.get_treepath_seg()
        )
        makefile_v: Union[None, int, str] = (
            VersionSeg.__get_makefile_interface_version_from_file(
                filepath=treepath_seg.get_abspath("MAKEFILE"),
            )
        )
        dashboard_mk_v: Union[None, int, str] = (
            VersionSeg.__get_makefile_interface_version_from_file(
                filepath=treepath_seg.get_abspath("DASHBOARD_MK"),
            )
        )
        filetree_mk_v: Union[None, int, str] = (
            VersionSeg.__get_makefile_interface_version_from_file(
                filepath=treepath_seg.get_abspath("DASHBOARD_MK"),
            )
        )
        project_v: Union[None, int, str] = (
            VersionSeg.__get_makefile_interface_version_from_file(
                filepath=f"{data.current_project.get_proj_rootpath()}/.beetle/dashboard_config.btl",
            )
        )
        latest_v = functions.get_latest_makefile_interface_version()
        text = f"""
        <p align='left'>
            The extracted Embeetle makefile interface versions are:<br>
            {tab}- makefile: {blue}{makefile_v}{end}<br>
            {tab}- dashboard.mk: {blue}{dashboard_mk_v}{end}<br>
            {tab}- filetree.mk: {blue}{filetree_mk_v}{end}<br>
            {tab}- project: {blue}{project_v}{end}<br>
            <br>
            (Note: The latest Embeetle makefile interface version is: {blue}{latest_v}{end})
        </p>
        """
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/gen/certificate.png",
            title_text="Project version",
            text=text,
        )
        return

    @classmethod
    def __get_makefile_interface_version_from_file(
        cls, filepath: str
    ) -> Union[None, int, str]:
        """SUMMARY =======

        Extract the makefile interface version from the given file and return it as an integer:
         - 'makefile',
         - 'filetree.mk'
         - 'dashboard.mk'
         - 'filetree_config.btl'
         - 'dashboard_config.btl'

        CORNER CASES
        ============
        Several corner cases are possible. This function can return one of the following values for
        the given situation:
            > None:         - No version found
                            - Version mentioned as None or string 'None' (*)

            > 'latest':     - Version mentioned as string 'latest'.

            > -1:           - Version mentioned as integer -1 or string '-1'

        For these corner cases, eventually the latest version must be applied. However, that's not
        the responsibility of this function.

        (*) Mentioning the version explicitely as None or 'None' is not good practice. None should
        be reserved for those instances where the version isn't mentioned at all. If you want to
        force the latest version, mention the version as either 'latest' or '-1'.
        """
        # Existence check
        if (
            (filepath is None)
            or (filepath.lower() == "none")
            or not os.path.isfile(filepath)
        ):
            purefunctions.printc(
                f"WARNING: Could not find file to extract makefile "
                f"interface version from:\n"
                f"{q}{filepath}{q}\n",
                color="warning",
            )
            return None

        def print_info(
            _m: Optional[re.Match[AnyStr]], _found_where: str
        ) -> None:
            "Print how the makefile version was found"
            # print(
            #     f'>>> found v{_m.group(1)} in {_found_where} from '
            #     f'{q}{os.path.basename(filepath)}{q}'
            # )
            return

        # * Parse file
        content = ""
        with open(
            filepath, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            content = f.read()

        # Throughout the years, the way this makefile version was shown evolved. Also, it depends
        # on the kind of file being investigated. Therefore, try out all sorts of regexes to find a
        # match.

        # $ 1. 'EMBEETLE_MAKEFILE_INTERFACE_VERSION' in 'dashboard.mk' and 'filetree.mk'
        # The 'dashboard.mk' and 'filetree.mk' files define this variable explicitely from v6
        # onwards.
        p = re.compile(r"EMBEETLE_MAKEFILE_INTERFACE_VERSION\s*=\s*(.*)")
        m = p.search(content)
        if m is None:
            # $ 2. 'EMBEETLE_MAKEFILE_INTERFACE_VERSION' in 'makefile'
            # The makefile defines checks on this variable after including the 'dashboard.mk'
            # and 'filetree.mk' files. Therefore, the regex to detect this variable and its
            # value must be different for the makefile.
            p = re.compile(r"\(EMBEETLE_MAKEFILE_INTERFACE_VERSION\),(.*)\)")
            m = p.search(content)
            if m is None:
                # $ 3. Explicit 'project_version = ..' in '*.btl'
                # The 'dashboard_config.btl' file defines the project version from v6 onwards,
                # as it is part of the VersionSeg()-instance.
                p = re.compile(r"project_version\s*=\s*(.*)")
                m = p.search(content)
                if m is None:
                    # $ 4. Explicit "project_verion": "7" in json-formatted '*.btl'
                    # The 'dashboard_config.btl' files are recently stored in json-format.
                    p = re.compile(
                        r"[\'\"]project_version[\'\"]\s*:\s*([\w\'\"-]*)"
                    )
                    m = p.search(content)
                    if m is None:
                        # $ 5. Look for implicit comment
                        # Before v6, the only way to detect the project's version nr was through
                        # parsing the comments.
                        # NOTE: if you ever change this regex, also adapt the regex in
                        # 'file_changer.py'!
                        p = re.compile(
                            r"[Ee]mbeetle\s*makefile\s*interface\s*version\s*(-?\d+)"
                        )
                        m = p.search(content)
                        if m is None:
                            p = re.compile(
                                r"makefile\s*interface\s*version\s*(-?\d+)"
                            )
                            m = p.search(content)
                            if m is None:
                                # Version not found
                                # Search was done on the whole content. No other try will be per-
                                # formed. Print about the failure
                                purefunctions.printc(
                                    f"WARNING: Failed to find version nr in "
                                    f"{q}{os.path.basename(filepath)}{q}!",
                                    color="warning",
                                )
                                return None
                            else:
                                print_info(m, "comment")
                        else:
                            print_info(m, "comment")
                    else:
                        print_info(m, "json")
                else:
                    print_info(m, "btl definition")
            else:
                print_info(m, "mk variable")
        else:
            print_info(m, "mk variable")

        # $ Version found
        # At this point, m must be a match, otherwise this subfunction already returned None.
        # The match should be an integer defining the version number. There are however two cor-
        # ner cases:
        #     - String 'None'
        #     - String 'latest'
        #     - Integer '-1'
        # In these cases, the latest version number must be applied eventually. However, that's
        # not the responsibility of this function.
        assert m is not None
        version = m.group(1).replace(q, "").replace(dq, "").replace(" ", "")
        if version.lower() in ("none", "null"):
            return None
        if version.lower() == "latest":
            return "latest"
        if version == "-1":
            return -1
        try:
            v = int(version)
            return v
        except:
            purefunctions.printc(
                f"\nWARNING: Could not extract makefile interface version from: {q}{version}{q} "
                f"in:\n"
                f"{q}{filepath}{q}\n",
                color="warning",
            )
        return None

    @classmethod
    def __determine_makefile_interface_version(
        cls,
        rootpath: str,
        makefile_abspath: Optional[str],
        dashboard_mk_abspath: Optional[str],
        filetree_mk_abspath: Optional[str],
        with_engine: bool,
        callback: Optional[Callable],
    ) -> None:
        """
        :param rootpath:              Toplevel project folder
        :param makefile_abspath:      Path to makefile
        :param dashboard_mk_abspath:  Path to dashboard.mk
        :param filetree_mk_abspath:   Path to filetree.mk

        > callback(version_nr, show_apply_changes)

        RULES:
        1. If there is a version number in the makefile, use it.

        2. Otherwise, if there is a dashboard.mk and it has a version number, use it.

        3. Otherwise, if there is a .beetle folder and it has a version number, use it.

        4. Otherwise, if there is no dashboard.mk and no .beetle folder, assume that this is a non-
           beetle project and use the latest version.

        5. Otherwise, dashboard.mk or the .beetle folder exist, but neither of them has a version
           number. Assume that this is an old style beetle project and use version 1.
           => Don't do this anymore. Too dangerous.
        """
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]

        #! ========================[ STEP 1: EXTRACT ALL VERSION NUMBERS ]======================= !#
        show_apply_changes: bool = False
        # $ MAKEFILE
        makefile_content: Optional[str] = None
        makefile_exists: bool = False
        makefile_v: Optional[int] = None
        # Corner cases:
        #    - Custom makefiles have version 'None' (unless otherwise specified)
        #    - Old beetle makefiles have version 'None'

        # $ DASHBOARD.MK
        dashboard_mk_exists: bool = False
        dashboard_mk_v: Optional[int] = None
        # Corner cases:
        #    - Old 'dashboard.mk' files have version 'None'

        # $ FILETREE.MK
        filetree_mk_exists: bool = False
        filetree_mk_v: Optional[int] = None
        # Corner cases:
        #    - Old 'filetree.mk' files have version 'None'

        # $ .BEETLE FOLDER
        beetle_folder_exists: bool = False
        project_v: Optional[int] = None
        # Corner cases:
        #    - If no .beetle folder existed, version is 'None' (-1 => None)
        #    - Old .beetle folder has version '1' (None => 1)

        # $ LATEST INTERFACE VERSION
        latest_v: int = functions.get_latest_makefile_interface_version()

        # $ Consider makefile
        if _pp_.isfile(makefile_abspath):
            makefile_exists = True
            with open(
                makefile_abspath, "r", encoding="utf-8", newline="\n"
            ) as f:
                makefile_content = f.read()
            v = cls.__get_makefile_interface_version_from_file(makefile_abspath)
            if isinstance(v, str):
                if v.lower() == "none":
                    makefile_v = None
                elif v.lower() == "latest":
                    makefile_v = latest_v
            else:
                if v == -1:
                    makefile_v = latest_v
                else:
                    makefile_v = v
        else:
            makefile_abspath = None

        # $ Consider 'dashboard.mk'
        if _pp_.isfile(dashboard_mk_abspath):
            dashboard_mk_exists = True
            v = cls.__get_makefile_interface_version_from_file(
                dashboard_mk_abspath
            )
            if isinstance(v, str):
                if v.lower() == "none":
                    dashboard_mk_v = None
                elif v.lower() == "latest":
                    dashboard_mk_v = latest_v
            else:
                if v == -1:
                    dashboard_mk_v = latest_v
                else:
                    dashboard_mk_v = v
        else:
            dashboard_mk_abspath = None

        # $ Consider 'filetree.mk'
        if _pp_.isfile(filetree_mk_abspath):
            filetree_mk_exists = True
            v = cls.__get_makefile_interface_version_from_file(
                filetree_mk_abspath
            )
            if isinstance(v, str):
                if v.lower() == "none":
                    filetree_mk_v = None
                elif v.lower() == "latest":
                    filetree_mk_v = latest_v
            else:
                if v == -1:
                    filetree_mk_v = latest_v
                else:
                    filetree_mk_v = v
        else:
            filetree_mk_abspath = None

        # $ Consider .beetle folder
        dot_beetle_folder = _pp_.rel_to_abs(
            rootpath=rootpath,
            relpath=".beetle",
        )
        dashboard_cfg_abspath = _pp_.rel_to_abs(
            rootpath=rootpath, relpath=".beetle/dashboard_config.btl"
        )
        project_v = None
        if os.path.isfile(dashboard_cfg_abspath):
            v = cls.__get_makefile_interface_version_from_file(
                dashboard_cfg_abspath
            )
            if isinstance(v, str):
                if v.lower() == "none":
                    project_v = None
                elif v.lower() == "latest":
                    project_v = latest_v
            else:
                if v == -1:
                    project_v = latest_v
                else:
                    project_v = v
        if not os.path.isdir(dot_beetle_folder):
            beetle_folder_exists = False
            project_v = None
        else:
            beetle_folder_exists = True

        #! ==============================[ STEP 2: PREPARE POPUPS ]============================== !#
        h = data.get_general_font_height()
        w = data.get_general_font_width()
        icon = iconfunctions.get_rich_text_pixmap_middle(
            pixmap_relpath="icons/gen/certificate.png",
            width=int(h * 1.75),
        )

        def popup_common_text(
            title: str,
            files: List[str],
        ) -> str:
            assert ("dashboard.mk" in makefile_content) or (
                "filetree.mk" in makefile_content
            )
            if len(files) == 1:
                title_listing = files[0].upper()
            elif len(files) == 2:
                title_listing = f"{files[0]} AND {files[1]}".upper()
            elif len(files) == 3:
                title_listing = f"{files[0]}, {files[1]} AND {files[2]}".upper()
            else:
                assert False
            txt = f"""
            {css['h1']}{icon} {title} IN<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{title_listing}{css['/hx']}
            {css['h2']}1. Why do I get this popup?{css['/hx']}
            <p align='left'>
                This project’s makefile includes Embeetle{q}s {q}dashboard.mk{q} and/or<br>
                {q}filetree.mk{q}
            """
            if "makefile" in files:
                txt += f""",
                    but does not mention what version of these files it<br>
                    expects.
                </p>
                """
            else:
                txt += f""".
                </p>
                """
            txt += f"""
            <p align='left'>
                The interface of {q}dashboard.mk{q} and {q}filetree.mk{q} - the set of<br>
                variables they define for use in the makefile - is updated from<br>
                time to time with new versions of Embeetle. To avoid mismatches<br>
                between the makefile and {q}dashboard.mk{q} or {q}filetree.mk{q}, an<br>
                interface version was introduced in Embeetle version 0.2.0. If<br>
                the expected version is mentioned in the makefile, Embeetle will<br>
                generate a matching {q}dashboard.mk{q} and {q}filetree.mk{q} (or update<br>
                the existing ones).
            </p>
            """
            return txt

        def popup_no_version(
            applied_version: int,
            files: List[str],
        ) -> None:
            assert isinstance(applied_version, int)
            txt = popup_common_text(
                title="NO MAKEFILE INTERFACE VERSION",
                files=files,
            )
            txt += f"""
                {css['h2']}2. What should I do?{css['/hx']}
            """
            if "makefile" in files:
                txt += f"""
                <p align='left'>
                    To avoid getting this popup each time you open this project, add<br>
                    the following comment on a separate line anywhere in your<br>
                    makefile:<br>
                    {tab}{green}# Compatible with Embeetle makefile interface version {applied_version}{end}
                </p>
                """
            if "filetree.mk" in files:
                txt += f"""
                <p align="left">
                    Embeetle will overwrite your current {q}filetree.mk{q} to be<br>
                    compatible with Embeetle makefile interface version {blue}{applied_version}{end}
                </p>
                """
            if "dashboard.mk" in files:
                txt += f"""
                <p align="left">
                    When you click {q}Apply dashboard{q} in the dashboard, Embeetle<br>
                    will update your current {q}dashboard.mk{q} file. Thanks to our<br>
                    three-way-merge system, your own changes to {q}dashboard.mk{q}<br>
                    should be preserved.
                </p>
                """
            if with_engine:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/gen/dashboard.png",
                    title_text="makefile without interface version",
                    text=txt,
                )
            else:
                print(txt)
            return

        def popup_version_mismatch(
            applied_version: int,
            _mismatch_files: List[str],
            _unversioned_files: List[str],
        ) -> None:
            assert isinstance(applied_version, int)
            txt = popup_common_text(
                title="MAKEFILE INTERFACE VERSION MISMATCH",
                files=_mismatch_files,
            )
            txt += f"""
            {css['h2']}2. Where is the mismatch?{css['/hx']}
            <p align='left'>
                The extracted Embeetle makefile interface versions are:<br>
                {tab}- makefile: {blue}{makefile_v}{end}<br>
                {tab}- dashboard.mk: {blue}{dashboard_mk_v}{end}<br>
                {tab}- filetree.mk: {blue}{filetree_mk_v}{end}<br>
                {tab}- project: {blue}{project_v}{end}<br>
                <br>
                (Note: The latest Embeetle makefile interface version is: {blue}{latest_v}{end})
            </p>
            {css['h2']}3. What will happen?{css['/hx']}
            <p align="left">
                Embeetle will apply <i>makefile interface version {blue}{applied_version}{end}</i> on your project.<br>
                So 
            """
            temp = _mismatch_files + _unversioned_files
            if "makefile" in _mismatch_files:
                assert False
            if ("filetree.mk" in temp) and ("dashboard.mk" not in temp):
                txt += f"""
                    Embeetle will regenerate {q}filetree.mk{q} in the <i>makefile interface<br>
                    version {blue}{applied_version}{end}</i> format.
                </p>
                """
            elif ("filetree.mk" not in temp) and ("dashboard.mk" in temp):
                txt += f"""
                    when you click {q}Apply dashboard{q} in the dashboard, Embeetle<br>
                    will update your current {q}dashboard.mk{q} file. Thanks to our<br>
                    three-way-merge system, your own changes to {q}dashboard.mk{q}<br>
                    should be preserved.
                </p>
                """
            elif ("filetree.mk" in temp) and ("dashboard.mk" in temp):
                txt += f"""
                    when you click {q}Apply dashboard{q} in the dashboard, Embeetle<br>
                    will update your current {q}dashboard.mk{q} file. Thanks to our<br>
                    three-way-merge system, your own changes to {q}dashboard.mk{q}<br>
                    should be preserved.<br>
                    As for {q}filetree.mk{q}, Embeetle will regenerate this file in<br>
                    in the <i>Embeetle makefile interface version {blue}{applied_version}{end}</i> format.
                </p>
                """
            if "makefile" in _unversioned_files:
                txt += f"""
                {css['h2']}4. Should I do something?{css['/hx']}
                <p align='left'>
                    You did not mention the <i>Embeetle makefile interface version</i> in your<br>
                    makefile, so Embeetle deduced the version from another source<br>
                    (in this case, from {
                        'the dashboard.mk file' if applied_version == dashboard_mk_v else
                        'the filetree.mk file' if applied_version == filetree_mk_v else
                        'the version stored in the .beetle folder' if applied_version == project_v else
                        'NONE'
                    })<br>
                    To avoid future confusions, add the following comment on a<br>
                    separate line anywhere in your makefile:<br>
                    {tab}{green}# Compatible with Embeetle makefile interface version {applied_version}{end}
                </p>
                """
            if with_engine:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/gen/dashboard.png",
                    title_text="version mismatch",
                    text=txt,
                )
            else:
                print(txt)
            return

        def popup_unsupported_version(_highest_v: int, _latest_v: int) -> None:
            text = f"""
            {css['h1']}{icon} NON-SUPPORTED EMBEETLE PROJECT{css['/hx']}
            {css['h2']}1. Why do I get this popup?{css['/hx']}
            <p align='left'>
                The interface of {q}dashboard.mk{q} and {q}filetree.mk{q} - the set of<br>
                variables they define for use in the makefile - is updated from<br>
                time to time with new versions of Embeetle. To avoid mismatches<br>
                between the makefile and {q}dashboard.mk{q} or {q}filetree.mk{q}, an<br>
                interface version was introduced in Embeetle version 0.2.0. If<br>
                the expected version is mentioned in the makefile, Embeetle will<br>
                generate a matching {q}dashboard.mk{q} and {q}filetree.mk{q} (or update<br>
                the existing ones).
            </p>
            <p align='left'>
                The beetle discovered that one or more of the project files<br>
                comply with <i>Embeetle makefile interface version {blue}{_highest_v}{end}</i>. However, your<br>
                current Embeetle installation can only handle projects with <i>makefile<br>
                interface version {blue}{_latest_v}{end}</i>.<br>
            </p>
            {css['h2']}2. What should I do?{css['/hx']}
            <p align='left'>
                Close this project and go back to the Embeetle Home Window. You<br>
                should see an update ready to download. If not, please contact<br>
                us.
            </p>
            """
            if with_engine:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/gen/dashboard.png",
                    title_text="non-supported Embeetle project",
                    text=text,
                )
            else:
                print(text)
            return

        #! ===============================[ STEP 3: APPLY RULES ]================================ !#
        # * ---[ RULE 0: We don't support forward compatibility yet.]--- *#
        highest_v = 0
        if (makefile_v is not None) and (makefile_v > highest_v):
            highest_v = makefile_v
        if (dashboard_mk_v is not None) and (dashboard_mk_v > highest_v):
            highest_v = dashboard_mk_v
        if (filetree_mk_v is not None) and (filetree_mk_v > highest_v):
            highest_v = filetree_mk_v
        if (project_v is not None) and (project_v > highest_v):
            highest_v = project_v
        if highest_v > latest_v:
            popup_unsupported_version(highest_v, latest_v)
            return

        # * ---[ RULE 1: If there is a version nr in the makefile, use it. ]---*#
        if makefile_exists and (makefile_v is not None):
            # Collect and report version mismatches and unversioned files.
            unversioned_files = []
            mismatch_files = []
            # $ Observe 'dashboard.mk'
            if (
                dashboard_mk_exists
                and (dashboard_mk_v is None)
                and ("dashboard.mk" in makefile_content)
            ):
                unversioned_files.append("dashboard.mk")
            elif (
                dashboard_mk_exists
                and (dashboard_mk_v is not None)
                and (dashboard_mk_v != makefile_v)
                and ("dashboard.mk" in makefile_content)
            ):
                mismatch_files.append("dashboard.mk")
            # $ Observe 'filetree.mk'
            if (
                filetree_mk_exists
                and (filetree_mk_v is None)
                and ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("filetree.mk")
            elif (
                filetree_mk_exists
                and (filetree_mk_v is not None)
                and (filetree_mk_v != makefile_v)
                and ("filetree.mk" in makefile_content)
            ):
                mismatch_files.append("filetree.mk")
            # $ Should 'APPLY DASHBOARD CHANGES' banner appear?
            if ("dashboard.mk" in unversioned_files) or (
                "dashboard.mk" in mismatch_files
            ):
                show_apply_changes = True
            # $ Show popup if needed
            if len(mismatch_files) > 0:
                popup_version_mismatch(
                    applied_version=makefile_v,
                    _mismatch_files=mismatch_files,
                    _unversioned_files=unversioned_files,
                )
            elif len(unversioned_files) > 0:
                popup_no_version(
                    applied_version=makefile_v,
                    files=unversioned_files,
                )
            # For all other cases, no warning will be shown.
            callback(makefile_v, show_apply_changes)
            return

        # When reaching this point, the makefile may or may not exist, but its
        # version is certainly None!
        assert makefile_v is None

        # * ---[ RULE 2: If there is a 'dashboard.mk' and it has a version nr, use it. ]--- *#
        if dashboard_mk_exists and (dashboard_mk_v is not None):
            # Collect and report version mismatches and unversioned files.
            unversioned_files = []
            mismatch_files = []
            # $ Observe makefile
            if makefile_exists and (
                ("dashboard.mk" in makefile_content)
                or ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("makefile")
            # $ Observe 'filetree.mk'
            if (
                filetree_mk_exists
                and makefile_exists
                and (filetree_mk_v is None)
                and ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("filetree.mk")
            elif (
                filetree_mk_exists
                and makefile_exists
                and (filetree_mk_v is not None)
                and (filetree_mk_v != dashboard_mk_v)
                and ("filetree.mk" in makefile_content)
            ):
                mismatch_files.append("filetree.mk")
            # $ Should 'APPLY DASHBOARD CHANGES' banner appear?
            if "dashboard.mk" in unversioned_files:
                show_apply_changes = True
            # $ Show popup if needed
            if len(mismatch_files) > 0:
                popup_version_mismatch(
                    applied_version=dashboard_mk_v,
                    _mismatch_files=mismatch_files,
                    _unversioned_files=unversioned_files,
                )
            elif len(unversioned_files) > 0:
                popup_no_version(
                    applied_version=dashboard_mk_v,
                    files=unversioned_files,
                )
            # For all other cases, no warning will be shown.
            callback(dashboard_mk_v, show_apply_changes)
            return

        # When reaching this point, 'dashboard.mk' may or may not exist, but its
        # version is certainly None!
        assert dashboard_mk_v is None

        # * ---[ RULE 2b: If there is a 'filetree.mk' and it has a version nr, use it. ]--- *#
        if filetree_mk_exists and (filetree_mk_v is not None):
            # Collect and report version mismatches and unversioned files.
            unversioned_files = []
            mismatch_files = []
            # $ Observe makefile
            if makefile_exists and (
                ("dashboard.mk" in makefile_content)
                or ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("makefile")
            # $ Observe 'dashboard.mk'
            if (
                dashboard_mk_exists
                and makefile_exists
                and ("dashboard.mk" in makefile_content)
            ):
                unversioned_files.append("dashboard.mk")
            # $ Should 'APPLY DASHBOARD CHANGES' banner appear?
            if "dashboard.mk" in unversioned_files:
                show_apply_changes = True
            # $ Show popup if needed
            if len(mismatch_files) > 0:
                popup_version_mismatch(
                    applied_version=filetree_mk_v,
                    _mismatch_files=mismatch_files,
                    _unversioned_files=unversioned_files,
                )
            elif len(unversioned_files) > 0:
                popup_no_version(
                    applied_version=filetree_mk_v,
                    files=unversioned_files,
                )
            # For all other cases, no warning will be shown.
            callback(filetree_mk_v, show_apply_changes)
            return

        # When reaching this point, 'filetree.mk' may or may not exist, but its
        # version is certainly None!
        assert filetree_mk_v is None

        # * ---[ RULE 3: If there is a '.beetle' folder and it has a version nr, use it. ]--- *#
        if beetle_folder_exists and (project_v is not None):
            # Collect and report unversioned files
            unversioned_files = []
            # $ Observe makefile
            if makefile_exists and (
                ("dashboard.mk" in makefile_content)
                or ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("makefile")
            # $ Observe 'dashboard.mk'
            if (
                dashboard_mk_exists
                and makefile_exists
                and ("dashboard.mk" in makefile_content)
            ):
                unversioned_files.append("dashboard.mk")
            # $ Observe 'filetree.mk'
            if (
                filetree_mk_exists
                and makefile_exists
                and ("filetree.mk" in makefile_content)
            ):
                unversioned_files.append("filetree.mk")
            # $ Should 'APPLY DASHBOARD CHANGES' banner appear?
            if "dashboard.mk" in unversioned_files:
                show_apply_changes = True
            # $ Show popup if needed
            if len(unversioned_files) > 0:
                popup_no_version(
                    applied_version=project_v,
                    files=unversioned_files,
                )
            # For all other cases, no warning will be shown.
            callback(project_v, show_apply_changes)
            return

        # When reaching this point, the '.beetle' folder may or may not exist,
        # but its version is certainly None!
        assert project_v is None

        # * ---[ RULE 4: If there is no 'dashboard.mk', no 'filetree.mk' and no '.beetle' folder
        # *               => use latest ]--- *#
        if (
            (not dashboard_mk_exists)
            and (not filetree_mk_exists)
            and (not beetle_folder_exists)
        ):
            # $ Always show 'APPLY DASHBOARD CHANGES' banner?
            show_apply_changes = True
            # $ Observe makefile
            if makefile_exists and (
                ("dashboard.mk" in makefile_content)
                or ("filetree.mk" in makefile_content)
            ):
                popup_no_version(
                    applied_version=latest_v,
                    files=[
                        "makefile",
                    ],
                )
            # For all other cases, no warning will be shown.
            callback(latest_v, show_apply_changes)
            return

        # * ---[ RULE 5: 'dashboard.mk' and/or 'filetree.mk' and/or '.beetle' folder exist,
        # *              but neither has a version nr => use version 1 ]--- *#
        # Do not apply this rule anymore. It is too dangerous.
        show_apply_changes = True
        callback(latest_v, show_apply_changes)
        return
