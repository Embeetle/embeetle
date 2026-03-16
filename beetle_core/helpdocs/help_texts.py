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
import purefunctions
import helpdocs.help_subjects.general as _gen_
import helpdocs.help_subjects.blasphemy_censored as _blasphemy_
import helpdocs.help_subjects.compilation as _compilation_
import helpdocs.help_subjects.console as _console_
import helpdocs.help_subjects.dashboard as _dashboard_
import helpdocs.help_subjects.diagnostics as _diagnostics_
import helpdocs.help_subjects.editor as _editor_
import helpdocs.help_subjects.filetree as _filetree_
import helpdocs.help_subjects.home_window as _home_window_
import helpdocs.help_subjects.libraries as _libraries_
import helpdocs.help_subjects.license as _license_
import helpdocs.help_subjects.new_tool_wizard as _new_tool_wiz_
import helpdocs.help_subjects.projstruct as _projstruct_
import helpdocs.help_subjects.source_analyzer as _sa_
import helpdocs.help_subjects.startup as _startup_
import helpdocs.help_subjects.symbolwindow as _symbolwindow_
import helpdocs.help_subjects.tools as _tools_
import helpdocs.help_subjects.pieces as _pieces_

if TYPE_CHECKING:
    import qt
    import project.segments.board_seg.board as _board_
    import project.segments.chip_seg.chip as _chip_
    import project.segments.probe_seg.probe as _probe_
    import bpathlib.tool_obj as _tool_obj_
    import bpathlib.treepath_obj as _treepath_obj_


#! 1. GENERAL
def beetle_busy(*args) -> None:
    return _gen_.beetle_busy()


def save_failed(explain: str = "") -> None:
    return _gen_.save_failed(explain)


def what_kind_of_building(*args) -> str:
    return _gen_.what_kind_of_building()


def do_manual_selection(unicum_name: str, isfile: bool) -> bool:
    return _gen_.do_manual_selection(unicum_name, isfile)


#! 2. BLASPHEMY
def register_unholy_char(relpath: str) -> None:
    return _blasphemy_.register_unholy_char(relpath)


def blasphemy_detected(*args) -> bool:
    return len(_blasphemy_.unholy_relpaths) > 0


def blasphemy_startup_warning(*args) -> None:
    return _blasphemy_.blasphemy_startup_warning()


def blasphemy_tresspass_warning(name: str, isfile: bool) -> None:
    return _blasphemy_.blasphemy_tresspass_warning(name, isfile)


def blasphemy_name_warning(name: str, isfile: bool) -> None:
    return _blasphemy_.blasphemy_name_warning(name, isfile)


def blasphemy_path_warning(relpath: str, isfile: bool) -> None:
    return _blasphemy_.blasphemy_path_warning(relpath, isfile)


def refuse_operation_on_blasphemous_directory(relpath: str) -> None:
    return _blasphemy_.refuse_operation_on_blasphemous_directory(relpath)


#! 3. COMPILATION
# * 3.1 General
def cannot_create_builddir(*args) -> None:
    return _compilation_.cannot_create_builddir()


def where_is_builddir(*args) -> None:
    return _compilation_.where_is_builddir()


def beetle_busy_yes_no(question) -> bool:
    return _compilation_.beetle_busy_yes_no(question)


#! 4. CONSOLE
# * 4.1 General
def previous_process_busy(*args) -> None:
    return _console_.previous_process_busy()


def cmds_file_not_attached(*args) -> None:
    return _console_.cmds_file_not_attached()


def cmds_file_not_found(*args) -> None:
    return _console_.cmds_file_not_found()


#! 5. DASHBOARD
# * 5.1 General
def dashboard_help(*args) -> None:
    return _dashboard_.dashboard_help()


# * 5.2 Chip & Memory
def memsection_to_clipboard(
    memsection: _chip_.MemSection,
    memregion: _chip_.MemRegion,
    attribute_text: str,
) -> None:
    return _dashboard_.memsection_to_clipboard(
        memsection, memregion, attribute_text
    )


def memregion_help(memregion: _chip_.MemRegion) -> None:
    return _dashboard_.memregion_help(memregion)


def memsection_help(
    memsection: _chip_.MemSection,
    memregion: _chip_.MemRegion,
    attribute_text: str,
) -> None:
    return _dashboard_.memsection_help(memsection, memregion, attribute_text)


def board_help(board: Optional[_board_.Board] = None) -> None:
    return _dashboard_.board_help(board)


def chip_help(chip: Optional[_chip_.Chip] = None) -> None:
    return _dashboard_.chip_help(chip)


def chip_swap_warning(*args) -> Optional[str]:
    return _dashboard_.chip_swap_warning()


def lib_help(*args) -> None:
    return _dashboard_.lib_help()


# * 5.3 Probe
def probe_help(probe: Optional[_probe_.Probe] = None) -> None:
    return _dashboard_.probe_help(probe)


def probe_comport_help(*args) -> None:
    return _dashboard_.probe_comport_help()


def probe_transport_protocol_help(
    probe: Optional[_probe_.Probe] = None,
) -> None:
    return _dashboard_.probe_transport_protocol_help(probe)


# * 5.4 Project layout and Tools
def treepaths_help(*args) -> None:
    return _dashboard_.treepaths_help()


def tools_help(*args) -> None:
    return _dashboard_.tools_help()


def toolchain_help(*args) -> None:
    return _dashboard_.toolchain_help()


def buildautomation_help(*args) -> None:
    return _dashboard_.buildautomation_help()


def flashtool_help(*args) -> None:
    return _dashboard_.flashtool_help()


# * 5.5 Dashboard permission
def ask_dashboard_permission(
    addperm_dict: Dict,
    delperm_dict: Dict,
    modperm_dict: Dict,
    repperm_dict: Dict,
    title_text: Optional[str],
    callback: Optional[Callable],
) -> None:
    return _dashboard_.ask_dashboard_permission(
        addperm_dict,
        delperm_dict,
        modperm_dict,
        repperm_dict,
        title_text,
        callback,
    )


def files_modified_info(*args) -> None:
    return _dashboard_.files_modified_info()


def files_deleted_info(*args) -> None:
    return _dashboard_.files_deleted_info()


def files_added_info(*args) -> None:
    return _dashboard_.files_added_info()


def explain_dashboard_permission(*args) -> None:
    return _dashboard_.explain_dashboard_permission()


def dashboard_info(typ: str) -> None:
    return _dashboard_.dashboard_info(typ)


# * 5.6 Elf file parsing
def cannot_parse_elf_file(elf_abspath: str, error_txt: str) -> None:
    return _dashboard_.cannot_parse_elf_file(elf_abspath, error_txt)


# * 5.7 PathObj info
def show_treepathobj_info(pathobj: _treepath_obj_.TreepathObj) -> None:
    return _dashboard_.show_treepathobj_info(pathobj)


#! 6. DIAGNOSTICS
def show_diagnostics_help(*args) -> None:
    return _diagnostics_.show_diagnostics_help()


#! 7. EDITOR
def editor_help(*args) -> None:
    return _editor_.editor_help()


#! 8. FILETREE
def show_filetree_help(*args) -> None:
    return _filetree_.show_filetree_help()


def main_makefile_checkbox_help(name: str) -> None:
    return _filetree_.main_makefile_checkbox_help(name)


def nonmain_makefile_checkbox_help(name: str) -> None:
    return _filetree_.nonmain_makefile_checkbox_help(name)


def file_hchbx_help(name: str, parentName: str, feedback: bool) -> None:
    return _filetree_.file_hchbx_help(name, parentName, feedback)


def dir_hchbx_help(name: str) -> None:
    return _filetree_.dir_hchbx_help(name)


def cannot_delete_file(abspath: str) -> None:
    return _filetree_.cannot_delete_file(abspath)


def cannot_move_file(abspath: str) -> None:
    return _filetree_.cannot_move_file(abspath)


def cannot_move_folder(abspath: str) -> None:
    return _filetree_.cannot_move_folder(abspath)


def cannot_rename_file(abspath: str) -> None:
    return _filetree_.cannot_rename_file(abspath)


def cannot_delete_dir(abspath: str) -> None:
    return _filetree_.cannot_delete_dir(abspath)


def cannot_rename_dir(abspath: str) -> None:
    return _filetree_.cannot_rename_dir(abspath)


#! 9. HOME WINDOW
def about(parent: qt.QWidget) -> None:
    return _home_window_.about(parent)


def import_from_library(parent: qt.QWidget) -> None:
    return _home_window_.import_from_library(parent)


def project_creation_info(parent: qt.QWidget, typ: str) -> None:
    return _home_window_.project_creation_info(parent, typ)


def show_info_field(
    projname: str, microcontroller: str, info_content: str, parent: qt.QWidget
) -> None:
    return _home_window_.show_info_field(
        projname, microcontroller, info_content, parent
    )


def project_import_info(
    parent: qt.QWidget, typ: str, vendor: str
) -> Optional[str]:
    return _home_window_.project_import_info(parent, typ, vendor)


def home_window_info(parent: qt.QWidget, *args) -> None:
    for arg in args:
        if isinstance(arg, str):
            try:
                _home_window_.home_window_info(parent, arg)
                return
            except Exception as e:
                print(e)
    purefunctions.printc(
        f"ERROR: home_window_info(args = {args})",
        color="error",
    )
    return


def home_window_release_notes(*args) -> Tuple[str, Callable]:
    return _home_window_.home_window_release_notes()


#! 10. LIBRARIES
def specific_lib_help(libname: str, libversion: str, libpath: str) -> None:
    return _libraries_.specific_lib_help(libname, libversion, libpath)


def lib_version_help(libname: str, libversion: str, libpath: str) -> None:
    return _libraries_.lib_version_help(libname, libversion, libpath)


def most_recent_version(libname: str, libversion: str) -> None:
    return _libraries_.most_recent_version(libname, libversion)


def new_version_available(
    libname: str, current_version: str, recent_version: str, libpath: str
) -> Optional[str]:
    return _libraries_.new_version_available(
        libname, current_version, recent_version, libpath
    )


def libcat_help(libcat: Optional[str]) -> None:
    return _libraries_.libcat_help(libcat)


def libraries_tab_help(*args) -> None:
    return _libraries_.libraries_tab_help()


#! 11. LICENSE
def show_license(
    parent: qt.QWidget, txt: str, typ: str = "accept_decline"
) -> Union[
    qt.QMessageBox.StandardButton.Ok, qt.QMessageBox.StandardButton.Cancel
]:
    return _license_.show_license(parent, txt, typ)


#! 12. NEW TOOL WIZARD
def tool_source_help(*args) -> None:
    return _new_tool_wiz_.tool_source_help()


def select_tool_help(toolcat) -> None:
    return _new_tool_wiz_.select_tool_help(toolcat)


def tool_parent_directory_help(*args) -> None:
    return _new_tool_wiz_.tool_parent_directory_help()


def tool_executable_help(*args) -> None:
    return _new_tool_wiz_.tool_executable_help()


def tool_directory_help(*args) -> None:
    return _new_tool_wiz_.tool_directory_help()


def tool_info_help(*args) -> None:
    return _new_tool_wiz_.tool_info_help()


#! 13. PROJ STRUCT
def cannot_rename_rootfolder_dialog(*args) -> None:
    return _projstruct_.cannot_rename_rootfolder_dialog()


def cannot_delete_rootfolder_dialog(*args) -> None:
    return _projstruct_.cannot_delete_rootfolder_dialog()


def cannot_select_path_outside_project(selected_path: str, *args) -> None:
    return _projstruct_.cannot_select_path_outside_project(selected_path)


def makefiles_together(*args) -> None:
    return _projstruct_.makefiles_together()


def save_filetree_mk_warning(*args) -> None:
    return _projstruct_.save_filetree_mk_warning()


#! 14. SOURCE ANALYZER
def source_analyzer_help(*args) -> None:
    return _sa_.source_analyzer_help()


def report_internal_error(msg: Optional[str], *args) -> Tuple[str, Callable]:
    return _sa_.report_internal_error(msg)


def sa_status_ok(*args) -> None:
    return _sa_.sa_status_ok()


def sa_launch_problem(*args) -> None:
    return _sa_.sa_launch_problem()


def sa_internal_problem(*args) -> None:
    return _sa_.sa_internal_problem()


def sa_project_err(*args) -> None:
    return _sa_.sa_project_err()


def sa_busy(*args) -> None:
    return _sa_.sa_busy()


def sa_dependencies(*args) -> None:
    return _sa_.sa_dependencies()


def sa_cpu_cores(*args) -> None:
    return _sa_.sa_cpu_cores()


def sa_clear_cache(*args) -> None:
    return _sa_.sa_clear_cache()


#! 15. STARTUP
def warning_for_external_folders(
    ext_folder_data: Dict[str, Dict[str, Optional[str]]],
) -> bool:
    return _startup_.warning_for_external_folders(ext_folder_data)


#! 16. SYMBOL WINDOW
def symbol_window_hamburger_help(*args) -> None:
    return _symbolwindow_.symbol_window_hamburger_help()


#! 17. TOOLS
def ask_to_download_tool(uid: str, beetle_tools_folder: str) -> bool:
    return _tools_.ask_to_download_tool(uid, beetle_tools_folder)


def tool_on_path(
    toolobj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
) -> None:
    return _tools_.tool_on_path(toolobj)


def tool_external(
    toolobj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
) -> None:
    return _tools_.tool_external(toolobj)


#! 18. PIECES
def show_model_download_help(*args, **kwargs) -> None:
    return _pieces_.show_model_download_help(*args, **kwargs)
