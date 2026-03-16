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

##
## Module with functions that only use the standard library and installed modules
##

from __future__ import annotations
from typing import *
import sys
import os
import os.path
import pathlib
import locale
import itertools
import subprocess
import time
import threading
import traceback
import types
import re
import argparse
import hashlib
import colorama
import json
import packaging
import packaging.version
import copy
import shlex
import shutil
import importlib
import datetime
import textwrap
import data
import qt
import os_checker
from various.kristofstuff import *

if TYPE_CHECKING:
    try:
        from _hashlib import HASH as Hash
    except:
        from hashlib import HASH as Hash


def get_short_path_name(long_name: str) -> str:
    """Returns the short path name (8.3 style) for a given long path on Windows.

    If not on Windows, returns the path unchanged.
    """
    if os_checker.is_os("windows"):
        from ctypes import create_unicode_buffer, windll

        buffer = create_unicode_buffer(260)  # MAX_PATH
        windll.kernel32.GetShortPathNameW(long_name, buffer, 260)
        short_name = buffer.value
        if short_name is not None:
            return short_name.replace("\\", "/")
    else:
        # On non-Windows, just return as-is
        pass
    return long_name


def load_module(script, globs, new_style_name=None) -> Dict:
    """"""
    code = ""
    try:
        if os.path.isfile(script):
            # OPTION 1: Parameter 'script' represents
            #           the filepath to a python script.
            with open(script, "r", encoding="utf-8", newline="\n") as f:
                code = f.read()
                f.close()
        else:
            # OPTION 2: Parameter 'script' represents
            #           the python script itself.
            code = script
    except:
        code = script

    if new_style_name is not None:
        module = types.ModuleType(new_style_name)
        exec(code, module.__dict__ + globs)
        return module
    else:
        module = globs
        exec(code, module)
        return module


def get_directory_structure_old(rootdir):
    """Creates a nested dictionary that represents the folder structure of
    rootdir."""
    #    performance_timer_start()
    rootdir = unixify_path(rootdir)
    directory_structure = {rootdir: {}}
    directory_count = 0
    file_count = 0
    for path, dirs, files in os.walk(rootdir):
        parent = directory_structure[rootdir]
        if path != rootdir:
            for i in unixify_path_remove(path, rootdir).split("/"):
                if i not in parent.keys():
                    parent[i] = {}
                parent = parent[i]
                directory_count += 1
        for f in files:
            parent[f] = unixify_path_join(path, f)
            file_count += 1
    #    performance_timer_show()
    return directory_structure, directory_count, file_count


def get_directory_structure(rootdir):
    """Creates a nested dictionary that represents the folder structure of
    rootdir."""
    #    performance_timer_start()
    rootdir = unixify_path(rootdir)
    directory_structure = {
        rootdir: {
            "//type//": "directory",
            "//full//": rootdir,
            "//relative//": "",
            "//directories//": {},
            "//files//": {},
        }
    }
    directory_count = 0
    file_count = 0
    for path, dirs, files in os.walk(rootdir):
        parent = directory_structure[rootdir]
        if path != rootdir:
            sub_path_list = []
            sub_paths = unixify_path_remove(path, rootdir).split("/")
            for i in sub_paths:
                sub_path_list.append(i)
                if i not in parent["//directories//"].keys():
                    directory_full_path = unixify_path_join(
                        rootdir, *sub_path_list
                    )
                    directory_relative_path = os.path.relpath(
                        directory_full_path, rootdir
                    ).replace("\\", "/")
                    parent["//directories//"][i] = {
                        "//type//": "directory",
                        "//full//": directory_full_path,
                        "//relative//": directory_relative_path,
                        "//directories//": {},
                        "//files//": {},
                    }
                parent = parent["//directories//"][i]
                directory_count += 1
        for f in files:
            file_full_path = unixify_path_join(path, f)
            file_relative_path = os.path.relpath(
                file_full_path, rootdir
            ).replace("\\", "/")
            parent["//files//"][f] = {
                "//type//": "file",
                "//full//": file_full_path,
                "//relative//": file_relative_path,
            }
            file_count += 1
    #    performance_timer_show("get_directory_structure")
    #    json_string = json.dumps(directory_structure, indent=2, ensure_ascii=False)
    #    print(json_string)
    return directory_structure, directory_count, file_count


def remove_all_dict_keys(obj, *keys_to_remove: str) -> None:
    """"""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in keys_to_remove:
                del obj[key]
            else:
                remove_all_dict_keys(obj[key], *keys_to_remove)


def any_keys_in_dict(dictionary: Optional[dict], *keys: str) -> bool:
    """"""
    if dictionary is None:
        return False
    if any([x in dictionary.keys() for x in keys]):
        return True
    for k, v in dictionary.items():
        if isinstance(v, dict):
            result = any_keys_in_dict(v, *keys)
            if result:
                return result
    return False


def test_text_file(file_with_path):
    """Test if a file is a plain text file and can be read."""
    # Try to read all of the lines in the file, return None if there is an error
    # (using Grace Hopper's/Alex Martelli's forgivness/permission principle)
    # @Kristof
    file_with_path_lower = file_with_path.lower()
    if (
        file_with_path_lower.endswith(".a")
        or file_with_path_lower.endswith(".o")
        or file_with_path_lower.endswith(".so")
        or file_with_path_lower.endswith(".dll")
    ):
        return "non-text"
    try:
        with open(
            file_with_path,
            "r",
            encoding=locale.getpreferredencoding(),
            errors="strict",
        ) as file:
            # Read only a couple of lines in the file
            for line in itertools.islice(file, 10):
                line = line
            # Close the file handle
            file.close()
            # Return the systems preferred encoding
            return locale.getpreferredencoding()
    except:
        test_encodings = [
            "utf-8",
            "ascii",
            "utf-16",
            "utf-32",
            "iso-8859-1",
            "latin-1",
        ]
        for current_encoding in test_encodings:
            try:
                with open(
                    file_with_path,
                    "r",
                    encoding=current_encoding,
                    errors="strict",
                ) as file:
                    # Read only a couple of lines in the file
                    for line in itertools.islice(file, 10):
                        line = line
                    # Close the file handle
                    file.close()
                    # Return the succeded encoding
                    return current_encoding
            except:
                # Error occured while reading the file, skip to next iteration
                continue
    # Error, no encoding was correct
    return None


def test_binary_file(file_with_path):
    """Test if a file is in binary format."""
    # @Kristof
    if file_with_path.endswith(".a"):
        return None
    file = open(file_with_path, "rb")
    # Read only a couple of lines in the file
    binary_text = None
    for line in itertools.islice(file, 20):
        if b"\x00" in line:
            # Return to the beginning of the binary file
            file.seek(0)
            # Read the file in one step
            binary_text = file.read()
            break
    file.close()
    # Return the result
    return binary_text


# ^                                          PATH SETUP                                            ^#
# % ============================================================================================== %#
# % Functions regarding the PATH env variable.                                                     %#
# %                                                                                                %#
def apply_path_changes():
    """Restart the currently running program to apply changes to environment
    variables like LD_LIBRARY_PATH on Linux, PATH on Windows or LD_LIBRARY_PATH
    on both.

    Changes to variables like PATH, PYTHONPATH and LD_LIBRARY_PATH are only
    effective for subprocesses; they do not apply to the process that makes the
    change.  To apply changes in Embeetle itself, Embeetle must be restarted
    after making initial changes.  This is in particular important when loading
    a dll/so that requires specific settings in Embeetle (think: source
    analyzer).

    Call this function only when an environment variable needs to be changed;
    calling it unconditionally results in infinite recursion.
    """

    # On Linux, the most efficient way to restart the current program is to use
    # a function of the os.exec* family, e.g. os.execv().  This starts a program
    # in the current process.  Windows does not natively provide exec*
    # functionality.  There are emulated os.exec* functions, but these behave
    # differently, because Windows cannot start another program in the current
    # process. The os.exec* functions will therefore always create a new
    # process. Sadly, these os.exec* return immediately after creating the new
    # process. The effect is that the program starts in the background, and the
    # terminal from which it was started immediately shows a new prompt.
    # To remedy this situation, we will use subprocess.call(...) on Windows
    # instead of os.execv(...). This will also create a new process, and
    # makes the original process wait until the new process exits.  As a
    # result, behavior is the same as on Linux, except that there is a small
    # extra overhead due to the extra process.
    # Note: using os.spawnv(os.P_WAIT, ...) instead of subprocess.call is
    # not a good idea, because it does not quote arguments containing spaces
    # or other special characters when creating the Windows command line to
    # be executed.
    # The command to be executed depends on whether the program is running in
    # interpreted mode or in compiled mode. In interpreted mode, the command
    # is sys.executable (= the python excutable) and not sys.argv[0] (= the
    # command typed on the command line).
    if getattr(sys, "frozen", False) == False:
        # Running in a Python interpreter
        program = sys.executable
        argv = [program] + sys.argv
    else:
        # Running as compiled code
        program = sys.argv[0]
        argv = sys.argv
    try:
        if os_checker.is_os("windows"):
            rc = subprocess.call([program] + argv[1:])
            sys.exit(rc)
        else:
            os.execv(program, argv)
    except Exception as exception:
        print(f"Failed to re-execute after setting paths")
        print(f"program: {program}")
        print(f"argv: {' '.join(argv)}")
        print(f"exception: {exception}")
        sys.exit(1)


def fix_environment_variables(**vars):
    """Restart Embeetle with path environment variable <name> set to <value> and
    then restore the original value."""
    backup_prefix = "EMBEETLE_ORIGINAL_"
    fixed_flag = "EMBEETLE_FIXED"

    def delete_environment_variable(name):
        os.environ.pop(name, None)

    def copy_environment_variable(source, destination):
        value = os.environ.get(source, None)
        if value:
            os.environ[destination] = value
        else:
            delete_environment_variable(destination)

    # Avoid infinite recursion: don't fix what is already fixed
    fixed_vars = os.environ.get(fixed_flag)
    if fixed_vars:
        # $ IN SECOND PROCESS
        # Restore original values before returning
        for _name in fixed_vars.split(":"):
            copy_environment_variable(backup_prefix + _name, _name)
            delete_environment_variable(backup_prefix + _name)
            continue
        delete_environment_variable(fixed_flag)

        if os_checker.is_os("windows"):
            # Patch the PATH for `make`.
            # On Windows, `make searches PATH for a directory containing
            # `sh.exe` and uses that as a shell. The SHELL make variable is set
            # to the full path of `sh.exe` and a unix style shell is assumed.
            # If no `sh.exe` is found, the SHELL make variable is set to
            # `sh.exe` without path and a cmd style shell is assumed.
            # Some instances of `sh.exe` do not work as expected. One example is
            # the `sh.exe` installed together with WinAVR, which is not able to
            # execute commands by default (it probably needs some extra PATH
            # entries or other settings).
            # Embeetle tries to be as independent as possible of the environment
            # in which it is running. For this reason, we remove all PATH
            # entries that contain a `sh.exe`.
            os.environ["PATH"] = os.pathsep.join(
                [
                    dir
                    for dir in os.environ.get("PATH", "").split(os.pathsep)
                    if not os.access(os.path.join(dir, "sh.exe"), os.X_OK)
                ]
            )
        else:
            # Work-around for bug in makefile of old projects on Linux: when
            # Embeetle is started from the start menu (and not from a shell), the
            # environment variable "_" remains undefined which causes old
            # makefiles to select "cmd" as shell style, i.e. to use Windows cmd
            # commands. The work-around is to make sure that "_" is always
            # defined on Linux.
            if not os.environ.get("_", None):
                os.environ["_"] = sys.argv[0]

        return

    # $ IN FIRST PROCESS
    os.environ[fixed_flag] = ":".join(vars.keys())
    for _name, value in vars.items():
        copy_environment_variable(_name, backup_prefix + _name)
        os.environ[_name] = value
        continue
    apply_path_changes()
    # apply_path_changes never returns
    assert False


def get_path_fixes():
    """Return a dictionary with environment variables that need to be patched to
    run Embeetle. Keys are the names of variables to be patches, and values are
    the desired values.

    This includes changes to PYTHONPATH so that imports of Embeetle's own
    modules succeed as well as changes to LD_LIBRARY_PATH (Linux) or PATH
    (Windows) to ensure that .so's or .dll's in the Embeetle installation are
    found.
    """
    if os_checker.is_os("windows"):
        # On Windows, PATH is used to search for both commands and DLLs, aka
        # dynamically linked libraries.
        lib_path_name = "PATH"
    else:
        # On Linux, PATH is used to search for commands and LD_LIBRARY_PATH is
        # used to search for shared objects, aka dynamically linked libraries.
        lib_path_name = "LD_LIBRARY_PATH"
    beetle_root = os.path.dirname(data.beetle_core_directory)
    beetle_lib_path = os.pathsep.join(
        [data.sys_lib, os.environ.get(lib_path_name, "")]
    )
    return {
        lib_path_name: beetle_lib_path,
        "PYTHONPATH": data.sys_esa,
    }


def fix_paths_in_global_environment():
    """Fix environment variables in the global environment (os.environ) so that
    Embeetle python modules and .dll's or .so's are found.

    The changes will take effect for all subprocesses started from Embeetle, but
    not for Embeetle itself.
    """
    for name, value in get_path_fixes().items():
        print(f"setenv {name}={value}")
        os.environ[name] = value


def fix_paths_for_embeetle_and_restore_global_environment():
    """Fix environment variables in Embeetle,  but keep the original value in
    the global environment.

    This requires a restart of Embeetle,  which will be performed automatically.
    """
    fix_environment_variables(**get_path_fixes())


"""
==============================[ END PATH SETUP ]================================
"""


def parse_arguments() -> argparse.Namespace:
    """Parse Embeetle commandline arguments."""
    # Initialize the argument parser
    arg_parser = argparse.ArgumentParser()

    # & Run Embeetle in testing mode
    arg_parser.add_argument(
        "--testing_mode",
        action="store_true",
        dest="testing_mode",
        default=False,
        help="Run Embeetle in testing mode.",
    )

    # & Version number
    arg_parser.add_argument(
        "--multiprocessing-fork",
        action="store",
        dest="multiprocessing_fork",
        default=None,
    )

    # & Version number
    arg_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Embeetle Version: {get_embeetle_version()}",
    )

    # & Force makefile version nr
    arg_parser.add_argument(
        "-mv",
        "--makefile-version",
        action="store",
        default=None,
        type=int,
        dest="makefile_version",
        help="Force a specific makefile version nr.",
    )

    # & Splash screen
    arg_parser.add_argument(
        "--show-splash",
        action="store_true",
        default=False,
        dest="show_splash",
        help="Show Qt based splash screen",
    )

    # & Filetree progbar mode
    arg_parser.add_argument(
        "-prog",
        "--progbar",
        action="store_true",
        default=False,
        dest="filetree_progbar_mode",
        help=str(
            "Filetree progbar mode: show progressbars at the top of "
            "the Filetree."
        ),
    )

    # & Debug mode
    arg_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        dest="debug_mode",
        help="Debug mode: display all output in the terminal.",
    )

    # & Logging mode
    arg_parser.add_argument(
        "-l",
        "--logging",
        action="store_true",
        default=False,
        dest="logging_mode",
        help="Logging mode: show the logging window on startup.",
    )

    # & Connect to test server
    arg_parser.add_argument(
        "-n",
        "--new_mode",
        action="store_true",
        default=False,
        dest="new_mode",
        help=str(
            "New mode: connect to the Embeetle test server to fetch "
            "projects."
        ),
    )

    # & Source analysis only
    arg_parser.add_argument(
        "-sao",
        "--source_analysis_only",
        action="store_true",
        default=False,
        dest="source_analysis_only",
        help="Run only the source analysis and check for errors.",
    )

    # & Testing output file
    arg_parser.add_argument(
        "-sarf",
        "--source_analysis_result_file",
        action="store",
        default=None,
        dest="source_analysis_result_file",
        help=str(
            "Select the output file where source analysis results will "
            "be written to."
        ),
    )

    # & Source analysis only diagnostic cap
    arg_parser.add_argument(
        "-sao-dc",
        "--source_analysis_only_diagnostic_cap",
        action="store",
        type=int,
        default=10000,
        dest="source_analysis_only_diagnostic_cap",
        help=str(
            "Select the diagnostic cap when running in source analysis "
            "only mode. Default is 10000."
        ),
    )

    # & Add a file group to the argument parser
    file_group = arg_parser.add_argument_group("input file options")

    # Nested function for input file parsing
    def parse_file_list(files_string):
        return files_string.split(";")

    # Input files
    file_group.add_argument(
        "-f",
        "--files",
        type=parse_file_list,
        help=str(
            f"List of files to open on startup, separated by semicolons "
            f"({q};{q}). This flag overrides the --new flag."
        ),
    )
    # Single file argument
    help_string = "Single file passed as an argument, "
    help_string += "Used for opening files with a desktops "
    help_string += '"Open with..." functionality'
    file_group.add_argument(
        "single_file",
        action="store",
        nargs="?",
        default=None,
        help=help_string,
    )

    # & Open project on startup
    arg_parser.add_argument(
        "-p",
        "--project",
        action="store",
        default=None,
        dest="open_project",
        help="Open an existing Embeetle project on startup.",
    )
    parsed_options = arg_parser.parse_args()
    return parsed_options


def get_embeetle_version(version_filepath: Optional[str] = None) -> str:
    """"""
    if version_filepath is None:
        version_filepath = unixify_path_join(
            data.beetle_core_directory, "version.txt"
        )
    text = ""
    version = "none"
    try:
        with open(version_filepath, "r", newline="\n") as f:
            text = f.read()
    except:
        print(
            f"WARNING: Could not extract version nr from {q}{version_filepath}{q}"
        )
        return "none"
    try:
        p = re.compile(r"\d+\.\d+\.\d+", re.MULTILINE)
        m = p.search(text)
        version = m.group(0)
    except:
        print(f"WARNING: Could not extract version nr from {version_filepath}")
        return "none"
    return version


def convert_to_bytes(numberStr: str) -> int:
    """Convert any string like '64K', '0x800', ...

    to the number of bytes it represents.
    """
    numberStr = numberStr.strip()
    numberStr = numberStr.lower()
    nr_bytes = 0
    if (
        numberStr.endswith("bytes")
        or numberStr.endswith("byte")
        or numberStr.endswith("b")
    ):
        numberStr = numberStr.replace("bytes", "")
        numberStr = numberStr.replace("byte", "")
        numberStr = numberStr.replace("b", "")
        numberStr = numberStr.strip()
        nr_bytes = int(numberStr)
        return nr_bytes
    if (
        numberStr.endswith("kbytes")
        or numberStr.endswith("kbyte")
        or numberStr.endswith("kb")
        or numberStr.endswith("k")
    ):
        numberStr = numberStr.replace("kbytes", "")
        numberStr = numberStr.replace("kbyte", "")
        numberStr = numberStr.replace("kb", "")
        numberStr = numberStr.replace("k", "")
        numberStr = numberStr.strip()
        nr_bytes = int(numberStr) * 1024
        return nr_bytes
    if (
        numberStr.endswith("mbytes")
        or numberStr.endswith("mbyte")
        or numberStr.endswith("mb")
        or numberStr.endswith("m")
    ):
        numberStr = numberStr.replace("mbytes", "")
        numberStr = numberStr.replace("mbyte", "")
        numberStr = numberStr.replace("mb", "")
        numberStr = numberStr.replace("m", "")
        numberStr = numberStr.strip()
        nr_bytes = int(numberStr) * 1048576
        return nr_bytes
    if numberStr.startswith("0x"):
        nr_bytes = int(numberStr, 16)
        return nr_bytes
    try:
        nr_bytes = int(numberStr)
        return nr_bytes
    except Exception as e:
        pass
    raise IOError(f"\nCannot convert {q}{numberStr}{q} into nr of bytes!\n")


def convert_to_hex(numberStr: str) -> str:
    """Convert any string like "64K", "0x800", "1024bytes", ...

    to the equivalent hexadecimal representation.
    """
    if numberStr.startswith("0x"):
        return numberStr
    bytes = convert_to_bytes(numberStr)
    return hex(bytes)


def test_write_permissions(dirpath: str, try_file: bool = True) -> bool:
    """Check if the given dirpath is writeable.

    If the 'try_file' parameter is set, this function will actually write a file
    to the path and delete it afterwards. This approach gives more certainty,
    but you risk to have a leftover temporary file if something goes wrong.
    """
    if not os.access(dirpath, os.W_OK):
        return False
    if try_file:
        tempfile = os.path.join(dirpath, "temp.txt").replace("\\", "/")
        while os.path.isfile(tempfile):
            tempfile = tempfile[0:-4]
            tempfile += "_.txt"
        assert not os.path.isfile(tempfile)
        try:
            with open(tempfile, "w+") as f:
                f.write("foo")
        except:
            if os.path.exists(tempfile):
                try:
                    os.remove(tempfile)
                except:
                    pass
            return False
        try:
            os.remove(tempfile)
        except:
            return False
    return True


def chmod_recursive(dirpath, mode=0o775) -> None:
    """"""
    for root, dirs, files in os.walk(dirpath):
        for d in dirs:
            os.chmod(os.path.join(root, d), mode)
        for f in files:
            os.chmod(os.path.join(root, f), mode)
    return


def index_iterator(starting_index=0):
    """"""
    index = starting_index
    while True:
        yield index
        index += 1


# ^                                          JSON FILES                                            ^#
# % ============================================================================================== %#
# % Functions to deal with json-files.                                                             %#
# %                                                                                                %#
def json_encode(input_data: Dict) -> str:
    """Convert the given dictionary into a json string."""
    return json.dumps(input_data, indent=2, ensure_ascii=False)


def load_json_file(filepath: str) -> Optional[Dict]:
    """Return a dictionary that represents the given json file.

    Return None if the given json file doesn't exist or is invalid.
    """
    json_dict: Optional[Dict] = None
    if (filepath is None) or (not os.path.isfile(filepath)):
        return None
    try:
        with open(
            filepath, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            json_dict = json.load(f)
    except:
        try:
            with open(
                filepath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                content = f.read()
            if content.strip() == "":
                # It's just an empty file
                return None
        except:
            pass
        printc(
            f"\nERROR: Cannot parse json file {q}{filepath}{q}\n",
            color="error",
        )
        traceback.print_exc()
        return None
    return json_dict


# This regex alternates between:
# 1) Double-quoted string  ("...") with escapes
# 2) Single-quoted string  ('...') with escapes (JSON5 allows single quotes)
# 3) Block comment         (/*...*/)
# 4) Line comment          (//...)
# 5) A fallback pattern    (everything else), so we don't miss any characters
# The idea:
#   - If we match a string (group 1 or 2), we keep it (because comment-like substrings inside strings must remain).
#   - If we match a comment (group 3 or 4), we remove it.
#   - If it's neither (group 5), we keep it as-is.
# Dot matches newlines because of DOTALL, enabling block comments to span lines.
comment_or_string_re = re.compile(
    r'("(?:(?:\\.)|[^"\\])*")'  # 1) double-quoted string
    r"|('(?:(?:\\.)|[^'\\])*')"  # 2) single-quoted string
    r"|(/\*[\s\S]*?\*/)"  # 3) block comment
    r"|(//[^\n]*)"  # 4) line comment
    r"|([^\"'/]+|.)",  # 5) fallback to capture everything else
    re.DOTALL,
)


def _strip_comment(m):
    """A function-based replacement for re.sub.

    If the match is a block comment (group 3) or a line comment (group 4),
    return '' to remove it. Otherwise return the matched text as-is.
    """
    # Groups 1 & 2 => string literals, group 5 => other text => keep
    # Groups 3 & 4 => comments => remove
    if m.group(3) or m.group(4):
        return ""  # remove comment
    else:
        return m.group(0)  # keep string or other text


def load_json_file_with_comments(file_path: str):
    """Loads a JSON/JSON5 file, removing // and /* ... */ comments while
    preserving string content.

    This function uses a single-pass regex to handle:
      - '...' and \"...\" string literals (retaining any // or /* inside them)
      - // single-line comments
      - /*...*/ multi-line comments

    Steps:
      1. Read the entire file at once into a string.
      2. Use a single regular expression to tokenize and remove comments:
         - Matches comments and strips them out.
         - Matches string literals and preserves them intact.
         - Matches any other characters and preserves them.
      3. Parse the cleaned JSON with Python's standard json.loads.

    Performance:
      - By relying on a single-pass regex and group-based substitutions, this
        approach avoids Python-level character-by-character iteration. It's
        typically fast and suitable for large files, though it still loads the
        entire file content into memory.

    Edge Cases:
      - Malformed JSON or comments (like unclosed quotes or unterminated block
        comments) may cause incorrect removals or parsing errors.
      - JSON5 allows more features (trailing commas, etc.) that are NOT handled
        here. Only the comment portion is removed. The rest must be valid JSON
        for `json.loads` to work.
      - Nested comments are not supported by JSON5 and are not handled here.
      - If the file contains extremely large strings or pathological patterns,
        regex performance might degrade.

    :param file_path: Path to the file containing JSON data with optional
                      comments.
    :return: A Python object (dict, list, etc.) from the parsed JSON.
    :raises json.JSONDecodeError: If the resulting string is not valid JSON.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove comments, keep strings and other data intact
    cleaned = comment_or_string_re.sub(_strip_comment, content)
    return json.loads(cleaned)


def write_json_file_with_comments(
    filepath: str, json_dict: Any, comment: str
) -> None:
    """Write the input data to the given file in json-format and add a comment
    at the top.
    """
    _comment = f"// {'\n// '.join(textwrap.wrap(comment, width=77))}\n"
    with open(
        filepath, "w+", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(_comment + json.dumps(json_dict, indent=2, ensure_ascii=False))
    return


def write_json_file(filepath: str, json_dict: Any) -> None:
    """Write the input data to the given file in json-format."""
    with open(
        filepath, "w+", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        f.write(json.dumps(json_dict, indent=2, ensure_ascii=False))
    return


def is_json_file(filepath: str) -> bool:
    """Check if the format is json5-compliant."""
    json_dict: Optional[Dict] = None
    try:
        with open(
            filepath, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            json_dict = json.loads(
                "\n".join(
                    line
                    for line in f
                    if not line.strip().startswith(("//", "#"))
                )
            )
    except:
        del json_dict
        return False
    del json_dict
    return True


# ^ ======================================[ END JSON FILES ]=========================================


def unixify_path(path: str) -> str:
    """"""
    result = os.path.realpath(path).replace("\\", "/")
    if os_checker.is_os("windows"):
        if result.startswith("/"):
            start = 0
            for i in range(len(result)):
                if result[i] == "/":
                    continue
                elif result[i] == "?":
                    continue
                else:
                    start = i
                    break
            result = result[start:]
    return result


def unixify_path_join(first_path: str, *paths) -> str:
    """"""
    merged_paths = "/".join(paths)
    joined_paths = os.path.join(first_path, merged_paths)
    return unixify_path(joined_paths)


def unixify_path_remove(absolute_path: str, path_to_remove: str) -> str:
    """"""
    absolute_path = unixify_path(absolute_path)
    path_to_remove = unixify_path(path_to_remove)
    if absolute_path.startswith(path_to_remove):
        result = os.path.relpath(absolute_path, path_to_remove).replace(
            "\\", "/"
        )
    else:
        result = absolute_path
    return result


def split_all_path_items(path):
    return path.replace("\\", "/").split("/")


def relativise_path(absolute_path, project_path, prepend_symbol):
    relative_path = unixify_path_remove(absolute_path, project_path)
    return "{}/{}".format(prepend_symbol, relative_path)


def get_file_extension(file_or_path):
    return os.path.splitext(file_or_path)[1]


def join_resources_dir_to_path(path):
    return unixify_path(os.path.join(str(data.resources_directory), path))


def join_application_dir_to_path(path):
    return unixify_path(os.path.join(str(data.beetle_core_directory), path))


def create_startup_file():
    user_directory = os.path.realpath(str(pathlib.Path.home()))
    embeetle_directory = os.path.join(user_directory, ".embeetle")
    if not os.path.isdir(embeetle_directory):
        os.mkdir(embeetle_directory)
    startup_file = os.path.join(embeetle_directory, "startup.btl")
    if os.path.isfile(startup_file):
        os.remove(startup_file)
    with open(startup_file, "w+") as f:
        f.write("Embeetle startup file for splash functionality")
        f.close()


def find_case_conflicts(names: Iterable) -> List[List[str]]:
    """Return the list of case conflicts for a given list of names. A case
    conflict is a list of names that are equal ignoring case.

    For example:
        find_case_conflicts([ 'Foo', 'foo', 'bar', 'foO', 'Wim', 'WIM' ])
    returns:
        [['Foo', 'foo', 'foO'], ['Wim', 'WIM']]
    """
    case_conflicts: List[List[str]] = []
    name_bins: Dict[str, List[str]] = {}
    for _name in names:
        _key = _name.lower()
        _bin = name_bins.get(_key, None)
        if _bin is None:
            name_bins[_key] = [_name]
            continue
        if len(_bin) == 1:
            case_conflicts.append(_bin)
        _bin.append(_name)
        continue
    return case_conflicts


def quote_portable_filename(name: str) -> str:
    """Quote a portable filename for use in a makefile. The quoting must not
    only take into account processing by make (which expands dollars) but also
    processing by one of a set of shells: the Bourne shell, the Bash shell or
    the Windows CMD shell.

    Precondition: is_valid_portable_filename(name)
    """
    assert is_valid_portable_filename(name)
    if _works_unquoted_in_any_shell(name):
        return name
    return '"' + name + '"'


def quote_linux_filename(name: str) -> str:
    """Quote a valid Linux filename for use in a makefile. The quoting must not
    only take into account processing by make (which expands dollars) but also
    processing by one of the supported shells on Linux (Bourne or Bash).

    Precondition: is_valid_linux_filename(name)
    """
    assert is_valid_linux_filename(name)
    raise NotImplementedError()  # TODO
    return name


def quote_windows_filename(name: str) -> str:
    """Quote a valid Windows filename for use in a makefile. The quoting must
    not only take into ac- count processing by make (which expands dollars) but
    also processing by one of the supported shells on Windows (CMD).

    Precondition: is_valid_windows_filename(name)
    """
    assert is_valid_windows_filename(name)
    raise NotImplementedError()  # TODO
    return name


def is_valid_portable_filename(name: str) -> bool:
    """Return true if the given file- or directory name is valid in an Embeetle
    source tree for any platform supported by Embeetle.

    Restrictions come not only from what the platforms allow, but also from what
    we can reliably quote in a makefile such that it will be accepted unchanged
    as a command line argument by any supported shell (Bource, Bash and CMD). If
    a valid portable name needs quoting, surrounding it by double quotes will
    suffice.
    """
    return re.search(_invalid_portable_name_regex, name) is None


def is_valid_portable_relpath(relpath: str) -> bool:
    """Apply the previous function on each part of a relpath."""
    if relpath == ".":
        return True
    if relpath.startswith("."):
        relpath = relpath[1:]
    relpath = relpath.strip("/")
    for name in relpath.split("/"):
        if not is_valid_portable_filename(name):
            return False
    return True


def get_invalid_chars(name: str) -> List[str]:
    """Extract and return the invalid characters from the given name.

    Return None if all characters are legal.
    """
    illegal_chars = set()
    for m in _invalid_portable_name_regex.finditer(name):
        illegal_chars.add(m.group(0))
    return list(illegal_chars)


def get_invalid_relpath_chars(relpath: str) -> List[str]:
    """Extract and return the invalid characters from the given relpath.

    Return None if all characters are legal.
    """
    illegal_chars = set()
    for name in relpath.split("/"):
        for m in _invalid_portable_name_regex.finditer(name):
            illegal_chars.add(m.group(0))
    return list(illegal_chars)


def is_valid_linux_filename(name: str) -> bool:
    """Return true if the given file- or directory name is valid in an Embeetle
    source tree for Linux or a Linux-like platform.

    Restrictions come not only from what Linux allows, but also from what we can
    reliably quote in a makefile.
    """
    return re.search(_invalid_linux_name_regex, name) is None


def is_valid_windows_filename(name: str) -> bool:
    """Return true if the given file- or directory name is valid in an Embeetle
    source tree for Windows or a Windows-like platform.

    Restrictions come not only from what Windows allows, but also from what we
    can reliably quote in a makefile.
    """
    return re.search(_invalid_windows_name_regex, name) is None


def _works_unquoted_in_any_shell(name: str) -> bool:
    """Return true if the given name can be used without quotes as a command
    line argument in any supported shell (Bourne, Bash and CMD)."""
    return re.search(_quotes_needed_regex, name) is None


def cut_list_in_pieces(my_list: List, piece_len: int) -> List[List]:
    """Cut the given list in pieces of 'piece_len' length each."""
    total_len = len(my_list)
    start_indexes = [i for i in range(0, total_len, piece_len)]
    end_indexes = start_indexes[1:]
    end_indexes.append(total_len + 1)
    indexes = list(zip(start_indexes, end_indexes))
    return [my_list[x:y] for x, y in indexes]


# Match names that need quoting with double quotes in at least one of
# the supported shells.
_quotes_needed_regex_string = r"[\[&|*?%^!$\\`<>]"
_quotes_needed_regex = re.compile(_quotes_needed_regex_string)

# Match invalid names for make. ASCII whitespace characters are not possible in
# target and prerequisite names because they split the name in two. Initial
# tilde expands to home directory and cannot be quoted. The characters *?[\ are
# only allowed if quoted with \ (backslash), otherwise they will cause filename
# expansion (shell globbing),  and we did not implement quoting for make yet.
_invalid_make_name_regex_string = r"[ \t\n\v\f\r*?\[\\]|^~$"
_invalid_make_name_regex = re.compile(_invalid_make_name_regex_string)

# Match invalid names for Linux. Linux allows almost anything, except for the
# empty string, / and the null character \0. The names . and .. have a special
# meaning.
_invalid_linux_name_regex_string = (
    r"/|^(|\.\.?)$" "|" + _invalid_make_name_regex_string
)
_invalid_linux_name_regex = re.compile(_invalid_linux_name_regex_string)

# Match invalid names for Windows. Windows disallows everything that Linux
# disallows, all control characters, the characters :\*?"<> , a trailing space
# or dot, and a list of special function names. We also disallow % (percent)
# because we have no simple and reliable way to quote it (for example, "%path%"
# expands the PATH environment variable).
# More information about valid Windows file names can be found at
# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
_invalid_windows_name_regex_string = (
    r'[:\\/*?"<>\000-\031 %]|[ .]$'
    r"|^(|\.\.?|(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.[^.]*)?)$"
    "|" + _invalid_make_name_regex_string
)
_invalid_windows_name_regex = re.compile(
    _invalid_windows_name_regex_string, re.IGNORECASE
)

# Match names that are not portable, i.e. are invalid for at least one platform
# and can be used as command line argument when quoted with double quotes.
# Portable names must be valid in Windows and in Linux and cannot contain $
# (dollar), ! (exclamation mark) or ` (backquote), because we have no portable
# way to quote them.
# We cannot use single-quoted strings like 'string', because CMD does not strip
# the single quotes.
# On Linux, we can use unquoted words with \ (backslash) in front of special
# characters, but Windows CMD does not interpret backslashes as escapes.
# In CMD, "$a" returns "$a" but on Linux, it expands the variable "a".  On
# linux, "\$a" works and removes the backslash, but in CMD, the backslash is not
# removed. Similarly for ! (exclamation mark) which expands history on Linux,
# and ` (backquote) which invokes command substitution.
_invalid_portable_name_regex_string = (
    _invalid_linux_name_regex_string
    + "|"
    + _invalid_windows_name_regex_string
    + r"|[$!`%]"
)
_invalid_portable_name_regex = re.compile(
    _invalid_portable_name_regex_string, re.IGNORECASE
)


def is_ascii_only_and_safe(path):
    """Check if the provided path is ASCII-only and safe for use with tools like
    GNU Make and GCC on both Windows and Linux by avoiding special characters
    and path length issues.

    Args:
        path (str): The path to check.

    Returns:
        str: "safe" if the path is ASCII-only and safe, otherwise a description of what is wrong.
    """

    def flatten_matches(matches):
        """Flatten a list of regex matches by joining any tuples into strings.

        Args:
            matches (list): List of regex matches, which may contain tuples.

        Returns:
            list: A list where all items are non-empty strings.
        """
        flattened = [
            "".join(tup) if isinstance(tup, tuple) else tup for tup in matches
        ]
        # Filter out empty strings resulting from empty matches
        return [match for match in flattened if match]

    # Initialize lists for each issue type
    quotes_needed_issues = flatten_matches(_quotes_needed_regex.findall(path))
    make_issues = flatten_matches(_invalid_make_name_regex.findall(path))
    linux_issues = flatten_matches(_invalid_linux_name_regex.findall(path))
    windows_issues = flatten_matches(_invalid_windows_name_regex.findall(path))
    portable_issues = flatten_matches(
        _invalid_portable_name_regex.findall(path)
    )

    # Check for non-ASCII characters
    non_ascii_chars = [char for char in path if ord(char) > 127]
    if non_ascii_chars:
        non_ascii_issue = (
            f"Path contains non-ASCII characters: {''.join(non_ascii_chars)}"
        )
    else:
        non_ascii_issue = None

    # If on Windows, remove space character from all issue lists
    if os_checker.is_os("windows"):
        quotes_needed_issues = [ch for ch in quotes_needed_issues if ch != " "]
        make_issues = [ch for ch in make_issues if ch != " "]
        linux_issues = [ch for ch in linux_issues if ch != " "]
        windows_issues = [ch for ch in windows_issues if ch != " "]
        portable_issues = [ch for ch in portable_issues if ch != " "]

    # Collect issues for reporting
    issues = []

    if quotes_needed_issues:
        issues.append(
            f"Path contains characters that need quoting in shells: {''.join(quotes_needed_issues)}"
        )
    if make_issues:
        issues.append(
            f"Path contains invalid characters for Make: {''.join(make_issues)}"
        )
    if linux_issues:
        issues.append(
            f"Path contains invalid characters for Linux: {''.join(linux_issues)}"
        )
    if windows_issues:
        issues.append(
            f"Path contains invalid characters for Windows: {''.join(windows_issues)}"
        )
    if portable_issues:
        issues.append(
            f"Path contains characters that are not portable: {''.join(portable_issues)}"
        )
    if non_ascii_issue:
        issues.append(non_ascii_issue)

    # Check if the path length exceeds typical limits
    if len(path) > 260:
        issues.append(
            "Path exceeds 260 characters, which may not be supported on all systems"
        )

    # If all lists are empty and no other issues are found, return "safe"
    if (
        not any(
            [
                quotes_needed_issues,
                make_issues,
                linux_issues,
                windows_issues,
                portable_issues,
                non_ascii_chars,
            ]
        )
        and not issues
    ):
        return "safe"

    # Return the detailed issues as a single string
    return "\n".join(issues)


if __name__ == "__main__":
    # Self-test

    # Some names that are portable when surrounded by double-quotes.
    _portable_names_quoted = ["&", "a&b", "||", "^^.cpp"]

    # Some names that are portable without quotes.
    _portable_names_unquoted = [
        "foo",
        "foo.c",
        "with_1_underscore.h",
        "45",
        "CON2",
        "2con",
        "€",
        ".init",
    ]

    # Some portable names requiring quotes or not.
    _portable_names = _portable_names_quoted + _portable_names_unquoted

    # Some valid names on Linux only.
    _linux_only_names = [
        "CON",
        "prn",
        ":a",
        '"',
        "<",
        "a>",
        "...",
        "com5",
        "Lpt8",
        "\005",
        "\a",
        "\b",
        "%path%",
        "x.",
        "nul.txt",
    ]

    # There are no names that are valid on Windows only.

    # Some names valid on both Linux and Windows that cannot be quoted in the
    # same way for both platforms.
    _non_portable_names = ["a$b", "$$", "!", "`"]

    # Some invalid names for both Windows and Linux
    _invalid_names = [
        "/foo",
        "",
        ".",
        "..",
        "a b",
        "tab\ttab",
        "\v",
        "\n",
        "\f",
        "\r",
        " space",
        "xx ",
        "a b",
        "[aha]",
        "\\",
        "\\foo",
        "*",
        "?",
        "yes?",
    ]

    for name in _portable_names:
        print(f"check {repr(name)} portable")
        assert is_valid_linux_filename(name)
        assert is_valid_windows_filename(name)
        assert is_valid_portable_filename(name)
    for name in _linux_only_names:
        print(f"check {repr(name)} linux-only")
        assert is_valid_linux_filename(name)
        assert not is_valid_portable_filename(name)
    for name in _non_portable_names:
        print(f"check {repr(name)} non-portable")
        assert is_valid_linux_filename(name)
        assert is_valid_windows_filename(name)
        assert not is_valid_portable_filename(name)
    for name in _invalid_names:
        print(f"check {repr(name)} illegal")
        assert not is_valid_portable_filename(name)
        assert not is_valid_linux_filename(name)
        assert not is_valid_windows_filename(name)
    for name in _portable_names_quoted:
        print(f"check {repr(name)} quoted")
        assert quote_portable_filename(name) == '"' + name + '"'
    for name in _portable_names_unquoted:
        print(f"check {repr(name)} unquoted")
        assert quote_portable_filename(name) == name

    conflicts = find_case_conflicts(["Foo", "foo", "bar", "foO", "Wim", "WIM"])
    print(repr(conflicts))
    assert conflicts == [["Foo", "foo", "foO"], ["Wim", "WIM"]]


# ^                                          SUBPROCESS                                            ^#
# % ============================================================================================== %#
# % Functions to launch subprocesses.                                                              %#
# %                                                                                                %#
def subprocess_popen(*args, **kwargs) -> subprocess.Popen:
    """This wrapper around subprocess.Popen() avoids the dreaded Windows empty
    console popping up."""
    # & Make sure 'startupinfo' is not yet defined in kwargs
    if kwargs is not None:
        assert "startupinfo" not in kwargs
    else:
        kwargs = {}

    # & Create the 'startupinfo' parameter
    startupinfo = None
    if os_checker.is_os("windows"):
        # approach 1:
        # -----------
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # approach 2:
        # -----------
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    kwargs["startupinfo"] = startupinfo

    # & Print command
    if ("verbose" in kwargs) and kwargs["verbose"]:
        printfunc = printc
        if "printfunc" in kwargs:
            printfunc = kwargs["printfunc"]
        try:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                printfunc(shlex.join(args[0]), color="cyan", bright=True)
            else:
                printfunc(args[0], color="cyan", bright=True)
        except:
            pass
    if "verbose" in kwargs:
        del kwargs["verbose"]
    if "printfunc" in kwargs:
        del kwargs["printfunc"]

    # & Invoke the subprocess.Popen() call
    return subprocess.Popen(
        *args,
        **kwargs,
    )


def launch_subprocess_with_printout(*args, **kwargs) -> Tuple[int, str, str]:
    """Launch a subprocess, print its output and error streams in real-time and
    return them in the end as well.

    PARAMETERS
    ==========
    Pass the parameters you would normally pass to subprocess.Popen(), for example:

        ```
        launch_subprocess_with_printout(
            ['C:/foo.exe', '--p1', '--p2'],
            shell = False,
            env   = purefunctions.get_modified_environment([data.sys_lib, data.sys_bin]),
        )
        ```

    This function will add the 'stdout', 'stderr' and 'text' parameters to that, because they're
    necessary for the correct functioning:

        ```
        launch_subprocess_with_printout(
            ['C:/foo.exe', '--p1', '--p2'],
            shell  = False,
            env    = purefunctions.get_modified_environment([data.sys_lib, data.sys_bin]),
       -->  stdout = subprocess.PIPE,
       -->  stderr = subprocess.PIPE,
       -->  text   = True,
        )
        ```

    PRINT PARAMETERS
    ================
    To print the output in real-time, add the 'printfunc' parameter and set 'verbose' to True. This
    has a double effect:
      - The command gets printed.
      - The output and error streams get printed in real-time.
    The 'printfunc' parameter will default to 'printc' if you don't assign it.

    Example:

        ```
        launch_subprocess_with_printout(
            ['C:/foo.exe', '--p1', '--p2'],
            shell       = False,
            env         = purefunctions.get_modified_environment([data.sys_lib, data.sys_bin]),
            stdout      = subprocess.PIPE,
            stderr      = subprocess.PIPE,
            text        = True,
       -->  verbose     = True,
       -->  replace_bsl = True,
       -->  printfunc   = functions.importer_printfunc,
        )
        ```

    OUTPUT
    ======
    This function returns the returncode, output and error strings:
        (process.returncode, output_str, err_str)
    """
    # & Modify kwargs
    # Make sure there is a kwargs dictionary
    if kwargs is None:
        kwargs: Dict[str, Any] = {}
    # Pass the 'text=True' parameter to indicate that you want to work with the standard input,
    # standard output and standard error of the subprocess in text mode, rather than binary mode.
    # Also make sure the stdout and stderr streams are pipes.
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE
    kwargs["text"] = True

    # & Define printfunc and verbosity
    # Look for the parameters 'printfunc' and 'verbose' in the given kwargs. Store them for later
    # use.
    verbose: bool = kwargs.get("verbose", False)
    replace_bsl: bool = kwargs.get("replace_bsl", False)
    printfunc: Callable = kwargs.get("printfunc", printc)
    if "replace_bsl" in kwargs:
        del kwargs["replace_bsl"]

    def capture_output(pipe: IO[str], store: List[str], color: str) -> None:
        # Read from a pipe (either stdout or stderr) and store the lines in a provided list, mean-
        # while print them also in real-time.
        for line in iter(pipe.readline, ""):
            line = line.replace("\r\n", "\n").replace("\r", "\n")
            if replace_bsl:
                line = line.replace("\\", "/").replace("//", "/")
            if verbose:
                printfunc(line, color=color, end="")
            store.append(line)
        return

    # & Prepare lists to store the output and error streams
    output: List[str] = []
    errors: List[str] = []

    # & Launch the process
    # The 'verbose' and 'printfunc' parameters travel along to this function call and will cause the
    # command to be printed out (or not).
    process: subprocess.Popen = subprocess_popen(*args, **kwargs)

    # & Create threads to capture stdout and stderr
    stdout_thread: threading.Thread = threading.Thread(
        target=capture_output,
        args=(process.stdout, output, "default"),
    )
    stderr_thread: threading.Thread = threading.Thread(
        target=capture_output,
        args=(process.stderr, errors, "error"),
    )

    # & Start the threads
    stdout_thread.start()
    stderr_thread.start()

    # & Wait for the process to complete and the threads to finish
    process.wait()
    stdout_thread.join()
    stderr_thread.join()

    # & Convert lists to strings
    output_str: str = "".join(output)
    errors_str: str = "".join(errors)

    # & Return returncode and output and error streams (as strings)
    return process.returncode, output_str, errors_str


def subprocess_popen_sync(*args, **kwargs):
    """For use with the source analyzer."""
    new_subprocess = subprocess_popen(*args, **kwargs)
    try:
        outs, errs = new_subprocess.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        new_subprocess.kill()
        outs, errs = new_subprocess.communicate()
    retcode = new_subprocess.poll()
    args = new_subprocess.args
    return subprocess.CompletedProcess(args, retcode, outs, errs)


def subprocess_popen_without_startup_info(*args, **kwargs) -> subprocess.Popen:
    """This wrapper around subprocess.Popen() doesn't add the 'startupinfo'
    parameter."""
    # & Make sure 'startupinfo' is not defined in kwargs.
    if kwargs is not None:
        assert "startupinfo" not in kwargs
    else:
        kwargs = {}

    # & Invoke the subprocess.Popen() call.
    return subprocess.Popen(
        *args,
        **kwargs,
    )


def get_css_tags() -> Dict[str, str]:
    """Get css tags for dialogs."""
    if data.theme["is_dark"]:
        return get_dark_css_tags()
    fps = data.get_general_font_pointsize()
    return {
        "h1": (
            f'<p align="center"><span style="color:#2e3436; font-size:{fps+4}pt; font-weight:bold;">'
        ),
        "h2": (
            f'<p align="left"><span style="color:#3e7b05; font-size:{fps}pt; font-weight:bold;">'
        ),
        "h3": (
            f'<p align="center"><span style="color:#a40000; font-size:{fps+2}pt; font-weight:bold;">'
        ),
        "/hx": "</span></p>",
        "tab": "&nbsp;&nbsp;&nbsp;&nbsp;",
        "red": '<span style="color:#cc0000">',
        "green": '<span style="color:#4e9a06">',
        "blue": '<span style="color:#204a87">',
        "orange": '<span style="color:#ce5c00">',
        "grey": '<span style="color:#555753">',
        "gray": '<span style="color:#555753">',
        "yellow": '<span style="color:#c4a000">',
        "purple": '<span style="color:#5c3566">',
        "end": "</span>",
        "p_code": (
            '<p align="left" style="background-color:#fef8c6; margin-top:10px; margin-bottom:10px; margin-right:3em; margin-left:2em;">'
        ),
    }


def get_dark_css_tags() -> Dict[str, str]:
    """Get css tags for dark stuff (eg.

    console)
    """
    fps = data.get_general_font_pointsize()
    return {
        "h1": (
            f'<p align="center"><span style="color:#ffffff; font-size:{fps+4}pt; font-weight:bold;">'
        ),
        "h2": (
            f'<p align="left"><span style="color:#a1e85b; font-size:{fps}pt; font-weight:bold;">'
        ),
        "h3": (
            f'<p align="center"><span style="color:#ef2929; font-size:{fps+2}pt; font-weight:bold;">'
        ),
        "/hx": "</span></p>",
        "tab": "&nbsp;&nbsp;&nbsp;&nbsp;",
        "red": '<span style="color:#ef2929">',
        "green": '<span style="color:#a1e85b">',
        "blue": '<span style="color:#8fb3d9">',
        "orange": '<span style="color:#ff9946">',
        "grey": '<span style="color:#555753">',
        "gray": '<span style="color:#555753">',
        "yellow": '<span style="color:#fce94f">',
        "purple": '<span style="color:#c5a4c1">',
        "end": "</span>",
        "p_code": (
            '<p align="left" style="background-color:#fef8c6; margin-top:10px; margin-bottom:10px; margin-right:3em; margin-left:2em;">'
        ),
    }


def strip_rootid(prefixed_relpath: str) -> Tuple[str, str]:
    """Take a prefixed relpath, like '<project>/foo/foobar.c' and split it into
    the prefix '<project>' and relpath 'foo/foobar.c'.

    Then return them in a tuple.
    """
    p = re.compile(r"<<(.*)>>")
    rootid: Optional[str] = None
    remainder: Optional[str] = None
    if not prefixed_relpath.startswith("<"):
        raise RuntimeError(f"ERROR: strip_rootdir({prefixed_relpath})")
    if prefixed_relpath.startswith("<project>"):
        rootid = "<project>"
    else:
        if not prefixed_relpath.startswith("<<"):
            raise RuntimeError(f"ERROR: strip_rootdir({prefixed_relpath})")
        m = p.match(prefixed_relpath)
        rootid = m.group(0)
    remainder = prefixed_relpath.replace(rootid, "", 1)
    if remainder.startswith("/"):
        remainder = remainder[1:]
    return rootid, remainder


# ^                                            HASHING                                             ^#
# % ============================================================================================== %#
# % Functions to hash files and folders.                                                           %#
# % Source: https://stackoverflow.com/questions/24937495                                           %#


def md5_update_from_file(
    filename: Union[str, pathlib.Path], _hash: Hash
) -> Hash:
    assert pathlib.Path(filename).is_file()
    with open(str(filename), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            _hash.update(chunk)
    return _hash


def md5_file(filename: Union[str, pathlib.Path]) -> str:
    return str(md5_update_from_file(filename, hashlib.md5()).hexdigest())


def md5_update_from_dir(
    directory: Union[str, pathlib.Path], _hash: Hash
) -> Hash:
    assert pathlib.Path(directory).is_dir()
    for path in sorted(
        pathlib.Path(directory).iterdir(), key=lambda p: str(p).lower()
    ):
        _hash.update(path.name.encode())
        if path.is_file():
            _hash = md5_update_from_file(path, _hash)
        elif path.is_dir():
            _hash = md5_update_from_dir(path, _hash)
    return _hash


def md5_dir(directory: Union[str, pathlib.Path]) -> str:
    return str(md5_update_from_dir(directory, hashlib.md5()).hexdigest())


PERFORMANCE_MEASURING_FLAG: bool = False
performance_timer_starting_count: float = 0.0
performance_timer_last_point: float = 0.0


def performance_timer_start() -> None:
    """"""
    if not PERFORMANCE_MEASURING_FLAG:
        return
    global performance_timer_starting_count
    global performance_timer_last_point
    performance_timer_starting_count = time.perf_counter()
    performance_timer_last_point = performance_timer_starting_count
    return


def performance_timer_show(text: Optional[str] = None) -> None:
    """"""
    if not PERFORMANCE_MEASURING_FLAG:
        return
    global performance_timer_last_point
    info_text = "PERFORMANCE-TIMER"
    try:
        if text:
            info_text = text
        current_point = time.perf_counter()
        end_count = current_point - performance_timer_starting_count
        diff_count = current_point - performance_timer_last_point
        performance_timer_last_point = current_point
        print(
            f"Time: {end_count:.4f}s / diff: {diff_count:.4f} -> [{info_text}]"
        )
    except:
        print(f"[{info_text}] Error!")
    return


module_dictionary = {}


def import_module(module_name: str) -> object:
    """"""
    # performance_timer_start()
    global module_dictionary
    if module_name not in module_dictionary:
        module = importlib.import_module(module_name)
        module_dictionary[module_name] = module
    #        print(f"Imported module: {module_name}")
    else:
        module = module_dictionary[module_name]
    # performance_timer_show(module_name)
    return module


# ^                                       OUTPUT REDIRECTION                                       ^#
# % ============================================================================================== %#
# %                                                                                                %#

original_output_stream: Optional[TextIO] = None
original_error_stream: Optional[TextIO] = None
original_except_hook: Optional[Callable] = None


def redirect_output(project_path: Optional[str]) -> None:
    """Redirect 'sys.stdout' and 'sys.stderr' to a file.

    For the PROJECT WINDOW, the file is created at
    '<project>/.beetle/output.txt'. For the HOME WINDOW, the file is created at
    '~/.embeetle/home_ window_output.txt'.
    """
    # Store original values
    global original_output_stream
    original_output_stream = sys.stdout
    global original_error_stream
    original_error_stream = sys.stderr
    global original_except_hook
    original_except_hook = sys.excepthook

    # Output file
    output_file: Optional[str] = None

    # & PROJECT WINDOW
    if project_path is not None:
        dotbeetle_path = unixify_path_join(project_path, ".beetle")
        if not os.path.isdir(dotbeetle_path):
            os.makedirs(dotbeetle_path)
        output_file = unixify_path_join(project_path, ".beetle/output.txt")

    # & HOME WINDOW
    else:
        # Home window
        if not os.path.isdir(data.settings_directory):
            os.makedirs(data.settings_directory)
        output_file = unixify_path_join(
            data.settings_directory,
            "home_window_output.txt",
        )

    # Open file and redirect output
    f = open(
        output_file, "w+", encoding="utf-8", newline="\n", errors="replace"
    )
    sys.stdout = f
    sys.stderr = f

    # Adapt exception hook for all threads
    def exception_hook(exctype, value, trace) -> None:
        print("-" * 80)
        print(
            "".join(traceback.format_exception(exctype, value, trace)),
            end="",
        )
        print("-" * 80)
        qt.QApplication.quit()
        f.close()
        # Rename and save output file
        sf = os.path.split(output_file)
        output_file_with_date = os.path.join(
            sf[0],
            sf[1].replace(
                ".txt", datetime.datetime.now().strftime(".%Y%m%d_%H%M%S.txt")
            ),
        )
        shutil.copy(output_file, output_file_with_date)
        return

    sys.excepthook = exception_hook
    init_original: Callable = threading.Thread.__init__

    def init(self, *args, **kwargs) -> None:
        init_original(self, *args, **kwargs)
        run_original = self.run

        def run_with_except_hook(*args2, **kwargs2):
            try:
                run_original(*args2, **kwargs2)
            except Exception:
                sys.excepthook(*sys.exc_info())

        self.run = run_with_except_hook
        return

    threading.Thread.__init__ = init  # type: ignore
    return


def reset_output() -> None:
    """Reset the 'sys.stdout' and 'sys.stderr' streams."""
    if original_output_stream is not None:
        sys.stdout = original_output_stream
    if original_error_stream is not None:
        sys.stderr = original_error_stream
    if original_except_hook is not None:
        sys.excepthook = original_except_hook
    return


def init_colorama() -> None:
    """Initialize colorama.

    The older 'colorama.init()' function is deprecated. Use the newer function
    'colorama.just_fix_windows_console()' instead. It can be invoked multiple
    times. I also noticed that, after using rsync, the function
    os.system('color') must be invoked to re- enable colors!
    """
    if os_checker.is_os("windows"):
        assert not data.redirecting_output
        colorama.just_fix_windows_console()  # noqa
        os.system("color")
    return


def printc(
    *args,
    color: Optional[str] = None,
    bright: bool = False,
    **kwargs,
) -> None:
    """Print the given text in the requested color. This function simply
    overrides the builtin print() function and adds characters to give the text
    a color in the terminal.

    The first four parameters are equal to those from the builtin print() function:

        :param args:    Text to print. Normally this is a string, but it can actually be anything
                        that can be converted into a string. It can be several values as well which
                        will then be concatenated by the 'sep' parameter.

        :param kwargs:  The keyword parameters from the builtin print() function:
                        > sep:     String inserted between values, defaults to a space.
                        > end:     String appended after the last value, defaults to a newline.
                        > file:    A file-like object (stream); defaults to the current sys.stdout.
                        > flush:   Forcibly flush the stream.

        :param color:   Pass a color for the text. Choose one of these:
                            - None (default color)
                            - 'default'
                            - 'black'
                            - 'red'
                            - 'green'
                            - 'yellow'
                            - 'blue'
                            - 'magenta'
                            - 'cyan'
                            - 'white'
                        Or pass a description for the 'kind-of-text':
                            - 'info'    (will be printed as white text)
                            - 'warning' (will be printed as bright yellow text)
                            - 'error'   (will be printed as bright red text)
                            - 'sa'      (SA output, will be printed as cyan text)

        :param bright:  Make the color look brighter. This parameter only has effect if you passed
                        an actual color in the previous parameter.

    IMPORTANT:
    Although you can pass specific colors for the 'color' parameter, I believe it's best to pass the
    'kind-of-text' descriptions instead, such as 'info, 'warning', 'error', ... This way we have a
    single point in our codebase to modify the colors of all warnings, errors, etc if ever needed.
    """
    if (
        data.redirecting_output
        or (color is None)
        or (color.lower() == "default")
    ):
        print(*args, **kwargs)
        return

    # & Define colors
    color = color.lower()
    color_codes = {
        "default": "",
        "black": "\u001b[30m",
        "red": "\u001b[31m",
        "green": "\u001b[32m",
        "yellow": "\u001b[33m",
        "blue": "\u001b[34m",
        "magenta": "\u001b[35m",
        "cyan": "\u001b[36m",
        "white": "\u001b[37m",
        "default_bright": "",
        "black_bright": "\u001b[30;1m",
        "red_bright": "\u001b[31;1m",
        "green_bright": "\u001b[32;1m",
        "yellow_bright": "\u001b[33;1m",
        "blue_bright": "\u001b[34;1m",
        "magenta_bright": "\u001b[35;1m",
        "cyan_bright": "\u001b[36;1m",
        "white_bright": "\u001b[37;1m",
        "reset": "\u001b[0m",
    }

    # & Assign colors to 'kind-of-text' descriptions
    # If the given 'color' parameter is not an actual color but rather a 'kind-of-text' description
    # such as 'warning', 'error', ... then the code below will transform that into an actual color
    # and set the 'bright' parameter accordingly.
    if color not in color_codes.keys():
        if color == "info":
            color = "blue"
            bright = True
        elif color == "warning":
            color = "yellow"
            bright = True
        elif color == "error":
            color = "red"
            bright = True
        elif color == "sa":
            color = "cyan"
            bright = False
        else:
            print(
                f'{color_codes["red_bright"]}\n'
                f"ERROR: Illegal color parameter to printc():\n"
                f"    printc("
                f"        ...,\n"
                f"        color  = {color},\n"
                f"        bright = {bright},\n"
                f"    )\n"
                f'{color_codes["reset"]}',
                **kwargs,
            )
            color = "default"
            bright = False
    # At this point, the 'color' parameter must be an actual color.
    assert color in color_codes.keys()

    # & Print
    if bright:
        color = f"{color}_bright"
    sep = kwargs.get("sep", " ")
    print(
        f'{color_codes[color]}{sep.join(args)}{color_codes["reset"]}',
        **kwargs,
    )
    return


def sort_versions_high_to_low(versionlist: List[str]) -> List[str]:
    """Using the 'packaging' module, sort the version nrs from high-to-low."""
    try:
        sorted_list = sorted(
            versionlist,
            key=packaging.version.parse,
            reverse=True,
        )
    except:
        printc(
            f"\nWARNING: packaging.version.parse cannot handle this list: {versionlist}\n",
            color="warning",
        )
        return versionlist
    return sorted_list


def is_more_recent_than(v1: str, v2: str) -> bool:
    """V1 > v2  => return True."""
    try:
        is_more_recent = packaging.version.parse(v1) > packaging.version.parse(
            v2
        )
    except:
        printc(
            f"\nWARNING: purefunctions.is_more_recent_than({q}{v1}{q}, {q}{v2}{q}) failed!",
            color="warning",
        )
        return False
    return is_more_recent


def get_modified_environment(path_list: Optional[List[str]]) -> Dict:
    """Add the entries from 'path_list' to 'os.environ' in its 'PATH' and
    'LD_LIBRARY_PATH' elements."""
    my_env = copy.deepcopy(dict(os.environ))
    if path_list is not None:
        for newpath in path_list:
            newpath = (
                newpath.replace("/", os.sep)
                .replace("\\", os.sep)
                .replace("'", "")
                .replace('"', "")
                .strip()
            )
            if my_env.get("PATH") is not None:
                my_env["PATH"] = newpath + os.pathsep + my_env["PATH"]
            else:
                my_env["PATH"] = newpath
            if my_env.get("LD_LIBRARY_PATH") is not None:
                my_env["LD_LIBRARY_PATH"] = (
                    newpath + os.pathsep + my_env["PATH"]
                )
            else:
                my_env["LD_LIBRARY_PATH"] = newpath
            continue
    return my_env


def standardize_abspath(abspath: Optional[str]) -> Optional[str]:
    """
    :param   abspath: Non-standardized abspath
    :return: abspath: Standardized abspath (all rules above applied)
    """
    if (abspath is None) or (abspath.lower() == "none"):
        return None
    abspath = os.path.realpath(abspath).replace("\\", "/")
    if not os.path.isabs(abspath):
        abspath = os.path.realpath(os.path.abspath(abspath)).replace("\\", "/")
    if abspath.endswith("/"):
        abspath = abspath[0:-1]
    return abspath.replace("//", "/")


def list_filepaths(dirpath: str) -> List[str]:
    """List all files from the given directory.

    Contrary to os.listdir(), this function lists the absolute paths.
    """
    dirpath = standardize_abspath(dirpath)
    assert os.path.isdir(dirpath)
    filepaths = []
    for fname in sorted(os.listdir(dirpath)):
        f = (
            os.path.realpath(os.path.join(dirpath, fname))
            .replace("\\", "/")
            .replace("//", "/")
        )
        if not os.path.isfile(f):
            continue
        filepaths.append(f)
    return filepaths


# ^                                       SPAWN NEW TERMINAL                                       ^#
# % ============================================================================================== %#
# % WARNING: DUPLICATED IN BEETLE_PROJECT_GENERATOR!                                               %#
# %                                                                                                %#
linux_shells = (
    "sh",
    "bash",
    "dash",
    "zsh",
    "ksh",
    "fish",
    "xonsh",
    "nushell",
)
linux_terminal_emulators = (
    "gnome-terminal",
    "x-terminal-emulator",
    "xterm",
    "konsole",
    "xfce4-terminal",
    "qterminal",
    "lxterminal",
    "alacritty",
    "rxvt",
    "terminator",
    "termit",
)


def spawn_new_terminal(
    script_or_exe_path: str, argv: List[str], **kwargs
) -> Callable:
    """Spawn a new terminal and launch the given script (python or shell script)
    or executable in that terminal. This function returns a callable
    'wait_function()' that the parent process (which invoked this function) can
    use to wait for the child process (which runs in the newly spawned terminal)
    to complete. That 'wait_function()' returns the 'returncode', which is 0 if
    all was good.

    :param script_or_exe_path:  The script (python or shell script) or executable to be launched in
                                the newly spawned terminal. For example:
                                  - 'C:/users/krist/child.py'  or '/home/krist/child.py'
                                  - 'C:/users/krist/child.bat' or '/home/krist/child.sh'
                                  - 'C:/users/krist/child.exe' or '/home/krist/child'

    :param argv:                The arguments to be passed to the script or executable. Do not
                                include the (path to the) script file or executable in here. Just
                                the arguments.
    """
    if "verbose" in kwargs:
        del kwargs["verbose"]
    # & WINDOWS
    if os_checker.is_os("windows"):
        # $ shell script
        if script_or_exe_path.endswith((".cmd", ".bat")):
            return __spawn_terminal_windows(script_or_exe_path, argv, **kwargs)
        # $ python script
        if script_or_exe_path.endswith(".py"):
            return __spawn_terminal_windows(
                __get_python_executable(), [script_or_exe_path, *argv], **kwargs
            )
        # $ executable
        if script_or_exe_path.endswith(".exe"):
            return __spawn_terminal_windows(script_or_exe_path, argv, **kwargs)
        # Reaching this point, the file has no known extension. The file is probably an executable.
        return __spawn_terminal_windows(script_or_exe_path, argv, **kwargs)

    # & LINUX
    # $ shell script
    if script_or_exe_path.endswith(".sh"):
        return __spawn_terminal_linux(script_or_exe_path, argv, **kwargs)
    # $ python script
    if script_or_exe_path.endswith(".py"):
        return __spawn_terminal_linux(
            __get_python_executable(), [script_or_exe_path, *argv], **kwargs
        )
    # $ executable
    if script_or_exe_path.endswith(".exe"):
        # Normally, executables on Linux don't end in '.exe'. But you never know.
        return __spawn_terminal_linux(script_or_exe_path, argv, **kwargs)
    # Try to find shebang
    try:
        with open(script_or_exe_path, "r", encoding="utf-8", newline="\n") as f:
            content = f.read()
        # Look for a shebang with a for-loop, to ignore empty lines at the start of the file. If
        # a non-empty line is found, and it is not a shebang, then stop looping.
        for line in content.splitlines():
            if line.strip() == "":
                continue
            # $ shell script
            if line.startswith(tuple(f"#!/bin/{s}" for s in linux_shells)):
                return __spawn_terminal_linux(
                    script_or_exe_path, argv, **kwargs
                )
            if line.startswith(tuple(f"#!/usr/bin/{s}" for s in linux_shells)):
                return __spawn_terminal_linux(
                    script_or_exe_path, argv, **kwargs
                )
            break
        # No shebang found
    except:
        # The file is probably not a script, but an executable
        pass
    # $ executable
    # Reaching this point, the file has no known extension, nor could a shebang be found. The
    # file is probably an executable.
    return __spawn_terminal_linux(script_or_exe_path, argv, **kwargs)


def __get_python_executable() -> str:
    """Return the path to the python interpreter executable."""
    interpreter_path: Optional[str] = None
    if getattr(sys, "frozen", False):
        # Frozen, running as compiled code
        if os_checker.is_os("linux"):
            # On Linux, first give 'python3' a try
            interpreter_path = shutil.which("python3")
        if interpreter_path is None:
            interpreter_path = shutil.which("python")
    else:
        # Running from interpreter
        interpreter_path = sys.executable
    assert interpreter_path is not None
    return interpreter_path.replace("\\", "/")


def __get_terminal_emulator_name_and_executable() -> Tuple[str, str]:
    """Return the name and path to the default terminal emulator on this system.

    For example:
    ('gnome-terminal', '/usr/bin/gnome-terminal')
    """
    assert os_checker.is_os("linux")
    for terminal in linux_terminal_emulators:
        if shutil.which(terminal):
            return str(terminal), str(shutil.which(terminal))
        continue
    raise RuntimeError("No terminal emulator found!")


def __spawn_terminal_windows(
    program: str, argv: List[str], **kwargs
) -> Callable:
    """"""
    # & RUN
    arguments = [program, *argv]
    print(
        f"subprocess.Popen(\n"
        f"    {arguments},"
        f"    creationflags = subprocess.CREATE_NEW_CONSOLE,\n"
        f"    {kwargs},\n"
        f")"
    )
    time.sleep(1)
    p = subprocess.Popen(
        arguments,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        **kwargs,
    )

    # & RETURN WAIT FUNCTION
    def wait_function() -> int:
        return p.wait()

    return wait_function


def __spawn_terminal_linux(program: str, argv: List[str], **kwargs) -> Callable:
    """"""
    # & RUN
    terminal_name, terminal_path = __get_terminal_emulator_name_and_executable()
    # The 'gnome-terminal' requires a '--wait' argument to let it not return until its child process
    # has completed. Also, this terminal needs the '--' argument instead of '-e', which is depre-
    # cated.
    if terminal_name == "gnome-terminal":
        arguments = [terminal_path, "--wait", "--", program, *argv]
        print(
            f"subprocess.Popen(\n"
            f"    {arguments},\n"
            f"    env={os.environ},"
            f"    {kwargs},\n"
            f")"
        )
        time.sleep(1)
        p = subprocess.Popen(
            arguments,
            env=os.environ,
            **kwargs,
        )
    # The 'xfce4-terminal' and 'terminator' terminal emulators don't work if you pass the program
    # and arguments as separate list elements. So you need to join them with shlex.
    elif terminal_name in ("xfce4-terminal", "terminator"):
        arguments = [terminal_path, "-e", shlex.join([program, *argv])]
        print(
            f"subprocess.Popen(\n"
            f"    {arguments},\n"
            f"    env={os.environ},"
            f"    {kwargs},\n"
            f")"
        )
        time.sleep(1)
        p = subprocess.Popen(
            arguments,
            env=os.environ,
            **kwargs,
        )
    # For all other terminal emulators, the approach is the same.
    else:
        arguments = [terminal_path, "-e", program, *argv]
        print(
            f"subprocess.Popen(\n"
            f"    {arguments},\n"
            f"    env={os.environ},"
            f"    {kwargs},\n"
            f")"
        )
        time.sleep(1)
        p = subprocess.Popen(
            arguments,
            env=os.environ,
            **kwargs,
        )

    # & RETURN WAIT FUNCTION
    def wait_function() -> int:
        return p.wait()

    return wait_function
