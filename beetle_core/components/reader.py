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
import functions
import regex as re

# Trick to give custom names to enums:
# https://www.notinventedhere.org/articles/python/how-to-use-strings-as-name-aliases-in-python-enums.html
""" --------------------------------------------------------------------------- """
""" PART 1:      CHIP.TXT, PROBE.TXT, PATHS.TXT READER                          """
""" --------------------------------------------------------------------------- """


def get_dictionary(filepath: str, dict_name: str) -> Dict:
    """Get a dictionary from the given file with the given dictionary name.

    :param filepath: The path to the file you want to parse.
    :param dict_name: The name of the dictionary you want to extract from the
        file.
    :return: Dictionary instance dict
    :rtype: dict
    """
    file = open(filepath)
    script = file.read().replace("\r\n", "\n")
    file.close()
    # Search for the right dictionary
    if not dict_name.startswith("_"):
        dict_name = "_" + dict_name
    p = re.compile(
        dict_name + r"\s*=\s*({(?>[^{}]|(?1))*})",
        re.MULTILINE | re.DOTALL,
    )
    try:
        script = p.search(script).group(0)
    except Exception as e:
        print(f"Exception {e}")
        print(f"In script:")
        print(script)
        raise
    return functions.load_module(script, {})[dict_name]


""" --------------------------------------------------------------------------- """
""" PART 2:      TEMPLATE READER                                                """
""" --------------------------------------------------------------------------- """


def get_filled_template(template_abspath: str, filling_dict: Dict) -> str:
    """Read the template at 'template_abspath' and fill its $<VAR> with the
    values from the 'filling_dict'. Return the result as a large string.

    :param template_abspath:   Absolute path to the template file.
    :param filling_dict:       Dictionary with values to replace the $<VAR>
                               in the template.

    :return:                   The filled template as a large string.

    Note: This function doesn't create a file on the harddisk! You've got to
    save the returned string yourself.
    """
    # * 1. Read template text.
    template_text = ""
    with open(
        template_abspath, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        template_text = f.read().replace("\r\n", "\n")
        f.close()
    orig_linelist = template_text.splitlines()
    new_linelist = []
    # * 2. Fill template with values from the dictionary.
    for orig_line in orig_linelist:
        # $ No keyword in original line
        if "$<" not in orig_line:
            # Nothing to be changed
            new_linelist.append(orig_line)
            continue
        # $ One or more keyword(s) in original line
        assert "$<" in orig_line
        minidict = {}
        for k, v in filling_dict.items():
            if f"$<{k}>" in orig_line:
                minidict[k] = v
        if len(minidict) == 0:
            # $ => No corresponding key(s) found
            new_linelist.append(orig_line)
            continue
        # $ => Corresponding key(s) found
        new_line = orig_line
        for k, v in minidict.items():
            p = re.compile(r"[$]<(" + k + r")>")
            if v is not None:
                if isinstance(v, str):
                    new_line = p.sub(
                        v.replace("\\", "\\" + "\\"),
                        new_line,
                    )
            else:
                new_line = p.sub(
                    "None",
                    new_line,
                )
        if new_line.strip() == "":
            # Key has empty value, resulting in empty line.
            # Do not add an empty line to the list!
            continue
        new_linelist.append(new_line)
    return "\n".join(new_linelist)
