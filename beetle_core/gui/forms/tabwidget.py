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
import functools
import traceback
import qt
import data
import functions
import purefunctions
import filefunctions
import iconfunctions
import gui.templates.textmanipulation
import gui.consoles.standardconsole
import helpdocs.help_subjects.tooltips


class TabWidget(qt.QTabWidget):
    """Basic widget used for holding QScintilla/QTextEdit/... objects."""

    class CustomTabBar(qt.QTabBar):
        class TabFrame(qt.QFrame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._index = None
                self.setStyleSheet("""
                    QFrame {
                        background: transparent;
                        border: 0px;
                    }
                    """)

            @property
            def index(self):
                return self._index

            @index.setter
            def index(self, value):
                self._index = value

        """
        Custom tab bar used to capture tab clicks, ...
        """
        # Layout constants
        SPACING = 3
        MARGINS = (5, 0, 5, 0)
        # Reference to the parent widget
        _parent = None
        # Reference to the main form
        main_form = None
        # Reference to the tab menu
        tab_menus = None
        # Color/tooltip list
        tab_settings = None
        # Cache for items that need style updates
        cache_close_button = []

        def __init__(self, parent, main_form):
            """Initialize the tab bar object."""
            # Initialize superclass
            super().__init__(parent)
            # Properties for stylesheets
            self.setProperty("indicated", False)
            # Store the parent reference
            self._parent = parent
            # Store the main form reference
            self.main_form = main_form
            # Connect the signals
            self.tabMoved.connect(self.__tab_moved_slot)
            self.currentChanged.connect(self.__current_tab_changed)
            # Enable mouse tracking move events
            self.setMouseTracking(True)
            self.mouse_hover_index = None
            # Initialize tab menus
            self.tab_menus = {}
            # Update style
            self.update_style()

            # Install the event filter

        #            self.installEventFilter(self)
        #        def eventFilter(self, object, event):
        #            print(event.type())
        #            return False

        #        def tabLayoutChange(self):
        #            pass

        def update_style(self):
            self.tab_settings = {
                data.FileType.Standard: {
                    "repaint": True,
                    "current_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.Standard]
                    ]["current_index"],
                    "other_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.Standard]
                    ]["other_index"],
                    "tooltip": helpdocs.help_subjects.tooltips.editor_tab(
                        "{}\nThis file is inside the project and has the "
                        + "standard WHITE/BLUE/GREY colors.\n"
                    ),
                },
                data.FileType.StandardIndicated: {
                    "repaint": True,
                    "current_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.StandardIndicated]
                    ]["current_index"],
                    "other_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.StandardIndicated]
                    ]["other_index"],
                    "tooltip": helpdocs.help_subjects.tooltips.editor_tab(
                        "{}\nThis file is the selected file in the active window."
                    ),
                },
                data.FileType.InsideCompiler: {
                    "repaint": True,
                    "current_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.InsideCompiler]
                    ]["current_index"],
                    "other_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.InsideCompiler]
                    ]["other_index"],
                    "tooltip": helpdocs.help_subjects.tooltips.editor_tab(
                        "{}\nThis file's tab is LIGHT-BLUE when selected because it "
                        + "is inside the compiler toolchain directory.\n"
                    ),
                },
                data.FileType.ExcludedFromProject: {
                    "repaint": True,
                    "current_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.ExcludedFromProject]
                    ]["current_index"],
                    "other_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.ExcludedFromProject]
                    ]["other_index"],
                    "tooltip": helpdocs.help_subjects.tooltips.editor_tab(
                        "{}\nThis file's tab is LIGHT-RED when selected because "
                        + "it is inside the project directory but is excluded,\n"
                        + "either manually or by the source analyzer.\n"
                    ),
                },
                data.FileType.OutsideOfProject: {
                    "repaint": True,
                    "current_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.OutsideOfProject]
                    ]["current_index"],
                    "other_index": data.theme["tab_headers"][
                        data.filelocations[data.FileType.OutsideOfProject]
                    ]["other_index"],
                    "tooltip": helpdocs.help_subjects.tooltips.editor_tab(
                        "{}\nThis file's tab is VIOLET when selected because "
                        + "it is outside the project or compiler directories.\n"
                    ),
                },
            }
            # Set stylesheet

            # Resize the right side groupbox
            for i in range(self.count()):
                groupbox = self.tabButton(
                    i, qt.QTabBar.ButtonPosition.RightSide
                )
                if groupbox is not None:
                    groupbox.setFixedSize(groupbox.sizeHint())

            # Update items from cache
            remove_list = []
            for item in TabWidget.CustomTabBar.cache_close_button:
                if not qt.sip.isdeleted(item):
                    item.update_style(
                        data.theme["tab_headers"]["close_button"]["active"][
                            "standard"
                        ],
                        data.theme["tab_headers"]["close_button"]["active"][
                            "press"
                        ],
                        data.theme["tab_headers"]["close_button"]["active"][
                            "hover"
                        ],
                        data.theme["tab_headers"]["close_button"]["active"][
                            "hover"
                        ],
                        data.theme["tab_headers"]["close_button"]["active"][
                            "standard"
                        ],
                        data.theme["tab_headers"]["close_button"]["passive"][
                            "standard"
                        ],
                        data.theme["tab_headers"]["close_button"]["passive"][
                            "press"
                        ],
                        data.theme["tab_headers"]["close_button"]["passive"][
                            "hover"
                        ],
                        data.theme["tab_headers"]["close_button"]["passive"][
                            "hover"
                        ],
                        data.theme["tab_headers"]["close_button"]["passive"][
                            "standard"
                        ],
                        qt.create_qsize(
                            data.get_custom_tab_pixelsize(),
                            data.get_custom_tab_pixelsize(),
                        ),
                    )
                else:
                    remove_list.append(item)
            for item in remove_list:
                TabWidget.CustomTabBar.cache_close_button.remove(item)

        def repolish(self):
            index = self._parent.currentIndex()
            if index != -1:
                self.refresh_tab_buttons(index)
            #            self.repaint() # This causes occasional C++ Qt errors
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = qt.QStylePainter(self)
            opt = qt.QStyleOptionTab()
            indication_state = self.property("indicated")

            def paint_normal(index):
                painter.drawControl(
                    qt.QStyle.ControlElement.CE_TabBarTabShape, opt
                )
                painter.drawControl(qt.QStyle.ControlElement.CE_TabBarTab, opt)
                painter.drawControl(
                    qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                )
                #                painter.drawText(
                #                    self.tabRect(index),
                #                    qt.Qt.AlignmentFlag.AlignVCenter | qt.Qt.AlignmentFlag.AlignHCenter,
                #                    self.tabText(index)
                #                )
                return

            def paint_colored(text_color, back_color, index):
                painter.setBrush(qt.QBrush(qt.QColor(back_color)))
                painter.setPen(qt.QPen(qt.QColor(back_color)))
                painter.setBackground(qt.QBrush(qt.QColor(back_color)))

                items = (
                    qt.QPalette.ColorRole.WindowText,
                    qt.QPalette.ColorRole.PlaceholderText,
                    qt.QPalette.ColorRole.Text,
                    qt.QPalette.ColorRole.ButtonText,
                    qt.QPalette.ColorRole.BrightText,
                    qt.QPalette.ColorRole.HighlightedText,
                )
                for it in items:
                    opt.palette.setBrush(it, qt.QColor(text_color))

                painter.drawRect(opt.rect)
                painter.drawControl(
                    qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                )

                #                painter.setPen(qt.QPen(qt.QColor("red")))
                #                painter.drawText(
                #                    self.tabRect(index),
                #                    qt.Qt.AlignmentFlag.AlignVCenter | qt.Qt.AlignmentFlag.AlignRight,
                #                    self.tabText(index)
                #                )
                return

            # CASE 1: No project active.
            if data.current_project is None:
                for i in range(self.count()):
                    self.initStyleOption(opt, i)
                    current_type_enum = data.FileType.Standard
                    if indication_state:
                        current_type_enum = data.FileType.StandardIndicated
                    current_type = self.tab_settings[current_type_enum]
                    if i == self.currentIndex():
                        ct = current_type["current_index"]
                        paint_colored(
                            text_color=ct["color"],
                            back_color=ct["background"],
                            index=i,
                        )
                    else:
                        paint_normal(i)
                return

            # CASE 2: Project active.
            for i in range(self.count()):
                self.initStyleOption(opt, i)
                w = self._parent.widget(i)
                skip_tooltip_assignment = False
                active_tab = i == self.currentIndex()

                # Tab is not a custom editor.
                if not isinstance(
                    w,
                    purefunctions.import_module(
                        "gui.forms.customeditor"
                    ).CustomEditor,
                ):
                    current_type_enum = data.FileType.Standard
                    if indication_state and active_tab:
                        current_type_enum = data.FileType.StandardIndicated
                    skip_tooltip_assignment = True
                else:
                    current_type_enum = functions.get_file_status(w.save_name)
                    if current_type_enum == data.FileType.Standard:
                        if indication_state and active_tab:
                            current_type_enum = data.FileType.StandardIndicated

                current_type = self.tab_settings[current_type_enum]
                if current_type["repaint"]:
                    if active_tab:
                        ct = current_type["current_index"]
                        paint_colored(
                            text_color=ct["color"],
                            back_color=ct["background"],
                            index=i,
                        )
                    else:
                        paint_normal(i)

                if not skip_tooltip_assignment:
                    file_path = "Not set yet, save document to a file first"
                    file_name = "Unknown"
                    if os.path.isfile(w.save_name):
                        file_path = w.save_name
                        file_name = os.path.basename(file_path)
                    tooltip = current_type["tooltip"].format(
                        f"Name: {file_name}\nPath: {file_path}\n"
                    )
                    self.setTabToolTip(i, tooltip)

            qt.QTimer.singleShot(50, self._check_scroller_visibility)

        def _check_scroller_visibility(self):
            size = sum([self.tabRect(i).width() for i in range(self.count())])
            w = self.width()
            if size > w and self._parent.count() > 1:
                self._parent.tab_scrollers_show()
            else:
                self._parent.tab_scrollers_hide()

        def _update_tab_indexes(self):
            # Readdress all tabs
            temp_tab_menus = self.tab_menus.copy()
            for i in range(self.count()):
                groupbox = self.tabButton(
                    i, qt.QTabBar.ButtonPosition.RightSide
                )
                if groupbox is not None:
                    adjust_condition = groupbox.index in temp_tab_menus.keys()
                    if adjust_condition:
                        self.tab_menus[i] = temp_tab_menus[groupbox.index]
                    else:
                        self.tab_menus[i] = None
                    groupbox.index = i

        def tabInserted(self, index):
            groupbox = self.TabFrame()
            layout = qt.QHBoxLayout()
            layout.setSpacing(int(self.SPACING))
            layout.setContentsMargins(*(int(x) for x in self.MARGINS))
            layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetNoConstraint)
            groupbox.setLayout(layout)
            groupbox.setSizePolicy(
                qt.QSizePolicy(
                    qt.QSizePolicy.Policy.MinimumExpanding,
                    qt.QSizePolicy.Policy.MinimumExpanding,
                )
            )

            # Close button
            def get_qpixmap(image):
                return iconfunctions.get_qpixmap(image)

            def close_function():
                close_index = groupbox.index
                self._parent.tabCloseRequested.emit(close_index)

            close_button = purefunctions.import_module(
                "gui.helpers.buttons"
            ).TabButton(
                "close",
                # Selected
                data.theme["tab_headers"]["close_button"]["active"]["standard"],
                data.theme["tab_headers"]["close_button"]["active"]["press"],
                data.theme["tab_headers"]["close_button"]["active"]["hover"],
                data.theme["tab_headers"]["close_button"]["active"]["hover"],
                data.theme["tab_headers"]["close_button"]["active"]["standard"],
                # Not selected
                data.theme["tab_headers"]["close_button"]["passive"][
                    "standard"
                ],
                data.theme["tab_headers"]["close_button"]["passive"]["press"],
                data.theme["tab_headers"]["close_button"]["passive"]["hover"],
                data.theme["tab_headers"]["close_button"]["passive"]["hover"],
                data.theme["tab_headers"]["close_button"]["passive"][
                    "standard"
                ],
                close_function,
                qt.create_qsize(
                    data.get_custom_tab_pixelsize(),
                    data.get_custom_tab_pixelsize(),
                ),
                parent=groupbox,
                background_transparent=True,
            )
            close_button.visible = True
            close_button.setObjectName("close-button")
            layout.addWidget(close_button)
            TabWidget.CustomTabBar.cache_close_button.append(close_button)

            widget = self._parent.widget(index)
            if (
                data.application_type == data.ApplicationType.Home
                and isinstance(self._parent.parent(), qt.QMainWindow)
            ):
                unclosable_tabs = [
                    "Projects",
                    "Updates",
                    "Toolbox",
                    "Vendors",
                    "Options",
                    "Libraries",
                    "Preferences",
                    "News",
                ]
                if widget.objectName() in unclosable_tabs:
                    close_button.setVisible(False)
                    close_button.visible = False

            # Store the groupbox
            self.setTabData(index, groupbox)

            self.setTabButton(
                index, qt.QTabBar.ButtonPosition.RightSide, groupbox
            )
            groupbox.show()
            self._update_tab_indexes()

        def tabRemoved(self, index):
            self._update_tab_indexes()

        @qt.pyqtSlot(int, int)
        def __tab_moved_slot(self, t_from, t_to):
            self._update_tab_indexes()

        @qt.pyqtSlot(int)
        def __current_tab_changed(self, current_index):
            data.signal_dispatcher.tab_index_changed.emit(
                current_index, self._parent, "tab-change"
            )
            buttons = data.application.mouseButtons()
            if buttons == qt.Qt.MouseButton.NoButton:
                self.refresh_tab_buttons(current_index)
            # Skip if not a project window
            if (
                data.application_type == data.ApplicationType.Home
                and isinstance(self._parent.parent(), qt.QMainWindow)
            ):
                return
            # Tooltips
            if not hasattr(self, "_tooltips"):
                module_dashboard = purefunctions.import_module(
                    "dashboard.chassis.dashboard"
                )
                module_make_console = purefunctions.import_module(
                    "beetle_console.make_console"
                )
                # Initialize the tooltips
                self._tooltips = {
                    purefunctions.import_module(
                        "gui.forms.customeditor"
                    ).CustomEditor: (
                        helpdocs.help_subjects.tooltips.editor_tab()
                    ),
                    purefunctions.import_module(
                        "gui.forms.messagewindow"
                    ).MessageWindow: (
                        helpdocs.help_subjects.tooltips.messageswindow_tab()
                    ),
                    purefunctions.import_module(
                        "gui.forms.newfiletree"
                    ).NewFiletree: (
                        helpdocs.help_subjects.tooltips.filetree_tab()
                    ),
                    purefunctions.import_module(
                        "gui.helpers.diagnosticwindow"
                    ).DiagnosticWindow: (
                        helpdocs.help_subjects.tooltips.diagnostics_tab()
                    ),
                    purefunctions.import_module(
                        "gui.helpers.symbolwindow"
                    ).SymbolWindow: (
                        helpdocs.help_subjects.tooltips.symbols_tab()
                    ),
                    module_dashboard.Dashboard: (
                        helpdocs.help_subjects.tooltips.dashboard_tab()
                    ),
                    module_make_console.MakeConsole: (
                        helpdocs.help_subjects.tooltips.general_console_tab()
                    ),
                }
            current_index = self._parent.currentIndex()
            for i in range(self._parent.count()):
                cls = self._parent.widget(i).__class__
                if cls in self._tooltips.keys():
                    self.setTabToolTip(i, self._tooltips[cls])

        def _refresh(self):
            index = self.__stored_index
            for i in range(self.count()):
                groupbox = self.tabButton(
                    i, qt.QTabBar.ButtonPosition.RightSide
                )
                if groupbox is None:
                    continue
                layout = groupbox.layout()
                # Set selected states
                for x in range(layout.count()):
                    item = layout.itemAt(x).widget()
                    item.setVisible(item.visible)
                    if (
                        isinstance(
                            item,
                            purefunctions.import_module(
                                "gui.helpers.buttons"
                            ).TabButton,
                        )
                        and self._parent.indicated
                    ):
                        item.set_selected(True)
                    else:
                        item.set_selected(False)

        def refresh_tab_buttons(self, index):
            if not hasattr(self, "_refresh_timer"):
                self._refresh_timer = qt.QTimer(self)
                self._refresh_timer.setSingleShot(True)
                self._refresh_timer.setInterval(10)
                self._refresh_timer.timeout.connect(self._refresh)
            self.__stored_index = index
            self._refresh_timer.stop()
            self._refresh_timer.start()

        def contextMenuEvent(self, event):
            index = self.tabAt(event.pos())
            if index in self.tab_menus.keys():
                if self.tab_menus[index] is not None:
                    self.tab_menus[index]()

        def add_rightclick_menu_function(
            self, index: int, func: Callable
        ) -> None:
            self.tab_menus[index] = func
            self._update_tab_indexes()

        def _set_tab_button_visibility(self, tab_index, button_index, visible):
            groupbox = self.tabButton(
                tab_index, qt.QTabBar.ButtonPosition.RightSide
            )
            if groupbox is None:
                return
            layout = groupbox.layout()
            button_item = layout.itemAt(button_index)
            if button_item is None:
                return
            button_widget = button_item.widget()
            if visible == True:
                button_widget.show()
            else:
                button_widget.hide()
            button_widget.visible = visible
            groupbox.adjustSize()
            self._force_resize()

        def _force_resize(self):
            # A hack to prevent the scroll buttons from disappearing
            self.setUsesScrollButtons(False)
            self.setUsesScrollButtons(True)

        def hide_tab_button(self, tab_index, button_index):
            self._set_tab_button_visibility(tab_index, button_index, False)

        def show_tab_button(self, tab_index, button_index):
            self._set_tab_button_visibility(tab_index, button_index, True)

        def scale_tab_buttons(self):
            for i in range(self.count()):
                groupbox = self.tabButton(
                    i, qt.QTabBar.ButtonPosition.RightSide
                )
                if groupbox is None:
                    continue
                layout = groupbox.layout()
                for j in range(layout.count()):
                    w = layout.itemAt(j).widget()
                    w.setFixedSize(
                        int(data.get_custom_tab_pixelsize()),
                        int(data.get_custom_tab_pixelsize()),
                    )
                    if isinstance(w, qt.QToolButton):
                        w.setIconSize(
                            qt.create_qsize(
                                data.get_custom_tab_pixelsize(),
                                data.get_custom_tab_pixelsize(),
                            )
                        )
            self._force_resize()

        def mousePressEvent(self, event):
            # Execute the superclass event method
            super().mousePressEvent(event)
            event_button = event.button()
            key_modifiers = qt.QApplication.keyboardModifiers()
            # Set focus to the clicked parent basic widget
            if hasattr(self.main_form.view, "indicate_window"):
                self.main_form.view.indicate_window(self._parent)
            self._parent.setFocus()
            # Check if symbols need updating
            current_tab = self._parent.currentWidget()
            if isinstance(
                current_tab,
                purefunctions.import_module(
                    "gui.forms.customeditor"
                ).CustomEditor,
            ):
                current_tab.set_symbol_analysis()
            elif isinstance(
                current_tab,
                purefunctions.import_module(
                    "gui.forms.messagewindow"
                ).MessageWindow,
            ):
                self.main_form.display.messages_button_reset()

            self._parent.store_drag_data()

        def mouseReleaseEvent(self, event):
            # Execute the superclass event method
            super().mouseReleaseEvent(event)
            event_button = event.button()
            # Focus on the current widget if valid
            try:
                cw = self._parent.currentWidget()
                if cw is not None:
                    cw.setFocus()
                    # Show in file-tree
                    self._parent._filetree_navigate_to(cw)
            except:
                traceback.print_exc()

        def mouseMoveEvent(self, event):
            super().mouseMoveEvent(event)
            # Set the tooltip
            pos = self.mapFromGlobal(qt.QCursor.pos())
            index = self.tabAt(pos)
            if index != -1:
                current_tab = self._parent.widget(index)

    class TabMenu(
        purefunctions.import_module("gui.templates.basemenu").BaseMenu
    ):
        """Custom menu that appears when right clicking a tab."""

        def __init__(
            self, parent, main_form, tab_widget, editor_widget, cursor_position
        ):
            # Nested function for creating a move or copy action
            def create_move_copy_action(
                action_name, window_name, move=True, focus_name=None
            ):
                window = main_form.get_window_by_name(window_name)
                action = qt.QAction(action_name, self)
                if move == True:
                    func = window.drag_tab_in
                    action_func = functools.partial(
                        func,
                        tab_widget,
                        parent.tabAt(cursor_position),
                    )
                    icon = iconfunctions.get_qicon(
                        "icons/gen/window_tab_move.png"
                    )
                else:
                    func = window.copy_editor_in
                    action_func = functools.partial(
                        func,
                        tab_widget,
                        parent.tabAt(cursor_position),
                        focus_name,
                    )
                    icon = iconfunctions.get_qicon(
                        "icons/gen/window_tab_copy.png"
                    )
                action.setIcon(icon)
                action.triggered.connect(action_func)
                return action

            # Nested function for creating text difference actions
            def create_diff_action(
                action_name, main_form, compare_tab_1, compare_tab_2
            ):
                def difference_function(
                    main_form, compare_tab_1, compare_tab_2
                ):
                    # Check for text documents in both tabs
                    if (
                        isinstance(
                            compare_tab_1,
                            purefunctions.import_module(
                                "gui.forms.customeditor"
                            ).CustomEditor,
                        )
                        == False
                        and isinstance(
                            compare_tab_1,
                            purefunctions.import_module(
                                "gui.forms.plaineditor"
                            ).PlainEditor,
                        )
                        == False
                    ):
                        main_form.display.display_message_with_type(
                            "First tab is not a text document!",
                            message_type=data.MessageType.ERROR,
                        )
                        return
                    elif (
                        isinstance(
                            compare_tab_2,
                            purefunctions.import_module(
                                "gui.forms.customeditor"
                            ).CustomEditor,
                        )
                        == False
                        and isinstance(
                            compare_tab_2,
                            purefunctions.import_module(
                                "gui.forms.plaineditor"
                            ).PlainEditor,
                        )
                        == False
                    ):
                        main_form.display.display_message_with_type(
                            "Second tab is not a text document!",
                            message_type=data.MessageType.ERROR,
                        )
                        return
                    # Initialize the compare parameters
                    text_1 = compare_tab_1.text()
                    text_1_name = compare_tab_1.name
                    text_2 = compare_tab_2.text()
                    text_2_name = compare_tab_2.name
                    # Display the text difference
                    main_form.display.show_text_difference(
                        text_1, text_2, text_1_name, text_2_name
                    )

                diff_action = qt.QAction(action_name, self)
                if "main" in action_name.lower():
                    diff_action.setIcon(
                        iconfunctions.get_qicon(
                            "icons/menu_edit/compare_text.png"
                        )
                    )
                elif "upper" in action_name.lower():
                    diff_action.setIcon(
                        iconfunctions.get_qicon(
                            "icons/menu_edit/compare_text.png"
                        )
                    )
                else:
                    diff_action.setIcon(
                        iconfunctions.get_qicon(
                            "icons/menu_edit/compare_text.png"
                        )
                    )
                function = functools.partial(
                    difference_function, main_form, compare_tab_1, compare_tab_2
                )
                diff_action.triggered.connect(function)
                return diff_action

            # Nested function for checking is the basic widgets current tab is an editor
            def check_for_editor(tab_widget):
                current_tab = tab_widget.currentWidget()
                if (
                    isinstance(
                        current_tab,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                    or isinstance(
                        current_tab,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                ):
                    return True
                else:
                    return False

            # Initialize the superclass
            super().__init__(parent)
            # Change the basic widget name to lowercase
            tab_widget_name = tab_widget.name.lower()
            # Add actions according to the parent TabWidget
            # Move actions
            move_to_main = create_move_copy_action(
                "Move to main window", "main"
            )
            move_to_upper = create_move_copy_action(
                "Move to upper window", "upper"
            )
            move_to_lower = create_move_copy_action(
                "Move to lower window", "lower"
            )
            # Copy action
            copy_to_main = create_move_copy_action(
                "Copy to main window", "main", move=False, focus_name="main"
            )
            copy_to_upper = create_move_copy_action(
                "Copy to upper window", "upper", move=False, focus_name="upper"
            )
            copy_to_lower = create_move_copy_action(
                "Copy to lower window", "lower", move=False, focus_name="lower"
            )
            # Clear REPL MESSAGES tab action
            clear_repl_action = qt.QAction("Clear messages", self)
            clear_repl_action.setIcon(
                iconfunctions.get_qicon("icons/gen/clean.png")
            )
            clear_repl_action.triggered.connect(
                main_form.display.repl_clear_tab
            )
            # Text difference actions
            diff_main_action = create_diff_action(
                "Text diff to main window",
                main_form,
                main_form.main_window.currentWidget(),
                editor_widget,
            )
            diff_upper_action = create_diff_action(
                "Text diff to upper window",
                main_form,
                main_form.upper_window.currentWidget(),
                editor_widget,
            )
            diff_lower_action = create_diff_action(
                "Text diff to lower window",
                main_form,
                main_form.lower_window.currentWidget(),
                editor_widget,
            )
            # Update current working directory action
            if hasattr(editor_widget, "save_name") == True:
                # Nested function for updating the current working directory
                def update_cwd(*args) -> None:
                    # Get the document path
                    path = os.path.dirname(editor_widget.save_name)
                    # Check if the path is not an empty string
                    if path == "":
                        message = "Document path is not valid!"
                        main_form.display.display_message_with_type(
                            message, message_type=data.MessageType.WARNING
                        )
                        return
                    main_form.set_cwd(path)

                #                update_cwd_action = qt.QAction("Update CWD", self)
                #                update_cwd_action.setIcon(
                #                    iconfunctions.get_qicon(f'icons/folder/open/refresh.png')
                #                )
                #                update_cwd_action.triggered.connect(update_cwd)
                #                self.addAction(update_cwd_action)
                #                self.addSeparator()

                # Navigate to Filetree location
                def navigate_to(*args) -> None:
                    data.filetree.goto_path(editor_widget.save_name)
                    return

                navigate_to_action = qt.QAction("Navigate to", self)
                navigate_to_action.setIcon(
                    iconfunctions.get_qicon("icons/gen/tree_navigate.png")
                )
                navigate_to_action.triggered.connect(navigate_to)
                self.addAction(navigate_to_action)
                self.addSeparator()
            # Add the 'copy file name to clipboard' action
            clipboard_copy_action = qt.QAction("Copy name to clipboard", self)

            def clipboard_copy(*args) -> None:
                cb = data.application.clipboard()
                cb.clear(mode=cb.Clipboard)
                cb.setText(editor_widget.name, mode=cb.Clipboard)
                return

            clipboard_copy_action.setIcon(
                iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
            )
            clipboard_copy_action.triggered.connect(clipboard_copy)
            self.addAction(clipboard_copy_action)
            self.addSeparator()

            # Nested function for adding diff actions
            def add_diff_actions():
                # Diff to main window
                if (
                    check_for_editor(main_form.main_window) == True
                    and editor_widget != main_form.main_window.currentWidget()
                ):
                    self.addAction(diff_main_action)
                # Diff to upper window
                if (
                    check_for_editor(main_form.upper_window) == True
                    and editor_widget != main_form.upper_window.currentWidget()
                ):
                    self.addAction(diff_upper_action)
                # Diff to lower window
                if (
                    check_for_editor(main_form.lower_window) == True
                    and editor_widget != main_form.lower_window.currentWidget()
                ):
                    self.addAction(diff_lower_action)

            # Check which basic widget is the parent to the clicked tab
            if "main" in tab_widget_name:
                # Add the actions to the menu
                self.addAction(move_to_upper)
                self.addAction(move_to_lower)
                self.addSeparator()
                # Check the tab widget type
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                ):
                    # Copy functions are only available to custom editors
                    self.addAction(copy_to_upper)
                    self.addAction(copy_to_lower)
                elif (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                    and editor_widget.name == "REPL MESSAGES"
                ):
                    # REPL MESSAGES tab clear option
                    self.addAction(clear_repl_action)
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                    or isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                ):
                    # Diff functions for plain and custom editors
                    self.addSeparator()
                    add_diff_actions()
            elif "upper" in tab_widget_name:
                # Add the actions to the menu
                self.addAction(move_to_main)
                self.addAction(move_to_lower)
                self.addSeparator()
                # Check the tab widget type
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                ):
                    # Copy functions are only available to custom editors
                    self.addAction(copy_to_main)
                    self.addAction(copy_to_lower)
                elif (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                    and editor_widget.name == "REPL MESSAGES"
                ):
                    # REPL MESSAGES tab clear option
                    self.addAction(clear_repl_action)
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                    or isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                ):
                    # Diff functions for plain and custom editors
                    self.addSeparator()
                    add_diff_actions()
            elif "lower" in tab_widget_name:
                # Add the actions to the menu
                self.addAction(move_to_main)
                self.addAction(move_to_upper)
                self.addSeparator()
                # Check the tab widget type
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                ):
                    # Copy functions are only available to custom editors
                    self.addAction(copy_to_main)
                    self.addAction(copy_to_upper)
                elif (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                    and editor_widget.name == "REPL MESSAGES"
                ):
                    # REPL MESSAGES tab clear option
                    self.addAction(clear_repl_action)
                if (
                    isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.customeditor"
                        ).CustomEditor,
                    )
                    == True
                    or isinstance(
                        editor_widget,
                        purefunctions.import_module(
                            "gui.forms.plaineditor"
                        ).PlainEditor,
                    )
                    == True
                ):
                    # Diff functions for plain and custom editors
                    self.addSeparator()
                    add_diff_actions()

    # Class variables
    # Name of the basic widget
    name = ""
    # Reference to the last file that was drag&dropped onto the main  form
    drag_dropped_file = None
    # QMainWindow
    main_form = None
    box = None
    # Custom tab bar
    custom_tab_bar = None
    # Default font for textboxes
    default_editor_font = qt.QFont(data.current_font_name, 10)
    # Default font and icon size for the tab bar
    default_tab_font = None
    default_icon_size = None
    # Attribute for indicating if the REPL is indicated
    indicated = False
    # Tab-bar stuff
    move_range = None
    drag_lock = None
    drag_event_data = None
    # Corner widget cache
    corner_widget_cache = None

    def __init__(self, parent, main_form, box):
        """Initialization."""
        # Initialize superclass, from which the current class is inherited,
        # THIS MUST BE DONE SO THAT THE SUPERCLASS EXECUTES ITS __init__ !!!!!!
        super().__init__(parent)
        # Properties for stylesheets
        self.setProperty("indicated", False)
        self.setProperty("notabs", True)
        # Set various events and attributes
        # Save references
        self.main_form = main_form
        self.box = box
        # Set font
        self.setFont(data.get_general_font())
        # Initialize the custom tab bar
        self.custom_tab_bar = self.CustomTabBar(self, main_form)
        self.setTabBar(self.custom_tab_bar)
        # Install tab-bar's event filter
        self.tabBar().installEventFilter(self)
        self.drag_lock = False
        # Enable drag&drop events
        self.setAcceptDrops(True)
        # Add close buttons to tabs
        self.setTabsClosable(False)
        # Set tabs as movable, so that you can move tabs with the mouse
        self.setMovable(True)
        # Add signal for coling a tab to the EVT_tabCloseRequested function
        self.tabCloseRequested.connect(self.__signal_tabclose)
        # Connect signal that fires when the tab index changes
        self.currentChanged.connect(self.__signal_tabindex_change)
        # Set the tabs to never shrink in width
        self.setElideMode(qt.Qt.TextElideMode.ElideNone)
        # Store the default settings
        self.default_tab_font = self.tabBar().font()
        self.default_icon_size = self.tabBar().iconSize()
        # Reset indication
        self.indication_reset()
        # Manual side scrollers
        self.tab_scrollers_init()
        qt.QTimer.singleShot(10, self.close_button_reposition)
        # Set the properties
        for k, v in data.filelocations.items():
            self.setProperty(v, False)
        # Initialize corner widget storage and groupbox
        self.init_corner_groupbox()
        # Update style
        self.update_style()

    def init_corner_groupbox(self):
        self.corner_widget_cache = {}
        self.corner_groupbox = purefunctions.import_module(
            "gui.templates.widgetgenerator"
        ).create_borderless_groupbox(
            name="CornerGroupbox",
            parent=self,
        )
        layout: qt.QHBoxLayout = cast(
            qt.QHBoxLayout,
            purefunctions.import_module(
                "gui.templates.widgetgenerator"
            ).create_layout(vertical=False),
        )
        self.corner_groupbox.setLayout(layout)

        def update_style(*args):
            for i in range(self.corner_groupbox.layout().count()):
                w = self.corner_groupbox.layout().itemAt(i).widget()
                if hasattr(w, "update_style"):
                    w.update_style()

        self.corner_groupbox.update_style = update_style
        self.setCornerWidget(self.corner_groupbox, qt.Qt.Corner.TopRightCorner)

    def tab_scrollers_init(self):
        # Left
        def scroll_left(*args):
            current = self.currentIndex()
            if current > 0:
                self.setCurrentIndex(current - 1)

        self.scroller_left = purefunctions.import_module(
            "gui.templates.widgetgenerator"
        ).create_groupbox_with_layout(
            parent=self,
            vertical=False,
            borderless=True,
            spacing=0,
            margins=(0, 0, 0, 0),
        )
        tb_1 = qt.QPushButton(self)
        tb_1.setObjectName("TabScrollLeft")
        tb_1.clicked.connect(scroll_left)
        self.scroller_left.layout().addWidget(tb_1)
        self.tb_1 = tb_1
        self.scroller_left.setVisible(False)

        # Right
        def scroll_right(*args):
            count = self.count()
            current = self.currentIndex()
            if current < (count - 1):
                self.setCurrentIndex(current + 1)

        self.scroller_right = purefunctions.import_module(
            "gui.templates.widgetgenerator"
        ).create_groupbox_with_layout(
            parent=self,
            vertical=False,
            borderless=True,
            spacing=0,
            margins=(0, 0, 0, 0),
        )
        tb_0 = qt.QPushButton(self)
        tb_0.setObjectName("TabScrollRight")
        tb_0.clicked.connect(scroll_right)
        self.scroller_right.layout().addWidget(tb_0)
        self.tb_0 = tb_0
        self.scroller_right.setVisible(False)

        # Down
        def show_tab_list(*args):
            if hasattr(self, "tab_list_menu"):
                self.tab_list_menu.setParent(None)
                self.tab_list_menu = None
            self.tab_list_menu = purefunctions.import_module(
                "gui.templates.basemenu"
            ).BaseMenu("TabListMenu", self)

            # Initialize the menu
            def set_index(index, *args):
                self.setCurrentIndex(index)

            for i in range(self.count()):
                new_item = qt.QAction(self.tabText(i), self.tab_list_menu)
                new_item.setIcon(self.tabIcon(i))
                new_item.triggered.connect(functools.partial(set_index, i))
                self.tab_list_menu.addAction(new_item)
            # Show the menu
            cursor = qt.QCursor.pos()
            self.tab_list_menu.popup(cursor)

        tb_down = qt.QPushButton(self)
        tb_down.setObjectName("TabScrollDown")
        tb_down.clicked.connect(show_tab_list)
        self.scroller_right.layout().addWidget(tb_down)
        self.tb_down = tb_down

        self.setCornerWidget(None, qt.Qt.Corner.TopRightCorner)
        self.setCornerWidget(None, qt.Qt.Corner.TopLeftCorner)

        self.tab_scrollers_rescale()

    def tab_scrollers_rescale(self):
        scale_factor = 1.00
        height = self.tabBar().height()
        if height < 16:
            height = 16
        used_height = height * scale_factor
        size = (int(used_height * 0.8), int(used_height))
        icon_size = (int(used_height / 1.7), int(used_height / 1.7))
        self.tb_1.setIconSize(qt.create_qsize(*icon_size))
        self.tb_0.setIconSize(qt.create_qsize(*icon_size))
        self.tb_down.setIconSize(qt.create_qsize(*icon_size))
        self.tb_1.setFixedSize(qt.create_qsize(*size))
        self.tb_0.setFixedSize(qt.create_qsize(*size))
        self.tb_down.setFixedSize(qt.create_qsize(*size))
        if hasattr(self, "corner_groupbox"):
            self.corner_groupbox.update_style()

    def tab_scrollers_show(self):
        if self.scroller_right.isVisible() == False:
            #            self.setCornerWidget(self.scroller_right, qt.Qt.Corner.TopRightCorner)
            self.corner_groupbox.layout().insertWidget(0, self.scroller_right)
            self.setCornerWidget(
                self.corner_groupbox, qt.Qt.Corner.TopRightCorner
            )
            self.corner_groupbox.setVisible(True)
            self.setCornerWidget(self.scroller_left, qt.Qt.Corner.TopLeftCorner)
            self.scroller_right.setVisible(True)
            self.scroller_left.setVisible(True)
            self.tab_scrollers_rescale()

    def tab_scrollers_hide(self):
        if self.scroller_right.isVisible() == True:
            #            self.setCornerWidget(None, qt.Qt.Corner.TopRightCorner)
            if self.corner_groupbox.layout().indexOf(self.scroller_right) != -1:
                self.corner_groupbox.layout().removeWidget(self.scroller_right)
            if self.corner_groupbox.layout().count() == 0:
                self.setCornerWidget(None, qt.Qt.Corner.TopRightCorner)
            else:
                self.corner_groupbox.setVisible(True)
            self.setCornerWidget(None, qt.Qt.Corner.TopLeftCorner)
            self.scroller_right.setVisible(False)
            self.scroller_left.setVisible(False)

    def add_corner_widget(self, name, widget):
        self.corner_widget_cache[name] = widget
        self.corner_groupbox.layout().addWidget(widget)

    def __init_drag_data(self, event=None):
        self.indexTab = self.currentIndex()
        self.tabRect = self.tabBar().tabRect(self.indexTab)
        self.pixmap = qt.QPixmap(self.tabRect.size())
        self.tabBar().render(self.pixmap, qt.QPoint(), qt.QRegion(self.tabRect))
        painter = qt.QPainter(self.pixmap)
        painter.setCompositionMode(
            painter.CompositionMode.CompositionMode_DestinationIn
        )
        painter.fillRect(self.pixmap.rect(), qt.QColor(0, 0, 0, 64))
        painter.end()

    def store_drag_data(self, event=None):
        TabWidget.drag_event_data = {
            "name": self.tabBar().tabText(self.currentIndex()),
            "index": self.currentIndex(),
        }

    def __start_tab_drag(self):
        index = self.currentIndex()
        if index != -1:
            mime_data = qt.QMimeData()
            #            mime_data.setText("{:s} {:d}".format(
            #                    self.name, index
            #                )
            #            )
            drag = qt.QDrag(self)
            drag.setMimeData(mime_data)
            drag.setPixmap(self.pixmap)
            drag.setHotSpot(
                qt.create_qpoint(
                    self.tabRect.width() / 2, self.tabRect.height() / 2
                )
            )
            drag.exec(qt.Qt.DropAction.CopyAction | qt.Qt.DropAction.MoveAction)
            drag.destroyed.connect(self.__drag_destroyed)

    def __drag_destroyed(self, *args):
        for i in (10, 0):
            mouse_event = qt.QMouseEvent(
                qt.QEvent.Type.MouseButtonRelease,
                qt.QPointF(i, i),
                qt.QPointF(i, i),
                qt.QPointF(i, i),
                qt.Qt.MouseButton.LeftButton,
                qt.Qt.MouseButton.LeftButton,
                qt.Qt.KeyboardModifier.NoModifier,
            )
            data.application.sendEvent(self.tabBar(), mouse_event)

    def _setmove_range(self):
        tabRect = self.tabBar().tabRect(self.currentIndex())
        pos = self.tabBar().mapFromGlobal(qt.QCursor.pos())
        self.move_range = pos.x() - tabRect.left(), tabRect.right() - pos.x()

    def eventFilter(self, source, event):
        #        def _mimic_mousemove_event():
        #            new_event = qt.QMouseEvent(
        #                qt.QEvent.Type.MouseMove,
        #                qt.QPointF(self.tabBar().width()/2, self.tabBar().height()/2),
        #                qt.Qt.MouseButton.NoButton,
        #                qt.Qt.MouseButton.NoButton,
        #                qt.Qt.KeyboardModifier.NoModifier,
        #            )
        #            qt.QCoreApplication.sendEvent(self.tabBar(), new_event)

        if source == self.tabBar():
            if (
                event.type() == qt.QEvent.Type.MouseButtonPress
                and event.buttons() == qt.Qt.MouseButton.LeftButton
            ):
                qt.QTimer.singleShot(0, self._setmove_range)
            elif event.type() == qt.QEvent.Type.MouseButtonRelease:
                self.move_range = None
            elif (
                event.type() == qt.QEvent.Type.MouseMove
                and self.move_range is not None
            ):
                pos = event.pos()
                if self.tabBar().rect().contains(pos):
                    self.drag_lock = False
                else:
                    buttons = data.application.mouseButtons()
                    if buttons == qt.Qt.MouseButton.LeftButton:
                        if self.drag_lock == False:
                            if hasattr(
                                self.main_form.display, "docking_overlay_show"
                            ):
                                self.drag_lock = True
                                self.main_form.display.docking_overlay_show()
                                self.__init_drag_data(event)
                                self.__start_tab_drag()
                    else:
                        self.drag_lock = False

                if pos.x() < self.move_range[0]:
                    return True
                elif pos.x() > self.tabBar().width() - self.move_range[1]:
                    return True
        return qt.QTabWidget.eventFilter(self, source, event)

    def dragEnterEvent(self, event):
        """Qt Drag event that fires when you click and drag something onto the
        basic widget."""
        if TabWidget.drag_event_data is not None:
            name = TabWidget.drag_event_data["name"]
            index = TabWidget.drag_event_data["index"]
            TabWidget.drag_event_data["source"] = event.source()

    def dropEvent(self, event):
        """Qt Drop event."""
        # Skip drops to System popup tabs
        try:
            if event.source().objectName() == self.objectName():
                event.ignore()
                if hasattr(self.main_form.display, "docking_overlay_hide"):
                    self.main_form.display.docking_overlay_hide()
                return

            if self.drag_dropped_file is not None:
                # Open file in a new scintilla tab
                self.main_form.open_file(self.drag_dropped_file, self)
                event.accept()
            elif TabWidget.drag_event_data is not None:
                # Drag&drop widget event occured
                name = TabWidget.drag_event_data["name"]
                index = TabWidget.drag_event_data["index"]
                source = TabWidget.drag_event_data["source"]
                self.drag_tab_in(source, index)
                event.accept()
                TabWidget.drag_event_data = None
            # Reset the drag&drop data attributes
            self.drag_dropped_file = None
            self.drag_text = None
        except Exception as ex:
            if hasattr(self.main_form.display, "display_error"):
                self.main_form.display.display_error(traceback.format_exc())
            event.ignore()
        # Hide the docking overlay
        if hasattr(self.main_form.display, "docking_overlay_hide"):
            self.main_form.display.docking_overlay_hide()

    def tabs(self):
        for i in range(self.count()):
            yield self.widget(i)

    def customize_tab_bar(self, update_style=True):
        tabbar = self.tabBar()
        if update_style:
            tabbar.update_style()
        if (
            data.get_toplevel_menu_pixelsize() is not None
            and data.get_global_font_family() is not None
        ):
            tabbar.setFont(data.get_toplevel_font())
            new_icon_size = qt.create_qsize(
                int(data.get_custom_tab_pixelsize()),
                int(data.get_custom_tab_pixelsize()),  # @Kristof
            )
            if new_icon_size != tabbar.iconSize():
                self.setIconSize(new_icon_size)
        else:
            tabbar.setFont(self.default_tab_font)
            self.setIconSize(self.default_icon_size)

    def update_style(self):
        if qt.sip.isdeleted(self):
            return
        self.customize_tab_bar()
        tab_bar = self.tabBar()
        if isinstance(tab_bar, TabWidget.CustomTabBar):
            self.tabBar().scale_tab_buttons()
        cw = self.cornerWidget()
        if cw is not None and hasattr(cw, "update_style"):
            cw.update_style()
        # Close button
        if hasattr(self, "close_button"):
            self.close_button.update_style(
                "icons/tab/close_white.png",
                "icons/tab/close_white_press.png",
                "icons/tab/close_white_hover.png",
                "icons/tab/close_white_hover.png",
                "icons/tab/close_white.png",
                "icons/tab/close.png",
                "icons/tab/close_press.png",
                "icons/tab/close_hover.png",
                "icons/tab/close_hover.png",
                "icons/tab/close.png",
                qt.create_qsize(
                    data.get_custom_tab_pixelsize() * 2,
                    data.get_custom_tab_pixelsize() * 2,
                ),
            )

        # Async scroller style update
        def scroller_update(*args):
            self.tab_scrollers_rescale()

        qt.QTimer.singleShot(10, scroller_update)

    #    def event(self, event):
    #        # Execute the superclass event method
    #        super().event(event)
    #        # Indicate that the event was processed by returning True
    #        return True

    def _style_pane(self):
        w = self.currentWidget()
        # Widget is not an editor
        if not isinstance(
            w,
            purefunctions.import_module("gui.forms.customeditor").CustomEditor,
        ):
            current_type_enum = data.FileType.Standard
        else:
            current_type_enum = functions.get_file_status(w.save_name)

        index = "other"
        inverse_index = "current"
        if self.indicated == True:
            index = "current"
            inverse_index = "other"

        for k, v in data.filelocations.items():
            if k == current_type_enum:
                self.setProperty(f"{v}-{index}", True)
            #                print(f"{p}-{index}")
            else:
                self.setProperty(f"{v}-{index}", False)

        for k, v in data.filelocations.items():
            self.setProperty(f"{v}-{inverse_index}", False)

    def setCurrentIndex(self, index: int):
        super().setCurrentIndex(index)
        self.tabBar().changeEvent(qt.QEvent(qt.QEvent.Type.FontChange))
        # Set symbol analysis
        if hasattr(self.currentWidget(), "set_symbol_analysis"):
            self.currentWidget().set_symbol_analysis()

    def enterEvent(self, enter_event):
        """Event that fires when the focus shifts to the TabWidget."""
        super().enterEvent(enter_event)
        cw = self.currentWidget()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # Set focus to the clicked basic widget
        self.setFocus()
        # Set Save/SaveAs buttons in the menubar
        self._set_save_status()
        # Store the last focused widget to the parent
        self.main_form.last_focused_widget = self
        # Hide the function wheel if it is shown
        if hasattr(self.main_form.view, "hide_all_overlay_widgets"):
            self.main_form.view.hide_all_overlay_widgets()
        # Reset the click&drag context menu action
        purefunctions.import_module(
            "components"
        ).actionfilter.ActionFilter.clear_action()

    def wheelEvent(self, wheel_event):
        """QScintilla mouse wheel rotate event."""
        key_modifiers = qt.QApplication.keyboardModifiers()
        delta = wheel_event.angleDelta().y()
        if delta < 0:
            if key_modifiers == qt.Qt.KeyboardModifier.ControlModifier:
                # Zoom out the scintilla tab view
                self.zoom_out()
        else:
            if key_modifiers == qt.Qt.KeyboardModifier.ControlModifier:
                # Zoom in the scintilla tab view
                self.zoom_in()
        # Handle the event
        if key_modifiers == qt.Qt.KeyboardModifier.ControlModifier:
            # Accept the event, the event will not be propageted(sent forward) to the parent
            wheel_event.accept()
        else:
            # Propagate(send forward) the wheel event to the parent
            wheel_event.ignore()

    def resizeEvent(self, event):
        """Resize basic widget event."""
        # First execute the superclass resize event function
        super().resizeEvent(event)
        event.setAccepted(False)
        # Reposition the close button if needed
        self.close_button_reposition()

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()

    def tabInserted(self, index):
        super().tabInserted(index)
        current_tab = self.currentWidget()
        if isinstance(
            current_tab,
            purefunctions.import_module("gui.forms.customeditor").CustomEditor,
        ):
            current_tab.set_symbol_analysis()

    def __signal_tabindex_change(self, new_index):
        """Signal when the tab index changes."""
        # Set Save/SaveAs buttons in the menubar
        self._set_save_status()
        # Check if there is a tab in the tab widget
        current_tab = self.currentWidget()
        # Update the icons of the tabs
        for i in range(self.count()):
            self.update_tab_icon(self.widget(i))
        # Show the close button
        self.check_close_button()
        # Update everything
        self.customize_tab_bar(update_style=False)
        self._check_tabcount()
        # Refresh tab buttons
        index = new_index
        if index != -1:
            self.tabBar().refresh_tab_buttons(index)
        # Save the layout
        if hasattr(self.main_form.view, "layout_save"):
            self.main_form.view.layout_save()
        # Add file for symbol analysis
        qt.QTimer.singleShot(0, self.__check_editor)
        # Update statusbar
        if hasattr(current_tab, "display_widget_statusbar_status"):
            current_tab.display_widget_statusbar_status()

        # Check for Filetree update
        self._filetree_navigate_to(current_tab)

        self.store_drag_data()

        if not self.isVisible():
            self.fix_rendering_issues()

    def fix_rendering_issues(self) -> None:
        """!!!

        This is a workaround for fixing the rendering of the tab-bar's tabs on
        first loading of a layout. Tabs to the left of the selected tab do not
        get rendered until the current active tab is changed. !!!
        """
        self.show()
        self.tabBar().show()

    def _filetree_navigate_to(self, current_tab, focus_filetree=False):
        if self.indicated and hasattr(current_tab, "save_name"):
            save_name = current_tab.save_name
            data.signal_dispatcher.file_tree_goto_path.emit(save_name, False)

    def __check_editor(self):
        current_tab = self.currentWidget()
        if isinstance(
            current_tab,
            purefunctions.import_module("gui.forms.customeditor").CustomEditor,
        ):
            current_tab.set_symbol_analysis()

    def check_close_button(self):
        if (
            data.application_type == data.ApplicationType.Project
            and len(self.main_form.get_all_windows()) > 1
        ):
            # Show the close button
            if self.count() == 0:
                self.close_button_show()
                self.close_button_reposition()
            else:
                self.close_button_hide()
        else:
            self.close_button_hide()

    __indicated_cache = False
    __count_cache = 0

    def _check_tabcount(self):
        update_needed = False
        if self.indicated and self.__indicated_cache != self.indicated:
            self.setProperty("indicated", True)
            self.tabBar().setProperty("indicated", True)
            update_needed = True
            self.__indicated_cache = self.indicated
        elif not self.indicated and self.__indicated_cache != self.indicated:
            self.setProperty("indicated", False)
            self.setProperty("notabs", False)
            self.tabBar().setProperty("indicated", False)
            update_needed = True
            self.__indicated_cache = self.indicated
        if self.count() == 0 and self.__count_cache != self.count():
            self.setProperty("notabs", True)
            update_needed = True
            self.__count_cache = self.count()
        elif self.count() != 0 and self.__count_cache != self.count():
            self.setProperty("notabs", False)
            update_needed = True
            self.__count_cache = self.count()

        if update_needed:
            self._style_pane()
            self.repolish()

    def __signal_tabclose(self, emmited_tab_number):
        """Event that fires when a tab closes."""

        # Nested function for clearing all bookmarks in the document
        def clear_document_bookmarks():
            # Check if bookmarks need to be cleared
            if isinstance(
                self.widget(emmited_tab_number),
                purefunctions.import_module(
                    "gui.forms.customeditor"
                ).CustomEditor,
            ):
                self.main_form.bookmarks.remove_editor_all(
                    self.widget(emmited_tab_number)
                )

        # Store the tab reference
        tab: TabWidget = self.widget(emmited_tab_number)
        # Check if the document is modified
        if hasattr(tab, "savable") and tab.savable == data.CanSave.YES:
            if tab.save_status == data.FileStatus.MODIFIED:
                # Display the close notification
                close_message = "Document '" + self.tabText(emmited_tab_number)
                close_message += "' has been modified!\nClose it anyway?"
                # Declare the function for closing a tab
                reply = purefunctions.import_module(
                    "gui.dialogs.popupdialog"
                ).PopupDialog.question(close_message, parent=self.main_form)
                if reply == qt.QMessageBox.StandardButton.Yes:
                    clear_document_bookmarks()
                    # Close tab anyway
                    self.removeTab(emmited_tab_number)
                else:
                    # Cancel tab closing
                    return
            else:
                clear_document_bookmarks()
                # The document is unmodified
                self.removeTab(emmited_tab_number)
        else:
            clear_document_bookmarks()
            # The document cannot be saved, close it
            self.removeTab(emmited_tab_number)
        # Delete the tab from memory
        if hasattr(tab, "self_destruct"):
            skip_classes = [
                purefunctions.import_module("gui.forms.newfiletree").NewFiletree
            ]
            if tab.__class__ not in skip_classes:
                tab.self_destruct()
        # Just in case, decrement the refcount of the tab (that's what del does)
        del tab
        # Save the layout
        if hasattr(self.main_form.view, "layout_save"):
            self.main_form.view.layout_save()
        self._check_tabcount()

    def _signal_editor_cursor_change(
        self, cursor_line=None, cursor_column=None
    ):
        """Signal that fires when cursor position changes."""
        pass

    def _set_save_status(self):
        """Enable/disable save/saveas buttons in the menubar."""
        cw = self.currentWidget()
        if cw is not None:
            #            #Check if the current widget is a custom editor or a QTextEdit widget
            #            if hasattr(cw, "name"):
            #                if isinstance(cw, purefunctions.import_module("gui.forms.customeditor").CustomEditor):
            #                    #Get currently selected tab in the basic widget and display its name and lexer
            #                    if hasattr(self.main_form.display, "write_to_statusbar"):
            #                        self.main_form.display.write_to_statusbar(cw.name)
            #                else:
            #                    #Display only the QTextEdit name
            #                    if hasattr(self.main_form.display, "write_to_statusbar"):
            #                        self.main_form.display.write_to_statusbar(cw.name)
            # Set the Save/SaveAs status of the menubar
            if hasattr(self.main_form, "savable"):
                if cw.savable == data.CanSave.YES:
                    self.main_form.set_save_file_state(True)
                else:
                    self.main_form.set_save_file_state(False)
        if self.count() == 0 and hasattr(self.main_form, "savable"):
            self.main_form.set_save_file_state(False)

    def _signal_text_changed(self, editor):
        """Signal that is emmited when the document text changes."""
        # Check if the current widget is valid
        if editor is None:
            return
        # Update the save status of the current widget
        if editor.savable == data.CanSave.YES:
            # Set document as modified
            editor.save_status = data.FileStatus.MODIFIED
            # Get editor's tab index
            editor_index = self.indexOf(editor)
            # Check if special character is already in the name of the tab
            if not "*" in self.tabText(editor_index):
                # Add the special character to the tab name
                self.setTabText(
                    editor_index, "*" + self.tabText(editor_index) + "*"
                )
            # Fire global text change signal
            data.signal_dispatcher.editor_state_changed.emit(
                self.currentIndex(), self, "edited"
            )
        # Update margin width
        self.editor_update_margin()

    def reset_text_changed(self, index=None, widget=None):
        """Reset the changed status of the current widget (remove the * symbols
        from the tab name)"""
        if widget is not None:
            index = self.indexOf(widget)
        # Update the save status of the current widget
        if index is None:
            if self.currentWidget().savable == data.CanSave.YES:
                self.currentWidget().save_status = data.FileStatus.OK
                self.setTabText(
                    self.currentIndex(),
                    self.tabText(self.currentIndex()).strip("*"),
                )
                data.signal_dispatcher.editor_state_changed.emit(
                    self.currentIndex(), self, "saved"
                )
        else:
            if self.widget(index).savable == data.CanSave.YES:
                self.widget(index).save_status = data.FileStatus.OK
                self.setTabText(index, self.tabText(index).strip("*"))
                data.signal_dispatcher.editor_state_changed.emit(
                    self.currentIndex(), self, "saved"
                )

    def close_tab(self, tab=None):
        """Close a tab in the basic widget."""
        # Return if there are no tabs open
        if self.count == 0:
            return

        def closable_check(widget):
            #            if (isinstance(widget, _filetree_.Filetree) == True or
            #                isinstance(widget, purefunctions.import_module("gui.forms.messagewindow").MessageWindow) == True or
            #                isinstance(widget, purefunctions.import_module("gui.helpers.diagnosticwindow").DiagnosticWindow) == True or
            #                isinstance(widget, _dashboard_.Dashboard) == True):
            #                    return False
            return True

        try:
            # First check if a tab name was given
            if isinstance(tab, str):
                for i in range(0, self.count()):
                    if self.tabText(i) == tab:
                        # Skip if it's a non-closable widget
                        widget = self.widget(i)
                        if not closable_check(widget):
                            return
                        # Tab found, close it
                        self.__signal_tabclose(i)
                        break
            elif isinstance(tab, int):
                # Skip if it's a non-closable widget
                widget = self.widget(tab)
                if not closable_check(widget):
                    return
                # Close the tab
                self.__signal_tabclose(tab)
            elif tab is None:
                # Skip if it's a non-closable widget
                widget = self.widget(self.currentIndex())
                if not closable_check(widget):
                    return
                # No tab number given, select the current tab for closing
                self.__signal_tabclose(self.currentIndex())
            else:
                for i in range(0, self.count()):
                    # Close tab by reference
                    if self.widget(i) == tab:
                        # Skip if it's a non-closable widget
                        widget = self.widget(i)
                        if not closable_check(widget):
                            return
                        # Tab found, close it
                        self.__signal_tabclose(i)
                        break
        except Exception as ex:
            traceback.print_exc()

    def close_all(self):
        for t in self.tabs():
            self.close_tab(t)

    def remove_from_box(self):
        if (
            data.application_type == data.ApplicationType.Project
            and len(self.main_form.get_all_windows()) > 1
        ):
            main_form = self.main_form
            self.hide()
            self.setParent(None)
            # Repeat deletion for removal of newly emptied boxed
            for b in main_form.get_all_boxes():
                if b.is_empty() and b.objectName() != "Main":
                    b.hide()
                    b.setParent(None)
            # Reindex all tab widgets
            main_form.view.reindex_all_windows()
        else:
            self.close_button_hide()

    def close_button_show(self):
        if not hasattr(self, "close_overlay"):
            close_button = purefunctions.import_module(
                "gui.helpers.buttons"
            ).TabButton(
                "close",
                # Selected
                "icons/tab/close_white.png",
                "icons/tab/close_white_press.png",
                "icons/tab/close_white_hover.png",
                "icons/tab/close_white_hover.png",
                "icons/tab/close_white.png",
                # Not selected
                "icons/tab/close.png",
                "icons/tab/close_press.png",
                "icons/tab/close_hover.png",
                "icons/tab/close_hover.png",
                "icons/tab/close.png",
                self.remove_from_box,
                qt.create_qsize(
                    data.get_custom_tab_pixelsize() * 2,
                    data.get_custom_tab_pixelsize() * 2,
                ),
                parent=self,
                border=True,
            )
            self.close_overlay = purefunctions.import_module(
                "gui.templates.widgetgenerator"
            ).create_borderless_groupbox(self)
            self.close_overlay.setAlignment(
                qt.Qt.AlignmentFlag.AlignRight
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            self.close_overlay.setLayout(qt.QHBoxLayout())
            self.close_overlay.layout().addWidget(close_button)
            self.close_overlay.layout().setAlignment(
                qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignTop
            )
            self.close_overlay.setParent(self)
            self.close_button = close_button
        self.close_overlay.show()
        self.close_button_reposition()

    def close_button_hide(self):
        if hasattr(self, "close_overlay"):
            self.close_overlay.hide()

    def close_button_reposition(self):
        if hasattr(self, "close_overlay"):
            if self.close_overlay.isVisible():
                self.close_overlay.resize(self.size())

    def zoom_in(self):
        """Zoom in view function (it is the same for the
        purefunctions.import_module("gui.forms.customeditor").CustomEditor and
        QTextEdit)"""
        # Zoom in
        try:
            self.currentWidget().zoomIn()
        except:
            pass
        # Update the margin width
        self.editor_update_margin()

    def zoom_out(self):
        """Zoom out view function (it is the same for the
        purefunctions.import_module("gui.forms.customeditor").CustomEditor and
        QTextEdit)"""
        # Zoom out
        try:
            self.currentWidget().zoomOut()
        except:
            pass
        # Update the margin width
        self.editor_update_margin()

    def zoom_reset(self):
        """Reset the zoom to default."""
        # Check is the widget is a scintilla custom editor
        if isinstance(
            self.currentWidget(),
            purefunctions.import_module("gui.forms.customeditor").CustomEditor,
        ):
            # Reset zoom
            self.currentWidget().zoomTo(0)
            # Update the margin width
            self.editor_update_margin()
        elif isinstance(self.currentWidget(), qt.QTextEdit):
            # Reset zoom
            self.currentWidget().setFont(self.default_editor_font)

    def repolish(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.tabBar().repolish()
        #        self.repaint()
        self.update()

    def indication_set(self):
        self.setProperty("indicated", True)
        tab_bar = self.tabBar()
        tab_bar.setProperty("indicated", True)
        self.indicated = True
        self._style_pane()
        self.repolish()

        # Check for Filetree update
        self._filetree_navigate_to(self.currentWidget())

    def indication_reset(self):
        self.setProperty("indicated", False)
        tab_bar = self.tabBar()
        tab_bar.setProperty("indicated", False)
        self.indicated = False
        self._style_pane()
        self.repolish()

    def plain_create_document(self, name):
        """Create a plain vanilla scintilla document."""
        # Initialize the custom editor
        new_scintilla_tab = purefunctions.import_module(
            "gui.forms.plaineditor"
        ).PlainEditor(self, self.main_form)
        # Add attributes for status of the document (!!you can add attributes to objects that have the __dict__ attribute!!)
        new_scintilla_tab.name = name
        # Initialize the scrollbars
        new_scintilla_tab.SendScintilla(
            qt.QsciScintillaBase.SCI_SETVSCROLLBAR, True
        )
        new_scintilla_tab.SendScintilla(
            qt.QsciScintillaBase.SCI_SETHSCROLLBAR, True
        )
        # Hide the margin
        new_scintilla_tab.hide_all_margins()
        # Disable drops
        new_scintilla_tab.setAcceptDrops(False)
        # Add needed signals
        new_scintilla_tab.cursorPositionChanged.connect(
            self._signal_editor_cursor_change
        )

        # Customize the mouse click event for the plain document with a decorator
        def custom_mouse_click(function_to_decorate):
            def decorated_function(*args, **kwargs):
                function_to_decorate(*args, **kwargs)
                # Set Save/SaveAs buttons in the menubar
                self._set_save_status()

            return decorated_function

        # Add the custom click decorator to the mouse click function
        new_scintilla_tab.mousePressEvent = custom_mouse_click(
            new_scintilla_tab.mousePressEvent
        )
        # Return the scintilla reference
        return new_scintilla_tab

    def plain_add_document(self, document_name) -> qt.QWidget:
        """Add a plain scintilla document to self(QTabWidget)"""
        # Create new scintilla object
        new_editor_tab = self.plain_create_document(document_name)
        # Add the scintilla document to the tab widget
        new_editor_tab_index = self.addTab(new_editor_tab, document_name)
        # Make new tab visible
        self.setCurrentIndex(new_editor_tab_index)
        # Return the reference to the new added scintilla tab widget
        return self.widget(new_editor_tab_index)

    def diagnostics_add(self, tab_name, diagnostics) -> qt.QWidget:
        new_diagnostics = purefunctions.import_module(
            "gui.helpers.diagnosticwindow"
        ).DiagnosticWindow(self, self.main_form, diagnostics)
        new_diagnostics_index = self.addTab(new_diagnostics, tab_name)
        self.setCurrentIndex(new_diagnostics_index)
        self.update_tabs(new_diagnostics_index)
        return self.widget(new_diagnostics_index)

    def symbols_add(self, tab_name, symbolhandler) -> qt.QWidget:
        new_symbols = purefunctions.import_module(
            "gui.helpers.symbolwindow"
        ).SymbolWindow(self, self.main_form, symbolhandler)
        new_symbols_index = self.addTab(new_symbols, tab_name)
        self.setCurrentIndex(new_symbols_index)
        self.update_tabs(new_symbols_index)
        return self.widget(new_symbols_index)

    def preferences_add(self, tab_name) -> qt.QWidget:
        new_preferences = purefunctions.import_module(
            "gui.forms.settingswindow"
        ).SettingsWindow(self, self.main_form)
        new_preferences_index = self.addTab(new_preferences, tab_name)
        self.setCurrentIndex(new_preferences_index)
        self.update_tabs(new_preferences_index)
        return self.widget(new_preferences_index)

    def debugger_add(self, tab_name) -> qt.QWidget:
        new_debugger = purefunctions.import_module(
            "debugger.debuggerwindow"
        ).DebuggerWindow(self, self.main_form)
        new_debugger_index = self.addTab(new_debugger, tab_name)
        self.setCurrentIndex(new_debugger_index)
        self.update_tabs(new_debugger_index)
        return self.widget(new_debugger_index)

    def pieces_add(self, tab_name: str, project_path: str) -> qt.QWidget:
        new_pieces = purefunctions.import_module(
            "pieces.pieceswindow"
        ).PiecesWindow(self, self.main_form, project_path)
        new_pieces_index = self.addTab(new_pieces, tab_name)
        self.setCurrentIndex(new_pieces_index)
        self.update_tabs(new_pieces_index)
        return self.widget(new_pieces_index)

    def new_dashboard_add(self, tab_name: str) -> qt.QWidget:
        # Create an empty `NewDashboard()`-instance and store it in
        # `data.new_dashboard`.
        data.new_dashboard = purefunctions.import_module(
            "new_dashboard.new_dashboard"
        ).NewDashboard(self, self.main_form)
        new_dashboard_index = self.addTab(data.new_dashboard, tab_name)
        self.setCurrentIndex(new_dashboard_index)
        self.update_tabs(new_dashboard_index)

        # Obtain the default dashboard data as a `DashboardData()`-instance and
        # store it in `data.dashboard_data`.
        data.dashboard_data = purefunctions.import_module(
            "new_dashboard.dashboard_data"
        ).restore_dashboard_data()
        # data.dashboard_data = purefunctions.import_module(
        #     "new_dashboard.dashboard_data"
        # ).get_default_dashboard_data()
        # purefunctions.import_module(
        #     "new_dashboard.dashboard_data"
        # ).store_dashboard_data(data.dashboard_data)

        # Let the widget display the data
        data.new_dashboard.set_dashboard_data(data.dashboard_data)

        # Return the widget
        return self.widget(new_dashboard_index)

    def chipconfigurator_add(
        self,
        tab_name: str,
        project_path: str,
        series_json_file: str,
        chip_name: str,
    ):
        new_chipconfigurator = purefunctions.import_module(
            "chipconfigurator.widgets"
        ).ChipConfiguratorWindow(
            parent=self,
            main_form=self.main_form,
            project_path=project_path,
        )
        new_chipconfigurator.load(
            series_json_file,
            chip_name,
        )
        new_chipconfigurator_index = self.addTab(new_chipconfigurator, tab_name)
        self.setCurrentIndex(new_chipconfigurator_index)
        self.update_tabs(new_chipconfigurator_index)
        return self.widget(new_chipconfigurator_index)

    def general_registers_add(self, tab_name):
        new_widget = purefunctions.import_module(
            "debugger.memoryviews"
        ).MemoryViewGeneralRegisters(self, self.main_form)
        new_widget_index = self.addTab(new_widget, tab_name)
        self.setCurrentIndex(new_widget_index)
        self.update_tabs(new_widget_index)
        return self.widget(new_widget_index)

    def memory_add(self, tab_name, typ):
        new_widget = purefunctions.import_module(
            "debugger.memoryviews"
        ).MemoryViewRawMemory(self, self.main_form, typ)
        new_widget_index = self.addTab(new_widget, tab_name)
        self.setCurrentIndex(new_widget_index)
        self.update_tabs(new_widget_index)
        return self.widget(new_widget_index)

    def variable_watch_add(self, tab_name):
        new_widget = purefunctions.import_module(
            "debugger.memoryviews"
        ).MemoryViewVariableWatch(self, self.main_form)
        new_widget_index = self.addTab(new_widget, tab_name)
        self.setCurrentIndex(new_widget_index)
        self.update_tabs(new_widget_index)
        return self.widget(new_widget_index)

    def messages_add(self, tab_name, existing_messages=None):
        if existing_messages is not None:
            new_messages = existing_messages
        else:
            new_messages = purefunctions.import_module(
                "gui.forms.messagewindow"
            ).MessageWindow(self, self.main_form)
        new_messages_index = self.addTab(new_messages, tab_name)
        self.setCurrentIndex(new_messages_index)
        return self.widget(new_messages_index)

    def console_add(
        self,
        tab_name,
        console_type: data.ConsoleType,
        cwd: Optional[str] = None,
    ):
        match console_type:
            case data.ConsoleType.Serial:
                module_serial_console = purefunctions.import_module(
                    "beetle_console.serial_console"
                )
                new_console = module_serial_console.SerialConsole(
                    parent=self,
                    main_form=self.main_form,
                    name=tab_name,
                )
            case data.ConsoleType.Make:
                module_make_console = purefunctions.import_module(
                    "beetle_console.make_console"
                )
                new_console = module_make_console.MakeConsole(
                    parent=self,
                    main_form=self.main_form,
                    name=tab_name,
                )
            case data.ConsoleType.Standard:
                # new_console = gui.templates.textmanipulation.ConsoleDisplay(
                #     parent=self,
                #     parent_window=None,
                # )
                new_console = gui.consoles.standardconsole.StandardConsole(
                    name=tab_name,
                    parent=self,
                    cwd=cwd,
                )
            case _:
                raise Exception(f"Unknown console type: {console_type}")
        new_console_index = self.addTab(new_console, tab_name)
        self.setCurrentIndex(new_console_index)
        self.update_tabs(new_console_index)
        return self.widget(new_console_index)

    def pinconfigurator_add(self, tab_name, project_path, chip_name):
        new_tab = purefunctions.import_module(
            "gui.forms.pinconfigurator"
        ).PinConfiguratorWindow(self, self.main_form, project_path, chip_name)
        new_tab_index = self.addTab(new_tab, tab_name)
        self.setCurrentIndex(new_tab_index)
        self.update_tabs(new_tab_index)
        return self.widget(new_tab_index)

    def editor_create_document(self, file_with_path=None):
        """Create and initialize a custom scintilla document."""
        # Initialize the custom editor
        new_scintilla_tab = purefunctions.import_module(
            "gui.forms.customeditor"
        ).CustomEditor(self, self.main_form, file_with_path)
        return new_scintilla_tab

    def editor_add_document(self, document_name, type=None, bypass_check=False):
        """Check tab type and add a document to self(QTabWidget)"""
        if type == "file":
            ## New tab is a file on disk
            file_type = "none"
            if bypass_check == False:
                file_type = functions.get_file_type(document_name)
            if file_type != "none" or bypass_check == True:
                # Test if file can be read
                result = functions.test_text_file(document_name)
                if result is None:
                    if hasattr(self.main_form.display, "display_warning"):
                        self.main_form.display.display_warning(
                            "Testing for TEXT file skipped!",
                        )
                    # File cannot be read
                    return None
                elif result != "non-text":
                    line_endings = functions.get_file_line_endings(
                        document_name
                    )
                    scintilla_line_endings = (
                        functions.get_file_scintilla_line_endings(document_name)
                    )
                    if line_endings != "\n":
                        if line_endings == "\r\n":
                            line_endings_string = "\\r\\n"
                        elif line_endings == "\r":
                            line_endings_string = "\\r"
                        else:
                            raise Exception(
                                "Unknown line endings in document: "
                                + document_name
                            )
                        if hasattr(self.main_form.display, "display_error"):
                            self.main_form.display.display_warning(
                                "File '{}' has '{}' line endings!".format(
                                    document_name, line_endings_string
                                )
                            )
                else:
                    # Non-text files
                    scintilla_line_endings = qt.QsciScintilla.EolMode.EolUnix
                # Create new scintilla document
                new_editor_tab = self.editor_create_document(document_name)

                new_editor_tab.setEolMode(scintilla_line_endings)

                # Set the lexer that colour codes the document
                new_editor_tab.choose_lexer(file_type)
                # Add the scintilla document to the tab widget
                new_editor_tab_index = self.addTab(
                    new_editor_tab, os.path.basename(document_name)
                )
                # Add the tab button
                self.update_tabs(new_editor_tab_index)
                # Make the new tab visible
                self.setCurrentIndex(new_editor_tab_index)
                # Return the reference to the new added scintilla tab widget
                return self.widget(new_editor_tab_index)
            else:
                if hasattr(self.main_form.display, "write_to_statusbar"):
                    self.main_form.display.write_to_statusbar(
                        "Document is not a text file, "
                        + "doesn't exist or has an unsupported format!",
                        1500,
                    )
                return None
        else:
            ## New tab is an empty tab
            # Create new scintilla object
            new_editor_tab = self.editor_create_document(document_name)
            # Add the scintilla document to the tab widget
            new_editor_tab_index = self.addTab(new_editor_tab, document_name)
            # Add the tab button
            self.update_tabs(new_editor_tab_index)
            # Make new tab visible
            self.setCurrentIndex(new_editor_tab_index)
            # Return the reference to the new added scintilla tab widget
            return self.widget(new_editor_tab_index)

    def tree_create_tab(self, tree_tab_name, tree_type=None):
        """Create and initialize a tree display widget."""
        # Initialize the custom editor
        if tree_type is not None:
            new_tree_tab = tree_type(self, self.main_form)
        else:
            new_tree_tab = purefunctions.import_module(
                "gui.helpers.treedisplay"
            ).TreeDisplay(self, self.main_form)
        # Add attributes for status of the document
        new_tree_tab.name = tree_tab_name
        new_tree_tab.savable = data.CanSave.NO
        # Return the reference to the new added tree tab widget
        return new_tree_tab

    def tree_add_tab(self, tree_tab_name, tree_type=None):
        """Create and initialize a tree display widget."""
        new_tree_tab = self.tree_create_tab(tree_tab_name, tree_type)
        # Add the tree tab to the tab widget
        new_tree_tab_index = self.addTab(new_tree_tab, tree_tab_name)
        # Return the reference to the new added tree tab widget
        return self.widget(new_tree_tab_index)

    def search_results_create_tab(self, new_search_results_tab_name):
        new_search_results_tab = purefunctions.import_module(
            "gui.helpers.searchresultswindow"
        ).SearchResultsWindow(self, self.main_form)
        # Add attributes for status of the document
        new_search_results_tab.name = new_search_results_tab_name
        new_search_results_tab.savable = data.CanSave.NO
        # Return the reference to the new added tree tab widget
        return new_search_results_tab

    def search_results_add_tab(self, new_search_results_tab_name):
        # Initialize the custom editor
        new_search_results_tab = self.search_results_create_tab(
            new_search_results_tab_name
        )
        # Add the tree tab to the tab widget
        new_search_results_tab_index = self.addTab(
            new_search_results_tab, new_search_results_tab_name
        )
        # Update style
        self.setCurrentIndex(new_search_results_tab_index)
        self.update_tabs(new_search_results_tab_index)
        # Return the reference to the new added tree tab widget
        return self.widget(new_search_results_tab_index)

    terminal_count = 0

    def terminal_add_tab(self):
        # Generate name
        tab_name = f"TERMINAL-{self.terminal_count}"
        self.terminal_count += 1
        # Create Widget
        new_terminal_tab = purefunctions.import_module(
            "gui.forms.terminal"
        ).Terminal(self, self.main_form)
        # Add attributes for status of the document
        new_terminal_tab.name = tab_name
        new_terminal_tab.savable = data.CanSave.NO
        # Add the tree tab to the tab widget
        new_terminal_tab_index = self.addTab(new_terminal_tab, tab_name)
        # Update style
        self.setCurrentIndex(new_terminal_tab_index)
        self.update_tabs(new_terminal_tab_index)
        # Return the reference to the new added tree tab widget
        return self.widget(new_terminal_tab_index)

    def filetree_create_tab(
        self, tree_tab_name, directory, project, excluded_directories
    ):
        """Create and initialize a tree display widget."""
        # Initialize the chassis
        new_tree = purefunctions.import_module(
            "gui.forms.newfiletree"
        ).NewFiletree(
            self,
            self.main_form,
            directory,
            excluded_directories,
        )
        # Return the reference to the new added tree tab widget
        return new_tree

    def filetree_add_tab(
        self, tree_tab_name, directory, project, excluded_directories
    ):
        """Create and initialize a tree display widget."""
        # Initialize the custom editor
        new_tree = self.filetree_create_tab(
            tree_tab_name, directory, project, excluded_directories
        )
        # Add the tree tab to the tab widget
        new_tree_tab_index = self.addTab(new_tree, tree_tab_name)
        # Return the reference to the new added tree tab widget
        return new_tree

    def dashboard_create_tab(self, project_tab_name):
        """Create and initialize a project display widget."""
        # Initialize the project display object
        try:
            module_dashboard = purefunctions.import_module(
                "dashboard.chassis.dashboard"
            )
            new_dashboard = module_dashboard.Dashboard(self.main_form, self)
            # Return the reference to the new added tree tab widget
            return new_dashboard
        except Exception as ex:
            self.main_form.display.display_error(traceback.format_exc())
            self.main_form.display.display_error("Failed creating Dashboard")

    def dashboard_add_tab(self, project_tab_name):
        """Create and initialize a project display widget."""
        # I nitialize the custom editor
        new_dashboard = self.dashboard_create_tab(project_tab_name)
        # Add the project tab to the tab widget
        new_project_tab_index = self.addTab(new_dashboard, project_tab_name)
        # Return the reference to the new added project tab widget
        return new_dashboard

    def source_analyzer_create_tab(self, source_analyzer_tab_name):
        """Create and initialize a source_analyzer display widget."""
        # Initialize the source_analyzer display object
        try:
            module_sa_tab = purefunctions.import_module("sa_tab.chassis.sa_tab")
            new_sa = module_sa_tab.SATab(self.main_form, self)
            # Return the reference to the new added tree tab widget
            return new_sa
        except Exception as ex:
            self.main_form.display.display_error(traceback.format_exc())
            self.main_form.display.display_error(
                "Failed creating Source Analyzer"
            )

    def source_analyzer_add_tab(self, source_analyzer_tab_name):
        new_source_analyzer = self.source_analyzer_create_tab(
            source_analyzer_tab_name
        )
        # Add the source_analyzer tab to the tab widget
        new_source_analyzer_tab_index = self.addTab(
            new_source_analyzer, source_analyzer_tab_name
        )
        # Return the reference to the new added source_analyzer tab widget
        return new_source_analyzer

    def editor_update_margin(self):
        """Update margin width according to the number of lines in the current
        document."""
        # Check is the widget is a scintilla custom editor
        if isinstance(
            self.currentWidget(),
            purefunctions.import_module("gui.forms.customeditor").CustomEditor,
        ):
            self.currentWidget().update_margin()

    def set_tab_name(self, tab, new_text):
        """Set the name of a tab by passing a reference to it."""
        # Cycle through all of the tabs
        for i in range(self.count()):
            if self.widget(i) == tab:
                # Set the new text of the tab
                self.setTabText(i, new_text)
                break

    def move_tab(self, direction=data.Direction.RIGHT):
        """Change the position of the current tab in the basic widget, according
        to the selected direction."""
        # Store the current index and widget
        current_index = self.currentIndex()
        # Check the move direction
        if direction == data.Direction.RIGHT:
            # Check if the widget is already at the far right
            if current_index < self.tabBar().count() - 1:
                new_index = current_index + 1
                self.tabBar().moveTab(current_index, new_index)
                # This hack is needed to correctly focus the moved tab
                self.setCurrentIndex(current_index)
                self.setCurrentIndex(new_index)
        else:
            # Check if the widget is already at the far left
            if current_index > 0:
                new_index = current_index - 1
                self.tabBar().moveTab(current_index, new_index)
                # This hack is needed to correctly focus the moved tab
                self.setCurrentIndex(current_index)
                self.setCurrentIndex(new_index)

    def update_tab_icon(self, tab):
        if (hasattr(tab, "current_icon") == True) and (
            tab.current_icon is not None
        ):
            self.setTabIcon(self.indexOf(tab), tab.current_icon)

    def update_tabs(self, index: int) -> None:
        if hasattr(self.widget(index), "get_rightclick_menu_function"):
            func = self.widget(index).get_rightclick_menu_function()
            if func is None:
                return

            self.tabBar().add_rightclick_menu_function(index, func)
            # A slight async delay is needed here
            self.tabBar().refresh_tab_buttons(index)
            self.customize_tab_bar()
        return

    def copy_editor_in(self, source_tab_widget, source_index, focus_name=None):
        """Copy another
        purefunctions.import_module("gui.forms.customeditor").CustomEditor
        widget into self."""
        # Create a new reference to the source custom editor
        source_widget = source_tab_widget.widget(source_index)
        # Check if the source tab is valid
        if source_widget is None:
            return
        # purefunctions.import_module("gui.forms.plaineditor").PlainEditor tabs should not be copied
        if (
            isinstance(
                source_widget,
                purefunctions.import_module(
                    "gui.forms.customeditor"
                ).CustomEditor,
            )
            == False
        ):
            if hasattr(self.main_form.display, "display_message_with_type"):
                self.main_form.display.display_message_with_type(
                    "Only custom editor tabs can be copied!",
                    message_type=data.MessageType.ERROR,
                )
            return
        # Check if the source file already exists in the target basic widget
        check_index = self.main_form.check_open_file(
            source_widget.save_name, self
        )
        if check_index is not None:
            # File is already open, focus it
            self.setCurrentIndex(check_index)
            return
        # Create a new editor document
        new_widget = self.editor_create_document(source_widget.save_name)
        # Add the copied custom editor to the target basic widget
        new_index = self.addTab(
            new_widget,
            source_tab_widget.tabIcon(source_index),
            source_tab_widget.tabText(source_index),
        )
        # Set focus to the copied widget
        self.setCurrentIndex(new_index)
        # Copy the source editor text and set the lexer accordigly
        source_widget.copy_self(new_widget)
        # Also reset the text change
        self.reset_text_changed(new_index)
        # Update the margin in the copied widget
        self.editor_update_margin()
        # Update tab buttons
        self.update_tabs(new_index)

    def drag_tab_in(self, source_tab_widget, source_index):
        """Drag another
        purefunctions.import_module("gui.forms.customeditor").CustomEditor
        widget into self without copying it."""
        dragged_widget = source_tab_widget.widget(source_index)
        dragged_widget_icon = source_tab_widget.tabIcon(source_index)
        dragged_widget_text = source_tab_widget.tabText(source_index)
        # Check if the source tab is valid
        if dragged_widget is None:
            return
        # purefunctions.import_module("gui.forms.plaineditor").PlainEditor tabs should not evaluate its name
        if (
            isinstance(
                dragged_widget,
                purefunctions.import_module(
                    "gui.forms.customeditor"
                ).CustomEditor,
            )
            == True
        ):
            # Check if the source file already exists
            # in the target basic widget
            check_index = self.main_form.check_open_file(
                dragged_widget.save_name, self
            )
            if check_index is not None:
                # File is already open, focus it
                self.setCurrentIndex(check_index)
                return
        # Move the custom editor widget from source to target
        source_tab_widget.removeTab(source_tab_widget.indexOf(dragged_widget))
        new_index = self.addTab(
            dragged_widget, dragged_widget_icon, dragged_widget_text
        )
        # Set focus to the copied widget
        self.setCurrentIndex(new_index)
        # Change the custom editor parent
        self.widget(new_index)._parent = self
        self.widget(new_index).icon_manipulator.update_tab_widget(self)
        # Update tab buttons
        self.update_tabs(new_index)

    def move_tab_in(self, moved_widget, moved_widget_icon, moved_widget_text):
        """Move another
        purefunctions.import_module("gui.forms.customeditor").CustomEditor
        widget into self without copying it."""
        # Check if the source tab is valid
        if moved_widget is None:
            return
        # purefunctions.import_module("gui.forms.plaineditor").PlainEditor tabs should not evaluate its name
        if (
            isinstance(
                moved_widget,
                purefunctions.import_module(
                    "gui.forms.customeditor"
                ).CustomEditor,
            )
            == True
        ):
            # Check if the source file already exists
            # in the target basic widget
            check_index = self.main_form.check_open_file(
                moved_widget.save_name, self
            )
            if check_index is not None:
                # File is already open, focus it
                self.setCurrentIndex(check_index)
                return
        # Move the custom editor widget in
        new_index = self.addTab(
            moved_widget, moved_widget_icon, moved_widget_text
        )
        # Set focus to the copied widget
        self.setCurrentIndex(new_index)
        # Change the custom editor parent
        self.widget(new_index)._parent = self
        self.widget(new_index).icon_manipulator.update_tab_widget(self)
        # Update tab buttons
        self.update_tabs(new_index)

    def get_tab_by_save_name(self, searched_save_name):
        for i in range(self.count()):
            if not hasattr(self.widget(i), "save_name"):
                continue
            if self.widget(i).save_name == searched_save_name:
                return self.widget(i)
        return None

    def get_tab_by_tab_text(self, searched_text):
        for i in range(self.count()):
            if self.tabText(i) == searched_text:
                return self.widget(i)
        return None
