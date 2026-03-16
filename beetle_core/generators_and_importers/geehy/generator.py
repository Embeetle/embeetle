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

# WARNING
# THIS FILE GETS OFTEN R-SYNCED FROM <BEETLE_CORE> TO <BEETLE_PROJECT_GENERATOR>. ONLY EDIT THIS
# FILE FROM WITHIN THE <BEETLE_CORE> FOLDER. OTHERWISE, YOUR CHANGES GET LOST.
from __future__ import annotations
import os
import data, purefunctions, functions
import generators_and_importers.helper as _helper_


def generate_projects() -> None:
    """"""
    functions.generator_printfunc(
        f"\n" f"GEEHY\n" f"=====",
        color="green",
    )
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/geehy/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        src_abspath = f"{data.sample_proj_resources}/geehy/projects/{relpath}"
        dst_abspath = f"{data.generated_projects_directory}/geehy/{relpath}"
        # $ Read 'hardware.json5'
        boardname, chipname, probename = _helper_.read_hardware_from_src(
            src_abspath
        )
        # $ Print project info
        _helper_.print_project_info(
            project_name, boardname, chipname, probename
        )
        # $ Skip unsupported hardware
        if _helper_.skip_project(boardname, chipname):
            # Already printed at this point: 'Import success: skipped'
            continue
        # $ Do the import in a new terminal
        _helper_.import_project(
            manufacturer="geehy",
            src_abspath=src_abspath,
            dst_abspath=dst_abspath,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
        )
        # $ Do the import in the same terminal (deprecated)
        # _beetlifyer_.beetlify_project(
        #     src_abspath = src_abspath,
        #     dst_abspath = dst_abspath,
        # )
        continue
    return


def zip_projects() -> None:
    """"""
    functions.generator_printfunc(
        f"\n" f"GEEHY\n" f"=====",
        color="green",
    )
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/geehy/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        proj_abspath = f"{data.generated_projects_directory}/geehy/{relpath}"
        zip_abspath = f"{data.zipped_projects_directory}/geehy/{relpath}.7z"
        if not os.path.isdir(proj_abspath):
            continue
        # $ Zip project
        functions.sevenzip_dir_to_file(
            src_dirpath=proj_abspath,
            dst_filepath=zip_abspath,
            forbidden_dirnames=None,
            forbidden_filenames=None,
            verbose=True,
            spawn_terminal=True,
        )
        continue
    return
