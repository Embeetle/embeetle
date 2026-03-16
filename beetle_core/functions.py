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

import os
import os.path
import sys
import errno
import re
import uuid
import ast
import codecs
import operator
import datetime
import components.lockcache
import subprocess
import threading
import time
import webbrowser
import json
import types
import traceback
import serial
import serial.tools
import serial.tools.list_ports
import xmltodict
import purefunctions
import qt
import constants
import data
import iconfunctions
import filefunctions
import serverfunctions
from purefunctions import *
from typing import Optional
import os_checker

if TYPE_CHECKING:
    import tree_widget.helpers.item_layout as _item_layout_

# REPL message displaying function (that needs to be assigned at runtime!)
repl_print = None


def get_position(
    event: Optional[
        Union[qt.QEvent, qt.QContextMenuEvent, qt.QMouseEvent]
    ] = None,
) -> Union[qt.QPoint, qt.QPointF]:
    """Get the global position.

    Returns a 'QPoint()' in PyQt5 and a 'QPointF()' in PyQt6.
    """
    # & No event-instance given
    if event is None:
        return qt.QPointF(qt.QCursor.pos())

    # & event-instance given
    assert event is not None
    try:
        return qt.QPointF(event.globalPosition().toPoint())  # type: ignore
    except:
        pass
    return get_position(event=None)


def echo(*args, **kwargs):
    #    print(*args, **kwargs)
    if data.main_form is not None:
        if hasattr(data.main_form, "display") and hasattr(
            data.main_form.display, "display_error"
        ):
            data.main_form.display.display_error(*args)


def create_thread(func, *args):
    t = threading.Thread(target=func, args=args)
    t.daemon = True
    t.start()


def get_resource_file(subpath):
    filename = join_resources_dir_to_path(subpath)
    return load_json_file(filename)


def get_geometry(widget):
    geometry = widget.geometry()
    return {
        "left": geometry.left(),
        "top": geometry.top(),
        "width": geometry.width(),
        "height": geometry.height(),
    }


def camel_to_snake(string):
    string = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    string = re.sub("(.)([0-9]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", string).lower()


def open_embeetle(arguments: List[str] = []) -> None:
    python_path = sys.executable
    eo_script_path = unixify_path_join(
        data.beetle_core_directory, "embeetle.py"
    )
    command_list = [
        python_path,
        eo_script_path,
    ] + arguments
    subprocess_popen(command_list)
    return


def process_events(cycles: int = 1, delay: Optional[float] = None) -> None:
    for i in range(cycles):
        qt.QCoreApplication.processEvents()
    if delay is not None:
        time.sleep(delay)


def get_object_as_string(value):
    if isinstance(value, str):
        return "'{}'".format(value)
    elif isinstance(value, int):
        return "{}".format(value)
    elif isinstance(value, bool):
        return "{}".format(value)
    elif isinstance(value, qt.QColor):
        return "qt.QColor({},{},{},alpha={})".format(
            value.red(), value.green(), value.blue(), value.alpha()
        )
    elif isinstance(value, qt.QFont):
        return "qt.QFont('{}',{})".format(value.family(), value.pointSize())
    else:
        raise Exception(
            "Unknown object to transform to string: " + value.__class__
        )


def safe_execute(function):
    """Wrapper for safe excecution of a function/method."""

    def safety_wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as ex:
            #            print(ex)
            return None

    return safety_wrapper


def focus_dialog(dialog):
    dialog.setFocus(True)
    dialog.activateWindow()
    dialog.raise_()


def wiggle_cursor():
    cursor = qt.QCursor()
    pos = cursor.pos()
    cursor.setPos(pos.x() + 1, pos.y())
    qt.QTest.qWait(10)
    cursor.setPos(pos.x() - 1, pos.y())
    qt.QTest.qWait(10)
    cursor.setPos(pos.x(), pos.y())


def get_file_status(path):
    # Editor does not have a file reference.
    if path == "":
        _type = data.FileType.Standard
    # File is in the project.
    elif data.current_project.check_if_project_file(path):
        _type = data.FileType.Standard
    # File is in the compiler.
    elif data.current_project.get_toolpath_seg().check_if_in_compiler(path):
        _type = data.FileType.InsideCompiler
    # File is outside everything.
    else:
        _type = data.FileType.OutsideOfProject
    return _type


def initialize_locks():
    # Initialize all multiprocessing locks, add them as needed.
    lock_names = (
        "update-editor-diagnostics",
        "show-symbols",
        "file-tree-structure-generate",
        "file-tree-structure-regenerate",
        "file-tree-structure-use",
        "diagnostics-buffer",
    )
    locks = {}
    for ln in lock_names:
        locks[ln] = components.lockcache.create_lock()
    components.lockcache.init(locks)


def get_keyboard_modifiers():
    mods = []
    key_modifiers = qt.QApplication.keyboardModifiers()
    if (int(key_modifiers) & qt.Qt.KeyboardModifier.ControlModifier) != 0:
        mods.append("ctrl")
    if (int(key_modifiers) & qt.Qt.KeyboardModifier.ShiftModifier) != 0:
        mods.append("shift")
    if (int(key_modifiers) & qt.Qt.KeyboardModifier.AltModifier) != 0:
        mods.append("alt")
    return mods


def disconnect_signals_connected_to_qobject(qobj: qt.QObject) -> None:
    """Disconnect all signals that are connected to a slot in the given 'qobj'.

    WARNING: It seems like this function is not as good as I thought.
             Disconnecting *all* signals seems to hinder the full cleanup of
             the given qt.QWidget() (eg. the 'destroyed' signal cannot fire any-
             more).
             I'll not yet delete the function here, but don't use it for now!
    """
    raise RuntimeWarning(
        "WARNING: Disconnecting all signals from a QObject() can hinder "
        "proper cleanup!"
    )

    # Define inner function for a complete signal
    # disconnection
    def discon_sig(signal):
        while True:
            try:
                signal.disconnect()
            except TypeError:
                break
        return

    # Loop to find all signals that need
    # disconnection
    for x in filter(
        lambda y: type(y) == qt.pyqtBoundSignal and 0 < qobj.receivers(y),
        map(lambda z: getattr(qobj, z), dir(qobj)),
    ):
        discon_sig(x)
    return


def get_file_type(file_with_path) -> str:
    """Get file extension and return file type as string."""
    # Split the file and path
    path, file = os.path.split(file_with_path)
    # Split file name and extension
    file_name, file_extension = os.path.splitext(file)

    # Special case for config files
    if file.lower() == data.config_filename or file.lower() == "exco.ini":
        return "python"

    # Special case for makefile
    if file_name.lower() == "makefile":
        return "makefile"

    # Special case for linkerscript
    if file_name.lower() == "linkerscript":
        return "linkerscript"

    # Convert extension to lowercase for case-insensitive comparison
    ext_lower = file_extension.lower()

    # Use the extensions dictionary for lookup
    for file_type, extensions in constants.file_extensions.items():
        if ext_lower in extensions:
            # Handle special return values that differ from dict keys
            if file_type == "cpp":
                return "c++"
            elif file_type == "hpp":
                return "h++"
            elif file_type == "oberon":
                return "oberon/modula"
            elif file_type == "csharp":
                return "c#"
            else:
                return file_type

    # The file extension was not recognized, try the file contents for more information
    file_type = test_file_content_for_type(file_with_path)

    # If the file content did not give any useful information, set the content as text
    if file_type == "none":
        return "text"

    # Return file type string
    return file_type


def create_project_relative_path(file_path):
    relative_path = unixify_path_remove(
        file_path,
        data.current_project.get_proj_rootpath(),
    )
    return "rel://" + relative_path


def get_file_size_Mb(file_with_path):
    """Get the file size in Mb."""
    size_bytes = os.path.getsize(file_with_path)
    # Convert size into megabytes
    size_Mb = size_bytes / (1024 * 1024)
    # return the size in megabyte
    return size_Mb


def find_files_with_text(
    search_text,
    search_dir,
    case_sensitive=False,
    search_subdirs=True,
    break_on_find=False,
):
    """Search for the specified text in files in the specified directory and
    return a file list."""
    # Check if the directory is valid
    if os.path.isdir(search_dir) == False:
        return None
    # Create an empty file list
    text_file_list = []
    # Check if subdirectories should be included
    if search_subdirs == True:
        walk_tree = os.walk(search_dir)
    else:
        # Only use the first generator value(only the top directory)
        walk_tree = [next(os.walk(search_dir))]
    # "walk" through the directory tree and save the readable files to a list
    for root, subFolders, files in walk_tree:
        for file in files:
            # Merge the path and filename
            full_with_path = os.path.join(root, file)
            if test_text_file(full_with_path) is not None:
                # On windows, the function "os.path.join(root, file)" line gives a combination of "/" and "\\",
                # which looks weird but works. The replace was added to have things consistent in the return file list.
                full_with_path = full_with_path.replace("\\", "/")
                text_file_list.append(full_with_path)
    # Search for the text in found files
    return_file_list = []
    for file in text_file_list:
        try:
            file_text = read_file_to_string(file)
            # Set the comparison according to case sensitivity
            if case_sensitive == False:
                compare_file_text = file_text.lower()
                compare_search_text = search_text.lower()
            else:
                compare_file_text = file_text
                compare_search_text = search_text
            # Check if file contains the search string
            if compare_search_text in compare_file_text:
                return_file_list.append(file)
                # Check if break option on first find is true
                if break_on_find == True:
                    break
        except:
            continue
    # Return the generated list
    return return_file_list


def find_files_with_text_enum(
    search_text,
    search_dir,
    case_sensitive=False,
    search_subdirs=True,
    break_on_find=False,
):
    """Search for the specified text in files in the specified directory and
    return a file list and lines where the text was found at."""
    # Check if the directory is valid
    if os.path.isdir(search_dir) == False:
        return None
    # Create an empty file list
    text_file_list = []
    # Check if subdirectories should be included
    if search_subdirs == True:
        walk_tree = os.walk(search_dir)
    else:
        # Only use the first generator value(only the top directory)
        walk_tree = [next(os.walk(search_dir))]
    # "walk" through the directory tree and save the readable files to a list
    for root, subFolders, files in walk_tree:
        for file in files:
            # Merge the path and filename
            full_with_path = os.path.join(root, file)
            if test_text_file(full_with_path) is not None:
                # On windows, the function "os.path.join(root, file)" line gives a combination of "/" and "\\",
                # which looks weird but works. The replace was added to have things consistent in the return file list.
                full_with_path = full_with_path.replace("\\", "/")
                text_file_list.append(full_with_path)
    # Search for the text in found files
    return_file_dict = {}
    break_out = False
    for file in text_file_list:
        if break_out == True:
            break
        try:
            file_lines = read_file_to_list(file)
            # Set the comparison according to case sensitivity
            if case_sensitive == False:
                compare_search_text = search_text.lower()
            else:
                compare_search_text = search_text
            # Check the file line by line
            for i, line in enumerate(file_lines):
                if case_sensitive == False:
                    line = line.lower()
                if compare_search_text in line:
                    if file in return_file_dict:
                        return_file_dict[file].append(i)
                    else:
                        return_file_dict[file] = [i]
                    # Check if break option on first find is true
                    if break_on_find == True:
                        break_out = True
        except:
            continue
    # Return the generated list
    return return_file_dict


def replace_text_in_files(
    search_text,
    replace_text,
    search_dir,
    case_sensitive=False,
    search_subdirs=True,
):
    """Search for the specified text in files in the specified directory and
    replace all instances of the search_text with replace_text and save the
    changes back to the file."""
    # Get the files with the search string in them
    found_files = find_files_with_text(
        search_text, search_dir, case_sensitive, search_subdirs
    )
    if found_files is None:
        return []
    # Loop through the found list and replace the text
    for file in found_files:
        # Read the file
        file_text = read_file_to_string(file)
        # Compile the regex expression according to case sensitivity
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        # Replace all instances of search text with the replace text
        replaced_text = re.sub(compiled_search_re, replace_text, file_text)
        # Write the replaced text back to the file
        write_to_file(replaced_text, file)
    # Return the found files list
    return found_files


def replace_text_in_files_enum(
    search_text,
    replace_text,
    search_dir,
    case_sensitive=False,
    search_subdirs=True,
):
    """The second version of replace_text_in_files, that goes line-by-line and
    replaces found instances and stores the line numbers, at which the
    replacements were made."""
    # Get the files with the search string in them
    found_files = find_files_with_text(
        search_text, search_dir, case_sensitive, search_subdirs
    )
    if found_files is None:
        return {}
    # Compile the regex expression according to case sensitivity
    if case_sensitive == True:
        compiled_search_re = re.compile(search_text)
    else:
        compiled_search_re = re.compile(search_text, re.IGNORECASE)
    # Loop through the found list and replace the text
    return_files = {}
    for file in found_files:
        # Read the file
        file_text_list = read_file_to_list(file)
        # Cycle through the lines, replacing text and storing the line numbers of replacements
        for i in range(len(file_text_list)):
            if case_sensitive == True:
                line = file_text_list[i]
            else:
                search_text = search_text.lower()
                line = file_text_list[i].lower()
            if search_text in line:
                if file in return_files:
                    return_files[file].append(i)
                else:
                    return_files[file] = [i]
                file_text_list[i] = re.sub(
                    compiled_search_re, replace_text, file_text_list[i]
                )
        # Write the replaced text back to the file
        replaced_text = "\n".join(file_text_list)
        write_to_file(replaced_text, file)
    # Return the found files list
    return return_files


def find_files_by_name(
    search_text,
    search_dir,
    case_sensitive=False,
    regex_search=False,
    search_subdirs=True,
):
    """Find file with search_text string in its name in the specified
    directory."""
    # Check if the directory is valid
    if os.path.isdir(search_dir) == False:
        return None
    # Check if subdirectories should be included
    if search_subdirs == True:
        walk_tree = os.walk(search_dir)
    else:
        # Only use the first generator value(only the top directory)
        walk_tree = [next(os.walk(search_dir))]
    # Create an empty file list
    found_file_list = []
    # Search
    if regex_search:
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        for root, subFolders, files in walk_tree:
            for file in files:
                if re.match(compiled_search_re, file):
                    full_with_path = os.path.join(root, file).replace("\\", "/")
                    found_file_list.append(full_with_path)
    else:
        for root, subFolders, files in walk_tree:
            for file in files:
                # Set the comparison according to case sensitivity
                if case_sensitive == False:
                    compare_actual_filename = file.lower()
                    compare_search_filename = search_text.lower()
                else:
                    compare_actual_filename = file
                    compare_search_filename = search_text
                # Test if the name of the file contains the search string
                if compare_search_filename in compare_actual_filename:
                    full_with_path = os.path.join(root, file).replace("\\", "/")
                    found_file_list.append(full_with_path)
    # Return the generated list
    return found_file_list


def get_nim_node_tree(nim_code):
    """Parse the text and return a node tree as a list.

    The text must be valid Nim/Nimrod code.
    """

    class NimNode:
        def __init__(self):
            # Attributes
            self.name = None
            self.description = None
            self.type = None
            self.parameters = None
            self.return_type = None
            self.line = None
            # Child node lists
            self.imports = []
            self.types = []
            self.consts = []
            self.lets = []
            self.vars = []
            self.procedures = []
            self.forward_declarations = []
            self.converters = []
            self.iterators = []
            self.methods = []
            self.properties = []
            self.templates = []
            self.macros = []
            self.objects = []
            self.namespaces = []

    # Nested function for determining the next blocks indentation level
    def get_next_blocks_indentation(current_step, lines):
        for ln in range(current_step, len(lines)):
            if (
                lines[ln].strip() != ""
                and lines[ln].strip().startswith("#") == False
            ):
                return get_line_indentation(lines[ln])
        else:
            return 250

    # Nested function for finding the closing parenthesis of parameter definitions
    def get_closing_parenthesis(current_step, lines):
        for ln in range(current_step, len(lines)):
            if ")" in lines[ln] and (
                lines[ln].count(")") == (lines[ln].count("(") + 1)
            ):
                return ln
        else:
            return None

    # Nested function for creating a procedure, method, macro or template node
    def create_node(
        node,
        search_string,
        current_line,
        current_line_number,
        line_list,
        previous_offset=0,
    ):
        # Reset the procedure's starting line adjustment variable
        body_starting_line_number = None
        # Reset the local skip line variable
        local_skip_to_line = None
        # Parse procedure name according to the line characters
        if "(" in current_line:
            # The procedure has parameters
            base_search_string = (
                r"{:s}\s+(.*?)\(|{:s}\s+(.*?)\:|{:s}\s+(.*?)\=".format(
                    search_string, search_string, search_string
                )
            )
            proc_name_search_pattern = re.compile(
                base_search_string, re.IGNORECASE
            )
            name_match_object = re.search(
                proc_name_search_pattern, current_line
            )
            for i in range(1, 4):
                node.name = name_match_object.group(i)
                if node.name != "" and node.name is not None:
                    break
            # Skip lines if the parameters stretch over multiple lines
            if not (")" in current_line):
                body_starting_line_number = get_closing_parenthesis(
                    current_line_number + 1, line_list
                )
                current_line = line_list[body_starting_line_number]
            # Parse the procedure parameters and return type
            if search_string == "proc":
                return_type = None
                parameters = None
                # Check if the parameters are declared over multiple lines
                if body_starting_line_number is not None:
                    parameter_string = ""
                    open_index = line_list[current_line_number].find("(") + 1
                    parameter_string += line_list[current_line_number][
                        open_index:
                    ]
                    for i in range(
                        current_line_number + 1, body_starting_line_number + 1
                    ):
                        if ")" in line_list[i] and (
                            line_list[i].count(")")
                            == (line_list[i].count("(") + 1)
                        ):
                            close_index = line_list[i].find(")")
                            current_parameter = line_list[i][
                                :close_index
                            ].strip()
                            # Filter out the parameter initialization
                            if "=" in current_parameter:
                                current_parameter = current_parameter[
                                    : current_parameter.find("=")
                                ]
                            parameter_string += current_parameter
                        else:
                            current_parameter = line_list[i].strip()
                            # Filter out the parameter initialization
                            if "=" in current_parameter:
                                current_parameter = current_parameter[
                                    : current_parameter.find("=")
                                ]
                            parameter_string += current_parameter
                    parameters = [
                        par.strip()
                        for par in parameter_string.split(",")
                        if par.strip() != ""
                    ]
                    # Check the return type
                    split_line = line_list[body_starting_line_number][
                        close_index:
                    ].split(":")
                    if len(split_line) > 1:
                        return_type = split_line[1].replace("=", "")
                        return_type = return_type.strip()
                else:
                    open_index = line_list[current_line_number].find("(") + 1
                    close_index = line_list[current_line_number].find(")")
                    parameter_string = line_list[current_line_number][
                        open_index:close_index
                    ]
                    parameters = [
                        par
                        for par in parameter_string.split(",")
                        if par.strip() != ""
                    ]
                    # Check the return type
                    split_line = line_list[current_line_number][
                        close_index:
                    ].split(":")
                    if len(split_line) > 1:
                        return_type = split_line[1].replace("=", "")
                        return_type = return_type.strip()
                node.parameters = parameters
                node.return_type = return_type
        elif ":" in current_line:
            # The procedure/macro/... has no parameters, but has a return type
            node.name = (
                current_line.replace(search_string, "", 1).split(":")[0].strip()
            )
            # Special parsing for classes
            if search_string == "class" or search_string == "property":
                node.name = node.name.split()[0]
        else:
            # The procedure/macro/... has no parameters and no return type
            node.name = (
                current_line.replace(search_string, "", 1).split()[0].strip()
            )

        # Parse node
        if "=" in current_line and current_line.strip().endswith("="):
            # Check if the declaration is a one-liner
            if (current_line.strip().endswith("=") == False) and (
                (
                    len(current_line.split("=")) == 2
                    and current_line.split("=")[1].strip() != ""
                )
                or (
                    len(current_line.split("=")) > 2
                    and current_line[current_line.rfind(")") :].split("=")[1]
                    != ""
                )
            ):
                # One-liner
                pass
            else:
                # Adjust the procedure body starting line as needed
                starting_line_number = current_line_number + 1
                if body_starting_line_number is not None:
                    starting_line_number = body_starting_line_number + 1
                # Parse the procedure for its local child nodes
                sub_node_lines = []
                compare_indentation = get_next_blocks_indentation(
                    starting_line_number, line_list
                )
                for ln in range(starting_line_number, len(line_list)):
                    # Skip empty lines
                    if (
                        line_list[ln].strip() == ""
                        or line_list[ln].strip().startswith("#") == True
                    ):
                        # Add the blank space at the correct indentation level
                        # to have the correct number of lines in the list
                        sub_node_lines.append(" " * compare_indentation)
                        continue
                    elif (
                        get_line_indentation(line_list[ln])
                        < compare_indentation
                    ):
                        # Store the end of the procedure declaration
                        local_skip_to_line = ln
                        # Reached the last line of the procedure declaration
                        break
                    else:
                        sub_node_lines.append(line_list[ln])
                else:
                    # For loop looped through all of the lines, skip them
                    local_skip_to_line = len(line_list) - 1
                starting_line_number += previous_offset
                node = parse_node(
                    node, sub_node_lines, line_offset=starting_line_number
                )
        elif (
            search_string == "class"
            or search_string == "namespace"
            or search_string == "property"
        ):
            """special macro identifiers: class, namespace, ..."""
            # Adjust the procedure body starting line as needed
            starting_line_number = current_line_number + 1
            if body_starting_line_number is not None:
                starting_line_number = body_starting_line_number + 1
            # Parse the procedure for its local child nodes
            sub_node_lines = []
            compare_indentation = get_next_blocks_indentation(
                starting_line_number, line_list
            )
            for ln in range(starting_line_number, len(line_list)):
                # Skip empty lines
                if (
                    line_list[ln].strip() == ""
                    or line_list[ln].strip().startswith("#") == True
                ):
                    # Add the blank space at the correct indentation level
                    # to have the correct number of lines in the list
                    sub_node_lines.append(" " * compare_indentation)
                    continue
                elif get_line_indentation(line_list[ln]) < compare_indentation:
                    # Store the end of the procedure declaration
                    local_skip_to_line = ln
                    # Reached the last line of the procedure declaration
                    break
                else:
                    sub_node_lines.append(line_list[ln])
            else:
                # For loop looped through all of the lines, skip them
                local_skip_to_line = len(line_list) - 1
            starting_line_number += previous_offset
            node = parse_node(
                node, sub_node_lines, line_offset=starting_line_number
            )
        else:
            """The procedure is a forward declaracion."""
            node.type = "forward declaration"
        # Return the relevant data
        return node, local_skip_to_line

    # Split the Nim code into lines
    nim_code_lines = nim_code.split("\n")
    # Create and initialize the main node that will hold all other nodes
    main_node = NimNode()
    main_node.name = "main"
    main_node.description = "main node"

    def parse_node(input_node, code_lines, line_offset=0):
        # Initialize the starting indentation levels (number of spaces)
        current_indentation = 0
        compare_indentation = 0
        # Initialize the various state flags
        import_statement = False
        type_statement = False
        const_statement = False
        let_statement = False
        var_statement = False
        proc_statement = False
        converter_statement = False
        iterator_statement = False
        method_statement = False
        macro_statement = False
        template_statement = False
        class_statement = False
        namespace_statement = False
        property_statement = False
        # Initialize the flag for skipping multiple lines
        skip_to_line = None
        # Main loop
        for line_count, line in enumerate(code_lines):
            # Skip blank lines
            if line.strip() == "" or line.strip().startswith("#"):
                continue
            # Check if line needs to be skipped
            if skip_to_line is not None:
                if line_count >= skip_to_line:
                    skip_to_line = None
                else:
                    continue
            # Get line indentation and strip leading/trailing whitespaces
            current_indentation = get_line_indentation(line)
            line = line.strip()
            # Discard the comment part of a line, if it's in the line
            if "#" in line:
                stringing = False
                string_character = None
                for ch_count, ch in enumerate(line):
                    if ch == '"' or ch == "'":
                        # Catch the string building characters
                        if stringing == False:
                            stringing = True
                            string_character = ch
                        elif ch == string_character:
                            stringing = False
                            string_character = None
                    elif ch == "#" and stringing == False:
                        # Discrad the part of the line from the
                        # comment character to the end of the line
                        line = line[:ch_count].strip()
                        break

            if import_statement == True:
                if current_indentation == compare_indentation:
                    for module in line.split(","):
                        module_name = module.strip()
                        if module_name != "":
                            import_node = NimNode()
                            import_node.name = module_name
                            import_node.description = "import"
                            import_node.line = line_count + line_offset
                            input_node.imports.append(import_node)
                elif current_indentation < compare_indentation:
                    import_statement = False
            elif type_statement == True:
                if current_indentation == compare_indentation:
                    type_node = NimNode()
                    type_node.name = line.split("=")[0].strip()
                    type_node.description = "type"
                    type_node.line = line_count + line_offset
                    input_node.types.append(type_node)
                elif current_indentation < compare_indentation:
                    type_statement = False
            elif const_statement == True:
                if current_indentation == compare_indentation:
                    const_node = NimNode()
                    if ":" in line:
                        const_node.name = line.split(":")[0].strip()
                        const_node.type = (
                            line.split(":")[1].split("=")[0].strip()
                        )
                    else:
                        const_node.name = line.split("=")[0].strip()
                        const_node.type = None
                    if const_node.name[0].isalpha():
                        const_node.description = "const"
                        const_node.line = line_count + line_offset
                        input_node.consts.append(const_node)
                elif current_indentation < compare_indentation:
                    const_statement = False
            elif let_statement == True:
                if current_indentation == compare_indentation:
                    let_node = NimNode()
                    if ":" in line:
                        let_node.name = line.split(":")[0].strip()
                        let_node.type = line.split(":")[1].split("=")[0].strip()
                    else:
                        let_node.name = line.split("=")[0].strip()
                        let_node.type = None
                    if let_node.name[0].isalpha():
                        let_node.description = "let"
                        let_node.line = line_count + line_offset
                        input_node.lets.append(let_node)
                elif current_indentation < compare_indentation:
                    let_statement = False
            elif var_statement == True:
                if current_indentation == compare_indentation:
                    if (
                        ":" in line
                        and "=" in line
                        and (line.find(":") < line.find("="))
                    ):
                        type = line.split(":")[1].split("=")[0].strip()
                        line = line.split(":")[0].strip()
                    elif ":" in line and not ("=" in line):
                        type = line.split(":")[1].strip()
                        line = line.split(":")[0].strip()
                    elif "=" in line:
                        type = line.split("=")[1][: line.find("(")].strip()
                        line = line.split("=")[0].strip()
                    for var in line.split(","):
                        var_name = var.strip()
                        if var_name != "" and var_name[0].isalpha():
                            var_node = NimNode()
                            var_node.name = var.strip()
                            var_node.description = "var"
                            var_node.type = type
                            var_node.line = line_count + line_offset
                            input_node.vars.append(var_node)
                elif current_indentation < compare_indentation:
                    var_statement = False
            elif proc_statement == True:
                proc_statement = False
            elif converter_statement == True:
                converter_statement = False
            elif iterator_statement == True:
                iterator_statement = False
            elif method_statement == True:
                method_statement = False
            elif macro_statement == True:
                macro_statement = False
            elif template_statement == True:
                template_statement = False
            elif class_statement == True:
                class_statement = False
            elif namespace_statement == True:
                namespace_statement = False
            elif property_statement == True:
                property_statement = False

            # Testing for base level declarations
            if line.startswith("import ") or line == "import":
                if line == "import":
                    import_statement = True
                    compare_indentation = get_next_blocks_indentation(
                        line_count + 1, code_lines
                    )
                else:
                    line = line.replace("import", "")
                    for module in line.split(","):
                        module_name = module.strip()
                        if module_name != "":
                            import_node = NimNode()
                            import_node.name = module_name
                            import_node.description = "import"
                            import_node.line = line_count + line_offset
                            input_node.imports.append(import_node)
            elif line.startswith("type ") or line == "type":
                if line == "type":
                    type_statement = True
                    compare_indentation = get_next_blocks_indentation(
                        line_count + 1, code_lines
                    )
                else:
                    line = line.replace("type", "")
                    type_node = NimNode()
                    type_node.name = line.split("=")[0].strip()
                    type_node.description = "type"
                    type_node.line = line_count + line_offset
                    input_node.types.append(type_node)
            elif line.startswith("const ") or line == "const":
                if line == "const":
                    const_statement = True
                    compare_indentation = get_next_blocks_indentation(
                        line_count + 1, code_lines
                    )
                else:
                    line = line.replace("const", "")
                    const_node = NimNode()
                    if ":" in line:
                        const_node.name = line.split(":")[0].strip()
                        const_node.type = (
                            line.split(":")[1].split("=")[0].strip()
                        )
                    else:
                        const_node.name = line.split("=")[0].strip()
                        const_node.type = None
                    const_node.description = "const"
                    const_node.line = line_count + line_offset
                    input_node.consts.append(const_node)
            elif line.startswith("let ") or line == "let":
                if line == "let":
                    let_statement = True
                    compare_indentation = get_next_blocks_indentation(
                        line_count + 1, code_lines
                    )
                else:
                    line = line.replace("let", "")
                    let_node = NimNode()
                    if ":" in line:
                        let_node.name = line.split(":")[0].strip()
                        let_node.type = line.split(":")[1].split("=")[0].strip()
                    else:
                        let_node.name = line.split("=")[0].strip()
                        let_node.type = None
                    let_node.description = "let"
                    let_node.line = line_count + line_offset
                    input_node.lets.append(let_node)
            elif line.startswith("var ") or line == "var":
                if line == "var":
                    var_statement = True
                    compare_indentation = get_next_blocks_indentation(
                        line_count + 1, code_lines
                    )
                else:
                    line = line.replace("var", "")
                    if (
                        ":" in line
                        and "=" in line
                        and (line.find(":") < line.find("="))
                    ):
                        type = line.split(":")[1].split("=")[0].strip()
                        line = line.split(":")[0].strip()
                    elif ":" in line and not ("=" in line):
                        type = line.split(":")[1].strip()
                        line = line.split(":")[0].strip()
                    elif "=" in line:
                        type = line.split("=")[1][: line.find("(")].strip()
                        line = line.split("=")[0].strip()
                    for var in line.split(","):
                        var_name = var.strip()
                        if var_name != "":
                            var_node = NimNode()
                            var_node.name = var_name
                            var_node.description = "var"
                            var_node.type = type
                            var_node.line = line_count + line_offset
                            input_node.vars.append(var_node)
            elif line.startswith("proc "):
                # Create and add the procedure node
                proc_node = NimNode()
                proc_node, skip_to_line = create_node(
                    proc_node, "proc", line, line_count, code_lines, line_offset
                )
                proc_node.description = "procedure"
                proc_node.line = line_count + line_offset
                # Add the procedure to the main node
                if proc_node.type == "forward declaration":
                    input_node.forward_declarations.append(proc_node)
                else:
                    input_node.procedures.append(proc_node)
                # Set the procedure flag
                proc_statement = True
            elif line.startswith("converter "):
                # Create and add the converter node
                converter_node = NimNode()
                converter_node, skip_to_line = create_node(
                    converter_node,
                    "converter",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                converter_node.description = "converter"
                converter_node.line = line_count + line_offset
                # Add the converter to the main node
                input_node.converters.append(converter_node)
                # Set the converter flag
                converter_statement = True
            elif line.startswith("iterator "):
                # Create and add the converter node
                iterator_node = NimNode()
                iterator_node, skip_to_line = create_node(
                    iterator_node,
                    "iterator",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                iterator_node.description = "iterator"
                iterator_node.line = line_count + line_offset
                # Add the iterator to the main node
                input_node.iterators.append(iterator_node)
                # Set the iterator flag
                iterator_statement = True
            elif line.startswith("method "):
                # Create and add the method node
                method_node = NimNode()
                method_node, skip_to_line = create_node(
                    method_node,
                    "method",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                method_node.description = "method"
                method_node.line = line_count + line_offset
                # Add the procedure to the main node
                input_node.methods.append(method_node)
                # Set the method flag
                method_statement = True
            elif line.startswith("property "):
                # Create and add the property node
                property_node = NimNode()
                property_node, skip_to_line = create_node(
                    property_node,
                    "property",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                property_node.description = "property"
                property_node.line = line_count + line_offset
                # Add the property to the parent node
                input_node.properties.append(property_node)
                # Set the property flag
                property_statement = True
            elif line.startswith("macro "):
                # Create and add the macro node
                macro_node = NimNode()
                macro_node, skip_to_line = create_node(
                    macro_node,
                    "macro",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                macro_node.description = "macro"
                macro_node.line = line_count + line_offset
                # Add the procedure to the main node
                input_node.macros.append(macro_node)
                # Set the macro flag
                macro_statement = True
            elif line.startswith("template "):
                # Create and add the template node
                template_node = NimNode()
                template_node, skip_to_line = create_node(
                    template_node,
                    "template",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                template_node.description = "template"
                template_node.line = line_count + line_offset
                # Add the procedure to the main node
                input_node.templates.append(template_node)
                # Set the template flag
                template_statement = True
            elif line.startswith("class "):
                # Create and add the class node
                search_term = "class"
                object_node = NimNode()
                object_node, skip_to_line = create_node(
                    object_node,
                    search_term,
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                object_node.description = search_term
                object_node.line = line_count + line_offset
                # Add the class to the main node
                input_node.objects.append(object_node)
                # Set the class flag
                class_statement = True
            elif line.startswith("namespace "):
                # Create and add the class node
                namespace_node = NimNode()
                namespace_node, skip_to_line = create_node(
                    namespace_node,
                    "namespace",
                    line,
                    line_count,
                    code_lines,
                    line_offset,
                )
                namespace_node.description = "namespace"
                namespace_node.line = line_count + line_offset
                # Add the class to the main node
                input_node.namespaces.append(namespace_node)
                # Set the class flag
                namespace_statement = True
        return input_node

    # Parse the main node
    main_node = parse_node(main_node, nim_code_lines)
    # Return the node list
    return main_node


def get_python_node_list(python_code):
    """Parse the text and return nodes as a list.

    The text must be valid Python 3 code.
    """

    # Nested function for recursivly traversing all the child nodes
    def check_children(node, level, function_list):
        lst = []
        for i in ast.iter_child_nodes(node):
            if isinstance(i, ast.ClassDef) or isinstance(i, ast.FunctionDef):
                if isinstance(i, ast.FunctionDef):
                    # Remove the function from the global function list
                    if i in function_list:
                        function_list.remove(i)
                lst.append((level, i))
            # Always descend into the child node to check for nested functions/classes
            lst.extend(check_children(i, level + 1, function_list))
        return lst

    # Parse the file
    parsed_string = ast.parse(python_code)
    nodes = [node for node in ast.walk(parsed_string)]
    # Get import/import_from nodes, combine them into one list and sort them
    import_nodes = [
        (node.names[0].name, node.lineno)
        for node in nodes
        if isinstance(node, ast.Import)
    ]
    importfrom_nodes = [
        (node.module, node.lineno)
        for node in nodes
        if isinstance(node, ast.ImportFrom)
    ]
    import_nodes.extend(importfrom_nodes)
    import_nodes.sort(key=operator.itemgetter(0))
    # Other nodes
    class_nodes = [node for node in nodes if isinstance(node, ast.ClassDef)]
    function_nodes = [
        node for node in nodes if isinstance(node, ast.FunctionDef)
    ]
    global_vars = [node for node in nodes if isinstance(node, ast.Name)]
    # Get child nodes for all of the classes
    children = []
    class_tree_nodes = []
    for c_node in class_nodes:
        # Check if the node has already been parsed as a child node in another class
        if not (c_node in children):
            cc = check_children(c_node, 0, function_nodes)
            class_tree_nodes.append((c_node, cc))
            children.extend([c[1] for c in cc])
    # Return the parse results
    return import_nodes, class_tree_nodes, function_nodes, global_vars


def get_python_node_tree(python_code):
    """Parse the text and return nodes as a nested tree.

    The text must be valid Python 3 code.
    """

    # Node object
    class PythonNode:
        def __init__(self, name, type, line_number, level):
            self.name = name
            self.type = type
            self.line_number = line_number
            self.level = level
            self.children = []

    # Main parsing function
    def parse_node(ast_node, level, parent_node=None):
        nonlocal globals_list
        nonlocal python_node_tree
        new_node = None
        if isinstance(ast_node, ast.ClassDef):
            new_node = PythonNode(
                ast_node.name, "class", ast_node.lineno, level
            )
            for child_node in ast_node.body:
                result = parse_node(child_node, level + 1, new_node)
                if result is not None:
                    if isinstance(result, list):
                        for n in result:
                            new_node.children.append(n)
                    else:
                        new_node.children.append(result)
            new_node.children = sorted(new_node.children, key=lambda x: x.name)
        elif isinstance(ast_node, ast.FunctionDef):
            new_node = PythonNode(
                ast_node.name, "function", ast_node.lineno, level
            )
            for child_node in ast_node.body:
                result = parse_node(child_node, level + 1, new_node)
                if result is not None:
                    if isinstance(result, list):
                        for n in result:
                            new_node.children.append(n)
                    else:
                        new_node.children.append(result)
            new_node.children = sorted(new_node.children, key=lambda x: x.name)
        elif isinstance(ast_node, ast.Import):
            new_node = PythonNode(
                ast_node.names[0].name, "import", ast_node.lineno, level
            )
        elif isinstance(ast_node, ast.Assign) and (
            level == 0 or parent_node is None
        ):
            # Globals that do are not defined with the 'global' keyword,
            # but are defined on the top level
            new_nodes = []
            for target in ast_node.targets:
                if hasattr(target, "id") == True:
                    name = target.id
                    if not (name in globals_list):
                        new_nodes.append(
                            PythonNode(
                                name, "global_variable", ast_node.lineno, level
                            )
                        )
                        globals_list.append(name)
            return new_nodes
        elif isinstance(ast_node, ast.Global):
            # Globals can be nested somewhere deep in the AST, so they
            # are appended directly into the non-local python_node_tree list
            for name in ast_node.names:
                if not (name in globals_list):
                    python_node_tree.append(
                        PythonNode(
                            name, "global_variable", ast_node.lineno, level
                        )
                    )
                    globals_list.append(name)
        else:
            if parent_node is not None and hasattr(ast_node, "body"):
                for child_node in ast_node.body:
                    result = parse_node(child_node, level + 1, parent_node)
                    if result is not None:
                        if isinstance(result, list):
                            for n in result:
                                parent_node.children.append(n)
                        else:
                            parent_node.children.append(result)
                parent_node.children = sorted(
                    parent_node.children, key=lambda x: x.name
                )
            else:
                new_nodes = []
                if hasattr(ast_node, "body"):
                    for child_node in ast_node.body:
                        result = parse_node(child_node, level + 1, None)
                        if result is not None:
                            if isinstance(result, list):
                                for n in result:
                                    new_nodes.append(n)
                            else:
                                new_nodes.append(result)
                if hasattr(ast_node, "orelse"):
                    for child_node in ast_node.orelse:
                        result = parse_node(child_node, level + 1, None)
                        if result is not None:
                            if isinstance(result, list):
                                for n in result:
                                    new_nodes.append(n)
                            else:
                                new_nodes.append(result)
                if hasattr(ast_node, "finalbody"):
                    for child_node in ast_node.finalbody:
                        result = parse_node(child_node, level + 1, None)
                        if result is not None:
                            if isinstance(result, list):
                                for n in result:
                                    new_nodes.append(n)
                            else:
                                new_nodes.append(result)
                if hasattr(ast_node, "handlers"):
                    for child_node in ast_node.handlers:
                        result = parse_node(child_node, level + 1, None)
                        if result is not None:
                            if isinstance(result, list):
                                for n in result:
                                    new_nodes.append(n)
                            else:
                                new_nodes.append(result)
                if new_nodes != []:
                    return new_nodes
        return new_node

    # Initialization
    parsed_string = ast.parse(python_code)
    python_node_tree = []
    # List of globals for testing for duplicates
    globals_list = []
    # Parse the nodes recursively
    for node in ast.iter_child_nodes(parsed_string):
        result = parse_node(node, 0)
        if result is not None:
            if isinstance(result, list):
                for n in result:
                    python_node_tree.append(n)
            else:
                python_node_tree.append(result)
    # Sort the node list
    python_node_tree = sorted(python_node_tree, key=lambda x: x.name)
    # Return the resulting tree
    return python_node_tree


def remove_comments_from_c_code(c_code):
    """Remove single and multiline comments from C source code."""
    code_list = c_code.split("\n")
    no_comment_code_list = []
    commenting = False
    for line in code_list:
        if commenting == False:
            if '"' in line and "//" in line:
                stringing = False
                for i, ch in enumerate(line):
                    if ch == '"' and stringing == False:
                        stringing = True
                    elif (
                        ch == '"' and line[i - 1] != "\\" and stringing == True
                    ):
                        stringing = False
                    elif stringing == False and line[i : i + 2] == "//":
                        line = line[:i]
                        break
                no_comment_code_list.append(line)
            elif '"' in line and "/*" in line:
                stringing = False
                for i, ch in enumerate(line):
                    if ch == '"' and stringing == False:
                        stringing = True
                    elif (
                        ch == '"' and line[i - 1] != "\\" and stringing == True
                    ):
                        stringing = False
                    elif stringing == False and line[i : i + 2] == "/*":
                        # Remove the closed comments
                        rest_line = re.sub(
                            r"/\*.*?\*/", "", line[i:], flags=re.DOTALL
                        )
                        line = line[:i] + rest_line
                        # Check again if there is a comment sequence left in the line
                        if "/*" in rest_line:
                            line = line[:i] + rest_line[: line.find("/*")]
                            commenting = True
                            break
                no_comment_code_list.append(line)
            elif "//" in line:
                if line.strip().startswith("//"):
                    continue
                else:
                    line = line[: line.find("//")]
                    no_comment_code_list.append(line)
            elif "/*" in line:
                # Remove the closed comments
                line = re.sub(r"/\*.*?\*/", "", line, flags=re.DOTALL)
                # Check again if there is a comment sequence left in the line
                if "/*" in line:
                    line_to_comment = line[: line.find("/*")]
                    if line_to_comment.strip() != "":
                        no_comment_code_list.append(line_to_comment)
                    commenting = True
                else:
                    no_comment_code_list.append(line)
            else:
                no_comment_code_list.append(line)
        else:
            if "*/" in line:
                # Remove the closed comments
                line = re.sub(r"/\*.*?\*/", "", line, flags=re.DOTALL)
                if "*/" in line:
                    if line.strip().endswith("*/"):
                        commenting = False
                    else:
                        line = line[line.find("/*") + 2 :]
                        no_comment_code_list.append(line)
                        commenting = False
    # Return the result
    result = "\n".join(no_comment_code_list)
    return result


def get_c_function_list(c_code):
    """Parse the text and return all C functions as a list.

    Made as simple as possible. The text must be valid C code.
    """
    # Store the text
    text = c_code
    # Initialize state variables
    curly_count = 0
    parenthesis_count = 0
    singleline_commenting = False
    multiline_commenting = False
    typedefing = False
    stringing = False
    previous_token = ""
    last_found_function = ""
    last_line = 0
    current_line = 1
    function_list = []
    # Tokenize the text and remove the space characters
    splitter = re.compile(r"(\#\w+|\'|\"|\n|\s+|\w+|\W)")
    tokens = [token for token in splitter.findall(text)]
    # Main Loop for filtering tokens
    for i, token in enumerate(tokens):
        stripped_token = token.strip()
        if "\n" in token:
            newline_count = token.count("\n")
            current_line += newline_count
            # Reset the single line comment flag
            singleline_commenting = False
        if stripped_token == "":
            continue
        # Check for function definitions
        if curly_count == 0:
            if multiline_commenting == False and singleline_commenting == False:
                if token == "{" and previous_token == ")":
                    # The function has passed the filter, add it to the list
                    function_list.append((last_found_function, last_line))
                elif (
                    token == "("
                    and re.match(r"\w", previous_token)
                    and parenthesis_count == 0
                ):
                    last_found_function = previous_token
                    last_line = current_line
        if token == "typedef":
            typedefing = True
        # Check for various state changes
        if (
            multiline_commenting == False
            and singleline_commenting == False
            and stringing == False
        ):
            if token == "{":
                curly_count += 1
            elif token == "}":
                curly_count -= 1
            elif token == "(":
                parenthesis_count += 1
            elif token == ")":
                parenthesis_count -= 1
            elif token == "*" and previous_token == "/":
                multiline_commenting = True
            elif token == "/" and previous_token == "/":
                singleline_commenting = True
        else:
            if token == "/" and previous_token == "*":
                multiline_commenting = False
        # Store the previous token
        if stripped_token != "":
            previous_token = token

    # Sort the functions alphabetically
    def compare_function(item):
        return item[0].lower()

    function_list = sorted(function_list, key=compare_function)
    # Return the function list
    return function_list


def get_c_node_tree_with_ctags(c_code):
    # Node object
    class CNode:
        def __init__(
            self, in_name, in_type, in_line_number, in_level, in_parent=None
        ):
            self.name = in_name.strip()
            self.type = in_type
            self.line_number = in_line_number
            self.level = in_level
            self.parent = in_parent
            self.children = []

    #    # Ctags symbol dictionary
    #    ctags_description_string = """
    #        #LETTER NAME       ENABLED REFONLY NROLES MASTER DESCRIPTION
    #        L       label      no      no      0      C      goto labels
    #        d       macro      yes     no      1      C      macro definitions
    #        e       enumerator yes     no      0      C      enumerators (values inside an enumeration)
    #        f       function   yes     no      0      C      function definitions
    #        g       enum       yes     no      0      C      enumeration names
    #        h       header     yes     yes     2      C      included header files
    #        l       local      no      no      0      C      local variables
    #        m       member     yes     no      0      C      struct, and union members
    #        p       prototype  no      no      0      C      function prototypes
    #        s       struct     yes     no      0      C      structure names
    #        t       typedef    yes     no      0      C      typedefs
    #        u       union      yes     no      0      C      union names
    #        v       variable   yes     no      0      C      variable definitions
    #        x       externvar  no      no      0      C      external and forward variable declarations
    #        z       parameter  no      no      0      C      function parameters inside function definitions
    #    """
    #    c_symbols = dict(
    #        [(x.split()[0], x.split()[1])
    #            for x in ctags_description_string.splitlines()
    #                if x.strip() != ""][1:]
    #    )

    global ctags_program
    # Test for ctags on the system
    ctags_test = ("ctags_present" in locals()) or ("ctags_present" in globals())
    if ctags_test == False:
        global ctags_present
        ctags_present = False
        ctags_program = "ctags"
        try:
            if os_checker.is_os("windows"):
                output = subprocess_popen(
                    [ctags_program, "--version"],
                    stdout=subprocess.PIPE,
                    shell=False,
                ).communicate()[0]
            else:
                output = subprocess_popen(
                    [ctags_program, "--version"],
                    stdout=subprocess.PIPE,
                    shell=False,
                ).communicate()[0]
            output_utf = output.decode("utf-8", errors="ignore")
            if output_utf.startswith(
                "Exuberant Ctags"
            ) or output_utf.startswith("Universal Ctags"):
                ctags_present = True
        except Exception as ex:
            if os_checker.is_os("windows"):
                repl_print(
                    "Windows operating system detected.\n "
                    + "Using Universal Ctags program from the resources directory."
                )
                ctags_program = join_resources_dir_to_path("programs/ctags.exe")
                ctags_present = True
            else:
                repl_print(ex)
                ctags_present = False
                raise Exception(
                    "Exuberant or Universal Ctags (ctags) could not be found on the system!\n"
                    + "If you are using a Debian based operating system,\n"
                    + "try executing 'sudo apt-get install exuberant-ctags' to install Exuberant-Ctags."
                )
    # Create the file for parsing
    filename = "temporary_ctags_file.c"
    with open(filename, "w+", encoding="utf-8", newline="\n") as f:
        f.write(c_code)
        f.close()
    # Parse the file with ctags
    try:
        if os_checker.is_os("windows"):
            output = subprocess_popen(
                [
                    ctags_program,
                    "-R",
                    "--fields=-f-k-t+K+n",
                    "--excmd=number",
                    filename,
                ],
                stdout=subprocess.PIPE,
                shell=False,
            ).communicate()[0]
        else:
            output = subprocess_popen(
                [
                    ctags_program,
                    "-R",
                    "--fields=-f-k-t+K+n",
                    "--excmd=number",
                    filename,
                ],
                stdout=subprocess.PIPE,
                shell=False,
            ).communicate()[0]
        output_utf = output.decode("utf-8", errors="ignore")
    except Exception as ex:
        repl_print(ex)
        raise Exception("Parse error!")
    # Read the tag file
    lines = []
    try:
        tag_filename = "tags"
        with open(tag_filename, "r", newline="\n") as f:
            lines = f.readlines()
            f.close()
        # Delete the tag file
        os.remove(tag_filename)
    except Exception as ex:
        repl_print(ex)
        raise Exception("Tag file parse error!")
    # Initialize state variables
    main_node = CNode("module", "", 0, -1)
    main_node_list = []
    main_current_line = 1

    # Function for adding a node
    def add_node(in_node):
        if main_node is not None:
            main_node.children.append(in_node)
        else:
            main_node_list.append(in_node)

    main_node = CNode("module", "", 0, -1)
    # Parse the output
    for line in lines:
        if line.startswith("!_TAG"):
            continue
        split_line = line.split("\t")
        if len(split_line) == 5:
            name, file, ex_data, typ, line_number = split_line
            line_number = int(line_number.split(":")[1])
            add_node(CNode(name, typ, line_number, 0))
        elif len(split_line) == 6:
            name, file, ex_data, typ, line_number, parent = split_line
            line_number = int(line_number.split(":")[1])
            parent = parent.split(":")[1].strip()
            add_node(CNode(name, typ, line_number, 0, parent))
    # Delete the temporary parsing file
    os.remove(filename)

    # Sort the nodes alphabetically
    def compare_function(item):
        return item.name.lower()

    main_node_list = sorted(main_node_list, key=compare_function)
    main_node_list.append(main_node)
    return main_node_list


def get_c_node_tree(c_code):
    """THIS IS A WORK IN PROGRESS ROUTINE!!!

    IT IS IN A SOMEWHAT USABLE STATE.
    """

    # Node object
    class CNode:
        def __init__(
            self, in_name, in_type, in_line_number, in_level, in_parent=None
        ):
            self.name = in_name.strip()
            self.type = in_type
            self.line_number = in_line_number
            self.level = in_level
            self.parent = in_parent
            self.children = []

    # C keywords
    keywords = [
        "auto",
        "break",
        "case",
        "const",
        "continue",
        "default",
        "do",
        "else",
        "enum",
        "extern",
        "for",
        "goto",
        "if",
        "register",
        "return",
        "signed",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "unsigned",
        "volatile",
        "while",
        "pragma",
    ]
    composite_types = ["typedef", "union", "enum", "struct"]
    types = [
        "char",
        "double",
        "enum",
        "float",
        "int",
        "long",
        "short",
        "void",
        "auto",
        "static",
        "struct",
        "signed",
        "unsigned",
        "register",
        "extern",
    ]
    macros = ["define", "include", "pragma", "undef", "error"]
    skip_macros = ["if", "ifdef", "ifndef", "else", "endif"]
    """Parsing."""
    # Store the text
    text = c_code
    # Initialize state variables
    main_node = CNode("module", "", 0, -1)  # None
    main_current_line = 1
    main_node_list = [main_node]

    # Function for adding a node
    def add_node(in_node):
        if main_node is not None:
            main_node.children.append(in_node)
        else:
            main_node_list.append(in_node)

    # Debugging helpers
    def debug_print(level, *args, **kwargs):
        pass

    # Tokenize the text and remove the space characters
    #    splitter = re.compile(r"(\#\s*\w+|\'|\"|\n|\s+|\w+|\W)")
    splitter = re.compile(r"(\#\s*\w+|\n|\s+|\w+|\W)")
    main_tokens = [token for token in splitter.findall(text)]

    # Main parse function
    def parse_loop(tokens, node_list, current_line, index, level):
        curly_count = 0
        parenthesis_count = 0
        singleline_commenting = False
        multiline_commenting = False

        macroing = False
        macro_type = ""
        macro_tokens = []

        composite_0_typeing = False
        composite_1_typeing = False
        stringing = False
        charactering = False

        previous_token = ""
        last_found_function = ""
        last_line = 0
        current_line_tokens = []
        current_statement_tokens = []
        previous_unfiltered_token = None

        skip_to_token = None

        # Main Loop for filtering tokens
        for i, token in enumerate(tokens):
            stripped_token = token.strip()
            # Store the previous token
            if i > 0:
                previous_unfiltered_token = tokens[i - 1]
                if stripped_token != "":
                    previous_token = token
            else:
                previous_unfiltered_token = ""
                previous_token = ""
            # Store the next token
            if i < len(tokens) - 2:
                next_token = tokens[i + 1]
            else:
                next_token = ""

            if "\n" in token:
                # Increase the line counter
                newline_count = token.count("\n")
                current_line += newline_count

                # Reset the line token list
                current_line_tokens = []
                # Reset the single line comment and string flags
                singleline_commenting = False
                stringing = False

            if skip_to_token is not None:
                if skip_to_token >= i:
                    continue
                else:
                    skip_to_token = None

            # Check for various special characters
            if "\n" in token:
                if previous_unfiltered_token != "\\":
                    # Check the macro type
                    if macro_type == "include":
                        filtered_macro_tokens = []
                        previous_token = ""
                        for m in macro_tokens:
                            if (m == "*" and previous_token == "/") or (
                                m == "/" and previous_token == "/"
                            ):
                                filtered_macro_tokens = filtered_macro_tokens[
                                    :-2
                                ]
                                break
                            filtered_macro_tokens.append(m)
                            previous_token = m
                        include_string = "".join(filtered_macro_tokens)
                        debug_print(
                            level,
                            "Found include:\n",
                            (level + 1) * "    ",
                            include_string,
                        )
                        add_node(
                            CNode(include_string, "include", macro_line, 0)
                        )
                    elif macro_type == "define":
                        define_macro = macro_tokens[0]
                        debug_print(
                            level,
                            "Found define:\n",
                            (level + 1) * "    ",
                            define_macro,
                        )
                        add_node(CNode(define_macro, "define", macro_line, 0))
                    elif macro_type == "undef":
                        undef_macro = macro_tokens[0]
                        debug_print(
                            level,
                            "Found undef:\n",
                            (level + 1) * "    ",
                            undef_macro,
                        )
                        add_node(CNode(undef_macro, "undef", macro_line, 0))
                    elif macro_type == "pragma":
                        pragma_macro = macro_tokens[0]
                        # Watcom compiler 'aux' keyword check
                        if pragma_macro == "aux":
                            pragma_macro = macro_tokens[1]
                        debug_print(
                            level,
                            "Found pragma:\n",
                            (level + 1) * "    ",
                            pragma_macro,
                        )
                        add_node(CNode(pragma_macro, "pragma", macro_line, 0))
                    elif macro_type == "error":
                        error_macro = " ".join(macro_tokens)[:10] + "..."
                        debug_print(
                            level,
                            "Found error:\n",
                            (level + 1) * "    ",
                            error_macro,
                        )
                        add_node(CNode(error_macro, "error", macro_line, 0))
                    # Reset the macroing flag
                    macro_tokens = []
                    macroing = False
                    macro_type = ""

            # Check for an empty token
            if stripped_token == "":
                previous_unfiltered_token = stripped_token
                continue

            if multiline_commenting == True:
                if token == "/" and previous_token == "*":
                    multiline_commenting = False
            elif singleline_commenting == True:
                pass
            elif macroing == True:
                macro_tokens.append(token)
            elif stringing == True:
                if token == '"' and previous_token != "\\":
                    stringing = False
            elif charactering == True:
                if token == "'" and previous_token != "\\":
                    charactering = False
            else:
                current_line_tokens.append(token)

                if token == "*" and previous_unfiltered_token == "/":
                    current_statement_tokens = current_statement_tokens[:-1]
                    multiline_commenting = True
                elif token == "/" and previous_unfiltered_token == "/":
                    current_statement_tokens = current_statement_tokens[:-1]
                    singleline_commenting = True
                elif token == '"':
                    stringing = True
                elif token == "'":
                    charactering = True
                elif token == ";":
                    current_statement_tokens.append(token)
                    first_word = current_statement_tokens[0]
                    if first_word in composite_types:
                        type_desc = first_word
                        if current_statement_tokens[-2].isidentifier():
                            type_name = current_statement_tokens[-2]
                        elif current_statement_tokens[
                            1
                        ].isidentifier() and not (
                            current_statement_tokens[1] in keywords
                        ):
                            type_name = current_statement_tokens[1]
                        else:
                            for t in current_statement_tokens:
                                if t.startswith("( *"):
                                    type_name = t[3:-2]
                                    break
                            else:
                                raise Exception(
                                    "'{}' (line:{}) has not known name! ({})".format(
                                        type_desc,
                                        current_line,
                                        current_statement_tokens,
                                    )
                                )
                        body_test = (
                            current_statement_tokens[-2] == "{ ... }"
                            or current_statement_tokens[-3] == "{ ... }"
                        )
                        if type_name.isidentifier() and body_test:
                            debug_print(
                                level,
                                "Found {}:\n".format(type_desc),
                                (level + 1) * "    ",
                                type_name,
                            )
                            add_node(
                                CNode(type_name, type_desc, current_line, 0)
                            )
                    else:

                        def parse_funcs(in_list, pos=0):
                            if in_list is None:
                                return
                            return_list = []
                            for i, item in enumerate(in_list):
                                if item.strip() == "":
                                    continue
                                elif item.startswith("("):
                                    try:
                                        if in_list[
                                            i - 1
                                        ].isidentifier() and not (
                                            in_list[i - 1] in keywords
                                        ):
                                            func = return_list.pop()
                                            return_list.append(func + item)
                                    except:
                                        return_list.append(item)
                                else:
                                    return_list.append(item)
                            return return_list

                        try:
                            result = parse_funcs(current_statement_tokens)
                            #                            print(result)
                            length = len(result)
                            if (
                                "(" in result[-2]
                                and ")" in result[-2]
                                and not ("=" in result[-2])
                                and level == 0
                                and result[-2][
                                    : result[-2].find("(")
                                ].isidentifier()
                            ):
                                name = current_statement_tokens[-3]
                                if (
                                    "(" in name
                                    and ")" in name
                                    and name[2] == "*"
                                ):
                                    prototype = name[3:-1]
                                else:
                                    prototype = result[-2][
                                        : result[-2].find("(")
                                    ]
                                add_node(
                                    CNode(
                                        prototype, "prototype", current_line, 0
                                    )
                                )
                                debug_print(
                                    level,
                                    "Found prototype 0:\n",
                                    (level + 1) * "    ",
                                    prototype,
                                )
                            elif length == 3:
                                if (
                                    "(" in result[1]
                                    and ")" in result[1]
                                    and (level == 0)
                                ):
                                    prototype = result[1][: result[1].find("(")]
                                    add_node(
                                        CNode(
                                            prototype,
                                            "prototype",
                                            current_line,
                                            0,
                                        )
                                    )
                                    debug_print(
                                        level,
                                        "Found prototype 1:\n",
                                        (level + 1) * "    ",
                                        prototype,
                                    )
                                elif (
                                    result[1].isidentifier()
                                    and not ("=" in result)
                                    and (level == 0)
                                ):
                                    variable = result[1]
                                    add_node(
                                        CNode(variable, "var", current_line, 0)
                                    )
                                    debug_print(
                                        level,
                                        "Found variable 0:\n",
                                        (level + 1) * "    ",
                                        variable,
                                    )
                                else:
                                    pass
                            elif "," in result:
                                # Multiple variable declarations delimited with ','
                                if level == 0:
                                    groups = []
                                    current_group = []
                                    for t in result:
                                        if t == "," or t == ";":
                                            groups.append(current_group)
                                            current_group = []
                                        else:
                                            current_group.append(t)
                                    for g in groups:
                                        if "=" in g:
                                            equal_index = g.index("=")
                                            var_name = g[equal_index - 1]
                                        else:
                                            if ("[" in g) and ("]" in g):
                                                open_index = g.index("[")
                                                var_name = g[open_index - 1]
                                            else:
                                                var_name = g[-1]
                                        if var_name.isidentifier():
                                            add_node(
                                                CNode(
                                                    var_name,
                                                    "var",
                                                    current_line,
                                                    0,
                                                )
                                            )
                                            debug_print(
                                                level,
                                                "Found variable 1:\n",
                                                (level + 1) * "    ",
                                                var_name,
                                            )
                            elif (
                                result[-2].isidentifier()
                                and not ("=" in result)
                                and (level == 0)
                            ):
                                variable = result[-2]
                                add_node(
                                    CNode(variable, "var", current_line, 0)
                                )
                                debug_print(
                                    level,
                                    "Found variable 2:\n",
                                    (level + 1) * "    ",
                                    variable,
                                )
                            elif (
                                "=" in result
                                and result[result.index("=") - 1].isidentifier()
                                and (level == 0)
                            ):
                                variable = result[result.index("=") - 1]
                                add_node(
                                    CNode(variable, "var", current_line, 0)
                                )
                                debug_print(
                                    level,
                                    "Found variable 3:\n",
                                    (level + 1) * "    ",
                                    variable,
                                )
                            elif (
                                ("[" in result)
                                and ("]" in result)
                                and result[result.index("[") - 1].isidentifier()
                                and (level == 0)
                            ):
                                variable = result[result.index("[") - 1]
                                add_node(
                                    CNode(variable, "var", current_line, 0)
                                )
                                debug_print(
                                    level,
                                    "Found array variable:\n",
                                    (level + 1) * "    ",
                                    variable,
                                )
                            else:
                                pass
                        except Exception as ex:
                            debug_print(
                                level - 1,
                                "**** UNKNOWN NODE ****",
                                current_line,
                                i + index,
                            )

                    current_statement_tokens = []
                elif "#" in token and any(x for x in macros if x in token):
                    macroing = True
                    macro_type = token.replace("#", "").strip()
                    macro_line = current_line
                    macro_tokens = []
                elif "#" in token and any(x for x in skip_macros if x in token):
                    # Skip macros that do nothing
                    macroing = True
                elif (
                    token == "{" and previous_token != "'" and next_token != "'"
                ):
                    try:
                        func_found = False
                        if current_statement_tokens[-1] == "( ... )" or (
                            current_statement_tokens[-1].startswith("(")
                            and current_statement_tokens[-1].endswith(")")
                        ):
                            func_name = current_statement_tokens[-2]
                            if func_name.isidentifier() and not (
                                func_name in keywords
                            ):
                                add_node(
                                    CNode(
                                        func_name, "function", current_line, 0
                                    )
                                )
                                debug_print(
                                    level,
                                    "Found function:\n",
                                    (level + 1) * "    ",
                                    func_name,
                                )
                                func_found = True
                    except:
                        pass
                    if func_found == False and not (
                        any(
                            x in composite_types
                            for x in current_statement_tokens
                        )
                    ):
                        next_level = level
                    else:
                        next_level = level + 1
                    # Start of a block
                    debug_print(level, "{ ", current_statement_tokens)
                    if func_found:
                        debug_print(
                            level,
                            "function start '{}':".format(func_name),
                            "level:",
                            next_level,
                            i,
                        )
                    node_list, skip_to_token = parse_loop(
                        tokens[i + 1 :],
                        node_list,
                        current_line,
                        i + 1,
                        next_level,
                    )
                    current_statement_tokens.append("{ ... }")
                    if func_found:
                        debug_print(
                            level,
                            "function end '{}':".format(func_name),
                            skip_to_token,
                        )
                        current_statement_tokens = []
                elif (
                    token == "}" and previous_token != "'" and next_token != "'"
                ):
                    return node_list, i + index
                #                elif token == ')' and previous_token != '\'' and next_token != '\'':
                #                    debug_print(level-1, ')', current_line, i+index)
                #                    return node_list, i+index
                elif (
                    token == "(" and previous_token != "'" and next_token != "'"
                ):
                    #                    repl_print(previous_token, token, next_token, tokens[i+2], tokens[i+3], tokens[i+4], tokens[i+5], tokens[i+6], tokens[i+7])
                    #                    repl_print(tokens[i+1],tokens[i+2],tokens[i+3],tokens[i+4],tokens[i+5])
                    paren_tokens = ["("]
                    paren_count = 0
                    skip_to_token = i
                    function_flag = False
                    previous_t = None
                    next_t = None
                    for j, t in enumerate(tokens[i + 1 :]):
                        print(paren_count)
                        skip_to_token += 1
                        paren_tokens.append(t)
                        if j > 0:
                            previous_t = tokens[i + 1 :][j - 1]
                        if j < len(tokens[i + 1 :]) - 1:
                            next_t = tokens[i + 1 :][j + 1]
                        if t == "(" and previous_t != "'" and next_t != "'":
                            paren_count += 1
                        if t == ")" and previous_t != "'" and next_t != "'":
                            if paren_count == 0:
                                #                                repl_print(previous_t, t, next_t)
                                try:
                                    tks = tokens[i + 1 :]
                                    for k in range(3):
                                        if "{" in tks[j + 1 + k].strip():
                                            function_flag = True
                                            break
                                except:
                                    pass
                                break
                            else:
                                paren_count -= 1
                    if paren_tokens[1] == "*" and function_flag == False:
                        current_statement_tokens.append(
                            "( {} )".format("".join(paren_tokens[1:-1]))
                        )
                    elif (
                        len(paren_tokens) > 4
                        and paren_tokens[-3] == "*"
                        and paren_tokens[-2].isidentifier()
                        and not ("," in "".join(paren_tokens))
                        and function_flag == False
                    ):
                        current_statement_tokens.append(
                            "( {} )".format("".join(paren_tokens[-3:-1]))
                        )
                    else:
                        current_statement_tokens.append("( ... )")
                    continue
                else:
                    current_statement_tokens.append(token)

        # Return the accumulated node list
        return node_list, skip_to_token

    main_node_list, skip_to_token = parse_loop(
        main_tokens, main_node_list, main_current_line, 0, 0
    )

    # Sort the nodes alphabetically
    def compare_function(item):
        return item.name.lower()

    main_node_list = sorted(main_node_list, key=compare_function)
    return main_node_list


def get_file_text(file_path):
    if not os.path.isfile(file_path):
        raise Exception(f"File '{file_path}' is missing!")
    with open(file_path, "r", newline="\n") as f:
        text = f.read()
        f.close()
    return text


def get_file_line_endings(file_path_or_text):
    line_endings = "\n"
    if os.path.isfile(file_path_or_text):
        # @Kristof
        if file_path_or_text.endswith(".a"):
            # Archive file => Do not open the file, just return '\n'.
            printc(
                "WARNING: functions.py => Attempt to read line "
                "endings from archive file!",
                color="warning",
            )
            return line_endings
        with open(file_path_or_text, "rb") as file:
            text = file.read()
            file.close()
    else:
        text = file_path_or_text.encode("utf-8")
    if b"\r\n" in text:
        line_endings = "\r\n"
    elif b"\r" in text:
        line_endings = "\r"
    return line_endings


def remove_comments(layout):
    line_endings = get_file_line_endings(layout)
    if line_endings != "\n":
        layout = layout.replace(line_endings, "\n")
    lines = layout.split("\n")
    new_lines = []
    for l in lines:
        if not l.strip().startswith("#"):
            new_lines.append(l)
    return "\n".join(new_lines)


def get_file_scintilla_line_endings(file_with_path):
    line_endings = get_file_line_endings(file_with_path)
    scintilla_line_endings = qt.QsciScintilla.EolMode.EolUnix
    if line_endings == "\r\n":
        scintilla_line_endings = qt.QsciScintilla.EolMode.EolWindows
    elif line_endings == "\r":
        scintilla_line_endings = qt.QsciScintilla.EolMode.EolMac
    return scintilla_line_endings


def check_line_endings(file_path):
    # Check that a file's line endings are Unix ('\n')
    line_endings = get_file_line_endings(file_path)
    if line_endings != "\n":
        with open(file_path, "rb+") as file:
            text = file.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            file.seek(0)
            file.write(text)
            file.truncate()
            file.close()
        return True
    else:
        return False


def test_file_content_for_type(file_with_path):
    """Test the first line of a file for relevant file type data."""
    # @Kristof
    if file_with_path.endswith(".a") or file_with_path.endswith(".o"):
        return "none"
    file_type = "none"
    try:
        first_line = ""
        # Read the first non-empty line in the file
        with open(file_with_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.strip() == "":
                    continue
                else:
                    first_line = line
                    break
        # Prepare the line
        first_line = first_line.lower().strip()
        # Check the line content
        if "<?xml" in first_line:
            file_type = "xml"
        elif "#!" in first_line and "python" in first_line:
            file_type = "python"
        elif "#!" in first_line and "perl" in first_line:
            file_type = "perl"
        elif "#!" in first_line and "ruby" in first_line:
            file_type = "ruby"
        elif (
            ("#!" in first_line and "bash" in first_line)
            or ("#!" in first_line and "dash" in first_line)
            or ("#!" in first_line and "sh" in first_line)
        ):
            file_type = "bash"
        # Return the file type
        return file_type
    except:
        # Error reading the file
        return file_type


def read_file_to_string(file_with_path):
    """Read contents of a text file to a single string."""
    # Test if a file is in binary format
    binary_text = test_binary_file(file_with_path)
    if binary_text is not None:
        cleaned_binary_text = binary_text.replace(b"\x00", b"")
        return cleaned_binary_text.decode(encoding="utf-8", errors="replace")
    else:
        # File is not binary, loop through encodings to find the correct one.
        # Try the default embeetle encoding UTF-8 first
        test_encodings = [
            #            "gb2312",
            "utf-8",
            "cp1250",
            "ascii",
            "utf-16",
            "utf-32",
            "iso-8859-1",
            "latin-1",
        ]
        for current_encoding in test_encodings:
            try:
                # If opening the file in the default embeetle encoding fails,
                # open it using the prefered system encoding!
                with open(
                    file_with_path,
                    "r",
                    encoding=current_encoding,
                    #                          errors="strict",
                    errors="surrogateescape",
                    newline="",
                ) as file:
                    # Read the whole file with "read()"
                    text = file.read()
                    # Close the file handle
                    file.close()
                # Return the text string
                return text
            except:
                # Error occured while reading the file, skip to next encoding
                continue
    # Error, no encoding was correct
    return None


def read_binary_file_as_generator(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.

    Default chunk size: 1k.
    """
    while True:
        _data = file_object.read(chunk_size)
        if not _data:
            break
        yield _data


def read_file_to_list(file_with_path):
    """Read contents of a text file to a list."""
    text = read_file_to_string(file_with_path)
    if text is not None:
        return text.split("\n")
    else:
        return None


def write_to_file(text, file_with_path, encoding="utf-8"):
    """Write text to a file."""
    # Again, the forgiveness principle
    try:
        # Encode the file to the selected encoding
        if encoding != "utf-8":
            # Convert UTF-8 string into a byte array
            byte_string = bytearray(text, encoding=encoding, errors="replace")
            # Convert the byte array into the desired encoding, none
            # characters will be displayed as question marks or something similar
            text = codecs.decode(byte_string, encoding, "replace")
        # Open the file for writing, create it if it doesn't exists
        with open(file_with_path, "w", newline="\n", encoding=encoding) as file:
            # Write text to the file
            file.write(text)
            # Close the file handle
            file.close()
        # Writing to file succeded
        return True
    except Exception as ex:
        # Wrtiting to file failed, return error message
        return ex


def list_character_positions(string, character):
    """Return a list of positions of all the instances of character in a
    string."""
    return [i for i, char in enumerate(string) if char == character]


def index_strings_in_linelist(search_text, list_of_lines, case_sensitive=False):
    """Return all instances of the searched text in the list of lines as a list
    of tuples(line, match_start_position, line, match_end_position).

    Line numbers are 0-to-(len(list_of_lines)-1)
    """
    list_of_matches = []
    if case_sensitive == True:
        compiled_search_re = re.compile(re.escape(search_text))
    else:
        compiled_search_re = re.compile(re.escape(search_text), re.IGNORECASE)
    # Check for and extend the list with all matches
    for i, line in enumerate(list_of_lines):
        line_matches = [
            (i, match.start(), i, match.end())
            for match in re.finditer(compiled_search_re, line)
        ]
        list_of_matches.extend(line_matches)
    return list_of_matches


def index_strings_in_text(
    search_text: str,
    text: str,
    case_sensitive: bool = False,
    regular_expression: bool = False,
    text_to_bytes: bool = False,
    whole_words: bool = False,
    line_by_line: bool = False,
) -> List[Tuple]:
    """Return all instances of the searched text in the text string as a list of
    tuples(0, match_start_position, 0, match_end_position).
    """
    # Build regex pattern efficiently
    if whole_words:
        if regular_expression:
            # For regex with whole words, wrap with word boundaries
            pattern = rf"\b(?:{search_text})\b"
        else:
            # Escape the search text and wrap with word boundaries
            pattern = rf"\b{re.escape(search_text)}\b"
    else:
        if regular_expression:
            pattern = search_text
        else:
            pattern = re.escape(search_text)

    # Handle byte conversion if needed
    if text_to_bytes:
        # Convert pattern and text to bytes
        pattern_bytes = pattern.encode("utf-8")
        text_target = text.encode("utf-8")
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_search_re = re.compile(pattern_bytes, flags)
    else:
        # Keep as strings
        text_target = text
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_search_re = re.compile(pattern, flags)

    if line_by_line:
        # Pre-split text once instead of in loop
        if text_to_bytes:
            lines = text_target.split(b"\n")
        else:
            lines = text_target.split("\n")

        list_of_matches = []
        append_match = list_of_matches.append  # Cache method lookup

        for i, line in enumerate(lines):
            # Skip empty lines early
            if not line:
                continue

            # Decode line for context display (always need string for context)
            line_decoded = line.decode("utf-8") if text_to_bytes else line
            line_len = len(line_decoded)

            for match in compiled_search_re.finditer(line):
                st = match.start()
                en = match.end()

                # Calculate context efficiently
                line_st = max(0, st - 20)
                line_en = min(line_len, en + 20)

                # Build context string with proper quotes
                prefix = "'..." if line_st > 0 else "'"
                suffix = "...'" if line_en < line_len else "'"

                context = prefix + line_decoded[line_st:line_en] + suffix
                append_match((i, st, i, en, context))

        return list_of_matches
    else:
        # Simple case: return basic matches
        return [
            (0, match.start(), 0, match.end())
            for match in compiled_search_re.finditer(text_target)
        ]


def index_strings_in_files(
    search_text: str,
    search_directory: str,
    case_sensitive: bool = False,
    regular_expression: bool = False,
    text_to_bytes: bool = False,
    whole_words: bool = False,
    exclude_directories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if exclude_directories is None:
        exclude_directories = []

    # Pre-compute excluded directory paths as sets for O(1) lookup
    search_directory_unix = unixify_path(search_directory)
    full_exclude_directories = {
        unixify_path_join(search_directory_unix, x) for x in exclude_directories
    }

    results = {}

    # Use os.scandir instead of os.walk for better performance
    def scan_directory(current_path: str) -> None:
        try:
            with os.scandir(current_path) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        dir_path = unixify_path(entry.path)
                        # Check if this directory should be excluded
                        should_skip = any(
                            dir_path.startswith(excluded)
                            for excluded in full_exclude_directories
                        )
                        if not should_skip:
                            scan_directory(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        file_path = unixify_path(entry.path)
                        # Skip binary files early
                        if filefunctions.is_binary_by_extension(file_path):
                            continue
                        if filefunctions.is_binary_file(file_path):
                            continue

                        try:
                            with open(
                                file_path,
                                "r",
                                encoding="utf-8",
                                errors="replace",
                                buffering=8192,
                            ) as f:
                                text = f.read()

                            list_of_matches = index_strings_in_text(
                                search_text,
                                text,
                                case_sensitive=case_sensitive,
                                regular_expression=regular_expression,
                                text_to_bytes=True,
                                line_by_line=True,
                            )

                            if list_of_matches:
                                results[file_path] = list_of_matches

                        except (OSError, UnicodeDecodeError):
                            continue
        except (OSError, PermissionError):
            pass

    scan_directory(search_directory_unix)

    # Build tree structure correctly
    tree_results = {
        "path": search_directory_unix,
        "search-text": search_text,
        "directories": {},
        "files": {},
    }

    # Ensure search directory ends with '/' for consistent path operations
    if search_directory_unix and not search_directory_unix.endswith("/"):
        search_directory_unix += "/"

    for path, matches in results.items():
        # Calculate relative path
        if path.startswith(search_directory_unix):
            rel_path = path[len(search_directory_unix) :]
        else:
            # Fallback for edge cases
            rel_path = os.path.relpath(
                path, search_directory_unix.rstrip("/")
            ).replace("\\", "/")
            if rel_path.startswith("../"):
                continue  # Skip files outside search directory

        if not rel_path or "/" not in rel_path:
            # File is directly in the search directory
            filename = rel_path if rel_path else os.path.basename(path)
            if filename:  # Avoid empty filenames
                tree_results["files"][filename] = matches
        else:
            # File is in subdirectory - build the directory tree
            parts = rel_path.split("/")
            current_node = tree_results

            # Build directory structure incrementally
            current_path_parts = []
            for i, dir_part in enumerate(parts[:-1]):
                current_path_parts.append(dir_part)
                # Build full path for this directory using unixify_path_join or manual join
                full_dir_path = search_directory_unix + "/".join(
                    current_path_parts
                )
                # Remove trailing slash if present (except for root)
                full_dir_path = full_dir_path.rstrip("/")

                if dir_part not in current_node["directories"]:
                    current_node["directories"][dir_part] = {
                        "path": full_dir_path,
                        "directories": {},
                        "files": {},
                    }
                current_node = current_node["directories"][dir_part]

            # Add the file to the final directory
            filename = parts[-1]
            if filename:  # Avoid empty filenames
                current_node["files"][filename] = matches

    return tree_results


def check_unmatched_quotes(string):
    """Check if there are unmatched single/double quotes in the text and return
    the position of the last unmatched quote character."""
    # Define locals
    found_single = False
    found_double = False
    last_quote_position = None
    # Loop through all the characters in the string
    for i, ch in enumerate(string):
        # Check for a double quote
        if ch == '"':
            if found_double == False and found_single == False:
                # Save state that the quote was found
                found_double = True
                # Save quote position
                last_quote_position = i
            elif found_double == True:
                # Reset quote state
                found_double = False
                last_quote_position = None
        # Check for a single quote
        elif ch == "'":
            if found_single == False and found_double == False:
                # Save state that the quote was found
                found_single = True
                # Save quote position
                last_quote_position = i
            elif found_single == True:
                # Reset quote state
                found_single = False
                last_quote_position = None
    # Return the last unclosed quote position
    return last_quote_position


def is_number(string):
    """Check if the string is a number (integer or float)"""
    try:
        float(string)
        return True
    except ValueError:
        return False


def is_header_file(path):
    try:
        directory, filename = os.path.split(path)
        filename = filename.lower()
        if any(
            [filename.endswith(x) for x in data.VALID_HEADER_FILE_EXTENSIONS]
        ):
            return True
        return False
    except:
        traceback.print_exc()
        return False


def replace_and_index(
    input_string,
    search_text,
    replace_text,
    case_sensitive=False,
    regular_expression=False,
):
    """Function that replaces the search text with replace text in a string,
    using regular expressions if specified, and returns the line numbers and
    indexes of the replacements as a list."""
    # First check if the replacement action is needed
    if search_text == replace_text and case_sensitive == True:
        return None, input_string
    elif (
        search_text.lower() == replace_text.lower() and case_sensitive == False
    ):
        return None, input_string
    # Initialize the return variables
    replaced_text = None
    # Find the search text matches that will be highlighted (pre-replacement)
    # Only when not searching with regular expressions
    if regular_expression == False:
        matches = index_strings_in_text(
            search_text,
            input_string,
            case_sensitive,
            regular_expression,
            text_to_bytes=True,
        )
    # Create a matches list according to regular expression selection
    if regular_expression == True:
        # Compile the regular expression object according to the case sensitivity
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        # Replace all instances of search text with the replace text
        replaced_text = re.sub(compiled_search_re, replace_text, input_string)
        replaced_match_indexes = []
        # Split old and new texts into line lists
        split_input_text = input_string.split("\n")
        split_replaced_text = replaced_text.split("\n")
        # Loop through the old text and compare it line-by-line to the old text
        try:
            for i in range(len(split_input_text)):
                if split_input_text[i] != split_replaced_text[i]:
                    replaced_match_indexes.append(i)
        except:
            # If regular expression replaced lines,
            # then we cannot highlight the replacements
            replaced_match_indexes = []
    else:
        replaced_text = None
        if case_sensitive == True:
            # Standard string replace
            replaced_text = input_string.replace(search_text, replace_text)
        else:
            # Escape the regex special characters
            new_search_text = re.escape(search_text)
            # Replace backslashes with double backslashes, so that the
            # regular expression treats backslashes the same as standard
            # Python string replace!
            new_replace_text = replace_text.replace("\\", "\\\\")
            compiled_search_re = re.compile(new_search_text, re.IGNORECASE)
            replaced_text = re.sub(
                compiled_search_re, new_replace_text, input_string
            )
        replaced_match_indexes = []
        # Loop while storing the new indexes
        diff = 0
        bl_search = bytes(search_text, "utf-8")
        bl_search = len(bl_search.replace(b"\\", b" "))
        bl_replace = bytes(replace_text, "utf-8")
        bl_replace = len(bl_replace.replace(b"\\", b" "))
        for i, match in enumerate(matches):
            # Subtract the length of the search text from the match index,
            # to offset the shortening of the whole text when the lenght
            # of the replace text is shorter than the search text
            diff = (bl_replace - bl_search) * i
            new_index = match[1] + diff
            # Check if the index correction went into a negative index
            if new_index < 0:
                new_index = 0
            # The line is always 0, because Scintilla also allows
            # indexing over multiple lines! If the index number goes
            # over the length of a line, it "overflows" into the next line.
            # Basically this means that you can access any line/index by
            # treating the whole text not as a list of lines, but as an array.
            replaced_match_indexes.append(
                (0, new_index, 0, new_index + bl_replace)
            )
    # Return the match list and the replaced text
    return replaced_match_indexes, replaced_text


def regex_replace_text(
    input_string,
    search_text,
    replace_text,
    case_sensitive=False,
    regular_expression=False,
):
    """Function that uses the re module to replace text in a string."""
    replaced_text = None
    if regular_expression == True:
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        replaced_text = re.sub(compiled_search_re, replace_text, input_string)
    else:
        if case_sensitive == True:
            replaced_text = input_string.replace(search_text, replace_text)
        else:
            #'re.escape' replaces the re module special characters with literals,
            # so that the search_text is treated as a string literal
            compiled_re = re.compile(re.escape(search_text), re.IGNORECASE)
            replaced_text = re.sub(compiled_re, replace_text, input_string)
    return replaced_text


def is_config_file(file_with_path):
    file_with_path = file_with_path.replace("\\", "/")
    if os.path.isfile(file_with_path) == False:
        return False
    file = os.path.basename(file_with_path)
    path = os.path.dirname(file_with_path)
    data.config_filename = data.config_filename.replace("\\", "/")
    data.user_directory = data.user_directory.replace("\\", "/")
    if file == data.config_filename and path == data.user_directory:
        return True
    else:
        return False


def create_default_config_file():
    user_definitions_file = os.path.join(
        data.settings_directory, data.config_filename
    )
    with open(user_definitions_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(data.default_config_file_content)
        f.close()


def get_line_indentation(line):
    """Function for determining the indentation level of a line string."""
    indentation = 0
    for char in line:
        if char == " ":
            indentation += 1
        else:
            break
    return indentation


def get_file_list(path, extensions=None):
    """Function for getting a flat list of all files in a directory."""
    file_list = []
    if extensions is not None:
        for root, dirs, files in os.walk(path):
            for f in files:
                extension = os.path.splitext(f)[1]
                if extension in extensions:
                    found_file = os.path.join(root, f)
                    found_file = unixify_path(found_file)
                    file_list.append(found_file)
    else:
        for root, dirs, files in os.walk(path):
            for f in files:
                found_file = os.path.join(root, f)
                found_file = unixify_path(found_file)
                file_list.append(found_file)
    return file_list


def get_cursor_position(widget) -> qt.QPoint:
    current_screen = get_widget_screen(widget)
    cursor_position = qt.QCursor.pos() - current_screen.geometry().topLeft()
    return cursor_position


def get_widget_screen(widget) -> qt.QScreen:
    screens = data.application.screens()
    for s in screens:
        window_handle = data.main_form.windowHandle()
        if window_handle is not None:
            if s is window_handle.screen():
                return s
    raise Exception("Could not find widget's ('{}') screen!".format(widget))


def get_widget_screen_index(widget) -> int:
    screens = data.application.screens()
    for i, s in enumerate(screens):
        window_handle = data.main_form.windowHandle()
        if window_handle is not None:
            if s is window_handle.screen():
                return i
    raise Exception(
        "Could not find widget's ('{}') screen index!".format(widget)
    )


def get_screen_data() -> dict:
    return {
        "NUMBER-OF-SCREENS": len(data.application.screens()),
        "SCREEN-RESOLUTIONS": [
            [s.size().width(), s.size().height()]
            for s in data.application.screens()
        ],
    }


def get_screen_size() -> qt.QSize:
    """"""
    try:
        if data.main_form is not None:
            screens = data.application.screens()
            for i, s in enumerate(screens):
                window_handle = data.main_form.windowHandle()
                if window_handle is not None:
                    if s is window_handle.screen():
                        return s.size()
            else:
                return data.application.primaryScreen().size()
        else:
            return data.application.primaryScreen().size()
    except:
        traceback.print_exc()
        return data.application.primaryScreen().size()


def get_desktop_size() -> Tuple[int, int]:
    """"""
    size = data.application.primaryScreen().size()
    return size.width(), size.height()


def check_size(widget):
    # Function is a NOP as it messes with multiple screen sizing
    limit_factor = 1.00
    screens = data.application.screens()
    for i, s in enumerate(screens):
        if s is data.main_form.windowHandle().screen():
            geometry = s.geometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
            width = widget.width()
            height = widget.height()
            resize_needed = False
            if width > (screen_width * limit_factor):
                width = screen_width - (screen_width * 0.98)
                resize_needed = True
            if height > (screen_height * limit_factor):
                height = screen_height - (screen_height * 0.98)
                resize_needed = True
            if resize_needed:
                widget.resize(int(width), int(height))
            break


def center_to_current_screen(widget):
    screen = None
    screens = data.application.screens()
    if data.main_form is not None and data.main_form.windowHandle() is not None:
        for i, s in enumerate(screens):
            if s is data.main_form.windowHandle().screen():
                screen = s
                break
    else:
        screen = widget.screen()

    if screen is not None:
        geometry = screen.geometry()
        left = geometry.left()
        top = geometry.top()
        offset_width = (geometry.width() / 2) - (widget.width() / 2)
        offset_height = (geometry.height() / 2) - (widget.height() / 2)
        center = qt.create_qpoint(left + offset_width, top + offset_height)

        def move(*args):
            widget.move(center - qt.create_qpoint(0, 50))  # Manual offset

        qt.QTimer.singleShot(0, move)


def center_to_main_screen(widget):
    widget.move(
        data.application.primaryScreen().rect().center()
        - widget.rect().center()
        - qt.create_qpoint(0, 50)  # Manual offset
    )
    return


def center_rectangle_to_widget(widget, widget_window, size, offset=(0, 0)):
    rect = widget.geometry()
    window_position = widget_window.mapToGlobal(rect.topLeft())
    widget_position = widget.mapToGlobal(rect.topLeft())
    position = widget_position - window_position
    # Center the rectangle to the widget
    position = (
        position.x() + ((rect.width() - size[0]) / 2) + offset[0],
        position.y() + ((rect.height() - size[1]) / 2) + offset[1],
    )
    return position


def get_edges_to_widget(widget, widget_window, size, offset=(0, 0)):
    rect = widget.geometry()
    window_position = widget_window.mapToGlobal(rect.topLeft())
    widget_position = widget.mapToGlobal(rect.topLeft())
    position = widget_position - window_position
    # Center the rectangle to the widget
    center = (
        position.x() + ((rect.width() - size[0]) / 2) + offset[0],
        position.y() + ((rect.height() - size[1]) / 2) + offset[1],
    )
    left = (center[0] - (rect.width() / 2) + (size[0] / 2), center[1])
    right = (center[0] + (rect.width() / 2) - (size[0] / 2), center[1])
    top = (center[0], center[1] - (rect.height() / 2) + (size[1] / 2))
    bottom = (center[0], center[1] + (rect.height() / 2) - (size[1] / 2))
    return (center, left, right, top, bottom)


def get_last_directory_from_path(directory):
    return os.path.basename(os.path.normpath(directory))


def get_text_bounding_rect(text, custom_font=None):
    font = data.get_general_font()
    if custom_font is not None:
        font = custom_font
    fm = qt.QFontMetrics(font)
    br = fm.boundingRect(text)
    return br


def get_text_width(text):
    font = data.get_general_font()
    fm = qt.QFontMetrics(font)
    width = fm.horizontalAdvance(text)
    return width


def get_separator(text):
    separator = "\n"
    if "\r\n" in text:
        separator = "\r\n"
    elif "\r" in text:
        separator = "\r"
    return separator


def is_pathname_valid(pathname: str) -> bool:
    """`True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise."""
    # Sadly, Python fails to provide the following magic number for us.
    ERROR_INVALID_NAME = 123
    """Windows-specific error code indicating an invalid pathname.

    See Also
    ----------
    https://msdn.microsoft.com/en-us/library/windows/desktop/ms681382%28v=vs.85%29.aspx
        Official listing of all such codes.
    """
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's windows-specific drive specifier (e.g., `C:\`)
        # if any. Since windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is windows, this is
        # the drive to which windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = (
            os.environ.get("HOMEDRIVE", "C:")
            if os_checker.is_os("windows")
            else os.path.sep
        )
        assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            # Only the following exceptions indicate invalid pathnames:
            # * Instances of the windows-specific "windowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, "winerror"):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError as exc:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    # Did we mention this should be shipped with Python already?


def get_line_from_offset(filename, offset):
    line = None
    line_number = None
    with open(filename, "rb") as f:
        # Line number
        text = f.read(offset)
        line_number = text.count(b"\n") + 1
        # Line text from offset
        f.seek(offset)
        line_from_offset = f.readline().decode("utf-8", errors="replace")
        # Whole line text
        f.seek(0)
        line = f.readlines()[line_number - 1].decode("utf-8", errors="replace")
        # Close file
        f.close()

    return line_number, line, line_from_offset


def get_line_from_line_number(filename, line_number, column):
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        # Whole line text
        line = f.readlines()[line_number]
        # Line text from offset
        line_from_offset = line[column:]
        # Close file
        f.close()

    return line, line_from_offset


"""
Docking system helpers
"""


def right_replace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def remove_last_box(name):
    split = name.split(".")
    return ".".join(split[:-1])


def remove_tabs_from_name(name):
    return name[: name.index(".Tabs")]


def remove_tab_number_from_name(name):
    tabs_string = ".Tabs"
    return name[: (name.index(tabs_string) + len(tabs_string))]


"""
License
"""


def license_agreement_check():
    file_path = user_file_path = os.path.join(
        data.settings_directory, data.license_agreement_filename
    )
    return os.path.isfile(file_path)


def license_agreement_create():
    file_path = user_file_path = os.path.join(
        data.settings_directory, data.license_agreement_filename
    )
    license_text = get_license_text()
    with open(file_path, "w+", encoding="utf-8", newline="\n") as f:
        f.write(license_text)
        f.close()


def get_license_text():
    license_path = unixify_path_join(
        data.beetle_licenses_directory, "license.pre"
    )
    return get_file_text(license_path)


def get_license_agreement_text():
    license_agreement_path = unixify_path_join(
        data.settings_directory, data.license_agreement_filename
    )
    return get_file_text(license_agreement_path)


def license_agreement_compare():
    license_text = get_license_text()
    license_agreement_text = get_license_agreement_text()
    return license_text == license_agreement_text


def open_url(url: Optional[str], *args, **kwargs) -> None:
    """
    Open URL
    Idea: check this out: QDesktopServices.openUrl(QUrl(self.anchor))
    """
    if (url is None) or (url.lower() == "none") or (url.strip() == ""):
        return
    url = serverfunctions.replace_base_url(url)
    webbrowser.open_new_tab(url)
    return


def is_larger_than(v1: str, v2: str) -> bool:
    """
    :return: True   if v1 > v2
             False  if v1 <= v2
    """
    try:
        v1_list = v1.strip().split(".")
        v2_list = v2.strip().split(".")

        # $ First level
        try:
            if int(v1_list[0]) > int(v2_list[0]):
                return True
        except:
            if v1_list[0] > v2_list[0]:
                return True

        try:
            if int(v1_list[0]) < int(v2_list[0]):
                return False
        except:
            if v1_list[0] < v2_list[0]:
                return False

        # $ Second level
        try:
            if int(v1_list[1]) > int(v2_list[1]):
                return True
        except:
            if v1_list[1] > v2_list[1]:
                return True

        try:
            if int(v1_list[1]) < int(v2_list[1]):
                return False
        except:
            if v1_list[1] < v2_list[1]:
                return False

        # $ Third level
        try:
            if int(v1_list[2]) > int(v2_list[2]):
                return True
        except:
            if v1_list[2] > v2_list[2]:
                return True

        try:
            if int(v1_list[2]) < int(v2_list[2]):
                return False
        except:
            if v1_list[2] < v2_list[2]:
                return False

    except Exception as e:
        print(f"!!! ERROR: Cannot compare '{v1}' to '{v2}': {e}")
    return False


def get_embeetle_builddate(version_filepath: Optional[str] = None) -> str:
    """Return a date string like "13 dec 2019".

    :param version_filepath:    [Optional] filepath to `version.txt` file. Only necessary
                                if you want to a `version.txt` file from some other
                                location.
    """
    if version_filepath is None:
        version_filepath = unixify_path_join(
            data.beetle_core_directory, "version.txt"
        )
    text = ""
    date = "none"
    try:
        with open(version_filepath, "r", newline="\n") as f:
            text = f.read()
    except Exception as e:
        print(f"Could not extract builddate from {version_filepath}")
        return "none"
    try:
        p = re.compile(r"\d+\s\w+\s\d+", re.MULTILINE)
        m = p.search(text)
        date = m.group(0)
    except Exception as e:
        print(f"Could not extract builddate from {version_filepath}")
        return "none"
    return date


def get_xml_dictionary(filepath: Optional[str] = None) -> Dict:
    """"""
    with open(filepath, "r", encoding="utf-8") as f:
        my_xml = f.read()
    return xmltodict.parse(my_xml)


def get_json_dictionary(filepath: Optional[str] = None) -> Union[Dict, str]:
    """"""
    datastruct = {}
    try:
        with open(filepath, "r", newline="\n") as f:
            datastruct = json.load(f)
    except Exception as e:
        print(
            f"Could not extract python dictionary from json file: '{filepath}'"
        )
        return "none"
    return datastruct


def extract_github_release_assets(
    filepath: str,
) -> List[str]:
    """From the downloaded GitHub API response file, extract a list of .7z
    asset filenames for the release.

    result = [
        'avrdude_7.3_64b.7z',
        'openocd_0.12.0_64b.7z',
        ...
    ]
    """
    text = ""
    try:
        with open(filepath, "r", newline="\n") as f:
            text = f.read()
    except Exception:
        print(
            f"ERROR: Could not read GitHub API response from {filepath}"
        )
        return []
    try:
        release = json.loads(text)
        assets = release.get("assets", [])
        return [
            a["name"]
            for a in assets
            if isinstance(a.get("name"), str)
            and a["name"].endswith(".7z")
        ]
    except Exception:
        print(
            f"ERROR: Cannot parse GitHub API response at {filepath}"
        )
        return []


def assign_icon_err_warn_suffix(itemstatus) -> None:
    """Assign the '_err', '_warn' or '_info' suffix to an icon."""
    # Clean given iconpaths
    p = re.compile(r"\([\d\w]*\)")
    itemstatus.closedIconpath = p.sub("", itemstatus.closedIconpath)
    itemstatus.openIconpath = p.sub("", itemstatus.openIconpath)

    # Add suffixes
    if itemstatus.has_error():
        itemstatus.closedIconpath = itemstatus.closedIconpath.replace(
            ".png", "(err).png"
        )
        itemstatus.openIconpath = itemstatus.openIconpath.replace(
            ".png", "(err).png"
        )
    else:
        assert not itemstatus.has_error()
        if itemstatus.has_warning():
            itemstatus.closedIconpath = itemstatus.closedIconpath.replace(
                ".png", "(warn).png"
            )
            itemstatus.openIconpath = itemstatus.openIconpath.replace(
                ".png", "(warn).png"
            )
        else:
            assert not itemstatus.has_warning()
            if itemstatus.has_info_purple():
                itemstatus.closedIconpath = itemstatus.closedIconpath.replace(
                    ".png", "(info_purple).png"
                )
                itemstatus.openIconpath = itemstatus.openIconpath.replace(
                    ".png", "(info_purple).png"
                )
            else:
                assert not itemstatus.has_info_purple()
                if itemstatus.has_info_blue():
                    itemstatus.closedIconpath = (
                        itemstatus.closedIconpath.replace(
                            ".png", "(info_blue).png"
                        )
                    )
                    itemstatus.openIconpath = itemstatus.openIconpath.replace(
                        ".png", "(info_blue).png"
                    )
                else:
                    assert not itemstatus.has_info_blue()
                    if not itemstatus.is_relevant():
                        itemstatus.closedIconpath = (
                            itemstatus.closedIconpath.replace(
                                ".png", "(dis).png"
                            )
                        )
                        itemstatus.openIconpath = (
                            itemstatus.openIconpath.replace(".png", "(dis).png")
                        )
                    else:
                        assert itemstatus.is_relevant()
                        if itemstatus.is_readonly():
                            itemstatus.closedIconpath = (
                                itemstatus.closedIconpath.replace(
                                    ".png", "(lock).png"
                                )
                            )
                            itemstatus.openIconpath = (
                                itemstatus.openIconpath.replace(
                                    ".png", "(lock).png"
                                )
                            )
                        else:
                            assert not itemstatus.is_readonly()
    return


def is_executable(filepath: str) -> bool:
    """"""
    if not os.path.isfile(filepath):
        return False
    if os_checker.is_os("windows"):
        if filepath.endswith(".exe"):
            return True
    return os.access(filepath, os.X_OK)


def get_h1():
    fps = data.get_general_font_pointsize()
    h1 = f"""<p align="center"><span style="color:'#2e3436'; font-size:{fps+4}pt; font-weight:bold;">"""
    return h1


def get_h2():
    fps = data.get_general_font_pointsize()
    h2 = f"""<p align="left"><span style="color:'#a40000'; font-size:{fps+2}pt; font-weight:bold;">"""
    return h2


def get_h3():
    fps = data.get_general_font_pointsize()
    h3 = f"""<p align="left"><span style="color:'#3e7b05'; font-size:{fps}pt;   font-weight:bold;">"""
    return h3


def discon_sig(signal):
    """Disconnect only breaks one connection at a time, so loop to be safe."""
    while True:
        try:
            signal.disconnect()
        except TypeError:
            break
    return


def get_latest_makefile_interface_version(*args) -> int:
    """Return the latest 'makefile interface version' available to this Embeetle
    installation."""
    if data.makefile_version_new_projects is not None:
        return data.makefile_version_new_projects

    # Return the cached number if available
    if data.latest_makefile_version_nr is not None:
        return data.latest_makefile_version_nr

    # Compute the latest version nr
    p = re.compile(r"EMBEETLE_MAKEFILE_INTERFACE_VERSION\s*=\s*(\d+)")
    makefile_script = join_resources_dir_to_path("hardware/makefile.py")
    content = ""
    v = 7
    try:
        with open(
            makefile_script,
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            content = f.read()
        m = p.search(content)
        if m is not None:
            v = int(m.group(1))
    except:
        pass
    data.latest_makefile_version_nr = v
    return v


def toolbar_comport_selection_changed_from_to(
    from_comport: str,
    to_comport: str,
    *args,
) -> None:
    """Invoked when user changes selection in the Toolbar COM-port widget.

    :param from_comport: Original name of comport
    :param to_comport: New name of comport
    """
    if data.current_project is None:
        return
    if data.current_project.get_probe() is None:
        return
    data.current_project.get_probe().dropdown_selection_changed_from_to(
        dropdown_src="toolbar",
        from_comport=from_comport,
        to_comport=to_comport,
    )
    return


def list_serial_ports() -> Dict[str, Dict[str, str]]:
    """
    List serial ports in a dictionary, eg:
    {
        'COM4': {
            'name'          : 'COM4',
            'description'   : 'Arduino Uno (COM4)',
            'hwid'          : 'USB VID:PID=2341:0043 SER=55731323836351D0A1D1 LOCATION=1-12',
            'vid'           : 9025,
            'pid'           : 67,
            'serial_number' : '55731323836351D0A1D1',
            'location'      : '1-12',
            'manufacturer'  : 'Arduino LLC (www.arduino.cc)',
            'product'       : None,
            'interface'     : None,
        }
    }
    """
    comport_dict = {}
    try:
        t0 = time.time()
        for comport in serial.tools.list_ports.comports():
            comport_dict[comport.device] = {
                "name": comport.device,
                "description": comport.description,
                "hwid": comport.hwid,
                "vid": comport.vid,
                "pid": comport.pid,
                "serial_number": comport.serial_number,
                "location": comport.location,
                "manufacturer": comport.manufacturer,
                "product": comport.product,
                "interface": comport.interface,
            }
            # Note: comport.name returns None
        t1 = time.time()
        # print(f'\nTime to list serial ports: {t1 - t0:.3f}s\n')
    except:
        traceback.print_exc()
        comport_dict = {}
    printc(
        f"\n--------------------------------------------------------------------------------\n"
        f"List serial ports:",
        color="warning",
    )
    for name in comport_dict.keys():
        printc(
            f"    name:        {name}\n"
            f'    description: {comport_dict[name]["description"]}\n',
            color="warning",
        )
    printc(
        "--------------------------------------------------------------------------------",
        color="warning",
    )
    return comport_dict


def allowed_to_delete_folder(
    abspath: str = "", allow_rootpath_deletion: bool = False
) -> bool:
    """Return False if the given folder is too important to delete."""
    important_folders = None
    if os_checker.is_os("windows"):
        important_folders = data.important_windows_folders
    else:
        important_folders = data.important_linux_folders
    abspath = abspath.replace("\\", "/")
    abspath = abspath.lower()
    if abspath.endswith("/"):
        abspath = abspath[0:-1]
    if any(abspath.endswith(e) for e in important_folders):
        if "embeetle" in abspath.lower():
            pass
        else:
            return False
    if (
        hasattr(data, "current_project")
        and (data.current_project is not None)
        and (abspath == data.current_project.get_proj_rootpath().lower())
    ):
        if allow_rootpath_deletion:
            return True
        return False
    return True


def open_file_folder_in_explorer(abspath: str) -> bool:
    """Return False if the given file or folder cannot be opened in the system's
    file explorer (eg.

    it doesn't exist).
    """
    if os.path.isfile(abspath) or os.path.isdir(abspath):
        abspath = abspath.replace("/", os.sep)
        try:
            if os_checker.is_os("windows"):
                if os.path.isfile(abspath):
                    command = f'explorer /select,"{abspath}"'
                else:
                    command = f'explorer "{abspath}"'
                subprocess_popen_without_startup_info(command, shell=False)
            else:
                if os.path.isfile(abspath):
                    command_list = ["xdg-open", os.path.dirname(abspath)]
                else:
                    command_list = ["xdg-open", abspath]
                subprocess_popen_without_startup_info(command_list)
        except Exception as e:
            printc(f'\nERROR: Cannot open file/folder at "{abspath}".\n')
            traceback.print_exc()
            return False
        # No error
        return True
    print(
        f"\nERROR: Cannot open file/folder at '{abspath}',"
        f"\nbecause it doesn't exist.\n"
    )
    return False


def strip_toplvl_key(key: str) -> str:
    """
    Temporary function: strip the toplevel key from popup signals.
    """
    toplvl_keylist = (
        "itemBtn",
        "itemActionBtn",
        "itemArrow",
        "itemLbl",
        "itemChbx",
        "cchbx",
        "hchbx",
        "hglass",
        "cfgchbx",
        "itemImg",
        "itemLineedit",
        "itemProgbar",
        "filetree",
        "dashboard",
        "console",
    )
    new_key = key.split("/")
    if any(toplvl_key == new_key[0] for toplvl_key in toplvl_keylist):
        return "/".join(new_key[1:])
    raise RuntimeError(f'Context Menu produced key "{key}"')


def get_readme_content_for_projObj(
    projObj: Any,
    info_txt: str,
    link: Optional[str] = None,
) -> str:
    """Generate content for a readme file to be inserted in the given
    project."""
    # Most importers first create the project skeleton, then copy all the files and folders into the
    # 'source/' subfolder from the target. If a 'readme.txt' file was also copied this way, it must
    # be used to create the final content of the readme.
    candidate_readme_files = [
        unixify_path_join(projObj.get_proj_rootpath(), "readme.txt"),
        unixify_path_join(projObj.get_proj_rootpath(), "source/readme.txt"),
    ]
    if os.path.isfile(candidate_readme_files[0]):
        with open(
            candidate_readme_files[0],
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            info_txt = f.read()
        print("\nNOTE: Readme file gets content from original project\n")
        try:
            os.remove(candidate_readme_files[0])
        except:
            pass
    elif os.path.isfile(candidate_readme_files[1]):
        with open(
            candidate_readme_files[1],
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            info_txt = f.read()
        print("\nNOTE: Readme file gets content from original project\n")
        try:
            os.remove(candidate_readme_files[1])
        except:
            pass

    board_manufacturer = projObj.get_board().get_board_dict()["manufacturer"]
    if board_manufacturer is None:
        board_manufacturer = "none"
    chip_manufacturer = projObj.get_chip().get_chip_dict(board=None)[
        "manufacturer"
    ]
    if chip_manufacturer is None:
        chip_manufacturer = "none"
    lines = [
        f"microcontroller: {projObj.get_chip().get_name().lower()}",
        f"board: {projObj.get_board().get_name().lower()}",
        f"microcontroller manufacturer: {chip_manufacturer.lower()}",
        f"board manufacturer: {board_manufacturer.lower()}",
    ]
    # $ Link to board
    if link is None:
        if (projObj.get_board().get_name().lower() != "custom") and (
            projObj.get_board().get_name().lower() != "none"
        ):
            lines.append(
                f'link: {projObj.get_board().get_board_dict()["link"]}\n'
            )
        # $ Link to chip
        else:
            lines.append(
                f'link: {projObj.get_chip().get_chip_dict(board=None)["link"]}\n'
            )
    else:
        lines.append(f"link: {link}")

    # $ Write info
    lines.append("")
    if info_txt.startswith("Info:"):
        info_txt = info_txt.replace("Info:", "info:", 1)
    if info_txt.startswith("info:"):
        pass
    else:
        lines.append("info:")
    lines.append(info_txt)
    # $ Return as string
    return "\n".join(lines)


def beetle_pprint(
    item: Union[Dict, List, Tuple],
    printfunc: Callable,
    depth: int = 0,
) -> None:
    """My implementation for a pretty printer."""
    if printfunc is print:

        def my_print(txt, *args) -> None:
            print(txt, end="")
            return

        printfunc = my_print

    tab = "    " * depth
    if isinstance(item, dict):
        for k, v in item.items():
            printfunc(f'{tab}"{k}"', "#fce94f")
            if isinstance(v, dict):
                printfunc(f": {{\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}}},\n", "#f47272")
                continue
            if isinstance(v, list):
                printfunc(f": [\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}],\n", "#f47272")
                continue
            if isinstance(v, tuple):
                printfunc(f": (\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}),\n", "#f47272")
                continue
            printfunc(f": ", "#f47272")
            if isinstance(v, str):
                printfunc(f'"{v}"', "#ffffff")
            else:
                printfunc(f"{v}", "#ffffff")
            printfunc(f",\n", "#f47272")
            continue
        return
    if isinstance(item, list) or isinstance(item, tuple):
        for v in item:
            if isinstance(v, dict):
                printfunc(f"{tab} {{\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}}},\n", "#f47272")
                continue
            if isinstance(v, list):
                printfunc(f"{tab} [\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}],\n", "#f47272")
                continue
            if isinstance(v, tuple):
                printfunc(f"{tab} (\n", "#f47272")
                beetle_pprint(v, printfunc, depth + 1)
                printfunc(f"{tab}),\n", "#f47272")
                continue
            if isinstance(v, str):
                printfunc(f'{tab}"{v}"', "#ffffff")
            else:
                printfunc(f"{tab}{v}", "#ffffff")
            printfunc(f",\n", "#f47272")
            continue
        return
    assert False


def beetle_format(
    item: Union[Dict, List, Tuple],
    depth: int = 0,
) -> List[str]:
    """My implementation for a pretty formatter."""
    lines = []
    tab = "    " * depth
    if isinstance(item, dict):
        for k, v in item.items():
            if isinstance(v, dict):
                lines.append(f'{tab}"{k}": {{\n')
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}}},\n")
                continue
            if isinstance(v, list):
                lines.append(f'{tab}"{k}": [\n')
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}],\n")
                continue
            if isinstance(v, tuple):
                lines.append(f'{tab}"{k}": (\n')
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}),\n")
                continue
            if isinstance(v, str):
                lines.append(f': "{v}",\n')
            else:
                lines.append(f": {v},\n")
            continue
        return lines
    if isinstance(item, list) or isinstance(item, tuple):
        for v in item:
            if isinstance(v, dict):
                lines.append(f"{tab} {{\n")
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}}},\n")
                continue
            if isinstance(v, list):
                lines.append(f"{tab} [\n")
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}],\n")
                continue
            if isinstance(v, tuple):
                lines.append(f"{tab} (\n")
                lines.extend(beetle_format(v, depth + 1))
                lines.append(f"{tab}),\n")
                continue
            if isinstance(v, str):
                lines.append(f'{tab}"{v}",\n')
            else:
                lines.append(f"{tab}{v},\n")
            continue
        return lines
    assert False


def clean_layout(
    lyt: Union[
        Union[qt.QLayout, Any],
        Tuple[
            Union[qt.QLayout, Any],
            Optional[Callable],
            Any,
        ],
    ],
) -> None:
    """Browse through all the items from the given qt.QLayout(). These items are
    either layouts themselves and/or qt.QWidget()s. Delete them properly.

    :param lyt:  Usually this parameter is just a qt.QLayout()-instance.
                 However, it can also be a tuple of three objects:
                     1. qt.QLayout()-instance
                     2. A callback
                     3. A callback argument
                 The callback will be invoked when cleaning the layout has completed. When that is,
                 depends on the behavior of the child widgets 'self_destruct()' methods.

    Sources:
        - https://newbedev.com/clear-all-widgets-in-a-layout-in-pyqt
    """
    _lyt: Optional[Union[qt.QLayout, _item_layout_.ItemLayout]] = None
    _callback: Optional[Callable] = None
    _callbackArg: Any = None
    if isinstance(lyt, tuple):
        # The given parameter contains not only the layout, but also a callback:
        _lyt, _callback, _callbackArg = lyt
    else:
        # The given parameter is just the layout:
        _lyt = lyt

    if qt.sip.isdeleted(_lyt):
        del _lyt
        if _callback is not None:
            _callback(_callbackArg)
        return

    # & LOOP OVER CHILD-ITEMS
    # & =====================
    # Loop over all the items from the given layout in reverse order. Delete them one-by-one.
    for i in reversed(range(_lyt.count())):
        # Request the child at index 'i'
        x = _lyt.itemAt(i)
        x_lyt = x.layout()
        x_widg = x.widget()

        # The child is either a widget or a layout itself, but never both:
        if (x_lyt is None) == (x_widg is None):
            assert x_lyt is None
            assert x_widg is None

        # $ ----------------------------
        # $ | Child is a qt.QSpacerItem() |
        # $ ----------------------------
        if isinstance(x, qt.QSpacerItem):
            # If the underlying Qt-object already died, just ignore it and move on to the next
            # child. Removing all Python references to the object is enough to completely delete it.
            if qt.sip.isdeleted(x):
                del x
                del x_lyt
                del x_widg
                continue
            # It seems like a qt.QSpacerItem() has no setParent() method. So the only thing we can do
            # here is to remove the spacer from the layout.
            _lyt.removeItem(x)

        # $ ----------------------------
        # $ |    Child is a layout     |
        # $ ----------------------------
        elif x_lyt is not None:
            assert isinstance(x_lyt, qt.QLayout)
            # If the child's underlying Qt-object already died, just ignore it and move on to the
            # next child. Removing all Python references to the object is enough to completely de-
            # lete it.
            if qt.sip.isdeleted(x_lyt):
                del x
                del x_lyt
                del x_widg
                continue

            # Recurse:
            clean_layout(x_lyt)

            # Do another check if the Qt-object has died, just because I'm paranoid about this.
            if qt.sip.isdeleted(x_lyt):
                del x
                del x_lyt
                del x_widg
                continue

            # Remove the sub-layout 'x_lyt' from this layout.
            # By now, the child layout 'x_lyt' should contain no more subitems, but it still exists
            # by itself. To kill it, I used to invoke 'x_lyt.setParent(None)' and 'x_lyt.delete-
            # Later()', but that sometimes caused crashes without traceback.
            # Quoted from this source:
            # https://newbedev.com/clear-all-widgets-in-a-layout-in-pyqt
            # "It's not enough to simply deparent the widget. At some point, you will get a 'Segmen-
            # tation fault (core dumped)' if you empty and refill the layout many times or with many
            # widgets. It seems that the layout keeps a list of widgets and that this list is limit-
            # ed in size."
            # Therefore, the sub-layout must be removed first from the layout list:
            _lyt.removeItem(x)

            # Deparent the sub-layout:
            x_lyt.setParent(None)  # noqa

        # $ ----------------------------
        # $ |    Child is a widget     |
        # $ ----------------------------
        elif x_widg is not None:
            assert isinstance(x_widg, qt.QWidget)
            # If the child's underlying Qt-object already died, just ignore it and move on to the
            # next child. Removing all Python references to the object is enough to completely de-
            # lete it.
            if qt.sip.isdeleted(x_widg):
                del x
                del x_lyt
                del x_widg
                continue

            # Remove the widget from this layout.
            # Quoted from this source:
            # https://newbedev.com/clear-all-widgets-in-a-layout-in-pyqt
            # "It's not enough to simply deparent the widget. At some point, you will get a 'Segmen-
            # tation fault (core dumped)' if you empty and refill the layout many times or with many
            # widgets. It seems that the layout keeps a list of widgets and that this list is limit-
            # ed in size."
            # Therefore, the widget must be removed first from that layout list:
            _lyt.removeWidget(x_widg)

            # It's a custom widget with a self_destruct() method
            if hasattr(x_widg, "self_destruct"):
                # Another sip check, because I'm paranoid:
                if qt.sip.isdeleted(x_widg):
                    del x
                    del x_lyt
                    del x_widg
                    continue

                # Now invoke the 'self_destruct()' method on the widget. The method should also
                # deparent it.
                try:
                    # Destroy the child widget and continue cleaning this layout after destruction
                    # of the child has completed.
                    x_widg.self_destruct(
                        callback=clean_layout,
                        callbackArg=lyt,
                    )
                    del x
                    del x_lyt
                    del x_widg
                    # No need to make a callback here! If there was a callback given, it should be
                    # encapsulated in the 'lyt' parameter. So the callback will be invoked later on.
                    return
                except:
                    # The child's self-destruct method has no callback, so it should do its job im-
                    # mediately.
                    x_widg.self_destruct()  # noqa
            else:
                # Deparent the widget:
                x_widg.setParent(None)  # noqa

        del x
        del x_lyt
        del x_widg
        continue

    assert _lyt.count() == 0
    if _callback is not None:
        _callback(_callbackArg)
    return


def get_embeetle_unique_identifier():
    guid_file = unixify_path_join(data.settings_directory, ".guid")
    if not os.path.isfile(guid_file):
        guid = str(uuid.uuid4())
        with open(guid_file, "w+", encoding="utf-8") as f:
            f.write(guid)
    else:
        with open(guid_file, "r", encoding="utf-8") as f:
            guid = f.read().strip()
    return guid


def get_feed_from_resource_file():
    path = join_resources_dir_to_path("feed/default.html")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            return text
        except:
            pass
    return None


def rss_format_time(dt) -> str:
    return datetime.datetime.strftime(dt, data.rss_feed_datetime_format)


def get_local_paths(*args, **kwargs) -> Dict[str, str]:
    """"""
    return {
        "beetle_core_directory": data.beetle_core_directory,
        "beetle_tools_directory": data.beetle_tools_directory,
        "beetle_project_generator_folder": data.beetle_project_generator_folder,
        "beetle_licenses_directory": data.beetle_licenses_directory,
        "sys_directory": data.sys_directory,
        "sys_bin": data.sys_bin,
        "sys_lib": data.sys_lib,
        "local_keypath": data.local_keypath,
        "resources_directory": data.resources_directory,
        "embeetle_toplevel_folder": data.embeetle_toplevel_folder,
    }


def get_rsync_location() -> Tuple[str, str, str, str]:
    """
    Get the location of:
        > rsyncpath: rsync executable
        > sshpath:   ssh executable
        > exefolder: rsync executable parent folder
        > dllfolder: rsync dll/so parent folder
    """
    rsyncpath = os.path.join(
        data.sys_bin,
        f"rsync",
    ).replace("\\", "/")
    if os_checker.is_os("windows"):
        rsyncpath = f"{rsyncpath}.exe"
    exefolder = data.sys_bin
    sshpath = os.path.join(
        exefolder,
        "ssh",
    ).replace("\\", "/")
    if os_checker.is_os("windows"):
        sshpath = f"{sshpath}.exe"
    assert os.path.isfile(rsyncpath)
    assert os.path.isfile(sshpath)
    return rsyncpath, sshpath, exefolder, data.sys_lib


def verify_local_paths(*args, **kwargs) -> None:
    """"""
    return


importer_printfunc_: Optional[Callable] = None
generator_printfunc_: Optional[Callable] = None


def importer_printfunc(*args, **kwargs) -> None:
    """"""
    if importer_printfunc_ is None:
        printc(*args, **kwargs)
        return
    sep = kwargs.get("sep", " ")
    html_text = (
        sep.join(args)
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
        .replace(" ", "&nbsp;")
    )
    if kwargs.get("end") == "":
        importer_printfunc_(html_text, **kwargs)
        return
    importer_printfunc_(html_text + "<br>", **kwargs)
    return


def generator_printfunc(*args, **kwargs) -> None:
    """"""
    if generator_printfunc_ is None:
        printc(*args, **kwargs)
        return
    sep = kwargs.get("sep", " ")
    html_text = (
        sep.join(args)
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
        .replace(" ", "&nbsp;")
    )
    if kwargs.get("end") == "":
        generator_printfunc_(html_text, **kwargs)
        return
    generator_printfunc_(html_text + "<br>", **kwargs)
    return


def text_to_pixmap_rectangle(
    text: str,
    offset: qt.QPointF,
    text_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    border_color: Optional[str] = None,
) -> qt.QPixmap:
    padding: int = 2

    # Create a QFont to set the font size
    font: qt.QFont = data.get_general_font()
    if text_color is not None:
        font_color: qt.QColor = qt.QColor(text_color)
    else:
        font_color: qt.QColor = qt.QColor(
            data.theme["fonts"]["default"]["color"]
        )

    # Calculate the size of the pixmap based on the text size
    metrics: qt.QFontMetrics = qt.QFontMetrics(font)
    text_width: int = metrics.horizontalAdvance(text)
    text_height: int = metrics.height()

    # Create a pixmap with padding for the text
    pixmap: qt.QPixmap = qt.QPixmap(
        text_width + (2 * padding), text_height + (2 * padding)
    )
    pixmap.fill(qt.QColor("red"))  # Fill with transparency

    # Draw a black rectangle with a white border (1px) behind the text
    adjustment: int = (2 * padding) - 1
    rect: qt.QRect = qt.QRect(
        0, 0, text_width + adjustment, text_height + adjustment
    )

    # Create a QPainter to draw the text on the pixmap
    painter: qt.QPainter = qt.QPainter(pixmap)
    # Move the painter
    #    painter.translate(offset)

    # Set pen for white border
    if border_color is not None:
        painter.setPen(qt.QColor(border_color))
    else:
        painter.setPen(qt.QColor(data.theme["button_border"]))
    if bg_color is not None:
        painter.setBrush(qt.QColor(bg_color))
    else:
        painter.setBrush(qt.QColor(data.theme["menu_background"]))
    painter.drawRect(rect)  # Draw the rectangle with a white border

    # Draw the text
    painter.setFont(font)
    painter.setPen(font_color)  # Set text color
    painter.drawText(padding, padding + metrics.ascent(), text)  # Draw the text
    painter.end()

    return pixmap
