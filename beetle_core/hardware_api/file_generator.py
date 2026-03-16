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
import os, traceback
import data, purefunctions, functions
import regex as re
import fnmatch as _fn_
import hardware_api.hardware_api as _hardware_api_
import hardware_api.board_unicum as _board_unicum_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.treepath_unicum as _treepath_unicum_
import hardware_api.toolcat_unicum as _toolcat_unicum_

if TYPE_CHECKING:
    pass
transition_period: bool = True
q = "'"
dq = '"'


# ^                                            MAKEFILE                                            ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_makefile(
    boardname: str,
    chipname: str,
    version: Optional[Union[str, int]],
) -> str:
    """"""
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)

    # $ Define version
    if (version == "latest") or (version is None):
        version = functions.get_latest_makefile_interface_version()

    # $ Define location of 'makefile.py' generator
    relpath: Optional[str] = chip_dict["makefile_generator"]
    if relpath is None:
        return "\n#NO MAKEFILE FOUND\n"
    abspath: str = purefunctions.join_resources_dir_to_path(relpath)

    # $ Invoke the 'makefile.py' generator
    try:
        my_module = purefunctions.load_module(abspath, {})
        return my_module["get_makefile"](
            version=version,
        )
    except:
        traceback.print_exc()
    return "\n#NO MAKEFILE FOUND\n"


# ^                                          DASHBOARD_MK                                          ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_default_project_layout(
    proj_rootpath: str,
    boardname: str,
    chipname: str,
    probename: str,
    ignore_list: List[str],
    relative: bool = False,
    rootid: Optional[str] = None,
) -> Dict[str, str]:
    """"""
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)

    # & First construct the project layout for *all* the treepath unicums
    filepaths = {}
    for treepath_unicum in _hardware_api_.HardwareDB().list_treepath_unicums(
        True
    ):
        assert isinstance(treepath_unicum, _treepath_unicum_.TREEPATH_UNIC)
        if treepath_unicum.get_name() in ignore_list:
            # These treepath unicums are never relevant to generate 'dashboard.mk'
            continue
        relpath = treepath_unicum.get_default_relpath(
            board_unicum=_board_unicum_.BOARD(boardname),
            chip_unicum=_chip_unicum_.CHIP(chipname),
        )
        if relative:
            if rootid:
                filepaths[treepath_unicum.get_name()] = f"{rootid}/{relpath}"
            else:
                filepaths[treepath_unicum.get_name()] = relpath
        else:
            filepaths[treepath_unicum.get_name()] = f"{proj_rootpath}/{relpath}"
        continue

    # & Take out the irrelevant ones
    # There are two places where the relevances of treepath unicums are applied:
    #   1) Here
    #   2) In 'treepath_seg.py'
    # The relevances are determined in 'toolcats.json5', more in particular in the FLASTHOOL
    # category. One exception is then applied based on the 'can_flash_bootloader' field from the
    # probe dictionary.
    flashtool_category_dict = _hardware_api_.HardwareDB().get_toolcat_dict(
        "FLASHTOOL"
    )
    relevant_list = []
    default_flashtool_uid = str(chip_dict.get("default_flashtool_uid")).lower()
    for p in flashtool_category_dict["uid_pattern"].keys():
        if _fn_.fnmatch(name=default_flashtool_uid, pat=p):
            relevant_list = flashtool_category_dict["uid_pattern"][p][
                "relevant_treepaths"
            ]
            break
        continue
    for k in filepaths.keys():
        if k in relevant_list:
            continue
        filepaths[k] = None
        continue
    if not probe_dict["can_flash_bootloader"]:
        filepaths["BOOTLOADER_FILE"] = None
    return filepaths


def get_new_dashboard_mk(
    proj_rootpath: str,
    boardname: str,
    chipname: str,
    probename: str,
    toolprefix: Optional[str] = None,
    flashtool_exename: Optional[str] = None,
    filepaths: Optional[Dict[str, str]] = None,
    repoints: Optional[Dict] = None,
    version: Optional[Union[str, int]] = None,
) -> str:
    """Get 'dashboard.mk' file (as a large string). First locate the
    'dashboard_mk.py' generator file in the '<resources>/hardware' database.
    Then invoke its main function with the proper para- meters.

    :param boardname: Identify board.
    :param chipname: Identify chip.
    :param probename: Identify probe.
    :param toolprefix: [Optional] Provide a compiler prefix like 'arm-none-
        eabi-' which is then in- serted in 'dashboard.mk' as a fallback value
        for when the absolute toolprefix isn't provided on the commandline. If
        empty, the default compiler prefix gets extracted from the chip json
        file.
    :param flashtool_exename: [Optional] Provide a flashtool executable name
        like 'openocd' which is then inserted in 'dashboard.mk' as a fallback
        value for when the absolute flashtool path isn't provided on the
        commandline. If empty, the default flashtool executable name gets
        extracted from the default flashtool unique ID in the json files.
    :param filepaths: [Optional] A dictionary of the names and absolute(!)
        filepaths represented in the PROJECT LAYOUT section in the Dashboard.
        These absolute paths get modified into relative ones (relative to the
        build folder) later on. If empty, the default values get extracted based
        on the given board, chip and probe.
    :param repoints: [Optional] Repoints for previous parameter.
    :param version: [Optional] Makefile interface version.
    """
    board_dict = _hardware_api_.HardwareDB().get_board_dict(boardname)
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)

    # & Parameter 'toolprefix'
    if (toolprefix is None) or (toolprefix.lower() == "none"):
        toolprefix = chip_dict.get("default_compiler_prefix")
    if toolprefix is None:
        toolprefix = "none"
    assert "/" not in toolprefix

    # & Parameter 'flasthool_exename'
    if (flashtool_exename is None) or (flashtool_exename.lower() == "none"):
        flashtool_uid = chip_dict.get("default_flashtool_uid")
        flashtool_exename = _toolcat_unicum_.TOOLCAT_UNIC(
            "FLASHTOOL"
        ).get_flashtool_exename(
            unique_id=flashtool_uid,
        )
    if flashtool_exename is None:
        flashtool_exename = "none"
    assert "/" not in flashtool_exename

    # & Parameter 'filepaths'
    if filepaths is None:
        filepaths = get_default_project_layout(
            proj_rootpath=proj_rootpath,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
            ignore_list=[
                "BUTTONS_BTL",
                "MAKEFILE",
                "DASHBOARD_MK",
                "FILETREE_MK",
            ],
            relative=False,
            rootid=None,
        )
    # Always add the 'SOURCE_DIR' in front. It's no longer a treepath unicum, but it's still needed
    # to form 'dashboard.mk'.
    _filepaths = {"SOURCE_DIR": proj_rootpath}
    _filepaths.update(filepaths)

    # & Parameter 'repoints'
    if repoints is not None:
        for k, v in filepaths.items():
            if k not in repoints.keys():
                continue
            filepaths[k] = repoints[k][1]
            continue

    # & Parameter 'version'
    if (version == "latest") or (version is None):
        version = functions.get_latest_makefile_interface_version()

    # & Apply
    # $ Define location of 'dashboard_mk.py' generator
    relpath: Optional[str] = None
    relpath = chip_dict["dashboard_mk_generator"]
    if (relpath is None) or (relpath.lower() == "none"):
        return "\n# NO DASHBOARD.MK FOUND\n"
    abspath: str = purefunctions.join_resources_dir_to_path(relpath)
    # $ Invoke the generator
    try:
        my_module = purefunctions.load_module(abspath, {})
        return my_module["get_dashboard_mk"](
            boardname=boardname,
            board_dict=board_dict,
            chipname=chipname,
            chip_dict=chip_dict,
            probename=probename,
            probe_dict=probe_dict,
            filepaths=_filepaths,
            resources_path=data.resources_directory,
            toolprefix=toolprefix,
            flashtool_exename=flashtool_exename,
            version=version,
        )
    except:
        traceback.print_exc()
    return "\n# NO DASHBOARD.MK FOUND\n"


# ^                                          FILETREE_MK                                           ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_filetree_mk_template(
    version: Optional[Union[str, int]] = None,
) -> str:
    """Get 'filetree.mk' file (as a large string)."""
    abspath = purefunctions.join_resources_dir_to_path(
        "hardware/filetree_mk.py"
    )
    try:
        my_module = purefunctions.load_module(abspath, {})
        content = my_module["get_filetree_mk_template"](
            version=version,
        )
    except:
        traceback.print_exc()
        return "\n# NO FILETREE.MK FOUND\n"
    return content


# ^                                         LINKERSCRIPT                                           ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_linkerscripts(
    boardname: Optional[str],
    chipname: str,
) -> Dict[str, str]:
    """
    Get the linkerscripts for the given board/chip (usually the chip is enough). The linkerscripts
    are returned as a dictionary:

    linkerscripts = {
        'linkerscript_name_01' : 'blah blah',
        'linkerscript_name_02' : 'blah blah',
        ...
    }
    """
    assert chipname is not None
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)

    def get_linkerscript_content(relpath: str) -> str:
        if relpath is None:
            return "# Cannot generate linkerscript"
        abspath = purefunctions.join_resources_dir_to_path(relpath)
        if not os.path.isfile(abspath):
            purefunctions.printc(
                f"\nERROR: The linkerscript path mentioned in your {q}board.json5{q} and/or "
                f"{q}chip.json5{q} file cannot be found: {q}{abspath}{q}\n",
                color="error",
            )
            return str(
                f"# Cannot generate linkerscript!\n"
                f"# Linkerscript mentioned in your {q}board.json5{q} and/or {q}chip.json5{q} file\n"
                f"# cannot be found: {q}{abspath}{q}\n"
            )
        # $ Linkerscript generator
        if abspath.endswith(".py"):
            try:
                my_module = purefunctions.load_module(abspath, {})
                return my_module["get_linkerscript"](
                    chipname=chipname,
                    chip_dict=chip_dict,
                )
            except:
                traceback.print_exc()
            return "# Cannot generate linkerscript"
        # $ Linkerscript as-is
        assert not abspath.endswith(".py")
        content = ""
        try:
            with open(
                abspath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                content = f.read()
        except:
            traceback.print_exc()
            content = "# Cannot generate linkerscript"
        return content

    linkerscript_generators = chip_dict["linkerscript"].get(
        "linkerscript_generators"
    )
    return {
        _relpath.split("/")[-1].replace(".py", ".ld"): get_linkerscript_content(
            _relpath
        )
        for _relpath in linkerscript_generators
    }


# ^                                        OPENOCD_CHIPFILE                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_openocd_chipcfg_file(
    boardname: str,
    chipname: str,
) -> str:
    """Get the OpenOCD chip config file (as a large string) corresponding to the
    given microcontroller."""
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)

    # $ Define location of 'openocd_chip_cfg.py' generator
    relpath = chip_dict["openocd"]["openocd_chip_cfg_generator"]
    if relpath is None:
        return "# Cannot generate OpenOCD config file"
    abspath: str = purefunctions.join_resources_dir_to_path(relpath)

    # $ Invoke the 'openocd_chip_cfg.py' generator
    try:
        my_module = purefunctions.load_module(abspath, {})
        return my_module["get_openocd_chip_cfg"](
            chipname=chipname,
            target_file=chip_dict["openocd"]["target_file"],
        )
    except:
        traceback.print_exc()
    return "# Cannot generate OpenOCD config file"


# ^                                       OPENOCD_PROBEFILE                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_openocd_probecfg_file(
    boardname: Optional[str] = None,
    chipname: Optional[str] = None,
    probename: Optional[str] = None,
    transport_protocol_name: Optional[str] = None,
) -> str:
    """Get the OpenOCD probe config file (as a large string) corresponding to
    the given probe."""
    if probename is None:
        return "# Probe unknown"
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)

    if (transport_protocol_name is None) or (
        transport_protocol_name.lower() == "none"
    ):
        transport_protocol_name = probe_dict["transport_protocols"][0]

    # $ Define location of 'openocd_probe_cfg.py' generator
    relpath: Optional[str] = probe_dict["openocd"][
        "openocd_probe_cfg_generator"
    ]
    if relpath is None:
        return "# Cannot generate OpenOCD config file"
    abspath: str = purefunctions.join_resources_dir_to_path(relpath)

    # $ Invoke the 'openocd_probe_cfg.py' generator
    try:
        my_module = purefunctions.load_module(abspath, {})
        return my_module["get_openocd_probe_cfg"](
            boardname=boardname,
            chipname=chipname,
            probename=probename,
            target_file=probe_dict["openocd"]["target_file"],
            transport_protocol=transport_protocol_name,
        )
    except:
        traceback.print_exc()
    return "# Cannot generate OpenOCD config file"


# ^                                         GDB_FLASHFILE                                          ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_gdbinit(
    boardname: Optional[str],
    chipname: str,
    probename: Optional[str] = None,
) -> str:
    """"""
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(chipname, boardname)

    # $ Select .gdbinit file or generator-file
    relpath_list = chip_dict["gdb_init"]
    if (relpath_list is None) or (len(relpath_list) == 0):
        return "# Cannot generate .gdbinit file"
    relpath = relpath_list[0]
    if "blackmagic" in probename.lower():
        for p in relpath_list:
            if "blackmagic" in p:
                relpath = p
                break
            continue
    abspath = purefunctions.join_resources_dir_to_path(relpath)

    # $ .gdbinit generator
    if abspath.endswith(".py"):
        try:
            my_module = purefunctions.load_module(abspath, {})
            return my_module["get_gdbinit"](
                chipname=chipname,
                chip_dict=chip_dict,
            )
        except:
            traceback.print_exc()
        return "# Cannot generate .gdbinit file"

    # $ .gdbinit as-is
    assert not abspath.endswith(".py")
    content = ""
    try:
        with open(
            abspath, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            content = f.read()
    except:
        traceback.print_exc()
        content = "# Cannot generate .gdbinit file"
    return content


# ^                                          BUTTONS_BTL                                           ^#
# % ============================================================================================== %#
# %                                                                                                %#


def get_new_buttonsbtl_file(
    probename: Optional[str] = None,
) -> str:
    """"""
    probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)
    can_flash_bootloader = probe_dict["can_flash_bootloader"]

    if not can_flash_bootloader:
        content = f"""# BUTTON DEFINITIONS
# ===================
# Modify this file to change/add buttons in the top toolbar.
# Tip: refer to icons in the 'beetle_core/resources/icons/' folder,
# in your Embeetle installation directory.
{{
    "clean":
    {{
        "icon": "icons/gen/clean.png",
        "hover-text": "Run 'clean' target in makefile",
        "help-text": "Run 'clean' target in makefile",
        "shortcut": "F2"
    }},

    "build":
    {{
        "icon": "icons/gen/build.png",
        "hover-text": "Run 'build' target in makefile",
        "help-text": "Run 'build' target in makefile",
        "shortcut": "F3"
    }},

    "flash":
    {{
        "icon": "icons/gen/flash.png",
        "hover-text": "Run 'flash' target in makefile",
        "help-text": "Run 'flash' target in makefile",
        "shortcut": "F4"
    }}
}}
"""
        return content

    assert can_flash_bootloader
    content = f"""# BUTTON DEFINITIONS
# ===================
# Modify this file to change/add buttons in the top toolbar.
# Tip: refer to icons in the 'beetle_core/resources/icons/' folder,
# in your Embeetle installation directory.
{{
    "clean":
    {{
        "icon": "icons/gen/clean.png",
        "hover-text": "Run 'clean' target in makefile",
        "help-text": "Run 'clean' target in makefile",
        "shortcut": "F2"
    }},

    "build":
    {{
        "icon": "icons/gen/build.png",
        "hover-text": "Run 'build' target in makefile",
        "help-text": "Run 'build' target in makefile",
        "shortcut": "F3"
    }},

    "flash":
    {{
        "icon": "icons/gen/flash.png",
        "hover-text": "Run 'flash' target in makefile",
        "help-text": "Run 'flash' target in makefile",
        "shortcut": "F4"
    }},

    "flash_bootloader":
    {{
        "icon": "icons/gen/flash_bootloader.png",
        "hover-text": "Run 'flash_bootloader' target in makefile",
        "help-text": "Run 'flash_bootloader' target in makefile",
        "shortcut": "F5"
    }}
}}
"""
    return content


# ^                                     CUBEMX HELP FUNCTIONS                                      ^#
# % ============================================================================================== %#
# % Help functions.                                                                                %#
# %                                                                                                %#


def get_new_adapted_cubemx_mainfile(
    proj_rootpath: str,
    boardname: str,
    chipname: str,
    freertos: bool,
    printfunc: Callable,
    catch_err: bool,
) -> Optional[str]:
    """This function reads the 'main.c' file and modifies it to let an LED
    blink.

    Return None if something fails.
    """
    # $ Define location of 'cubemx_adaptor.py' generator
    relpath: str = "hardware/chip/stmicro/cubemx_adaptor.py"
    abspath: str = purefunctions.join_resources_dir_to_path(relpath)

    # $ Look for corresponding nucleo/disco board if needed
    cor_boardname: Optional[str] = None
    cor_boarddict: Optional[Dict[str, Any]] = None
    if boardname == "custom":
        brds = _hardware_api_.HardwareDB().list_boards(
            chip_list=[
                chipname,
            ],
            return_unicums=False,
        )
        valid_brd = None
        for brd in brds:
            if (brd.lower() == "custom") or (brd.lower() == "none"):
                continue
            valid_brd = brd
            break
        if valid_brd is not None:
            cor_boardname = valid_brd
            cor_boarddict = _hardware_api_.HardwareDB().get_board_dict(
                valid_brd
            )

    # $ Invoke the 'cubemx_adaptor.py' generator
    try:
        my_module = purefunctions.load_module(abspath, {})
        return my_module["get_new_adapted_cubemx_mainfile"](
            proj_rootpath=proj_rootpath,
            chipname=chipname,
            chip_dict=_hardware_api_.HardwareDB().get_chip_dict(
                chipname, boardname
            ),
            boardname=boardname,
            board_dict=_hardware_api_.HardwareDB().get_board_dict(boardname),
            cor_boardname=cor_boardname,
            cor_boarddict=cor_boarddict,
            freertos=freertos,
            printfunc=printfunc,
        )
    except:
        traceback.print_exc()
    return None


# ^                                       DASHBOARD_CONFIG                                         ^#
# % ============================================================================================== %#
# %                                                                                                %#


def write_dashboard_config(
    dashboard_config_abspath: str, dashboard_config_dict: Dict[str, Any]
):
    """"""
    assert dashboard_config_abspath.endswith(".btl")
    beetle_abspath = dashboard_config_abspath
    json_abspath = dashboard_config_abspath.replace(".btl", ".json5")

    # & Make sure the file 'dashboard_config.btl' exists
    # During the transition period, ensure the existence of the '.btl' and '.json5' variants. If the
    # files don't exist yet, just create empty ones. This ensures there is write access. After the
    # transition period, only the existence of the '.btl' file must be guaranteed.
    def ensure_existence(abspath: str) -> None:
        if not os.path.isdir(os.path.dirname(abspath)):
            os.makedirs(os.path.dirname(abspath), 0o777, False)
        if not os.path.isfile(abspath):
            with open(abspath, "w", encoding="utf-8", newline="\n") as _f:
                _f.write("")
        assert os.path.isfile(abspath)
        return

    ensure_existence(beetle_abspath)
    if transition_period:
        ensure_existence(json_abspath)
    elif os.path.isfile(json_abspath):
        os.remove(json_abspath)

    # & Extract, format and write the content
    # During the transition period, Embeetle will save the project in python-format to the btl-file
    # and in json-format to the json-file. Add an extra field to the json-file, to store the hash
    # code of the btl-file.
    # After the transition period, Embeetle will save the project in json-format to the btl-file.
    # $ python_content
    if transition_period:
        python_content: str = __get_dashboard_config_intro("#")
        python_content += "\n\n"
        for k, v in dashboard_config_dict.items():
            python_content += f"{k} = {q}{v}{q}\n"
        python_content += "\n\n"
        python_content += __get_mit_license("#")
        with open(
            beetle_abspath,
            "w+",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            f.write(python_content)
        dashboard_config_dict["hash_value"] = purefunctions.md5_file(
            beetle_abspath
        )

    # $ json_content
    json_content: str = __get_dashboard_config_intro("//")
    json_content += "\n\n"
    json_content += purefunctions.json_encode(dashboard_config_dict)
    json_content += "\n\n"
    json_content += __get_mit_license("//")
    if transition_period:
        with open(
            json_abspath, "w+", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            f.write(json_content)
    else:
        with open(
            beetle_abspath,
            "w+",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            f.write(json_content)
    return


def read_dashboard_config(dashboard_config_abspath: str) -> Dict[str, Any]:
    """"""
    assert dashboard_config_abspath.endswith(".btl")
    beetle_abspath = dashboard_config_abspath
    json_abspath = dashboard_config_abspath.replace(".btl", ".json5")

    def create_default() -> Dict[str, Any]:
        _json_dict = __get_default_dashboard_config_dict()
        write_dashboard_config(
            dashboard_config_abspath=dashboard_config_abspath,
            dashboard_config_dict=_json_dict,
        )
        return _json_dict

    # $ CASE 1: no '.btl' nor '.json5' file
    # Create a default '.btl' and '.json5' file - depending on being in the transition period. That
    # decision is taken in write_dashboard_config().
    if (not os.path.isfile(beetle_abspath)) and (
        not os.path.isfile(json_abspath)
    ):
        return create_default()

    # $ CASE 2: '.btl' file in json-format
    # This will be the new normal after the transition period. Delete a '.json5' file if present.
    if os.path.isfile(beetle_abspath) and purefunctions.is_json_file(
        beetle_abspath
    ):
        if os.path.isfile(json_abspath):
            os.remove(json_abspath)
        json_dict = purefunctions.load_json_file_with_comments(beetle_abspath)
        if json_dict is None:
            return create_default()
        return json_dict

    # $ CASE 3: '.btl' file in python-format and '.json5' file in json-format
    #  This is the usual case for the transition period.
    if os.path.isfile(beetle_abspath) and os.path.isfile(json_abspath):
        # During transition period: Check the hash signature stored in the '.json5' file. Does the
        # hash correspond to the content of the '.btl' file? Then just ignore the '.btl' file and
        # continue with the '.json5' file. Otherwise, continue with the '.btl' file.
        if transition_period:
            json_dict = purefunctions.load_json_file_with_comments(json_abspath)
            if json_dict is None:
                # Try again, as if there is no '.json5' file, just a '.btl' file only.
                os.remove(json_abspath)
                return read_dashboard_config(dashboard_config_abspath)
            stored_hash_value = json_dict.get("hash_value")
            computed_hash_value = purefunctions.md5_file(beetle_abspath)
            if stored_hash_value == computed_hash_value:
                return json_dict
            python_dict = __load_python_format(beetle_abspath)
            if python_dict is None:
                return create_default()
            write_dashboard_config(
                dashboard_config_abspath=dashboard_config_abspath,
                dashboard_config_dict=python_dict,
            )
            return python_dict
        # After transition period: Throw away the '.btl' file. Rename the '.json5' into '.btl' and
        # continue from there.
        assert not transition_period
        os.remove(beetle_abspath)
        os.rename(json_abspath, beetle_abspath)
        json_dict = purefunctions.load_json_file_with_comments(beetle_abspath)
        if json_dict is None:
            return create_default()
        return json_dict

    # $ CASE 4: only '.btl' file in python-format
    # This is the case for an 'old' project
    if os.path.isfile(beetle_abspath):
        python_dict = __load_python_format(beetle_abspath)
        if python_dict is None:
            return create_default()
        write_dashboard_config(
            dashboard_config_abspath=dashboard_config_abspath,
            dashboard_config_dict=python_dict,
        )
        return python_dict

    # $ OTHER
    # This shouldn't happen
    json_dict = __get_default_dashboard_config_dict()
    write_dashboard_config(
        dashboard_config_abspath=dashboard_config_abspath,
        dashboard_config_dict=json_dict,
    )
    return json_dict


def __load_python_format(filepath: str) -> Dict[str, Any]:
    """"""
    content: Optional[str] = None
    with open(
        filepath, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        content = f.read()
    assert content is not None

    def get_value(varname: str) -> Optional[str]:
        p = re.compile(rf"{varname}\s+=\s+[\'\"]([\w\d\.\/<>-]+)[\'\"]")
        m = p.search(content)
        if m is not None:
            value = m.group(1).replace(q, "").replace(dq, "").strip()
            if value.lower() in ("none", "null"):
                return None
            return value
        return None

    _raw_proj_data = {
        "project_type": get_value("project_type"),
        "project_version": get_value("project_version"),
        "chip_name": get_value("chip_name"),
        "board_name": get_value("board_name"),
        "probe_name": get_value("probe_name"),
        "transport_protocol": get_value("transport_protocol"),
        "COM_port": get_value("COM_port"),
        "BUILD_DIR": get_value("BUILD_DIR"),
        "BIN_FILE": get_value("BIN_FILE"),
        "ELF_FILE": get_value("ELF_FILE"),
        "BOOTLOADER_FILE": get_value("BOOTLOADER_FILE"),
        "BOOTSWITCH_FILE": get_value("BOOTSWITCH_FILE"),
        "PARTITIONS_CSV_FILE": get_value("PARTITIONS_CSV_FILE"),
        "LINKERSCRIPT": get_value("LINKERSCRIPT"),
        "MAKEFILE": get_value("MAKEFILE"),
        "GDB_FLASHFILE": get_value("GDB_FLASHFILE"),
        "OPENOCD_CHIPFILE": get_value("OPENOCD_CHIPFILE"),
        "OPENOCD_PROBEFILE": get_value("OPENOCD_PROBEFILE"),
        "PACKPATH": get_value("PACKPATH"),
        "COMPILER_TOOLCHAIN": get_value("COMPILER_TOOLCHAIN"),
        "BUILD_AUTOMATION": get_value("BUILD_AUTOMATION"),
        "FLASHTOOL": get_value("FLASHTOOL"),
    }
    if _raw_proj_data["project_type"] is None:
        _raw_proj_data["project_type"] = "makefile"
    if _raw_proj_data["project_version"] is None:
        _raw_proj_data["project_version"] = "latest"
    return _raw_proj_data


def __get_default_dashboard_config_dict() -> Dict[str, Any]:
    """"""
    return {
        "project_type": "makefile",
        "project_version": "latest",
        "chip_name": None,
        "board_name": None,
        "probe_name": None,
        "transport_protocol": None,
        "COM_port": None,
        "BUILD_DIR": None,
        "BIN_FILE": None,
        "ELF_FILE": None,
        "BOOTLOADER_FILE": None,
        "BOOTSWITCH_FILE": None,
        "PARTITIONS_CSV_FILE": None,
        "LINKERSCRIPT": None,
        "MAKEFILE": None,
        "GDB_FLASHFILE": None,
        "OPENOCD_CHIPFILE": None,
        "OPENOCD_PROBEFILE": None,
        "PACKPATH": None,
        "COMPILER_TOOLCHAIN": None,
        "BUILD_AUTOMATION": None,
        "FLASHTOOL": None,
    }


def __get_dashboard_config_intro(comment: str = "#") -> str:
    """"""
    intro = str(
        "# ============================================================================= #\n"
        "#                                DASHBOARD CONFIG                               #\n"
        "# ============================================================================= #\n"
        "#  COPYRIGHT (c) 2023 Embeetle                                                  #\n"
        "#  This software component is licensed by Embeetle under the MIT license. Con-  #\n"
        "#  sult the license text at the bottom of this file.                            #\n"
        "#                                                                               #\n"
        "#  SUMMARY                                                                      #\n"
        "#  This file saves all your settings from the Dashboard.                        #\n"
        "#                                                                               #\n"
    )
    if comment == "//":
        intro = intro.replace("# ", "//").replace(" #", "//")
    return intro


def __get_mit_license(comment: str = "#") -> str:
    """"""
    mit_license = str(
        "# MIT LICENSE\n"
        "# ===========\n"
        "# COPYRIGHT (c) 2023 Embeetle\n"
        "#\n"
        "# Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        '# of this software and associated documentation files (the "Software"), to deal\n'
        "# in the Software without restriction, including without limitation the rights\n"
        "# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "# copies of the Software, and to permit persons to whom the Software is furn-\n"
        "# ished to do so, subject to the following conditions:\n"
        "#\n"
        "# The above copyright notice and this permission notice shall be included in all\n"
        "# copies or substantial portions of the Software.\n"
        "#\n"
        '# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "# SOFTWARE.\n"
    ).replace("#", comment)
    return mit_license
