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
##  The base class for tree displays
##

import os
import qt
import data
import functions
import gui
import components.actionfilter
import components.iconmanipulator
import components.thesquid
import gui.stylesheets.treewidget
import gui.stylesheets.scrollbar as scrollbar


class TreeDisplayBase(qt.QTreeView):
    # Class variables
    _parent = None
    main_form = None
    name = ""
    savable = data.CanSave.NO
    tree_menu = None
    icon_manipulator = None
    # Background image stuff
    BACKGROUND_IMAGE_SIZE = (217, 217)
    BACKGROUND_IMAGE_OFFSET = (-55, -8)
    BACKGROUND_IMAGE_HEX_EDGE_LENGTH = 18

    def __del__(self) -> None:
        try:
            self.self_destruct()
        except Exception as ex:
            print(ex)
        return

    def self_destruct(self) -> None:
        """"""
        model = self.model()
        if model:
            root = model.invisibleRootItem()
            for item in self.iterate_items(root):
                if item is None:
                    continue
                item.setData(None)
                for row in range(item.rowCount()):
                    item.removeRow(row)
                for col in range(item.columnCount()):
                    item.removeRow(col)

        # Clean up the tree model
        self._clean_model()
        # Disconnect signals
        try:
            self.doubleClicked.disconnect()
        except:
            pass
        try:
            self.expanded.disconnect()
        except:
            pass
        self._parent = None
        self.main_form = None
        self.icon_manipulator = None
        if self.tree_menu is not None:
            self.tree_menu.setParent(None)  # noqa
            self.tree_menu = None
        # Clean up self
        self.setParent(None)  # noqa
        self.deleteLater()
        return

    def __init__(self, parent, main_form, name):
        # Initialize the superclass
        super().__init__(parent)

        # Initialize everything else
        self._parent = parent
        self.main_form = main_form
        self.name = name
        self.icon_manipulator = components.iconmanipulator.IconManipulator()
        # Set the icon size for every node
        self.update_icon_size()
        # Set the nodes to be animated on expand/contract
        self.setAnimated(True)
        # Disable node expansion on double click
        self.setExpandsOnDoubleClick(False)
        # Set the styling
        self.update_style()

    def update_style(self):
        # Scrollbars
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )

    """
    Private/Internal functions
    """

    def _create_standard_item(self, text, bold=False, icon=None):
        # Font
        brush = qt.QBrush(qt.QColor(data.theme["fonts"]["keyword"]["color"]))
        font = qt.QFont(
            data.current_font_name,
            data.get_general_font_height(),
        )
        font.setBold(bold)
        # Item initialization
        item = qt.QStandardItem(text)
        item.setEditable(False)
        item.setForeground(brush)
        item.setFont(font)
        # Set icon if needed
        if icon is not None:
            item.setIcon(icon)
        return item

    def _create_menu(self):
        self.tree_menu = qt.QMenu()
        self.default_menu_font = self.tree_menu.font()
        self.customize_context_menu()
        return self.tree_menu

    def _clean_model(self):
        if self.model() is not None:
            self.model().setParent(None)
            self.setModel(None)

    def _set_font_size(self, size_in_points):
        """Set the font size for the tree display items."""
        # Initialize the font with the new size
        new_font = qt.QFont(data.current_font_name, size_in_points)
        # Set the new font
        self.setFont(new_font)
        # Set the header font
        header_font = qt.QFont(self._parent.default_tab_font)
        header_font.setPointSize(size_in_points)
        header_font.setBold(True)
        self.header().setFont(header_font)

    def _check_contents(self):
        # Update the horizontal scrollbar width
        self._resize_horizontal_scrollbar()

    def _resize_horizontal_scrollbar(self):
        """Resize the header so the horizontal scrollbar will have the correct
        width."""
        for i in range(self.model().rowCount()):
            self.resizeColumnToContents(i)

    """
    Overridden functions
    """

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()

    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        """Function connected to the clicked signal of the tree display."""
        super().mousePressEvent(event)
        # Clear the selection if the index is invalid
        # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned object is a
        # QPointF() instead of a QPoint()
        posF: qt.QPointF = event.position()
        pos: qt.QPoint = posF.toPoint()
        index = self.indexAt(pos)

        if not index.isValid():
            self.clearSelection()
        # Set the focus
        self.setFocus()
        # Set the last focused widget to the parent basic widget
        self.main_form.last_focused_widget = self._parent
        # Set Save/SaveAs buttons in the menubar
        self._parent._set_save_status()
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()
        return

    """
    Public functions
    """

    def update_icon_size(self):
        self.setIconSize(
            qt.create_qsize(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            )
        )

    def _customize_context_menu(self, menu, default_menu_font):
        """This needs to be called in a subclass as needed."""
        if (
            data.get_toplevel_menu_pixelsize() is not None
            and data.get_global_font_family() is not None
        ):
            menu.update_style()
            self._set_font_size(data.get_general_font_height())
            font = qt.QFont(
                data.current_font_name, data.get_general_font_height()
            )
            if menu is not None:
                menu.setFont(font)
            # Recursively change the fonts of all items
            root = self.model().invisibleRootItem()
            for item in self.iterate_items(root):
                if item is None:
                    continue
                font.setBold(item.font().bold())
                item.setFont(font)
        else:
            if default_menu_font is None:
                return
            self._set_font_size(default_menu_font)
            if menu is not None:
                menu.update_style()
                menu.setFont(default_menu_font)
            # Recursively change the fonts of all items
            root = self.model().invisibleRootItem()
            for item in self.iterate_items(root):
                if item is None:
                    continue
                default_menu_font.setBold(item.font().bold())
                item.setFont(default_menu_font)

    def iterate_items(self, root=None):
        """Iterator that returns all tree items recursively."""
        if root is None:
            root = self.model().invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop(0)
            for row in range(parent.rowCount()):
                for column in range(parent.columnCount()):
                    child = parent.child(row, column)
                    yield child
                    if child is not None:
                        if child.hasChildren():
                            stack.append(child)
