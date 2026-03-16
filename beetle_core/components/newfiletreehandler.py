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
import os
import time
import os_checker
import fnmatch
import traceback
import enum
import queue
import multiprocessing
import concurrent.futures
import watchdog.events
import watchdog.observers
import watchdog.observers.polling
import qt
import data
import purefunctions
import iconfunctions
import functions
import components.lockcache
import source_analyzer
import hardware_api.hardware_api as _hardware_api_


class ItemEvent(enum.Enum):
    Created = enum.auto()
    Deleted = enum.auto()
    Modified = enum.auto()
    Moved = enum.auto()


class NewFileTreeHandler(qt.QObject):
    # Signals
    tree_structure_completed = qt.pyqtSignal(dict, dict)
    stopped = qt.pyqtSignal()
    file_analysis_change = qt.pyqtSignal(object, int)
    file_inclusion_change = qt.pyqtSignal(object, int)
    file_linking_change = qt.pyqtSignal(object, int)
    hdir_inclusion_change = qt.pyqtSignal(object, int)
    send_items_signal = qt.pyqtSignal(list)

    # Constants
    SKIP_DIRECTORIES = [
        ".beetle",
        "template",
    ]
    CONFIG_GENERATED_VERSION = 1
    CONFIG_MINIMUM_VERSION = 1

    # Attributes
    __directories = None
    __observer = None

    def create_directory_item(self, name, full_path, relative_path, icon=None):
        new_directory = {
            "type": "directory",
            "name": name,
            "html": name,
            "node": None,
            "icon": icon,
            "path": relative_path,
            "relative-path": relative_path,
            "absolute-path": full_path,
            "directories": {},
            "files": {},
            "source-analysis-status-file": None,
            "source-analysis-status-file-locked": False,
            "source-analysis-status-hdir": None,
            "source-analysis-status-hdir-files": None,
            "source-analysis-status-hdir-manual": None,
            "source-analysis-mode": None,
        }
        return new_directory

    def create_file_item(
        self, name, full_path, relative_path, icon=None, base_directory=None
    ):
        if not os.path.isfile(full_path):
            return None
        try:
            new_file = {
                "type": "file",
                "name": name,
                "html": name,
                "node": None,
                "icon": icon,
                "path": relative_path,
                "relative-path": relative_path,
                "absolute-path": full_path,
                "source-analysis-status-file": None,
                "source-analysis-status-file-manual": None,
                "source-analysis-status-hdir": None,
                "source-analysis-type": None,
                "source-analysis-mode": None,
            }
            # Check extension for special inclusion status
            self.source_file_check(new_file, base_directory)

            return new_file
        except:
            return None

    def source_file_check(self, item, base_directory=None):
        relative_path = item["relative-path"]
        start, extension = os.path.splitext(relative_path)

        skip_analyzer = False
        if base_directory:
            relative_path = functions.unixify_path_remove(
                relative_path, base_directory
            )
            if any(
                [
                    relative_path.startswith(x)
                    for x in self.__directories["excluded"]
                ]
            ):
                skip_analyzer = True

        if not skip_analyzer:
            if extension.lower() in data.VALID_HEADER_FILE_EXTENSIONS:
                item["source-analysis-type"] = "header"
                item["source-analysis-status-hdir"] = (
                    source_analyzer.inclusion_status_excluded
                )
                item["source-analysis-status-file"] = None
            elif extension.lower() in data.VALID_SOURCE_FILE_EXTENSIONS:
                item["source-analysis-type"] = "source"
                item["source-analysis-status-hdir"] = None
                item["source-analysis-status-file"] = (
                    source_analyzer.inclusion_status_excluded
                )

    def __init__(self, parent, initial_path, exclude_directories) -> None:
        super().__init__(parent)
        self.__running = True
        # Initialize watched directories / files
        self.__directories = {
            "initial": initial_path,
            "excluded": exclude_directories + self.SKIP_DIRECTORIES,
        }
        # Connect signals
        data.signal_dispatcher.source_analyzer.file_analysis_change_sig.connect(
            self.__file_analysis_change
        )
        data.signal_dispatcher.source_analyzer.file_inclusion_change_sig.connect(
            self.__file_inclusion_change
        )
        data.signal_dispatcher.source_analyzer.file_linking_change_sig.connect(
            self.__file_linking_change
        )
        data.signal_dispatcher.source_analyzer.hdir_inclusion_change_sig.connect(
            self.__hdir_inclusion_change
        )

        self.__item_queue = multiprocessing.Queue()
        self.__item_lock = multiprocessing.Lock()

    def start(self, *args):
        try:
            # Initialize file event handler
            event_handler = FileTreeEventHandler(self.__directories["initial"])
            event_handler.emit_all_signal.connect(self.process_items)
            # Initialize the observer
            self.__observer = watchdog.observers.Observer()
            self.__observer.schedule(
                event_handler, self.__directories["initial"], recursive=True
            )
            self.__observer.start()

            # Create initial tree
            init_directory = self.__directories["initial"]
            if not os.path.isdir(init_directory):
                raise Exception(
                    "[NewFileTreeHandler] Directory does not exist: '{}'".format(
                        self.__directories["initial"]
                    )
                )
            init_tree_structure, directory_count, file_count = (
                functions.get_directory_structure(init_directory)
            )
            prepared_tree_structure, flat_item_dictionary = (
                self.__prepare_tree_structure(
                    init_directory,
                    init_tree_structure,
                    directory_count,
                    file_count,
                )
            )
            self.tree_structure_completed.emit(
                prepared_tree_structure, flat_item_dictionary
            )
        except Exception as ex:
            traceback.print_exc()
            data.signal_dispatcher.file_tree_watchdog_observer_error.emit(
                str(ex)
            )

    special_directory_icons = {
        ".beetle": "icons/folder/closed/beetle.png",
        "build": "icons/folder/closed/build.png",
    }

    def get_directory_icon(self, directory_path) -> str:
        "Get a relative path to an icon"
        icon_relpath = "icons/folder/closed/folder.png"
        relative_path = functions.unixify_path_remove(
            directory_path, self.__directories["initial"]
        )
        if relative_path == ".":
            icon_relpath = "icons/folder/closed/chip.png"
        elif relative_path in self.special_directory_icons.keys():
            icon_relpath = self.special_directory_icons[relative_path]
        return icon_relpath

    def get_file_icon(self, file_path) -> str:
        "Get a relative path to an icon"
        file_type = functions.get_file_type(file_path)
        icon_relpath = iconfunctions.get_language_icon_relpath(file_type)
        return icon_relpath

    def __prepare_tree_structure(
        self, base_directory, tree_structure, directory_count, file_count
    ):
        # Try to reload stored setting
        config_file = "{}/{}".format(
            data.current_project.get_proj_rootpath(),
            data.filetree_config_relative_path,
        )
        config_flat_item_dictionary = {}
        if os.path.isfile(config_file):
            try:
                # Load the data
                config_data = functions.load_json_file(config_file)
                if config_data is not None:
                    if "version-generated" not in config_data.keys():
                        ##
                        ## Pre version 1 style config file
                        ##
                        try:
                            project_path = config_data["path"]

                            # Create a flat representation of the config settings
                            def config_recurse(_in, path):
                                if "relative-path" not in _in.keys():
                                    _in["relative-path"] = (
                                        functions.unixify_path_remove(
                                            _in["path"], project_path
                                        )
                                    )
                                path = _in["path"]
                                relative_path = _in["relative-path"]
                                config_flat_item_dictionary[relative_path] = _in
                                if "directories" in _in.keys():
                                    for k, v in _in["directories"].items():
                                        config_recurse(v, path)
                                if "files" in _in.keys():
                                    for k, v in _in["files"].items():
                                        config_recurse(v, path)

                            config_recurse(config_data, base_directory)
                            data.signal_dispatcher.notify_success.emit(
                                "[Filetree] Config file loaded successfully."
                            )
                        except:
                            traceback.print_exc()
                            data.signal_dispatcher.notify_error.emit(
                                "[Filetree] Opening a pre-version-1 configuration file could not be done!"
                                + "           All manual lock information will be reset!"
                            )
                    else:
                        ##
                        ## New style config
                        ##
                        config_generated_minimum = config_data[
                            "version-generated"
                        ]
                        config_version_minimum = config_data["version-minimum"]
                        config_flat_item_dictionary = config_data["items"]
                        if (
                            self.CONFIG_GENERATED_VERSION
                            < config_version_minimum
                        ):
                            data.signal_dispatcher.notify_error.emit(
                                "[Filetree] Opening a config file version '{}' which is incompatible with the current {} version!"
                                + "           There might be incompatibilities between locking information, please check them manually!"
                            )
            except:
                traceback.print_exc()
                config_flat_item_dictionary = {}

        counter = 0
        data.signal_dispatcher.source_analyzer.file_tree_handler_initialization_report.emit(
            counter, file_count, "processing file: %v/%m"
        )

        # Create the main directory node
        flat_item_dictionary = {}
        relative_base_directory = functions.unixify_path_remove(
            base_directory, self.__directories["initial"]
        )
        prepared_tree_structure = self.create_directory_item(
            name=relative_base_directory,
            full_path=base_directory,
            relative_path=relative_base_directory,
        )
        flat_item_dictionary[relative_base_directory] = prepared_tree_structure

        # Recurse to all items in directory
        def recurse(_in, _out):
            nonlocal counter
            for key, item in _in.items():
                # Directory
                directory_path = item["//full//"]
                relative_path = item["//relative//"]
                _out["directories"][key] = self.create_directory_item(
                    name=key,
                    full_path=directory_path,
                    relative_path=relative_path,
                    icon=self.get_directory_icon(directory_path),
                )
                out_directory = _out["directories"][key]
                flat_item_dictionary[relative_path] = out_directory

                # Files
                for k, v in item["//files//"].items():
                    counter += 1
                    if (counter % 100) == 0:
                        data.signal_dispatcher.source_analyzer.file_tree_handler_initialization_report.emit(
                            counter, file_count, "processing file: %v/%m"
                        )

                    if "\\?" in v["//full//"] or "/?" in v["//full//"]:
                        continue

                    file_path = v["//full//"]
                    relative_path = v["//relative//"]
                    new_file = self.create_file_item(
                        name=k,
                        full_path=file_path,
                        relative_path=relative_path,
                        icon=self.get_file_icon(file_path),
                        base_directory=relative_base_directory,
                    )
                    if new_file is not None:
                        # Add to lists
                        out_directory["files"][k] = new_file
                        flat_item_dictionary[relative_path] = new_file

                # Recurse further if needed
                if len(item["//directories//"]) > 0:
                    recurse(item["//directories//"], out_directory)

        functions.performance_timer_start()
        recurse(tree_structure, prepared_tree_structure)
        functions.performance_timer_show("tree-structure-recurse")
        #        import json
        #        json_string = json.dumps(prepared_tree_structure, indent=2, ensure_ascii=False)
        #        print(json_string)

        data.signal_dispatcher.source_analyzer.file_tree_handler_initialization_report.emit(
            file_count, file_count, "processing file: %v/%m"
        )

        # Load the settings from the config file
        try:
            copy_keys = (
                "source-analysis-status-file-manual",
                "source-analysis-status-hdir-manual",
            )

            for k, v in flat_item_dictionary.items():
                if k in config_flat_item_dictionary.keys():
                    config_item_data = config_flat_item_dictionary[k]
                    for ck in copy_keys:
                        if ck in v.keys() and ck in config_item_data.keys():
                            config_state = config_item_data[ck]
                            v[ck] = config_state
                            if config_state is not None:
                                if v["type"] == "directory":
                                    status = STATUSES_HDIR[config_state]
                                    set_hdir_status(v, status)
                                else:
                                    status = STATUSES_FILE[config_state]
                                    set_file_status(v, status)
        except:
            data.signal_dispatcher.notify_error.emit(
                "[Filetree] There was an error trying to apply manual locks to files!"
                "           Some locking information has probably been lost! Please re-check your manual locks!"
            )

        return prepared_tree_structure, flat_item_dictionary

    def __send_to_source_analyzer(self, flat_tree_structure):
        """"""
        # Start the source analyzer. The signal emitted below triggers the following method from
        # the SourceAnalysisCommunicator() in 'sourceanalyzerinterface.py':
        #   > __start_stop_engine_conditionally()
        # This method starts the SA engine if certain minimal requirements are met (such as the
        # existence of a makefile, the selection of a build folder, ..). Otherwise, it stops the
        # engine (if it was already running).
        # NOTE:
        # Even if the SA engine is not started here, you can still send the hdirs and source files
        # to the engine. I believe Johan's engine will then simply queue them for processing later
        # on.
        data.signal_dispatcher.source_analyzer.start_stop_engine_conditionally_sig.emit()

        # Get heuristics for special inclusion/exclusion
        heuristics = get_source_analysis_heuristics()

        success = False
        while not success:
            try:
                # Send all directories and files to source analyzer
                for k, v in flat_tree_structure.items():
                    if v["type"] == "directory":
                        self.source_analyzer_hdir_set(v, heuristics=heuristics)
                    else:
                        self.source_analyzer_file_add(v, heuristics=heuristics)

                # Generate makefile
                self.generate_makefile(flat_tree_structure)
                success = True
            except:
                time.sleep(0.1)

        return

    def source_analyzer_hdir_set(self, item, heuristics=None):
        path = item["relative-path"]
        if any([path.startswith(x) for x in self.__directories["excluded"]]):
            return
        if heuristics is None:
            heuristics = get_source_analysis_heuristics()
        # Set the inclusion state
        state = get_heuristics_state(path, "directory", heuristics)
        # Manual-mode
        if item["source-analysis-status-hdir-manual"] is not None:
            state = STATUSES_HDIR[item["source-analysis-status-hdir-manual"]]
        # Send hdir mode to the source analyzer
        data.signal_dispatcher.source_analyzer.set_hdir_mode_sig.emit(
            path, state, None
        )

    def source_analyzer_file_add(self, item, heuristics=None):
        relative_path = item["relative-path"]
        #        name, extension = os.path.splitext(relative_path.lower())
        #        if extension.lower() in data.VALID_SOURCE_FILE_EXTENSIONS:
        # !!!!!!!!!!!!!!!!!!!!!!!!!! #
        # All files now passed to SA #
        # !!!!!!!!!!!!!!!!!!!!!!!!!! #
        if any(
            [
                relative_path.startswith(x)
                for x in self.__directories["excluded"]
            ]
        ):
            return
        # Set the inclusion state
        state = get_heuristics_state(relative_path, "file", heuristics)
        # Manual-mode
        if item["source-analysis-status-file-manual"] is not None:
            state = STATUSES_FILE[item["source-analysis-status-file-manual"]]
        # Send the file to the source analyzer
        data.signal_dispatcher.source_analyzer.add_file_sig.emit(
            relative_path, state, None
        )
        return

    @qt.pyqtSlot(object, int)
    def __file_inclusion_change(self, file_abspath_or_obj, status):
        try:
            file_abspath_or_obj = functions.unixify_path_remove(
                file_abspath_or_obj, self.__directories["initial"]
            )
        except:
            pass
        self.file_inclusion_change.emit(file_abspath_or_obj, status)

    @qt.pyqtSlot(object, int)
    def __file_linking_change(self, file_abspath_or_obj, status):
        try:
            file_abspath_or_obj = functions.unixify_path_remove(
                file_abspath_or_obj, self.__directories["initial"]
            )
        except:
            pass
        self.file_linking_change.emit(file_abspath_or_obj, status)

    @qt.pyqtSlot(object, int)
    def __file_analysis_change(self, file_abspath_or_obj, status):
        self.file_analysis_change.emit(file_abspath_or_obj, status)

    @qt.pyqtSlot(object, int)
    def __hdir_inclusion_change(self, hdir_abspath_or_obj, status):
        try:
            hdir_abspath_or_obj = functions.unixify_path_remove(
                hdir_abspath_or_obj, self.__directories["initial"]
            )
        except:
            pass
        self.hdir_inclusion_change.emit(hdir_abspath_or_obj, status)

    def stop(self, *args):
        self.__running = False

        # Stop observer
        if self.__observer is not None:
            self.__observer.stop()
            self.__observer.join()

        # Stop makefile timer
        if (
            hasattr(self, "generate_makefile_timer")
            and self.generate_makefile_timer is not None
        ):
            while self.generate_makefile_timer.isActive():
                qt.QThread.msleep(50)
            self.generate_makefile_timer.stop()
            try:
                self.generate_makefile_timer.timeout.disconnect()
            except:
                pass
            self.generate_makefile_timer = None

        # Fire stopped signal
        self.stopped.emit()

    @qt.pyqtSlot(dict)
    def send_to_source_analyzer(self, tree_structure):
        self.__send_to_source_analyzer(tree_structure)

    @qt.pyqtSlot(dict)
    def generate_makefile(self, flat_tree_structure):
        if not hasattr(self, "generate_makefile_timer"):
            self.generate_makefile_timer = qt.QTimer(self)
            self.generate_makefile_timer.setInterval(300)
            self.generate_makefile_timer.setSingleShot(True)
            self.generate_makefile_timer.timeout.connect(
                lambda *args: self.__generate_makefile(flat_tree_structure)
            )
        else:
            self.generate_makefile_timer.stop()
            try:
                self.generate_makefile_timer.timeout.disconnect()
            except:
                pass
            self.generate_makefile_timer.timeout.connect(
                lambda *args: self.__generate_makefile(flat_tree_structure)
            )
        self.generate_makefile_timer.start()

    def __generate_makefile(self, flat_tree_structure):
        return generate_makefile(
            flat_tree_structure, self.__directories["initial"]
        )

    qt.pyqtSlot(object)

    def process_items(self, items):
        try:
            for item in items:
                if item["type"] == ItemEvent.Created:
                    relative_path = functions.unixify_path_remove(
                        item["src_path"], self.__directories["initial"]
                    )
                    if item["is_directory"]:
                        new_item = self.create_directory_item(
                            name=os.path.basename(item["src_path"]),
                            full_path=item["src_path"],
                            relative_path=relative_path,
                            icon=self.get_directory_icon(item["src_path"]),
                        )
                    else:
                        new_item = self.create_file_item(
                            name=os.path.basename(item["src_path"]),
                            full_path=item["src_path"],
                            relative_path=relative_path,
                            icon=self.get_file_icon(item["src_path"]),
                            base_directory=self.__directories["initial"],
                        )
                    if new_item is not None:
                        item = {
                            "type": ItemEvent.Created,
                            "is_synthetic": item["is_synthetic"],
                            "is_directory": item["is_directory"],
                            "src_path": item["src_path"],
                            "new_item": new_item,
                        }
                        self.__item_queue.put(item)
                        self.__send_item_from_queue()
                else:
                    self.__item_queue.put(item)
                    self.__send_item_from_queue()

                    if item["type"] == ItemEvent.Moved:
                        # Send global signal that an item has been renamed
                        if item["is_directory"]:
                            data.signal_dispatcher.file_folder.folder_renamed_sig.emit(
                                item["src_path"],
                                item["dest_path"],
                                item["is_synthetic"],
                            )
                        else:
                            data.signal_dispatcher.file_folder.file_renamed_sig.emit(
                                item["src_path"],
                                item["dest_path"],
                                item["is_synthetic"],
                            )
        except:
            traceback.print_exc()

    retry_flag = False

    def __send_item_from_queue(self):
        if self.__item_lock.acquire(False):
            item_list = []
            while True:
                try:
                    item = self.__item_queue.get_nowait()

                    if item["type"] == ItemEvent.Created:
                        is_synthetic = item["is_synthetic"]
                        is_directory = item["is_directory"]
                        src_path = item["src_path"]
                        new_item = item["new_item"]
                        item_list.append(
                            (
                                ItemEvent.Created,
                                is_synthetic,
                                is_directory,
                                src_path,
                                new_item,
                            )
                        )

                    elif item["type"] == ItemEvent.Deleted:
                        is_synthetic = item["is_synthetic"]
                        is_directory = item["is_directory"]
                        src_path = item["src_path"]
                        item_list.append(
                            (
                                ItemEvent.Deleted,
                                is_synthetic,
                                is_directory,
                                src_path,
                            )
                        )

                    elif item["type"] == ItemEvent.Modified:
                        is_synthetic = item["is_synthetic"]
                        is_directory = item["is_directory"]
                        src_path = item["src_path"]
                        item_list.append(
                            (
                                ItemEvent.Modified,
                                is_synthetic,
                                is_directory,
                                src_path,
                            )
                        )

                    elif item["type"] == ItemEvent.Moved:
                        is_synthetic = item["is_synthetic"]
                        is_directory = item["is_directory"]
                        src_path = item["src_path"]
                        dest_path = item["dest_path"]
                        item_list.append(
                            (
                                ItemEvent.Moved,
                                is_synthetic,
                                is_directory,
                                src_path,
                                dest_path,
                            )
                        )

                    else:
                        raise Exception(
                            "[NewFileTreeHandler] Unknown item type: {}".format(
                                item["type"]
                            )
                        )

                except queue.Empty:
                    if not self.retry_flag:
                        self.retry_flag = True
                        qt.QTimer.singleShot(100, self.__send_item_from_queue)
                    else:
                        self.retry_flag = False
                    break
                except:
                    traceback.print_exc()
            if len(item_list) > 0:
                self.send_items_signal.emit(item_list)
            self.__item_lock.release()


class FileTreeEventHandler(watchdog.events.FileSystemEventHandler, qt.QObject):
    # Signals
    on_error_signal = qt.pyqtSignal()
    emit_all_signal = qt.pyqtSignal(object)
    __timer_restart_signal = qt.pyqtSignal()

    # Private attributes
    __debug = False
    __base_directory = False
    __item_list = None

    # Public attributes
    emit_queue = None
    emit_timer = None
    emit_timer_constant = 300

    def __init__(self, initial_directory):
        watchdog.events.FileSystemEventHandler.__init__(self)
        qt.QObject.__init__(self)

        self.__base_directory = initial_directory

        # Emit queue
        self.emit_queue = multiprocessing.Queue()

        # Emit timer
        self.emit_timer = qt.QTimer()
        self.emit_timer.setInterval(self.emit_timer_constant)
        self.emit_timer.setSingleShot(True)
        self.emit_timer.timeout.connect(self.__emit_all)
        self.__timer_restart_signal.connect(self.__emit_timer_restart)

        # Special error signal processing
        data.signal_dispatcher.file_watcher_on_error.connect(self.on_error)

        # Manual checking stuff
        self.__manual_check_lock = multiprocessing.Lock()

    def __emit_timer_restart(self):
        if self.emit_timer.isActive():
            self.emit_timer.stop()
        self.emit_timer.start()

    def __emit_queue_add(self, item):
        self.emit_queue.put(item)
        self.__timer_restart_signal.emit()

    def __emit_all(self):
        empty = False
        items = []
        while not empty:
            try:
                item = self.emit_queue.get(block=False)
                items.append(item)
            except queue.Empty:
                empty = True
                self.__manual_check_reset()
                if len(items) > 0:
                    self.emit_all_signal.emit(items)

    def __manual_check_reset(self):
        if not hasattr(self, "manual_check_timer"):
            self.manual_check_timer = qt.QTimer(self)
            self.manual_check_timer.setInterval(500)
            self.manual_check_timer.setSingleShot(True)
            self.manual_check_timer.timeout.connect(self.__manual_check_execute)
        self.manual_check_timer.stop()
        self.manual_check_timer.start()

    #        print("RESET")

    def __manual_check_execute(self):
        #        print("PRE-LOCK")
        if self.__manual_check_lock.acquire(False):
            #            print("LOCK")
            with concurrent.futures.ProcessPoolExecutor() as executor:
                future = executor.submit(
                    check_item_list,  # check_item_tree,
                    self.__base_directory,
                    self.__item_list,
                )
                future.add_done_callback(self.__manual_check_callback)

    def __manual_check_callback(self, future):
        item_list, event_list = future.result()
        self.__item_list = item_list
        for _type, event in event_list:
            #            print("-->>", _type, event)
            if _type == "created":
                self.on_created(event)
            elif _type == "deleted":
                self.on_deleted(event)
            else:
                raise Exception(
                    f"[FileTreeEventHandler] Unknown file detection event: {_type}"
                )
        #        print("PRE-RELEASE")
        self.__manual_check_lock.release()

    #        print("RELEASE")

    def on_created(self, event):
        item = {
            "type": ItemEvent.Created,
            "is_directory": event.is_directory,
            "is_synthetic": event.is_synthetic,
            "src_path": functions.unixify_path(event.src_path),
            "dest_path": None,
        }
        self.__emit_queue_add(item)
        if self.__debug:
            print(item)

    def on_deleted(self, event):
        item = {
            "type": ItemEvent.Deleted,
            "is_directory": event.is_directory,
            "is_synthetic": event.is_synthetic,
            "src_path": functions.unixify_path(event.src_path),
            "dest_path": None,
        }
        self.__emit_queue_add(item)
        if self.__debug:
            print(item)

    def on_modified(self, event):
        item = {
            "type": ItemEvent.Modified,
            "is_directory": event.is_directory,
            "is_synthetic": event.is_synthetic,
            "src_path": functions.unixify_path(event.src_path),
            "dest_path": None,
        }
        self.__emit_queue_add(item)
        if self.__debug:
            print(item)

    def on_moved(self, event):
        item = {
            "type": ItemEvent.Moved,
            "is_directory": event.is_directory,
            "is_synthetic": event.is_synthetic,
            "src_path": functions.unixify_path(event.src_path),
            "dest_path": functions.unixify_path(event.dest_path),
        }
        self.__emit_queue_add(item)
        if self.__debug:
            print(item)

    def on_error(self):
        self.on_error_signal.emit()
        print("[FileTreeEventHandler] ERROR")


if os_checker.is_os("windows"):
    import watchdog.observers.winapi
    import watchdog.observers.read_directory_changes

    original_read_events = watchdog.observers.winapi.read_events

    def custom_read_events(handle, path, *, recursive):
        buf, nbytes = watchdog.observers.winapi.read_directory_changes(
            handle=handle, path=path, recursive=recursive
        )
        events = watchdog.observers.winapi._parse_event_buffer(buf, nbytes)
        if nbytes == 0:
            data.signal_dispatcher.file_watcher_on_error.emit()
        return [
            watchdog.observers.winapi.WinAPINativeEvent(action, src_path)
            for action, src_path in events
        ]

    watchdog.observers.winapi.read_events = custom_read_events
    watchdog.observers.read_directory_changes.read_events = custom_read_events


def check_item_tree(base_directory, item_tree):
    event_list = []
    current_tree = directory_to_dict(base_directory)

    # Check differences if manual signal emitting is needed
    if item_tree is not None:
        results = compare_directories(item_tree, current_tree)
        for path, item_type, event_type in results:
            if event_type == ItemEvent.Created:
                event = watchdog.events.FileCreatedEvent(
                    src_path=functions.unixify_path_join(base_directory, path)
                )
                event.is_directory = item_type == "directory"
                event.is_synthetic = False
                event_list.append(("created", event))
            elif event_type == ItemEvent.Deleted:
                event = watchdog.events.FileDeletedEvent(
                    src_path=functions.unixify_path_join(base_directory, path)
                )
                event.is_directory = item_type == "directory"
                event.is_synthetic = False
                event_list.append(("deleted", event))
            else:
                raise Exception(
                    f"[FileTreeEventHandler] Unknown tree item type: {event_type}"
                )

    return current_tree, event_list


def check_item_list(base_directory, item_list):
    event_list = []
    current_list = list_files_and_directories_recursively(base_directory)

    # Check differences if manual signal emitting is needed
    if item_list is not None:
        results = compare_file_lists(item_list, current_list)
        for path, item_type in results["created"]:
            event = watchdog.events.FileCreatedEvent(
                src_path=functions.unixify_path_join(base_directory, path)
            )
            event.is_directory = item_type == "directory"
            event.is_synthetic = False
            event_list.append(("created", event))
        for path, item_type in results["deleted"]:
            event = watchdog.events.FileDeletedEvent(
                src_path=functions.unixify_path_join(base_directory, path)
            )
            event.is_directory = item_type == "directory"
            event.is_synthetic = False
            event_list.append(("deleted", event))

    return current_list, event_list


STATUSES_HDIR = {
    None: source_analyzer.hdir_mode_automatic,
    "force-included": source_analyzer.hdir_mode_include,
    "force-excluded": source_analyzer.hdir_mode_exclude,
}

STATUSES_FILE = {
    None: source_analyzer.file_mode_automatic,
    "force-included": source_analyzer.file_mode_include,
    "force-excluded": source_analyzer.file_mode_exclude,
}


def set_hdir_status(item_data, status, reset_manual_status=False):
    path = item_data["relative-path"]
    data.signal_dispatcher.source_analyzer.set_hdir_mode_sig.emit(
        path, status, None
    )
    if reset_manual_status:
        item_data["source-analysis-status-hdir-manual"] = None
    else:
        if status == source_analyzer.hdir_mode_automatic:
            item_data["source-analysis-status-hdir-manual"] = None
        elif status == source_analyzer.hdir_mode_include:
            item_data["source-analysis-status-hdir-manual"] = "force-included"
        elif status == source_analyzer.hdir_mode_exclude:
            item_data["source-analysis-status-hdir-manual"] = "force-excluded"
        else:
            raise Exception(
                f"[Filetree] Setting unknown hdir status: '{status}'"
            )


def set_file_status(item_data, status, reset_manual_status=False):
    path = item_data["path"]
    data.signal_dispatcher.source_analyzer.set_file_mode_sig.emit(path, status)
    if reset_manual_status:
        item_data["source-analysis-status-file-manual"] = None
        parent_data = item_data["node"].parent().get_data()
        if "source-analysis-status-file-locked" in parent_data:
            parent_data["source-analysis-status-file-locked"] = False
    else:
        if status == source_analyzer.file_mode_automatic:
            item_data["source-analysis-status-file-manual"] = None
            if (
                item_data["node"] is not None
                and item_data["node"].parent() is not None
            ):
                parent_data = item_data["node"].parent().get_data()
                if "source-analysis-status-file-locked" in parent_data:
                    parent_data["source-analysis-status-file-locked"] = False
        elif status == source_analyzer.file_mode_include:
            item_data["source-analysis-status-file-manual"] = "force-included"
            if (
                item_data["node"] is not None
                and item_data["node"].parent() is not None
            ):
                parent_data = item_data["node"].parent().get_data()
                if "source-analysis-status-file-locked" in parent_data:
                    parent_data["source-analysis-status-file-locked"] = True
        elif status == source_analyzer.file_mode_exclude:
            item_data["source-analysis-status-file-manual"] = "force-excluded"
            if (
                item_data["node"] is not None
                and item_data["node"].parent() is not None
            ):
                parent_data = item_data["node"].parent().get_data()
                if "source-analysis-status-file-locked" in parent_data:
                    parent_data["source-analysis-status-file-locked"] = True
        else:
            raise Exception(
                f"[Filetree] Setting unknown source file status: '{status}'"
            )


def generate_makefile_async(
    flat_tree_structure_copy: Dict[any, any], project_path: str
) -> None:
    try:
        # Filetree makefile path
        filetree_mk_abspath = (
            data.current_project.get_treepath_seg().get_default_abspath(
                "FILETREE_MK"
            )
        )
        # Remove all Qt nodes
        functions.remove_all_dict_keys(flat_tree_structure_copy, "node")
        # Start the process
        p = multiprocessing.Process(
            target=generate_makefile,
            args=(
                flat_tree_structure_copy,
                project_path,
                None,
                False,
                filetree_mk_abspath,
            ),
            daemon=True,
        )
        p.start()
    except:
        traceback.print_exc()
        return


def generate_makefile(
    flat_tree_structure_copy,
    project_path: str,
    external_version: Optional[int] = None,
    template_only: bool = False,
    in_makefile_path: Optional[str] = None,
) -> Optional[str]:
    """Generate the 'filetree.mk' file used for building a project."""
    #    functions.performance_timer_start()

    if isinstance(external_version, int):
        version_number = external_version
    else:
        version_number = 7
        try:
            version_number = (
                data.current_project.get_version_seg().get_version_nr()
            )
        except:
            pass
    makefile_path = purefunctions.join_resources_dir_to_path(
        "hardware/filetree_mk.py"
    )
    try:
        my_module = purefunctions.load_module(makefile_path, {})
        makefile_template = my_module["get_filetree_mk_template"](
            version=version_number,
        )
    except:
        traceback.print_exc()
        return None
    if makefile_template is None:
        makefile_template = ""
    if template_only or (flat_tree_structure_copy is None):
        return makefile_template
    # Get the files for the selected version
    file_groups = {
        1: {
            "CFILES =": [],
            "CPPFILES =": [],
            "SFILES =": [],
            "HDIRS =": [],
        },
        2: {
            "CFILES =": [],
            "CPPFILES =": [],
            "SFILES =": [],
            "HDIRS =": [],
        },
        3: {
            "CFILES =": [],
            "CXXFILES =": [],
            "SFILES =": [],
            "HDIRS =": [],
        },
        4: {
            "CFILES =": [],
            "CXXFILES =": [],
            "SFILES =": [],
            "HDIRS =": [],
            "PROJECT_LOADLIBES =": [],
        },
        5: {
            "CFILES =": [],
            "CXXFILES =": [],
            "SFILES =": [],
            "HDIRS =": [],
            "PROJECT_LOADLIBES =": [],
        },
        6: {
            "C_OFILES =": [],
            "CXX_OFILES =": [],
            "S_OFILES =": [],
            "HDIR_FLAGS =": [],
            "PROJECT_LDLIBS =": [],
        },
        7: {
            "C_OFILES =": [],
            "CXX_OFILES =": [],
            "S_OFILES =": [],
            "HDIR_FLAGS =": [],
            "PROJECT_LDLIBS =": [],
        },
    }
    if version_number not in file_groups.keys():
        data.signal_dispatcher.notify_error.emit(
            f"[Filetree] Makefile version '{version_number}' not supported yet!"
        )
        return None

    def adjust_source_file(path, add_o_extension):
        if os.path.isabs(path):
            filtered_path = functions.unixify_path_remove(path, project_path)
        else:
            filtered_path = path
        if add_o_extension:
            filtered_path = "project/{}.o".format(filtered_path)
        return filtered_path

    def adjust_include_directory(path, add_minus_i_prefix):
        if os.path.isabs(path):
            filtered_path = functions.unixify_path_remove(path, project_path)
        else:
            filtered_path = path
        if add_minus_i_prefix:
            filtered_path = "-I$(SOURCE_DIR){}".format(filtered_path)
        return filtered_path

    def adjust_object_or_archive_file(path):
        if os.path.isabs(path):
            filtered_path = functions.unixify_path_remove(path, project_path)
        else:
            filtered_path = path
        adjusted_path = "$(SOURCE_DIR){}".format(filtered_path)
        return adjusted_path

    for ec in range(10):
        try:
            status_included = source_analyzer.inclusion_status_included
            for k, v in file_groups[version_number].items():
                # C source files
                if "C_OFILES" in k or "CFILES" in k:
                    for kk, vv in flat_tree_structure_copy.items():
                        if kk.lower().endswith(".c"):
                            if (
                                vv["source-analysis-status-file"]
                                == status_included
                            ):
                                f = adjust_source_file(kk, "C_OFILES" in k)
                                v.append(f)
                elif "CPPFILES" in k or "CXXFILES" in k or "CXX_OFILES" in k:
                    for kk, vv in flat_tree_structure_copy.items():
                        if (
                            kk.lower().endswith(".cpp")
                            or kk.lower().endswith(".cxx")
                            or kk.lower().endswith(".c++")
                            or kk.lower().endswith(".cc")
                        ):
                            if (
                                vv["source-analysis-status-file"]
                                == status_included
                            ):
                                f = adjust_source_file(kk, "CXX_OFILES" in k)
                                v.append(f)
                elif "SFILES" in k or "S_OFILES" in k:
                    for kk, vv in flat_tree_structure_copy.items():
                        if kk.lower().endswith(".s") or kk.lower().endswith(
                            ".asm"
                        ):
                            if (
                                vv["source-analysis-status-file"]
                                == status_included
                            ):
                                f = adjust_source_file(kk, "S_OFILES" in k)
                                v.append(f)
                elif "HDIRS" in k or "HDIR_FLAGS" in k:
                    for kk, vv in flat_tree_structure_copy.items():
                        if vv["type"] == "directory":
                            status = vv["source-analysis-status-hdir"]
                            if status == status_included:
                                d = adjust_include_directory(
                                    kk, "HDIR_FLAGS" in k
                                )
                                v.append(d)
                elif "PROJECT_LDLIBS" in k or "PROJECT_LOADLIBES" in k:
                    for kk, vv in flat_tree_structure_copy.items():
                        if kk.lower().endswith(".o") or kk.lower().endswith(
                            ".a"
                        ):
                            if (
                                vv["source-analysis-status-file"]
                                == status_included
                            ):
                                f = adjust_object_or_archive_file(kk)
                                v.append(f)
                else:
                    data.signal_dispatcher.notify_error.emit(
                        f"[Filetree] Unknown makefile item: '{k}'"
                    )
                    return None
            break
        except:
            traceback.print_exc()
            time.sleep(0.100)
    else:
        data.signal_dispatcher.notify_error.emit(
            "[Filetree] Safety counter reached when trying to create makefile!"
        )
        return None

    # Add the data to the makefile template
    for k, v in file_groups[version_number].items():
        if len(v) == 0:
            continue
        filtered_list = list(set(v))
        filtered_list.sort()
        replace_text = "{} \\\n{}".format(k, " \\\n".join(filtered_list))
        makefile_template = makefile_template.replace(k, replace_text)

    # Get makefile data
    if in_makefile_path:
        filetree_mk_abspath = in_makefile_path
    else:
        treepath_seg = data.current_project.get_treepath_seg()
        filetree_mk_abspath = treepath_seg.get_default_abspath("FILETREE_MK")

    # Check if there are changes
    changed_flag = True
    if os.path.isfile(filetree_mk_abspath):
        content = ""
        with open(
            filetree_mk_abspath,
            "r",
            encoding="utf-8",
            newline="\n",
            errors="replace",
        ) as f:
            content = f.read()
        changed_flag = content != makefile_template

    # Write to file
    if changed_flag:
        if os.path.isdir(os.path.dirname(filetree_mk_abspath)):
            with open(
                filetree_mk_abspath,
                "w+",
                encoding="utf-8",
                newline="\n",
                errors="replace",
            ) as f:
                f.write(makefile_template)

    #    functions.performance_timer_show("generate-makefile")

    # Returned only for Kristof's use
    return makefile_template


def get_source_analysis_heuristics() -> Dict[str, List[str]]:
    """Get heuristics for special inclusion/exclusion."""
    # Observe the chosen chip and board for the current project. If the current project isn't
    # properly initiated, print an error message and return empty heuristics.
    if (
        (data.current_project is None)
        or (data.current_project.get_chip() is None)
        or (data.current_project.get_board() is None)
    ):
        purefunctions.printc(
            f"\nERROR: get_source_analysis_heuristics() invoked while current project is not "
            f"properly initiated!\n",
            color="error",
        )
        return {
            "required_source_files": [],
            "required_header_directories": [],
            "rejected_source_files": [],
            "rejected_header_directories": [],
        }

    # Extract 'chipname' and 'boardname'.
    chipname: Optional[str] = data.current_project.get_chip().get_name()
    boardname: Optional[str] = data.current_project.get_board().get_name()
    if (chipname is None) or (chipname.lower() == "none"):
        chipname = "custom"
    if (boardname is None) or (boardname.lower() == "none"):
        boardname = "custom"

    # Extract chip dictionary (from the corresponding json-file), potentially overridden by values
    # from the board file.
    chip_dict = _hardware_api_.HardwareDB().get_chip_dict(
        chip=chipname,
        board=boardname,
    )
    return {
        "required_source_files": chip_dict["heuristics"]["required_srcfiles"],
        "required_header_directories": chip_dict["heuristics"][
            "required_hdirs"
        ],
        "rejected_source_files": chip_dict["heuristics"]["rejected_srcfiles"],
        "rejected_header_directories": chip_dict["heuristics"][
            "rejected_hdirs"
        ],
    }


def get_heuristics_state(relative_path, _type, heuristics=None):
    # Get heuristics for special inclusion/exclusion
    if heuristics is None:
        heuristics = get_source_analysis_heuristics()

    """
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        Pattern matching with the heuristics is now FULLY CASE-INSESITIVE
        
        It would be better to make it case sensitive as per Johan's information:
            Case sometimes matters, for example: a .S file is preprocessed, and a .s file is not preprocessed,
            even on Windows. A .C file is C++ code, and a .c file is C code.
        
        On Kristof's information that currently all heuristics are based on CASE-INSENSITIVITY:
            This may make heuristics OS independent, but it does not make toolchain behavior case independent.
            On the longer term, since the toolchain is case-dependent even on Windows, it would be better to
            support case-sensitive heuristics.
            Let's document this issue in the python code where the matching is implemented,
            so that we can easily find the answer when we run into this problem again in the future.
            When we encounter a case where heuristics absolutely need to be case sensitive,
            we will have to decide on a solution; maybe add a marker for case-sensitive patterns,
            or maybe check and fix all existing patterns. Checking all existing patterns is a lot of work,
            but would also allow us to verify which of these patterns is still required,
            with the current improvements in the SA
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    """
    relative_path_lowercase = (
        relative_path.lower()
    )  # READ ABOVE NOTE WHY THIS IS HERE!

    if _type == "directory":
        # Set the directory inclusion state
        # READ ABOVE NOTE WHY THE RELATIVE-PATH AND THE PATTERN IS LOWER-CASED!
        state = source_analyzer.hdir_mode_automatic
        if any(
            (
                fnmatch.fnmatch(relative_path_lowercase, pattern.lower())
                for pattern in heuristics["required_header_directories"]
            )
        ):
            state = source_analyzer.hdir_mode_include
        elif any(
            (
                fnmatch.fnmatch(relative_path_lowercase, pattern.lower())
                for pattern in heuristics["rejected_header_directories"]
            )
        ):
            state = source_analyzer.hdir_mode_exclude
    else:
        # Set the file inclusion state
        # READ ABOVE NOTE WHY THE RELATIVE-PATH AND THE PATTERN IS LOWER-CASED!
        state = source_analyzer.file_mode_automatic
        if any(
            (
                fnmatch.fnmatch(relative_path_lowercase, pattern.lower())
                for pattern in heuristics["rejected_source_files"]
            )
        ):
            state = source_analyzer.file_mode_exclude
        elif any(
            (
                fnmatch.fnmatch(relative_path_lowercase, pattern.lower())
                for pattern in heuristics["required_source_files"]
            )
        ):
            state = source_analyzer.file_mode_include
    return state


def directory_to_dict(directory):
    """Recursively converts a directory structure into a nested dictionary.

    Each item in the dictionary is stored as a "file" or "directory".
    """
    result = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            result[item] = "file"
        elif os.path.isdir(item_path):
            result[item] = directory_to_dict(item_path)
            result[item]["__type__"] = "directory"
    return result


def compare_directories(dir1, dir2, path=""):
    """Compares two directory structures represented by dictionaries and returns
    a list of differences.

    Each difference is a tuple (path_to_difference, file_or_directory,
    ItemEvent).
    """
    differences = []

    # Check for items in dir1 but not in dir2 and items in both that are directories
    for item in dir1:
        item_path = os.path.join(path, item)
        if item not in dir2:
            differences.append(
                (
                    item_path,
                    "file" if dir1[item] == "file" else "directory",
                    ItemEvent.Deleted,
                )
            )
        elif isinstance(dir1[item], dict) and isinstance(dir2[item], dict):
            differences.extend(
                compare_directories(dir1[item], dir2[item], item_path)
            )

    # Check for items in dir2 but not in dir1
    for item in dir2:
        item_path = os.path.join(path, item)
        if item not in dir1:
            differences.append(
                (
                    item_path,
                    "file" if dir2[item] == "file" else "directory",
                    ItemEvent.Created,
                )
            )

    return differences


def list_files_and_directories_recursively(directory):
    result = []

    for root, dirs, files in os.walk(directory):
        for name in dirs:
            result.append((os.path.join(root, name), "directory"))
        for name in files:
            result.append((os.path.join(root, name), "file"))

    return result


def compare_file_lists(list1, list2):
    set1 = set(list1)
    set2 = set(list2)

    only_in_list1 = set1 - set2
    only_in_list2 = set2 - set1

    differences = {
        "deleted": list(only_in_list1),  #'only_in_first': list(only_in_list1),
        "created": list(only_in_list2),  #'only_in_second': list(only_in_list2)
    }

    return differences
