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
from typing import *
import os, tempfile
import purefunctions, filefunctions, functions
import hardware_api.file_generator as _file_generator_
import hardware_api.hardware_api as _hardware_api_
import hardware_api.toolcat_unicum as _toolcat_unicum_
import generators_and_importers.fix_warnings as _fix_warnings_

q = "'"


def beetlify_project_in_place(
    src_abspath: str,
    boardname: Optional[str] = None,
    chipname: Optional[str] = None,
    probename: Optional[str] = None,
    convert_line_endings: bool = True,
    convert_encoding: bool = True,
) -> bool:
    """Same as 'beetlify_project(..)' but src_abspath == dst_abspath."""
    # & Create temporary folder
    tempdir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
    tempdir_path: str = str(tempdir.name).replace("\\", "/")
    if tempdir_path.endswith("/"):
        tempdir_path = tempdir_path[:-1]

    # & Use it as destination folder
    beetlify_project(
        src_abspath=src_abspath,
        dst_abspath=tempdir_path,
        boardname=boardname,
        chipname=chipname,
        probename=probename,
        convert_line_endings=convert_line_endings,
        convert_encoding=convert_encoding,
    )

    # & Clean the source folder
    filefunctions.clean(
        folderpath=src_abspath,
        verbose=True,
        exit_on_fail=False,
        printfunc=functions.importer_printfunc,
    )

    # & Move everything from the temporary to the source folder
    filefunctions.move_contents(
        src=tempdir_path,
        dst=src_abspath,
        verbose=True,
        exit_on_fail=False,
        printfunc=functions.importer_printfunc,
    )

    # & Clean up the temporary folder
    tempdir.cleanup()
    if os.path.isdir(tempdir_path):
        filefunctions.delete(
            abspath=tempdir_path,
            verbose=True,
            exit_on_fail=False,
            printfunc=functions.importer_printfunc,
        )
    return True


def beetlify_project(
    src_abspath: str,
    dst_abspath: str,
    boardname: Optional[str] = None,
    chipname: Optional[str] = None,
    probename: Optional[str] = None,
    convert_line_endings: bool = True,
    convert_encoding: bool = True,
) -> bool:
    """Embeetlify the given project while copying it from 'src_abspath' to
    'dst_abspath'.

    When called from Embeetle, the hardware names will be filled in by the user.
    In that case, the 'hardware.json5' file is not needed.

    When invoked automatically by a project generator, the hardware names are
    not given (except for the stmicro generator that extracts the hardware names
    from the '.ioc' file). In that case, the 'hardware.json5' file must be
    present.

    :return: success
    """
    functions.importer_printfunc(
        f"beetlify_project(", color="yellow", bright=True
    )
    functions.importer_printfunc(
        f"    src_abspath = ", color="yellow", bright=True, end=""
    )
    functions.importer_printfunc(f"{q}{src_abspath}{q}")
    functions.importer_printfunc(
        f"    dst_abspath = ", color="yellow", bright=True, end=""
    )
    functions.importer_printfunc(f"{q}{dst_abspath}{q}")
    functions.importer_printfunc(
        f"    boardname   = ", color="yellow", bright=True, end=""
    )
    functions.importer_printfunc(f"{q}{boardname}{q}")
    functions.importer_printfunc(
        f"    chipname    = ", color="yellow", bright=True, end=""
    )
    functions.importer_printfunc(f"{q}{chipname}{q}")
    functions.importer_printfunc(
        f"    probename   = ", color="yellow", bright=True, end=""
    )
    functions.importer_printfunc(f"{q}{probename}{q}")
    functions.importer_printfunc(f")", color="yellow", bright=True)
    if src_abspath == dst_abspath:
        return beetlify_project_in_place(
            src_abspath=src_abspath,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
            convert_line_endings=convert_line_endings,
            convert_encoding=convert_encoding,
        )
    assert src_abspath != dst_abspath

    # & Hardware
    # Extract hardware names from 'hardware.json5' if the names are not given
    if boardname is None:
        hardware_dict = purefunctions.load_json_file_with_comments(
            f"{src_abspath}/hardware.json5"
        )
        if hardware_dict is None:
            raise RuntimeError(
                f"Cannot load json file: {q}{src_abspath}/hardware.json5{q}"
            )
        boardname = hardware_dict["board_name"]
        chipname = hardware_dict["chip_name"]
        probename = hardware_dict["probe_name"]

    # & Copy override files
    # First copy the override json-files, such that they can take effect in the next step, where the
    # project skeleton is built.
    override_filepath_list: List[str] = [
        f"{src_abspath}/board.json5",
        f"{src_abspath}/chip.json5",
        f"{src_abspath}/probe.json5",
        f"{src_abspath}/.beetle/board.json5",
        f"{src_abspath}/.beetle/chip.json5",
        f"{src_abspath}/.beetle/probe.json5",
        f"{src_abspath}/config/board.json5",
        f"{src_abspath}/config/chip.json5",
        f"{src_abspath}/config/probe.json5",
    ]
    for f in reversed(override_filepath_list):
        if os.path.isfile(f):
            continue
        override_filepath_list.remove(f)
        continue
    for f in override_filepath_list:
        override_filepath_src = f
        override_filepath_dst = (
            f'{dst_abspath}/.beetle/{override_filepath_src.split("/")[-1]}'
        )
        # The override json-file from a previous run can still exist. A clean didn't happen yet at
        # this point.
        if os.path.isfile(override_filepath_dst):
            filefunctions.delete(
                abspath=override_filepath_dst,
                verbose=False,
                printfunc=functions.importer_printfunc,
            )
        filefunctions.copy(
            src=override_filepath_src,
            dst=override_filepath_dst,
            printfunc=functions.importer_printfunc,
        )
        continue

    # & Project skeleton
    # Generate the project folders and config files.
    __create_empty_project_skeleton(
        proj_rootpath=dst_abspath,
        boardname=boardname,
        chipname=chipname,
        probename=probename,
    )

    # & Copy source code
    def copy_source_code(_src_abspath, _dst_abspath):
        for e1 in os.listdir(_src_abspath):
            # We loop over all elements 'e1' in '_src_abspath' - both files and folders. We then
            # copy them one by one to the 'source/' folder within the '_dst_abspath', like so:
            #     e2 = e1
            #     copy f'{_src_abspath}/{e1}' => f'{_dst_abspath}/source/{e2}'
            # However, a few elements must be skipped. A few others must be copied, but to a
            # slightly different location (eg. not to the source/ folder).

            # & ELEMENTS TO SKIP
            # $ SKIP:
            # Skip Eclipse stuff
            if any(
                e1.lower() == s
                for s in (
                    ".settings",
                    ".project",
                    ".project_org",
                    ".cproject",
                    ".cproject_org",
                )
            ):
                continue
            if e1.lower().endswith(".launch"):
                continue
            # $ SKIP:
            # Skip VSCode stuff
            if any(
                e1.lower() == s
                for s in (
                    ".vscode",
                    ".devcontainer",
                )
            ):
                continue
            # $ SKIP:
            # 'hardware.json5'
            # Was used to extract the names of the chip, board and probe. No need to copy into final
            # project.
            if e1.lower() == "hardware.json5":
                continue
            # $ SKIP:
            # 'readme.txt'
            # Will be used later to generate a new 'readme.txt' file. No need to copy right now.
            if e1.lower() == "readme.txt":
                continue

            # & ELEMENTS TO COPY DIFFERENTLY
            # Everything that passed the filters above should end up in the '<project>/source' fol-
            # der. However, there are a few exceptions, listed below.
            e2 = e1
            # $ EXCEPTION:
            # 'chip.json5', 'board.json5' and 'probe.json5'
            # Override files must end up in the '<project>/.beetle' folder.
            if e1.lower() in ("chip.json5", "board.json5", "probe.json5"):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/.beetle/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # Rename 'src' and 'user' into 'user_code'
            if e1.lower() == "src" or e1.lower() == "user":
                # Unless it's for CIP United
                if "cip-united" in boardname:
                    pass
                else:
                    e2 = "user_code"
            # $ EXCEPTION:
            # A 'filetree_config.btl' file should be copied into the '<project>/.beetle' folder
            if e1 == "filetree_config.btl":
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/.beetle/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # A 'chip_config.json5' and 'chip_config.svd' must be copied into '<project>/.beetle'
            if (
                (e1.lower() == "chip_config.json")
                or (e1.lower() == "chip_config.json5")
                or (e1.lower() == "chip_config.tjson5")
                or (e1.lower() == "chip_config.svd")
            ):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/.beetle/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # A 'template/' folder must be copied to '<project>/template'
            if (e1.lower() == "template") or (e1.lower() == "templates"):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/template",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # An 'openocd/' folder must be copied to '<project>/config/openocd'. Same for
            # 'gdb-scripts'.
            if any(
                e1.lower() == s
                for s in (
                    "openocd",
                    "gdb-scripts",
                )
            ):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/config/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # A 'tag_data/' folder must be copied to '<project>/tag_data'
            if e1.lower() == "tag_data":
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/tag_data",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # A 'source/' folder must not end up as '<project>/source/source' but simply as
            # '<project>/source'
            if e1.lower() == "source":
                copy_source_code(f"{_src_abspath}/{e1}", _dst_abspath)
                continue
            # $ EXCEPTION:
            # A 'resources/' folder can remain toplevel
            if e1.lower() == "resources":
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # A '.git', '.github', '.settings', '.vscode' folder must end up directly in
            # '<project>/'. Same for a '.gitignore', '.gitmodules' file.
            if any(
                e1.lower() == s
                for s in (
                    ".git",
                    ".github",
                    ".gitignore",
                    ".gitmodules",
                )
            ):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue
            # $ EXCEPTION:
            # The '.ino' Arduino sketch must end up toplevel. Otherwise, in a 'replacement' option,
            # the '.ino' sketch file would end up in the 'source/' subfolder, thereby no longer
            # useable to invoke the Arduino compiler!
            if e1.lower().endswith(".ino"):
                filefunctions.copy(
                    src=f"{_src_abspath}/{e1}",
                    dst=f"{_dst_abspath}/{e2}",
                    printfunc=functions.importer_printfunc,
                )
                continue

            # & NORMAL COPY
            # All other files and folders go into '<project>/source'
            filefunctions.copy(
                src=f"{_src_abspath}/{e1}",
                dst=f"{_dst_abspath}/source/{e2}",
                printfunc=functions.importer_printfunc,
            )
            continue
        return

    copy_source_code(src_abspath, dst_abspath)

    # & Copy readme file
    readme_content = __get_readme_content(
        original_readme_path=f"{src_abspath}/readme.txt",
        boardname=boardname,
        chipname=chipname,
        probename=probename,
    )
    with open(
        f"{dst_abspath}/readme.txt",
        "w",
        encoding="utf-8",
        newline="\n",
        errors="replace",
    ) as f:
        f.write(readme_content)

    # & Convert encodings
    if convert_encoding:
        functions.importer_printfunc("Convert file encodings[", end="")
        filefunctions.convert_file_encodings_recursively(
            target_abspath=dst_abspath,
            verbose=False,
            miniverbose=True,
            printfunc=functions.importer_printfunc,
        )
        functions.importer_printfunc("]\n")

    # & Unixify line endings
    if convert_line_endings:
        functions.importer_printfunc("Convert line endings[", end="")
        filefunctions.unixify_line_endings_recursively(
            target_abspath=dst_abspath,
            verbose=False,
            miniverbose=True,
            printfunc=functions.importer_printfunc,
        )
        functions.importer_printfunc("]\n")

    # & Fix compiler warnings
    functions.importer_printfunc("Fix warnings[", end="")
    _fix_warnings_.fix_source_tree(
        rootpath=dst_abspath,
        verbose=False,
        miniverbose=True,
        printfunc=functions.importer_printfunc,
    )
    functions.importer_printfunc("]\n")
    return True


def __create_empty_project_skeleton(
    proj_rootpath: str,
    boardname: str,
    chipname: str,
    probename: str,
) -> None:
    """"""
    # * Apply override data files
    _hardware_api_.HardwareDB().clean_overrides_db()
    _hardware_api_.HardwareDB().parse_overrides_db(proj_rootpath)

    # * Extract dictionaries
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)

    # * Clean
    if os.path.isdir(proj_rootpath):
        filefunctions.clean(
            proj_rootpath, printfunc=functions.importer_printfunc
        )
    else:
        filefunctions.makedirs(
            proj_rootpath, printfunc=functions.importer_printfunc
        )

    # * Build skeleton
    filefunctions.makedirs(
        f"{proj_rootpath}/source", printfunc=functions.importer_printfunc
    )
    filefunctions.makedirs(
        f"{proj_rootpath}/build", printfunc=functions.importer_printfunc
    )
    filefunctions.makedirs(
        f"{proj_rootpath}/config", printfunc=functions.importer_printfunc
    )
    filefunctions.makedirs(
        f"{proj_rootpath}/.beetle", printfunc=functions.importer_printfunc
    )
    filefunctions.makedirs(
        f"{proj_rootpath}/.beetle/.config_orig",
        printfunc=functions.importer_printfunc,
    )
    filefunctions.makedirs(
        f"{proj_rootpath}/.beetle/.cache",
        printfunc=functions.importer_printfunc,
    )

    # * Build resources
    # & Generate 'makefile'
    abspath = f"{proj_rootpath}/config/makefile"
    content = _file_generator_.get_new_makefile(
        boardname=boardname,
        chipname=chipname,
        version="latest",
    )
    with open(
        abspath, "w", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(content)

    # & Generate 'dashboard.mk'
    abspath = f"{proj_rootpath}/config/dashboard.mk"
    content = _file_generator_.get_new_dashboard_mk(
        proj_rootpath=proj_rootpath,
        boardname=boardname,
        chipname=chipname,
        probename=probename,
    )
    with open(
        abspath, "w", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(content)

    # & Generate 'filetree.mk'
    abspath = f"{proj_rootpath}/config/filetree.mk"
    content = _file_generator_.get_new_filetree_mk_template()
    with open(
        abspath, "w", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(content)

    # & Generate linkerscripts
    linkerscript_dict = _file_generator_.get_new_linkerscripts(
        boardname=boardname,
        chipname=chipname,
    )
    for name in linkerscript_dict.keys():
        content = linkerscript_dict[name]
        abspath = f"{proj_rootpath}/config/{name}"
        with open(
            abspath, "w", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            f.write(content)
        continue

    # & Generate 'openocd_probe.cfg' and 'openocd_chip.cfg'
    if "openocd" in str(chip_dict.get("default_flashtool_uid")).lower():
        abspath = f"{proj_rootpath}/config/openocd_probe.cfg"
        content = _file_generator_.get_new_openocd_probecfg_file(
            boardname=boardname,
            chipname=chipname,
            probename=probename,
        )
        with open(
            abspath, "w", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            f.write(content)
        abspath = f"{proj_rootpath}/config/openocd_chip.cfg"
        content = _file_generator_.get_new_openocd_chipcfg_file(
            boardname=boardname,
            chipname=chipname,
        )
        with open(
            abspath, "w", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            f.write(content)

    # & Copy bootloaders
    # $ Bootloader original locations
    bootloader_src_relpaths = chip_dict["boot"]["bootloaders"]
    if (bootloader_src_relpaths is None) or (len(bootloader_src_relpaths) == 0):
        # Nothing to copy
        pass
    else:
        bootloader_src_abspaths = [
            purefunctions.join_resources_dir_to_path(p)
            for p in bootloader_src_relpaths
        ]
        # $ Bootloader target locations
        bootloader_dst_folder = f"{proj_rootpath}/config/bootloaders"
        filefunctions.makedirs(
            bootloader_dst_folder, printfunc=functions.importer_printfunc
        )
        bootloader_dst_abspaths = [
            f'{bootloader_dst_folder}/{bootloader_src_file.split("/")[-1]}'
            for bootloader_src_file in bootloader_src_abspaths
        ]
        # $ Do the copy
        for bootloader_src_file, bootloader_dst_file in zip(
            bootloader_src_abspaths, bootloader_dst_abspaths
        ):
            filefunctions.copy(
                bootloader_src_file,
                bootloader_dst_file,
                printfunc=functions.importer_printfunc,
            )

    # & Copy bootswitches
    # $ Bootswitch original locations
    bootswitch_src_relpaths = chip_dict["boot"]["bootswitches"]
    if (bootswitch_src_relpaths is None) or (len(bootswitch_src_relpaths) == 0):
        # Nothing to copy
        pass
    else:
        bootswitch_src_abspaths = [
            purefunctions.join_resources_dir_to_path(p)
            for p in bootswitch_src_relpaths
        ]
        # $ Bootswitch target locations
        bootswitch_dst_folder = f"{proj_rootpath}/config/bootswitches"
        filefunctions.makedirs(
            bootswitch_dst_folder, printfunc=functions.importer_printfunc
        )
        bootswitch_dst_abspaths = [
            f'{bootswitch_dst_folder}/{bootswitch_src_file.split("/")[-1]}'
            for bootswitch_src_file in bootswitch_src_abspaths
        ]
        # $ Do the copy
        for bootswitch_src_file, bootswitch_dst_file in zip(
            bootswitch_src_abspaths, bootswitch_dst_abspaths
        ):
            filefunctions.copy(
                bootswitch_src_file,
                bootswitch_dst_file,
                printfunc=functions.importer_printfunc,
            )

    # & Copy partitions
    # $ Partitions original locations
    partitions_src_relpaths = chip_dict["boot"]["partitions"]
    if (partitions_src_relpaths is None) or (len(partitions_src_relpaths) == 0):
        # Nothing to copy
        pass
    else:
        partitions_src_abspaths = [
            purefunctions.join_resources_dir_to_path(p)
            for p in partitions_src_relpaths
        ]
        # $ Partitions target locations
        partitions_dst_folder = f"{proj_rootpath}/config/partitions"
        filefunctions.makedirs(
            partitions_dst_folder, printfunc=functions.importer_printfunc
        )
        partitions_dst_abspaths = [
            f'{partitions_dst_folder}/{partitions_src_file.split("/")[-1]}'
            for partitions_src_file in partitions_src_abspaths
        ]
        # $ Do the copy
        for partitions_src_file, partitions_dst_file in zip(
            partitions_src_abspaths, partitions_dst_abspaths
        ):
            filefunctions.copy(
                partitions_src_file,
                partitions_dst_file,
                printfunc=functions.importer_printfunc,
            )

    # & Generate 'dashboard_config.btl'
    dashboard_config_dict = {
        "project_type": "makefile",
        "project_version": "7",
        "chip_name": chipname,
        "board_name": boardname,
        "probe_name": probename,
        "transport_protocol": probe_dict["transport_protocols"][0],
        "COM_port": None,
    }
    dashboard_config_dict.update(
        _file_generator_.get_default_project_layout(
            proj_rootpath=proj_rootpath,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
            ignore_list=["FILETREE_MK", "DASHBOARD_MK", "BUTTONS_BTL"],
            relative=True,
            rootid="<project>",
        )
    )
    for category_unicum in _hardware_api_.HardwareDB().list_toolcat_unicums(
        True
    ):
        assert isinstance(category_unicum, _toolcat_unicum_.TOOLCAT_UNIC)
        dashboard_config_dict[category_unicum.get_name()] = (
            category_unicum.get_default_unique_id(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
            )
        )
        continue
    _file_generator_.write_dashboard_config(
        dashboard_config_abspath=f"{proj_rootpath}/.beetle/dashboard_config.btl",
        dashboard_config_dict=dashboard_config_dict,
    )


def __get_readme_content(
    original_readme_path: str,
    boardname: str,
    chipname: str,
    probename: str,
) -> str:
    """Generate content for a readme file to be inserted in the given project.

    The content will be based on the original 'readme.txt' file and insert a few
    basic lines before that.
    """
    # $ Write basic info
    board_dict = _hardware_api_.HardwareDB().get_board_dict(boardname)
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, None)
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)
    new_content_lines = [
        f"microcontroller: {chipname}",
        f"board: {boardname}",
        f'microcontroller manufacturer: {chip_dict["manufacturer"]}',
        f'board manufacturer: {board_dict["manufacturer"]}',
    ]
    if (boardname != "custom") and (boardname != "none"):
        new_content_lines.append(f'link: {board_dict["link"]}\n')
    else:
        new_content_lines.append(f'link: {chip_dict["link"]}\n')

    # $ Write content from original readme file
    original_content = "No readme file found in original project."
    if os.path.isfile(original_readme_path):
        with open(
            original_readme_path,
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            original_content = f.read()
    new_content_lines.append("")
    if original_content.startswith("Info:"):
        original_content = original_content.replace("Info:", "info:", 1)
    if original_content.startswith("info:"):
        pass
    else:
        new_content_lines.append("info:")
    new_content_lines.append(original_content)

    # $ Return as string
    return "\n".join(new_content_lines)
