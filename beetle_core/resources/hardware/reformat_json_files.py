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

from typing import *
import os, json, textwrap, deepdiff

q = "'"
dq = '"'
indent = "    "
textwidth = 100
hardware_path = (
    "C:/Users/krist/EMBEETLE IDE/embeetle/beetle_core/resources/hardware"
)
sample_path = "C:/sample_proj_resources"


def __get_title(
    title_txt: str,
    explanation: str,
    underline: str = "-",
    level: int = 0,
) -> str:
    """"""
    title = f"// {title_txt}"
    underline = f"// " + (len(title) - 3) * underline
    explanation = "// " + "\n// ".join(
        textwrap.wrap(
            text=explanation,
            width=textwidth - len("// ") - (len(indent) * level),
        )
    )
    txt = str(title + "\n" + underline + "\n" + explanation + "\n")
    return textwrap.indent(txt, indent * level)


def __get_comment_listing(
    comment_dict: Dict[str, str],
    level: int = 0,
) -> str:
    """"""
    content_lines = []
    for k, v in comment_dict.items():
        content_lines.append(f"{indent}- {k}")
        content_lines.extend(
            [
                f"{indent}{line}"
                for line in textwrap.wrap(
                    text=v,
                    width=textwidth - len("// ") - (len(indent) * (level + 1)),
                )
            ]
        )
        content_lines.append("")
        continue
    if content_lines[-1] == "":
        del content_lines[-1]
    for i in range(len(content_lines)):
        content_lines[i] = f"// {content_lines[i]}"

    txt = "\n".join(content_lines)
    return textwrap.indent(txt, indent * level) + "\n"


def __get_comment(
    comment: str,
    newline: bool = False,
    level: int = 0,
) -> str:
    """"""
    text = ""
    if newline:
        text += "//\n"

    text += "\n// ".join(
        textwrap.wrap(
            text="// " + comment,
            width=textwidth - len("// ") - len(indent * level),
        )
    )
    text = textwrap.indent(
        text,
        indent * level,
    )
    text += "\n"
    return text


def __get_left_side(key: str, justify: int = 0) -> str:
    """"""
    if justify == 0:
        return f"{dq}{key}{dq}: "
    return f"{dq}{key}{dq}:".ljust(justify)


def __get_right_side(value: Any) -> str:
    """"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return f"{dq}{value}{dq}"
    if isinstance(value, list):
        return str(value).replace(q, dq)
    return json.dumps(value, indent=len(indent))


def __combine(
    leftside: str, rightside: str, level: int = 1, last: bool = False
) -> str:
    """"""
    if last:
        return textwrap.indent(
            str(leftside + rightside + "\n"),
            indent * level,
        )
    return textwrap.indent(
        str(leftside + rightside + ",\n"),
        indent * level,
    )


# ^                                             BOARD                                              ^#
# % ============================================================================================== %#
# % Upgrade the 'board.json5' files.                                                               %#
# %                                                                                                %#


def get_upgraded_json_string_for_board(
    boardname: Optional[str], board_dict: Dict
) -> str:
    """"""
    json_str = ""
    if boardname is None:
        boardname = board_dict["name"]

    # & Top title
    json_str += __get_title(
        title_txt=f"DATA FOR BOARD {q}{boardname}{q}",
        explanation=str(
            f"This file contains all the basic data for the {q}{boardname}{q}. The data presented "
            f"in this file can (potentially) override data in the corresponding {q}chip.json5{q} "
            f"file."
        ),
        underline="=",
        level=0,
    )
    json_str += "//\n"
    json_str += "// "
    json_str += "\n// ".join(
        textwrap.wrap(
            text=str(
                f"NOTE: If the data in the corresponding {q}chip.json5{q} file is good, there is "
                f"no need to override it here."
            ),
            width=textwidth - len("// "),
        )
    )
    json_str += "\n{\n"

    # & MAIN DATA
    # & =========
    json_str += __get_title(
        title_txt="MAIN DATA",
        explanation=f"This is the most basic information from the {q}{boardname}{q} board.",
        underline="-",
        level=1,
    )
    # $ name
    key, value = "name", boardname
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ kind
    key, value = "kind", board_dict["kind"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ boardfamily
    key, value = "boardfamily", board_dict["boardfamily"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ manufacturer
    key, value = "manufacturer", board_dict["manufacturer"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ active
    key, value = "active", board_dict["active"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ icon
    key, value = "icon", board_dict["icon"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ link
    key, value = "link", board_dict["link"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ synonyms
    key, value = "synonyms", board_dict["synonyms"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ user_leds
    key, value = "user_leds", board_dict["user_leds"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ user_buttons
    key, value = "user_buttons", board_dict["user_buttons"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & HARDWARE
    # & ========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="HARDWARE",
        explanation=str(
            "The chip is obviously fixed, the probe is more flexible, but we specify a default "
            "one here. Note that the actual hardware for a sample project is determined by the "
            "'hardware.json5' file in the sample project."
        ),
        underline="-",
        level=1,
    )
    # $ chip
    key, value = "chip", board_dict["chip"]
    leftside = __get_left_side(key, 17)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ probe
    key, value = "default_probe", board_dict["default_probe"]
    leftside = __get_left_side(key, 17)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & WEBPAGE DATA
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="WEBPAGE DATA",
        explanation=f"This is data mainly used for the webpage.",
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}purchase_links{dq}": str(
                "Provide for each distributor (farnell, digikey, ...) the order number and a "
                "weblink."
            ),
            f"{dq}references{dq}": str(
                f"These are the references shown at the bottom of the webpage. There's some freedom "
                f"in which keys to provide. Common ones are: 'webpage', 'schematic', "
                f"'design_files'. Use other fields as placeholders: '{{name}}' will be "
                f"replaced with '{boardname}'."
            ),
        },
        level=1,
    )
    # $ purchase_links
    key, value = "purchase_links", board_dict.get("purchase_links")
    leftside = __get_left_side(key, 18)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ references
    key, value = "references", board_dict.get("references")
    leftside = __get_left_side(key, 18)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & OVERRIDE CHIP DATA
    # & ==================
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="OVERRIDE CHIP DATA",
        explanation=str(
            f"Override (some of) the data in the corresponding {q}chip.json5{q} file. To override "
            f"a certain key-value pair, add a {q}++{q}, {q}--{q} or {q}~~{q} token at the end of "
            f"the key, like:"
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}key++{dq}: <value>": str(
                f"The board value gets added to the chip value. This only works if the chip value "
                f"is a list or a dictionary. Typical example is adding a compiler flag."
            ),
            f"{dq}key--{dq}: <value>": str(
                f"The board value gets subtracted from the chip value. This only works if the chip "
                f"value is a list or dictionary. Typical example is deleting a compiler flag."
            ),
            f"{dq}key~~{dq}: <value>": str(
                f"The board value replaces entirely the chip value."
            ),
        },
        level=1,
    )
    json_str += __get_comment(
        comment=str(f"This system also works for nested key-value pairs."),
        newline=False,
        level=1,
    )
    # Figure out which keys are override-keys
    override_dict = {}
    for key, value in board_dict.items():
        if key.endswith(("++", "--", "~~")):
            override_dict[key] = value
            continue
        if not isinstance(value, dict):
            continue
        for key2, value2 in value.items():
            if key2.endswith(("++", "--", "~~")):
                if key not in override_dict.keys():
                    override_dict[key] = {}
                override_dict[key][key2] = value2
            continue
        continue
    if len(override_dict) == 0:
        json_str += f"{indent}// [Nothing to override]"
    else:
        json_snippet = json.dumps(override_dict, indent=len(indent))
        # Strip off the {} enclosing curly braces
        assert json_snippet.startswith("{")
        assert json_snippet.endswith("}")
        json_snippet = json_snippet[1:-1]
        # Strip off leading and ending '\n'
        json_snippet = json_snippet.strip("\n")
        # Add a comma at the end
        json_snippet += ","
        # Add this snipped to the json string
        json_str += json_snippet
        # print(boardname)
        # print(json_snippet)
    json_str += "\n"

    # & MISCELLANEOUS
    # & =============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"MISCELLANEOUS",
        explanation=str(f"Anything I haven{q}t ordered yet."),
        underline="-",
        level=1,
    )
    # $ arduino_params
    key, value = "arduino_params", board_dict["arduino_params"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside, last=True)

    # & Return json string
    json_str += "}"
    return json_str


# ^                                             CHIP                                               ^#
# % ============================================================================================== %#
# % Upgrade the 'chip.json5' files.                                                                %#
# %                                                                                                %#


def get_upgraded_json_string_for_chip(
    chipname: Optional[str], chip_dict: Dict
) -> str:
    """"""
    json_str = ""
    if chipname is None:
        chipname = chip_dict["name"]

    # & Top title
    json_str += __get_title(
        title_txt=f"DATA FOR CHIP {q}{chipname}{q}",
        explanation=str(
            f"This file contains all the data for the {q}{chipname}{q}, all references to "
            f"supporting files (such as the linkerscript, .gdbinit files, bootloader files, ...) "
            f"that must be copied into a project as well as the parameters that must be filled "
            f"into them. "
            f"Any data presented in this file can be overridden by a {q}board.json5{q} file (in "
            f"other words: board-files take priority over chip-files)."
        ),
        underline="=",
        level=0,
    )
    json_str += "{\n"

    # & MAIN DATA
    # & =========
    json_str += __get_title(
        title_txt="MAIN DATA",
        explanation=f"This is the most basic information from the {q}{chipname}{q} chip.",
        underline="-",
        level=1,
    )
    # $ name
    key, value = "name", chipname
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ kind
    key, value = "kind", chip_dict["kind"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ chipfamily
    key, value = "chipfamily", chip_dict["chipfamily"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ manufacturer
    key, value = "manufacturer", chip_dict["manufacturer"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ active
    key, value = "active", chip_dict["active"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ icon
    key, value = "icon", chip_dict["icon"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ link
    key, value = "link", chip_dict["link"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ synonyms
    key, value = "synonyms", chip_dict["synonyms"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ isa
    key, value = "isa", chip_dict["isa"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ debugger_enabled
    key, value = "debugger_enabled", chip_dict["debugger_enabled"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ pinconfig_enabled
    key, value = "pinconfig_enabled", chip_dict["pinconfig_enabled"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & WEBPAGE DATA
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="WEBPAGE DATA",
        explanation=f"This is data mainly used for the webpage.",
        underline="-",
        level=1,
    )
    # $ purchase_links
    key, value = "purchase_links", chip_dict.get("purchase_links")
    leftside = __get_left_side(key, 18)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ references
    key, value = "references", chip_dict.get("references")
    leftside = __get_left_side(key, 14)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & COMPILER TOOLCHAIN
    # & ==================
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="COMPILER TOOLCHAIN",
        explanation=str(
            f"Define here which compiler toolchain(s) can be used to compile code for this chip."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}default_compiler_uid{dq}": str(
                f"Unique ID from the default compiler toolchain."
            ),
            f"{dq}default_compiler_prefix{dq}": str(
                f"The prefix belonging to the default compiler toolchain."
            ),
            f"{dq}compiler_patterns{dq}": str(
                f"The unique ID from the chosen compiler toolchain should match at least one of "
                f"these patterns."
            ),
        },
        level=1,
    )
    # $ default_compiler_uid
    key, value = "default_compiler_uid", chip_dict["default_compiler_uid"]
    leftside = __get_left_side(key, 27)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ default_compiler_prefix
    key, value = "default_compiler_prefix", chip_dict["default_compiler_prefix"]
    leftside = __get_left_side(key, 27)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ compiler_patterns
    key, value = "compiler_patterns", chip_dict["compiler_patterns"]
    leftside = __get_left_side(key, 27)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & FLASHTOOL
    # & =========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="FLASHTOOL",
        explanation=str(
            f"Define here which flashtool(s) can be used to upload code to this chip."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}default_flashtool_uid{dq}": str(
                f"Unique ID from the default flashtool."
            ),
            f"{dq}flashtool_patterns{dq}": str(
                f"Unique ID from the chosen flashtool should match at least one of these patterns."
            ),
        },
        level=1,
    )
    # $ default_flashtool_uid
    key, value = "default_flashtool_uid", chip_dict["default_flashtool_uid"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ flashtool_patterns
    key, value = "flashtool_patterns", chip_dict["flashtool_patterns"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & MAKEFILE
    # & ========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="MAKEFILE",
        explanation=str(
            f"Embeetle is makefile-based. Define here which python file must be used to generate "
            f"the makefile for this {q}{chipname}{q} chip. "
        ),
        underline="-",
        level=1,
    )
    # $ makefile_generator
    key, value = "makefile_generator", chip_dict["makefile_generator"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & DASHBOARD.MK
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"DASHBOARD.MK",
        explanation=str(
            f"The Embeetle makefile always includes two sub-makefiles: {q}dashboard.mk{q} and "
            f"{q}filetree.mk{q}. The first one represents the Dashboard settings (eg. where to "
            f"find the linkerscript and other files, the compiler flags based on the chosen chip, "
            f"...), the latter represents the checkboxes in the Filetree (it lists the .c, .cpp "
            f"and .s files that should be compiled)."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment(
        comment=str(
            f"Provide following data to generate the {q}dashboard.mk{q} file:"
        ),
        newline=False,
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}dashboard_mk_generator{dq}": str(
                f"This python module will generate the whole {q}dashboard.mk{q} file, based on "
                f"the data in this json-file. If you dive into the python module, you{q}ll notice "
                f"that it goes even further - it requires the data from the board, chip and probe "
                f"json-dictionaries, as well as the locations of several important project files "
                f"(linkerscript, binaries, ...). Embeetle provides all that data when the python "
                f"module gets invoked."
            ),
            f"{dq}binary_rules_generator{dq}": str(
                f"The python module mentioned above is unable to complete its task alone. It needs "
                f"a little help from this binary_rules_generator python module. This module "
                f"generates the {q}BINARIES{q} section in {q}dashboard.mk{q}."
            ),
            f"{dq}flash_rules_generator{dq}": str(
                f"Also to make the {q}FLASH RULES{q} section in {q}dashboard.mk{q}, a little help "
                f"is needed. That{q}s where this flash_rules_generator python module jumps in. The "
                f"probe can also point to such a module, which will then take precedence."
            ),
            f"{dq}cpu_flags{dq}": str(
                f"These cpu_flags get added to the TARGET_COMMONFLAGS variable in "
                f"{q}dashboard.mk{q}."
            ),
            f"{dq}compiler_flags{dq}": str(
                f"List all the flags required to compile the source files for this "
                f"{q}{chipname}{q} chip. They get added to the {q}COMPILATION FLAGS{q} section "
                f"in {q}dashboard.mk{q}."
            ),
        },
        level=1,
    )
    # $ dashboard_mk_generator
    key, value = "dashboard_mk_generator", chip_dict["dashboard_mk_generator"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ binary_rules_generator
    key, value = "binary_rules_generator", chip_dict["binary_rules_generator"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ flash_rules_generator
    key, value = "flash_rules_generator", chip_dict["flash_rules_generator"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ cpu_flags
    key, value = "cpu_flags", chip_dict["cpu_flags"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ compiler_flags
    key, value = "compiler_flags", chip_dict["compiler_flags"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & FILETREE.MK
    # & ===========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"FILETREE.MK",
        explanation=str(
            f"As mentioned before, the Embeetle {q}makefile{q} always includes {q}dashboard.mk{q} "
            f"and {q}filetree.mk{q}. The latter one lists all the source files that take part in "
            f"the build. Embeetle does this automatically, but needs a little push now and then "
            f"from some heuristics:"
        ),
        underline="-",
        level=1,
    )
    # $ heuristics
    key, value = "heuristics", chip_dict["heuristics"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & LINKERSCRIPT
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"LINKERSCRIPT",
        explanation=str(
            f"A microcontroller project can have one or more linkerscripts. In case there are "
            f"multiple, usually one *main* linkerscript invokes the others. List the "
            f"{dq}linkerscript_generators{dq} below. These are python-file(s) that generate a "
            f"linkerscript (based on some input from this json-file), or just plain linkerscript "
            f"file(s) that must be copied as-is into the project."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment(
        comment=str(
            f"The order at which you list these linkerscript (generators) matters. Embeetle "
            f"considers the first one as your *main* linkerscript, and passes that one explicitely "
            f"to the linker. The other ones just sit next to it."
        ),
        newline=True,
        level=1,
    )
    json_str += __get_comment(
        comment=str(
            f"You can also add some linkerscript parameters in the {dq}params{dq} listing. The "
            f"usual ones are:"
        ),
        newline=True,
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}MIN_HEAP_SIZE{dq}": (
                f"Minimum size of the heap, eg. {dq}0x200{dq}."
            ),
            f"{dq}MIN_STACK_SIZE{dq}": (
                f"Minimum size of the stack, eg. {dq}0x400{dq}."
            ),
            f"{dq}ESTACK{dq}": f"The end of stack, eg. {dq}0x20002000{dq}.",
        },
        level=1,
    )
    json_str += __get_comment(
        comment=str(
            f"These parameters can be literally anything that should be passed on to the "
            f"linkerscript generator(s), such that they can spit out the correct linkerscript(s) "
            f"for this board/chip."
        ),
        newline=True,
        level=1,
    )
    json_str += __get_comment(
        comment=str(
            f"Finally, list the memory segments as they are shown in the linkerscript."
        ),
        newline=True,
        level=1,
    )
    # $ linkerscript
    key, value = "linkerscript", chip_dict["linkerscript"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & SUPPLEMENTARY FILES
    # & ===================
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="SUPPLEMENTARY FILES",
        explanation=str(
            f"List here supplementary files (such as bootloaders) that can be used for the "
            f"{q}{chipname}{q} chip.\n"
            f"At *project creation time*, they get copied from their original location into the "
            f"{q}<project>/config/{q} folder.\n"
            f"At *project runtime*, the Dashboard Project Layout section takes note of their "
            f"project locations. In other words, Project Layout entries such as "
            f"{q}BOOTLOADER_FILE{q}, {q}BOOTSWITCH_FILE{q} and {q}PARTITIONS_CSV_FILE{q} get filled "
            f"up. That{q}s how these values end up in the {q}dashboard.mk{q} file, where they can "
            f"be used in certain rules."
        ),
        underline="-",
        level=1,
    )
    # $ boot
    key, value = "boot", chip_dict["boot"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & OPENOCD_CHIP.CFG
    # & ================
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"OPENOCD_CHIP.CFG",
        explanation=str(f"List all data relevant for {q}openocd_chip.cfg{q}:"),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}openocd_chip_cfg_generator{dq}": str(
                f"Point to the python module that generates {q}openocd_chip.cfg{q}."
            ),
            f"{dq}target_file{dq}": str(
                f"The location of the OpenOCD config file that represents this chip/board, "
                f"relative to the {q}scripts{q} folder within the OpenOCD installation."
            ),
        },
        level=1,
    )
    # $ openocd
    key, value = "openocd", chip_dict["openocd"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    assert "openocd_chip_cfg_generator" in value.keys()
    assert "target_file" in value.keys()
    assert "prestatements" not in value.keys()
    assert "poststatements" not in value.keys()
    json_str += __combine(leftside, rightside)

    # & .GDBINIT
    # & ========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f".GDBINIT",
        explanation=str(
            f"List all the data relevant for the {q}.gdbinit{q} file. First and foremost, "
            f"list the .gdbinit(s) that must be copied into the project. These files might contain "
            f"placeholders between $<..> symbols. Currently, these placeholders can be filled with "
            f"parameters extracted from the linkerscript data. If extra data is needed, place it "
            f"below."
        ),
        underline="-",
        level=1,
    )
    # $ gdb_init
    key, value = "gdb_init", chip_dict["gdb_init"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & MISCELLANEOUS
    # & =============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"MISCELLANEOUS",
        explanation=str(f"Anything I haven{q}t ordered yet."),
        underline="-",
        level=1,
    )
    # $ arduino_params
    key, value = "arduino_params", chip_dict["arduino_params"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside, last=True)

    # & Return json string
    json_str += "}"
    return json_str


# ^                                          BOARDFAMILY                                           ^#
# % ============================================================================================== %#
# % Upgrade the 'family.json5' files.                                                              %#
# %                                                                                                %#


def get_upgraded_json_string_for_boardfam(
    boardfam_name: Optional[str], boardfam_dict: Dict
) -> str:
    """"""
    json_str = ""
    if boardfam_name is None:
        boardfam_name = boardfam_dict["name"]

    # & Top title
    json_str += __get_title(
        title_txt=f"DATA FOR BOARDFAMILY {q}{boardfam_name}{q}",
        explanation=str(
            f"This file contains very basic data for the {q}{boardfam_name}{q} boardfamily. More "
            f"detailed data is given in the specific boardfiles."
        ),
        underline="=",
        level=0,
    )
    json_str += "{\n"

    # $ name
    key, value = "name", boardfam_name
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ kind
    key, value = "kind", boardfam_dict["kind"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ active
    key, value = "active", boardfam_dict["active"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ icon
    key, value = "icon", boardfam_dict["icon"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ synonyms
    key, value = "synonyms", boardfam_dict["synonyms"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ manufacturer
    key, value = "manufacturer", boardfam_dict["manufacturer"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside, last=True)

    # & Return json string
    json_str += "}"
    return json_str


# ^                                           CHIPFAMILY                                           ^#
# % ============================================================================================== %#
# % Upgrade the 'family.json5' files.                                                              %#
# %                                                                                                %#


def get_upgraded_json_string_for_chipfam(
    chipfam_name: Optional[str], chipfam_dict: Dict
) -> str:
    """"""
    json_str = ""
    if chipfam_name is None:
        chipfam_name = chipfam_dict["name"]

    # & Top title
    json_str += __get_title(
        title_txt=f"DATA FOR CHIPFAMILY {q}{chipfam_name}{q}",
        explanation=str(
            f"This file contains very basic data for the {q}{chipfam_name}{q} chipfamily. More "
            f"detailed data is given in the specific chipfiles."
        ),
        underline="=",
        level=0,
    )
    json_str += "{\n"

    # $ name
    key, value = "name", chipfam_name
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ kind
    key, value = "kind", chipfam_dict["kind"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ active
    key, value = "active", chipfam_dict["active"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ icon
    key, value = "icon", chipfam_dict["icon"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ synonyms
    key, value = "synonyms", chipfam_dict["synonyms"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ manufacturer
    key, value = "manufacturer", chipfam_dict["manufacturer"]
    leftside = __get_left_side(key, 22)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside, last=True)

    # & Return json string
    json_str += "}"
    return json_str


# ^                                              PROBE                                             ^#
# % ============================================================================================== %#
# % Upgrade the '<probe>.json5' files.                                                             %#
# %                                                                                                %#


def get_upgraded_json_string_for_probe(
    probe_name: Optional[str], probe_dict: Dict
) -> str:
    """"""
    json_str = ""
    if probe_name is None:
        probe_name = probe_dict["name"]

    # & Top title
    json_str += __get_title(
        title_txt=f"DATA FOR PROBE {q}{probe_name}{q}",
        explanation=str(
            f"This file contains very basic data for the {q}{probe_name}{q} probe."
        ),
        underline="=",
        level=0,
    )
    json_str += "{\n"

    # & MAIN DATA
    # & =========
    json_str += __get_title(
        title_txt="MAIN DATA",
        explanation=f"This is the most basic information from the {q}{probe_name}{q} probe.",
        underline="-",
        level=1,
    )
    # $ name
    key, value = "name", probe_name
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ kind
    key, value = "kind", probe_dict["kind"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ active
    key, value = "active", probe_dict["active"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ icon
    key, value = "icon", probe_dict["icon"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ synonyms
    key, value = "synonyms", probe_dict["synonyms"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ manufacturer
    key, value = "manufacturer", probe_dict["manufacturer"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ built_in
    key, value = "built_in", probe_dict["built_in"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ link
    key, value = "link", probe_dict["link"]
    leftside = __get_left_side(key, 16)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & WEBPAGE DATA
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="WEBPAGE DATA",
        explanation=f"This is data mainly used for the webpage.",
        underline="-",
        level=1,
    )
    # $ purchase_links
    key, value = "purchase_links", probe_dict.get("purchase_links")
    leftside = __get_left_side(key, 18)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & FLASHTOOL
    # & =========
    json_str += "\n\n"
    json_str += __get_title(
        title_txt="FLASHTOOL",
        explanation=str(
            f"Define here which flashtool(s) can be used with this probe."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}default_flashtool_uid{dq}": str(
                f"Unique ID from the default flashtool. Beware: the one from the chip.json file "
                f"has precedence! To override the one from the chip.json file, you must set the "
                f"{q}default_flashtool_uid{q} override in the board.json file."
            ),
            f"{dq}flashtool_patterns{dq}": str(
                f"Unique ID from the chosen flashtool should match at least one of these patterns."
            ),
            f"{dq}transport_protocols{dq}": str(
                f"List the transport protocols (such as {q}jtag{q}, {q}swd{q}, ...) compatible "
                f"with this probe."
            ),
            f"{dq}needs_serial_port{dq}": str(
                f"Does this probe upload the firmware over a serial port? Does Embeetle need to "
                f"show a dropdown menu for selecting the COM-port/TTY-port?"
            ),
            f"{dq}can_flash_bootloader{dq}": str(
                f"Can this probe flash a bootloader? If yes, Embeetle will make the corresponding "
                f"field in the Dashboard {q}relevant{q} and add a button for flashing the "
                f"bootloader."
            ),
        },
        level=1,
    )
    # $ default_flashtool_uid
    key, value = "default_flashtool_uid", probe_dict["default_flashtool_uid"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ flashtool_patterns
    key, value = "flashtool_patterns", probe_dict["flashtool_patterns"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ transport_protocols
    key, value = "transport_protocols", probe_dict["transport_protocols"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ needs_serial_port
    key, value = "needs_serial_port", probe_dict["needs_serial_port"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)
    # $ can_flash_bootloader
    key, value = "can_flash_bootloader", probe_dict["can_flash_bootloader"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & DASHBOARD.MK
    # & ============
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"DASHBOARD.MK",
        explanation=str(
            f"List the data necessary to generate the {q}dashboard.mk{q} file."
        ),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}flash_rules_generator{dq}": str(
                f"Point to the python module that generates the {q}FLASH RULES{q} section in "
                f"{q}dashboard.mk{q}. The chip also points to such a python module. The probe must "
                f"only do this if the module pointed at by the chip is not compatible."
            ),
        },
        level=1,
    )
    # $ flash_rules_generator
    key, value = "flash_rules_generator", probe_dict["flash_rules_generator"]
    leftside = __get_left_side(key, 25)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside)

    # & OPENOCD_PROBE.CFG
    # & =================
    json_str += "\n\n"
    json_str += __get_title(
        title_txt=f"OPENOCD_PROBE.CFG",
        explanation=str(f"List all data relevant for {q}openocd_probe.cfg{q}:"),
        underline="-",
        level=1,
    )
    json_str += __get_comment_listing(
        comment_dict={
            f"{dq}openocd_probe_cfg_generator{dq}": str(
                f"This python module generates the {q}openocd_probe.cfg{q} file, based on the data "
                f"presented below."
            ),
            f"{dq}target_file{dq}": str(
                f"The location of the OpenOCD config file that represents this probe, "
                f"relative to the {q}scripts{q} folder within the OpenOCD installation."
            ),
        },
        level=1,
    )
    # $ openocd
    key, value = "openocd", probe_dict["openocd"]
    leftside = __get_left_side(key)
    rightside = __get_right_side(value)
    json_str += __combine(leftside, rightside, last=True)

    # & Return json string
    json_str += "}"
    return json_str


# ^                                              MAIN                                              ^#
# % ============================================================================================== %#
# % Main function to do the thing you want.                                                        %#
# %                                                                                                %#


def treat_file(abspath: str) -> None:
    """"""
    # The name of the chip, board or probe can be deduced from the absolute path to the file. It
    # equals the name of the parental folder. However, this is no longer true for files in the
    # C:/sample_proj_resources folder!
    item_name: Optional[str] = None
    if abspath.startswith(sample_path):
        item_name = None
    else:
        item_name: str = abspath.split("/")[-2]
    # Original python dictionary, extracted from the original 'chip.json5'
    original_dict: Optional[Dict] = None
    # Reformatted json-string, created from the data in 'chip_dict_original'
    reformatted_json_str: Optional[str] = None
    # Python dictionary loaded from the 'reformatted_json_str'. Will be compared to the python dict
    # from the original json file.
    new_dict: Optional[Dict] = None

    # & Extract 'original_dict'
    with open(
        abspath, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        original_dict = json.loads(
            "\n".join(
                line for line in f if not line.strip().startswith(("//", "#"))
            )
        )

    # & Convert 'original_dict' to 'reformatted_json_str'
    try:
        # $ CHIP
        if abspath.endswith("/chip.json5"):
            reformatted_json_str = get_upgraded_json_string_for_chip(
                chipname=item_name,
                chip_dict=original_dict,
            )
        # $ BOARD
        elif abspath.endswith("/board.json5"):
            reformatted_json_str = get_upgraded_json_string_for_board(
                boardname=item_name,
                board_dict=original_dict,
            )
        elif abspath.endswith("/family.json5"):
            # $ BOARDFAMILY
            if abspath.split("/")[-4] == "board":
                reformatted_json_str = get_upgraded_json_string_for_boardfam(
                    boardfam_name=item_name,
                    boardfam_dict=original_dict,
                )
            # $ CHIPFAMILY
            if abspath.split("/")[-4] == "chip":
                reformatted_json_str = get_upgraded_json_string_for_chipfam(
                    chipfam_name=item_name,
                    chipfam_dict=original_dict,
                )
        # $ PROBE
        elif abspath.endswith("/probe.json5"):
            reformatted_json_str = get_upgraded_json_string_for_probe(
                probe_name=item_name,
                probe_dict=original_dict,
            )
    except:
        print(f"ERROR: Cannot upgrade json-string from {q}{abspath}{q}!")
        raise

    # & Convert 'reformatted_json_str' to 'new_dict'
    try:
        new_dict = json.loads(
            "\n".join(
                line
                for line in reformatted_json_str.splitlines()
                if not line.strip().startswith(("//", "#"))
            )
        )
    except:
        print(reformatted_json_str)
        raise
        return

    # & Compare 'original_dict' to 'new_dict'
    diff = deepdiff.DeepDiff(original_dict, new_dict)
    # print(f'Diff for {q}{item_name}{q} = {diff}')
    # diff = {}

    # & If okay, write to file
    if diff != {}:
        # print(f'    => ignore file')
        # import pprint
        # print(reformatted_json_str)
        # print('')
        # print('')
        # pprint.pprint(original_dict)
        # raise RuntimeError()
        pass
    with open(
        abspath, "w", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(reformatted_json_str)
    if abspath.endswith("chip.json5"):
        # print(f'    => wrote new json string to {q}chip.json5{q}')
        pass
    elif abspath.endswith("board.json5"):
        # print(f'    => wrote new json string to {q}board.json5{q}')
        pass
    elif abspath.endswith("family.json5"):
        # print(f'    => wrote new json string to {q}family.json5{q}')
        pass
    else:
        # print(f'    => wrote new json string to {q}{item_name}.json5{q}')
        pass
    return


if __name__ == "__main__":
    if not os.path.isdir(hardware_path):
        print(f"Cannot find: {q}{hardware_path}{q}")
    if not os.path.isdir(sample_path):
        print(f"Cannot find: {q}{sample_path}{q}")
    # $ Treat files in the Embeetle hardware database
    for root, dirs, files in os.walk(hardware_path):
        for name in files:
            if not name.endswith(".json5"):
                continue
            _abspath: str = os.path.join(root, name).replace("\\", "/")
            try:
                if name == "chip.json5":
                    treat_file(_abspath)
                    continue
                elif name == "board.json5":
                    treat_file(_abspath)
                    continue
                elif name == "family.json5":
                    treat_file(_abspath)
                    continue
                elif name == "probe.json5":
                    treat_file(_abspath)
                    continue
                else:
                    # Ignore this json-file
                    pass
            except:
                print(f"Can{q}t read file {q}{_abspath}{q}")
                raise
            continue
        continue

    # $ Treat files in the 'sample_proj_resources' repo
    for root, dirs, files in os.walk(sample_path):
        for name in files:
            if not name.endswith(".json5"):
                continue
            _abspath: str = os.path.join(root, name).replace("\\", "/")
            try:
                if name == "chip.json5":
                    treat_file(_abspath)
                    continue
                elif name == "board.json5":
                    treat_file(_abspath)
                    continue
                elif name == "probe.json5":
                    treat_file(_abspath)
                    continue
                else:
                    # Ignore this json-file
                    pass
            except:
                print(f"Can{q}t read file {q}{_abspath}{q}")
                raise
            continue
        continue
