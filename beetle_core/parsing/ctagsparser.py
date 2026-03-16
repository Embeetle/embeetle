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

import sys
import os
import pathlib
import subprocess
import json
import time
import functools
import qt
import constants
import data
import purefunctions
import functions
import parsing

"""
---------------------------------
A tag used by the ctags parser
---------------------------------
"""


class Tag:
    _type = None  # type: str
    name = None  # type: str
    path = None  # type: str
    line = None  # type: str
    pattern = None  # type: str
    typeref = None  # type: str
    kind = None  # type: str
    scope = None  # type: str
    scopeKind = None  # type: str

    def __init__(
        self, _type, name, path, line, pattern, typeref, kind, scope, scopeKind
    ):
        self._type = _type
        self.name = name
        self.path = path
        self.line = line
        self.pattern = pattern
        self.typeref = typeref
        self.kind = kind
        self.scope = scope
        self.scopeKind = scopeKind


"""
-------------
Ctags parser
-------------
"""


class CtagsParser(qt.QObject):
    # Choose either to parse to a pathon list or a dirtree
    USING_DATABASE = False  # type: bool

    files_to_parse = None  # type: typing.List[str]
    ctags_path = None  # type: str
    parsed_tags = None  # type: typing.List[Tag]
    ctags_worker = None  # type: CtagsThreadWorker
    thread = None  # type: qt.QThread
    asynchronous_parsing = True  # type: bool

    # Signals
    databaseInsertMany = qt.pyqtSignal([list])
    parsedFile = qt.pyqtSignal(str, int, int)
    parsingComplete = qt.pyqtSignal()

    @staticmethod
    def check_c_cpp_file(file):
        if os.path.isfile(file) == False:
            raise Exception(
                "[CtagsParser] Item '{}' is not a file!".format(file)
            )
        file_extension = os.path.splitext(file)[1]
        check = (
            file_extension in constants.file_extensions["c"]
            or file_extension in constants.file_extensions["h"]
            or file_extension in constants.file_extensions["cpp"]
            or file_extension in constants.file_extensions["hpp"]
        )
        if check == False:
            raise Exception(
                "[CtagsParser] Item '{}' is not a C/C++ file!".format(file)
            )

    def terminate_thread(self):
        if self.thread is not None:
            self.thread.terminate()
            self.thread.setParent(None)
            self.thread.deleteLater()
            self.thread = None

    def __del__(self):
        self.terminate_thread()

    def __init__(self, *items):
        super().__init__()
        # Initialize the files for parsing
        self.files_to_parse = []
        self.add(items)
        # Initialize the ctags executable location
        raise DeprecationWarning("ctags no longer in use!")
        self.ctags_path = purefunctions.join_resources_dir_to_path(
            "/programs/ctags.exe"
        )
        return

    def _add_initial_items(self, items):
        if isinstance(items, None):
            # Files must be added manually
            pass
        elif self.add(items) == True:
            # Items added successfully
            pass
        else:
            raise Exception(
                "[CtagsParser] Invalid construction parameters: {}".format(
                    items.__class__
                )
            )

    def add(self, items):
        if isinstance(items, str):
            file = items
            # Check file validity
            CtagsParser.check_c_cpp_file(file)
            # Store the file for parsing
            if not (file in self.files_to_parse):
                self.files_to_parse.append(file)
            return True
        elif isinstance(items, list) or all(
            [isinstance(x, str) for x in items]
        ):
            for file in items:
                CtagsParser.check_c_cpp_file(file)
            # Store the files for parsing
            for file in items:
                if not (file in self.files_to_parse):
                    self.files_to_parse.append(file)
            return True
        elif isinstance(items, tuple):
            if len(items) == 1:
                items = items[0]
            for file in items:
                CtagsParser.check_c_cpp_file(file)
            # Store the files for parsing
            self.files_to_parse.extend(items)
            return True
        # Invalid items
        return False

    def get_files_to_parse(self):
        return self.files_to_parse

    def set_synchronous(self, state):
        self.asynchronous_parsing = not state

    def _parse_to_list(self, files_to_parse):
        start_time = time.time()
        data.tag_database = parsing.ParseDatabase()
        command_list = [
            "ctags",
            "--output-format=json",
            "--fields=+n",
            "--c-types=+l",
        ]
        file_counter = 0
        file_count = len(files_to_parse)
        for file in files_to_parse:
            proc = purefunctions.subprocess_popen(
                command_list + [file], stdout=subprocess.PIPE, shell=True
            )
            json_output_string = proc.communicate()[0].decode("utf-8")
            if json_output_string == "":
                continue
            for l in json_output_string.splitlines():
                parsed_json = json.loads(l)
                keys = parsed_json.keys()
                if "kind" in keys:
                    new_tag = Tag(
                        (
                            parsed_json["_type"]
                            if "_type" in parsed_json
                            else None
                        ),
                        parsed_json["name"] if "name" in parsed_json else None,
                        parsed_json["path"] if "path" in parsed_json else None,
                        parsed_json["line"] if "line" in parsed_json else None,
                        (
                            parsed_json["pattern"]
                            if "pattern" in parsed_json
                            else None
                        ),
                        (
                            parsed_json["typeref"]
                            if "typeref" in parsed_json
                            else None
                        ),
                        parsed_json["kind"] if "kind" in parsed_json else None,
                        (
                            parsed_json["scope"]
                            if "scope" in parsed_json
                            else None
                        ),
                        (
                            parsed_json["scopeKind"]
                            if "scopeKind" in parsed_json
                            else None
                        ),
                    )
                    data.tag_database.add_tag(new_tag)
            self.parsedFile.emit(file, file_counter, file_count)
            file_counter += 1
        print("CTags parsing time: ", time.time() - start_time)

    def _parse_to_database(self, files_to_parse):
        start_time = time.time()
        data.tag_database = parsing.ParseDatabase()
        self.databaseInsertMany.connect(data.tag_database.add_tags)
        command_list = [
            "ctags",
            "--output-format=json",
            "--fields=+n",
            "--c-types=+l",
        ]
        file_counter = 0
        file_count = len(files_to_parse)
        for file in files_to_parse:
            proc = purefunctions.subprocess_popen(
                command_list + [file],
                stdout=subprocess.PIPE,
                shell=True,
            )
            json_output_string = proc.communicate()[0].decode("utf-8")
            if json_output_string == "":
                continue
            file_tags = []
            for l in json_output_string.splitlines():
                parsed_json = json.loads(l)
                keys = parsed_json.keys()
                if "kind" in keys:
                    new_tag = (
                        (
                            parsed_json["_type"]
                            if "_type" in parsed_json
                            else None
                        ),
                        parsed_json["name"] if "name" in parsed_json else None,
                        parsed_json["path"] if "path" in parsed_json else None,
                        parsed_json["line"] if "line" in parsed_json else None,
                        (
                            parsed_json["pattern"]
                            if "pattern" in parsed_json
                            else None
                        ),
                        (
                            parsed_json["typeref"]
                            if "typeref" in parsed_json
                            else None
                        ),
                        parsed_json["kind"] if "kind" in parsed_json else None,
                        (
                            parsed_json["scope"]
                            if "scope" in parsed_json
                            else None
                        ),
                        (
                            parsed_json["scopeKind"]
                            if "scopeKind" in parsed_json
                            else None
                        ),
                    )
                    #                    data.tag_database.add_tag(new_tag)
                    file_tags.append(new_tag)
            if len(file_tags) > 0:
                data.tag_database.add_tags(file_tags)
            self.parsedFile.emit(file, file_counter, file_count)
            file_counter += 1
        print("CTags dirtree parsing time: ", time.time() - start_time)

    def _parsing_complete(self):
        self.terminate_thread()
        self.parsingComplete.emit()
        print("Complete")

    def parse(self):
        if self.asynchronous_parsing == True:
            # Asynchronous
            func = self._parse_to_list
            if CtagsParser.USING_DATABASE:
                func = self._parse_to_database
            self.ctags_worker = CtagsThreadWorker(self.files_to_parse, func)
            self.thread = qt.QThread()
            self.thread.setTerminationEnabled(True)
            self.ctags_worker.moveToThread(self.thread)
            self.ctags_worker.finished.connect(self._parsing_complete)
            self.thread.started.connect(self.ctags_worker.work)
            self.thread.start()
        else:
            # Synchronous
            if CtagsParser.USING_DATABASE:
                self._parse_to_database(self.files_to_parse)
            else:
                self._parse_to_list(self.files_to_parse)

    def parsing(self):
        if self.thread is not None and self.thread.isRunning():
            return True
        else:
            return False


"""
------------------------------------------------
Worker that crunches Ctags in a separate thread
------------------------------------------------
"""


class CtagsThreadWorker(qt.QObject):
    if CtagsParser.USING_DATABASE:
        finished = qt.pyqtSignal()

        def __init__(self, file_list, func):
            super().__init__()
            self.file_list = file_list
            self.func = func

        @qt.pyqtSlot()
        def work(self):
            self.func(self.file_list)
            self.finished.emit()

    else:
        finished = qt.pyqtSignal()

        def __init__(self, file_list, func):
            super().__init__()
            self.file_list = file_list
            self.func = func

        @qt.pyqtSlot()
        def work(self):
            self.func(self.file_list)
            self.finished.emit()
