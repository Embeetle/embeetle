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
import tempfile, os, traceback
import data, purefunctions, functions, sys
import generators_and_importers.helper as _helper_
from various.kristofstuff import *

"""
                   Prerequisites
===========================================================
nRF5_SDK
========
I downloaded the nRF5_SDK here:

 - nRF5_SDK_16.0.0_98a08e2.zip
 - nRF5_SDK_16.0.0_offline_doc.zip
https://developer.nordicsemi.com/nRF5_SDK/nRF5_SDK_v16.x.x/

And put it here:
 -> C:/sample_proj_resources/nordic/sdk/nRF5_SDK_16.0.0_98a08e2/
 
Next go to C:/sample_proj_resources/nordic/sdk/nRF5_SDK_16.0.0_98a08e2/components/toolchain/gcc/Makefile.windows
and fill in:

    GNU_INSTALL_ROOT := C:/Users/krist/.embeetle/beetle_tools/windows/gnu_arm_toolchain_10.3.1_20210824_32b/bin/
    GNU_VERSION := 10.3.1
    GNU_PREFIX := arm-none-eabi
"""


def generate_projects() -> None:
    """Generating all Nordic projects happens in two stages (per project):

    1) extract_nordic_project_from_sdk(): Generate a Nordic project from the
    SDK, into a temporary                                       directory.

    2) beetlify
    """
    functions.generator_printfunc(
        f"\n" f"NORDIC\n" f"======",
        color="green",
    )
    # Extract the 'project_list' from the corresponding json-file. It lists all nordic projects and
    # their relative paths. From that, the absolute src and dst paths can be derived.
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/nordic/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        src_abspath = f"{data.sample_proj_resources}/nordic/projects/{relpath}"
        dst_abspath = f"{data.generated_projects_directory}/nordic/{relpath}"
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
        # $ Generate SDK project to temporary directory in a new terminal
        # First extract the Nordic project from the SDK into a temporary directory
        tempdir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
        argv = [
            "--src",
            src_abspath,
            "--dst",
            tempdir.name.replace("\\", "/"),
            "--make",
            f"{data.beetle_tools_directory}/gnu_make_4.2.1_64b/make.exe",
        ]
        if "freertos" in project_name:
            argv.append("--freertos")
        functions.generator_printfunc(
            f"SDK generation success: ", color="yellow", end=""
        )
        try:
            wait_func = purefunctions.spawn_new_terminal(
                script_or_exe_path=f"{data.beetle_project_generator_folder}/generators_and_importers/nordic/sdk_generator.py",
                argv=argv,
            )
            result = wait_func()
        except:
            traceback.print_exc()
            functions.generator_printfunc(f"false", color="red")
            functions.generator_printfunc("")
            functions.fail_exit(
                f"\nFailed to generate SDK project {q}{project_name}{q}\n"
            )
            tempdir.cleanup()
            return
        if result == 0:
            functions.generator_printfunc(f"true", color="green")
        else:
            functions.generator_printfunc(f"false", color="red")
            functions.generator_printfunc("")
            functions.fail_exit(
                f"\nFailed to generate SDK project {q}{project_name}{q}\n"
            )
            tempdir.cleanup()
            return
        assert result == 0
        # $ Generate SDK project to temporary directory in same terminal (deprecated)
        # __extract_nordic_project_from_sdk(
        #     boardname    = boardname,
        #     dst_abspath  = tempdir.name.replace('\\', '/')
        #     has_freertos = 'freertos' in project_name,
        # )
        # $ Do the import in a new terminal
        _helper_.import_project(
            manufacturer="nordic",
            src_abspath=tempdir.name.replace("\\", "/"),
            dst_abspath=dst_abspath,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
        )
        # $ Do the import in the same terminal (deprecated)
        # Now import the project from the temporary directory into the dst folder, which is in the
        # '<user>/.embeetle/' folder.
        # _beetlifyer_.beetlify_project(
        #     src_abspath = tempdir.name.replace('\\', '/'),
        #     dst_abspath = dst_abspath,
        #     boardname   = boardname,
        #     chipname    = chipname,
        #     probename   = probename,
        # )
        # $ Delete the temporary directory
        tempdir.cleanup()
        continue
    return


def zip_projects() -> None:
    """"""
    functions.generator_printfunc(
        f"\n" f"NORDIC\n" f"======",
        color="green",
    )
    project_list = purefunctions.load_json_file_with_comments(
        f"{data.sample_proj_resources}/nordic/projects/project_list.json5"
    )
    for project_name in project_list.keys():
        # $ Extract paths from 'project_list.json5'
        relpath = project_list[project_name]
        proj_abspath = f"{data.generated_projects_directory}/nordic/{relpath}"
        zip_abspath = f"{data.zipped_projects_directory}/nordic/{relpath}.7z"
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
