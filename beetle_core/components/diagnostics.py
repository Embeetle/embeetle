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

import qt
import data
import functions
import source_analyzer
import time
import queue
import threading
import multiprocessing
import math
import traceback
import components.lockcache
from typing import *
from pprint import pprint


class Diagnostics(qt.QObject):
    """Class to handle all diagnostic messages."""

    # Signals
    message_added_signal = qt.pyqtSignal(object)
    message_bulk_add_signal = qt.pyqtSignal(object)
    message_removed_signal = qt.pyqtSignal(object)
    message_bulk_remove_signal = qt.pyqtSignal(object)
    message_available_signal = qt.pyqtSignal(object, int)
    start_processing_signal = qt.pyqtSignal()
    cap_reset_signal = qt.pyqtSignal(object)

    # Signal locking
    #    lock = None
    recheck = False

    # Storage
    ci_project = None
    diagnostics_dict = None
    diagnostic_caps = None
    diagnostics_shown = None
    diagnostics_hidden = None
    cap_reset_timers = None
    output_add_buffer = None
    output_remove_buffer = None

    def __init__(self, project) -> None:
        super().__init__()
        self.set_project(project)
        #        self.lock = threading.Lock()
        self.recheck = False
        self.diagnostics_dict = {}
        self.diagnostic_caps = {}
        self.diagnostics_shown = {}
        self.diagnostics_hidden = {}
        self.cap_reset_timers = {}
        self.output_add_buffer = []
        self.output_remove_buffer = []
        #        self.start_processing_signal.connect(self.__process_added_messages)
        self.start_processing_signal.connect(self._start_processing)
        self.cap_reset_signal.connect(self.cap_reset)
        self.reset_capping()

    def reset_capping(self):
        # Initialize capping in the Clang Engine
        for severity in source_analyzer.Severity:
            #            self.set_diagnostic_limit(severity, data.diagnostic_cap)
            self.set_diagnostic_limit(severity, 500)
            self.diagnostic_caps[severity] = data.diagnostic_cap

    def cap_increase(self, severity, addition):
        if not (severity in self.diagnostic_caps):
            self.diagnostic_caps[severity] = data.diagnostic_cap
        self.diagnostic_caps[severity] += addition
        self.set_diagnostic_limit(severity, self.diagnostic_caps[severity])

    @qt.pyqtSlot(object)
    def cap_reset(self, severity):
        if not (severity in self.cap_reset_timers.keys()):

            def reset(*args):
                shown = self.diagnostics_shown[severity]
                new_level = math.floor(shown / data.diagnostic_cap)
                if new_level == 0:
                    new_level = 1
                if (shown % data.diagnostic_cap) > 0:
                    new_level += 1
                self.diagnostic_caps[severity] = new_level * data.diagnostic_cap
                self.set_diagnostic_limit(
                    severity, self.diagnostic_caps[severity]
                )

            self.cap_reset_timers[severity] = qt.QTimer()
            self.cap_reset_timers[severity].setInterval(200)
            self.cap_reset_timers[severity].setSingleShot(True)
            self.cap_reset_timers[severity].timeout.connect(reset)
        self.cap_reset_timers[severity].stop()
        self.cap_reset_timers[severity].start()

    def _add_message_to_queue(self, _type, message) -> None:
        # Create queue if needed
        if hasattr(self, "message_queue") == False:
            #            self.message_queue = multiprocessing.Queue()
            self.message_queue = []
        # Add the 'add' message to queue
        #        self.message_queue.put((_type, message))
        self.message_queue.append((_type, message))
        # Start processing
        self.start_processing_signal.emit()

    def _start_processing(self, *args):
        if not hasattr(self, "adding_timer"):
            self.adding_timer = qt.QTimer(self)
            self.adding_timer.setInterval(500)
            self.adding_timer.setSingleShot(True)
            self.adding_timer.timeout.connect(self.__process_added_messages)
        if self.adding_timer.isActive():
            self.adding_timer.stop()
        self.adding_timer.start()

    def __process_added_messages(self, *args):
        try:
            while True:
                with components.lockcache.Locker("diagnostics-buffer"):
                    if len(self.message_queue) == 0:
                        if self.recheck == False:
                            self.recheck = True
                            qt.QTimer.singleShot(
                                10, self.__process_added_messages
                            )
                        else:
                            self.recheck = False
                        return
                    _type, message = self.message_queue.pop(0)
                    if _type == "add":
                        #                        self.message_added_signal.emit(message)
                        self.output_add_buffer.append(message)
                        self.__start_output_timer()
                    elif _type == "remove":
                        #                        self.message_removed_signal.emit(message)
                        self.output_remove_buffer.append(message)
                        self.__start_output_timer()
                    else:
                        raise Exception(f"Unknown message type: '{_type}'")
        except:
            traceback.print_exc()

    def __start_output_timer(self):
        if not hasattr(self, "output_timer"):
            self.output_timer = qt.QTimer(self)
            self.output_timer.setInterval(200)
            self.output_timer.setSingleShot(True)
            self.output_timer.timeout.connect(self.__output)
        if self.output_timer.isActive():
            self.output_timer.stop()
        self.output_timer.start()

    def __output(self):
        with components.lockcache.Locker("diagnostics-buffer"):
            try:
                self.message_bulk_add_signal.emit(self.output_add_buffer)
                self.output_add_buffer = []
                self.message_bulk_remove_signal.emit(self.output_remove_buffer)
                self.output_remove_buffer = []
            except:
                traceback.print_exc()

    @components.lockcache.inter_process_lock("update-editor-diagnostics")
    def message_add(self, diagnostic) -> None:
        # Counting
        severity = diagnostic.severity
        # Add to internal 'shown' table
        if not (severity in self.diagnostics_shown.keys()):
            self.diagnostics_shown[severity] = 0
        self.diagnostics_shown[severity] += 1
        # Emit the signal
        self._add_message_to_queue("add", diagnostic)
        self.diagnostics_dict[diagnostic._id] = diagnostic

    @components.lockcache.inter_process_lock("update-editor-diagnostics")
    def message_remove(self, diagnostic) -> None:
        # Counting
        severity = diagnostic.severity
        self.diagnostics_shown[severity] -= 1
        # Emit the signal
        self._add_message_to_queue("remove", diagnostic)
        self.diagnostics_dict.pop(diagnostic._id, None)
        # Reset the message cap as needed
        self.cap_reset_signal.emit(severity)

    def get_diagnostic_limit(self, severity):
        return self.ci_project.set_diagnostic_limit(severity)

    def set_diagnostic_limit(self, severity, limit):
        self.ci_project.set_diagnostic_limit(severity, limit)

    def more_available_callback(self, severity, count):
        # Counting
        if not (severity in self.diagnostics_hidden.keys()):
            self.diagnostics_hidden[severity] = 0
        self.diagnostics_hidden[severity] = count
        # Emit the signal
        self.message_available_signal.emit(severity, count)

    def set_project(self, project) -> None:
        self.ci_project = project

    def show_all(self, cap=1000):
        for s in source_analyzer.Severity:
            self.cap_increase(s, cap)

    def get_item_sum(self, severity):
        if not (severity in self.diagnostics_shown.keys()):
            self.diagnostics_shown[severity] = 0
        if not (severity in self.diagnostics_hidden.keys()):
            self.diagnostics_hidden[severity] = 0
        return (
            self.diagnostics_shown[severity] + self.diagnostics_hidden[severity]
        )
