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
import os, re, tempfile, traceback
import purefunctions, data, filefunctions, functions
import generators_and_importers.fix_warnings as _fix_warnings_
import beetlifyer as _beetlifyer_
import hardware_api.hardware_api as _hardware_api_
import generators_and_importers.compilation_extractor as _compilation_extractor_
import generators_and_importers.arduino.locator as _arduino_locator_
from various.kristofstuff import *
import os_checker


def import_arduino_project(
    arduinosketch_filepath: str,
    dst_abspath: str,
    boardname: str,
    chipname: str,
    probename: str,
    convert_line_endings: bool = True,
    convert_encoding: bool = True,
) -> bool:
    """
    :param arduinosketch_filepath: Absolute path to the arduino '.ino' sketch file. Also accepted
                                   (but not recommended) is the parental folder of this sketch file.
    :param dst_abspath:            Absolute path to the folder where the resulting Embeetle project
                                   should end up. Accepted:
                                   - Empty target directory
                                   - Non-empty target directory (will be cleaned)
                                   - Parent of sketch file, which indicates the 'Replacement' option
                                   - Sketch file, which indicates the 'Replacement' option

    :return: success
    """
    input_folderpath: Optional[str] = None
    output_folderpath: Optional[str] = None
    archive_src_folder: Optional[str] = None
    archive_dst_folder: Optional[str] = None

    # $ Parameter 'arduinosketch_filepath'
    arduinosketch_filepath = arduinosketch_filepath.replace("\\", "/")
    if arduinosketch_filepath.endswith(".ino"):
        assert os.path.isfile(arduinosketch_filepath)
    else:
        # It might be the toplevel folder
        arduinosketch_filepath = f'{arduinosketch_filepath}/{arduinosketch_filepath.split("/")[-1]}.ino'
        assert os.path.isfile(arduinosketch_filepath)
    input_folderpath = os.path.dirname(arduinosketch_filepath).replace(
        "\\", "/"
    )

    # $ Parameter 'dst_abspath'
    if os.path.isfile(dst_abspath):
        output_folderpath = os.path.dirname(dst_abspath).replace("\\", "/")
    else:
        output_folderpath = dst_abspath

    board_dict = _hardware_api_.HardwareDB().get_board_dict(boardname)
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)

    # * STEP 1: PREPARE TARGET DIRECTORY
    functions.importer_printfunc(
        "\n"
        "STEP 1: PREPARE TARGET DIRECTORY\n"
        "================================",
        color="blue",
        bright=True,
    )
    _beetlifyer_.beetlify_project(
        src_abspath=input_folderpath,
        dst_abspath=output_folderpath,
        boardname=boardname,
        chipname=chipname,
        probename=probename,
        convert_line_endings=convert_line_endings,
        convert_encoding=convert_encoding,
    )

    # * STEP 2: CHECK AND INSTALL ARDUINO CORES
    functions.importer_printfunc(
        "\n"
        "STEP 2: CHECK AND INSTALL ARDUINO CORES\n"
        "=======================================",
        color="blue",
        bright=True,
    )
    # $ Check installed cores
    core_list = __list_installed_cores()

    # $ Install needed cores
    core = board_dict["arduino_params"]["core"]
    if core not in core_list:
        functions.importer_printfunc(
            f"\nCore {q}{core}{q} not found. The core will be installed.\n"
        )
        __install_core(core)
    else:
        functions.importer_printfunc(
            f"\nCore {q}{core}{q} found. Proceed to compilation.\n"
        )

    # * STEP 3: RUN ARDUINO COMPILER
    functions.importer_printfunc(
        "\n" "STEP 3: RUN ARDUINO COMPILER\n" "============================",
        color="blue",
        bright=True,
    )
    output, success = __run_arduino_cli_compiler(
        arduinosketch_filepath=arduinosketch_filepath,
        boardname=boardname,
    )
    if output is not None:
        # No more need to print the output here. It's already printed during the process run.
        # functions.importer_printfunc(output.replace('\\', '/').replace('//', '/'))
        pass

    # * STEP 4: PARSE COMPILER OUTPUT
    functions.importer_printfunc(
        "\n" "STEP 4: PARSE COMPILER OUTPUT\n" "=============================",
        color="blue",
        bright=True,
    )
    if (not success) or (output is None):
        functions.importer_printfunc(
            f"ERROR: Compiling the arduino sketch with the official\n"
            f"Arduino CLI tool failed. Embeetle will now clean-up the\n"
            f"target folder.\n",
            color="error",
        )
        return False
    core = board_dict["arduino_params"]["core"]
    cfile_list0, hfile_list0, supfile_list0, folder_list = (
        __extract_source_files(output)
    )
    cfile_list1, hfile_list1, supfile_list1 = __extract_core_files(folder_list)
    if "esp" in core:
        # There are too many libraries for the ESP, and they won't compile.
        cfile_list2, hfile_list2, supfile_list2 = [], [], []
    else:
        cfile_list2, hfile_list2, supfile_list2 = __extract_core_library_files(
            folder_list
        )

    cfile_list = list(set(cfile_list0 + cfile_list1 + cfile_list2))
    hfile_list = list(set(hfile_list0 + hfile_list1 + hfile_list2))
    supfile_list = list(set(supfile_list0 + supfile_list1 + supfile_list2))

    # & STEP 4.1: PROCESS SOURCE FILES
    for srcfile in sorted(cfile_list + hfile_list + supfile_list):
        fname = srcfile.split("/")[-1]
        folder = purefunctions.standardize_abspath(os.path.dirname(srcfile))
        targetfile = None
        # $ sketch
        # eg. /tmp/arduino_build_852524/sketch/WiFiScan.ino.cpp
        if fname.endswith(".ino.cpp"):
            targetfile = os.path.join(
                output_folderpath,
                f"source/user_code/{fname}",
            ).replace("\\", "/")
        # $ cores
        # eg. /home/kristof/.arduino15/packages/esp32/hardware/esp32/1.0.6/cores/esp32/esp32-hal-misc.c
        elif "/core" in folder.lower():
            if "/cores" in folder.lower():
                remainder = srcfile.split("/cores/")[-1]
            else:
                remainder = srcfile.split("/core/")[-1]
            targetfile = os.path.join(
                output_folderpath,
                f"source/core/{remainder}".replace("//", "/"),
            ).replace("\\", "/")
        # $ variants
        elif "/variant" in folder.lower():
            if "/variants" in srcfile:
                remainder = srcfile.split("/variants/")[-1]
            else:
                remainder = srcfile.split("/variant/")[-1]
            targetfile = os.path.join(
                output_folderpath,
                f"source/variants/{remainder}".replace("//", "/"),
            ).replace("\\", "/")
        # $ sdk
        elif "/tools/sdk" in folder.lower():
            remainder = srcfile.split("/tools/sdk/")[-1]
            targetfile = os.path.join(
                output_folderpath,
                f"source/sdk/{remainder}".replace("//", "/"),
            ).replace("\\", "/")
            # This could be the '~.arduino15/packages/esp32/hardware/esp32/1.0.6/tools/sdk/' folder.
            # That folder has a subfolder 'include/' to keep all the h-files for the archives. The
            # archive files themselves are stored in the 'lib/' subfolder. Look for this archive
            # folder and store its absolute path.
            if archive_src_folder is None:
                temp = os.path.join(
                    srcfile.split("/tools/sdk/")[0],
                    "tools/sdk/lib",
                ).replace("\\", "/")
                if os.path.isdir(temp):
                    archive_src_folder = purefunctions.standardize_abspath(temp)
                    archive_dst_folder = os.path.join(
                        output_folderpath,
                        "source/sdk/archives",
                    ).replace("\\", "/")
        # $ libraries
        elif "/libraries" in folder.lower():
            remainder = srcfile.split("/libraries/")[-1]
            targetfile = os.path.join(
                output_folderpath,
                f"source/libraries/{remainder}".replace("//", "/"),
            ).replace("\\", "/")
        # $ not known
        else:
            arduino15_folder = get_arduino15_dir()
            if srcfile.startswith(arduino15_folder):
                remainder = srcfile.replace(arduino15_folder, "", 1)
                targetfile = os.path.join(
                    output_folderpath,
                    f"source/other/{remainder}".replace("//", "/"),
                ).replace("\\", "/")
            else:
                functions.importer_printfunc(
                    f"\nWARNING: Don{q}t know what to do with file: {q}{srcfile}{q}\n",
                    color="warning",
                )
                continue

        # $ Do the copy...
        if not os.path.isfile(srcfile):
            functions.importer_printfunc(
                f"ERROR: Can{q}t copy file {q}{srcfile}{q} to {q}{targetfile}{q}. File\n"
                f"{q}{srcfile}{q} not found!",
                color="error",
            )
            continue
        assert os.path.isfile(srcfile)
        filefunctions.copy(
            src=srcfile,
            dst=targetfile,
            verbose=True,
            printfunc=functions.importer_printfunc,
        )

        # $ Postprocessing...
        # At this point, the copy has succeeded. For some files, a few modifications are needed.
        if ".ino" in fname:
            s = __process_sketch_file(
                sketchfile_abspath=targetfile,
            )
            if not s:
                functions.importer_printfunc(
                    "\nERROR: Project import failed.\n",
                    color="error",
                )
                return False
        if fname == "new.h":
            s = __process_new_dot_h_file(
                orig_filepath=srcfile,
                target_filepath=targetfile,
            )
            if not s:
                functions.importer_printfunc(
                    "\nERROR: Project import failed.\n",
                    color="error",
                )
                return False
        continue

    # & STEP 4.2: COPY ARCHIVE FILES
    # $ ESP32
    # ESP32 projects: an 'archive_src_folder' and 'archive_dst_folder' can be already defined at
    # this point. Do the copy.
    if ("esp" in chipname.lower()) and (archive_src_folder is not None):
        for archive in sorted(purefunctions.list_filepaths(archive_src_folder)):
            if not archive.endswith(".a"):
                continue
            if not os.path.isfile(archive):
                functions.importer_printfunc(
                    f"ERROR: Can{q}t copy file {q}{archive}{q} to {q}{archive_dst_folder}{q}. File\n"
                    f"{q}{archive}{q} not found!",
                    color="error",
                )
                continue
            assert os.path.isfile(archive)
            filefunctions.copy(
                src=archive,
                dst=archive_dst_folder,
                verbose=True,
                printfunc=functions.importer_printfunc,
            )
            continue
    # $ ATSAM
    # The ATSAM3X8E has an archive file stored in the 'templates' folder.
    elif "atsam3x8e" in chipname.lower():
        archive_src = purefunctions.join_resources_dir_to_path(
            "templates/microchip-atmel/sam/archives/libsam_sam3x8e_gcc_rel.a"
        )
        archive_dst = os.path.join(
            output_folderpath,
            f"source/variants/libsam_sam3x8e_gcc_rel.a",
        ).replace("\\", "/")
        if not os.path.isfile(archive_src):
            functions.importer_printfunc(
                f"ERROR: Can{q}t copy file {q}{archive_src}{q} to {q}{archive_dst}{q}. File\n"
                f"{q}{archive_src}{q} not found!",
                color="error",
            )
        else:
            filefunctions.copy(
                src=archive_src,
                dst=archive_dst,
                verbose=True,
                printfunc=functions.importer_printfunc,
            )
    # $ Other chips
    # For now, other chip families have no known archive files to be copied.
    else:
        pass

    # * STEP 5: FIX COMPILER WARNINGS
    functions.importer_printfunc(
        "\n" "STEP 5: FIX COMPILER WARNINGS\n" "=============================",
        color="blue",
        bright=True,
    )
    functions.importer_printfunc("Fix warnings[", end="")
    _fix_warnings_.fix_source_tree(
        rootpath=output_folderpath,
        verbose=False,
        miniverbose=True,
        printfunc=functions.importer_printfunc,
    )
    functions.importer_printfunc("]\n")
    return True


def __get_arduino_cli_abspath() -> str:
    """Return absolute path to 'arduino-cli' tool."""
    arduino_cli_abspath = f"{data.sys_bin}/arduino-cli"
    if os_checker.is_os("windows"):
        arduino_cli_abspath += ".exe"
    return arduino_cli_abspath


def __clean_arduino_tempfiles() -> None:
    """Run the arduino-cli tool to clean all temp files.

    Then clean them manually to be 100% sure.
    """
    # & Clean with arduino-cli tool
    arduino_cli_abspath = __get_arduino_cli_abspath()
    cmd = [
        arduino_cli_abspath,
        f"cache",
        f"clean",
        f"--verbose",
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )

    # & Manual clean
    # The 'tempfile.gettempdir()' returns a path like 'C:/Users/krist/AppData/Local/Temp'. Look for
    # arduino traces in that folder.
    tempdir = tempfile.gettempdir().replace("\\", "/")
    for c in os.listdir(tempdir):
        folder = f"{tempdir}/{c}"
        if not os.path.isdir(folder):
            continue
        if "arduino" not in folder.lower():
            continue
        filefunctions.delete(
            abspath=folder,
            verbose=True,
            printfunc=functions.importer_printfunc,
        )
        continue
    return


def __list_installed_cores() -> List[str]:
    """Run the arduino-cli tool to list all the installed cores. They are
    returned as a List[str].

    eg. cores = [     'Heltec-esp32:esp32',     'esp32:esp32',
    'esp8266:esp8266',     'stm32duino:STM32F4' ]
    """
    # & List cores with arduino-cli tool
    arduino_cli_abspath = __get_arduino_cli_abspath()
    cmd = [
        arduino_cli_abspath,
        "core",
        "list",
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )

    # & Parse output
    cores: List[str] = []
    try:
        p = re.compile(r"ID\s+Installed\s+Latest\s+Name")
        content_list = p.split(output_str, 1)
        core_content = content_list[1]
        p = re.compile(r"([-\w]+:\w+)\s")
        for m in p.finditer(core_content):
            cores.append(m.group(1))
    except:
        traceback.print_exc()
        cores = []
    return cores


def __install_core(core: str) -> None:
    """Install the given core with the 'arduino-cli' tool.

    eg. core = 'arduino:avr'        # Arduino AVR Boards          =
    'arduino:megaavr'    # Arduino megaAVR Boards          = 'arduino:nrf52' #
    Arduino nRF52 Boards          = 'arduino:sam'        # Arduino SAM Boards
    (32-bits ARM Cortex-M3)          = 'arduino:samd'       # Arduino SAMD
    Boards (32-bits ARM Cortex-M0+)          = 'arduino:mbed'       # Arduino
    mbed-enabled Boards
    """
    arduino_cli_abspath = __get_arduino_cli_abspath()

    # & Write config init file
    cmd_list = []
    # For non-AVR boards, additional package indexes must be added to the Arduino CLI, and the
    # core index must be updated. Start by writing the config init file. It gets saved to a place
    # like 'C:/Users/krist/AppData/Local/Arduino15/arduino-cli.yaml'.
    cmd = [
        arduino_cli_abspath,
        "config",
        "init",
        "--additional-urls",
        "https://dl.espressif.com/dl/package_esp32_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json",
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )

    # & Core update
    cmd = [
        arduino_cli_abspath,
        "core",
        "update-index",
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )

    # & Core search
    cmd = [
        arduino_cli_abspath,
        "core",
        "search",
        core,
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )

    # & Core install
    cmd = [
        arduino_cli_abspath,
        "core",
        "install",
        core,
    ]
    returncode, output_str, err_str = (
        purefunctions.launch_subprocess_with_printout(
            cmd,
            verbose=True,
            replace_bsl=True,
            printfunc=functions.importer_printfunc,
        )
    )
    return


def __run_arduino_cli_compiler(
    arduinosketch_filepath: str, boardname: str
) -> Tuple[Optional[str], bool]:
    """Run the arduino-cli tool to compile the given sketch for the given board.
    Catch the compiler output and return it.

    COMPILE FLAGS
    =============
    More info on compile flags at
    https://arduino.github.io/arduino-cli/latest/commands/arduino-cli_compile/

    Used compile flags:
      --fqbn        # Fully Qualified Board Name, e.g.: arduino:avr:uno

      --libraries   # List of custom libraries paths separated by commas. Can also be used multiple
                    # times for multiple libraries paths.

      --clean       # Optional, cleanup the build folder and do not use any cached build.

    Interesting (unused) flags:
      --show-properties  # Show all build properties used instead of compiling.

    :return:    output, success
    """
    homedir = data.user_directory
    arduino_cli_abspath = __get_arduino_cli_abspath()
    arduinosketch_dirpath = (
        os.path.dirname(arduinosketch_filepath).replace("\\", "/").rstrip("/")
    )

    # $ List libraries
    libraries_parameter: List[str] = []
    for name, folders in _arduino_locator_.list_arduino_libraries().items():
        assert name in (
            "dot_embeetle",
            "arduino_sketchbook",
            "arduino15",
            "arduino_installation",
        )
        for folder in folders:
            libraries_parameter.append("--libraries")
            libraries_parameter.append(folder)
            continue
        continue

    # $ arduino-cli compile command
    board_dict = _hardware_api_.HardwareDB().get_board_dict(boardname)
    fqbn = board_dict["arduino_params"]["fqbn"]
    cmd = [
        arduino_cli_abspath,
        "compile",
        "--fqbn",
        fqbn,
        *libraries_parameter,
        arduinosketch_dirpath,
        "--verbose",
        "--clean",
    ]
    # EXAMPLE
    # -------
    # cmd = [
    #    'C:/Users/krist/EMBEETLE IDE/embeetle/sys/bin/arduino-cli.exe',
    #    'compile',
    #    '--fqbn',
    #    'arduino:avr:uno',
    #    '--libraries',
    #    'C:/Users/krist/.embeetle/libraries',
    #    '--libraries',
    #    'C:/Users/krist/Documents/Arduino/libraries',
    #    '--libraries',
    #    'C:/Users/krist/AppData/Local/Arduino15/packages/arduino/hardware/avr/1.8.6/libraries',
    #    '--libraries',
    #    'C:/Users/krist/AppData/Local/Arduino15/packages/arduino/hardware/megaavr/1.8.8/libraries',
    #    '--libraries',
    #    'C:/Users/krist/AppData/Local/Arduino15/packages/arduino/hardware/sam/1.6.12/libraries',
    #    '--libraries',
    #    'C:/Users/krist/AppData/Local/Arduino15/staging/libraries',
    #    'C:/Users/krist/Downloads/Adafruit_ILI9341/Adafruit_ILI9341/examples/graphicstest',
    #    '--verbose',
    #    '--clean'
    # ]
    try:
        returncode, output_str, err_str = (
            purefunctions.launch_subprocess_with_printout(
                cmd,
                verbose=True,
                replace_bsl=True,
                printfunc=functions.importer_printfunc,
            )
        )
        if returncode != 0:
            return output_str, False
    except:
        traceback.print_exc()
        return traceback.format_exc(), False
    return output_str, True


def __extract_source_files(
    compiler_output: str,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Parse the given compiler output to find source files and support files.
    Return them in three lists. Also add a list of all the folders that are
    somehow involved (containing at least one of the listed files).

    :return: cfile_list, hfile_list, supfile_list, folder_list
    """
    compiler_output = compiler_output.replace("\\", "/").replace("//", "/")

    # & cfiles
    # Define a list of regexes to identify cfiles in the compiler output. The first half of the re-
    # gexes has no quotes, so it doesn't allow spaces. The second half is quoted and therefore al-
    # lows spaces.
    regex_list = [
        r"([-~:\w\d/\.]+[.]S)\s",
        r"([-~:\w\d/\.]+[.]s)\s",
        r"([-~:\w\d/\.]+[.]asm)\s",
        r"([-~:\w\d/\.]+[.]c)\s",
        r"([-~:\w\d/\.]+[.]C)\s",
        r"([-~:\w\d/\.]+[.]cpp)\s",
        r'"([-~:\w\d /\.]+[.]S)"\s',
        r'"([-~:\w\d /\.]+[.]s)"\s',
        r'"([-~:\w\d /\.]+[.]asm)"\s',
        r'"([-~:\w\d /\.]+[.]c)"\s',
        r'"([-~:\w\d /\.]+[.]C)"\s',
        r'"([-~:\w\d /\.]+[.]cpp)"\s',
    ]
    temp = []
    for r in regex_list:
        p = re.compile(r)
        for m in p.finditer(compiler_output):
            filepath = m.group(1)
            if "/preproc/ctags_target" in filepath:
                pass
            else:
                temp.append(filepath)
    # Extract realpath
    # eg. 'C:/Users/GEBRUI~1/AppData/' => 'C:/Users/Gebruiker/AppData'
    cfile_list = [purefunctions.standardize_abspath(f) for f in set(temp)]
    del temp

    # & ofiles and dfiles
    # Define a list of regexes to identify the output .o files in the compiler output. The .d files
    # are sitting next to them, so they're easy to catch once you have the .o files. These .d and .o
    # files are obviously not needed for copying into the beetle project, but the .d files contain
    # all the hfile dependencies. We'll use them in the next step to extract the hfiles.
    regex_list = [
        r"([-~:\w\d/\.]+[.]S[.]o)\s",
        r"([-~:\w\d/\.]+[.]s[.]o)\s",
        r"([-~:\w\d/\.]+[.]asm[.]o)\s",
        r"([-~:\w\d/\.]+[.]c[.]o)\s",
        r"([-~:\w\d/\.]+[.]C[.]o)\s",
        r"([-~:\w\d/\.]+[.]cpp[.]o)\s",
        r'"([-~:\w\d /\.]+[.]S[.]o)"\s',
        r'"([-~:\w\d /\.]+[.]s[.]o)"\s',
        r'"([-~:\w\d /\.]+[.]asm[.]o)"\s',
        r'"([-~:\w\d /\.]+[.]c[.]o)"\s',
        r'"([-~:\w\d /\.]+[.]C[.]o)"\s',
        r'"([-~:\w\d /\.]+[.]cpp[.]o)"\s',
    ]
    temp = []
    for r in regex_list:
        p = re.compile(r)
        for m in p.finditer(compiler_output):
            filepath = m.group(1)
            if "/preproc/ctags_target" in filepath:
                pass
            else:
                temp.append(filepath)
    # Extract realpath
    # eg. 'C:/Users/GEBRUI~1/AppData/' => 'C:/Users/Gebruiker/AppData'
    ofile_list = [purefunctions.standardize_abspath(f) for f in set(temp)]
    del temp

    # & hfiles
    # Extract all the hfile dependencies from the dfiles.
    temp = []
    for f in ofile_list:
        dfilepath = f[0:-1] + "d"
        temp.extend(
            _compilation_extractor_.extract_hfiles_from_dfile(dfilepath)
        )
    hfile_list = list(set(temp))
    del temp

    # & support files
    # Look for all the support files, such as *.txt, *.properties, *.md that are in the same
    # folders as the found cfiles and hfiles. Add them too.
    temp = []
    already_parsed = []
    for f in cfile_list + hfile_list:
        folder = purefunctions.standardize_abspath(os.path.dirname(f))
        if folder in already_parsed:
            continue
        already_parsed.append(folder)
        if not os.path.isdir(folder):
            functions.importer_printfunc(
                f"ERROR: Cannot find directory: {q}{folder}{q}",
                color="error",
            )
            continue
        for fname in os.listdir(folder):
            if any(fname.lower().endswith(s) for s in supfile_suffixes):
                temp.append(f"{folder}/{fname}")
            continue
        continue
    supfile_list = list(set(temp))
    del temp

    # & Involved folders
    # List all the folders that are in any way involved - those that contain at least one of the
    # listed files.
    folder_list = []
    for f in cfile_list + hfile_list + supfile_list:
        folder = purefunctions.standardize_abspath(os.path.dirname(f))
        if folder in folder_list:
            continue
        folder_list.append(folder)

    return cfile_list, hfile_list, supfile_list, folder_list


def __extract_core_files(
    folder_list: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Core files are sitting in folders like:
    ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/cores/

    or:
    ~/.arduino15/packages/arduino/hardware/avr/1.8.3/cores/

    These core files should be copied entirely into the beetle project. This function returns all
    the relevant files in three lists:

    :return:    cfile_list, hfile_list, supfile_list
    """
    # List the core folder(s), eg:
    #   ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/cores/esp32
    # Normally this list should contain just one entry - but I want to play it safe.
    core_folder_list = [
        d for d in folder_list if ("/cores" in d) or ("/core" in d)
    ]

    # Now list all the relevant files in these core folder(s).
    cfile_list = []
    hfile_list = []
    supfile_list = []
    for core_folder in core_folder_list:
        for _r_, _d_, _f_ in os.walk(core_folder):
            if "examples" in _r_:
                _d_[:] = []
                _f_[:] = []
                continue
            for fname in _f_:
                # $ cfile
                if any(fname.endswith(s) for s in cfile_suffixes):
                    cfile = os.path.join(_r_, fname).replace("\\", "/")
                    if cfile not in cfile_list:
                        cfile_list.append(cfile)
                    continue
                # $ hfile
                if any(fname.endswith(s) for s in hfile_suffixes):
                    hfile = os.path.join(_r_, fname).replace("\\", "/")
                    if hfile not in hfile_list:
                        hfile_list.append(hfile)
                    continue
                # $ supfile
                if any(fname.lower().endswith(s) for s in supfile_suffixes):
                    supfile = os.path.join(_r_, fname).replace("\\", "/")
                    if supfile not in supfile_list:
                        supfile_list.append(supfile)
                    continue
                # $ not known
                continue
            continue
        continue
    return cfile_list, hfile_list, supfile_list


def __extract_core_library_files(
    folder_list: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """Core libraries are libraries that are sitting at the same hierarchical
    level as the '/cores/' folder in 'arduino15', eg for the esp32:

    ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/cores/esp32        <- cores folder
    ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/libraries/WiFi     <- WiFi library

    And for the Arduino Uno:
    ~/.arduino15/packages/arduino/hardware/avr/1.8.3/cores/arduino      <- cores folder
    ~/.arduino15/packages/arduino/hardware/avr/1.8.3/libraries/EEPROM   <- EEPROM library

    These core libraries should be copied entirely into the beetle project, except their 'examples'
    folder of course. This function returns all the relevant files in three lists:

    :return:    cfile_list, hfile_list, supfile_list
    """
    # List the core folder(s), eg:
    #   ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/cores/esp32
    # Normally this list should contain just one entry - but I want to play it safe.
    core_folder_list = [
        d for d in folder_list if ("/cores" in d) or ("/core" in d)
    ]

    # List the core library-collection folder(s), eg:
    #   ~/.arduino15/packages/esp32/hardware/esp32/1.0.6/libraries
    # Normally this list should contain just one entry - but I want to play it safe.
    temp = []
    for core_folder in core_folder_list:
        if "/cores" in core_folder:
            core_libfolder = core_folder.split("/cores")[0] + "/libraries"
        else:
            core_libfolder = core_folder.split("/core")[0] + "/libraries"
        core_libfolder = purefunctions.standardize_abspath(
            core_libfolder.replace("//", "/")
        )
        if os.path.isdir(core_libfolder):
            temp.append(core_libfolder)
        continue
    core_libcollection_list = list(set(temp))

    # Now list all the relevant files in these library-collection folder(s).
    cfile_list = []
    hfile_list = []
    supfile_list = []
    for core_libcollection in core_libcollection_list:
        for _r_, _d_, _f_ in os.walk(core_libcollection):
            if "examples" in _r_:
                _d_[:] = []
                _f_[:] = []
                continue
            for fname in _f_:
                # $ cfile
                if any(fname.endswith(s) for s in cfile_suffixes):
                    cfile = os.path.join(_r_, fname).replace("\\", "/")
                    if cfile not in cfile_list:
                        cfile_list.append(cfile)
                    continue
                # $ hfile
                if any(fname.endswith(s) for s in hfile_suffixes):
                    hfile = os.path.join(_r_, fname).replace("\\", "/")
                    if hfile not in hfile_list:
                        hfile_list.append(hfile)
                    continue
                # $ supfile
                if any(fname.lower().endswith(s) for s in supfile_suffixes):
                    supfile = os.path.join(_r_, fname).replace("\\", "/")
                    if supfile not in supfile_list:
                        supfile_list.append(supfile)
                    continue
                # $ not known
                continue
            continue
        continue
    return cfile_list, hfile_list, supfile_list


def __process_sketch_file(sketchfile_abspath: str) -> bool:
    """Arduino sketch files are transformed by the Arduino CLI tool into
    '.ino.cpp' files. However, they have a few quirks that should be cleaned
    before presenting the file to the user.

    Return True if processing succeeded.
    """
    functions.importer_printfunc(
        f"\n__process_sketch_file({q}{sketchfile_abspath}{q})\n"
    )
    if not os.path.isfile(sketchfile_abspath):
        functions.importer_printfunc(
            f"\nERROR: The sketch file could not be found:\n"
            f"{q}{sketchfile_abspath}{q}",
            color="error",
        )
        return False

    # & Read content
    content = ""
    try:
        with open(
            sketchfile_abspath,
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            content = f.read()
    except:
        traceback.print_exc()
        functions.importer_printfunc(
            f"{traceback.format_exc()}",
            color="error",
        )
        return False

    # & Modify content
    p = re.compile(r"#line\s\d+.*")
    content = p.sub("", content)
    intro_msg = str(
        "/*\n"
        "  IMPORTANT NOTE FOR ARDUINO USERS\n"
        "  ================================\n"
        "\n"
        "  The language used in Arduino sketches is a subset of C/C++.\n"
        "  However, in Embeetle you should use plain C/C++, which means\n"
        "  that:\n"
        "\n"
        "    - Functions should have a function prototype, usually\n"
        "      declared at the top of the file.\n"
        "\n"
        "    - Include statements are important to use functions,\n"
        "      variables and classes from other files.\n"
        "\n"
        "*/\n\n"
    )
    content = intro_msg + content

    # & Write content
    try:
        with open(
            sketchfile_abspath,
            "w",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            f.write(content)
    except:
        traceback.print_exc()
        functions.importer_printfunc(
            f"{traceback.format_exc()}",
            color="error",
        )
        return False
    functions.importer_printfunc("\nComplete sketch file modification.\n")
    return True


def __process_new_dot_h_file(
    orig_filepath: str,
    target_filepath: str,
) -> bool:
    """On one occasion, I had the following files in.

    'C:/Users/krist/AppData/Local/Arduino15/packages/arduino/hardware/avr/1.8.4/cores/arduino':
        - new.cpp
        - new.h
        - new

    The 'new.h' file was just a shell referring to the 'new' file for content. For this particular
    case, I believe the content of 'new' should be copied into 'new.h'.
    """
    functions.importer_printfunc(
        f"\n__process_new_dot_h_file({q}{target_filepath}{q})\n"
    )

    # & Check parameters
    if (not os.path.isfile(orig_filepath)) or (
        not orig_filepath.endswith("new.h")
    ):
        functions.importer_printfunc(
            f"\nERROR: The original {q}new.h{q} file could not be found:\n"
            f"{q}{orig_filepath}{q}",
            color="error",
        )
        return False
    if (not os.path.isfile(target_filepath)) or (
        not target_filepath.endswith("new.h")
    ):
        functions.importer_printfunc(
            f"\nERROR: The target {q}new.h{q} file could not be found:\n"
            f"{q}{target_filepath}{q}",
            color="error",
        )
        return False

    # & Read content
    content = ""
    try:
        with open(
            target_filepath,
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            content = f.read()
    except:
        traceback.print_exc()
        functions.importer_printfunc(
            f"{traceback.format_exc()}",
            color="error",
        )
        return False

    # & Check if file 'new' is included and if it exists
    p = re.compile(r'#include\s+"new"')
    m = p.search(content)
    if m is None:
        # Nothing to process. No problems either, so just return True.
        return True
    # Remove the '.h' extension to point to the 'new' file.
    new_filepath = orig_filepath[:-2]
    if not os.path.isfile(new_filepath):
        functions.importer_printfunc(
            f"\nERROR: The file:\n"
            f"{q}{target_filepath}{q}\n"
            f"contains the following include statement:\n"
            f'    #include "new"\n'
            f"However, this file could not be found!\n",
            color="error",
        )
        return False
    # Read the content from the 'new' file and store it.
    new_content = ""
    try:
        with open(
            new_filepath, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            new_content = f.read()
    except:
        functions.importer_printfunc(
            f"{traceback.format_exc()}",
            color="error",
        )
        return False

    # & Make the substitution
    content = p.sub(new_content, content)

    # & Write content
    try:
        with open(
            target_filepath,
            "w",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            f.write(content)
    except:
        functions.importer_printfunc(
            f"{traceback.format_exc()}",
            color="error",
        )
        return False
    functions.importer_printfunc(f"\nComplete {q}new.h{q} modification.\n")
    return True


def get_arduino15_dir() -> Optional[str]:
    """Get the Arduino15 directory, like:

    - 'C:/Users/Kristof/AppData/Local/Arduino15'
    - '~/.arduino15'
    """
    homedir = data.user_directory

    def get_windows_arduino15(*args) -> Optional[str]:
        appdir_local = os.path.join(homedir, "AppData/Local").replace("\\", "/")
        appdir_roaming = os.path.join(homedir, "AppData/Roaming").replace(
            "\\", "/"
        )
        # $ Try 'Arduino15'
        arduino15_dir = os.path.join(appdir_local, "Arduino15").replace(
            "\\", "/"
        )
        if os.path.isdir(arduino15_dir):
            return arduino15_dir
        arduino15_dir = os.path.join(appdir_roaming, "Arduino15").replace(
            "\\", "/"
        )
        if os.path.isdir(arduino15_dir):
            return arduino15_dir
        # $ Try 'ArduinoXX'
        p = re.compile(r"[aA]rduino\d*")
        if os.path.isdir(appdir_local):
            for dname in os.listdir(appdir_local):
                if not "arduino" in dname.lower():
                    continue
                dpath = os.path.join(appdir_local, dname).replace("\\", "/")
                if not os.path.isdir(dpath):
                    continue
                if p.search(dname) is not None:
                    return dpath
        if os.path.isdir(appdir_roaming):
            for dname in os.listdir(appdir_roaming):
                if not "arduino" in dname.lower():
                    continue
                dpath = os.path.join(appdir_roaming, dname).replace("\\", "/")
                if not os.path.isdir(dpath):
                    continue
                if p.search(dname) is not None:
                    return dpath
        # $ Try '..arduino..'
        if os.path.isdir(appdir_local):
            for dname in os.listdir(appdir_local):
                if not "arduino" in dname.lower():
                    continue
                dpath = os.path.join(appdir_local, dname).replace("\\", "/")
                if not os.path.isdir(dpath):
                    continue
                return dpath
        if os.path.isdir(appdir_roaming):
            for dname in os.listdir(appdir_roaming):
                if not "arduino" in dname.lower():
                    continue
                dpath = os.path.join(appdir_roaming, dname).replace("\\", "/")
                if not os.path.isdir(dpath):
                    continue
                return dpath
        return None

    def get_linux_arduino15(*args) -> Optional[str]:
        # $ Try '~/.arduino15'
        arduino15_dir = os.path.join(homedir, ".arduino15").replace("\\", "/")
        if os.path.isdir(arduino15_dir):
            return arduino15_dir
        # $ Try with capital
        arduino15_dir = os.path.join(homedir, ".Arduino15").replace("\\", "/")
        if os.path.isdir(arduino15_dir):
            return arduino15_dir
        # $ Try '~/.arduinoXX'
        p = re.compile(r"[.][aA]rduino\d*")
        for dname in os.listdir(homedir):
            if not "arduino" in dname.lower():
                continue
            dpath = os.path.join(homedir, dname).replace("\\", "/")
            if not os.path.isdir(dpath):
                continue
            if p.search(dname) is not None:
                return dpath
        return None

    if os_checker.is_os("windows"):
        return get_windows_arduino15()
    return get_linux_arduino15()
