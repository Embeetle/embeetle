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

import functools
import os
import traceback

import data
import debugger.debuggerwindow
import debugger.memoryviews
import functions
import gui.consoles.standardconsole
import gui.forms.customeditor
import gui.forms.messagewindow
import gui.forms.tabwidget
import gui.forms.terminal
import gui.stylesheets.splitter
import qt


class TheBox(qt.QSplitter):
    name = None
    parent_name = None
    generated_name = None
    main_form = None

    def __init__(self, name, parent_name, orientation, parent, main_form):
        super().__init__(orientation, parent)
        self.main_form = main_form
        self._generate_name(name, parent_name)
        # Disable collapsing of children
        self.setChildrenCollapsible(False)
        # Connect the signals
        self.splitterMoved.connect(self.splitterMoveEvent)
        # Update style
        self.update_style()

    def _generate_name(self, name, parent_name):
        self.name = name
        self.parent_name = parent_name
        if self.name == "":
            self.generated_name = parent_name
        else:
            self.generated_name = ".".join([parent_name, name])
        self.setObjectName(self.generated_name)

    def _get_number_of_tabs(self):
        count = 0
        for t in self.main_form.get_all_windows():
            if self.generated_name in t.objectName():
                count += 1
        return count

    def __set_stretch_factors(self, moved_index=None):
        def check_widget(widget, orientation, moved_index=None):
            if moved_index is None:
                moved_index = 0
            if isinstance(widget, TheBox):
                for i in range(widget.count()):
                    if widget.orientation() == orientation:
                        if i != moved_index:
                            widget.setStretchFactor(i, 0)
                        else:
                            widget.setStretchFactor(i, 1)
                        w = widget.widget(i)
                    if isinstance(w, TheBox):
                        check_widget(w, w.orientation())

        check_widget(self, self.orientation(), moved_index)

    def is_empty(self):
        return self.count() == 0

    def get_orientation_letter(self):
        if self.orientation() == qt.Qt.Orientation.Vertical:
            return "V"
        else:
            return "H"

    def update_orientations(self):
        if self.orientation() == qt.Qt.Orientation.Vertical:
            name = functions.right_replace(self.objectName(), "H", "V", 1)
        else:
            name = functions.right_replace(self.objectName(), "V", "H", 1)
        self.setObjectName(name)
        self.generated_name = name
        parent = self.parent()
        if isinstance(parent, TheBox) and parent.objectName() != "Main":
            parent.update_orientations()

    def add_box(self, orientation, index=None, add_tabs=True):
        if orientation == qt.Qt.Orientation.Vertical:
            name_symbol = "V"
        else:
            name_symbol = "H"
        if index is not None:
            name = f"{name_symbol}{index}"
        else:
            # Count needed indexes
            new_index = self.count()
            name = f"{name_symbol}{new_index}"
        box = TheBox(
            name, self.generated_name, orientation, self, self.main_form
        )
        if index is not None:
            self.insertWidget(index, box)
        else:
            self.addWidget(box)
        if add_tabs == True:
            tabs_number = self._get_number_of_tabs()
            tab_widget = gui.forms.tabwidget.TabWidget(
                self, self.main_form, self
            )
            tab_widget.setObjectName(box.generated_name + f".Tabs{tabs_number}")
            box.addWidget(tab_widget)
        #        self.__set_stretch_factors()
        return box

    def add_tabs(self, index=None):
        tabs_number = self._get_number_of_tabs()
        tab_widget = gui.forms.tabwidget.TabWidget(self, self.main_form, self)
        tab_widget.setObjectName(self.generated_name + f".Tabs{tabs_number}")
        if index is not None:
            self.insertWidget(index, tab_widget)
        else:
            self.addWidget(tab_widget)
        #        self.__set_stretch_factors()
        return tab_widget

    def rename(self, new_name):
        current_name = self.objectName()
        self.setObjectName(new_name)
        self.generated_name = new_name
        for b in self.main_form.findChildren(TheBox):
            on = b.objectName()
            if current_name in on:
                b.setObjectName(on.replace(current_name, new_name))
        for t in self.main_form.findChildren(gui.forms.tabwidget.TabWidget):
            on = t.objectName()
            if current_name in on:
                t.setObjectName(on.replace(current_name, new_name))

    def clear_all(self):
        for i in reversed(range(self.count())):
            self.widget(i).hide()
            self.widget(i).setParent(None)
        for i in self.findChildren(TheBox):
            i.deleteLater()
            i.setParent(None)

    def get_child_boxes(self):
        classes, inverted_classes = self.main_form.view._get_layout_classes()
        children = {}
        for i in range(self.count()):
            child = self.widget(i)
            if isinstance(child, TheBox):
                orientation = child.get_orientation_letter()
                children[i] = {
                    f"BOX-{orientation}": child.get_child_boxes(),
                    "SIZES": child.sizes(),
                }
            else:
                tabs = {}
                for j in range(child.count()):
                    w = child.widget(j)
                    name = w.name
                    if isinstance(w, gui.forms.customeditor.CustomEditor):
                        name = w.save_name
                        if data.current_project.check_if_project_file(name):
                            name = functions.create_project_relative_path(name)
                        line, index = w.getCursorPosition()
                        first_visible_line = w.firstVisibleLine()
                        x_view_offset = w.SendScintilla(
                            qt.QsciScintilla.SCI_GETXOFFSET
                        )
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "tab-index": j,
                            "data": {
                                "line": line,
                                "index": index,
                                "first-visible-line": first_visible_line,
                                "x-view-offset": x_view_offset,
                            },
                        }
                    elif isinstance(
                        w, debugger.memoryviews.MemoryViewGeneralRegisters
                    ):
                        auto_update = w.get_auto_update()
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {
                                "auto-update": auto_update,
                            },
                        }
                    elif isinstance(
                        w, debugger.memoryviews.MemoryViewRawMemory
                    ):
                        auto_update = w.get_auto_update()
                        memory_type = w.get_memory_type()
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {
                                "auto-update": auto_update,
                                "memory-type": memory_type,
                            },
                        }
                    elif isinstance(w, debugger.debuggerwindow.DebuggerWindow):
                        gdb_url = w.get_gdb_url()
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {
                                "gdb-url": gdb_url,
                            },
                        }
                    elif isinstance(w, gui.forms.terminal.Terminal):
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {},
                        }
                    elif isinstance(w, gui.forms.messagewindow.MessageWindow):
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {},
                        }
                    elif isinstance(
                        w, gui.consoles.standardconsole.StandardConsole
                    ):
                        tabs[name] = {
                            "class": inverted_classes[w.__class__],
                            "data": {"current-working-directory": w.cwd},
                        }
                    else:
                        tabs[name] = {"class": inverted_classes[w.__class__]}
                tabs["CURRENT-INDEX"] = child.currentIndex()
                children[i] = {"TABS": tabs}
        return children

    def update_style(self):
        self.setStyleSheet(
            gui.stylesheets.splitter.get_transparent_stylesheet()
        )

    """
    Overridden functions
    """

    def resizeEvent(self, e):
        super().resizeEvent(e)
        mouse_buttons = data.application.mouseButtons()
        if mouse_buttons == qt.Qt.MouseButton.LeftButton:
            self.main_form.view.layout_save()

    def splitterMoveEvent(self, pos, index):
        #        self.__set_stretch_factors(index-1)
        mouse_buttons = data.application.mouseButtons()
        if mouse_buttons == qt.Qt.MouseButton.LeftButton:
            self.main_form.view.layout_save()
