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
import sys
import qt
import data
import functions
import time
import threading
import multiprocessing


class FileChecker(qt.QObject):
    checker_add = qt.pyqtSignal(str)
    checker_remove = qt.pyqtSignal(str)
    file_changed = qt.pyqtSignal(str)
    file_removed = qt.pyqtSignal(str)

    debug = False
    files_line_endings = None
    change_checker = None

    def __init__(self):
        super().__init__()
        self.files_line_endings = {}
        self.change_checker = ChangeChecker(self)
        self.change_checker.start()
        # Connect signals
        self.checker_add.connect(self.change_checker.file_add)
        self.checker_remove.connect(self.change_checker.file_remove)

    def echo(self, *messages):
        if self.debug:
            print("[FileChecker]", *messages)

    def check_line_endings(self, path):
        if not (path in self.files_line_endings.keys()) or (
            os.path.getmtime(path) > self.files_line_endings[path]
        ):
            if functions.check_line_endings(path):
                self.echo("Converted line endings in file:\n", f"  {path}")
            self.files_line_endings[path] = os.path.getmtime(path)

    def checker_file_add(self, path):
        if os.path.isfile(path):
            self.echo(f"Added file: {path}")
            self.checker_add.emit(path)

    def checker_file_remove(self, path):
        self.checker_remove.emit(path)
        self.echo(f"Removed file: {path}")

    @qt.pyqtSlot(str)
    def _file_changed(self, path):

        self.file_changed.emit(path)
        self.echo(f"File has changed: {path}")

    @qt.pyqtSlot(str)
    def _file_removed(self, path):
        self.file_removed.emit(path)
        self.echo(f"Removed checking of missing file: {path}")


class ChangeChecker(qt.QThread):
    file_changed = qt.pyqtSignal(str)
    file_removed = qt.pyqtSignal(str)

    CHECK_INTERVAL = 1.0

    file_cache = None
    event_handler = None

    def __init__(self, file_checker):
        qt.QThread.__init__(self)
        self.file_cache = {}
        self.file_changed.connect(file_checker._file_changed)
        self.file_removed.connect(file_checker._file_removed)

    def __del__(self):
        self.wait()

    @qt.pyqtSlot(str)
    def file_add(self, file_path):
        self.file_cache[file_path] = os.path.getmtime(file_path)

    @qt.pyqtSlot(str)
    def file_remove(self, file_path):
        self.file_cache.pop(file_path, None)

    def check_file_cache(self):
        missing_files = []
        for file_path, last_change_time in list(self.file_cache.items()):
            if not os.path.isfile(file_path):
                missing_files.append(file_path)
                continue
            current_change_time = os.path.getmtime(file_path)
            if last_change_time != current_change_time:
                self.file_cache[file_path] = os.path.getmtime(file_path)
                self.file_changed.emit(file_path)
        # Clean missing files
        for mf in missing_files:
            self.file_cache.pop(mf, None)
            self.file_removed.emit(mf)

    def run(self):
        while True:
            self.check_file_cache()
            time.sleep(self.CHECK_INTERVAL)
