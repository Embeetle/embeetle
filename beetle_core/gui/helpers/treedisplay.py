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
import ast
import re
import iconfunctions
import gui.templates.treedisplaybase
import qt
import data
import components.iconmanipulator

"""
----------------------------------------------------------------------------
Object for displaying various results in a tree structure
----------------------------------------------------------------------------
"""


class TreeDisplay(gui.templates.treedisplaybase.TreeDisplayBase):
    # Class custom objects/types
    class Directory:
        """Object for holding directory/file information when building directory
        trees."""

        item = None
        directories = None
        files = None

        def __init__(self, input_item):
            """Initialization."""
            self.item = input_item
            self.directories = {}
            self.files = {}

        def add_directory(self, dir_name, dir_item):
            # Create a new instance of Directory class using the __class__ dunder method
            new_directory = self.__class__(dir_item)
            # Add the new directory to the dictionary
            self.directories[dir_name] = new_directory
            # Add the new directory item to the parent(self)
            self.item.appendRow(dir_item)
            # Return the directory object reference
            return new_directory

        def add_file(self, file_name, file_item):
            self.files[file_name] = file_item
            # Add the new file item to the parent(self)
            self.item.appendRow(file_item)

    #            i = qt.QStandardItem("TEST")
    #            i.setIcon(iconfunctions.get_qicon("icons/node/node_macro.png"))
    #            self.item.appendRow([file_item , i])

    # Class variables
    tree_display_type = None
    bound_tab = None
    default_menu_font = None
    # Attributes specific to the display data
    bound_node_tab = None
    # Node icons
    node_icon_import = None
    node_icon_type = None
    node_icon_const = None
    node_icon_function = None
    node_icon_procedure = None
    node_icon_converter = None
    node_icon_iterator = None
    node_icon_class = None
    node_icon_method = None
    node_icon_property = None
    node_icon_macro = None
    node_icon_template = None
    node_icon_variable = None
    node_icon_namespace = None
    node_icon_nothing = None
    node_pragma = None
    folder_icon = None
    goto_icon = None
    python_icon = None
    nim_icon = None
    c_icon = None

    def parent_destroyed(self, event):
        # Connect the bound tab 'destroy' signal to this function
        # for automatic closing of this tree widget
        self._parent.close_tab(self)

    def __init__(self, parent=None, main_form=None):
        """Initialization."""
        # Initialize the superclass
        super().__init__(parent, main_form)
        # Initialize components
        self.icon_manipulator = components.iconmanipulator.IconManipulator()
        # Store the reference to the parent
        self._parent = parent
        # Store the reference to the main form
        self.main_form = main_form
        # Set font
        self.setFont(data.current_font)
        # Store name of self
        self.name = "Tree display"
        # Disable node expansion on double click
        self.setExpandsOnDoubleClick(False)
        # Connect the click and doubleclick signal
        self.doubleClicked.connect(self._item_double_click)
        #        self.clicked.connect(self._item_click)
        # Connect the doubleclick signal
        self.expanded.connect(self._check_contents)
        # Initialize the icons
        # Node icons
        self.node_icon_import = iconfunctions.get_qicon(
            "icons/node/node_module.png"
        )
        self.node_icon_type = iconfunctions.get_qicon(
            "icons/node/node_type.png"
        )
        self.node_icon_variable = iconfunctions.get_qicon(
            "icons/node/node_variable.png"
        )
        self.node_icon_const = iconfunctions.get_qicon(
            "icons/node/node_const.png"
        )
        self.node_icon_function = iconfunctions.get_qicon(
            "icons/node/node_function.png"
        )
        self.node_icon_procedure = iconfunctions.get_qicon(
            "icons/node/node_procedure.png"
        )
        self.node_icon_converter = iconfunctions.get_qicon(
            "icons/node/node_converter.png"
        )
        self.node_icon_iterator = iconfunctions.get_qicon(
            "icons/node/node_iterator.png"
        )
        self.node_icon_class = iconfunctions.get_qicon(
            "icons/node/node_class.png"
        )
        self.node_icon_method = iconfunctions.get_qicon(
            "icons/node/node_method.png"
        )
        self.node_icon_macro = iconfunctions.get_qicon(
            "icons/node/node_macro.png"
        )
        self.node_icon_template = iconfunctions.get_qicon(
            "icons/node/node_template.png"
        )
        self.node_icon_namespace = iconfunctions.get_qicon(
            "icons/node/node_namespace.png"
        )
        self.node_icon_pragma = iconfunctions.get_qicon(
            "icons/node/node_pragma.png"
        )
        self.node_icon_unknown = iconfunctions.get_qicon(
            "icons/node/node_unknown.png"
        )
        self.node_icon_nothing = iconfunctions.get_qicon(
            "icons/dialog/warning.png"
        )
        self.python_icon = iconfunctions.get_qicon("icons/languages/python.png")
        self.nim_icon = iconfunctions.get_qicon("icons/languages/nim.png")
        self.c_icon = iconfunctions.get_qicon("icons/languages/c.png")
        self.search_icon = iconfunctions.get_qicon(
            "icons/system/find_files.png"
        )
        # File searching icons
        self.file_icon = iconfunctions.get_qicon(f"icons/file/file.png")
        self.folder_icon = iconfunctions.get_qicon(
            f"icons/folder/closed/folder.png"
        )
        self.goto_icon = iconfunctions.get_qicon(f"icons/menu_edit/goto.png")

        # Set the icon size for every node
        self.update_icon_size()

    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        """Function connected to the clicked signal of the tree display."""
        super().mousePressEvent(event)
        # Get the index of the clicked item
        if event.button() == qt.Qt.MouseButton.RightButton:
            # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned object is a
            # QPointF() instead of a QPoint()
            posF: qt.QPointF = event.position()
            pos: qt.QPoint = posF.toPoint()
            index = self.indexAt(pos)
            self._item_click(index)
        return

    def _item_click(self, model_index):
        if self.tree_display_type == data.TreeDisplayType.FILES:
            item = self.model().itemFromIndex(model_index)
            if (
                hasattr(item, "is_dir") == True
                or hasattr(item, "is_base") == True
            ):

                def update_cwd():
                    self.main_form.set_cwd(item.full_name)

                cursor = qt.QCursor.pos()

                if self.tree_menu is not None:
                    self.tree_menu.setParent(None)
                    self.tree_menu = None

                self.tree_menu = self._create_menu()

                action_update_cwd = qt.QAction("Update CWD", self.tree_menu)
                action_update_cwd.triggered.connect(update_cwd)
                icon = iconfunctions.get_qicon(f"icons/folder/open/refresh.png")
                action_update_cwd.setIcon(icon)
                self.tree_menu.addAction(action_update_cwd)
                if hasattr(item, "is_base") == True:

                    def update_to_parent():
                        parent_directory = os.path.abspath(
                            os.path.join(item.full_name, os.pardir)
                        )
                        self.main_form.set_cwd(parent_directory)

                    action_update_to_parent = qt.QAction(
                        "Update CWD to parent", self.tree_menu
                    )
                    action_update_to_parent.triggered.connect(update_to_parent)
                    icon = iconfunctions.get_qicon(
                        f"icons/folder/open/refresh.png"
                    )
                    action_update_to_parent.setIcon(icon)
                    self.tree_menu.addAction(action_update_to_parent)
                    self.tree_menu.addSeparator()

                    def one_dir_up():
                        parent_directory = os.path.abspath(
                            os.path.join(item.full_name, os.pardir)
                        )
                        self.main_form.display.show_directory_tree(
                            parent_directory
                        )

                    action_one_dir_up = qt.QAction(
                        "One directory up ..", self.tree_menu
                    )
                    action_one_dir_up.triggered.connect(one_dir_up)
                    icon = iconfunctions.get_qicon(f"icons/folder/open/up.png")
                    action_one_dir_up.setIcon(icon)
                    self.tree_menu.addAction(action_one_dir_up)
                self.tree_menu.popup(cursor)
            elif hasattr(item, "full_name") == True:

                def open_file():
                    self.main_form.open_file(item.full_name)

                cursor = qt.QCursor.pos()

                if self.tree_menu is not None:
                    self.tree_menu.setParent(None)
                    self.tree_menu = None

                self.tree_menu = self._create_menu()
                action_open_file = qt.QAction("Open", self.tree_menu)
                action_open_file.triggered.connect(open_file)
                icon = iconfunctions.get_qicon(f"icons/folder/open/file.png")
                action_open_file.setIcon(icon)
                self.tree_menu.addAction(action_open_file)
                self.tree_menu.addSeparator()

                def update_to_parent():
                    directory = os.path.dirname(item.full_name)
                    self.main_form.set_cwd(directory)

                action_update_to_parent = qt.QAction(
                    "Update CWD", self.tree_menu
                )
                action_update_to_parent.triggered.connect(update_to_parent)
                icon = iconfunctions.get_qicon(f"icons/folder/open/refresh.png")
                action_update_to_parent.setIcon(icon)
                self.tree_menu.addAction(action_update_to_parent)
                self.tree_menu.popup(cursor)
        elif self.tree_display_type == data.TreeDisplayType.NODES:

            def goto_item():
                # Parse the node
                self._node_item_parse(item)

            def open_document():
                # Focus the bound tab in its parent window
                self.bound_tab.parent.setCurrentWidget(self.bound_tab)

            item = self.model().itemFromIndex(model_index)
            if item is None:
                return
            item_text = item.text()
            cursor = qt.QCursor.pos()

            if self.tree_menu is not None:
                self.tree_menu.setParent(None)
                self.tree_menu = None

            self.tree_menu = self._create_menu()

            if hasattr(item, "line_number") == True or "line:" in item_text:
                action_goto_line = qt.QAction("Goto node item", self.tree_menu)
                action_goto_line.triggered.connect(goto_item)
                icon = iconfunctions.get_qicon(f"icons/menu_edit/goto.png")
                action_goto_line.setIcon(icon)
                self.tree_menu.addAction(action_goto_line)
            elif "DOCUMENT" in item_text:
                action_open = qt.QAction("Focus document", self.tree_menu)
                action_open.triggered.connect(open_document)
                icon = iconfunctions.get_qicon(f"icons/folder/open/file.png")
                action_open.setIcon(icon)
                self.tree_menu.addAction(action_open)

            self.tree_menu.popup(cursor)

    def _item_double_click(self, model_index):
        """Function connected to the doubleClicked signal of the tree
        display."""
        # Use the item text according to the tree display type
        if self.tree_display_type == data.TreeDisplayType.NODES:
            # Get the text of the double clicked item
            item = self.model().itemFromIndex(model_index)
            self._node_item_parse(item)
        elif self.tree_display_type == data.TreeDisplayType.FILES:
            # Get the double clicked item
            item = self.model().itemFromIndex(model_index)
            # Test if the item has the 'full_name' attribute
            if hasattr(item, "is_dir") == True:
                # Expand/collapse the directory node
                if self.isExpanded(item.index()) == True:
                    self.collapse(item.index())
                else:
                    self.expand(item.index())
                return
            elif hasattr(item, "full_name") == True:
                # Open the file
                self.main_form.open_file(file=item.full_name)
        elif self.tree_display_type == data.TreeDisplayType.FILES_WITH_LINES:
            # Get the double clicked item
            item = self.model().itemFromIndex(model_index)
            # Test if the item has the 'full_name' attribute
            if hasattr(item, "full_name") == False:
                return
            # Open the file
            self.main_form.open_file(file=item.full_name)
            # Check if a line item was clicked
            if hasattr(item, "line_number") == True:
                # Goto the stored line number
                document = self.main_form.main_window.currentWidget()
                document.goto_line(item.line_number)

    def _node_item_parse(self, item):
        # Check if the bound tab has been cleaned up and has no parent
        if self.bound_tab is None or self.bound_tab.parent is None:
            self.main_form.display.display_message_with_type(
                "The bound tab has been closed! Reload the tree display.",
                message_type=data.MessageType.ERROR,
            )
            return
        # Check the item text
        item_text = item.text()
        if hasattr(item, "line_number") == True:
            # Goto the stored line number
            self.bound_tab.parent.setCurrentWidget(self.bound_tab)
            self.bound_tab.goto_line(item.line_number)
        elif "line:" in item_text:
            # Parse the line number out of the item text
            line = item_text.split()[-1]
            start_index = line.index(":") + 1
            end_index = -1
            line_number = int(line[start_index:end_index])
            # Focus the bound tab in its parent window
            self.bound_tab.parent.setCurrentWidget(self.bound_tab)
            # Go to the item line number
            self.bound_tab.goto_line(line_number)
        elif "DOCUMENT" in item_text:
            # Focus the bound tab in its parent window
            self.bound_tab.parent.setCurrentWidget(self.bound_tab)

    def _check_contents(self):
        # Update the horizontal scrollbar width
        self._resize_horizontal_scrollbar()

    def set_display_type(self, tree_type):
        """Set the tree display type attribute."""
        self.tree_display_type = tree_type

    def display_python_nodes_in_list(
        self,
        custom_editor,
        import_nodes,
        class_nodes,
        function_nodes,
        global_vars,
        parse_error=False,
    ):
        """Display the input python data in the tree display."""
        # Store the custom editor tab that for quicker navigation
        self.bound_tab = custom_editor
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.NODES)
        # Define the document name, type
        document_name = os.path.basename(custom_editor.save_name)
        document_name_text = "DOCUMENT: {:s}".format(document_name)
        document_type_text = "TYPE: {:s}".format(
            custom_editor.current_file_type
        )
        # Define the display structure texts
        import_text = "IMPORTS:"
        class_text = "CLASS/METHOD TREE:"
        function_text = "FUNCTIONS:"
        # Initialize the tree display to Python file type
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        tree_model.setHorizontalHeaderLabels([document_name])
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        # Add the file attributes to the tree display
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["keyword"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_document_name = qt.QStandardItem(document_name_text)
        item_document_name.setEditable(False)
        item_document_name.setForeground(description_brush)
        item_document_name.setFont(description_font)
        item_document_type = qt.QStandardItem(document_type_text)
        item_document_type.setEditable(False)
        item_document_type.setForeground(description_brush)
        item_document_type.setFont(description_font)
        item_document_type.setIcon(self.python_icon)
        tree_model.appendRow(item_document_name)
        tree_model.appendRow(item_document_type)
        # Set the label properties
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        # Check if there was a parsing error
        if parse_error != False:
            error_brush = qt.QBrush(qt.QColor(180, 0, 0))
            error_font = qt.QFont(
                data.current_font_name,
                int(data.general_font_scale),
                qt.QFont.Weight.Bold,
            )
            item_error = qt.QStandardItem("ERROR PARSING FILE!")
            item_error.setEditable(False)
            item_error.setForeground(error_brush)
            item_error.setFont(error_font)
            item_error.setIcon(self.node_icon_nothing)
            tree_model.appendRow(item_error)
            # Show the error message
            error_font = qt.QFont(
                data.current_font_name, data.general_font_scale
            )
            item_error_msg = qt.QStandardItem(str(parse_error))
            item_error_msg.setEditable(False)
            item_error_msg.setForeground(error_brush)
            item_error_msg.setFont(error_font)
            line_number = int(
                re.search(r"line (\d+)", str(parse_error)).group(1)
            )
            item_error_msg.line_number = line_number
            tree_model.appendRow(item_error_msg)
            return
        """Imported module filtering"""
        item_imports = qt.QStandardItem(import_text)
        item_imports.setEditable(False)
        item_imports.setForeground(label_brush)
        item_imports.setFont(label_font)
        for node in import_nodes:
            node_text = str(node[0]) + " (line:"
            node_text += str(node[1]) + ")"
            item_import_node = qt.QStandardItem(node_text)
            item_import_node.setEditable(False)
            item_import_node.setIcon(self.node_icon_import)
            item_imports.appendRow(item_import_node)
        if import_nodes == []:
            item_no_imports = qt.QStandardItem("No imports found")
            item_no_imports.setEditable(False)
            item_no_imports.setIcon(self.node_icon_nothing)
            item_imports.appendRow(item_no_imports)
        # Append the import node to the model
        tree_model.appendRow(item_imports)
        if import_nodes == []:
            self.expand(item_imports.index())
        """Class nodes filtering"""
        item_classes = qt.QStandardItem(class_text)
        item_classes.setEditable(False)
        item_classes.setForeground(label_brush)
        item_classes.setFont(label_font)
        # Check deepest nest level and store it
        max_level = 0
        for node in class_nodes:
            for child in node[1]:
                child_level = child[0] + 1
                if child_level > max_level:
                    max_level = child_level
        # Initialize the base level references to the size of the deepest nest level
        base_node_items = [None] * max_level
        base_node_type = [None] * max_level
        # Create class nodes as tree items
        for node in class_nodes:
            # Construct the parent node
            node_text = str(node[0].name) + " (line:"
            node_text += str(node[0].lineno) + ")"
            parent_tree_node = qt.QStandardItem(node_text)
            parent_tree_node.setEditable(False)
            parent_tree_node.setIcon(self.node_icon_class)
            # Create a list that will hold the child nodes
            child_nodes = []
            # Create base nodes
            # Create the child nodes and add them to list
            for i, child in enumerate(node[1]):
                """!! child_level IS THE INDENTATION LEVEL !!"""
                child_level = child[0]
                child_object = child[1]
                child_text = str(child_object.name) + " (line:"
                child_text += str(child_object.lineno) + ")"
                child_tree_node = qt.QStandardItem(child_text)
                child_tree_node.setEditable(False)
                # Save the base node, its type for adding children to it
                base_node_items[child_level] = child_tree_node
                if isinstance(child_object, ast.ClassDef) == True:
                    base_node_type[child_level] = 0
                elif isinstance(child_object, ast.FunctionDef) == True:
                    base_node_type[child_level] = 1
                # Check if the child is a child of a child.
                if child_level != 0:
                    # Set the child icon
                    if isinstance(child_object, ast.ClassDef) == True:
                        child_tree_node.setIcon(self.node_icon_class)
                    else:
                        # Set method/function icon according to the previous base node type
                        if base_node_type[child_level - 1] == 0:
                            child_tree_node.setIcon(self.node_icon_method)
                        elif base_node_type[child_level - 1] == 1:
                            child_tree_node.setIcon(self.node_icon_procedure)
                    # Determine the parent node level
                    level_retraction = 1
                    parent_level = child_level - level_retraction
                    parent_node = None
                    while parent_node is None and parent_level >= 0:
                        parent_node = base_node_items[parent_level]
                        level_retraction += 1
                        parent_level = child_level - level_retraction
                    # Add the child node to the parent node
                    parent_node.appendRow(child_tree_node)
                    # Sort the base node children
                    parent_node.sortChildren(0)
                else:
                    # Set the icon for the
                    if isinstance(child_object, ast.ClassDef) == True:
                        child_tree_node.setIcon(self.node_icon_class)
                    elif isinstance(child_object, ast.FunctionDef) == True:
                        child_tree_node.setIcon(self.node_icon_method)
                    child_nodes.append(child_tree_node)
            # Append the child nodes to the parent and sort them
            for cn in child_nodes:
                parent_tree_node.appendRow(cn)
            parent_tree_node.sortChildren(0)
            # Append the parent to the model and sort them
            item_classes.appendRow(parent_tree_node)
            item_classes.sortChildren(0)
        # Append the class nodes to the model
        tree_model.appendRow(item_classes)
        # Check if there were any nodes found
        if class_nodes == []:
            item_no_classes = qt.QStandardItem("No classes found")
            item_no_classes.setEditable(False)
            item_no_classes.setIcon(self.node_icon_nothing)
            item_classes.appendRow(item_no_classes)
        """Function nodes filtering"""
        item_functions = qt.QStandardItem(function_text)
        item_functions.setEditable(False)
        item_functions.setForeground(label_brush)
        item_functions.setFont(label_font)
        # Create function nodes as tree items
        for func in function_nodes:
            # Set the function node text
            func_text = func.name + " (line:"
            func_text += str(func.lineno) + ")"
            # Construct the node and add it to the tree
            function_node = qt.QStandardItem(func_text)
            function_node.setEditable(False)
            function_node.setIcon(self.node_icon_procedure)
            item_functions.appendRow(function_node)
        item_functions.sortChildren(0)
        # Check if there were any nodes found
        if function_nodes == []:
            item_no_functions = qt.QStandardItem("No functions found")
            item_no_functions.setEditable(False)
            item_no_functions.setIcon(self.node_icon_nothing)
            item_functions.appendRow(item_no_functions)
        # Append the function nodes to the model
        tree_model.appendRow(item_functions)
        # Expand the base nodes
        self.expand(item_classes.index())
        self.expand(item_functions.index())
        # Resize the header so the horizontal scrollbar will have the correct width
        self._resize_horizontal_scrollbar()

    def construct_node(self, node, parent_is_class=False):
        # Construct the node text
        node_text = str(node.name) + " (line:"
        node_text += str(node.line_number) + ")"
        tree_node = qt.QStandardItem(node_text)
        tree_node.setEditable(False)
        if node.type == "class":
            tree_node.setIcon(self.node_icon_class)
        elif node.type == "function":
            if parent_is_class == False:
                tree_node.setIcon(self.node_icon_procedure)
            else:
                tree_node.setIcon(self.node_icon_method)
        elif node.type == "global_variable":
            tree_node.setIcon(self.node_icon_variable)
        # Append the children
        node_is_class = False
        if node.type == "class":
            node_is_class = True
        for child_node in node.children:
            tree_node.appendRow(self.construct_node(child_node, node_is_class))
        # Sort the child node alphabetically
        tree_node.sortChildren(0)
        # Return the node
        return tree_node

    def display_python_nodes_in_tree(
        self, custom_editor, python_node_tree, parse_error=False
    ):
        """Display the input python data in the tree display."""
        # Store the custom editor tab that for quicker navigation
        self.bound_tab = custom_editor
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.NODES)
        # Define the document name, type
        document_name = os.path.basename(custom_editor.save_name)
        document_name_text = "DOCUMENT: {:s}".format(document_name)
        document_type_text = "TYPE: {:s}".format(
            custom_editor.current_file_type
        )
        # Define the display structure texts
        import_text = "IMPORTS:"
        global_vars_text = "GLOBALS:"
        class_text = "CLASS/METHOD TREE:"
        function_text = "FUNCTIONS:"
        # Initialize the tree display to Python file type
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        #        tree_model.setHorizontalHeaderLabels([document_name])
        self.header().hide()
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        # Add the file attributes to the tree display
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["keyword"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_document_name = qt.QStandardItem(document_name_text)
        item_document_name.setEditable(False)
        item_document_name.setForeground(description_brush)
        item_document_name.setFont(description_font)
        item_document_type = qt.QStandardItem(document_type_text)
        item_document_type.setEditable(False)
        item_document_type.setForeground(description_brush)
        item_document_type.setFont(description_font)
        item_document_type.setIcon(self.python_icon)
        tree_model.appendRow(item_document_name)
        tree_model.appendRow(item_document_type)
        # Set the label properties
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        # Check if there was a parsing error
        if parse_error != False:
            error_brush = qt.QBrush(qt.QColor(180, 0, 0))
            error_font = qt.QFont(
                data.current_font_name,
                int(data.general_font_scale),
                qt.QFont.Weight.Bold,
            )
            item_error = qt.QStandardItem("ERROR PARSING FILE!")
            item_error.setEditable(False)
            item_error.setForeground(error_brush)
            item_error.setFont(error_font)
            item_error.setIcon(self.node_icon_nothing)
            tree_model.appendRow(item_error)
            # Show the error message
            error_font = qt.QFont(
                data.current_font_name, data.general_font_scale
            )
            item_error_msg = qt.QStandardItem(str(parse_error))
            item_error_msg.setEditable(False)
            item_error_msg.setForeground(error_brush)
            item_error_msg.setFont(error_font)
            try:
                line_number = int(
                    re.search(r"line (\d+)", str(parse_error)).group(1)
                )
                item_error_msg.line_number = line_number
            except:
                pass
            tree_model.appendRow(item_error_msg)
            return
        # Create the filtered node lists
        import_nodes = [x for x in python_node_tree if x.type == "import"]
        class_nodes = [x for x in python_node_tree if x.type == "class"]
        function_nodes = [x for x in python_node_tree if x.type == "function"]
        globals_nodes = [
            x for x in python_node_tree if x.type == "global_variable"
        ]
        """Imported module filtering."""
        item_imports = qt.QStandardItem(import_text)
        item_imports.setEditable(False)
        item_imports.setForeground(label_brush)
        item_imports.setFont(label_font)
        for node in import_nodes:
            node_text = str(node.name) + " (line:"
            node_text += str(node.line_number) + ")"
            item_import_node = qt.QStandardItem(node_text)
            item_import_node.setEditable(False)
            item_import_node.setIcon(self.node_icon_import)
            item_imports.appendRow(item_import_node)
        if import_nodes == []:
            item_no_imports = qt.QStandardItem("No imports found")
            item_no_imports.setEditable(False)
            item_no_imports.setIcon(self.node_icon_nothing)
            item_imports.appendRow(item_no_imports)
        # Append the import node to the model
        tree_model.appendRow(item_imports)
        if import_nodes == []:
            self.expand(item_imports.index())
        """Global variable nodes filtering"""
        item_globals = qt.QStandardItem(global_vars_text)
        item_globals.setEditable(False)
        item_globals.setForeground(label_brush)
        item_globals.setFont(label_font)
        # Check if there were any nodes found
        if globals_nodes == []:
            item_no_globals = qt.QStandardItem("No global variables found")
            item_no_globals.setEditable(False)
            item_no_globals.setIcon(self.node_icon_nothing)
            item_globals.appendRow(item_no_globals)
        else:
            # Create the function nodes and add them to the tree
            for node in globals_nodes:
                item_globals.appendRow(self.construct_node(node))
        # Append the function nodes to the model
        tree_model.appendRow(item_globals)
        if globals_nodes == []:
            self.expand(item_globals.index())
        """Class nodes filtering"""
        item_classes = qt.QStandardItem(class_text)
        item_classes.setEditable(False)
        item_classes.setForeground(label_brush)
        item_classes.setFont(label_font)
        # Check if there were any nodes found
        if class_nodes == []:
            item_no_classes = qt.QStandardItem("No classes found")
            item_no_classes.setEditable(False)
            item_no_classes.setIcon(self.node_icon_nothing)
            item_classes.appendRow(item_no_classes)
        else:
            # Create the class nodes and add them to the tree
            for node in class_nodes:
                item_classes.appendRow(self.construct_node(node, True))
        # Append the class nodes to the model
        tree_model.appendRow(item_classes)
        """Function nodes filtering."""
        item_functions = qt.QStandardItem(function_text)
        item_functions.setEditable(False)
        item_functions.setForeground(label_brush)
        item_functions.setFont(label_font)
        # Check if there were any nodes found
        if function_nodes == []:
            item_no_functions = qt.QStandardItem("No functions found")
            item_no_functions.setEditable(False)
            item_no_functions.setIcon(self.node_icon_nothing)
            item_functions.appendRow(item_no_functions)
        else:
            # Create the function nodes and add them to the tree
            for node in function_nodes:
                item_functions.appendRow(self.construct_node(node))
        # Append the function nodes to the model
        tree_model.appendRow(item_functions)
        """Finalization."""
        # Expand the base nodes
        self.expand(item_classes.index())
        self.expand(item_functions.index())
        # Resize the header so the horizontal scrollbar will have the correct width
        self._resize_horizontal_scrollbar()

    def display_c_nodes(self, custom_editor, module):
        """Display the input C data in a tree structure."""
        # Store the custom editor tab that for quicker navigation
        self.bound_tab = custom_editor
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.NODES)
        # Set the label properties
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )

        # Filter the nodes
        def display_node(tree_node, c_node):
            node_group = {}
            for v in c_node.children:
                if v.type in node_group.keys():
                    node_group[v.type].append(v)
                else:
                    node_group[v.type] = [v]
            # Initialize a list of struct references for later addition of their members
            struct_list = {}
            # Add The nodes to the tree using the parent tree node
            for k in sorted(node_group.keys()):
                if k == "member":
                    continue
                group_name = k.upper()
                item = qt.QStandardItem("{}:".format(group_name))
                current_list = node_group[k]
                if k == "function":
                    icon = self.node_icon_procedure
                elif k == "var" or k == "variable":
                    icon = self.node_icon_variable
                elif k == "prototype":
                    icon = self.node_icon_function
                elif (
                    k == "typedef"
                    or k == "struct"
                    or k == "enum"
                    or k == "union"
                ):
                    icon = self.node_icon_type
                elif k == "enumerator":
                    icon = self.node_icon_const
                elif k == "include":
                    icon = self.node_icon_import
                elif k == "define":
                    icon = self.node_icon_macro
                elif k == "pragma":
                    icon = self.node_icon_pragma
                elif k == "undef":
                    icon = self.node_icon_macro
                elif k == "error":
                    icon = self.node_icon_macro
                elif k == "macro":
                    icon = self.node_icon_macro
                elif k == "member":
                    icon = self.node_icon_method
                else:
                    icon = self.node_icon_unknown

                item.setEditable(False)
                item.setForeground(label_brush)
                item.setFont(label_font)
                # Create nodes as tree items
                current_list = sorted(current_list, key=lambda x: x.name)
                for n in current_list:
                    # Set the function node text
                    node_text = n.name + " (line:"
                    node_text += str(n.line_number) + ")"
                    # Construct the node and add it to the tree
                    node = qt.QStandardItem(node_text)
                    node.setEditable(False)
                    node.setIcon(icon)

                    if n.children != []:
                        display_node(node, n)

                    item.appendRow(node)

                    if k == "struct":
                        struct_list[n.name] = node
                # Check if there were any nodes found
                if current_list == []:
                    item_no_nodes = qt.QStandardItem("No items found")
                    item_no_nodes.setEditable(False)
                    item.appendRow(item_no_nodes)
                # Append the nodes to the parent node
                tree_node.appendRow(item)
            # Add the struct members directly to the structs
            if "member" in node_group.keys():
                for n in node_group["member"]:
                    # Set the function node text
                    node_text = n.name + " (line:"
                    node_text += str(n.line_number) + ")"
                    # Construct the node and add it to the tree
                    node = qt.QStandardItem(node_text)
                    node.setEditable(False)
                    node.setIcon(self.node_icon_method)
                    struct_list[n.parent].appendRow(node)

        # Define the document name, type
        document_name = os.path.basename(custom_editor.save_name)
        document_name_text = "DOCUMENT: {:s}".format(document_name)
        document_type_text = "TYPE: {:s}".format(
            custom_editor.current_file_type
        )
        # Initialize the tree display
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        #        tree_model.setHorizontalHeaderLabels([document_name])
        self.header().hide()
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        # Add the file attributes to the tree display
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["keyword"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_document_name = qt.QStandardItem(document_name_text)
        item_document_name.setEditable(False)
        item_document_name.setForeground(description_brush)
        item_document_name.setFont(description_font)
        item_document_type = qt.QStandardItem(document_type_text)
        item_document_type.setEditable(False)
        item_document_type.setForeground(description_brush)
        item_document_type.setFont(description_font)
        item_document_type.setIcon(self.c_icon)
        tree_model.appendRow(item_document_name)
        tree_model.appendRow(item_document_type)
        # Add the items recursively
        display_node(tree_model, module[0])
        # Resize the header so the horizontal scrollbar will have the correct width
        self._resize_horizontal_scrollbar()

    def display_nim_nodes(self, custom_editor, nim_nodes):
        """Display the Nim nodes in a tree structure."""
        # Store the custom editor tab that for quicker navigation
        self.bound_tab = custom_editor
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.NODES)
        # Define the document name, type
        document_name = os.path.basename(custom_editor.save_name)
        document_name_text = "DOCUMENT: {:s}".format(document_name)
        document_type_text = "TYPE: {:s}".format(
            custom_editor.current_file_type
        )
        # Initialize the tree display
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        #        tree_model.setHorizontalHeaderLabels([document_name])
        self.header().hide()
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        # Add the file attributes to the tree display
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["keyword"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_document_name = qt.QStandardItem(document_name_text)
        item_document_name.setEditable(False)
        item_document_name.setForeground(description_brush)
        item_document_name.setFont(description_font)
        item_document_type = qt.QStandardItem(document_type_text)
        item_document_type.setEditable(False)
        item_document_type.setForeground(description_brush)
        item_document_type.setFont(description_font)
        item_document_type.setIcon(self.nim_icon)
        tree_model.appendRow(item_document_name)
        tree_model.appendRow(item_document_type)
        """Add the nodes."""
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )

        # Nested function for creating a tree node
        def create_tree_node(
            node_text,
            node_text_brush,
            node_text_font,
            node_icon,
            node_line_number,
        ):
            tree_node = qt.QStandardItem(node_text)
            tree_node.setEditable(False)
            if node_text_brush is not None:
                tree_node.setForeground(node_text_brush)
            if node_text_font is not None:
                tree_node.setFont(node_text_font)
            if node_icon is not None:
                tree_node.setIcon(node_icon)
            if node_line_number is not None:
                tree_node.line_number = node_line_number
            return tree_node

        # Nested recursive function for displaying nodes
        def show_nim_node(tree, parent_node, new_node):
            # Nested function for retrieving the nodes name attribute case insensitively
            def get_case_insensitive_name(item):
                name = item.name
                return name.lower()

            # Check if parent node is set, else append to the main tree model
            appending_node = parent_node
            if parent_node is None:
                appending_node = tree
            if new_node.imports != []:
                item_imports_node = create_tree_node(
                    "IMPORTS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_imports_node)
                # Sort the list by the name attribute
                new_node.imports.sort(key=get_case_insensitive_name)
                # new_node.imports.sort(key=operator.attrgetter('name'))
                for module in new_node.imports:
                    item_module_node = create_tree_node(
                        module.name,
                        None,
                        None,
                        self.node_icon_import,
                        module.line + 1,
                    )
                    item_imports_node.appendRow(item_module_node)
            if new_node.types != []:
                item_types_node = create_tree_node(
                    "TYPES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_types_node)
                # Sort the list by the name attribute
                new_node.types.sort(key=get_case_insensitive_name)
                for type in new_node.types:
                    item_type_node = create_tree_node(
                        type.name,
                        None,
                        None,
                        self.node_icon_type,
                        type.line + 1,
                    )
                    item_types_node.appendRow(item_type_node)
            if new_node.consts != []:
                item_consts_node = create_tree_node(
                    "CONSTANTS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_consts_node)
                # Sort the list by the name attribute
                new_node.consts.sort(key=get_case_insensitive_name)
                for const in new_node.consts:
                    item_const_node = create_tree_node(
                        const.name,
                        None,
                        None,
                        self.node_icon_const,
                        const.line + 1,
                    )
                    item_consts_node.appendRow(item_const_node)
            if new_node.lets != []:
                item_lets_node = create_tree_node(
                    "SINGLE ASSIGNMENT VARIABLES:",
                    label_brush,
                    label_font,
                    None,
                    None,
                )
                appending_node.appendRow(item_lets_node)
                # Sort the list by the name attribute
                new_node.consts.sort(key=get_case_insensitive_name)
                for let in new_node.lets:
                    item_let_node = create_tree_node(
                        let.name, None, None, self.node_icon_const, let.line + 1
                    )
                    item_lets_node.appendRow(item_let_node)
            if new_node.vars != []:
                item_vars_node = create_tree_node(
                    "VARIABLES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_vars_node)
                # Sort the list by the name attribute
                new_node.vars.sort(key=get_case_insensitive_name)
                for var in new_node.vars:
                    item_var_node = create_tree_node(
                        var.name,
                        None,
                        None,
                        self.node_icon_variable,
                        var.line + 1,
                    )
                    item_vars_node.appendRow(item_var_node)
            if new_node.procedures != []:
                item_procs_node = create_tree_node(
                    "PROCEDURES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_procs_node)
                # Sort the list by the name attribute
                new_node.procedures.sort(key=get_case_insensitive_name)
                for proc in new_node.procedures:
                    item_proc_node = create_tree_node(
                        proc.name,
                        None,
                        None,
                        self.node_icon_procedure,
                        proc.line + 1,
                    )
                    item_procs_node.appendRow(item_proc_node)
                    show_nim_node(None, item_proc_node, proc)
            if new_node.forward_declarations != []:
                item_fds_node = create_tree_node(
                    "FORWARD DECLARATIONS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_fds_node)
                # Sort the list by the name attribute
                new_node.forward_declarations.sort(
                    key=get_case_insensitive_name
                )
                for proc in new_node.forward_declarations:
                    item_fd_node = create_tree_node(
                        proc.name,
                        None,
                        None,
                        self.node_icon_procedure,
                        proc.line + 1,
                    )
                    item_fds_node.appendRow(item_fd_node)
                    show_nim_node(None, item_fd_node, proc)
            if new_node.converters != []:
                item_converters_node = create_tree_node(
                    "CONVERTERS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_converters_node)
                # Sort the list by the name attribute
                new_node.converters.sort(key=get_case_insensitive_name)
                for converter in new_node.converters:
                    item_converter_node = create_tree_node(
                        converter.name,
                        None,
                        None,
                        self.node_icon_converter,
                        converter.line + 1,
                    )
                    item_converters_node.appendRow(item_converter_node)
                    show_nim_node(None, item_converter_node, converter)
            if new_node.iterators != []:
                item_iterators_node = create_tree_node(
                    "ITERATORS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_iterators_node)
                # Sort the list by the name attribute
                new_node.iterators.sort(key=get_case_insensitive_name)
                for iterator in new_node.iterators:
                    item_iterator_node = create_tree_node(
                        iterator.name,
                        None,
                        None,
                        self.node_icon_iterator,
                        iterator.line + 1,
                    )
                    item_iterators_node.appendRow(item_iterator_node)
                    show_nim_node(None, item_iterator_node, iterator)
            if new_node.methods != []:
                item_methods_node = create_tree_node(
                    "METHODS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_methods_node)
                # Sort the list by the name attribute
                new_node.methods.sort(key=get_case_insensitive_name)
                for method in new_node.methods:
                    item_method_node = create_tree_node(
                        method.name,
                        None,
                        None,
                        self.node_icon_method,
                        method.line + 1,
                    )
                    item_methods_node.appendRow(item_method_node)
                    show_nim_node(None, item_method_node, method)
            if new_node.properties != []:
                item_properties_node = create_tree_node(
                    "PROPERTIES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_properties_node)
                # Sort the list by the name attribute
                new_node.properties.sort(key=get_case_insensitive_name)
                for property in new_node.properties:
                    item_property_node = create_tree_node(
                        property.name,
                        None,
                        None,
                        self.node_icon_method,
                        property.line + 1,
                    )
                    item_properties_node.appendRow(item_property_node)
                    show_nim_node(None, item_property_node, property)
            if new_node.macros != []:
                item_macros_node = create_tree_node(
                    "MACROS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_macros_node)
                # Sort the list by the name attribute
                new_node.macros.sort(key=get_case_insensitive_name)
                for macro in new_node.macros:
                    item_macro_node = create_tree_node(
                        macro.name,
                        None,
                        None,
                        self.node_icon_macro,
                        macro.line + 1,
                    )
                    item_macros_node.appendRow(item_macro_node)
                    show_nim_node(None, item_macro_node, macro)
            if new_node.templates != []:
                item_templates_node = create_tree_node(
                    "TEMPLATES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_templates_node)
                # Sort the list by the name attribute
                new_node.templates.sort(key=get_case_insensitive_name)
                for template in new_node.templates:
                    item_template_node = create_tree_node(
                        template.name,
                        None,
                        None,
                        self.node_icon_template,
                        template.line + 1,
                    )
                    item_templates_node.appendRow(item_template_node)
                    show_nim_node(None, item_template_node, template)
            if new_node.objects != []:
                item_classes_node = create_tree_node(
                    "OBJECTS:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_classes_node)
                # Sort the list by the name attribute
                new_node.objects.sort(key=get_case_insensitive_name)
                for obj in new_node.objects:
                    item_class_node = create_tree_node(
                        obj.name, None, None, self.node_icon_class, obj.line + 1
                    )
                    item_classes_node.appendRow(item_class_node)
                    show_nim_node(None, item_class_node, obj)
            if new_node.namespaces != []:
                item_namespaces_node = create_tree_node(
                    "NAMESPACES:", label_brush, label_font, None, None
                )
                appending_node.appendRow(item_namespaces_node)
                # Sort the list by the name attribute
                new_node.namespaces.sort(key=get_case_insensitive_name)
                for namespace in new_node.namespaces:
                    item_namespace_node = create_tree_node(
                        namespace.name,
                        None,
                        None,
                        self.node_icon_namespace,
                        namespace.line + 1,
                    )
                    item_namespaces_node.appendRow(item_namespace_node)
                    show_nim_node(None, item_namespace_node, namespace)

        show_nim_node(tree_model, None, nim_nodes)

    def _init_found_files_options(
        self, search_text, directory, custom_text=None
    ):
        # Initialize the tree display to the found files type
        self.horizontalScrollbarAction(1)
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        tree_model.setHorizontalHeaderLabels(["FOUND FILES TREE"])
        self.header().hide()
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        """Define the description details."""
        # Font
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["keyword"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        # Directory item
        item_directory = qt.QStandardItem(
            self.search_icon,
            "BASE DIRECTORY: {:s}".format(directory.replace("\\", "/")),
        )
        item_directory.setEditable(False)
        item_directory.setForeground(description_brush)
        item_directory.setFont(description_font)
        # Search item, display according to the custom text parameter
        if custom_text is None:
            item_search_text = qt.QStandardItem(
                "FILE HAS: {:s}".format(search_text)
            )
        else:
            item_search_text = qt.QStandardItem(custom_text)
        item_search_text.setEditable(False)
        item_search_text.setForeground(description_brush)
        item_search_text.setFont(description_font)
        item_directory.appendRow(item_search_text)
        tree_model.appendRow(item_directory)
        self.expand(item_directory.index())
        return tree_model

    def _init_explorer_options(self, search_text, directory):
        # Initialize the tree display to the found files type
        self.horizontalScrollbarAction(1)
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel(0, 2)
        tree_model.setHorizontalHeaderLabels(
            ["Directories & Files", "Item status"]
        )
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        return tree_model

    def _init_replace_in_files_options(
        self, search_text, replace_text, directory
    ):
        # Initialize the tree display to the found files type
        self.horizontalScrollbarAction(1)
        self.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        tree_model = qt.QStandardItemModel()
        tree_model.setHorizontalHeaderLabels(["REPLACED IN FILES TREE"])
        self.header().hide()
        self._clean_model()
        self.setModel(tree_model)
        self.setUniformRowHeights(True)
        self._set_font_size(data.general_font_scale)
        """Define the description details."""
        # Font
        description_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["default"]["color"])
        )
        description_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        # Directory item
        item_directory = qt.QStandardItem(
            "BASE DIRECTORY: {:s}".format(directory.replace("\\", "/"))
        )
        item_directory.setEditable(False)
        item_directory.setForeground(description_brush)
        item_directory.setFont(description_font)
        # Search item
        item_search_text = qt.QStandardItem(
            "SEARCH TEXT: {:s}".format(search_text)
        )
        item_search_text.setEditable(False)
        item_search_text.setForeground(description_brush)
        item_search_text.setFont(description_font)
        # Replace item
        item_replace_text = qt.QStandardItem(
            "REPLACE TEXT: {:s}".format(replace_text)
        )
        item_replace_text.setEditable(False)
        item_replace_text.setForeground(description_brush)
        item_replace_text.setFont(description_font)
        tree_model.appendRow(item_directory)
        tree_model.appendRow(item_search_text)
        tree_model.appendRow(item_replace_text)
        return tree_model

    def _sort_item_list(self, items, base_directory):
        """Helper function for sorting a file/directory list so that all of the
        directories are before any files in the list."""
        sorted_directories = []
        sorted_files = []
        for item in items:
            dir = os.path.dirname(item)
            if not dir in sorted_directories:
                sorted_directories.append(dir)
            if os.path.isfile(item):
                sorted_files.append(item)
        # Remove the base directory from the directory list, it is not needed
        if base_directory in sorted_directories:
            sorted_directories.remove(base_directory)
        # Sort the two lists case insensitively
        sorted_directories.sort(key=str.lower)
        sorted_files.sort(key=str.lower)
        # Combine the file and directory lists
        sorted_items = sorted_directories + sorted_files
        return sorted_items

    def _add_items_to_tree(self, tree_model, directory, items):
        """Helper function for adding files to a tree view."""
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["default"]["color"])
        )
        item_font = qt.QFont(data.current_font_name, data.general_font_scale)
        # Check if any files were found
        if items != []:
            # Set the UNIX file format to the directory
            directory = directory.replace("\\", "/")
            """Adding the files."""
            # Create the base directory item that will hold all of the found files
            item_base_directory = qt.QStandardItem(directory)
            item_base_directory.setEditable(False)
            item_base_directory.setForeground(label_brush)
            item_base_directory.setFont(label_font)
            item_base_directory.setIcon(self.folder_icon)
            # Add an indicating attribute that shows the item is a directory.
            # It's a python object, attributes can be added dynamically!
            item_base_directory.is_base = True
            item_base_directory.full_name = directory
            # Create the base directory object that will hold everything else
            base_directory = self.Directory(item_base_directory)
            # Create the files that will be added last directly to the base directory
            base_files = {}
            # Sort the item list so that all of the directories are before the files
            sorted_items = self._sort_item_list(items, directory)
            # Loop through the files while creating the directory tree
            for item_with_path in sorted_items:
                if os.path.isfile(item_with_path):
                    file = item_with_path.replace(directory, "")
                    file_name = os.path.basename(file)
                    directory_name = os.path.dirname(file)
                    # Strip the first "/" from the files directory
                    if directory_name.startswith("/"):
                        directory_name = directory_name[1:]
                    # Initialize the file item
                    item_file = qt.QStandardItem(file_name)
                    item_file.setEditable(False)
                    item_file.setForeground(item_brush)
                    item_file.setFont(item_font)
                    qicon = iconfunctions.get_language_document_qicon(file_name)
                    item_file.setIcon(qicon)

                    #                    item_file.setCheckable(True)
                    #                    item_file.setTristate(True)
                    #                    item_file.setToolTip("MyToolTip")

                    # Add an atribute that will hold the full file name to the QStandartItem.
                    # It's a python object, attributes can be added dynamically!
                    item_file.full_name = item_with_path
                    # Check if the file is in the base directory
                    if directory_name == "":
                        # Store the file item for adding to the bottom of the tree
                        base_files[file_name] = item_file
                    else:
                        # Check the previous file items directory structure
                        parsed_directory_list = directory_name.split("/")
                        # Create the new directories
                        current_directory = base_directory
                        for dir in parsed_directory_list:
                            # Check if the current loop directory already exists
                            if dir in current_directory.directories:
                                current_directory = (
                                    current_directory.directories[dir]
                                )
                        # Add the file to the directory
                        current_directory.add_file(file_name, item_file)
                else:
                    directory_name = item_with_path.replace(directory, "")
                    # Strip the first "/" from the files directory
                    if directory_name.startswith("/"):
                        directory_name = directory_name[1:]
                    # Check the previous file items directory structure
                    parsed_directory_list = directory_name.split("/")
                    # Create the new directories
                    current_directory = base_directory
                    for dir in parsed_directory_list:
                        # Check if the current loop directory already exists
                        if dir in current_directory.directories:
                            current_directory = current_directory.directories[
                                dir
                            ]
                        else:
                            # Create the new directory item
                            item_new_directory = qt.QStandardItem(dir)
                            item_new_directory.setEditable(False)
                            item_new_directory.setIcon(self.folder_icon)
                            item_new_directory.setForeground(item_brush)
                            item_new_directory.setFont(item_font)
                            # Add an indicating attribute that shows the item is a directory.
                            # It's a python object, attributes can be added dynamically!
                            item_new_directory.is_dir = True
                            item_new_directory.full_name = item_with_path
                            current_directory = current_directory.add_directory(
                                dir, item_new_directory
                            )
            # Add the base level files from the stored dictionary, first sort them
            for file_key in sorted(base_files, key=str.lower):
                base_directory.add_file(file_key, base_files[file_key])
            tree_model.appendRow(item_base_directory)
            # Expand the base directory item
            self.expand(item_base_directory.index())
            # Resize the header so the horizontal scrollbar will have the correct width
            self._resize_horizontal_scrollbar()
        else:
            item_no_files_found = qt.QStandardItem("No items found")
            item_no_files_found.setEditable(False)
            item_no_files_found.setIcon(self.node_icon_nothing)
            item_no_files_found.setForeground(label_brush)
            item_no_files_found.setFont(label_font)
            tree_model.appendRow(item_no_files_found)

    def _add_items_with_lines_to_tree(self, tree_model, directory, items):
        """Helper function for adding files to a tree view."""
        label_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["string"]["color"])
        )
        label_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
            qt.QFont.Weight.Bold,
        )
        item_brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["default"]["color"])
        )
        item_font = qt.QFont(
            data.current_font_name,
            int(data.general_font_scale),
        )
        # Check if any files were found
        if items != {}:
            # Set the UNIX file format to the directory
            directory = directory.replace("\\", "/")
            """Adding the files."""
            # Create the base directory item that will hold all of the found files
            item_base_directory = qt.QStandardItem(directory)
            item_base_directory.setEditable(False)
            item_base_directory.setForeground(label_brush)
            item_base_directory.setFont(label_font)
            item_base_directory.setIcon(self.folder_icon)
            # Create the base directory object that will hold everything else
            base_directory = self.Directory(item_base_directory)
            # Create the files that will be added last directly to the base directory
            base_files = {}
            # Sort the the item list so that all of the directories are before the files
            items_list = list(items.keys())
            sorted_items = self._sort_item_list(items_list, directory)
            # Loop through the files while creating the directory tree
            for item_with_path in sorted_items:
                if os.path.isfile(item_with_path):
                    file = item_with_path.replace(directory, "")
                    file_name = os.path.basename(file)
                    directory_name = os.path.dirname(file)
                    # Strip the first "/" from the files directory
                    if directory_name.startswith("/"):
                        directory_name = directory_name[1:]
                    # Initialize the file item
                    item_file = qt.QStandardItem(file_name)
                    item_file.setEditable(False)
                    qicon = iconfunctions.get_language_document_qicon(file_name)
                    item_file.setIcon(qicon)
                    item_file.setForeground(item_brush)
                    item_file.setFont(item_font)
                    # Add an atribute that will hold the full file name to the QStandartItem.
                    # It's a python object, attributes can be added dynamically!
                    item_file.full_name = item_with_path
                    for line in items[item_with_path]:
                        # Adjust the line numbering to embeetle (1 to end)
                        line += 1
                        # Create the goto line item
                        item_line = qt.QStandardItem("line {:d}".format(line))
                        item_line.setEditable(False)
                        item_line.setIcon(self.goto_icon)
                        item_line.setForeground(item_brush)
                        item_line.setFont(item_font)
                        # Add the file name and line number as attributes
                        item_line.full_name = item_with_path
                        item_line.line_number = line
                        item_file.appendRow(item_line)
                    # Check if the file is in the base directory
                    if directory_name == "":
                        # Store the file item for adding to the bottom of the tree
                        base_files[file_name] = item_file
                    else:
                        # Check the previous file items directory structure
                        parsed_directory_list = directory_name.split("/")
                        # Create the new directories
                        current_directory = base_directory
                        for dir in parsed_directory_list:
                            # Check if the current loop directory already exists
                            if dir in current_directory.directories:
                                current_directory = (
                                    current_directory.directories[dir]
                                )
                        # Add the file to the directory
                        current_directory.add_file(file_name, item_file)
                else:
                    directory_name = item_with_path.replace(directory, "")
                    # Strip the first "/" from the files directory
                    if directory_name.startswith("/"):
                        directory_name = directory_name[1:]
                    # Check the previous file items directory structure
                    parsed_directory_list = directory_name.split("/")
                    # Create the new directories
                    current_directory = base_directory
                    for dir in parsed_directory_list:
                        # Check if the current loop directory already exists
                        if dir in current_directory.directories:
                            current_directory = current_directory.directories[
                                dir
                            ]
                        else:
                            # Create the new directory item
                            item_new_directory = qt.QStandardItem(dir)
                            item_new_directory.setEditable(False)
                            item_new_directory.setIcon(self.folder_icon)
                            item_new_directory.setForeground(item_brush)
                            item_new_directory.setFont(item_font)
                            # Add an indicating attribute that shows the item is a directory.
                            # It's a python object, attributes can be added dynamically!
                            item_new_directory.is_dir = True
                            current_directory = current_directory.add_directory(
                                dir, item_new_directory
                            )
            # Add the base level files from the stored dictionary, first sort them
            for file_key in sorted(base_files, key=str.lower):
                base_directory.add_file(file_key, base_files[file_key])
            tree_model.appendRow(item_base_directory)
            # Expand the base directory item
            self.expand(item_base_directory.index())
            # Resize the header so the horizontal scrollbar will have the correct width
            self._resize_horizontal_scrollbar()
        else:
            item_no_files_found = qt.QStandardItem("No items found")
            item_no_files_found.setEditable(False)
            item_no_files_found.setIcon(self.node_icon_nothing)
            item_no_files_found.setForeground(item_brush)
            item_no_files_found.setFont(item_font)
            tree_model.appendRow(item_no_files_found)

    def display_directory_tree(self, directory):
        """Display the selected directory in a tree view structure."""
        # Set the tree display type to FILES
        self.set_display_type(data.TreeDisplayType.FILES)
        # Create the walk generator that returns all files/subdirectories
        try:
            walk_generator = os.walk(directory)
        except:
            self.main_form.display.display_message_with_type(
                "Invalid directory!", message_type=data.MessageType.ERROR
            )
            return
        # Initialize and display the search options
        tree_model = self._init_explorer_options(None, directory)
        # Initialize the list that will hold both the directories and files
        found_items = []
        for item in walk_generator:
            base_directory = item[0]
            for dir in item[1]:
                found_items.append(
                    os.path.join(base_directory, dir).replace("\\", "/")
                )
            for file in item[2]:
                found_items.append(
                    os.path.join(base_directory, file).replace("\\", "/")
                )
        # Add the items to the treeview
        self._add_items_to_tree(tree_model, directory, found_items)

    def display_found_files(self, search_text, found_files, directory):
        """Display files that were found using the 'functions' module's
        find_files function."""
        # Check if found files are valid
        if found_files is None:
            self.main_form.display.display_message_with_type(
                "Error in finding files!", message_type=data.MessageType.WARNING
            )
            return
        # Set the tree display type to FILES
        self.set_display_type(data.TreeDisplayType.FILES)
        # Initialize and display the search options
        tree_model = self._init_found_files_options(search_text, directory)
        # Sort the found file list
        found_files.sort(key=str.lower)
        # Add the items to the treeview
        self._add_items_to_tree(tree_model, directory, found_files)

    def display_found_files_with_lines(
        self, search_text, found_files, directory
    ):
        """Display files with lines that were found using the 'functions'
        module's find_in_files function."""
        # Check if found files are valid
        if found_files is None:
            self.main_form.display.display_message_with_type(
                "Error in finding files!", message_type=data.MessageType.WARNING
            )
            return
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.FILES_WITH_LINES)
        # Initialize and display the search options
        tree_model = self._init_found_files_options(search_text, directory)
        # Add the items with lines to the treeview
        self._add_items_with_lines_to_tree(tree_model, directory, found_files)

    def display_replacements_in_files(
        self, search_text, replace_text, replaced_files, directory
    ):
        """Display files with lines that were replaces using the 'functions'
        module's replace_text_in_files_enum function."""
        # Check if found files are valid
        if replaced_files is None:
            self.main_form.display.display_message_with_type(
                "Error in finding files!", message_type=data.MessageType.WARNING
            )
            return
        # Set the tree display type to NODE
        self.set_display_type(data.TreeDisplayType.FILES_WITH_LINES)
        # Initialize and display the search options
        tree_model = self._init_replace_in_files_options(
            search_text, replace_text, directory
        )
        # Add the items with lines to the treeview
        self._add_items_with_lines_to_tree(
            tree_model, directory, replaced_files
        )

    def customize_context_menu(self):
        self._customize_context_menu(self.tree_menu, self.default_menu_font)
