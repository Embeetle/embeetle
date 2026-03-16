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

import multiprocessing
import queue
import threading
import time
import traceback
from typing import *

import data
import functions
import qt
import source_analyzer


class SymbolHandler(qt.QObject):
    """Class to handle symbol information."""

    # Signals
    symbols_added_signal = qt.pyqtSignal(list)
    symbols_removed_signal = qt.pyqtSignal(list)
    start_processing_signal = qt.pyqtSignal()
    add_symbol_to_queue_signal = qt.pyqtSignal(str, object)

    # Signal locking
    recheck = False

    # Storage
    ci_project = None
    symbols_dict = None
    current_file = None

    # General
    debug = False

    def __init__(self, project) -> None:
        super().__init__()
        self.set_project(project)
        self.recheck = False
        self.current_file = None

        self.symbols_dict = {}
        self.symbol_list_add = []
        self.symbol_list_remove = []
        self.add_symbol_to_queue_signal.connect(self.__add_symbol_to_queue)

        self.start_processing_signal.connect(self.__process_added_symbols)

    def echo(self, *messages):
        class_name = self.__class__.__name__
        print(f"[{class_name}]", *messages)

    def __add_symbol_to_queue(self, _type, symbol) -> None:
        if _type == "add":
            self.symbols_dict[symbol._id] = symbol
            self.symbol_list_add.append((symbol, self.current_file))
        elif _type == "remove":
            self.symbols_dict.pop(symbol._id, None)
            self.symbol_list_remove.append(symbol)
        else:
            raise Exception(f"[SymbolHandler] Unknown _type: '{_type}'")

        self.__restart_add_remove_timer()

    def __process_added_symbols(self):
        qt.start_named_qtimer(
            owner=self,
            timer_name="process_timer",
            interval_ms=20,
            callback=self.__process_symbols,
        )

    def __process_symbols(self):
        if len(self.symbol_list_add) > 0:
            self.symbols_added_signal.emit(self.symbol_list_add)
            self.symbol_list_add = []

        if len(self.symbol_list_remove) > 0:
            self.symbols_removed_signal.emit(self.symbol_list_remove)
            self.symbol_list_remove = []

    def symbol_add(self, symbol) -> None:
        if self.debug:
            self.echo(f"Added symbol: {symbol.name}")
        self.add_symbol_to_queue_signal.emit("add", symbol)

    def symbol_remove(self, symbol) -> None:
        if self.debug:
            self.echo(f"Removed symbol: {symbol.name}")
        self.add_symbol_to_queue_signal.emit("remove", symbol)

    def __process_add_remove_queue(self) -> None:
        self.start_processing_signal.emit()

    def __restart_add_remove_timer(self) -> None:
        if not hasattr(self, "add_remove_timer"):
            self.add_remove_timer = qt.QTimer(self)
            self.add_remove_timer.setInterval(50)
            self.add_remove_timer.setSingleShot(True)
            self.add_remove_timer.timeout.connect(self.__process_add_remove_queue)
        if self.add_remove_timer.isActive():
            self.add_remove_timer.stop()
        self.add_remove_timer.start()

    def set_project(self, project) -> None:
        self.ci_project = project

    def start_analysis(self, path):
        self.current_file = path
        self.ci_project.track_occurrences(
            path,
            source_analyzer.all_definition_kinds,
            source_analyzer.all_entity_kinds,
        )

    def stop_analysis(self, path):
        self.ci_project.track_occurrences(
            path,
            [],
            [],
        )
