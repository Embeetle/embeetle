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
import os, threading, functools, traceback
import qt, data, purefunctions, functions
import gui.helpers.various
from components.singleton import Singleton
import hardware_api.treepath_unicum as _treepath_unicum_
import project_generator.generator.file_changer as _fc_
import helpdocs.help_texts as _ht_
import bpathlib.file_power as _fp_
import bpathlib.path_power as _pp_

if TYPE_CHECKING:
    import project.project as _project_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
from various.kristofstuff import *


class DashboardWorker(metaclass=Singleton):
    """Worker object for the Dashboard, in analogy to the one for the Filetree.

    Right now, the tasks are not computationally intensive enough to do them in
    a separate thread.
    """

    def __init__(self) -> None:
        """"""
        super().__init__()
        assert threading.current_thread() is threading.main_thread()
        return

    # ^                                        APPLY DASHBOARD                                         ^#
    # % ============================================================================================== %#
    # % This is the toplevel function to apply all changes in the dashboard.                           %#
    # %                                                                                                %#

    def apply_dashboard(
        self,
        impacted_files: List[str],
        ask_permissions: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Analyze the 'impactedFiles' based on CONTENT and NAME. Both content
        and name must comply with current Project()-instance settings (eg.
        chip/probe name, ...).

         The following dictionaries get filled and passed to _ht_.ask_dashboard_permission():

        ╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
        ║  PERMISSION DICTIONARIES                                                                                   ║
        ║                                                                                                            ║
        ║                 ┌───────────┐  ┌────────────────────────────────────────────────────────────────────────┐  ║
        ║                 │unicum name│  │  file abspath  │ diff   │ chbx  │ confl │ cur_cont │ res_cont │ man_mod│  ║
        ║                 └───────────┘  └────────────────────────────────────────────────────────────────────────┘  ║
        ║  addperm_dict >  'MAKEFILE' : [ 'C:/../makefile', ''     , False ]                                         ║
        ║  delperm_dict >  'MAKEFILE' : [ 'C:/../makefile', ''     , False ]                                         ║
        ║  modperm_dict >  'MAKEFILE' : [ 'C:/../makefile', '3.5%' , False , True  , 'abc...' , 'abc...' , True ]    ║
        ║                                                                                                            ║
        ║                 ┌───────────┐ ┌─────────────────────────────────────────┐                                  ║
        ║                 │unicum name│ │  from_abspath   |  to_abspath   │ chbx  │                                  ║
        ║                 └───────────┘ └─────────────────────────────────────────┘                                  ║
        ║  repperm_dict >  'MAKEFILE' : [ 'C:/../frompath', 'C:/../topath', False ]                                  ║
        ║                                                                                                            ║
        ╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

         NOTE:
         Q: Why is the 'BOOTLOADER_FILE' never offered for deletion, even when you switch to a probe
            that makes this file irrelevant?
         A: The file is simply nowhere added to the 'impactedFiles' listing.
        """
        assert threading.current_thread() is threading.main_thread()
        origthread: qt.QThread = qt.QThread.currentThread()
        addperm_dict: Dict[str, List[Union[str, bool]]] = {}
        delperm_dict: Dict[str, List[Union[str, bool]]] = {}
        modperm_dict: Dict[str, List[Union[str, bool]]] = {}
        repperm_dict: Dict[str, List[Union[str, bool]]] = {}
        impacted_file_unicums: List[_treepath_unicum_.TREEPATH_UNIC] = [
            _treepath_unicum_.TREEPATH_UNIC(f) for f in impacted_files
        ]

        def analyze_content_and_name(
            repperm_only: bool, cb: Callable, cba: Any, *args
        ) -> None:
            # This function gets called from 'save_procedure_01()' and 'save_procedure_02()'. It
            # analyzes all impacted files and saves the results to 'addperm_dict', 'delperm_dict',
            # 'modperm_dict' and 'repperm_dict'. First it's invoked with the focus on repoints only.
            # Then it's invoked for the general case.
            assert qt.QThread.currentThread() is origthread
            nonlocal addperm_dict, delperm_dict, modperm_dict, repperm_dict

            def analysis_complete(
                _addperm_dict_: Dict[str, List[Union[str, bool]]],
                _delperm_dict_: Dict[str, List[Union[str, bool]]],
                _modperm_dict_: Dict[str, List[Union[str, bool]]],
                _repperm_dict_: Dict[str, List[Union[str, bool]]],
                *_args,
            ) -> None:
                assert qt.QThread.currentThread() is origthread
                nonlocal addperm_dict, delperm_dict, modperm_dict, repperm_dict
                addperm_dict = _addperm_dict_
                delperm_dict = _delperm_dict_
                modperm_dict = _modperm_dict_
                repperm_dict = _repperm_dict_
                cb(cba)
                return

            self.__analyze_content_and_name__(
                _impactedFiles_=impacted_file_unicums,
                _addperm_dict_=addperm_dict,
                _delperm_dict_=delperm_dict,
                _modperm_dict_=modperm_dict,
                _repperm_dict_=repperm_dict,
                repperm_only=repperm_only,
                callback=analysis_complete,
                callbackArg=None,
            )
            return

        def save_procedure_01(*args) -> None:
            # Analyze all impacted files, and save the results to 'addperm_dict', 'delperm_dict',
            # 'modperm_dict' and 'repperm_dict' dictionaries. But focus only on repoints.
            assert qt.QThread.currentThread() is origthread
            if len(impacted_file_unicums) == 0:
                finish()
                return
            analyze_content_and_name(
                repperm_only=True,
                cb=save_procedure_02,
                cba=None,
            )
            return

        def save_procedure_02(*args) -> None:
            # Analyze all impacted files, and save the results to the local 'addperm_dict',
            # 'delperm_dict', 'modperm_dict' and 'repperm_dict' dictionaries.
            assert qt.QThread.currentThread() is origthread
            analyze_content_and_name(
                repperm_only=False,
                cb=save_procedure_03,
                cba=None,
            )
            return

        def save_procedure_03(*args) -> None:
            # If the 'ask_permissions' parameter is set, jump to the 'ask_permission()' subfunction.
            # Otherwise, jump to 'grant_permission()'.
            assert qt.QThread.currentThread() is origthread
            if (
                len(addperm_dict)
                + len(delperm_dict)
                + len(modperm_dict)
                + len(repperm_dict)
            ) == 0:
                finish()
                return
            if not ask_permissions:
                grant_permission()
                return
            ask_permission()
            return

        def grant_permission(*args) -> None:
            # Force all 'checkboxes' to be ticked.
            assert qt.QThread.currentThread() is origthread
            for key in addperm_dict.keys():
                assert isinstance(addperm_dict[key][2], bool)
                addperm_dict[key][2] = True
            for key in delperm_dict.keys():
                assert isinstance(delperm_dict[key][2], bool)
                delperm_dict[key][2] = True
            for key in modperm_dict.keys():
                assert isinstance(modperm_dict[key][2], bool)
                modperm_dict[key][2] = True
            for key in repperm_dict.keys():
                assert isinstance(repperm_dict[key][2], bool)
                repperm_dict[key][2] = True
            apply_permitted_changes(
                _addperm_dict_=addperm_dict,
                _delperm_dict_=delperm_dict,
                _modperm_dict_=modperm_dict,
                _repperm_dict_=repperm_dict,
                _diff_dialog_=None,
            )
            return

        def ask_permission(*args) -> None:
            # Let the user tick the checkboxes.
            assert qt.QThread.currentThread() is origthread
            _ht_.ask_dashboard_permission(
                addperm_dict=addperm_dict,
                delperm_dict=delperm_dict,
                modperm_dict=modperm_dict,
                repperm_dict=repperm_dict,
                title_text=None,
                callback=apply_permitted_changes,
            )
            return

        def apply_permitted_changes(
            _addperm_dict_: Dict[str, List[Union[str, bool]]],
            _delperm_dict_: Dict[str, List[Union[str, bool]]],
            _modperm_dict_: Dict[str, List[Union[str, bool]]],
            _repperm_dict_: Dict[str, List[Union[str, bool]]],
            _diff_dialog_: Optional[gui.helpers.various.DiffDialog],
        ) -> None:
            # Apply all changes for which the checkbox has been ticked.
            assert qt.QThread.currentThread() is origthread
            if _diff_dialog_ is not None:
                _diff_dialog_.close()
            if any(
                d is None
                for d in (
                    _addperm_dict_,
                    _delperm_dict_,
                    _modperm_dict_,
                    _repperm_dict_,
                )
            ):
                abort()
                return

            def apply_next_repoint(key_iter: Iterator[str]) -> None:
                # Apply the next file repoint. Which file to repoint is extracted from the
                # '_repperm_dict_' with the next key from the iterator.
                assert qt.QThread.currentThread() is origthread
                try:
                    key: str = next(key_iter)
                except StopIteration:
                    apply_next_addition(None, iter(_addperm_dict_.keys()))
                    return
                treepath_unic: _treepath_unicum_.TREEPATH_UNIC = (
                    _treepath_unicum_.TREEPATH_UNIC(key)
                )
                frompath: Optional[str] = _repperm_dict_[key][0]
                topath: Optional[str] = _repperm_dict_[key][1]
                perm: bool = _repperm_dict_[key][2]
                if perm:
                    # repoint
                    data.current_project.get_treepath_seg().set_abspath(
                        unicum=treepath_unic,
                        abspath=topath,
                        history=False,
                        refresh=False,
                        callback=apply_next_repoint,
                        callbackArg=key_iter,
                    )
                    return
                # no permission
                apply_next_repoint(key_iter)
                return

            def apply_next_addition(
                file_data: Optional[
                    Dict[
                        str,
                        Union[None, str, bool, int, Dict[str, Optional[str]]],
                    ]
                ],
                key_iter: Iterator[str],
            ) -> None:
                # Apply the next file addition. Which file to add is extracted from the '_addperm_
                # dict_' with the next key from the iterator. The 'file_data' parameter is merely
                # an artifact from the previous run of this sub-subfunction.
                assert qt.QThread.currentThread() is origthread
                try:
                    key = next(key_iter)
                except StopIteration:
                    apply_next_deletion(iter(_delperm_dict_.keys()))
                    return
                treepath_unic: _treepath_unicum_.TREEPATH_UNIC = (
                    _treepath_unicum_.TREEPATH_UNIC(key)
                )
                filepath: Optional[str] = _addperm_dict_[key][0]
                perm: bool = _addperm_dict_[key][2]
                if perm:
                    # create empty file
                    assert not os.path.isfile(
                        filepath
                    ), f"Filepath {filepath} already exists"
                    _fp_.make_file(filepath)
                    assert os.path.isfile(filepath)
                    # fresh content -> must use the 'change_file_content()' function to ensure
                    #                  proper file gets stored in .config_orig folder!
                    _fc_.FileChanger().change_file_content(
                        version=None,
                        file_unicum=treepath_unic,
                        abspath=filepath,
                        repoints=None,
                        dry_run=False,
                        force_new_content=False,
                        callback=apply_next_addition,
                        callbackArg=key_iter,
                    )
                    return
                # no permission
                apply_next_addition(None, key_iter)
                return

            def apply_next_deletion(key_iter: Iterator[str]) -> None:
                # Apply the next file deletion. Which file to delete is extracted from the
                # '_delperm_dict_' with the next key from the iterator.
                assert qt.QThread.currentThread() is origthread
                try:
                    key = next(key_iter)
                except StopIteration:
                    apply_next_mod(None, iter(_modperm_dict_.keys()))
                    return
                treepath_unic: _treepath_unicum_.TREEPATH_UNIC = (
                    _treepath_unicum_.TREEPATH_UNIC(key)
                )
                filepath: Optional[str] = _delperm_dict_[key][0]
                perm: bool = _delperm_dict_[key][2]
                if perm:
                    # delete file
                    assert os.path.isfile(filepath), str(
                        f"ERROR: Need to delete {q}{filepath}{q} "
                        f"but cannot find it."
                    )
                    _fp_.delete_file(filepath)
                    assert not os.path.isfile(filepath)
                apply_next_deletion(key_iter)
                return

            def apply_next_mod(
                file_data: Optional[
                    Dict[
                        str,
                        Union[None, str, bool, int, Dict[str, Optional[str]]],
                    ]
                ],
                key_iter: Iterator[str],
            ) -> None:
                # Apply the next file modification. Which file to modify is extracted from the
                # '_modperm_dict_' with the next key from the iterator. The 'file_data' parameter is
                # merely an artifact from the previous run of this sub-subfunction.
                assert qt.QThread.currentThread() is origthread
                try:
                    key = next(key_iter)
                except StopIteration:
                    finish()
                    return
                treepath_unic: _treepath_unicum_.TREEPATH_UNIC = (
                    _treepath_unicum_.TREEPATH_UNIC(key)
                )
                filepath: Optional[str] = _modperm_dict_[key][0]
                perm: bool = _modperm_dict_[key][2]
                if perm:
                    # change file
                    assert os.path.isfile(filepath)
                    _fc_.FileChanger().change_file_content(
                        version=None,
                        file_unicum=treepath_unic,
                        abspath=filepath,
                        repoints=None,
                        dry_run=False,
                        force_new_content=False,
                        callback=apply_next_mod,
                        callbackArg=key_iter,
                    )
                    return
                # no permission
                apply_next_mod(None, key_iter)
                return

            apply_next_repoint(iter(_repperm_dict_.keys()))
            return

        def finish(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            try:
                data.main_form.parse_buttons()
            except AttributeError as e:
                pass
            if callback is not None:
                callback(True, callbackArg)
            return

        def abort(*args) -> None:
            # First callback arg is 'False'
            #     -> Project().save_later() aborts too
            #     -> inner func '_reset_projsegments_history_baseline_()' never runs
            assert qt.QThread.currentThread() is origthread
            if callback is not None:
                callback(False, callbackArg)
            return

        # * Start
        assert qt.QThread.currentThread() is origthread
        for f in impacted_file_unicums:
            assert isinstance(f, _treepath_unicum_.TREEPATH_UNIC)
        # Copy config files to .orig_config folder (if there is no copy yet).
        # self.save_orig_cfgfiles(
        #     callback    = save_procedure_01,
        #     callbackArg = None,
        # )
        # I do this now at project startup!
        save_procedure_01()
        return

    # ^                                         HELP FUNCTIONS                                         ^#
    # % ============================================================================================== %#
    # % Help functions to analyze config files.                                                        %#
    # %                                                                                                %#

    def __analyze_content_and_name__(
        self,
        _impactedFiles_: List[_treepath_unicum_.TREEPATH_UNIC],
        _addperm_dict_: Dict[str, List],
        _delperm_dict_: Dict[str, List],
        _modperm_dict_: Dict[str, List],
        _repperm_dict_: Dict[str, List],
        repperm_only: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        GOAL:
        =====
        Analyze the impacted files:
            - Analyze file path for existence.
            - Analyze file name and a suggest another one if illegal.
            - Check file on relevance.
            - Compare file content to merged content (obtained from a dry-run-merge) and evaluate
              the difference.

        The analysis results in filling up the permission dictionaries. That should make them ready
        for asking permission.

        NOTE:
        The 'repperm_only' parameter dictates if this function must only adapt repoints. In fact,
        this function should run twice: once with and once without this parameter set.

        MECHANISM:
        ==========
        For each TreepathObj() in 'impactedFiles', extract:
        - disppath: the path as displayed in the dashboard
        - diskpath: the actual path on disk (autolocated)

        Based on that, figure out the CASE:
            ┌───────────┬──────────────────────────────┐
            │ disppath  │  diskpath                    │
            ╞═══════════╪══════════════════════════════╡
            │           │  File absent                 │ <- CASE 1
            │ None      │╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│
            │           │  File exists                 │ <- CASE 2
            ├───────────┼──────────────────────────────┤
            │           │  File absent                 │ <- CASE 3
            │           │╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│
            │ some_path │  File exists, correct loc    │ <- CASE 4
            │           │╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│
            │           │  File exists, incorrect loc  │ <- CASE 5
            └───────────┴──────────────────────────────┘

        CASE 1: 'None' displayed and file absent(*)
        (* nothing found with autolocation)
            If relevant, ask permission to add the given file.

        CASE 2: 'None' displayed but file exists(*)
        (* found with autolocation)
            If relevant, ask permission to point to the file and to modify it.
            If irrelevant, ask permission to delete the file.

        CASE 3: Path displayed but file absent(*)
        (* nothing found with autolocation)
            If relevant, ask permission to add the file.
            If irrelevant, ask permission to clear the pointer.

        CASE 4: Path displayed and file exists there
            If relevant, ask permission to modify the file.
            If irrelevant, ask permission to delete the file and clear the pointer.

        CASE 5: Path displayed but file exists elsewhere(*)
        (* found with autolocation)
            If relevant, ask permission to repoint to and then modify the file.
            If irrelevant, ask permission to delete the file and clear the pointer.

        > callback(
            _addperm_dict_,
            _delperm_dict_,
            _modperm_dict_,
            _repperm_dict_,
            callbackArg,
        )
        """
        origthread: qt.QThread = qt.QThread.currentThread()
        projObj: _project_.Project = data.current_project
        treepath_seg: _treepath_seg_.TreepathSeg = projObj.get_treepath_seg()
        disppath: Optional[str] = None
        file_unicum: Optional[_treepath_unicum_.TREEPATH_UNIC] = None

        def next_impacted_file_a(
            file_unicum_iter: Iterator[_treepath_unicum_.TREEPATH_UNIC],
        ) -> None:
            # Start processing next impacted file from the iterator. The first step is determining
            # the 'disppath' and 'diskpath'.
            assert qt.QThread.currentThread() is origthread
            try:
                nonlocal file_unicum
                file_unicum = next(file_unicum_iter)
            except StopIteration:
                finish()
                return
            assert isinstance(file_unicum, _treepath_unicum_.TREEPATH_UNIC)

            # $ DISPLAY PATH
            nonlocal disppath
            disppath = _pp_.standardize_abspath(
                treepath_seg.get_abspath(file_unicum)
            )

            # $ DISK PATH
            # Important: the autolocate function can return a 'default fallback' path to an empty
            # location!
            treepath_seg.autolocate(
                unicum=file_unicum,
                force=False,
                adapt=False,
                history=False,
                callback=next_impacted_file_b,
                callbackArg=file_unicum_iter,
            )
            return

        def next_impacted_file_b(
            diskpath: Optional[str],
            file_unicum_iter: Iterator[_treepath_unicum_.TREEPATH_UNIC],
            *args,
        ) -> None:
            # At this point, the 'disppath' and 'diskpath' are both known for the impacted file
            # being investigated in this iterator-cycle. Define the five cases on how to deal with
            # the file.
            if (diskpath is not None) and (diskpath.lower() != "none"):
                if not os.path.isfile(diskpath):
                    # Create empty file
                    _fp_.make_file(
                        file_abspath=diskpath,
                        printfunc=None,
                        catch_err=False,
                        overwr=False,
                    )
            # Now diskpath is either None/'None' or a path to an existing file.

            #! ---------------------------------- DEFINE CASES ---------------------------------- !#
            def case_01(*_args) -> None:
                # & None displayed, file absent(*)
                # (* Nothing found with autolocation)
                # If relevant, ask permission to add the given file at its default location and move
                # the pointer there. If irrelevant, ignore the file.
                assert qt.QThread.currentThread() is origthread

                # $ RELEVANT
                if treepath_seg.is_relevant(file_unicum):
                    new_path = treepath_seg.get_default_abspath(
                        unicum=file_unicum
                    )
                    if not os.path.isfile(new_path):
                        if not repperm_only:
                            _addperm_dict_[file_unicum.get_name()] = [
                                new_path,
                                "",
                                False,
                            ]
                    else:
                        purefunctions.printc(
                            f"WARNING: new_path = {q}{new_path}{q} "
                            f"already exists for {file_unicum.get_name()} "
                            f"but wasn{q}t found by autolocate function.",
                            color="warning",
                        )
                    _repperm_dict_[file_unicum.get_name()] = [
                        "None",
                        new_path,
                        False,
                    ]

                # $ IRRELEVANT
                else:
                    # repoint to None -> is already None
                    # delete -> doesn't exist
                    pass

                next_impacted_file_a(file_unicum_iter)
                return

            def case_02(*_args) -> None:
                # & None displayed, file exists(*)
                # (* Found with autolocation at 'diskpath')
                # If relevant, ask permission to point to 'diskpath' and to modify the file. If ir-
                # relevant, ask permission to delete the file.
                assert qt.QThread.currentThread() is origthread
                assert os.path.isfile(diskpath)
                # Note: The found file at 'diskpath' is already checked for (filename?) validity in
                # autolocate() function.

                def case_02_finish(
                    file_data: Dict[
                        str,
                        Union[None, str, bool, int, Dict[str, Optional[str]]],
                    ],
                    *_args_,
                ) -> None:
                    assert qt.QThread.currentThread() is origthread
                    diff = file_data["diff"]
                    if diff != 0:
                        _modperm_dict_[file_unicum.get_name()] = [
                            diskpath,
                            f"{diff}%",
                            False,
                            file_data["has_conflicts"],
                            file_data["cur_content"],
                            file_data["res_content"],
                            False,
                        ]
                    _repperm_dict_[file_unicum.get_name()] = [
                        "None",
                        diskpath,
                        False,
                    ]
                    next_impacted_file_a(file_unicum_iter)
                    return

                # $ RELEVANT
                if treepath_seg.is_relevant(file_unicum):
                    if not repperm_only:
                        # Ask permission to repoint and to modify the file.
                        _fc_.FileChanger().change_file_content(
                            version=None,
                            file_unicum=file_unicum,
                            abspath=diskpath,
                            repoints=_repperm_dict_,
                            dry_run=True,
                            force_new_content=False,
                            callback=case_02_finish,
                            callbackArg=None,
                        )
                        return
                    _repperm_dict_[file_unicum.get_name()] = [
                        "None",
                        diskpath,
                        False,
                    ]

                # $ IRRELEVANT
                else:
                    # repoint to None -> is already None
                    # delete -> yes (file exists at 'diskpath')
                    if not repperm_only:
                        _delperm_dict_[file_unicum.get_name()] = [
                            diskpath,
                            "",
                            False,
                        ]

                next_impacted_file_a(file_unicum_iter)
                return

            def case_03(*_args) -> None:
                # & Something displayed, file absent(*)
                # (* Nothing found with autolocation)
                # If relevant, ask permission to add the file. Otherwise, ask permission to clear
                # the pointer.
                assert qt.QThread.currentThread() is origthread

                # $ RELEVANT
                if treepath_seg.is_relevant(file_unicum):
                    if not os.path.isfile(disppath):
                        if not repperm_only:
                            _addperm_dict_[file_unicum.get_name()] = [
                                disppath,
                                "",
                                False,
                            ]
                    else:
                        purefunctions.printc(
                            f"WARNING: disppath = {q}{disppath}{q} already exists "
                            f"for {file_unicum.get_name()} but wasn{q}t found by "
                            f"autolocate function.",
                            color="warning",
                        )

                # $ IRRELEVANT
                else:
                    # repoint to None -> yes
                    _repperm_dict_[file_unicum.get_name()] = [
                        disppath,
                        "None",
                        False,
                    ]
                    # delete -> yes ('diskpath' doesn't exist, 'disppath' might)
                    if os.path.isfile(disppath):
                        if not repperm_only:
                            _delperm_dict_[file_unicum.get_name()] = [
                                disppath,
                                "",
                                False,
                            ]

                next_impacted_file_a(file_unicum_iter)
                return

            def case_04(*_args) -> None:
                # & Something displayed, file exists there
                # diskpath == disppath
                # If relevant, ask permission to modify the file. Otherwise, ask permission to de-
                # lete the file and clear the pointer.
                assert qt.QThread.currentThread() is origthread

                def case_04_finish(
                    file_data: Dict[
                        str,
                        Union[None, str, bool, int, Dict[str, Optional[str]]],
                    ],
                    *_args_,
                ) -> None:
                    assert qt.QThread.currentThread() is origthread
                    diff = file_data["diff"]
                    if diff != 0:
                        _modperm_dict_[file_unicum.get_name()] = [
                            disppath,
                            f"{diff}%",
                            False,
                            file_data["has_conflicts"],
                            file_data["cur_content"],
                            file_data["res_content"],
                            False,
                        ]
                    next_impacted_file_a(file_unicum_iter)
                    return

                assert os.path.isfile(diskpath)
                # The found file at 'diskpath' is already checked for validity in autolocate() func-
                # tion.

                # $ RELEVANT
                if treepath_seg.is_relevant(file_unicum):
                    if not repperm_only:
                        # Ask permission to modify the file (will be done in the
                        # callback).
                        _fc_.FileChanger().change_file_content(
                            version=None,
                            file_unicum=file_unicum,
                            abspath=diskpath,
                            repoints=_repperm_dict_,
                            dry_run=True,
                            force_new_content=False,
                            callback=case_04_finish,
                            callbackArg=None,
                        )
                        return
                    else:
                        # Nothing to do
                        pass

                # $ IRRELEVANT
                else:
                    # repoint to None -> yes
                    _repperm_dict_[file_unicum.get_name()] = [
                        disppath,
                        "None",
                        False,
                    ]
                    # delete -> yes (file exists at 'diskpath' == 'disppath')
                    if not repperm_only:
                        _delperm_dict_[file_unicum.get_name()] = [
                            disppath,
                            "",
                            False,
                        ]
                next_impacted_file_a(file_unicum_iter)
                return

            def case_05(*_args) -> None:
                # & Something displayed, file exists elsewhere(*)
                # (* found with autolocation)
                # diskpath != disppath
                # If relevant, ask permission to repoint to - and then modify - the file. Otherwise,
                # ask permission to delete the file and clear the pointer.
                assert qt.QThread.currentThread() is origthread

                def case_05_finish(
                    file_data: Dict[
                        str,
                        Union[None, str, bool, int, Dict[str, Optional[str]]],
                    ],
                    *_args_,
                ) -> None:
                    assert qt.QThread.currentThread() is origthread
                    diff = file_data["diff"]
                    if diff != 0:
                        _modperm_dict_[file_unicum.get_name()] = [
                            diskpath,
                            f"{diff}%",
                            False,
                            file_data["has_conflicts"],
                            file_data["cur_content"],
                            file_data["res_content"],
                            False,
                        ]
                    _repperm_dict_[file_unicum.get_name()] = [
                        disppath,
                        diskpath,
                        False,
                    ]
                    if os.path.isfile(disppath):
                        # Note: It is possible that there is *also* a file at the 'disppath' loca-
                        # tion. That one should be deleted.
                        if not repperm_only:
                            _delperm_dict_[file_unicum.get_name()] = [
                                disppath,
                                "",
                                False,
                            ]
                    next_impacted_file_a(file_unicum_iter)
                    return

                assert os.path.isfile(diskpath)
                # The found file at 'diskpath' is already checked for validity in autolocate() func-
                # tion.

                # $ RELEVANT
                if treepath_seg.is_relevant(file_unicum):
                    if not repperm_only:
                        # Ask permission to modify the file (will be done in the callback) and to
                        # repoint (also in callback).
                        _fc_.FileChanger().change_file_content(
                            version=None,
                            file_unicum=file_unicum,
                            abspath=diskpath,
                            repoints=_repperm_dict_,
                            dry_run=True,
                            force_new_content=False,
                            callback=case_05_finish,
                            callbackArg=None,
                        )
                        return
                    # Just repoint
                    _repperm_dict_[file_unicum.get_name()] = [
                        disppath,
                        diskpath,
                        False,
                    ]
                    if os.path.isfile(disppath):
                        # Note: It is possible that there is *also* a file at the 'disppath' loca-
                        # tion. That one should be deleted.
                        if not repperm_only:
                            _delperm_dict_[file_unicum.get_name()] = [
                                disppath,
                                "",
                                False,
                            ]

                # $ IRRELEVANT
                else:
                    # repoint to None -> yes
                    _repperm_dict_[file_unicum.get_name()] = [
                        disppath,
                        "None",
                        False,
                    ]
                    # delete -> yes (file exists at 'diskpath' and another one might even exist at
                    # 'disppath')
                    if not repperm_only:
                        _delperm_dict_[file_unicum.get_name()] = [
                            diskpath,
                            "",
                            False,
                        ]
                        if os.path.isfile(disppath):
                            _delperm_dict_[file_unicum.get_name()] = [
                                disppath,
                                "",
                                False,
                            ]
                next_impacted_file_a(file_unicum_iter)
                return

            #! ---------------------------------- SELECT CASE ----------------------------------- !#
            if (disppath is None) or (disppath.lower() == "none"):
                if (diskpath is None) or (diskpath.lower() == "none"):
                    case_01()
                else:
                    case_02()
            else:
                if (diskpath is None) or (diskpath.lower() == "none"):
                    case_03()
                elif diskpath == disppath:
                    case_04()
                else:
                    case_05()
            return

        def finish(*args):
            # note(1): special case -> diff == 0 and man_mod == True
            #          This means the user modified his file such that
            #          it equals the 'new content', then he modified it
            #          further. The 'cur content' therefore equals the
            #          merged one. -> diff == 0 but man_mod == True
            assert qt.QThread.currentThread() is origthread
            callback(
                _addperm_dict_,
                _delperm_dict_,
                _modperm_dict_,
                _repperm_dict_,
                callbackArg,
            )
            return

        # * Start
        assert qt.QThread.currentThread() is origthread
        next_impacted_file_a(iter(_impactedFiles_))
        return

    def save_orig_cfgfiles(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """If it doesn't exist yet, save a copy of all config files to:
        '.beetle/.config_orig/' For later use in three-way merges.

            Example:
                C:/myproject/config/makefile
                            └───────◡───────┘

                C:/myproject/.build/.config_orig/config/makefile
                                                └───────◡───────┘

        This should only happen if:
            - There is no '.beetle/.config_orig/' folder yet.
            - The '.beetle/.config_orig/' folder is not complete.

        WARNING:
        For now, only config files in the project's rootfolder get handled!
        """
        treepath_seg = data.current_project.get_treepath_seg()
        rootpath = data.current_project.get_proj_rootpath()
        buildpath = treepath_seg.get_abspath("BUILD_DIR")
        dotbeetledir = _pp_.rel_to_abs(
            rootpath=rootpath,
            relpath=".beetle",
        )
        config_orig_abspath = _pp_.rel_to_abs(
            rootpath=dotbeetledir,
            relpath=f".config_orig",
        )
        readme_abspath = _pp_.rel_to_abs(
            rootpath=config_orig_abspath,
            relpath="readme.txt",
        )
        readme_template_abspath = purefunctions.join_resources_dir_to_path(
            "templates/config_orig_readme.txt"
        )

        # * 1. Check '.beetle' path
        if not os.path.isdir(dotbeetledir):
            try:
                _fp_.make_dir(
                    dir_abspath=dotbeetledir,
                    catch_err=False,
                )
            except:
                purefunctions.printc(
                    f"\nERROR: Could not create {q}.beetle{q} folder.",
                    color="error",
                )
                print(f"{traceback.format_exc()}\n")
                if callback is not None:
                    qt.QTimer.singleShot(
                        50, functools.partial(callback, callbackArg)
                    )
                return
        assert os.path.isdir(dotbeetledir)

        # * 2. Check '.beetle/.config_orig' path.
        if not os.path.isdir(config_orig_abspath):
            try:
                _fp_.make_dir(
                    dir_abspath=config_orig_abspath,
                    catch_err=False,
                )
            except:
                purefunctions.printc(
                    f"\n"
                    f"ERROR: Could not create {q}{config_orig_abspath}{q} folder.\n"
                    f"\n{traceback.format_exc()}\n",
                    color="error",
                )
                if callback is not None:
                    qt.QTimer.singleShot(
                        50, functools.partial(callback, callbackArg)
                    )
                return
        assert os.path.isdir(config_orig_abspath)

        # * 3. Write all
        for treepath_obj in treepath_seg.get_treepath_obj_list():
            abspath = treepath_obj.get_abspath()
            orig_abspath = None
            if not treepath_obj.is_file():
                # it's a directory
                continue
            if (abspath is None) or (abspath.lower() == "none"):
                # no pointer
                continue
            if not os.path.isfile(abspath):
                # file doesn't exist
                continue
            if abspath.endswith(("bin", ".hex", ".elf")):
                # don't copy binaries
                continue
            if abspath.startswith(buildpath):
                # don't copy build artefacts
                continue
            if abspath.startswith(dotbeetledir):
                # don't copy files in '.beetle/'
                if treepath_obj.get_name() == "BUTTONS_BTL":
                    # make exception
                    pass
                else:
                    continue
            if not abspath.startswith(rootpath):
                # file outside root
                continue
            # file passed all the filters
            assert os.path.isfile(abspath)
            assert abspath.startswith(rootpath)
            orig_abspath = abspath.replace(
                rootpath,
                config_orig_abspath,
                1,
            )
            if os.path.isfile(orig_abspath):
                # orig file already there
                pass
            else:
                try:
                    _fp_.copy_file(
                        sourcefile_abspath=abspath,
                        targetfile_abspath=orig_abspath,
                        catch_err=False,
                    )
                except Exception as e:
                    purefunctions.printc(
                        f"\n"
                        f"ERROR: Could not copy:\n"
                        f"{q}{abspath}{q} to:\n"
                        f"{q}{orig_abspath}{q}\n"
                        f"\n{traceback.format_exc()}\n",
                        color="error",
                    )
                    if callback is not None:
                        qt.QTimer.singleShot(
                            50, functools.partial(callback, callbackArg)
                        )
                    return

        # * 4. Write readme.txt
        if not os.path.isfile(readme_abspath):
            try:
                _fp_.copy_file(
                    sourcefile_abspath=readme_template_abspath,
                    targetfile_abspath=readme_abspath,
                    catch_err=False,
                )
            except Exception as e:
                purefunctions.printc(
                    f"\n"
                    f"ERROR: Could not write the readme file to:\n"
                    f"{q}{readme_abspath}{q}\n"
                    f"\n{traceback.format_exc()}\n",
                    color="error",
                )
                (
                    qt.QTimer.singleShot(
                        50, functools.partial(callback, callbackArg)
                    )
                    if callback is not None
                    else nop()
                )
                return
        if callback is not None:
            qt.QTimer.singleShot(50, functools.partial(callback, callbackArg))
        return

    def reload_dashboard(
        self,
        callback: Callable,
        callbackArg: object,
    ) -> None:
        """Check out the config files in the project's config folder and try to
        reconstruct the dash- board settings from them."""
        # Not yet implemented
        if callback is not None:
            callback(callbackArg)
        return
