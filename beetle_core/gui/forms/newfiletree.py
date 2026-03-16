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
import os
import copy
import shutil
import functools
import traceback
import multiprocessing
import qt
import data
import constants
import os_checker
import functions
import iconfunctions
import gui.templates.treewidget
import gui.templates.basemenu
import gui.templates.widgetgenerator
import gui.dialogs.popupdialog
import components.newfiletreehandler
import components.thesquid
import components.lockcache
import source_analyzer


class NewFiletree(gui.templates.treewidget.TreeWidget):
    IMAGES = {
        "hdir": {
            source_analyzer.inclusion_status_excluded: (
                "icons/include_chbx/h_files/magnifierlight.png"
            ),
            source_analyzer.inclusion_status_included: (
                "icons/include_chbx/h_files/magnifier.png"
            ),
            "force-included": "icons/include_chbx/h_files/magnifier_lock.png",
            "force-excluded": "icons/include_chbx/h_files/magnifier_cross.png",
        },
        "hdir-files": {
            source_analyzer.inclusion_status_excluded: (
                "icons/include_chbx/h_files/red.png"
            ),
            source_analyzer.inclusion_status_included: (
                "icons/include_chbx/h_files/green.png"
            ),
            "mixed": "icons/include_chbx/h_files/mix.png",
        },
        "file": {
            source_analyzer.inclusion_status_excluded: (
                "icons/include_chbx/c_files/red.png"
            ),
            source_analyzer.inclusion_status_included: (
                "icons/include_chbx/c_files/green.png"
            ),
            "mixed": "icons/include_chbx/c_files/mix.png",
            "force-included": "icons/include_chbx/c_files/green_lock.png",
            "force-excluded": "icons/include_chbx/c_files/red_lock.png",
        },
        "file-locked": {
            source_analyzer.inclusion_status_excluded: (
                "icons/include_chbx/c_files/red_lock.png"
            ),
            source_analyzer.inclusion_status_included: (
                "icons/include_chbx/c_files/green_lock.png"
            ),
            "mixed": "icons/include_chbx/c_files/mix_lock.png",
            "force-included": "icons/include_chbx/c_files/green_lock.png",
            "force-excluded": "icons/include_chbx/c_files/red_lock.png",
        },
    }
    PRINT_FILE_STATUS_CHANGES = False
    PRINT_MANUAL_CHANGES = False

    # Signals
    send_to_source_analyzer = qt.pyqtSignal(dict)
    stop_filetree_handler = qt.pyqtSignal()
    sa_file_add = qt.pyqtSignal(dict, object)
    sa_hdir_set = qt.pyqtSignal(dict, object)

    # Attributes
    __flat_tree_structure = None
    __new_filetree_handler = None
    __project_path = None
    __thread = None
    __processing_animation_frame = None
    __processing_label = None
    __processing_label_size = (50, 50)
    makefile_generation_in_progress: bool = False
    api = None

    def __init__(self, parent, main_form, project_path, exclude_directories=[]):
        # Initilaze super-class
        super().__init__(
            parent,
            main_form,
            "Filetree",
            iconfunctions.get_qicon("icons/gen/tree.png"),
            _type="file-tree",
        )
        # Inital path
        self.__project_path = project_path
        # FileTree handler
        self.__new_filetree_handler = (
            components.newfiletreehandler.NewFileTreeHandler(
                None,
                project_path,
                exclude_directories,
            )
        )
        self.__new_filetree_handler.tree_structure_completed.connect(
            self.__tree_structure_completed
        )
        self.__new_filetree_handler.file_inclusion_change.connect(
            self.__file_inclusion_change
        )
        self.__new_filetree_handler.file_linking_change.connect(
            self.__file_linking_change
        )
        self.__new_filetree_handler.file_analysis_change.connect(
            self.__file_analysis_change
        )
        self.__new_filetree_handler.hdir_inclusion_change.connect(
            self.__hdir_inclusion_change
        )
        self.__new_filetree_handler.send_items_signal.connect(
            self.__process_items
        )

        # Connect file tree signals to the handler
        self.send_to_source_analyzer.connect(
            self.__new_filetree_handler.send_to_source_analyzer
        )
        self.stop_filetree_handler.connect(self.__new_filetree_handler.stop)
        self.sa_file_add.connect(
            self.__new_filetree_handler.source_analyzer_file_add
        )
        self.sa_hdir_set.connect(
            self.__new_filetree_handler.source_analyzer_hdir_set
        )
        # Make first colums stretch to fill all available space
        # self.header().setSectionResizeMode(0, qt.QHeaderView.ResizeMode.Stretch)

        # Tree widget signals
        self.itemClicked.connect(self.__click)
        self.itemChanged.connect(self.__changed)
        self.editor_closed.connect(self.__editing_closed)

        # Add backwards compatibility calls for the old Filetree
        self.__init_backwards_compatibility()

        # API handler
        self.api = NewFiletreeAPI(self)
        self.__flat_tree_structure = None

        # Add loading indicator
        self.__add_loading_indicator()

        # Create thread
        self.__thread = qt.QThread(self)
        self.__new_filetree_handler.moveToThread(self.__thread)
        self.__thread.started.connect(self.__new_filetree_handler.start)
        self.__new_filetree_handler.stopped.connect(self.__thread.quit)
        self.__thread.finished.connect(self.__thread.deleteLater)
        self.__thread.finished.connect(self.__new_filetree_handler.stop)
        self.__thread.start()

    def self_destruct(self, *args):
        """The Filetree (like some other widgets) does not actually get
        destroyed, only hidden.

        That is why it should not destroy its attributes for monitoring the
        filesystem!
        """
        self.stop_filetree_handler.emit()
        if self.__thread is not None:
            self.__thread.quit()
            del self.__thread
        if self.__new_filetree_handler is not None:
            del self.__new_filetree_handler

    def __add_loading_indicator(self) -> None:
        """Show that the Filetree is loading when the project launches (instead
        of merely going blank)."""
        loading_node = gui.templates.treewidget.TreeNode(
            self, in_id=self.get_node_id_counter()
        )
        loading_node.setText(0, "Loading project files...")
        icon = iconfunctions.get_qicon("icons/gen/hourglass.svg")
        loading_node.setIcon(0, icon)
        loading_node_data = {
            "type": "loading-indicator",
            "html": "Loading project files...",
            "path": "loading-indicator",
            "relative-path": "loading-indicator",
            "absolute-path": "loading-indicator",
        }
        loading_node.set_data(loading_node_data)
        self.__loading_indicator = loading_node
        return

    def __remove_loading_indicator(self) -> None:
        """"""
        # Force clear all top level items - this is more reliable
        while self.topLevelItemCount() > 0:
            self.takeTopLevelItem(0)

        # Reset loading indicator reference
        if hasattr(self, "__loading_indicator"):
            self.__loading_indicator = None
        return

    def __refresh(self):
        self.update()

    def update_style(self):
        super().update_style()

        current_icons_path = iconfunctions.get_icon_source_folder() + "/"
        if data.theme["is_dark"]:
            other_icons_path = (
                iconfunctions.get_icon_source_folder("plump_color") + "/"
            )
        else:
            other_icons_path = (
                iconfunctions.get_icon_source_folder("plump_color_light") + "/"
            )
        for item in self.iterate_items():
            item_data = item.get_data()
            item_data["html"] = item_data["html"].replace(
                other_icons_path, current_icons_path
            )

    def config_file_check(self, *args):
        # Check if there are superfluous fields are in the
        # config file and remove them and re-save the file.
        config_file = "{}/{}".format(
            data.current_project.get_proj_rootpath(),
            data.filetree_config_relative_path,
        )
        config_data = functions.load_json_file(config_file)
        if functions.any_keys_in_dict(config_data, *get_unneeded_config_keys()):
            # Remove unneeded fields
            functions.remove_all_dict_keys(
                config_data,
                *get_unneeded_config_keys(),
            )
            functions.write_json_file(config_file, config_data)

    def generate_makefile(self):
        self.makefile_generation_in_progress = True
        if not hasattr(self, "generate_makefile_timer"):
            self.generate_makefile_timer = qt.QTimer(self)
            self.generate_makefile_timer.setInterval(250)
            self.generate_makefile_timer.setSingleShot(True)
            self.generate_makefile_timer.timeout.connect(
                self.__generate_makefile
            )
        else:
            self.generate_makefile_timer.stop()
        self.generate_makefile_timer.start()

    @components.lockcache.inter_process_lock("file-tree-structure-generate")
    def __generate_makefile(self):
        # Copy the entire structure
        #        functions.performance_timer_start()

        ASYNC = False
        if ASYNC:
            # ASYNC
            copied_structure = copy.deepcopy(self.__flat_tree_structure)
            components.newfiletreehandler.generate_makefile_async(
                copied_structure, self.__project_path
            )
        else:
            # SYNC
            components.newfiletreehandler.generate_makefile(
                flat_tree_structure_copy=self.__flat_tree_structure,
                project_path=self.__project_path,
                external_version=None,
                template_only=False,
                in_makefile_path=data.current_project.get_treepath_seg().get_default_abspath(
                    "FILETREE_MK"
                ),
            )
        self.makefile_generation_in_progress = False

    #        functions.performance_timer_show("call-generate-makefile")

    def __tree_structure_completed(
        self,
        init_tree_structure: Dict,
        flat_tree_structure: Dict,
    ) -> None:
        """"""
        # Remove the loading indicator before adding actual file tree
        self.__remove_loading_indicator()

        self.__tree_structure = init_tree_structure
        self.__flat_tree_structure = flat_tree_structure

        id_counter = 0
        flat_item_ids = []

        def create_tree(dict_item, parent_node_id, path):
            nonlocal id_counter
            nonlocal flat_item_ids

            items = []
            node = []
            update_statuses_flag = False

            directories = dict_item["directories"]
            for k in sorted(directories.keys()):
                v = directories[k]
                directory_path = functions.unixify_path_join(path, k)
                row_string = constants.HTML_TEMPLATE_ROW_TEXT_ONLY.format(k)
                manual_status = v["source-analysis-status-hdir-manual"]
                if manual_status is not None:
                    image_html = constants.HTML_IMAGE_TEMPLATE.format(
                        iconfunctions.get_icon_abspath(
                            self.IMAGES["hdir"][manual_status]
                        ),
                    )
                    row_string = constants.HTML_TEMPLATE_ROW.format(
                        image_html, k
                    )
                v["html"] = row_string
                directory_node_id = self.get_node_id_counter() + id_counter
                #                print("directory:", directory_node_id, v["path"])
                id_counter += 1
                directory_node = {
                    "text": k,
                    "id": directory_node_id,
                    "parent": parent_node_id,
                    "icon": v["icon"],
                    "tooltip": k,
                    "data": v,
                }
                items.append(directory_node)
                item_path = v["path"]
                if item_path == "":
                    item_path = "."
                flat_item_ids.append((item_path, directory_node_id, False))
                sub_items, update_statuses_flag = create_tree(
                    v, directory_node_id, directory_path
                )
                items.extend(sub_items)

            files = dict_item["files"]
            for k in sorted(files.keys()):
                v = files[k]
                is_source_analysis_file, row_string = (
                    self.__generate_row_string(k, v)
                )
                manual_status = v["source-analysis-status-file-manual"]
                if manual_status is not None:
                    image_html = constants.HTML_IMAGE_TEMPLATE.format(
                        iconfunctions.get_icon_abspath(
                            self.IMAGES["file"][manual_status]
                        ),
                    )
                    row_string = constants.HTML_TEMPLATE_ROW.format(
                        image_html, k
                    )
                v["html"] = row_string
                file_node_id = self.get_node_id_counter() + id_counter
                #                print("file:", file_node_id, v["path"])
                id_counter += 1
                file_node = {
                    "text": k,
                    "id": file_node_id,
                    "parent": parent_node_id,
                    "icon": v["icon"],
                    "tooltip": k,
                    "data": v,
                }
                items.append(file_node)
                flat_item_ids.append(
                    (
                        v["path"],
                        file_node_id,
                        is_source_analysis_file and not update_statuses_flag,
                    )
                )
                if is_source_analysis_file:
                    update_statuses_flag = True

            return items, update_statuses_flag

        # Create main directory node
        functions.performance_timer_start()
        items, _ = create_tree(
            init_tree_structure, None, init_tree_structure["name"]
        )
        functions.performance_timer_show("create_tree")
        functions.performance_timer_start()
        new_items = self.multi_add(items)
        functions.performance_timer_show("multi_add")
        functions.performance_timer_start()
        # Save all sub-nodes
        for path, _id, update_status in flat_item_ids:
            node = self.get(_id)
            flat_tree_structure[path]["node"] = node
            #            print(path, _id, node, node.parent())
            if update_status:
                self.__update_parent_statuses(node.parent())  # !! VERY SLOW !!
        functions.performance_timer_show("re-reference-nodes")
        self.update_style()
        # Expand main nodes
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            self.expand(index)

        # Set custom sorting model
        self.setSortingEnabled(True)

        # Initialize the Source analyzer communicator
        self.__sai: (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator
        ) = functions.import_module(
            "components.sourceanalyzerinterface"
        ).SourceAnalysisCommunicator()

        def send_to_source_analyzer(
            project: components.sourceanalyzerinterface.Project,
            diagnostics: components.diagnostics.Diagnostics,
            symbol_handler: components.symbolhandler.SymbolHandler,
        ) -> None:
            self.send_to_source_analyzer.emit(self.__flat_tree_structure)
            return

        self.__sai.project_generated_sig.connect(send_to_source_analyzer)
        self.__sai.generate_project(
            project_rootpath=self.__project_path,
        )

        # Config file check
        self.config_file_check()
        return

    def __highlight_main_function(self):
        try:
            symbols = self.__sai.find_symbols("main")
            if len(symbols) > 0:
                found = False
                for s in symbols:
                    main = s
                    for d in main.definitions:
                        file_path = d.file.path
                        offset = d.begin_offset
                        #                        adjusted_file = functions.unixify_path_remove(file_path, self.__project_path)
                        #                        item = self.__flat_tree_structure[adjusted_file]["node"]
                        #                        self._highlight(item)
                        self.main_form.open_file(file_path)
                        tab = self.main_form.get_tab_by_save_name(file_path)
                        if tab is not None and offset is not None:
                            tab.goto_index(offset)
                        found = True
                        break
                    if found:
                        break
                else:
                    data.signal_dispatcher.notify_error.emit(
                        "[NewFiletree] Cannot locate main function."
                    )
            else:
                data.signal_dispatcher.notify_error.emit(
                    "[NewFiletree] Cannot locate main function."
                )
        except:
            data.signal_dispatcher.notify_error.emit(traceback.format_exc())
            data.signal_dispatcher.notify_error.emit(
                "[NewFiletree] Cannot locate main function: The above tracback has more details."
            )

    def __click(self, item, column):
        try:
            item_data = item.get_data()
            if item_data["type"] == "file":
                file_path = item_data["path"]
                full_path = functions.unixify_path_join(
                    self.__project_path, file_path
                )
                self.main_form.open_file(file=full_path, focus_tab=True)
        except:
            traceback.print_exc()

    def __changed(self, item, column):
        pass

    def __editing_closed(self, editor, hint):
        if self.__edit_item is None:
            return
        item = self.__edit_item
        self.__edit_item = None
        item_data = item.get_data()
        if "action" in item_data.keys():
            text = item.text(0)
            path = item_data["path"]
            item.setText(0, item_data["name"])
            if hint == qt.QAbstractItemDelegate.EndEditHint.SubmitModelCache:
                if text.strip() == "":
                    data.signal_dispatcher.notify_error.emit(
                        "[NewFiletree] Cannot create a file with empty name!"
                    )
                else:
                    if (
                        item_data["type"] == "file"
                        or item_data["type"] == "directory"
                    ):
                        previous_path = item_data["absolute-path"]
                        previous_relative_path = item_data["relative-path"]
                        #                        print("previous_path:", previous_path)
                        previous_directory, previous_name = os.path.split(
                            previous_path
                        )
                        #                        print("previous_directory:", previous_directory)
                        #                        print("previous_name:", previous_name)
                        new_path = functions.unixify_path_join(
                            previous_directory, editor.text()
                        )

                        #                        if item_data["type"] == "directory":
                        #                            self.__item_moved(False, True, previous_path, new_path, True)
                        #                        print("FROM:", previous_path)
                        #                        print("TO:", new_path)
                        os.rename(previous_path, new_path)
                    else:
                        data.signal_dispatcher.notify_error.emit(
                            "[NewFiletree] Cannot rename an unknown type: {}".format(
                                item_data["type"]
                            )
                        )
        elif "type" in item_data.keys():
            if item_data["type"] == "new-file":
                text = item.text(0)
                path = item_data["path"]
                if os.path.isfile(path):
                    split_path, split_file = os.path.split(path)
                    path = functions.unixify_path(split_path)
                if (
                    hint
                    == qt.QAbstractItemDelegate.EndEditHint.SubmitModelCache
                ):
                    if text.strip() == "":
                        data.signal_dispatcher.notify_error.emit(
                            "[NewFiletree] Cannot create a file with empty name!"
                        )
                    elif len(text) > 0:
                        if os.path.isdir(path):
                            open(
                                os.path.join(path, text), "w+", encoding="utf-8"
                            ).close()
                if self.has(item):
                    self.remove(item)
            elif item_data["type"] == "new-directory":
                text = item.text(0)
                path = item_data["path"]
                if os.path.isfile(path):
                    split_path, split_file = os.path.split(path)
                    path = functions.unixify_path(split_path)
                if (
                    hint
                    == qt.QAbstractItemDelegate.EndEditHint.SubmitModelCache
                ):
                    if text.strip() == "":
                        data.signal_dispatcher.notify_error.emit(
                            "[NewFiletree] Cannot create a directory with empty name!"
                        )
                    elif os.path.isdir(path):
                        os.mkdir(os.path.join(path, text))
                if self.has(item):
                    self.remove(item)
            else:
                # Not a new item
                pass

    @qt.pyqtSlot(object, int)
    def __file_analysis_change(self, file_relpath_or_obj, status):
        #        print(file_relpath_or_obj, status)
        self.__refresh()

    def __choose_file_status_icons(self, item_data):
        # Inclusion status
        if item_data["source-analysis-type"] != "header":
            if (
                item_data["source-analysis-status-hdir"]
                == source_analyzer.inclusion_status_excluded
            ):
                item_data["source-analysis-status-hdir"] = None
        sa_hdir_status = item_data["source-analysis-status-hdir"]

        inclusion_image_html = None
        if sa_hdir_status is not None:
            inclusion_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                iconfunctions.get_icon_abspath(
                    self.IMAGES["hdir-files"][sa_hdir_status]
                ),
            )
        elif item_data["source-analysis-type"] == "header":
            inclusion_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                iconfunctions.get_icon_abspath(
                    self.IMAGES["hdir-files"][
                        source_analyzer.inclusion_status_excluded
                    ]
                ),
            )

        # Linking status
        sa_file_status = item_data["source-analysis-status-file"]

        linking_image_html = None
        if sa_file_status is not None:
            manual_status = item_data["source-analysis-status-file-manual"]
            if manual_status is not None:
                # Correct
                if (
                    manual_status == "force-included"
                    and sa_file_status
                    == source_analyzer.inclusion_status_included
                ):
                    linking_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                        iconfunctions.get_icon_abspath(
                            self.IMAGES["file"][manual_status]
                        ),
                    )
                # Correct
                elif (
                    manual_status == "force-excluded"
                    and sa_file_status
                    == source_analyzer.inclusion_status_excluded
                ):
                    linking_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                        iconfunctions.get_icon_abspath(
                            self.IMAGES["file"][manual_status]
                        ),
                    )
                # Different
                else:
                    linking_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                        iconfunctions.get_icon_abspath(
                            "icons/include_chbx/c_files/mix_lock_exclam.png"
                        ),
                    )
            else:
                linking_image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][sa_file_status]
                    ),
                )

        # Set the row images
        if inclusion_image_html is not None and linking_image_html is not None:
            row = constants.HTML_TEMPLATE_ROW_TWO_ICONS.format(
                linking_image_html, inclusion_image_html, item_data["name"]
            )
        elif inclusion_image_html is not None:
            row = constants.HTML_TEMPLATE_ROW.format(
                inclusion_image_html, item_data["name"]
            )
        elif linking_image_html is not None:
            row = constants.HTML_TEMPLATE_ROW.format(
                linking_image_html, item_data["name"]
            )
        else:
            row = constants.HTML_TEMPLATE_ROW_TEXT_ONLY.format(
                item_data["name"]
            )
        return row

    @qt.pyqtSlot(object, int)
    def __file_inclusion_change(self, file_relpath_or_obj, status):
        if self.PRINT_FILE_STATUS_CHANGES:
            print("__file_inclusion_change\n    ", file_relpath_or_obj, status)

        # Check if it's actually a file
        file_absolute_path = functions.unixify_path_join(
            self.__project_path, file_relpath_or_obj
        )
        if not os.path.isfile(file_absolute_path):
            if data.debug_mode:
                print(
                    "[Filetree] NOT A FILE:",
                    file_relpath_or_obj,
                    file_absolute_path,
                )
            return

        if file_relpath_or_obj in self.__flat_tree_structure.keys():
            item = self.__flat_tree_structure[file_relpath_or_obj]["node"]

            if qt.sip.isdeleted(item):
                return

            item_data = item.get_data()
            item_data["source-analysis-status-hdir"] = status
            filled_html = self.__choose_file_status_icons(item_data)
            item.setText(0, item_data["name"])
            item_data["html"] = filled_html
            # Update parent node visuals
            self.__update_parent_statuses(item)
            with components.lockcache.Locker("file-tree-structure-use"):
                self.generate_makefile()
            self.__refresh()

    @qt.pyqtSlot(object, int)
    def __file_linking_change(self, file_relpath_or_obj, status):
        if self.PRINT_FILE_STATUS_CHANGES:
            print("__file_linking_change\n    ", file_relpath_or_obj, status)

        # Check if it's actually a file
        file_absolute_path = functions.unixify_path_join(
            self.__project_path, file_relpath_or_obj
        )
        if not os.path.isfile(file_absolute_path):
            if data.debug_mode:
                print(
                    "[Filetree] NOT A FILE:",
                    file_relpath_or_obj,
                    file_absolute_path,
                )
            return

        if file_relpath_or_obj in self.__flat_tree_structure.keys():
            item = self.__flat_tree_structure[file_relpath_or_obj]["node"]

            if qt.sip.isdeleted(item):
                return

            item_data = item.get_data()
            item_data["source-analysis-status-file"] = status
            filled_html = self.__choose_file_status_icons(item_data)
            item.setText(0, item_data["name"])
            item_data["html"] = filled_html
            # Update parent node visuals
            self.__update_parent_statuses(item)
            with components.lockcache.Locker("file-tree-structure-use"):
                self.generate_makefile()
            self.__refresh()

    @qt.pyqtSlot(object, int)
    def __hdir_inclusion_change(self, hdir_abspath_or_obj, status):
        if self.PRINT_FILE_STATUS_CHANGES:
            print("__hdir_inclusion_change\n    ", hdir_abspath_or_obj, status)

        # Check if it's actually a file
        hdir_absolute_path = functions.unixify_path_join(
            self.__project_path, hdir_abspath_or_obj
        )
        if not os.path.isdir(hdir_absolute_path):
            print(
                "[Filetree] NOT A DIRECTORY:",
                hdir_abspath_or_obj,
                hdir_absolute_path,
            )
            return

        for item in self.iterate_items():
            if qt.sip.isdeleted(item):
                continue

            if hdir_abspath_or_obj == item.get_data()["path"]:
                item_data = item.get_data()
                # Update item status
                item_data["source-analysis-status-hdir"] = status
                # Update item visuals
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["hdir-files"][status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, item_data["name"]
                )
                #                item.setText(0, filled_html)
                item.setText(0, item_data["name"])
                item_data["html"] = filled_html
                # Update parent node visuals
                self.__update_parent_statuses(item)
                with components.lockcache.Locker("file-tree-structure-use"):
                    self.generate_makefile()
                self.__refresh()
                break

    def __update_parent_statuses(self, parent):
        try:
            self.setUpdatesEnabled(False)

            if parent is not None:
                if parent.childCount() != 0:
                    parent = parent.child(0)
                else:
                    parent_data = parent.get_data()
                    if parent_data is None:
                        return
                    if parent_data["type"] == "directory":
                        filled_html = (
                            constants.HTML_TEMPLATE_ROW_TEXT_ONLY.format(
                                parent_data["name"]
                            )
                        )
                        parent_data["html"] = filled_html
                    parent = parent.parent()
                while (
                    isinstance(parent, gui.templates.treewidget.TreeNode)
                    and parent.parent() is not None
                ):
                    # Check child statuses
                    parent_data = parent.get_data()
                    if parent_data["type"] == "file":
                        parent = parent.parent()
                        continue
                    parent_status_file = None
                    parent_status_file_lock = False
                    parent_status_h_files = None
                    for i in range(parent.childCount()):
                        child_data = parent.child(i).get_data()
                        if child_data["type"] == "directory":
                            child_status_hdir = child_data[
                                "source-analysis-status-hdir-files"
                            ]
                            if parent_status_h_files is None:
                                parent_status_h_files = child_status_hdir
                            else:
                                if (
                                    child_status_hdir is not None
                                    and parent_status_h_files
                                    != child_status_hdir
                                ):
                                    parent_status_h_files = "mixed"
                            if child_data["source-analysis-status-file-locked"]:
                                parent_status_file_lock = True
                        elif child_data["type"] == "file":
                            # Lock
                            if (
                                child_data["source-analysis-status-file-manual"]
                                is not None
                            ):
                                parent_status_file_lock = True

                            # Linking status
                            child_status_hdir = child_data[
                                "source-analysis-status-hdir"
                            ]
                            if parent_status_h_files is None:
                                parent_status_h_files = child_status_hdir
                            else:
                                if (
                                    child_status_hdir is not None
                                    and parent_status_h_files
                                    != child_status_hdir
                                ):
                                    parent_status_h_files = "mixed"

                        else:
                            continue

                        child_status_file = child_data[
                            "source-analysis-status-file"
                        ]
                        if parent_status_file is None:
                            parent_status_file = child_status_file
                        else:
                            if (
                                child_status_file is not None
                                and parent_status_file != child_status_file
                            ):
                                parent_status_file = "mixed"

                    parent_status_hdir = None
                    parent_status_hdir_manual = parent_data[
                        "source-analysis-status-hdir-manual"
                    ]
                    if parent_status_hdir_manual is not None:
                        parent_status_hdir = parent_status_hdir_manual
                    elif (
                        "source-analysis-status-hdir-files"
                        in parent_data.keys()
                    ):
                        if (
                            parent_data["source-analysis-status-hdir"]
                            != source_analyzer.inclusion_status_excluded
                        ):
                            parent_status_hdir = parent_data[
                                "source-analysis-status-hdir"
                            ]
                    parent_data["source-analysis-status-hdir-files"] = (
                        parent_status_h_files
                    )
                    parent_data["source-analysis-status-file"] = (
                        parent_status_file
                    )

                    parent_data["source-analysis-status-file-locked"] = (
                        parent_status_file_lock
                    )

                    # Empty
                    if (
                        parent_status_h_files is None
                        and parent_status_file is None
                        and parent_status_hdir is None
                    ):
                        filled_html = (
                            constants.HTML_TEMPLATE_ROW_TEXT_ONLY.format(
                                parent_data["name"]
                            )
                        )
                    else:
                        images = []
                        # file only
                        if parent_status_file is not None:
                            image_html = constants.HTML_IMAGE_TEMPLATE.format(
                                iconfunctions.get_icon_abspath(
                                    self.IMAGES["file"][parent_status_file]
                                ),
                            )
                            if parent_status_file_lock:
                                image_html = (
                                    constants.HTML_IMAGE_TEMPLATE.format(
                                        iconfunctions.get_icon_abspath(
                                            self.IMAGES["file-locked"][
                                                parent_status_file
                                            ]
                                        )
                                    )
                                )
                            images.append(image_html)
                        # h-file only
                        if parent_status_h_files is not None:
                            image_html = constants.HTML_IMAGE_TEMPLATE.format(
                                iconfunctions.get_icon_abspath(
                                    self.IMAGES["hdir-files"][
                                        parent_status_h_files
                                    ]
                                ),
                            )
                            images.append(image_html)
                        # hdir only
                        if parent_status_hdir is not None:
                            image_html = constants.HTML_IMAGE_TEMPLATE.format(
                                iconfunctions.get_icon_abspath(
                                    self.IMAGES["hdir"][parent_status_hdir]
                                ),
                            )
                            images.append(image_html)

                        templates = {
                            1: constants.HTML_TEMPLATE_ROW,
                            2: constants.HTML_TEMPLATE_ROW_TWO_ICONS,
                            3: constants.HTML_TEMPLATE_ROW_THREE_ICONS,
                        }
                        filled_html = templates[len(images)].format(
                            *images, parent_data["name"]
                        )

                    parent.setText(0, parent_data["name"])
                    parent_data["html"] = filled_html

                    parent = parent.parent()

        finally:
            self.setUpdatesEnabled(True)
            self.__refresh()

    def __generate_row_string(self, name, item):
        is_source_analysis_file = False
        if item["type"] == "file" and (
            item["source-analysis-status-file"] is not None
            or item["source-analysis-status-hdir"] is not None
        ):
            is_source_analysis_file = True
            if item["source-analysis-type"] == "header":
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["hdir-files"][
                            item["source-analysis-status-hdir"]
                        ]
                    ),
                )
            else:
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][item["source-analysis-status-file"]]
                    ),
                )
            row_string = constants.HTML_TEMPLATE_ROW.format(image_html, name)
        else:
            row_string = constants.HTML_TEMPLATE_ROW_TEXT_ONLY.format(name)
        return is_source_analysis_file, row_string

    def __item_validity_check(self, path):
        return True

    @qt.pyqtSlot(list)
    def __process_items(self, item_list: list) -> None:
        for item in item_list:
            if item[0] == components.newfiletreehandler.ItemEvent.Created:
                self.__item_created(*item[1:])
            elif item[0] == components.newfiletreehandler.ItemEvent.Deleted:
                self.__item_deleted(*item[1:])
            elif item[0] == components.newfiletreehandler.ItemEvent.Modified:
                self.__item_modified(*item[1:])
            elif item[0] == components.newfiletreehandler.ItemEvent.Moved:
                self.__item_moved(*item[1:])
            else:
                raise Exception(
                    "[NewFileTree] Unknown item type: {}".format(item["type"])
                )

    def __item_created(
        self, is_synthetic, is_directory, src_path, item, skip_lock=False
    ):
        try:
            with components.lockcache.Locker(
                "file-tree-structure-use",
                custom_name="__item_created",
                skip=skip_lock,
            ):
                if not self.__item_validity_check(src_path):
                    return
                elif is_directory and not os.path.isdir(src_path):
                    return
                elif not is_directory and not os.path.isfile(src_path):
                    return

                parent_path = functions.unixify_path(
                    os.path.dirname(item["absolute-path"])
                )
                adjusted_parent_path = functions.unixify_path_remove(
                    parent_path, self.__project_path
                )
                if (
                    adjusted_parent_path
                    not in self.__flat_tree_structure.keys()
                ):
                    return
                elif item["relative-path"] in self.__flat_tree_structure.keys():
                    return
                parent_node = self.__flat_tree_structure[adjusted_parent_path][
                    "node"
                ]
                is_source_analysis_file, row_string = (
                    self.__generate_row_string(item["name"], item)
                )
                item["html"] = row_string
                new_node = self.add(
                    text=item["name"],
                    parent=parent_node,
                    icon_path=item["icon"],
                    tooltip=item["name"],
                    in_data=item,
                )
                #                print("add", new_node.id, os.path.basename(src_path))
                item["node"] = new_node
                self.__flat_tree_structure[item["relative-path"]] = item
                # Add to source analyzer if needed
                if is_directory:
                    self.sa_hdir_set.emit(item, None)
                else:
                    self.sa_file_add.emit(item, None)
                # Update parents
                if not qt.sip.isdeleted(item["node"]):
                    if not qt.sip.isdeleted(item["node"].parent()):
                        self.__update_parent_statuses(item["node"].parent())
                # Regenerate node items
                self.regenerate_tree_structure()
                # Generate makefile
                self.generate_makefile()
        except:
            traceback.print_exc()

    def __item_deleted(
        self, is_synthetic, is_directory, src_path, skip_lock=False
    ):
        #        print("on_deleted", is_directory, src_path)
        try:
            with components.lockcache.Locker(
                "file-tree-structure-use",
                custom_name="__item_deleted",
                skip=skip_lock,
            ):
                src_path = functions.unixify_path(src_path)
                adjusted_src_path = functions.unixify_path_remove(
                    src_path, self.__project_path
                )
                if not self.__item_validity_check(src_path):
                    return
                if adjusted_src_path not in self.__flat_tree_structure.keys():
                    return
                item = self.__flat_tree_structure[adjusted_src_path]
                node = item["node"]
                if not qt.sip.isdeleted(node):
                    parent = node.parent()

                if self.has(node.id) and not qt.sip.isdeleted(node):
                    self.remove(node)

                # Remove item from internal structure
                item = self.__flat_tree_structure.pop(adjusted_src_path, None)
                # Remove item from source analysis
                if (
                    item is not None
                    and "type" in item.keys()
                    and item["type"] == "file"
                ):
                    data.signal_dispatcher.source_analyzer.remove_file_sig.emit(
                        src_path
                    )

                # Update parents
                if not qt.sip.isdeleted(node):
                    self.__update_parent_statuses(parent)
                # Regenerate node items
                self.regenerate_tree_structure()
                # Generate makefile
                self.generate_makefile()
        except:
            traceback.print_exc()

    def __item_modified(self, is_synthetic, is_directory, src_path):
        #        print("on_modified", is_directory, src_path)
        pass

    def __item_moved(
        self, is_synthetic, is_directory, src_path, dest_path, skip_lock=False
    ):
        #        print("on_moved", is_synthetic, is_directory, src_path, dest_path)
        try:
            with components.lockcache.Locker(
                "file-tree-structure-use",
                custom_name="__item_moved",
                skip=skip_lock,
            ):
                if os_checker.is_os("linux"):
                    if os.path.dirname(src_path) != os.path.dirname(dest_path):
                        self.__item_deleted(
                            False, is_directory, src_path, skip_lock=True
                        )
                        relative_path = functions.unixify_path_remove(
                            dest_path, self.__project_path
                        )
                        if is_directory:
                            new_item = self.__new_filetree_handler.create_directory_item(
                                name=os.path.basename(dest_path),
                                full_path=dest_path,
                                relative_path=relative_path,
                                icon=self.__new_filetree_handler.get_directory_icon(
                                    dest_path
                                ),
                            )
                        else:
                            new_item = self.__new_filetree_handler.create_file_item(
                                name=os.path.basename(dest_path),
                                full_path=dest_path,
                                relative_path=relative_path,
                                icon=self.__new_filetree_handler.get_file_icon(
                                    dest_path
                                ),
                                base_directory=self.__project_path,
                            )
                        self.__item_created(
                            False,
                            is_directory,
                            dest_path,
                            new_item,
                            skip_lock=True,
                        )

                # Adjust paths
                src_path = functions.unixify_path(src_path)
                dest_path = functions.unixify_path(dest_path)
                adjusted_src_path = functions.unixify_path_remove(
                    src_path, self.__project_path
                )
                adjusted_dest_path = functions.unixify_path_remove(
                    dest_path, self.__project_path
                )
                if not self.__item_validity_check(
                    src_path
                ) or not self.__item_validity_check(dest_path):
                    return
                if adjusted_src_path not in self.__flat_tree_structure.keys():
                    return
                if not is_directory and not os.path.exists(
                    os.path.dirname(dest_path)
                ):
                    return
                try:
                    # Remove the old path from source analysis
                    data.signal_dispatcher.source_analyzer.remove_file_sig.emit(
                        src_path
                    )
                    # Rename the item
                    poped_item = self.__flat_tree_structure.pop(
                        adjusted_src_path
                    )
                    poped_item["path"] = dest_path
                    poped_item["absolute-path"] = dest_path
                    poped_item["relative-path"] = adjusted_dest_path
                    poped_item["name"] = os.path.basename(dest_path)
                    if poped_item["type"] == "file":
                        poped_item["source-analysis-status-file"] = None
                        poped_item["source-analysis-status-file-manual"] = None
                        self.__new_filetree_handler.source_file_check(
                            poped_item, self.__project_path
                        )
                    self.__flat_tree_structure[adjusted_dest_path] = poped_item

                    # Reset the item text
                    is_source_analysis_file, row_string = (
                        self.__generate_row_string(
                            poped_item["name"], poped_item
                        )
                    )
                    poped_item["node"].setText(0, poped_item["name"])
                    poped_item["html"] = row_string
                    if is_source_analysis_file:
                        self.__update_parent_statuses(
                            poped_item["node"].parent()
                        )
                    # Add the new named item to source analysis
                    if poped_item["type"] == "file":
                        self.__new_filetree_handler.source_analyzer_file_add(
                            poped_item
                        )
                    else:
                        self.__new_filetree_handler.source_analyzer_hdir_set(
                            poped_item
                        )
                    # Update parents
                    self.__update_parent_statuses(poped_item["node"].parent())
                    # Regenerate node items
                    self.regenerate_tree_structure()
                except:
                    traceback.print_exc()
                    print("[File-tree] Error moving:")
                    print("    - ", src_path)
                    print("  to:")
                    print("    - ", dest_path)
        except:
            traceback.print_exc()

    def regenerate_tree_structure(self):
        if not hasattr(self, "regenerate_timer"):
            self.regenerate_timer = qt.QTimer(self)
            self.regenerate_timer.setInterval(200)
            self.regenerate_timer.setSingleShot(True)
            self.regenerate_timer.timeout.connect(
                self.__regenerate_tree_structure
            )
        else:
            self.regenerate_timer.stop()
            try:
                self.regenerate_timer.timeout.disconnect()
            except:
                pass
            self.regenerate_timer.timeout.connect(
                self.__regenerate_tree_structure
            )
        self.regenerate_timer.start()

    @components.lockcache.inter_process_lock("file-tree-structure-regenerate")
    def __regenerate_tree_structure(self):
        # Fix all the paths for the items
        try:
            base_path = self.__project_path
            nodes = []
            for node in self.iterate_items():
                node_data = copy.deepcopy(node.get_data())
                functions.remove_all_dict_keys(node_data, "node")
                parent = node.parent()
                paths = []
                while parent != self.rootIndex() and parent is not None:
                    paths.insert(0, parent.get_data()["name"])
                    parent = parent.parent()
                paths.append(node_data["name"])
                nodes.append((node_data, paths))

        #            flat_tree_structure_copy = copy.deepcopy(self.__flat_tree_structure)
        #            functions.remove_all_dict_keys(flat_tree_structure_copy, "node")
        # Execute with a separate process
        # p = multiprocessing.Process(
        #     target=regenerate_tree_structure,
        #     args=(
        #         data.current_project.get_proj_rootpath(),
        #         base_path,
        #         nodes,
        #         flat_tree_structure_copy,
        #     ),
        #     daemon=True,
        # )
        # p.start()
        # Direct execution
        #            regenerate_tree_structure(
        #                data.current_project.get_proj_rootpath(),
        #                base_path,
        #                nodes,
        #                flat_tree_structure_copy,
        #            )
        except:
            traceback.print_exc()
            return

    def __init_backwards_compatibility(self):
        old_items = {
            "are_rootdirs_ready": {
                "return": True,
            },
            "find_item": {
                "callback-parameters": (None,),
                "return": True,
            },
            "save_later": {
                "callback-parameters": {
                    "save_params": {
                        "save_dashboard": False,
                        "callback": None,
                        "callbackArg": None,
                    },
                    "success": False,
                },
                "return": True,
            },
            "get_rootdir_list": {
                "return": [],
            },
            "fire_repaint_editor_tab_headers_signal": {
                "return": None,
            },
            "fire_init_complete_signal": {
                "return": None,
            },
        }

        def call_wrapper(name, func_data):
            def call(*args, **kwargs):
                print(f"[NewFiletree] Compatibility call: {name}")
                if "callback" in kwargs and kwargs["callback"] is not None:
                    if isinstance(func_data["callback-parameters"], dict):
                        try:
                            kwargs["callback"](
                                **func_data["callback-parameters"]
                            )
                        except:
                            kwargs["callback"]()
                    else:
                        kwargs["callback"](*func_data["callback-parameters"])
                return func_data["return"]

            return call

        for k, v in old_items.items():
            setattr(self, k, call_wrapper(k, v))

    def __processing_animation_resize(self):
        self.__processing_animation_frame.setStyleSheet(
            "background-color: #44ffffff;"
        )
        self.__processing_animation_frame.setGeometry(self.geometry())

        self.__processing_label.setGeometry(
            int(
                (
                    (self.geometry().width() / 2)
                    - (
                        self.__processing_label_size[0]
                        / 2
                        * data.get_global_scale()
                    )
                )
            ),
            int(
                (
                    (self.geometry().height() / 2)
                    - (
                        self.__processing_label_size[1]
                        / 2
                        * data.get_global_scale()
                    )
                )
            ),
            int(self.__processing_label_size[0] * data.get_global_scale()),
            int(self.__processing_label_size[1] * data.get_global_scale()),
        )

    def processing_animation_show(self):
        self.processing_animation_hide()

        self.__processing_animation_frame = (
            gui.templates.widgetgenerator.create_frame(
                parent=self,
                layout_vertical=True,
            )
        )
        self.__processing_animation_frame.show()

        self.__processing_label = qt.QLabel()
        self.__processing_label.setAttribute(
            qt.Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        movie = qt.QMovie(
            iconfunctions.get_icon_abspath(
                "icons/loading_animation/hourglass_animation/hourglass.gif"
            )
        )
        self.__processing_label.setMovie(movie)
        movie.start()
        self.__processing_label.setParent(self.__processing_animation_frame)
        self.__processing_label.setScaledContents(True)
        self.__processing_label.setVisible(True)
        self.__processing_animation_frame.layout().addWidget(
            self.__processing_label
        )
        self.__processing_label.show()
        self.__processing_animation_resize()

        functions.process_events()

    def processing_animation_hide(self):
        if self.__processing_label is not None:
            self.__processing_label.hide()
            self.__processing_label.setParent(None)
            self.__processing_label = None
            self.__processing_animation_frame.hide()
            self.__processing_animation_frame.setParent(None)
            self.__processing_animation_frame = None

            functions.process_events()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.__processing_animation_frame is not None:
            self.__processing_animation_resize()

    def __automatically_analyze_all_source_subfiles(self, item):
        def automatically_analyze_recurse(_item):
            for i in range(_item.childCount()):
                it = _item.child(i)
                it_data = it.get_data()
                if it_data["type"] == "directory":
                    automatically_analyze_recurse(it_data["node"])
                    continue
                elif (
                    it_data["type"] != "file"
                    or it_data["source-analysis-type"] != "source"
                ):
                    continue

                path = it_data["path"]
                status = components.newfiletreehandler.get_heuristics_state(
                    path, "file"
                )
                components.newfiletreehandler.set_file_status(
                    it_data, status, reset_manual_status=True
                )

                manual_status = it_data["source-analysis-status-file"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, it_data["name"]
                )
                it.setText(0, it_data["name"])
                it_data["html"] = filled_html
                functions.process_events()

                self.__update_parent_statuses(it)
                functions.process_events()
                if self.PRINT_MANUAL_CHANGES:
                    print("AUTOMATIC:", status, path)

        self.processing_animation_show()
        automatically_analyze_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __force_include_all_source_subfiles(self, item):
        def force_include_recurse(_item):
            for i in range(_item.childCount()):
                it = _item.child(i)
                it_data = it.get_data()
                if it_data["type"] == "directory":
                    force_include_recurse(it_data["node"])
                    continue
                elif (
                    it_data["type"] != "file"
                    or it_data["source-analysis-type"] != "source"
                ):
                    continue

                path = it_data["path"]
                status = source_analyzer.file_mode_include
                components.newfiletreehandler.set_file_status(it_data, status)

                manual_status = it_data["source-analysis-status-file-manual"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, it_data["name"]
                )
                it.setText(0, it_data["name"])
                it_data["html"] = filled_html
                functions.process_events()

                self.__update_parent_statuses(it)
                functions.process_events()
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-INCLUDE:", status, path)

        self.processing_animation_show()
        force_include_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __force_exclude_all_source_subfiles(self, item):
        def force_exclude_recurse(_item):
            for i in range(_item.childCount()):
                it = _item.child(i)
                it_data = it.get_data()
                if it_data["type"] == "directory":
                    force_exclude_recurse(it_data["node"])
                    continue
                elif (
                    it_data["type"] != "file"
                    or it_data["source-analysis-type"] != "source"
                ):
                    continue

                path = it_data["path"]
                status = source_analyzer.file_mode_exclude
                components.newfiletreehandler.set_file_status(it_data, status)

                manual_status = it_data["source-analysis-status-file-manual"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, it_data["name"]
                )
                it.setText(0, it_data["name"])
                it_data["html"] = filled_html
                functions.process_events()

                self.__update_parent_statuses(it)
                functions.process_events()
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-EXCLUDE:", status, path)

        self.processing_animation_show()
        force_exclude_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __automatically_analyze_all_recursive(self, item):
        def automatically_analyze_recurse(_item):
            item_data = _item.get_data()
            if (
                item_data["type"] == "file"
                and item_data["source-analysis-type"] == "source"
            ):
                path = item_data["path"]
                status = components.newfiletreehandler.get_heuristics_state(
                    path, "file"
                )
                self.__set_file_status(
                    _item,
                    item_data,
                    status,
                    "source-analysis-status-file",
                    in_reset_manual_status=True,
                )
                if self.PRINT_MANUAL_CHANGES:
                    print("AUTOMATIC:", status, path)
            else:
                # Parent
                path = item_data["path"]
                status = components.newfiletreehandler.get_heuristics_state(
                    path, "directory"
                )
                components.newfiletreehandler.set_hdir_status(
                    item_data, status, reset_manual_status=True
                )
                if self.PRINT_MANUAL_CHANGES:
                    print("AUTOMATIC:", status, path)

                # Children
                for i in range(_item.childCount()):
                    it = _item.child(i)
                    it_data = it.get_data()

                    path = it_data["path"]
                    if it_data["type"] == "directory":
                        # Directory
                        status = (
                            components.newfiletreehandler.get_heuristics_state(
                                path, "directory"
                            )
                        )
                        components.newfiletreehandler.set_hdir_status(
                            it_data, status, reset_manual_status=True
                        )
                        automatically_analyze_recurse(it_data["node"])

                    else:
                        # File
                        if it_data["source-analysis-type"] != "source":
                            continue

                        status = (
                            components.newfiletreehandler.get_heuristics_state(
                                path, "file"
                            )
                        )
                        self.__set_file_status(
                            it,
                            it_data,
                            status,
                            "source-analysis-status-file",
                            in_reset_manual_status=True,
                        )
                        if self.PRINT_MANUAL_CHANGES:
                            print("AUTOMATIC:", status, path)

        self.processing_animation_show()
        automatically_analyze_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __force_include_all_recursive(self, item):
        def force_include_recurse(_item):
            item_data = _item.get_data()
            if (
                item_data["type"] == "file"
                and item_data["source-analysis-type"] == "source"
            ):
                status = source_analyzer.file_mode_include
                self.__set_file_status(
                    _item,
                    item_data,
                    status,
                    "source-analysis-status-file-manual",
                )
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-INCLUDE:", status, item_data["path"])
            else:
                # Parent
                path = item_data["path"]
                status = source_analyzer.hdir_mode_include
                components.newfiletreehandler.set_hdir_status(item_data, status)
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-INCLUDE:", status, path)

                # Children
                for i in range(_item.childCount()):
                    it = _item.child(i)
                    it_data = it.get_data()

                    path = it_data["path"]
                    if it_data["type"] == "directory":
                        # Directory
                        status = source_analyzer.hdir_mode_include
                        components.newfiletreehandler.set_hdir_status(
                            it_data, status
                        )
                        force_include_recurse(it_data["node"])
                        if self.PRINT_MANUAL_CHANGES:
                            print("FORCE-INCLUDE:", status, path)

                    else:
                        # File
                        if it_data["source-analysis-type"] != "source":
                            continue

                        status = source_analyzer.file_mode_include
                        self.__set_file_status(
                            it,
                            it_data,
                            status,
                            "source-analysis-status-file-manual",
                        )
                        if self.PRINT_MANUAL_CHANGES:
                            print("FORCE-INCLUDE:", status, path)

        self.processing_animation_show()
        force_include_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __force_exclude_all_recursive(self, item):
        def force_exclude_recurse(_item):
            item_data = _item.get_data()
            if (
                item_data["type"] == "file"
                and item_data["source-analysis-type"] == "source"
            ):
                status = source_analyzer.file_mode_exclude
                self.__set_file_status(
                    _item,
                    item_data,
                    status,
                    "source-analysis-status-file-manual",
                )
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-EXCLUDE:", status, item_data["path"])
            else:
                # Parent
                path = item_data["path"]
                status = source_analyzer.hdir_mode_exclude
                components.newfiletreehandler.set_hdir_status(item_data, status)
                if self.PRINT_MANUAL_CHANGES:
                    print("FORCE-EXCLUDE:", status, path)

                # Children
                for i in range(_item.childCount()):
                    it = _item.child(i)
                    it_data = it.get_data()

                    if it_data["type"] == "directory":
                        # Directory
                        status = source_analyzer.hdir_mode_exclude
                        components.newfiletreehandler.set_hdir_status(
                            it_data, status
                        )
                        force_exclude_recurse(it_data["node"])
                        if self.PRINT_MANUAL_CHANGES:
                            print("FORCE-EXCLUDE:", status, it_data["path"])

                    else:
                        # File
                        if it_data["source-analysis-type"] != "source":
                            continue

                        status = source_analyzer.file_mode_exclude
                        self.__set_file_status(
                            it,
                            it_data,
                            status,
                            "source-analysis-status-file-manual",
                        )
                        if self.PRINT_MANUAL_CHANGES:
                            print("FORCE-EXCLUDE:", status, it_data["path"])

        self.processing_animation_show()
        force_exclude_recurse(item)
        self.__regenerate_tree_structure()
        self.processing_animation_hide()

    def __set_file_status(
        self,
        item,
        item_data,
        status,
        manual_status_field,
        in_reset_manual_status=False,
    ):
        path = item_data["path"]
        components.newfiletreehandler.set_file_status(
            item_data, status, reset_manual_status=in_reset_manual_status
        )

        manual_status = item_data[manual_status_field]
        image_html = constants.HTML_IMAGE_TEMPLATE.format(
            iconfunctions.get_icon_abspath(self.IMAGES["file"][manual_status])
        )
        filled_html = constants.HTML_TEMPLATE_ROW.format(
            image_html, item_data["name"]
        )
        item.setText(0, item_data["name"])
        item_data["html"] = filled_html
        functions.process_events()

        self.__update_parent_statuses(item)
        functions.process_events()

    def contextMenuEvent(self, event):
        # Get the item
        item = self.itemAt(event.pos())
        if item is None:
            return
        item_data = item.get_data()

        # Create a menu
        if self.context_menu is not None:
            self.context_menu.setParent(None)
            self.context_menu = None
        self.context_menu = gui.templates.basemenu.BaseMenu(self)

        # Creation function
        def __create_item(_type, path, icon, *args):
            parent = None
            if item_data["type"] == "file":
                parent = item.parent()
            else:
                parent = item
            new_item = self.add(
                text="",
                parent=parent,
                icon_path=None,
                in_data={
                    "type": _type,
                    "path": path,
                    "html": "",
                },
            )
            new_item.setFlags(
                qt.Qt.ItemFlag.ItemIsEditable
                | qt.Qt.ItemFlag.ItemIsEnabled
                | qt.Qt.ItemFlag.ItemIsSelectable
            )
            new_index = self.indexFromItem(new_item, 0)
            self.setCurrentIndex(new_index)
            self.edit(new_index)
            self.__edit_item = new_item
            # Add the session signal when editing is canceled

        #            delegate = self.get_item_delegate_for_index(new_index)
        #            try:
        #                delegate.closeEditor.disconnect()
        #            except:
        #                pass
        #            delegate.closeEditor.connect(
        #                functools.partial(self.__editing_closed, new_item)
        #            )

        def __delete_item(_type, path, *args):
            try:
                msg = "Are you sure you want to delete {}:<br>'{}' ?".format(
                    _type, path
                )
                reply = gui.dialogs.popupdialog.PopupDialog.question(
                    msg, parent=self.main_form
                )
                if reply != qt.QMessageBox.StandardButton.Yes:
                    return
                if _type == "directory":
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:
                traceback.print_exc()
                data.signal_dispatcher.notify_error.emit(
                    "[NewFiletree] Could not delete item: {}".format(path)
                )

        def __rename_item(*args):
            item_data["action"] = "rename"
            node = item_data["node"]
            node.setFlags(
                qt.Qt.ItemFlag.ItemIsEditable
                | qt.Qt.ItemFlag.ItemIsEnabled
                | qt.Qt.ItemFlag.ItemIsSelectable
            )
            index = self.indexFromItem(node, 0)
            self.setCurrentIndex(index)
            self.edit(index)
            self.__edit_item = item
            # Add the session signal when editing is canceled

        #            delegate = self.get_item_delegate_for_index(index)
        #            try:
        #                if hasattr(self, "delegate_func") and self.delegate_func is not None:
        #                    delegate.closeEditor.disconnect(self.delegate_func)
        #            except:
        #                traceback.print_exc()
        #            self.delegate_func = functools.partial(self.__editing_closed, item)
        #            delegate.closeEditor.connect(self.delegate_func)

        def __automatically_analyze_item(*args):
            path = item_data["path"]
            if item_data["type"] == "directory":
                status = components.newfiletreehandler.get_heuristics_state(
                    path, "directory"
                )
                components.newfiletreehandler.set_hdir_status(
                    item_data, status, reset_manual_status=True
                )
            else:
                status = components.newfiletreehandler.get_heuristics_state(
                    path, "file"
                )
                components.newfiletreehandler.set_file_status(
                    item_data, status, reset_manual_status=True
                )

                manual_status = item_data["source-analysis-status-file"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, item_data["name"]
                )
                item.setText(0, item_data["name"])
                item_data["html"] = filled_html

            self.__update_parent_statuses(item)
            self.__regenerate_tree_structure()
            if self.PRINT_MANUAL_CHANGES:
                print("AUTOMATIC:", status, path)

        def __force_include_item(*args):
            path = item_data["path"]
            if item_data["type"] == "directory":
                status = source_analyzer.hdir_mode_include
                components.newfiletreehandler.set_hdir_status(item_data, status)
            else:
                status = source_analyzer.file_mode_include
                components.newfiletreehandler.set_file_status(item_data, status)

                manual_status = item_data["source-analysis-status-file-manual"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, item_data["name"]
                )
                item.setText(0, item_data["name"])
                item_data["html"] = filled_html

            self.__update_parent_statuses(item)
            self.__regenerate_tree_structure()
            if self.PRINT_MANUAL_CHANGES:
                print("FORCE-INCLUDE:", status, path)

        def __force_exclude_item(*args):
            path = item_data["path"]
            if item_data["type"] == "directory":
                status = source_analyzer.hdir_mode_exclude
                components.newfiletreehandler.set_hdir_status(item_data, status)
            else:
                status = source_analyzer.file_mode_exclude
                components.newfiletreehandler.set_file_status(item_data, status)

                manual_status = item_data["source-analysis-status-file-manual"]
                image_html = constants.HTML_IMAGE_TEMPLATE.format(
                    iconfunctions.get_icon_abspath(
                        self.IMAGES["file"][manual_status]
                    ),
                )
                filled_html = constants.HTML_TEMPLATE_ROW.format(
                    image_html, item_data["name"]
                )
                item.setText(0, item_data["name"])
                item_data["html"] = filled_html

            self.__update_parent_statuses(item)
            self.__regenerate_tree_structure()
            if self.PRINT_MANUAL_CHANGES:
                print("FORCE-EXCLUDE:", status, path)

        def __display_header_information(*args):
            it_data = item.get_data()
            path = it_data["path"]
            data.signal_dispatcher.show_symbol_details.emit(path, True)

        def __file_help(*args):
            print("__file_help")

        def __h_file_help(*args):
            print("__h_file_help")

        def __subfile_help(*args):
            print("__subfile_help")

        def __directory_help(*args):
            print("__directory_help")

        def __open_in_explorer(*args):
            path = item_data["absolute-path"]
            functions.open_file_folder_in_explorer(path)

        def __show_object_file(_type: str, path: str, *args) -> None:
            if not _type == "file":
                return
            if path is None:
                return
            object_path_location = components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_corresponding_object_file(
                path
            )
            success = False
            if object_path_location is not None:
                success = data.filetree.goto_path(object_path_location)
            if success:
                return
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/message.png",
                title_text="Cannot find object file",
                text=f"Cannot find object file for\n'{path}'\nDid you build the project?",
            )
            return

        # Get the path, in which the new item will be created
        if item_data["type"] == "file":
            if item.parent() is not None:
                create_path = item_data["absolute-path"]
            else:
                create_path = functions.unixify_path(os.path.dirname(item))
        else:
            create_path = item_data["absolute-path"]

        hide_check_field = True

        texts = {
            "mk0": {
                "multi-automatic": "Add source files to build if needed",
                "multi-include": "Always add source files to build",
                "multi-exclude": "Never add source files to build",
                "multi-help": "What are these options?",
                "set-automatic-directory": "Search for header files if needed",
                "set-include-directory": "Always search for header files",
                "set-exclude-directory": "Never search for header files",
                "set-automatic-file": "Select file automatically",
                "set-include-file": "Always add to build",
                "set-exclude-file": "Never add to build",
                "help": "What are these options?",
                "header-info": "Display header information",
                "header-help": "Why the circle icon?",
            },
            "mk1": {
                "multi-automatic": "Add needed source files to build",
                "multi-include": "Always add source files to build",
                "multi-exclude": "Never add source files to build",
                "multi-help": "What are these options?",
                "set-automatic-directory": "Search for header files if needed",
                "set-include-directory": "Always search for header files",
                "set-exclude-directory": "Never search for header files",
                "set-automatic-file": "Add to build if needed",
                "set-include-file": "Always add to build",
                "set-exclude-file": "Never add to build",
                "help": "What are these options?",
                "header-info": "Display header information",
                "header-help": "Why the circle icon?",
            },
            "mk2": {
                "multi-recurse-automatic": "Automatic",
                "multi-recurse-include": "Force include",
                "multi-recurse-exclude": "Force exclude",
                "multi-automatic": "Auto detect needed source files",
                "multi-include": "Force include all source files",
                "multi-exclude": "Force exclude all source files",
                "multi-help": "What are these options?",
                "set-automatic-directory": "Search for header files if needed",
                "set-include-directory": "Always search for header files",
                "set-exclude-directory": "Never search for header files",
                "set-automatic-file": "Auto detect",
                "set-include-file": "Force include",
                "set-exclude-file": "Force exclude",
                "help": "What are these options?",
                "header-info": "Display header information",
                "header-help": "Why the circle icon?",
            },
        }
        texts_selected_version = "mk2"

        def add_recursive_options(*args):
            """New simpler recursive system for directories."""
            items = (
                {
                    "name": "multi-recurse-automatic",
                    "icon": "icons/gen/gear.svg",
                    "function": functools.partial(
                        self.__automatically_analyze_all_recursive, item
                    ),
                },
                {
                    "name": "multi-recurse-include",
                    "icon": "icons/dialog/checkmark.svg",
                    "function": functools.partial(
                        self.__force_include_all_recursive, item
                    ),
                },
                {
                    "name": "multi-recurse-exclude",
                    "icon": "icons/dialog/cross.svg",
                    "function": functools.partial(
                        self.__force_exclude_all_recursive, item
                    ),
                },
            )
            for i in items:
                text = texts[texts_selected_version][i["name"]]
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=self.context_menu,
                    name=i["name"],
                    icon=i["icon"],
                    text=text,
                    tooltip=text,
                    checkable=False,
                    hide_check_field=hide_check_field,
                )
                new_action.triggered.connect(i["function"])
                self.context_menu.addAction(new_action)

            self.context_menu.addSeparator()

        # Source analysis stuff
        root, extension = os.path.splitext(item_data["path"].lower())
        if (
            extension in data.VALID_SOURCE_FILE_EXTENSIONS
            or item_data["type"] == "directory"
        ):
            add_recursive_options()

            # Advanced menu
            advanced_menu = self.context_menu.addMenu("Advanced")
            temp_icon = iconfunctions.get_qicon(f"icons/menu_edit/advanced.png")
            advanced_menu.setIcon(temp_icon)
            self.context_menu.addMenu(advanced_menu)

            # Multi force include/exclude/automatic source files
            if (
                item_data["type"] == "directory"
                and item_data["source-analysis-status-file"] is not None
            ):
                # Automatic
                icon = "icons/include_chbx/c_files/auto.png"
                text = texts[texts_selected_version]["multi-automatic"]
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=advanced_menu,
                    name="multi-automatic",
                    icon=icon,
                    text=text,
                    tooltip=text,
                    checkable=False,
                )
                new_action.triggered.connect(
                    functools.partial(
                        self.__automatically_analyze_all_source_subfiles
                    )
                )
                advanced_menu.addAction(new_action)
                # Force include source sub-files
                icon = "icons/include_chbx/c_files/green_lock.png"
                text = texts[texts_selected_version]["multi-include"]
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=advanced_menu,
                    name="multi-include",
                    icon=icon,
                    text=text,
                    tooltip=text,
                    checkable=False,
                )
                new_action.triggered.connect(
                    functools.partial(
                        self.__force_include_all_source_subfiles, item
                    )
                )
                advanced_menu.addAction(new_action)
                # Force exclude
                icon = "icons/include_chbx/c_files/red_lock.png"
                text = texts[texts_selected_version]["multi-exclude"]
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=advanced_menu,
                    name="multi-exclude",
                    icon=icon,
                    text=text,
                    tooltip=text,
                    checkable=False,
                )
                new_action.triggered.connect(
                    functools.partial(
                        self.__force_exclude_all_source_subfiles, item
                    )
                )
                advanced_menu.addAction(new_action)

                # Help
                icon = "icons/dialog/help.png"
                text = texts[texts_selected_version]["multi-help"]
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=advanced_menu,
                    name="multi-help",
                    icon=icon,
                    text=text,
                    tooltip=text,
                    checkable=False,
                )
                new_action.triggered.connect(functools.partial(__subfile_help))
                advanced_menu.addAction(new_action)

                advanced_menu.addSeparator()

            ## Directory / file options
            # Automatic
            if item_data["type"] == "directory":
                name = "set-automatic-directory"
                icon = "icons/include_chbx/h_files/auto.png"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-hdir-manual"] is None
                )
            else:
                name = "set-automatic-file"
                icon = "icons/include_chbx/c_files/auto.png"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-file-manual"] is None
                )
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=advanced_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=True,
                checked=checked,
            )
            new_action.triggered.connect(
                functools.partial(__automatically_analyze_item)
            )
            advanced_menu.addAction(new_action)

            # Force include
            icon = "icons/include_chbx/c_files/green_lock.png"
            if item_data["type"] == "directory":
                icon = "icons/include_chbx/h_files/magnifier_lock.png"
            if item_data["type"] == "directory":
                name = "set-include-directory"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-hdir-manual"]
                    == "force-included"
                )
            else:
                name = "set-include-file"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-file-manual"]
                    == "force-included"
                )
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=advanced_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=True,
                checked=checked,
            )
            new_action.triggered.connect(
                functools.partial(__force_include_item)
            )
            advanced_menu.addAction(new_action)

            # Force exclude
            icon = "icons/include_chbx/c_files/red_lock.png"
            if item_data["type"] == "directory":
                icon = "icons/include_chbx/h_files/magnifier_cross.png"
            if item_data["type"] == "directory":
                name = "set-exclude-directory"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-hdir-manual"]
                    == "force-excluded"
                )
            else:
                name = "set-exclude-file"
                text = texts[texts_selected_version][name]
                checked = (
                    item_data["source-analysis-status-file-manual"]
                    == "force-excluded"
                )
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=advanced_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=True,
                checked=checked,
            )
            new_action.triggered.connect(
                functools.partial(__force_exclude_item)
            )
            advanced_menu.addAction(new_action)

            # Help
            name = "help"
            icon = "icons/dialog/help.png"
            text = texts[texts_selected_version][name]
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=advanced_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=False,
            )
            if item_data["type"] == "directory":
                new_action.triggered.connect(
                    functools.partial(__directory_help)
                )
            else:
                new_action.triggered.connect(functools.partial(__file_help))
            advanced_menu.addAction(new_action)

            # Show corresponding object file
            if item_data["type"] == "file":
                advanced_menu.addSeparator()
                name = "how-obj-file"
                icon = "icons/file/file_o.png"
                text = "Show corresponding object file."
                new_action = gui.templates.basemenu.CheckMenuItem(
                    parent=advanced_menu,
                    name=name,
                    icon=icon,
                    text=text,
                    tooltip=text,
                    checkable=False,
                )
                new_action.triggered.connect(
                    functools.partial(
                        __show_object_file,
                        item_data["type"],
                        item_data["absolute-path"],
                    )
                )
                advanced_menu.addAction(new_action)

            self.context_menu.addSeparator()
            # Do not show the check, now that the 'Advanced' menu is added
            # hide_check_field = False

        # Header files:
        elif extension in data.VALID_HEADER_FILE_EXTENSIONS:
            # Header information
            name = "header-info"
            icon = "icons/file/file_h.png"
            text = texts[texts_selected_version][name]
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=self.context_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=False,
                hide_check_field=hide_check_field,
            )
            new_action.triggered.connect(
                functools.partial(__display_header_information)
            )
            self.context_menu.addAction(new_action)

            # Help
            name = "header-help"
            icon = "icons/dialog/help.png"
            text = texts[texts_selected_version][name]
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=self.context_menu,
                name=name,
                icon=icon,
                text=text,
                tooltip=text,
                checkable=False,
                hide_check_field=hide_check_field,
            )
            new_action.triggered.connect(functools.partial(__h_file_help))
            self.context_menu.addAction(new_action)

            self.context_menu.addSeparator()

        def __copy(path):
            self.cache_disk_items = {
                "copy": path,
                "cut": None,
            }
            data.signal_dispatcher.notify_message.emit(
                "Item copied to clipboard: '{}'".format(path)
            )

        def __cut(path):
            self.cache_disk_items = {
                "copy": None,
                "cut": path,
            }
            data.signal_dispatcher.notify_message.emit(
                "Item cut to clipboard: '{}'".format(path)
            )

        def __paste(path):
            if not hasattr(self, "cache_disk_items"):
                data.signal_dispatcher.notify_error.emit(
                    "No item in copy/cut cache!"
                )
                return

            # Check if copy or cut
            operation = None
            if isinstance(self.cache_disk_items["copy"], str):
                paste_item = self.cache_disk_items["copy"]
                operation = "copy"
            elif isinstance(self.cache_disk_items["cut"], str):
                paste_item = self.cache_disk_items["cut"]
                operation = "cut"
            else:
                data.signal_dispatcher.notify_error.emit(
                    "Copy/cut cache is invalid!"
                )
                return

            # Get path of where to paste to
            paste_path = None
            if os.path.isfile(path):
                paste_path = os.path.dirname(path)
            else:
                paste_path = path
            paste_item_name = os.path.basename(paste_item)
            destination_path = functions.unixify_path_join(
                paste_path, paste_item_name
            )

            # Check if destination path already exists
            if os.path.exists(destination_path):
                msg = "Item already exists:<br>'{}'<br>What do you wish to do?".format(
                    destination_path
                )
                buttons = [
                    ("Overwrite", "overwrite"),
                    ("Rename", "rename"),
                    ("Cancel", "cancel"),
                ]
                reply = gui.dialogs.popupdialog.PopupDialog.custom_buttons(
                    msg, parent=self, buttons=buttons, text_centered=True
                )
                if reply[0] == "cancel":
                    return
                elif reply[0] == "overwrite":
                    if not os.path.isfile(paste_item):
                        shutil.rmtree(destination_path)
                elif reply[0] == "rename":
                    if os.path.isfile(paste_item):
                        name, extension = os.path.splitext(destination_path)
                        destination_path = "{}{}{}".format(
                            name, "_copy", extension
                        )
                    else:
                        destination_path += "_copy"
                else:
                    data.signal_dispatcher.notify_error.emit(
                        "Unknown dialog result: '{}'".format(operation)
                    )
                    return

            # Paste
            try:
                if operation == "copy":
                    if os.path.isfile(paste_item):
                        shutil.copyfile(paste_item, destination_path)
                    else:
                        shutil.copytree(paste_item, destination_path)
                elif operation == "cut":
                    shutil.move(paste_item, destination_path)
                else:
                    data.signal_dispatcher.notify_error.emit(
                        "Unknown operation: '{}'".format(operation)
                    )
            except:
                data.signal_dispatcher.notify_error.emit(traceback.format_exc())

            self.cache_disk_items = {
                "copy": None,
                "cut": None,
            }

        # Copy item
        icon = "icons/menu_edit/copy.png"
        text = "Copy"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="copy",
            icon=icon,
            text=text,
            tooltip="Copy the item to clipboard",
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(
            functools.partial(
                __copy,
                create_path,
            )
        )
        self.context_menu.addAction(new_action)

        # Cut item
        icon = "icons/menu_edit/cut.png"
        text = "Cut"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="cut",
            icon=icon,
            text=text,
            tooltip="Cut the item to clipboard",
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(
            functools.partial(
                __cut,
                create_path,
            )
        )
        self.context_menu.addAction(new_action)

        # Paste
        icon = "icons/menu_edit/paste.png"
        text = "Paste"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="paste",
            icon=icon,
            text=text,
            tooltip="Paste the item from clipboard",
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.setEnabled(False)
        new_action.triggered.connect(
            functools.partial(
                __paste,
                create_path,
            )
        )
        self.context_menu.addAction(new_action)
        if hasattr(self, "cache_disk_items") and isinstance(
            self.cache_disk_items, dict
        ):
            if (
                self.cache_disk_items["copy"] is not None
                or self.cache_disk_items["cut"] is not None
            ):
                new_action.setEnabled(True)

        # Separator
        self.context_menu.addSeparator()

        # Copy name to clipboard
        def clipboard_copy_name():
            name = item_data["name"]
            if os.path.isdir(name):
                name = os.path.basename(name)
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(name, mode=cb.Mode.Clipboard)

        icon = "icons/menu_edit/copy.png"
        text = "Copy name"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="copy-name",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(clipboard_copy_name)
        self.context_menu.addAction(new_action)

        # Copy path to clipboard
        def clipboard_copy_path():
            path = item_data["absolute-path"]
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(path, mode=cb.Mode.Clipboard)

        icon = "icons/menu_edit/copy.png"
        text = "Copy path"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="copy-path",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(clipboard_copy_path)
        self.context_menu.addAction(new_action)

        # Rename (only if non-top-level node)
        # -----------------------------------
        node = item_data["node"]
        index = self.indexFromItem(node, 0)
        parent = index.parent()
        if parent != self.rootIndex():
            base_icon = "icons/file/file.png"
            if item_data["type"] == "directory":
                base_icon = "icons/folder/closed/folder.png"
            icon = base_icon.replace(".png", "(rename).png")
            text = "Rename"
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=self.context_menu,
                name="rename-item",
                icon=icon,
                text=text,
                tooltip=text,
                checkable=False,
                hide_check_field=hide_check_field,
            )
            new_action.triggered.connect(
                functools.partial(
                    __rename_item,
                    create_path,
                )
            )
            self.context_menu.addAction(new_action)

        # Get the delete path
        delete_path = item.get_data()["absolute-path"]
        # Do not allow the deletion of the project directory
        if delete_path != self.get_project_path():
            # Delete item
            # -----------
            icon = "icons/file/file.png"
            if item_data["type"] == "directory":
                icon = "icons/folder/closed/folder.png"
            icon = icon.replace(".png", "(del).png")
            text = "Delete {}".format(item_data["type"])
            new_action = gui.templates.basemenu.CheckMenuItem(
                parent=self.context_menu,
                name="delete-item",
                icon=icon,
                text=text,
                tooltip=text,
                checkable=False,
                hide_check_field=hide_check_field,
            )
            new_action.triggered.connect(
                functools.partial(__delete_item, item_data["type"], delete_path)
            )
            self.context_menu.addAction(new_action)

        # Separator
        self.context_menu.addSeparator()

        # Create directory
        # ----------------
        icon = "icons/folder/closed/new_folder.png"
        text = "Create directory"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="create-directory",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(
            functools.partial(
                __create_item,
                "new-directory",
                create_path,
                "icons/folder/closed/folder.png",
            )
        )
        self.context_menu.addAction(new_action)

        # Create file
        # -----------
        icon = "icons/file/file(add).png"
        text = "Create file"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="create-file",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(
            functools.partial(
                __create_item,
                "new-file",
                create_path,
                "icons/file/file.png",
            )
        )
        self.context_menu.addAction(new_action)

        # Separator
        self.context_menu.addSeparator()

        # Find 'main' function
        icon = "icons/other/location.svg"
        text = "Find 'main' function"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="find-main-function",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(self.__highlight_main_function)
        self.context_menu.addAction(new_action)

        # Open in explorer
        icon = "icons/folder/open/magnifier.png"
        text = "Open in explorer"
        new_action = gui.templates.basemenu.CheckMenuItem(
            parent=self.context_menu,
            name="open-in-explorer",
            icon=icon,
            text=text,
            tooltip=text,
            checkable=False,
            hide_check_field=hide_check_field,
        )
        new_action.triggered.connect(__open_in_explorer)
        self.context_menu.addAction(new_action)

        adjusted_position = qt.QCursor.pos() - qt.create_qpoint(6, 6)
        self.context_menu.popup(adjusted_position)

    def get_project_path(self) -> Optional[str]:
        return self.__project_path

    def goto_path(self, absolute_path: str, select: bool = False) -> bool:
        """Go to the requested path.

        Also return True if the path is present in the Filetree.
        """
        # Safety checks
        try:
            len(self.__flat_tree_structure.keys())
        except:
            # Structure already cleaned
            return False

        relative_path = functions.unixify_path_remove(
            absolute_path, self.__project_path
        )
        if relative_path not in self.__flat_tree_structure.keys():
            if not select:
                data.signal_dispatcher.notify_warning.emit(
                    f"[NewFiletree] Cannot go-to item '{absolute_path}', it's not in any filetree directory!"
                )
            return False
        for item in self.iterate_items():
            item_data = item.get_data()
            if item_data["relative-path"] == relative_path:
                if select:
                    self._select(item)
                else:
                    self._highlight(item)
                return True
        print(f"[NewFiletree] Goto item not found: {absolute_path}")
        return False

    def get_makefile(self, template_only, version):
        return components.newfiletreehandler.generate_makefile(
            self.__flat_tree_structure,
            self.__project_path,
            external_version=version,
            template_only=template_only,
        )

    def get_config(self):
        config_file = f"{data.current_project.get_proj_rootpath()}/{data.filetree_config_relative_path}"
        text = ""
        if os.path.isfile(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                text = f.read()
        return text

    def get_flat_tree_structure(self):
        return self.__flat_tree_structure


def regenerate_tree_structure(
    project_rootpath, base_path, nodes, flat_tree_structure
) -> None:
    try:
        for node_data, paths in nodes:
            new_path = functions.unixify_path_join(base_path, *paths)
            new_path = functions.unixify_path_remove(new_path, base_path)
            node_data["path"] = new_path

            if node_data["type"] == "directory":
                for k, v in node_data["directories"].items():
                    if v["path"] in flat_tree_structure.keys():
                        poped_item = flat_tree_structure.pop(v["path"])
                        if new_path != ".":
                            poped_item["path"] = (
                                new_path + "/" + poped_item["name"]
                            )
                        else:
                            poped_item["path"] = poped_item["name"]
                        flat_tree_structure[poped_item["path"]] = poped_item
                for k, v in node_data["files"].items():
                    if v["path"] in flat_tree_structure.keys():
                        poped_item = flat_tree_structure.pop(v["path"])
                        if new_path != ".":
                            poped_item["path"] = (
                                new_path + "/" + poped_item["name"]
                            )
                        else:
                            poped_item["path"] = poped_item["name"]
                        flat_tree_structure[poped_item["path"]] = poped_item

        items = {}
        for k, v in flat_tree_structure.items():
            if v["type"] == "directory":
                if v["source-analysis-status-hdir-manual"] is not None:
                    items[k] = v.copy()
            else:
                if v["source-analysis-status-file-manual"] is not None:
                    items[k] = v.copy()

        # Remove unneeded fields
        functions.remove_all_dict_keys(items, *get_unneeded_config_keys())

        out_data = {
            "version-generated": (
                components.newfiletreehandler.NewFileTreeHandler.CONFIG_GENERATED_VERSION
            ),
            "version-minimum": (
                components.newfiletreehandler.NewFileTreeHandler.CONFIG_MINIMUM_VERSION
            ),
            "items": items,
        }

        # Write the data to the config file
        config_file = f"{project_rootpath}/{data.filetree_config_relative_path}"
        functions.write_json_file(config_file, out_data)
    except:
        traceback.print_exc()
        return


class NewFiletreeAPI(qt.QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.filetree = parent

    def __str__(self):
        help_list = ["This is the new Filetree API help documentation:"]
        functions = {
            "Function goto_path": self.goto_path.__doc__,
            "Function generate_filetree_mk": self.generate_filetree_mk.__doc__,
            "Function generate_config": self.generate_config.__doc__,
        }
        for k, v in functions.items():
            help_list.append(f"    {k}:")
            help_list.append(v)
        return "\n".join(help_list)

    def goto_path(self, *args, **kwargs):
        """Go to the path item in the Filetree. If the path item does not
        exists, an error is displayed in the messages.

        arguments:
            - path: str -> absolute path of the item to go to
        """
        return self.filetree.goto_path(*args, **kwargs)

    def generate_filetree_mk(
        self,
        template_only: bool,
        version: int,
    ) -> str:
        """Generate the content for 'filetree.mk'.

        arguments:
            - template_only: bool -> Return the content for 'filetree.mk' as if no files were added
                                     to the build at all.
            - version: int        -> The content for 'filetree.mk' should be generated for the given
                                     version nr, a number between 1 and 7 at the moment.
        """
        return self.filetree.get_makefile(template_only, version)

    def generate_config(
        self,
        version: int,
        *args,
        **kwargs,
    ) -> str:
        """Generate the content for '.beetle/filetree_config.btl'.

        arguments:
            - version: int -> The content for 'filetree_config.btl' should be generated for the
                              given version nr, a number between 1 and 7 at the moment.
        """
        return self.filetree.get_config(*args, **kwargs)

    def is_file_included(self, file_abspath) -> bool:
        result = False
        file_relpath = functions.unixify_path_remove(
            file_abspath, self.filetree.get_project_path()
        )
        flat_structure = self.filetree.get_flat_tree_structure()
        if file_relpath in flat_structure.keys():
            file_data = flat_structure[file_relpath]
            result = (
                file_data["source-analysis-status-file"]
                == source_analyzer.inclusion_status_included
                or file_data["source-analysis-status-file-manual"]
                == "force-included"
            )
        return result


def get_unneeded_config_keys() -> tuple:
    return (
        "html",
        "node",
        "icon",
        "path",
        "absolute-path",
        "mouse-position",
        "level",
    )
