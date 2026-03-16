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
import os, tempfile, traceback, sys
import data, purefunctions, functions
import generators_and_importers.stmicro.importer as _stmicro_importer_
import generators_and_importers.helper as _helper_
from various.kristofstuff import *


def generate_projects() -> None:
    """
    Generating all STMicro projects happens in two stages (per project), for those sample projects
    that contain a 'cubemx.ioc' file:

      1) generate_cubemx_project(): Generate a CubeMX project from the 'cubemx.ioc' file in the
                                    'sample_proj_resources' repo, into a temporary directory.

      2) import_cubemx_project(): Import the project from the temporary directory into the
                                  '<user>/.embeetle/' folder.

    Sample projects that don't contain this 'cubemx.ioc' file simply get beetlified.
    """
    functions.generator_printfunc(
        f"\n" f"STMICRO\n" f"=======",
        color="green",
    )
    # Extract the 'project_list' from the corresponding json-file. It lists all stmicro projects and
    # their relative paths. From that, the absolute src and dst paths can be derived.
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/stmicro/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        src_abspath = f"{data.sample_proj_resources}/stmicro/projects/{relpath}"
        dst_abspath = f"{data.generated_projects_directory}/stmicro/{relpath}"
        # $ Read 'hardware.json5' or 'cubemx.ioc'
        # Give preference to 'hardware.json5'. Some 'cubemx.ioc' files, like the one from the Blue
        # Pill, cannot return the right boardname.
        if os.path.isfile(f"{src_abspath}/hardware.json5"):
            boardname, chipname, probename = _helper_.read_hardware_from_src(
                src_abspath
            )
        elif os.path.isfile(f"{src_abspath}/cubemx.ioc"):
            try:
                board_unicum, chip_unicum, probe_unicum = (
                    _stmicro_importer_.extract_data_from_ioc_file(
                        f"{src_abspath}/cubemx.ioc"
                    )
                )
                boardname = board_unicum.get_name()
                chipname = chip_unicum.get_name()
                probename = probe_unicum.get_name()
            except:
                functions.generator_printfunc(
                    f"{traceback.format_exc()}\n",
                    color="error",
                )
                input("Press any key ...")
                raise
        else:
            traceback.print_exc()
            functions.fail_exit(
                f"\nCannot extract hardware data from {q}{src_abspath}{q}!\n"
            )
            return
        # $ Print project info
        _helper_.print_project_info(
            project_name, boardname, chipname, probename
        )
        # $ Skip unsupported hardware
        if _helper_.skip_project(boardname, chipname):
            # Already printed at this point: 'Import success: skipped'
            continue

        # & No 'cubemx.ioc' found
        # If there's no 'cubemx.ioc' file in the src project, then it's a complete project that just
        # must be beetlified.
        if not os.path.isfile(f"{src_abspath}/cubemx.ioc"):
            # $ Do the import in a new terminal
            # I've extended the STMicro importer a bit. Normally it would only look for a '.ioc'
            # file to extract the hardware names from. But now, it also looks for a 'hardware.json5'
            # file if it cannot detect any '.ioc' file.
            _helper_.import_project(
                manufacturer="stmicro",
                src_abspath=src_abspath,
                dst_abspath=dst_abspath,
            )
            # $ do the import in the same terminal (deprecated)
            # _beetlifyer_.beetlify_project(
            #     src_abspath = src_abspath,
            #     dst_abspath = dst_abspath,
            # )
            continue

        # & 'cubemx.ioc' found
        # $ Generate CubeMX project to temporary directory (in a new terminal)
        # A `cubemx.ioc` file was found in the src project, so the two-stage-approach must be taken.
        # Note that the `cubemx.ioc` file can either be a full `.ioc` file itself, or point to one
        # of the default ones (recently I added the functionality that it can direct the system to
        # look automatically for the right one).
        # First generate the CubeMX project into a temporary directory.
        tempdir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
        functions.generator_printfunc(
            f"CubeMX generation success: ", color="yellow", end=""
        )
        try:
            wait_func = purefunctions.spawn_new_terminal(
                script_or_exe_path=f"{data.beetle_project_generator_folder}/generators_and_importers/stmicro/cubemx_generator.py",
                argv=[
                    "--src",
                    src_abspath,
                    "--dst",
                    str(tempdir.name).replace("\\", "/"),
                ],
            )
            result = wait_func()
        except:
            traceback.print_exc()
            functions.generator_printfunc(f"false", color="red")
            functions.generator_printfunc("")
            functions.fail_exit(
                f"\nFailed to generate CubeMX project {q}{project_name}{q}\n"
            )
            tempdir.cleanup()
            return
        if result == 0:
            functions.generator_printfunc(f"true", color="green")
        else:
            functions.generator_printfunc(f"false", color="red")
            functions.generator_printfunc("")
            functions.fail_exit(
                f"\nFailed to generate CubeMX project {q}{project_name}{q}\n"
            )
            tempdir.cleanup()
            return
        assert result == 0
        # $ Do  the import (in a new terminal)
        # input(f'Check temporary directory: {tempdir.name}')
        _helper_.import_project(
            manufacturer="stmicro",
            src_abspath=str(tempdir.name).replace("\\", "/"),
            dst_abspath=dst_abspath,
        )
        # $ Delete the temporary directory
        tempdir.cleanup()
        continue
    return


def zip_projects() -> None:
    """"""
    functions.generator_printfunc(
        f"\n" f"STMICRO\n" f"=======",
        color="green",
    )
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/stmicro/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        proj_abspath = f"{data.generated_projects_directory}/stmicro/{relpath}"
        zip_abspath = f"{data.zipped_projects_directory}/stmicro/{relpath}.7z"
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
