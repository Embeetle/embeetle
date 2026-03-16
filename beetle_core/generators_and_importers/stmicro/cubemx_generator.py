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
import sys
import os
import argparse
import traceback

my_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
parent_dir = os.path.dirname(my_dir).replace("\\", "/")
grandparent_dir = os.path.dirname(parent_dir).replace("\\", "/")
try:
    import data, purefunctions, functions, filefunctions, os_checker
    import hardware_api.hardware_api as _hardware_api_
    import hardware_api.file_generator as _file_generator_
    import generators_and_importers.stmicro.importer as _stmicro_importer_
    import generators_and_importers.helper as _helper_
except:
    sys.path.insert(0, grandparent_dir)
    import data, purefunctions, functions, filefunctions, os_checker
    import hardware_api
    import hardware_api.hardware_api as _hardware_api_
    import hardware_api.file_generator as _file_generator_
    import generator
    import generators_and_importers.stmicro
    import generators_and_importers.stmicro.importer as _stmicro_importer_
    import generators_and_importers.helper as _helper_
q = "'"
dq = '"'


def __help() -> None:
    """Help message in console."""
    header = (
        "\n"
        + "=" * 80
        + "\n"
        + "|"
        + " " * 28
        + "CUBEMX GENERATOR TOOL"
        + " " * 29
        + "|"
        + "\n"
        + "=" * 80
    )
    functions.generator_printfunc(header, color="yellow")
    functions.generator_printfunc(f"Only for internal use!\n")
    functions.generator_printfunc(
        f"SUMMARY\n" f"=======",
        color="yellow",
    )
    functions.generator_printfunc(
        f"This tool generates a CubeMX project based on a {q}cubemx.ioc{q} file.\n"
        f"The sample project it starts from typically looks like this:\n"
        f"\n"
        f"  nucleo-f303k8\n"
        f"     ├ cubemx.ioc\n"
        f"     └ readme.txt\n"
        f"\n"
        f"with {q}cubemx.ioc{q} being either a full fledged {q}.ioc{q} file itself, or a pointer\n"
        f"to a {q}.ioc{q} file in the CubeMX database.\n"
        f"The result is a CubeMX project (not an Embeetle project!) in the destination\n"
        f"folder, usually a temporary directory. The next step is to import that, which\n"
        f"can be done with the toplevel importer tool.\n"
    )
    functions.generator_printfunc(
        f"ARGUMENTS\n" f"=========",
        color="yellow",
    )
    functions.generator_printfunc("--src".ljust(8), color="yellow", end="")
    functions.generator_printfunc(
        f"Source folder, eg. {dq}C:/sample_proj_resources/stmicro/projects/nucleo/nucleo-f303k8{dq}."
    )
    functions.generator_printfunc("--dst".ljust(8), color="yellow", end="")
    functions.generator_printfunc(
        f"Destination folder, eg. {dq}C:/Users/krist/AppData/Local/Temp/tmpjygwckqi{dq}.\n"
    )
    functions.generator_printfunc(
        f"NOTES\n" f"=====",
        color="yellow",
    )
    functions.generator_printfunc(
        f"I{q}ve developed this script as a standalone tool, such that it can be invoked\n"
        f"in a newly launched terminal, to keep the main terminal clean.\n"
    )
    return


def __generate_cubemx_project(src_abspath: str, dst_abspath: str) -> None:
    """Generate a CubeMX project based on the 'cubemx.ioc' file in the sample
    project (given by 'src_ abspath') and put it in the given 'dst_abspath'
    directory.

    This function finds the 'cubemx.ioc' file automatically and then determines
    if that file is the actual '.ioc' file or just a pointer to one in the
    CubeMX database.
    """
    cubemx_executable_path: str = __get_cubemx_abspath()
    javapath: str = __get_java_abspath()
    cubemx_installation_path: str = os.path.dirname(
        cubemx_executable_path
    ).replace("\\", "/")
    boardmanager_path: str = (
        f"{cubemx_installation_path}/db/plugins/boardmanager/boards"
    )
    cubemx_script_path: str = f"{dst_abspath}/cubemx_script.txt"
    cubemx_ioc_path: str = f"{dst_abspath}/cubemx_project.ioc"
    cubemx_original_ioc_path: Optional[str] = None

    # & Define original '.ioc' file
    # The original '.ioc' file will be used as a basis to generate the CubeMX project. Further on,
    # we'll generate a new '.ioc' file with a few minor modifications (eg. turning on a switch for
    # Freertos if applicable, ...). The original '.ioc' file should be in the sample project, stored
    # as 'cubemx.ioc'. It can contain the actual '.ioc' code, or it can contain a pointer to the
    # file in the CubeMX database.
    cubemx_original_ioc_path = _stmicro_importer_.find_original_ioc_file(
        ioc_abspath=f"{src_abspath}/cubemx.ioc"
    )

    # & Extract hardware from original '.ioc' file
    if os.path.isfile(f"{src_abspath}/hardware.json5"):
        boardname, chipname, probename = _helper_.read_hardware_from_src(
            src_abspath
        )
    else:
        try:
            board_unicum, chip_unicum, probe_unicum = (
                _stmicro_importer_.extract_data_from_ioc_file(
                    cubemx_original_ioc_path
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

    # & Create new '.ioc' file
    # Create a 'cubemx_script.txt' in the target folder. We'll fire up CubeMX with this script,
    # which will save the project as 'cubemx_project.ioc' in the target folder. That's the new
    # '.ioc' file we need to generate the project code. It will have a few minor modifications
    # compared to the original '.ioc' file.
    # $ Load original '.ioc' file
    content = ""
    content += (
        f'config load {dq}{cubemx_original_ioc_path.replace("/", os.sep)}{dq}\n'
    )
    content += f"project toolchain Makefile\n"
    content += f"project name cubemx_project\n"
    # $ Disable modules for STM32F746NG and STM32F429ZI
    if ("f746ng" in chipname) or ("f429zi" in chipname):
        content += f"reset mode FATFS {dq}SDIO{dq}\n"
        content += f"reset mode FREERTOS {dq}CMSIS_V1{dq}\n"
        content += f"reset mode USB_HOST {dq}CDC_FS{dq}\n"
        content += f"reset mode USB_OTG_FS {dq}Host_Only{dq}\n"
        content += f"reset mode ETH {dq}RMII{dq}\n"
        content += f"reset mode SDMMC1 {dq}SD_4_bits_Wide_bus{dq}\n"
        content += f"reset mode SPI2 {dq}Full_Duplex_Master{dq}\n"
    # $ Enable freertos if applicable
    if "freertos" in src_abspath.lower():
        TIM = None
        if "l053r8" in chipname:
            TIM = "TIM2"
        else:
            TIM = "TIM1"
        # content += "set mode FREERTOS Enabled\n"
        content += f"set mode FREERTOS CMSIS_V1\n"
        content += f"set mode SYS {TIM}\n"
    # $ Add save instructions
    content += f'config saveas {dq}{cubemx_ioc_path.replace("/", os.sep)}{dq}\n'
    content += f"exit\n"
    # $ Save the script
    with open(
        cubemx_script_path,
        "w",
        encoding="utf-8",
        newline="\n",
        errors="replace",
    ) as f:
        f.write(content)
    # $ Run the cubemx script to create the '.ioc' file
    cmd = str(
        f'{dq}{javapath.replace("/", os.sep)}{dq} '
        f'-jar {dq}{cubemx_executable_path.replace("/", os.sep)}{dq} '
        f'-q {dq}{cubemx_script_path.replace("/", os.sep)}{dq}'
    )
    p = purefunctions.subprocess_popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        verbose=True,
    )
    p.communicate()
    assert os.path.isfile(cubemx_ioc_path)
    filefunctions.delete(
        cubemx_script_path, printfunc=functions.generator_printfunc
    )

    # & Generate code from new '.ioc' file
    # Create again a 'cubemx_script.txt' file that will generate the code from the '.ioc' file.
    # $ Define content
    content = ""
    content += f'config load {dq}{cubemx_ioc_path.replace("/", os.sep)}{dq}\n'
    content += f"project generate\n"
    content += f"exit\n"
    # $ Save the script
    with open(
        cubemx_script_path,
        "w",
        encoding="utf-8",
        newline="\n",
        errors="replace",
    ) as f:
        f.write(content)
    # $ Run the cubemx script to generate the code
    cmd = str(
        f'{dq}{javapath.replace("/", os.sep)}{dq} '
        f'-jar {dq}{cubemx_executable_path.replace("/", os.sep)}{dq} '
        f'-q {dq}{cubemx_script_path.replace("/", os.sep)}{dq}'
    )
    p = purefunctions.subprocess_popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        verbose=True,
    )
    p.communicate()
    filefunctions.delete(
        cubemx_script_path, printfunc=functions.generator_printfunc
    )
    # $ Cleanup
    # A folder named 'cubemx_project' appears at the same level as the 'dst_abspath' for unknown
    # reasons.
    unknown_tempfolder = (
        os.path.dirname(dst_abspath).replace("\\", "/") + "/cubemx_project"
    )
    if os.path.isdir(unknown_tempfolder):
        filefunctions.delete(
            unknown_tempfolder, printfunc=functions.generator_printfunc
        )

    # & Modify 'main.c'
    try:
        mainpath = f"{dst_abspath}/Src/main.c"
        if not os.path.isfile(mainpath):
            for _r_, _d_, _f_ in os.walk(dst_abspath):
                for fname in _f_:
                    if fname == "main.c":
                        mainpath = f"{_r_}/main.c"
                        _d_[:] = []
                        _f_[:] = []
                        break
                    continue
                if os.path.isfile(mainpath):
                    break
                continue
        if not os.path.isfile(mainpath):
            functions.generator_printfunc(f"Cannot find {q}main.c{q}!")
            input(f"Press any key to continue...")
        if os.path.isfile(mainpath):
            content = _file_generator_.get_new_adapted_cubemx_mainfile(
                proj_rootpath=dst_abspath,
                boardname=boardname,
                chipname=chipname,
                freertos="freertos" in src_abspath.lower(),
                printfunc=print,
                catch_err=False,
            )
            assert content is not None
            with open(
                mainpath, "w", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                f.write(content)
    except:
        traceback.print_exc()
        input("Press any key to continue...")

    # & Copy 'readme.txt'
    if os.path.isfile(f"{src_abspath}/readme.txt"):
        filefunctions.copy(
            src=f"{src_abspath}/readme.txt",
            dst=f"{dst_abspath}/readme.txt",
            verbose=True,
            exit_on_fail=True,
            printfunc=functions.generator_printfunc,
        )

    # & Copy 'hardware.json5'
    if os.path.isfile(f"{src_abspath}/hardware.json5"):
        filefunctions.copy(
            src=f"{src_abspath}/hardware.json5",
            dst=f"{dst_abspath}/hardware.json5",
            verbose=True,
            exit_on_fail=True,
            printfunc=functions.generator_printfunc,
        )
    return


def __get_java_abspath() -> str:
    """Return path to java executable."""
    if os.path.isfile(
        "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/jre/bin/java.exe"
    ):
        return "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/jre/bin/java.exe"
    if os.path.isfile("C:/ProgramData/Oracle/Java/javapath/java.exe"):
        return "C:/ProgramData/Oracle/Java/javapath/java.exe"
    if os.path.isfile(
        "C:/Program Files (x86)/Common Files/Oracle/Java/javapath/java.exe"
    ):
        return (
            "C:/Program Files (x86)/Common Files/Oracle/Java/javapath/java.exe"
        )
    if os.path.isfile("C:/Program Files (x86)/Java/jre1.8.0_211/bin/java.exe"):
        return "C:/Program Files (x86)/Java/jre1.8.0_211/bin/java.exe"
    if os.path.isfile("C:/Program Files (x86)/Java/jre1.8.0_231/bin/java.exe"):
        return "C:/Program Files (x86)/Java/jre1.8.0_231/bin/java.exe"
    if os.path.isfile("C:/Program Files/Java/jre1.8.0_231/bin/java.exe"):
        return "C:/Program Files/Java/jre1.8.0_231/bin/java.exe"
    if os.path.isfile("C:/Program Files/Java/jre1.8.0_291/bin/java.exe"):
        return "C:/Program Files/Java/jre1.8.0_291/bin/java.exe"
    raise RuntimeError()


def __get_cubemx_abspath() -> str:
    """Return path to CubeMX executable."""
    if os.path.isfile(
        "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    ):
        return "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    if os.path.isfile(
        "C:/Program Files (x86)/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    ):
        return "C:/Program Files (x86)/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    raise RuntimeError()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate STMicro project with CubeMX", add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--src", action="store")
    parser.add_argument("--dst", action="store")
    args = parser.parse_args()
    if args.help:
        __help()
        sys.exit(0)
    try:
        _src: str = args.src.replace(q, "").replace(dq, "").strip()
        _dst: str = args.dst.replace(q, "").replace(dq, "").strip()
    except:
        functions.generator_printfunc(
            f"ERROR: Cannot parse arguments!",
            color="error",
        )
        __help()
        sys.exit(1)
    data.embeetle_toplevel_folder = os.path.dirname(grandparent_dir).replace(
        "\\", "/"
    )
    data.beetle_core_directory = f"{data.embeetle_toplevel_folder}/beetle_core"
    data.beetle_tools_directory = (
        f"{data.settings_directory}/beetle_tools"
    )
    data.beetle_project_generator_folder = (
        f"{data.embeetle_toplevel_folder}/../beetle_project_generator"
    )
    data.beetle_licenses_directory = f"{data.embeetle_toplevel_folder}/licenses"
    data.sys_directory = f"{data.embeetle_toplevel_folder}/sys"

    # sys/bin
    sys_bin_candidates = (
        f"{data.embeetle_toplevel_folder}/sys/bin",
        f"{data.embeetle_toplevel_folder}/sys/{os_checker.get_os_with_arch()}/bin",
        f"{data.embeetle_toplevel_folder}/sys/{os_checker.get_os()}/bin"
    )
    data.sys_bin = sys_bin_candidates[0]
    if not os.path.exists(data.sys_bin):
        data.sys_bin = sys_bin_candidates[1]
        if not os.path.exists(data.sys_bin):
            print(
                f"ERROR: Cannot find\n"
                f"{dq}{sys_bin_candidates[0]}{dq}\n"
                f"nor\n"
                f"{dq}{sys_bin_candidates[1]}{dq}\n"
                f"nor\n"
                f"{dq}{sys_bin_candidates[2]}{dq}\n"
            )

    # sys/lib
    sys_lib_candidates = (
        f"{data.embeetle_toplevel_folder}/sys/lib",
        f"{data.embeetle_toplevel_folder}/sys/{os_checker.get_os_with_arch()}/lib",
        f"{data.embeetle_toplevel_folder}/sys/{os_checker.get_os()}/lib"
    )
    data.sys_lib = sys_lib_candidates[0]
    if not os.path.exists(data.sys_lib):
        data.sys_lib = sys_lib_candidates[1]
        if not os.path.exists(data.sys_lib):
            print(
                f"ERROR: Cannot find\n"
                f"{dq}{sys_lib_candidates[0]}{dq}\n"
                f"nor\n"
                f"{dq}{sys_lib_candidates[1]}{dq}\n"
                f"nor\n"
                f"{dq}{sys_lib_candidates[2]}{dq}\n"
            )
    data.resources_directory = (
        f"{data.beetle_project_generator_folder}/resources"
    )
    try:
        __generate_cubemx_project(
            src_abspath=_src,
            dst_abspath=_dst,
        )
    except:
        traceback.print_exc()
    sys.exit(0)
