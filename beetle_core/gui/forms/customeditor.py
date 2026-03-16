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

import os
import re
import traceback
import qt
import data
import purefunctions
import iconfunctions
import functions
import os_checker
import gui.templates.baseeditor
import gui.templates.basemenu
import gui.dialogs.popupdialog
import gui.helpers.various
import settings
import settings.constants
import lexers
import components.hotspots
import components.actionfilter
import components.linelist
import helpdocs.help_texts

from typing import *


class CustomEditor(gui.templates.baseeditor.BaseEditor):
    """QScintilla widget with added custom functions.

    COMMENT:
        Functions treat items as if the starting index is 1 instead of 0!
        It's a little confusing at first, but you will get the hang of it.
        This is done because scintilla displays line numbers from index 1.
    """

    # Signals
    controlPressed = qt.pyqtSignal()
    controlReleased = qt.pyqtSignal()
    focusLost = qt.pyqtSignal()
    symbolIndicate = qt.pyqtSignal(object, object)
    symbolClickIndicate = qt.pyqtSignal(object, object)
    mouseReleased = qt.pyqtSignal()
    autocompletion_signal = qt.pyqtSignal()

    # Class variables
    _save_name = ""
    save_status = data.FileStatus.OK
    embedded = False
    last_browsed_dir = ""
    # Current document type, initialized to text
    current_file_type = "TEXT"
    # Current tab icon
    current_icon = None
    icon_manipulator = None
    # Comment character/s that will be used in comment/uncomment functions
    comment_string = None
    # Oberon/Modula-2/CP have the begin('(*')/end('*)') commenting style,
    # set the attribute to signal this commenting style and the beginning
    # and end commenting string
    open_close_comment_style = False
    end_comment_string = None
    edit_callback_flag = True
    # Indicator enumerations
    HIGHLIGHT_INDICATOR = 0
    BACKGROUND_SELECTION_INDICATOR = 1
    FIND_INDICATOR = 2
    REPLACE_INDICATOR = 3
    SELECTION_INDICATOR = 4
    SYMBOL_INDICATOR = 6
    BLINK_INDICATOR = 7
    ERROR_INDICATOR = 8
    WARNING_INDICATOR = 9
    SYMBOL_UNDERLINE_INDICATOR = 10
    FLASH_LINE_INDICATOR = 11
    indicators = [
        HIGHLIGHT_INDICATOR,
        FIND_INDICATOR,
        REPLACE_INDICATOR,
        SYMBOL_INDICATOR,
        BLINK_INDICATOR,
        ERROR_INDICATOR,
        WARNING_INDICATOR,
        BACKGROUND_SELECTION_INDICATOR,
        SYMBOL_UNDERLINE_INDICATOR,
        FLASH_LINE_INDICATOR,
    ]
    # List that holds the line numbers, gets updated on every text change
    line_count = None
    # Reference to the custom context menu
    context_menu = None
    # Autocompletion state
    __autocompletion_enabled = False
    """Namespace references for grouping functionality."""
    hotspots = None
    bookmarks = None
    keyboard = None
    diagnostics_handler = None
    """
    Built-in and private functions
    """

    def self_destruct(self) -> None:
        """"""
        # Clean up references
        self._parent = None
        self.main_form = None
        # Disconnect signals
        try:
            self.cursorPositionChanged.disconnect()
        except TypeError as e:
            purefunctions.printc(
                "ERROR: Could not disconnect self.cursorPositionChanged",
                color="error",
            )
        try:
            self.marginClicked.disconnect()
        except TypeError as e:
            purefunctions.printc(
                "ERROR: Could not disconnect self.marginClicked",
                color="error",
            )
        try:
            self.linesChanged.disconnect()
        except TypeError as e:
            purefunctions.printc(
                "ERROR: Could not disconnect self.linesChanged",
                color="error",
            )
        # Clean up namespaces
        self.hotspots = None
        self.bookmarks.parent = None
        self.bookmarks = None
        self.keyboard.parent = None
        self.keyboard = None
        # Clean up special functions
        self.find = None
        self.save = None
        self.clear = None
        self.highlight = None
        # Clean up the corner widget
        self.current_icon = None
        self.icon_manipulator = None
        # Clear the lexer
        self.clear_lexer()
        # Clean up the context menu if necessary
        self.delete_context_menu()
        # Remove file checking
        if os.path.isfile(self._save_name):
            data.filechecker.checker_file_remove(self._save_name)
        # Disengage self from the parent and clean up self
        self.setParent(None)
        self.deleteLater()
        return

    def __init__(
        self, parent, main_form, file_with_path=None, enable_event_filter=True
    ):
        """Initialize the scintilla widget."""
        # Initialize superclass, from which the current class is inherited,
        # THIS MUST BE DONE SO THAT THE SUPERCLASS EXECUTES ITS __init__ !!!!!!
        super().__init__(parent, main_form)
        self.set_saveable(True)
        self.__init_edit_settings()
        self.__init_margins()
        # Reset the modified status of the document
        self.setModified(False)
        # Autoindentation enabled when using "Enter" to indent to the same level as the previous line
        self.setAutoIndent(True)
        # Set backspace to delete by tab widths
        self.setBackspaceUnindents(True)
        # Scintilla widget must not accept drag/drop events,
        # the cursor freezes if it does!!!
        self.setAcceptDrops(False)
        # Initialize background selection
        self.background_selection = None
        # Correct the file name if it is unspecified
        if file_with_path is None:
            file_with_path = ""
        # Add attributes for status of the document
        self._parent = parent
        self.main_form = main_form
        self.name = os.path.basename(file_with_path)
        # Set save name with path
        if os.path.dirname(file_with_path) != "":
            self.save_name = functions.unixify_path(file_with_path)
        else:
            self.save_name = ""
        # Set file type
        self.file_location = data.FileType.Standard
        if main_form.name == "Main Window":
            self.file_location = functions.get_file_status(self.save_name)
        # Last directory browsed by the "Open File" and other dialogs
        if self.save_name != "":
            # If save_name was valid, extract the directory of the save file
            self.last_browsed_dir = os.path.dirname(self.save_name)
        else:
            self.last_browsed_dir = self.save_name
        # Reset the file save status
        self.save_status = data.FileStatus.OK
        # Enable saving of the scintilla document
        self.savable = data.CanSave.YES
        # Initialize instance variables
        self._init_special_functions()
        # Add needed signals
        self.cursorPositionChanged.connect(
            self._parent._signal_editor_cursor_change
        )
        self.marginClicked.connect(self.__margin_clicked)
        self.linesChanged.connect(self.__lines_changed)
        self.selectionChanged.connect(self.__selection_changed)
        self.controlPressed.connect(self.main_form.view.editor_control_press)
        self.controlPressed.connect(self.control_pressed)
        self.controlReleased.connect(self.main_form.view.editor_control_release)
        self.controlReleased.connect(self.control_released)
        self.symbolIndicate.connect(self._highlight_symbol)
        self.symbolClickIndicate.connect(self._highlight_click_symbol)
        if hasattr(self.main_form, "projects"):
            self.cursorPositionChanged.connect(self.__cursor_position_changed)
        self.mouseReleased.connect(self.mouse_released)
        self.autocompletion_signal.connect(self.__autocompletion_execute)
        data.signal_dispatcher.source_analyzer.set_alternate_content.connect(
            self.__set_alternate_content
        )
        self.textChanged.connect(self.text_changed)
        self.SCN_ZOOM.connect(self.__zoom_changed)
        # Cursor counter
        self.cursor_counter = 0
        # Set the lexer to the default Plain Text
        self.choose_lexer("text")
        #        self.add_corner_buttons()
        # Setup the LineList object that will hold the custom editor text as a list of lines
        self.line_list = components.linelist.LineList(self, self.text())
        # Reset the selection anti-recursion lock
        self.selection_lock = False
        # Bookmark initialization
        self.__init_bookmark_marker()
        # Breakpoints initialization
        self.__init_debugging_markers()
        # Diagnostic marker initialization
        self._init_diagnostic_markers()
        # Store Source-analyzer reference
        self.__sai: (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator
        ) = purefunctions.import_module(
            "components.sourceanalyzerinterface"
        ).SourceAnalysisCommunicator()
        self.__sa = purefunctions.import_module("source_analyzer")
        # Set file kind
        if self.__sai.has_project():
            self.file_kind = self.__sai.get_file_kind(self.save_name)
        else:
            self.file_kind = self.__sa.FileKind.OTHER
        data.signal_dispatcher.source_analyzer.project_initialized.connect(
            self.__set_file_kind_callback
        )
        # Initialize the namespace references
        self.hotspots = components.hotspots.Hotspots()
        self.bookmarks = Bookmarks(self)
        self.keyboard = Keyboard(self)
        self.diagnostics_handler = DiagnosticsHandler(self)
        # Set the horizontal scrollbar to adjust to contents
        self.setScrollWidthTracking(True)
        # Make last line scrollable to the top
        self.SendScintilla(self.SCI_SETENDATLASTLINE, False)
        # Check file is read-only
        self.readonly_check()
        # Set settings that can be changed
        self.update_variable_settings()
        # Look and feel
        self.set_style()
        # Check diagnostics
        if hasattr(main_form, "update_editor_diagnostics"):
            qt.QTimer.singleShot(10, main_form.update_editor_diagnostics)
        if hasattr(main_form, "update_debugger_items"):
            qt.QTimer.singleShot(20, main_form.update_debugger_items)
        # Enable multiple cursors and multi-cursor typing
        self.SendScintilla(self.SCI_SETMULTIPLESELECTION, True)
        self.SendScintilla(self.SCI_SETADDITIONALSELECTIONTYPING, True)
        #        self.SendScintilla(self.SCI_SETCARETLINEVISIBLEALWAYS, True)
        #        self.SendScintilla(self.SCI_SETCARETPERIOD, 0)
        #        self.SendScintilla(self.SCI_SETCARETWIDTH, 10)
        # Debug functionality initialization
        self.update_debug_settings()

        # Add a custom event filter
        if enable_event_filter:
            self.installEventFilter(self)
        else:
            self.removeEventFilter(self)

        alternate_content = self.__sai.get_alternative_content(self.save_name)
        if alternate_content is not None:
            self.__set_alternate_content(self.save_name, alternate_content)

    def eventFilter(self, object, event):
        if event.type() == qt.QEvent.Type.ToolTip:
            mouse_cursor_position = event.pos()
            cursor_margin = self.__get_cursor_margin(mouse_cursor_position.x())
            if cursor_margin != -1:
                # Margin hovered

                # 'lineAt' does not return correct line when hovering on margin
                chpos = self.SendScintilla(
                    self.SCI_POSITIONFROMPOINT,
                    mouse_cursor_position.x(),
                    mouse_cursor_position.y(),
                )
                line = self.SendScintilla(self.SCI_LINEFROMPOSITION, chpos)

                # Check markers
                if cursor_margin == self.MARGINS["symbol"]:
                    marker_mask = self.markersAtLine(line)
                    if (
                        marker_mask & self.MARKERS["error"]["32-bit-mask"]
                    ) != 0:
                        self.__tooltip_manual_show(
                            "There is an 'error' in this line.\n"
                            + "Click the 'error' icon to show more details in the Diagnostics window."
                        )
                    if (
                        marker_mask & self.MARKERS["warning"]["32-bit-mask"]
                    ) != 0:
                        self.__tooltip_manual_show(
                            "There is a 'warning' in this line.\n"
                            + "Click the 'warning' icon to show more details in the Diagnostics window."
                        )
                elif cursor_margin == self.MARGINS["debug"]:
                    marker_mask = self.markersAtLine(line)
                    if (
                        marker_mask
                        & self.MARKERS["debugging-position"]["32-bit-mask"]
                    ) != 0:
                        self.__tooltip_manual_show(
                            "The debugger's current stack-frame position is in this line"
                        )

            else:
                # Check if debug hover is applicable
                debugger_window = self.main_form.projects.debugger_window
                if (
                    data.debugging_active is True
                    and debugger_window is not None
                ):
                    mouse_cursor_line = self.lineAt(mouse_cursor_position)
                    word_at = self.wordAtPoint(mouse_cursor_position)
                    if word_at.strip() != "":
                        closest_word_index = self.SendScintilla(
                            self.SCI_POSITIONFROMPOINTCLOSE,
                            mouse_cursor_position.x(),
                            mouse_cursor_position.y(),
                        )
                        entity = self.__sai.get_entity_data(
                            self.save_name, closest_word_index
                        )
                        if entity is not None:
                            debugger_window.debugger_symbol_value(
                                {
                                    "editor": self,
                                    "word": word_at,
                                }
                            )

        return super().eventFilter(object, event)

    def __set_alternate_content(self, file_abspath_or_obj, content):
        if file_abspath_or_obj == self.save_name:
            # The bellow part needs to be called as an event,
            # otherwise the content doesn't update.
            # Don't know why yet, this seems to be Windows specific.
            def set_content(*args):
                self.setText(content)
                self.setReadOnly(True)
                self._parent.reset_text_changed(widget=self)

            qt.QTimer.singleShot(0, set_content)

    def __set_file_kind_callback(self, *args, **kwargs):
        self.file_kind = self.__sai.get_file_kind(self.save_name)

    def variable_list_callback(self, payload, word):
        try:
            if "variables" in payload.keys():
                variables = payload["variables"]
                for v in variables:
                    if v["name"] == word:
                        text = "{}: {}".format(word, v["value"])
                        self.__tooltip_manual_show(text)
                        break
                else:
                    text = "'{}' is not in the stack variable list!".format(
                        word
                    )
                    self.__tooltip_manual_show(text)
        except:
            traceback.print_exc()

    def symbol_show_value_callback(self, word, value):
        try:
            text = "{}: {}".format(word, value)
            self.__tooltip_manual_show(text)
        except:
            traceback.print_exc()

    def __get_cursor_margin(self, x_position: int) -> int:
        """Get the margin under the cursor, -1 if no margin is under the
        cursor."""
        width = 0
        for margin in range(5):
            width += self.marginWidth(margin)
            if x_position <= width:
                return margin
        return -1

    def __tooltip_manual_show(
        self, text: str, point: Optional[qt.QPoint] = None
    ) -> None:
        if point is not None:
            position = point
        else:
            position = qt.QCursor.pos()
        qt.QToolTip.showText(position, text, self)

    def update_debug_settings(self) -> None:
        self.update_margin()

    def enable_edit_callbacks(self):
        if self.edit_callback_flag:
            self.edit_callback_flag = False
            self.SCN_MODIFIED.connect(self.__text_modified)
            self.SendScintilla(
                self.SCI_SETMODEVENTMASK,
                self.SC_MOD_INSERTTEXT | self.SC_MOD_DELETETEXT,
            )

    def readonly_check(self):
        readonly = False

        if data.current_project is not None:
            # Inside compiler tool-chain
            toolpath_segment = data.current_project.get_toolpath_seg()
            if toolpath_segment.check_if_in_compiler(self.save_name):
                readonly = True

            # Is a valid Filetree generated makefile
            if data.current_project.is_filetree_mk(self.save_name):
                readonly = True

        # Debugging active
        if data.debugging_active:
            readonly = True

        # Set the state
        self.setReadOnly(readonly)

    @property
    def save_name(self):
        return self._save_name

    @save_name.setter
    def save_name(self, new_value):
        if os.path.isfile(self._save_name):
            data.filechecker.checker_file_remove(self._save_name)
        self._save_name = new_value
        if os.path.isfile(new_value):
            data.filechecker.checker_file_add(self._save_name)

    MARGINS = {
        "line": 0,
        "symbol": 1,
        "fold": 2,
        "debug": 3,
    }

    def __init_margins(self):
        # Set the margin type (0 is by default line numbers, 1 is for non code folding symbols and 2 is for code folding)
        self.setMarginType(
            self.MARGINS["line"], qt.QsciScintilla.MarginType.NumberMargin
        )

        # Symbol
        self.setMarginType(
            self.MARGINS["symbol"], qt.QsciScintilla.MarginType.SymbolMargin
        )
        self.setMarginMarkerMask(
            self.MARGINS["symbol"],
            (
                self.MARKERS["bookmark"]["32-bit-mask"]
                | self.MARKERS["fatal"]["32-bit-mask"]
                | self.MARKERS["error"]["32-bit-mask"]
                | self.MARKERS["warning"]["32-bit-mask"]
                | self.MARKERS["debugging-breakpoint"]["32-bit-mask"]
            ),
        )

        # Debugging
        self.setMarginType(
            self.MARGINS["debug"], qt.QsciScintilla.MarginType.SymbolMargin
        )
        self.setMarginMarkerMask(
            self.MARGINS["debug"],
            self.MARKERS["debugging-position"]["32-bit-mask"],
        )

        # Make line and symbol margin sensitive to mouseclicks
        self.setMarginSensitivity(self.MARGINS["line"], True)
        self.setMarginSensitivity(self.MARGINS["symbol"], True)
        self.setMarginSensitivity(self.MARGINS["debug"], True)

    def __init_edit_settings(self):
        """These settings reset everytime Embeetle is restarted."""
        # Set encoding format to UTF-8 (Unicode)
        self.setUtf8(True)
        # Overwrite mode
        self.setOverwriteMode(settings.editor["overwrite_mode"])
        # Wrap-indent mode:
        #   - WrapIndentFixed: Wrapped sub-lines are indented by the amount set by setWrapVisualFlags().
        #   - WrapIndentSame: Wrapped sub-lines are indented by the same amount as the first sub-line.
        #   - WrapIndentIndented: Wrapped sub-lines are indented by the same amount as the first sub-line plus one more level of indentation.
        #   - WrapIndentDeeplyIndented: Wrapped sub-lines are indented by the same amount as the first sub-line plus two more level of indentation.
        self.setWrapIndentMode(qt.QsciScintilla.WrapIndentMode.WrapIndentFixed)
        # Edge mode:
        #   - EdgeNone: Long lines are not marked.
        #   - EdgeLine: A vertical line is drawn at the column set by setEdgeColumn(). This is recommended for monospace fonts.
        #   - EdgeBackground: The background color of characters after the column limit is changed to the color set by setEdgeColor(). This is recommended for proportional fonts.
        #   - EdgeMultipleLines: Multiple vertical lines are drawn at the columns defined by multiple calls to addEdgeColumn().
        self.setEdgeMode(qt.QsciScintilla.EdgeMode.EdgeNone)
        # Tab draw mode:
        #   - TabLongArrow: An arrow stretching to the tab stop.
        #   - TabStrikeOut: A horizontal line stretching to the tab stop.
        self.setTabDrawMode(qt.QsciScintilla.TabDrawMode.TabLongArrow)

    def update_variable_settings(self):
        """These are global settings that are saved every time a setting is
        changed."""
        # Autocompletion
        if not self.isReadOnly():
            self.set_autocompletion(settings.editor["autocompletion"])
        else:
            self.set_autocompletion(False)
        # Word wrap
        self.set_wordwrap(settings.editor["word_wrap"])
        # Set font family and size
        self.setFont(data.get_editor_font())
        # Set brace matching
        self.setBraceMatching(qt.QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(
            qt.QColor(settings.editor["brace_color"])
        )
        # Set tab space indentation width
        self.setTabWidth(settings.editor["tab_width"])
        # Set line endings to be Unix style ("\n")
        self.setEolMode(settings.editor["end_of_line_mode"])
        self.setEolMode(
            qt.QsciScintilla.EolMode(settings.editor["end_of_line_mode"])
        )
        # Set the initial zoom factor
        self.zoomTo(settings.editor["zoom_factor"])
        # Set cursor line visibility and color
        self.set_cursor_line_visibility(settings.editor["cursor_line_visible"])
        # Edge marker
        if settings.editor["edge_marker_visible"]:
            self.edge_marker_show()
        else:
            self.edge_marker_hide()
        # Tabs use spaces
        self.setIndentationsUseTabs(not settings.editor["tabs_use_spaces"])
        # Visibility of whitespace characters
        if settings.editor["whitespace_visible"]:
            self.setWhitespaceVisibility(
                qt.QsciScintilla.WhitespaceVisibility.WsVisible
            )
        else:
            self.setWhitespaceVisibility(
                qt.QsciScintilla.WhitespaceVisibility.WsInvisible
            )
        # Makefile special settings
        if isinstance(self.lexer(), lexers.Makefile):
            if settings.editor["makefile_uses_tabs"]:
                self.setIndentationsUseTabs(True)
            if settings.editor["makefile_whitespace_visible"]:
                self.setWhitespaceVisibility(
                    qt.QsciScintilla.WhitespaceVisibility.WsVisible
                )
        # Margin settings
        self.setMarginsFont(
            qt.QFont(
                data.editor_font_name,
                data.get_general_font_pointsize(),
                weight=qt.QFont.Weight.Bold,
            )
        )
        fm = qt.QFontMetrics(data.get_editor_font())
        br = fm.boundingRect("99")
        self.__init_bookmark_marker(br.size())
        self.__init_debugging_markers(br.size())
        self.update_margin()
        # Special markers
        self.markerDefine(
            qt.QsciScintillaBase.SC_MARK_BACKGROUND, self.FLASH_LINE_INDICATOR
        )
        self.setMarkerBackgroundColor(
            qt.QColor(data.theme["indication"]["error"]),
            self.FLASH_LINE_INDICATOR,
        )
        # Update style
        self.set_style()

    def __setattr__(self, name, value):
        """Special/magic method that is called everytime an attribute of the
        CustomEditor class is set."""
        # Filter out the line_list attribute
        if name == "line_list":
            # Check if the assigned object is NOT a LineList object
            if isinstance(value, components.linelist.LineList) == False:
                # Check the extend value type
                if isinstance(value, list) == False:
                    raise Exception(
                        "Reassignment value of line_list must be a list!"
                    )
                elif all(isinstance(item, str) for item in value) == False:
                    raise Exception("All value list items must be strings!")
                text = self.list_to_text(value)
                self.set_all_text(text)
                self.line_list.update_text_to_list(text)
                # Cancel the assignment
                return
        # Call the superclasses/original __setattr__() special method
        super().__setattr__(name, value)

    def _init_special_functions(self):
        """Initialize the methods for document manipulation."""
        # Set references to the special functions
        self.find = self.find_text
        self.save = self.save_document
        self.clear = self.clear_editor
        self.highlight = self.highlight_text

    MARKERS = {
        "bookmark": {
            "number": 1,
            "32-bit-mask": 0b00000000_00000010,
            "icon": "icons/menu_edit/bookmark.png",
        },
        "error": {
            "number": 2,
            "32-bit-mask": 0b00000000_00000100,
            "icon": "icons/dialog/fatal.png",
        },
        "warning": {
            "number": 3,
            "32-bit-mask": 0b00000000_00001000,
            "icon": "icons/dialog/warning.png",
        },
        "debugging-breakpoint": {
            "number": 4,
            "32-bit-mask": 0b00000000_00010000,
            "icon": "icons/dialog/stop_red.png",
        },
        "debugging-position": {
            "number": 5,
            "32-bit-mask": 0b00000000_00100000,
            "icon": "icons/arrow/arrow_red/arrow_right.png",
        },
        "fatal": {
            "number": 6,
            "32-bit-mask": 0b00000000_01000000,
            "icon": "icons/dialog/warning_red.svg",
        },
    }

    def __init_bookmark_marker(self, size=qt.create_qsize(16, 16)):
        """Initialize the marker for the bookmarks."""
        image_scale_size = size
        bookmark_image = iconfunctions.get_qpixmap(
            self.MARKERS["bookmark"]["icon"]
        )
        bookmark_image = bookmark_image.scaled(image_scale_size)
        self.bookmark_marker = self.markerDefine(
            bookmark_image, self.MARKERS["bookmark"]["number"]
        )

    def _init_diagnostic_markers(self, size=qt.create_qsize(16, 16)):
        image_scale_size = size
        markers = [
            (
                self.MARKERS["fatal"]["number"],
                "fatal",
                self.MARKERS["fatal"]["icon"],
            ),
            (
                self.MARKERS["error"]["number"],
                "error",
                self.MARKERS["error"]["icon"],
            ),
            (
                self.MARKERS["warning"]["number"],
                "warning",
                self.MARKERS["warning"]["icon"],
            ),
        ]
        for m in markers:
            number, name, image_path = m
            image = iconfunctions.get_qpixmap(image_path)
            image = image.scaled(image_scale_size)
            marker = self.markerDefine(image, number)
            setattr(self, f"{name}_marker", marker)

    def __init_debugging_markers(self, size=qt.create_qsize(16, 16)):
        """Initialize the marker for the breakpoints."""
        image_scale_size = size
        # Breakpoint
        breakpoint_image = iconfunctions.get_qpixmap(
            self.MARKERS["debugging-breakpoint"]["icon"]
        )
        breakpoint_image = breakpoint_image.scaled(image_scale_size)
        self.debugging_breakpoint_marker = self.markerDefine(
            breakpoint_image, self.MARKERS["debugging-breakpoint"]["number"]
        )
        # Current position
        position_image = iconfunctions.get_qpixmap(
            self.MARKERS["debugging-position"]["icon"]
        )
        position_image = position_image.scaled(image_scale_size)
        self.debugging_position_marker = self.markerDefine(
            position_image, self.MARKERS["debugging-position"]["number"]
        )

    def is_valid_file(self):
        return os.path.isfile(self.save_name)

    def __margin_clicked(self, margin, line, state):
        """Signal for a mouseclick on the margin."""
        if isinstance(self.main_form, gui.helpers.various.DiffDialog):
            return
        # Check if there is a non-bookmark marker already present
        marker_mask = self.markersAtLine(line)
        if (
            (marker_mask & self.MARKERS["error"]["32-bit-mask"]) != 0
            or (marker_mask & self.MARKERS["warning"]["32-bit-mask"]) != 0
            or (marker_mask & self.MARKERS["fatal"]["32-bit-mask"]) != 0
        ):
            # Diagnostic marker is present here
            diagnostic = self.diagnostics_handler.get_diagnostic_at_line(line)
            tab_widget = self.main_form.projects.diagnostics_window._parent
            tab_widget.setCurrentWidget(
                self.main_form.projects.diagnostics_window
            )
            self.main_form.projects.diagnostics_window.highlight(diagnostic)
        #        elif marker_mask == 0b0 or (marker_mask & self.MARKERS["bookmark"]["32-bit-mask"]) != 0:
        #            # Adjust line index to the line list indexing (1..lines)
        #            adjusted_line = line + 1
        #            # Add/remove bookmark
        #            self.bookmarks.toggle_at_line(adjusted_line)

        if data.debugging_active:
            scintilla_line = line
            debugger_line = line + 1
            if (
                marker_mask
                & self.MARKERS["debugging-breakpoint"]["32-bit-mask"]
                != 0
            ):
                breakpoint_number = None
                for (
                    k,
                    v,
                ) in CustomEditor.debugger_marker_cache_breakpoint.items():
                    if v["line"] == line and v["editor"] == self:
                        breakpoint_number = v["number"]
                        break
                if breakpoint_number is None:
                    print("Error finding breakpoint!")
                    return
                data.signal_dispatcher.debug_breakpoint_delete.emit(
                    self.save_name,
                    debugger_line,
                    scintilla_line,
                    breakpoint_number,
                )
                print("BREAKPOINT-DELETED")
            else:
                data.signal_dispatcher.debug_breakpoint_insert.emit(
                    self.save_name, debugger_line, scintilla_line
                )
                print("BREAKPOINT-INSERTED")

    def __lines_changed(self):
        """Signal that fires when the number of lines changes."""
        bookmarks = self.main_form.bookmarks.marks
        for i in bookmarks:
            if bookmarks[i]["editor"] == self:
                line = self.markerLine(bookmarks[i]["handle"]) + 1
                bookmarks[i]["line"] = line

    selection_lock = False

    def __selection_changed(self) -> None:
        """Signal that fires when selected text changes."""
        # This function seems to be asynchronous so a lock
        # is required in order to prevent recursive access to
        # Python's objects
        try:
            if not self.selection_lock:
                self.selection_lock = True
                selected_text = self.selectedText()
                self.clear_selection_highlights()
                if selected_text.isidentifier():
                    self.__highlight_selection(
                        highlight_text=selected_text,
                        case_sensitive=False,
                        regular_expression=True,
                    )
                self.selection_lock = False
        except:
            self.selection_lock = False
        return

    def __cursor_position_changed(self, line, index):
        self.update_statusbar_status()

        #        buttons = data.application.mouseButtons()
        selection = self.getSelection()

        if selection != (-1, -1, -1, -1):
            return
        elif not self.__sai.is_engine_on():
            return
        elif not self.__sai.is_engine_on() and self.__sai.has_project():
            return
        elif not self.is_valid_file():
            return
        elif self.main_form.projects is None:
            return
        elif self.main_form.projects.symbols_window is None:
            return
        # Symbol
        position = self.positionFromLineIndex(line, index)
        try:
            reference = self.__sai.get_reference(self.save_name, position)
            symbol = self.__sai.get_entity_from_reference(reference)
            self.main_form.projects.symbols_window.show_symbol_details(
                symbol=symbol
            )
        except:
            traceback.print_exc()

    def __text_modified(
        self,
        position,
        modificationType,
        text,
        length,
        added,
        line,
        foldLevelNow,
        foldLevelPrev,
        token,
        annotationLinesAdded,
    ):
        if (not self.__sai.has_project()) or (length < 1):
            return
        elif not self.is_valid_file():
            return

        # Set file kind
        if (
            self.file_kind != self.__sa.FileKind.OBJECT
            and self.file_kind != self.__sa.FileKind.ARCHIVE
        ):
            path = self.save_name
            begin_offset = position
            end_offset = position + length
            new_content = text.decode("utf-8")
            if (modificationType & self.SC_MOD_INSERTTEXT) != 0:
                end_offset = begin_offset
            elif (modificationType & self.SC_MOD_DELETETEXT) != 0:
                new_content = ""
            self.__sai.edit_file(path, begin_offset, end_offset, new_content)
            data.signal_dispatcher.file_edited.emit(self._save_name)

    def get_rightclick_menu_function(self):
        def show_menu():
            # Main menu
            menu = gui.templates.basemenu.BaseMenu(self.main_form)

            # General functions
            general_actions = self.__create_general_actions()
            for _type, action in general_actions:
                if _type == "menu":
                    menu.addMenu(action)
                elif _type == "action":
                    menu.addAction(action)
                else:
                    raise Exception("Unknown type: {}".format(_type))

            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        return show_menu

    def add_corner_buttons(self):
        def show_lexer_menu():
            def set_lexer(lexer, lexer_name):
                try:
                    # Initialize and set the new lexer
                    lexer_instance = lexer()
                    self.set_lexer(lexer_instance, lexer_name)
                    # Change the corner widget (button) icon
                    self.icon_manipulator.update_corner_button_icon(
                        self.current_icon
                    )
                    self.icon_manipulator.update_icon(self)
                    # Display the lexer change
                    message = "Lexer changed to: {}".format(lexer_name)
                    self.main_form.display.display_message(message)
                except Exception as ex:
                    print(ex)
                    message = "Error with lexer selection!\n"
                    message += (
                        "Select a window widget with an opened document first."
                    )
                    self.main_form.display.display_error(message)
                    self.main_form.display.write_to_statusbar(message)

            lexers_menu = self.main_form.display.create_lexers_menu(
                "Change lexer", set_lexer
            )
            cursor = qt.QCursor.pos()
            lexers_menu.popup(cursor)
            if data.get_toplevel_menu_pixelsize() is not None:
                lexers_menu.update_style()

        # Edit session
        self.icon_manipulator.add_corner_button(
            self.current_icon, "Change the current lexer", show_lexer_menu
        )

    """
    Qt QSciScintilla functions
    """

    def keyPressEvent(self, event):
        """QScintila keyPressEvent, to catch which key was pressed."""
        # Hide the context menu if it is shown
        if self.context_menu is not None:
            self.delete_context_menu()
        # Filter out TAB and SHIFT+TAB key combinations to override
        # the default indent/unindent functionality
        key = event.key()
        #        char = event.text()
        key_modifiers = qt.QApplication.keyboardModifiers()

        # Autocompletion
        if self.__autocompletion_enabled:
            if (
                settings.editor["autocompletion_type"]
                == settings.constants.AutocompletionType.Automatic
            ):
                key_skip_list = (
                    qt.Qt.Key.Key_Return,
                    qt.Qt.Key.Key_Enter,
                    qt.Qt.Key.Key_Tab,
                    qt.Qt.Key.Key_Backspace,
                    qt.Qt.Key.Key_Space,
                    qt.Qt.Key.Key_Shift,
                    qt.Qt.Key.Key_Meta,
                    qt.Qt.Key.Key_Control,
                )
                if key not in key_skip_list:
                    self.autocompletion_signal.emit()

            elif (
                settings.editor["autocompletion_type"]
                == settings.constants.AutocompletionType.Tab
            ):
                line, index = self.getCursorPosition()
                line_text = self.text(line)
                if key == qt.Qt.Key.Key_Tab and line_text[:index].strip() != "":
                    # Autocompletion
                    line_number, index = self.getCursorPosition()
                    if (
                        self.text(line_number)[index - 1] not in (" ", "\n")
                        and not self.isListActive()
                    ):
                        self.autocompletion_signal.emit()
                        return
            else:
                if (
                    key == qt.Qt.Key.Key_Space
                    and key_modifiers == qt.Qt.KeyboardModifier.ControlModifier
                ):
                    # Autocompletion
                    line_number, index = self.getCursorPosition()
                    if (
                        self.text(line_number)[index - 1] not in (" ", "\n")
                        and not self.isListActive()
                    ):
                        self.autocompletion_signal.emit()
                        return

        #        elif key == qt.Qt.Key.Key_Backtab:
        #            self.custom_unindent()

        if key == qt.Qt.Key.Key_Control:
            self.controlPressed.emit()
        else:
            # Execute the superclass method first, the same trick as in __init__ !
            super().keyPressEvent(event)
        # Execute custom keyboard shortcuts
        key_combination = qt.QKeyCombination(
            event.modifiers(), qt.Qt.Key(event.key())
        )
        cmp_shortcut = str(qt.QKeySequence(key_combination).toString())
        cmp_shortcut = cmp_shortcut.lower()
        for sc, func in self.keyboard.custom_shortcuts.items():
            if sc.lower() == cmp_shortcut:
                func()
        # Blink statusbar data when file is read-only
        try:
            if not isinstance(self.main_form, gui.helpers.various.DiffDialog):
                if self.isReadOnly():
                    self.readonly_blink()
                    self.show_readonly_warning()
        except:
            pass

    def readonly_blink(self, *args):
        if not hasattr(self, "__readonly_blink_timer"):
            self.__readonly_blink_timer = qt.QTimer(self)
            self.__readonly_blink_timer.setInterval(100)
            self.__readonly_blink_timer.setSingleShot(True)
            self.__readonly_blink_timer.timeout.connect(self.__readonly_blink)
        else:
            self.__readonly_blink_timer.stop()
        self.__readonly_blink_counter = 10
        self.__readonly_blink_flag = True
        self.__readonly_blink_timer.start()

    def __readonly_blink(self, *args):
        if self.__readonly_blink_counter > 0:
            self.__readonly_blink_counter -= 1
            self.__readonly_blink_flag = not self.__readonly_blink_flag
            self.update_statusbar_status(self.__readonly_blink_flag)
            self.__readonly_blink_timer.start()
        else:
            self.update_statusbar_status()

    def show_readonly_warning(self, *args):
        line, index = self.getCursorPosition()
        x = self.SendScintilla(
            qt.QsciScintilla.SCI_POINTXFROMPOSITION,
            0,
            self.positionFromLineIndex(line, index),
        )
        y = self.SendScintilla(
            qt.QsciScintilla.SCI_POINTYFROMPOSITION,
            0,
            self.positionFromLineIndex(line, index),
        )
        point = self.mapToGlobal(qt.QPoint(x, y))
        if data.debugging_active:
            text = (
                "The document is in readonly mode because\n"
                + "debugging is active!"
            )
        else:
            text = (
                "The document is in readonly mode because\n"
                + "this is a special non-editable file!"
            )
        self.__tooltip_manual_show(text, point=point)

    def keyReleaseEvent(self, event):
        """QScintila KeyReleaseEvent, to catch which key was released."""
        # Execute the superclass method first, the same trick as in __init__ !
        super().keyReleaseEvent(event)
        # Catch speacial key presses
        key = event.key()
        #        key_text = event.text()
        key_modifiers = qt.QApplication.keyboardModifiers()
        if key == qt.Qt.Key.Key_Control:
            self.controlReleased.emit()
        elif key == qt.Qt.Key.Key_Escape:
            # Hide the symbol popup
            main_form = self.main_form
            if hasattr(main_form, "symbol_popup"):
                if main_form.symbol_popup is not None:
                    main_form.symbol_popup.hide()

    def mousePressEvent(self, event):
        """Overloaded mouse click event."""
        # Execute the superclass method first, the same trick as in __init__ !
        super().mousePressEvent(event)
        # Set focus to the clicked editor
        self.setFocus()
        # Set Save/SaveAs buttons in the menubar
        self._parent._set_save_status()
        # Set the last focused widget to the parent basic widget
        self.main_form.last_focused_widget = self.parent
        # Hide the function wheel if it is shown
        self.main_form.view.hide_all_overlay_widgets()

        try:
            if hasattr(self.main_form.view, "indicate_window"):
                module = purefunctions.import_module("gui.forms.tabwidget")
                parent = self.parent()
                for i in range(10):
                    if isinstance(parent, module.TabWidget):
                        if not parent.indicated:
                            self.main_form.view.indicate_window(parent)
                        break
                    else:
                        parent = parent.parent()
        except:
            traceback.print_exc()

        # Update statusbar details for the editor
        self.update_statusbar_status()

        # Hide the context menu if it is shown
        if self.context_menu is not None:
            self.delete_context_menu()
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()
        # Hide the symbol popup
        if hasattr(self.main_form, "symbol_popup"):
            if not qt.sip.isdeleted(self.main_form.symbol_popup):
                self.main_form.symbol_popup.hide()
        # Clear the background selection indicator
        self.clear_background_selection()
        # Add file for symbol analysis
        self.set_symbol_analysis()
        # Highlight file in filtree
        data.signal_dispatcher.file_tree_goto_path.emit(self.save_name, False)

    def set_symbol_analysis(self):
        module = purefunctions.import_module("gui.forms.tabwidget")
        if not isinstance(self._parent, module.TabWidget):
            return

        if not hasattr(CustomEditor, "analysis_cache"):
            CustomEditor.analysis_cache = []
        path = self.save_name
        if not os.path.isfile(path):
            return

        if path in CustomEditor.analysis_cache:
            return

        symbol_handler = self.__sai.get_symbolhandler()
        if symbol_handler is not None:
            for p in CustomEditor.analysis_cache:
                self.__sai.get_symbolhandler().stop_analysis(p)
            CustomEditor.analysis_cache = []
            CustomEditor.analysis_cache.append(path)
            symbol_handler.start_analysis(path)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.main_form.mouseReleaseEvent(event)
        self.mouseReleased.emit()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        main_form = self.main_form
        if (
            hasattr(main_form, "symbol_popup")
            and main_form.symbol_popup is not None
            and main_form.symbol_popup.isVisible() == True
        ):
            return

        # Symbol highlighting
        if not self.__sai.is_engine_on():
            # Clang engine not running! Click&Jump can not work!#
            return
        elif event.buttons() != qt.Qt.MouseButton.NoButton:
            return

        position = self.get_index_from_cursor()
        if position is None:
            return
        elif not self.is_valid_file():
            return

        reference = self.__sai.get_reference(self.save_name, position)
        symbol = self.__sai.get_entity_from_reference(reference)
        self.clear_symbol_highlights()
        key_modifiers = qt.QApplication.keyboardModifiers()
        if symbol and (key_modifiers != qt.Qt.KeyboardModifier.ControlModifier):
            self.symbolIndicate.emit(symbol, reference)
        elif symbol and (
            key_modifiers == qt.Qt.KeyboardModifier.ControlModifier
        ):
            self.symbolClickIndicate.emit(symbol, reference)
        else:
            self.reset_cursor()

    @qt.pyqtSlot()
    def control_pressed(self, *args):
        functions.wiggle_cursor()

    @qt.pyqtSlot()
    def control_released(self, *args):
        functions.wiggle_cursor()
        self.reset_cursor()

    @qt.pyqtSlot()
    def mouse_released(self, *args):
        line, index = self.getCursorPosition()
        position = self.positionFromLineIndex(line, index)
        indicator_state_highlight = self.SendScintilla(
            self.SCI_INDICATORVALUEAT,
            self.__get_indicator_index("underline"),
            position,
        )
        if indicator_state_highlight > 0:
            self.clear_highlights()
            self.reset_cursor()
            self.click_and_jump()

    @qt.pyqtSlot(object, object)
    def _highlight_symbol(self, symbol, reference):
        self.set_indicator("symbol")
        index_info = (
            0,
            reference.begin_offset,
            0,
            reference.end_offset,
        )
        self.highlight_raw((index_info,))

    def _highlight_click_symbol(self, symbol, reference):
        self._highlight_symbol(symbol, reference)
        self.set_indicator("underline")
        index_info = (
            0,
            reference.begin_offset,
            0,
            reference.end_offset,
        )
        self.highlight_raw((index_info,))
        # Pointing hand cursor
        #        self.SendScintilla(qt.QsciScintilla.SCI_SETCURSOR, 8)
        if self.cursor_counter == 0:
            data.application.setOverrideCursor(
                qt.Qt.CursorShape.PointingHandCursor
            )
        else:
            data.application.changeOverrideCursor(
                qt.Qt.CursorShape.PointingHandCursor
            )
        self.cursor_counter += 1

    def _hotspot_click_symbol(self, editor, indicator_number, index, length):
        editor.SendScintilla(
            qt.QsciScintilla.SCI_SETINDICATORCURRENT, indicator_number
        )
        editor.SendScintilla(
            qt.QsciScintilla.SCI_SETINDICATORVALUE,
            data.CLICK_AND_JUMP_INDICATOR_VALUE,
        )
        editor.SendScintilla(
            qt.QsciScintilla.SCI_INDICATORFILLRANGE, index, length
        )

    def reset_cursor(self):
        # Reset cursor image
        #        self.SendScintilla(
        #            qt.QsciScintilla.SCI_SETCURSOR,
        #            qt.QsciScintilla.SC_CURSORNORMAL
        #        )
        data.application.changeOverrideCursor(qt.Qt.CursorShape.ArrowCursor)
        for i in range(self.cursor_counter + 1):
            data.application.restoreOverrideCursor()
        self.cursor_counter = 0

    def delete_context_menu(self):
        # Clean up the context menu
        #        if self.contextmenu is not None:
        #            self.contextmenu.hide()
        #            for b in self.contextmenu.button_list:
        #                b.setParent(None)
        #            self.contextmenu.setParent(None)
        #            self.contextmenu = None
        pass

    def contextMenuEvent(self, event):
        # Built-in context menu
        #        super().contextMenuEvent(event)
        # If the parent is a text differ return from this function
        if hasattr(self, "actual_parent"):
            return

        # Create a menu
        if self.context_menu is not None:
            self.context_menu.setParent(None)
            self.context_menu = None
        self.context_menu = gui.templates.basemenu.BaseMenu(self)

        # Add symbol popup action if applicable
        click_global_position = qt.QCursor.pos()
        click_editor_index = self.get_index_from_cursor()
        #        selection = self.getSelection()
        #        if click_editor_index != -1 and selection == (-1, -1, -1, -1):
        #            self.setCursorPosition(0, click_editor_index)
        #        line, index = self.getCursorPosition() # This gives offset in bytes, which is what is needed
        #        line, index = self.lineIndexFromPosition(click_editor_index)

        if self.is_valid_file():
            # Check Clang-Engine validity
            if not self.__sai.is_engine_on():
                self.main_form.display.display_warning(
                    "Clang engine not running! Click&Jump cannot work!"
                )
                return
            # Get symbol information
            symbol = self.__sai.get_entity_data(
                self.save_name, click_editor_index
            )
            new_action = qt.QAction("Symbol information ...", self.context_menu)

            new_action.setStatusTip("Display symbol information popup")
            #            new_action.setIcon(iconfunctions.get_qicon(f"icons/"))
            self.context_menu.addAction(new_action)
            if symbol:

                def create_symbol_popup(*args):
                    self.main_form.symbol_popup.generate_symbol_information(
                        symbol
                    )
                    self.main_form.symbol_popup.display_at_position(
                        click_global_position
                    )

                new_action.triggered.connect(create_symbol_popup)
                new_action.setEnabled(True)
            else:
                new_action.setEnabled(False)

            # Go to definition
            new_action = qt.QAction(
                "Go to definition\tCtrl+LMB", self.context_menu
            )
            new_action.setStatusTip("Go to the symbol's definition")
            self.context_menu.addAction(new_action)
            if symbol:
                if isinstance(symbol, str):

                    def go_to_include_file(*args):
                        path = symbol
                        self.main_form.open_file(path)

                    new_action.triggered.connect(go_to_include_file)
                    new_action.setText("Go to include file\tCtrl+LMB")
                    new_action.setStatusTip("Go to the include file")
                else:
                    defs = self.__sai.get_definitions(symbol)
                    if defs:
                        if len(defs) > 1:
                            # Multiple definitions
                            new_action.triggered.connect(create_symbol_popup)

                        elif len(defs) == 1:
                            # One definition
                            d = defs[0]
                            path = functions.unixify_path(d.file.path)
                            if not os.path.isfile(path):
                                message = f"Definition location is not a file: '{d.file.path}'"
                                self.main_form.display.display_error(message)
                                return
                            begin = d.begin_offset
                            end = d.end_offset

                            def go_to_def(*args):
                                self.main_form.open_file(path)
                                editor = self.main_form.get_tab_by_save_name(
                                    path
                                )
                                editor.goto_index(begin)

                            new_action.triggered.connect(go_to_def)

                        else:
                            decls = symbol.declarations
                            if len(decls) > 1:
                                # Multiple declarations
                                new_action.triggered.connect(
                                    create_symbol_popup
                                )

                            elif len(decls) == 1:
                                # One declaration
                                d = decls[0]
                                path = functions.unixify_path(d.file.path)
                                if not os.path.isfile(path):
                                    message = f"Declaration location is not a file: '{d.file.path}'"
                                    self.main_form.display.display_error(
                                        message
                                    )
                                    return
                                begin = d.begin_offset
                                end = d.end_offset

                                def go_to_decl(*args):
                                    self.main_form.open_file(path)
                                    editor = (
                                        self.main_form.get_tab_by_save_name(
                                            path
                                        )
                                    )
                                    editor.goto_index(begin)

                                new_action.triggered.connect(go_to_decl)

                            else:
                                message = (
                                    f"I don't know what's going on, but symbol '{symbol.name}'"
                                    "has neither any definitions, nor declarations!"
                                )
                                self.main_form.display.display_error(message)

            else:
                new_action.setEnabled(False)
            # Add watch-point
            debugger_window = self.main_form.projects.debugger_window
            if data.debugging_active is True and debugger_window is not None:
                click_global_position = qt.QCursor.pos()
                click_cursor_index = self.get_index_from_cursor()
                word_at = self.wordAtLineIndex(0, click_cursor_index)

                try:
                    # Get the symbol details
                    symbol_string = None
                    if self.hasSelectedText():
                        selection_data = self.getSelection()
                        start_index = self.positionFromLineIndex(
                            selection_data[0],
                            selection_data[1],
                        )
                        entity = self.__sai.get_entity_data(
                            self.save_name, start_index
                        )
                        if entity is not None:
                            defs = self.__sai.get_definitions(entity)
                            filepath = ""
                            index = -1
                            _type = entity.kind_name
                            if defs:
                                for d in defs:
                                    filepath = functions.unixify_path(
                                        d.file.path
                                    )
                                    index = d.begin_offset
                                    break
                            symbol_string = self.selectedText().strip()

                    else:
                        entity = self.__sai.get_entity_data(
                            self.save_name, click_cursor_index
                        )
                        if word_at.strip() != "" and entity is not None:
                            defs = self.__sai.get_definitions(entity)
                            filepath = ""
                            index = -1
                            _type = entity.kind_name
                            if defs:
                                for d in defs:
                                    filepath = functions.unixify_path(
                                        d.file.path
                                    )
                                    index = d.begin_offset
                                    break
                            symbol_string = word_at.strip()

                    if symbol_string is not None:
                        # Watch-point
                        def insert_watchpoint(*args):
                            data.signal_dispatcher.debug_watchpoint_insert.emit(
                                symbol_string,
                                filepath,
                                index,
                                _type,
                            )

                        text = (
                            "Add watchpoint for '{}' (halt on change)".format(
                                symbol_string
                            )
                        )
                        new_action = qt.QAction(text, self.context_menu)
                        new_action.triggered.connect(insert_watchpoint)
                        new_action.setStatusTip(text)
                        self.context_menu.addAction(new_action)

                        # Watch variable
                        def insert_watch_variable(*args):
                            data.signal_dispatcher.debug_variable_object_create.emit(
                                symbol_string
                            )
                            self.main_form.projects.show_variable_watch()

                        text = "Monitor value of '{}'".format(symbol_string)
                        new_action = qt.QAction(text, self.context_menu)
                        new_action.triggered.connect(insert_watch_variable)
                        new_action.setStatusTip(text)
                        self.context_menu.addAction(new_action)

                        # Watch pointer-to-variable
                        def insert_watch_variable_pointer(*args):
                            data.signal_dispatcher.debug_variable_object_create.emit(
                                "*{}".format(symbol_string)
                            )
                            self.main_form.projects.show_variable_watch()

                        text = "Monitor value of '*{}'".format(symbol_string)
                        new_action = qt.QAction(text, self.context_menu)
                        new_action.triggered.connect(
                            insert_watch_variable_pointer
                        )
                        new_action.setStatusTip(text)
                        self.context_menu.addAction(new_action)
                except:
                    traceback.print_exc()

        # Special functions
        self.context_menu.addSeparator()
        funcs = {
            f"Cut\t{settings.keys['editor']['cut']}": {
                "func": self.cut,
                "desc": "Cut text in the editor",
                "icon": "icons/menu_edit/cut.png",
            },
            f"Copy\t{settings.keys['editor']['copy']}": {
                "func": self.copy,
                "desc": "Copy text in the editor",
                "icon": "icons/menu_edit/copy.png",
            },
            f"Paste\t{settings.keys['editor']['paste']}": {
                "func": self.paste,
                "desc": "Copy text in the editor",
                "icon": "icons/menu_edit/paste.png",
            },
        }
        for k, v in funcs.items():
            new_action = qt.QAction(k, self.context_menu)
            new_action.setToolTip(v["desc"])
            new_action.setStatusTip(v["desc"])
            new_action.setIcon(iconfunctions.get_qicon(v["icon"]))
            new_action.triggered.connect(v["func"])
            self.context_menu.addAction(new_action)

        ## General functions
        self.context_menu.addSeparator()
        general_actions = self.__create_general_actions()
        for _type, action in general_actions:
            if _type == "menu":
                self.context_menu.addMenu(action)
            elif _type == "action":
                self.context_menu.addAction(action)
            else:
                raise Exception("Unknown type: {}".format(_type))

        event.accept()
        # Adjust popup position so that the cursor already selects
        # the symbol information option
        adjusted_position = click_global_position - qt.create_qpoint(6, 6)
        self.context_menu.popup(adjusted_position)

    def __create_general_actions(self):
        actions = []

        # ---[Lexer option]--- #
        def set_lexer(lexer, lexer_name) -> None:
            try:
                # Initialize and set the new lexer
                lexer_instance = lexer()
                self.set_lexer(lexer_instance, lexer_name)
                # Change the corner widget (button) icon
                self.icon_manipulator.update_corner_button_icon(
                    self.current_icon
                )
                self.icon_manipulator.update_icon(self)
                # Display the lexer change
                message = "Lexer changed to: {}".format(lexer_name)
                self.main_form.display.display_message(message)
            except Exception:
                message = "Error with lexer selection!\n"
                self.main_form.display.display_error(message)
                self.main_form.display.display_error(traceback.format_exc())
                self.main_form.display.write_to_statusbar(message)
            return

        lexers_menu = self.main_form.display.create_lexers_menu(
            "Change lexer", set_lexer
        )
        lexers_menu.setIcon(iconfunctions.get_qicon("icons/gen/lexers.png"))
        lexers_menu.setStatusTip("Set the lexer for this document.")
        actions.append(("menu", lexers_menu))
        # ---[Show in file-tree]--- #
        if data.current_project.check_if_project_file(self.save_name):

            def navigate_to(*args) -> None:
                pe = self.main_form.get_tab_by_name("Filetree")
                try:
                    pe._parent.setCurrentWidget(pe)
                except Exception:
                    data.signal_dispatcher.notify_error.emit(
                        f"[CustomEditor] Filetree is not in the layout!"
                    )
                data.filetree.goto_path(self.save_name)
                return

            navigate_to_action = qt.QAction("Show in filetree", self.main_form)
            navigate_to_action.setIcon(
                iconfunctions.get_qicon("icons/gen/tree_navigate.png")
            )
            navigate_to_action.setToolTip(
                "Show the location of the file in the filetree."
            )
            navigate_to_action.setStatusTip(
                "Show the location of the file in the filetree."
            )
            navigate_to_action.triggered.connect(navigate_to)
            actions.append(("action", navigate_to_action))
        # ---[Copy file name]--- #
        clipboard_copy_action = qt.QAction("Copy file name", self.main_form)

        def clipboard_copy(*args) -> None:
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(self.name, mode=cb.Mode.Clipboard)
            return

        clipboard_copy_action.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
        )
        clipboard_copy_action.setStatusTip(
            "Copy the document's name to clipboard."
        )
        clipboard_copy_action.triggered.connect(clipboard_copy)
        actions.append(("action", clipboard_copy_action))
        # ---[Copy file path]--- #
        clipboard_copy_path_action = qt.QAction(
            "Copy file path", self.main_form
        )

        def clipboard_copy(*args) -> None:
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(self.save_name, mode=cb.Mode.Clipboard)
            return

        clipboard_copy_path_action.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
        )
        clipboard_copy_path_action.setStatusTip(
            "Copy the document's path to clipboard: {}".format(self.save_name)
        )
        clipboard_copy_path_action.triggered.connect(clipboard_copy)
        actions.append(("action", clipboard_copy_path_action))
        # ---[Hard/soft tabs]--- #
        text = "Indentation: spaces"
        icon = f"icons/menu_edit/tab_spaces_invisible.png"
        if not settings.editor["tabs_use_spaces"]:
            text = "Indentation: tabs"
            icon = f"icons/menu_edit/tab_visible.png"
        toggle_tabs_action = qt.QAction(text, self.main_form)
        toggle_tabs_action.setStatusTip("Toggle indentation with tabs/spaces")
        toggle_tabs_action.setIcon(iconfunctions.get_qicon(icon))

        def toggle_tabs(*args):
            self.main_form.settings.manipulator.pmf_tabs_use_spaces_toggle(
                not settings.editor["tabs_use_spaces"]
            )
            data.signal_dispatcher.update_tabs_use_spaces.emit()
            return

        toggle_tabs_action.triggered.connect(toggle_tabs)
        actions.append(("action", toggle_tabs_action))
        # ---[Whitespace visibility]--- #
        text = "Tabs/whitespaces are: visible"
        icon_path = f"icons/menu_edit/tab_visible.png"
        if not settings.editor["whitespace_visible"]:
            text = "Tabs/whitespaces are: not-visible"
            icon_path = f"icons/menu_edit/tab_spaces_invisible.png"
        toggle_tab_visibility_action = qt.QAction(text, self.main_form)
        toggle_tab_visibility_action.setStatusTip(
            "Toggle visibility of whitespaces and tabs"
        )
        toggle_tab_visibility_action.setIcon(iconfunctions.get_qicon(icon_path))

        def toggle_tab_visibility(*args) -> None:
            self.main_form.settings.manipulator.pmf_whitespace_visible_toggle(
                not settings.editor["whitespace_visible"]
            )
            data.signal_dispatcher.update_whitespace_visible.emit()
            return

        toggle_tab_visibility_action.triggered.connect(toggle_tab_visibility)
        actions.append(("action", toggle_tab_visibility_action))
        # ---[Tabs to spaces]--- #
        tabs_to_spaces_action = qt.QAction(
            "Convert tabs to spaces", self.main_form
        )
        tabs_to_spaces_action.setStatusTip(
            "Convert all tabs in the editor to spaces."
        )
        tabs_to_spaces_action.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/edit.png")
        )

        def tabs_to_spaces(*args) -> None:
            self.tabs_to_spaces()
            return

        tabs_to_spaces_action.triggered.connect(tabs_to_spaces)
        actions.append(("action", tabs_to_spaces_action))
        # ---[Open corresponding object file]--- #
        object_file_action = qt.QAction(
            "Open corresponding object file", self.main_form
        )
        object_file_action.setStatusTip("Open corresponding object file.")
        object_file_action.setIcon(
            iconfunctions.get_qicon(f"icons/file/file_o.png")
        )

        def open_object_file(*args) -> None:
            path = self.save_name
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

        object_file_action.triggered.connect(open_object_file)
        actions.append(("action", object_file_action))
        # ---[Help action]--- #
        help_action = qt.QAction("Help", self.main_form)
        help_action.setStatusTip("Display editor help")
        help_action.setIcon(iconfunctions.get_qicon("icons/dialog/help.png"))

        def help_func(*args) -> None:
            helpdocs.help_texts.editor_help()
            return

        help_action.triggered.connect(help_func)
        actions.append(("action", help_action))

        return actions

    def get_index_from_cursor(self):
        try:
            cursor_position = self.mapFromGlobal(qt.QCursor.pos())
            return self.SendScintilla(
                qt.QsciScintilla.SCI_POSITIONFROMPOINTCLOSE,
                cursor_position.x(),
                cursor_position.y(),
            )
        except:
            return None

    def wheelEvent(self, event):
        """Mouse scroll event of the custom editor."""
        key_modifiers = qt.QApplication.keyboardModifiers()
        if key_modifiers != qt.Qt.KeyboardModifier.ControlModifier:
            # Execute the superclass method
            super().wheelEvent(event)
        else:
            # Ignore the event, it will be propageted up to the parent objects
            event.ignore()
        self.set_symbol_analysis()

    def text_changed(self):
        """Event that fires when the scintilla document text changes."""
        # Update the line list
        self.line_list.update_text_to_list(self.text())
        # Update the line count list with a list comprehention
        self.line_count = [line for line in range(1, self.lines() + 1)]
        # Execute the parent basic widget signal
        if hasattr(self._parent, "_signal_text_changed"):
            self._parent._signal_text_changed(self)

    def reset_file_reference(self):
        # self.text_changed()
        pass

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()
        # Check the save button status of the menubar
        self._parent._set_save_status()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Fire the leave signal
        self.focusLost.emit()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Fire the leave signal
        self.focusLost.emit()

    def focus_in_parent(self):
        self._parent.setCurrentWidget(self)

    """
    Line manipulation functions
    """

    def goto_line(self, line_number):
        """Set focus and cursor to the selected line."""
        # Check if the selected line is within the line boundaries of the current document
        line_number = self.check_line_numbering(line_number)
        # Move the cursor to the start of the selected line
        self.setCursorPosition(line_number, 0)
        # Move the first displayed line to the top of the viewing area minus an offset
        #        self.set_first_visible_line(line_number - 10)
        qt.QTimer.singleShot(0, self.__goto_adjust_view)

    def goto_line_column(self, line, column):
        # Move the cursor to the start of the selected line
        self.setCursorPosition(line, column)
        # Move the first displayed line to the top of the viewing area minus an offset
        #        self.set_first_visible_line(line - 10)
        qt.QTimer.singleShot(0, self.__goto_adjust_view)

    def goto_index(self, index):
        """Set focus and cursor to the selected index."""
        #        self.setCursorPosition(0, index)
        self.SendScintilla(self.SCI_GOTOPOS, index)
        line, column = self.lineIndexFromPosition(index)
        #        self.set_first_visible_line(line - 10)
        qt.QTimer.singleShot(0, self.__goto_adjust_view)

    def __goto_adjust_view(self, *args):
        line, column = self.getCursorPosition()
        first_visible_line = self.firstVisibleLine()
        lines_on_screen = self.SendScintilla(self.SCI_LINESONSCREEN)
        last_visible_line = first_visible_line + lines_on_screen
        if line < (first_visible_line + 20) or line > (last_visible_line - 20):
            self.set_first_visible_line(line - int(lines_on_screen / 2))

        self.setFocus()

    def lines_on_screen(self):
        lines_on_screen = self.SendScintilla(
            qt.QsciScintillaBase.SCI_LINESONSCREEN
        )
        return lines_on_screen

    def blink_error_line_column(self, line, column):
        self.markerDeleteAll(self.FLASH_LINE_INDICATOR)
        self.setCursorPosition(line, 0)
        self.blink_data = {}
        self.blink_data["counter"] = 0
        self.blink_data["line"] = line
        self.blink_data["boundary"] = [
            (line, 0, line, len(self.text(line)) - 1)
        ]
        self.blink_data["state"] = False
        qt.QTimer.singleShot(100, self._blink_highlight)

    def blink_error_index(self, index):
        line, column = self.lineIndexFromPosition(index)
        self.markerDeleteAll(self.FLASH_LINE_INDICATOR)
        self.setCursorPosition(line, 0)
        self.blink_data = {}
        self.blink_data["counter"] = 0
        self.blink_data["line"] = line
        self.blink_data["boundary"] = [
            (line, 0, line, len(self.text(line)) - 1)
        ]
        self.blink_data["state"] = False
        qt.QTimer.singleShot(100, self._blink_highlight)

    def _blink_highlight(self):
        self.blink_data["counter"] += 1
        if self.blink_data["counter"] > 6:
            self.blink_data["counter"] = 0
            self.blink_data["boundary"] = None
            self.clear_highlights()
            self.markerDelete(
                self.blink_data["line"], self.FLASH_LINE_INDICATOR
            )
            return
        if self.blink_data["state"]:
            #            self.set_indicator("blink")
            #            self.highlight_raw(self.blink_data["boundary"])
            self.markerAdd(self.blink_data["line"], self.FLASH_LINE_INDICATOR)
        else:
            #            self.clear_highlights()
            self.markerDelete(
                self.blink_data["line"], self.FLASH_LINE_INDICATOR
            )
        self.blink_data["state"] = not self.blink_data["state"]
        self.setFocus()
        qt.QTimer.singleShot(100, self._blink_highlight)

    def set_first_visible_line(self, line_number):
        """Move the top of the viewing area to the selected line."""
        if line_number < 0:
            line_number = 0
        self.SendScintilla(
            qt.QsciScintillaBase.SCI_SETFIRSTVISIBLELINE, line_number
        )

    def remove_line(self, line_number):
        """Remove a line from the custom editor."""
        # Check if the selected line is within the line boundaries of the current document
        line_number = self.check_line_numbering(line_number)
        # Select the whole line text, "tab.lineLength(line_number)" doesn't work because a single UTF-8 character has the length of 2
        self.setSelection(line_number, 0, line_number + 1, 0)
        # Replace the line with an empty string
        self.replaceSelectedText("")

    def replace_line(self, replace_text, line_number):
        """
        Replace an entire line in a scintilla document
            - line_number has to be as displayed in a QScintilla widget, which is ""from 1 to number_of_lines""
        """
        # Check if the selected line is within the line boundaries of the current document
        line_number = self.check_line_numbering(line_number)
        # Select the whole line text, "tab.lineLength(line_number)" doesn't work because a single UTF-8 character has the length of 2
        if line_number == self.lines() - 1:
            self.setSelection(
                line_number, 0, line_number, len(self.text(line_number))
            )
        else:
            self.setSelection(
                line_number, 0, line_number, len(self.text(line_number)) - 1
            )
        # Replace the selected text with the new
        if "\n" in self.selectedText() or "\r\n" in self.selectedText():
            self.replaceSelectedText(replace_text + "\n")
        else:
            # The last line, do not add the newline character
            self.replaceSelectedText(replace_text)

    def set_line(self, line_text, line_number):
        """Set the text of a line."""
        self.replace_line(line_text, line_number)

    def set_lines(self, line_from, line_to, list_of_strings):
        """Set the text of multiple lines in one operation.

        This function is almost the same as "prepend_to_lines" and
        "append_to_lines", they may be merged in the future.
        """
        # Check the boundaries
        if line_from < 0:
            line_from = 0
        if line_to < 0:
            line_to = 0
        # Select the text from the lines and test if line_to is the last line in the document
        if line_to == self.lines() - 1:
            self.setSelection(line_from, 0, line_to, len(self.text(line_to)))
        else:
            self.setSelection(
                line_from, 0, line_to, len(self.text(line_to)) - 1
            )
        # Split get the selected lines and add them to a list
        selected_lines = []
        for i in range(line_from, line_to + 1):
            selected_lines.append(self.text(i))
        # Loop through the list and replace the line text
        for i in range(len(selected_lines)):
            selected_lines[i] = list_of_strings[i]
        # Replace the selected text with the prepended list merged into one string
        self.replaceSelectedText(self.list_to_text(selected_lines))
        # Set the cursor to the beginning of the last set line
        self.setCursorPosition(line_to, 0)

    def set_all_text(self, text):
        """Set the entire scintilla document text with a single select/replace
        routine.

        This function was added, because "setText()" function from Qscintilla
        cannot be undone!
        """
        # Check if the text is a list of lines
        if isinstance(text, list):
            # Join the list items into one string with newline as the delimiter
            text = "\n".join(text)
        # Select all the text in the document
        self.setSelection(0, 0, self.lines(), 0)
        # Replace it with the new text
        self.replaceSelectedText(text)

    def get_line_number(self):
        """Return the line on which the cursor is."""
        return self.getCursorPosition()[0] + 1

    def get_line(self, line_number):
        """Return the text of the selected line in the scintilla document."""
        line_text = self.text(line_number - 1)
        return line_text.replace("\n", "")

    def get_lines(self, line_from=None, line_to=None):
        """Return the text of the entire scintilla document as a list of
        lines."""
        # Check if boundaries are valid
        if line_from is None or line_to is None:
            return self.line_list
        else:
            # Slice up the line_list list according to the boundaries
            return self.line_list[line_from:line_to]

    def get_absolute_cursor_position(self):
        """
        Get the absolute cursor position using the line list
        NOTE:
            This function returns the actual length of characters,
            NOT the length of bytes!
        """
        return self.line_list.get_absolute_cursor_position()

    def append_to_line(self, append_text, line_number):
        """Add text to the back of the line."""
        # Check if the appending text is valid
        if append_text != "" and append_text is not None:
            # Append the text, stripping the newline characters from the current line text
            self.replace_line(
                self.get_line(line_number).rstrip() + append_text, line_number
            )

    def append_to_lines(self, *args, **kwds):
        """Add text to the back of the line range."""
        # Check the arguments and keyword arguments
        appending_text = ""
        sel_line_from, sel_index_from, sel_line_to, sel_index_to = (
            self.getSelection()
        )
        if (
            len(args) == 1
            and isinstance(args[0], str)
            and (sel_line_from == sel_line_to)
        ):
            # Append text to all lines
            appending_text = args[0]
            line_from = 1
            line_to = self.lines()
        elif (
            len(args) == 3
            and isinstance(args[0], str)
            and isinstance(args[1], int)
            and isinstance(args[2], int)
        ):
            # Append text to specified lines
            appending_text = args[0]
            line_from = args[1]
            line_to = args[2]
        elif sel_line_from != sel_line_to:
            # Append text to selected lines
            appending_text = args[0]
            line_from = sel_line_from + 1
            line_to = sel_line_to + 1
        else:
            self.main_form.display.write_to_statusbar(
                "Wrong arguments to 'append' function!", 1000
            )
            return
        # Check if the appending text is valid
        if appending_text != "" and appending_text is not None:
            # Adjust the line numbers to standard(0..lines()) numbering
            line_from -= 1
            line_to -= 1
            # Check the boundaries
            if line_from < 0:
                line_from = 0
            if line_to < 0:
                line_to = 0
            # Select the text from the lines
            self.setSelection(
                line_from, 0, line_to, len(self.text(line_to).replace("\n", ""))
            )
            # Split the line text into a list
            selected_lines = self.text_to_list(self.selectedText())
            # Loop through the list and prepend the prepend text
            for i in range(len(selected_lines)):
                selected_lines[i] = selected_lines[i] + appending_text
            # Replace the selected text with the prepended list merged into one string
            self.replaceSelectedText(self.list_to_text(selected_lines))
            # Select the appended lines, to enable consecutive prepending
            self.setSelection(
                line_from, 0, line_to, len(self.text(line_to)) - 1
            )

    def prepend_to_line(self, append_text, line_number):
        """Add text to the front of the line."""
        # Check if the appending text is valid
        if append_text != "" and append_text is not None:
            # Prepend the text, stripping the newline characters from the current line text
            self.replace_line(
                append_text + self.get_line(line_number).rstrip(), line_number
            )

    def prepend_to_lines(self, *args, **kwds):
        """Add text to the front of the line range."""
        # Check the arguments and keyword arguments
        prepending_text = ""
        sel_line_from, sel_index_from, sel_line_to, sel_index_to = (
            self.getSelection()
        )
        if (
            len(args) == 1
            and isinstance(args[0], str)
            and (sel_line_from == sel_line_to)
        ):
            # Prepend text to all lines
            prepending_text = args[0]
            line_from = 1
            line_to = self.lines()
        elif (
            len(args) == 3
            and isinstance(args[0], str)
            and isinstance(args[1], int)
            and isinstance(args[2], int)
        ):
            # Prepend text to specified lines
            prepending_text = args[0]
            line_from = args[1]
            line_to = args[2]
        elif sel_line_from != sel_line_to:
            # Prepend text to selected lines
            prepending_text = args[0]
            line_from = sel_line_from + 1
            line_to = sel_line_to + 1
        else:
            self.main_form.display.write_to_statusbar(
                "Wrong arguments to 'prepend' function!", 1000
            )
            return
        # Check if the appending text is valid
        if prepending_text != "" and prepending_text is not None:
            # Adjust the line numbers to standard(0..lines()) numbering
            line_from -= 1
            line_to -= 1
            # Check the boundaries
            if line_from < 0:
                line_from = 0
            if line_to < 0:
                line_to = 0
            # Select the text from the lines
            self.setSelection(
                line_from, 0, line_to, len(self.text(line_to)) - 1
            )
            # Split the line text into a list
            selected_lines = self.text_to_list(self.selectedText())
            # Loop through the list and prepend the prepend text
            for i in range(len(selected_lines)):
                selected_lines[i] = prepending_text + selected_lines[i]
            # Replace the selected text with the prepended list merged into one string
            self.replaceSelectedText(self.list_to_text(selected_lines))
            # Select the prepended lines, to enable consecutive prepending
            self.setSelection(
                line_from,
                0,
                line_to,
                len(self.text(line_to))
                - 1,  # -1 to offset the newline character ('\n')
            )

    def comment_line(self, line_number=None):
        """Comment a single line according to the currently set lexer."""
        if line_number is None:
            line_number = self.getCursorPosition()[0] + 1
        # Check commenting style
        if self.lexer().open_close_comment_style == True:
            self.prepend_to_line(self.lexer().comment_string, line_number)
            self.append_to_line(self.lexer().end_comment_string, line_number)
        else:
            self.prepend_to_line(self.lexer().comment_string, line_number)
        # Return the cursor to the commented line
        self.setCursorPosition(line_number - 1, 0)

    def comment_lines(self, line_from=0, line_to=0):
        """Comment lines according to the currently set lexer."""
        if line_from == line_to:
            return
        else:
            # Check commenting style
            if self.lexer().open_close_comment_style == True:
                self.prepend_to_lines(
                    self.lexer().comment_string, line_from, line_to
                )
                self.append_to_lines(
                    self.lexer().end_comment_string, line_from, line_to
                )
            else:
                self.prepend_to_lines(
                    self.lexer().comment_string, line_from, line_to
                )
            # Select the commented lines again, reverse the boundaries,
            # so that the cursor will be at the beggining of the selection
            line_to_length = len(self.line_list[line_to])
            self.setSelection(line_to - 1, line_to_length, line_from - 1, 0)

    def uncomment_line(self, line_number=None):
        """Uncomment a single line according to the currently set lexer."""
        if line_number is None:
            line_number = self.getCursorPosition()[0] + 1
        line_text = self.get_line(line_number)
        # Check the commenting style
        if self.lexer().open_close_comment_style == True:
            if line_text.lstrip().startswith(self.lexer().comment_string):
                new_line = line_text.replace(self.lexer().comment_string, "", 1)
                new_line = functions.right_replace(
                    new_line, self.lexer().end_comment_string, "", 1
                )
                self.replace_line(new_line, line_number)
                # Return the cursor to the uncommented line
                self.setCursorPosition(line_number - 1, 0)
        else:
            if line_text.lstrip().startswith(self.lexer().comment_string):
                self.replace_line(
                    line_text.replace(self.lexer().comment_string, "", 1),
                    line_number,
                )
                # Return the cursor to the uncommented line
                self.setCursorPosition(line_number - 1, 0)

    def uncomment_lines(self, line_from, line_to):
        """Uncomment lines according to the currently set lexer."""
        if line_from == line_to:
            return
        else:
            # Select the lines
            selected_lines = self.line_list[line_from:line_to]
            # Loop through the list and remove the comment string if it's in front of the line
            for i in range(len(selected_lines)):
                # Check the commenting style
                if self.lexer().open_close_comment_style == True:
                    if (
                        selected_lines[i]
                        .lstrip()
                        .startswith(self.lexer().comment_string)
                    ):
                        selected_lines[i] = selected_lines[i].replace(
                            self.lexer().comment_string, "", 1
                        )
                        selected_lines[i] = functions.right_replace(
                            selected_lines[i],
                            self.lexer().end_comment_string,
                            "",
                            1,
                        )
                else:
                    if (
                        selected_lines[i]
                        .lstrip()
                        .startswith(self.lexer().comment_string)
                    ):
                        selected_lines[i] = selected_lines[i].replace(
                            self.lexer().comment_string, "", 1
                        )
            # Replace the selected text with the prepended list merged into one string
            self.line_list[line_from:line_to] = selected_lines
            # Select the uncommented lines again, reverse the boundaries,
            # so that the cursor will be at the beggining of the selection
            line_to_length = len(self.line_list[line_to])
            self.setSelection(line_to - 1, line_to_length, line_from - 1, 0)

    def indent_lines_to_cursor(self):
        """Indent selected lines to the current cursor position in the document.

        P.S.:   embeetle uses spaces as tabs by default, so if you copy text
        that         contains tabs, the indent will not be correct unless you
        run the         tabs_to_spaces function first!
        """
        # Get the cursor index in the current line and selected lines
        cursor_position = self.getCursorPosition()
        indent_space = cursor_position[1] * " "
        # Test if indenting one or many lines
        if self.getSelection() == (-1, -1, -1, -1):
            line_number = cursor_position[0] + 1
            line = self.line_list[line_number].lstrip()
            self.line_list[line_number] = indent_space + line
        else:
            # Get the cursor index in the current line and selected lines
            start_line_number = self.getSelection()[0] + 1
            end_line_number = self.getSelection()[2] + 1
            # Get the lines text as a list
            indented_lines = []
            line_list = self.get_lines(start_line_number, end_line_number)
            for i in range(len(line_list)):
                line = line_list[i].lstrip()
                indented_lines.append(indent_space + line)
            # Adjust the line numbers to standard(0..lines()) numbering
            start_line_number -= 1
            end_line_number -= 1
            # Select the text from the lines
            if end_line_number == (self.lines() - 1):
                # The last selected line is at the end of the document,
                # select every character to the end.
                self.setSelection(
                    start_line_number,
                    0,
                    end_line_number,
                    self.lineLength(end_line_number),
                )
            else:
                self.setSelection(
                    start_line_number,
                    0,
                    end_line_number,
                    self.lineLength(end_line_number) - 1,
                )
            # Replace the selected text with the prepended list merged into one string
            self.replaceSelectedText(self.list_to_text(indented_lines))
            # Move the cursor to the beggining of the restore line
            # to reset the document view to the beginning of the line
            self.setCursorPosition(cursor_position[0], 0)
            # Restore cursor back to the original position
            self.setCursorPosition(cursor_position[0], cursor_position[1])

    def custom_indent(self):
        """TEMPORARY."""
        selection = self.getSelection()
        if selection == (-1, -1, -1, -1):
            line_number, position = self.getCursorPosition()
            self.indent(line_number)
        else:
            line_from = selection[0]
            line_to = selection[2]
            for i in range(line_from, line_to):
                self.indent(i)
        return
        """
        Scintila indents line-by-line, which is very slow for a large amount of lines. Try indenting 20000 lines.
        This is a custom indentation function that indents all lines in one operation.
        """
        tab_width = settings.editor["tab_width"]
        # Check QScintilla's tab width
        if self.tabWidth() != tab_width:
            self.setTabWidth(tab_width)
        # Indent according to selection
        selection = self.getSelection()
        if selection == (-1, -1, -1, -1):
            line_number, index = self.getCursorindex()
            # Adjust index to the line list indexing
            line_number += 1
            line_text = self.line_list[line_number]
            # Check if there is no text before the cursor index in the current line
            if line_text[:index].strip() == "":
                for i, ch in enumerate(line_text):
                    # Find the first none space character
                    if ch != " ":
                        diff = tab_width - (i % tab_width)
                        adding_text = diff * " "
                        new_line = adding_text + line_text
                        self.line_list[line_number] = new_line
                        self.setCursorindex(line_number - 1, i + diff)
                        break
                else:
                    # No text in the current line
                    diff = tab_width - (index % tab_width)
                    adding_text = diff * " "
                    new_line = (
                        line_text[:index] + adding_text + line_text[index:]
                    )
                    self.line_list[line_number] = new_line
                    self.setCursorindex(line_number - 1, len(new_line))
            else:
                # There is text before the cursor
                diff = tab_width - (index % tab_width)
                adding_text = diff * " "
                new_line = line_text[:index] + adding_text + line_text[index:]
                self.line_list[line_number] = new_line
                self.setCursorindex(line_number - 1, index + diff)
        else:
            # MULTILINE INDENT
            selected_line = self.getCursorPosition()[0]
            # Adjust the 'from' and 'to' indexes to the line list indexing
            line_from = selection[0] + 1
            line_to = selection[2] + 1
            # This part is to mimic the default indent functionality of Scintilla
            if selection[3] == 0:
                line_to = selection[2]
            # Get the selected line list
            lines = self.line_list[line_from:line_to]
            # Set the indentation width
            indentation_string = tab_width * " "

            ## # Select the indentation function
            ## if sys.version_info.minor <= 2:
            ##     def nested_indent(line, indent_string):
            ##         if line.strip() != " ":
            ##             line = indent_string + line
            ##         return line
            ##     indent_func = nested_indent
            ## else:
            ##     indent_func = textwrap.indent
            ## #Indent the line list in place
            ## for i, line in enumerate(lines):
            ##     lines[i] = indent_func(line, indentation_string)
            # Smart indentation that tabs to tab-width columns
            def indent_func(line):
                if line.strip() != " ":
                    if line.startswith(" "):
                        leading_spaces = len(line) - len(line.lstrip())
                        diff = tab_width - (leading_spaces % tab_width)
                        adding_text = diff * " "
                        line = adding_text + line
                    else:
                        line = (tab_width * " ") + line
                return line

            # Indent the line list in place
            for i, line in enumerate(lines):
                lines[i] = indent_func(line)
            # Set the new line list in one operation
            self.line_list[line_from:line_to] = lines
            # Set the selection again according to which line was selected before the indent
            if selected_line == selection[0]:
                # This part is also to mimic the default indent functionality of Scintilla
                if selection[3] == 0:
                    select_from = selection[2]
                else:
                    select_from = selection[2] + 1
                select_from_length = 0
                select_to = selection[0]
                select_to_length = 0
            else:
                select_from = selection[0]
                select_from_length = 0
                select_to = selection[2]
                # This part is also to mimic the default indent functionality of Scintilla
                if selection[3] == 0:
                    select_to = selection[2]
                else:
                    select_to = selection[2] + 1
                select_to_length = 0
            self.setSelection(
                select_from, select_from_length, select_to, select_to_length
            )

    def custom_unindent(self):
        """TEMPORARY."""
        selection = self.getSelection()
        if selection == (-1, -1, -1, -1):
            line_number, index = self.getCursorindex()
            self.unindent(line_number)
        else:
            line_from = selection[0]
            line_to = selection[2]
            for i in range(line_from, line_to):
                self.unindent(i)
        return
        """
        Scintila unindents line-by-line, which is very slow for a large amount of lines. Try unindenting 20000 lines.
        This is a custom unindentation function that unindents all lines in one operation.
        """
        tab_width = settings.editor["tab_width"]
        # Check QScintilla's tab width
        if self.tabWidth() != tab_width:
            self.setTabWidth(tab_width)
        # Unindent according to selection
        selection = self.getSelection()
        if selection == (-1, -1, -1, -1):
            line_number, index = self.getCursorindex()
            # Adjust index to the line list indexing
            line_number += 1
            line_text = self.line_list[line_number]
            if line_text == "":
                return
            elif line_text.strip() == "":
                # The line contains only spaces
                diff = len(line_text) % tab_width
                if diff == 0:
                    diff = tab_width
                new_length = len(line_text) - diff
                self.line_list[line_number] = self.line_list[line_number][
                    :new_length
                ]
                self.setCursorindex(line_number - 1, new_length)
            else:
                if line_text[0] != " ":
                    # Do not indent, just move the cursor back
                    if index == 0:
                        return
                    diff = index % tab_width
                    if diff == 0:
                        diff = tab_width
                    self.setCursorindex(line_number - 1, index - diff)
                elif line_text[:index].strip() == "":
                    # The line has spaces in the beginning
                    for i, ch in enumerate(line_text):
                        if ch != " ":
                            diff = i % tab_width
                            if diff == 0:
                                diff = tab_width
                            self.line_list[line_number] = self.line_list[
                                line_number
                            ][diff:]
                            self.setCursorindex(line_number - 1, i - diff)
                            break
                else:
                    # Move the cursor to the first none space character then repeat above code
                    diff = index % tab_width
                    if diff == 0:
                        diff = tab_width
                    self.setCursorindex(line_number - 1, index - diff)
        else:
            # MULTILINE UNINDENT
            selected_line = self.getCursorPosition()[0]
            # Adjust the 'from' and 'to' indexes to the line list indexing
            line_from = selection[0] + 1
            line_to = selection[2] + 1
            # This part is to mimic the default indent functionality of Scintilla
            if selection[3] == 0:
                line_to = selection[2]
            # Get the selected line list
            lines = self.line_list[line_from:line_to]

            ## Remove the leading tab-width number of spaces in every line
            ## for i in range(0, len(lines)):
            ##     for j in range(0, tab_width):
            ##         if lines[i].startswith(" "):
            ##             lines[i] = lines[i].replace(" ", "", 1)
            # Smart unindentation that unindents each line to the nearest tab column
            def unindent_func(line):
                if line.startswith(" "):
                    leading_spaces = len(line) - len(line.lstrip())
                    diff = leading_spaces % tab_width
                    if diff == 0:
                        diff = tab_width
                    line = line.replace(diff * " ", "", 1)
                return line

            # Unindent the line list in place
            for i, line in enumerate(lines):
                lines[i] = unindent_func(line)
            # Set the new line list in one operation
            self.line_list[line_from:line_to] = lines
            # Set the selection again according to which line was selected before the indent
            if selected_line == selection[0]:
                # This part is also to mimic the default indent functionality of Scintilla
                if selection[3] == 0:
                    select_from = selection[2]
                else:
                    select_from = selection[2] + 1
                select_from_length = 0
                select_to = selection[0]
                select_to_length = 0
            else:
                select_from = selection[0]
                select_to = selection[2]
                select_from_length = 0
                # This part is also to mimic the default indent functionality of Scintilla
                if selection[3] == 0:
                    select_to = selection[2]
                else:
                    select_to = selection[2] + 1
                select_to_length = 0
            self.setSelection(
                select_from, select_from_length, select_to, select_to_length
            )

    def text_to_list(self, input_text):
        """Split the input text into a list of lines according to the document
        EOL delimiter."""
        out_list = []
        if self.eolMode() == qt.QsciScintilla.EolMode.EolUnix:
            out_list = input_text.split("\n")
        elif self.eolMode() == qt.QsciScintilla.EolMode.EolWindows:
            out_list = input_text.split("\r\n")
        elif self.eolMode() == qt.QsciScintilla.EolMode.EolMac:
            out_list = input_text.split("\r")
        return out_list

    def list_to_text(self, line_list):
        """Convert a list of lines to one string according to the document EOL
        delimiter."""
        out_text = ""
        if self.eolMode() == qt.QsciScintilla.EolMode.EolUnix:
            out_text = "\n".join(line_list)
        elif self.eolMode() == qt.QsciScintilla.EolMode.EolWindows:
            out_text = "\r\n".join(line_list)
        elif self.eolMode() == qt.QsciScintilla.EolMode.EolMac:
            out_text = "\r".join(line_list)
        return out_text

    def toggle_comment_uncomment(self):
        """Toggle commenting for the selected lines."""
        # Check if the document is a valid programming language
        if self.lexer().comment_string is None:
            self.main_form.display.display_message_with_type(
                "Lexer '{}' has no comment abillity!".format(
                    self.lexer().language()
                ),
                message_type=data.MessageType.WARNING,
            )
            return
        # Test if there is no selected text
        if (
            self.getSelection() == (-1, -1, -1, -1)
            or self.getSelection()[0] == self.getSelection()[2]
        ):
            # No selected text
            line_number = self.getCursorPosition()[0] + 1
            line_text = self.get_line(line_number)
            # Un/comment only the current line (no arguments un/comments current line)
            if line_text.lstrip().startswith(self.lexer().comment_string):
                self.uncomment_line()
            else:
                self.comment_line()
        else:
            # Text is selected
            start_line_number = self.getSelection()[0] + 1
            first_selected_chars = self.selectedText()[
                0 : len(self.lexer().comment_string)
            ]
            end_line_number = self.getSelection()[2] + 1
            # Choose un/commenting according to the first line in selection
            if first_selected_chars == self.lexer().comment_string:
                self.uncomment_lines(start_line_number, end_line_number)
            else:
                self.comment_lines(start_line_number, end_line_number)

    def for_each_line(self, in_func):
        """Apply function 'in_func' to lines."""
        # Check that in_func is really a function
        if callable(in_func) == False:
            self.main_form.display.display_message_with_type(
                "'for_each_line' argument has to be a function!",
                message_type=data.MessageType.ERROR,
            )
            return
        # Loop through the lines and apply the function to each line
        if (
            self.getSelection() == (-1, -1, -1, -1)
            or self.getSelection()[0] == self.getSelection()[2]
        ):
            # No selected text, apply function to the every line
            try:
                new_line_list = []
                function_returns_none = False
                for line in self.line_list:
                    new_line = in_func(line)
                    if new_line is None:
                        function_returns_none = True
                        continue
                    new_line_list.append(new_line)
                if function_returns_none == False:
                    # Assign the new list over the old one
                    self.line_list = new_line_list
            except Exception as ex:
                self.main_form.display.display_message_with_type(
                    "'for_each_line' has an error:\n" + str(ex),
                    message_type=data.MessageType.ERROR,
                )
                return
        else:
            # Selected text, apply function to the selected lines only
            try:
                # Get the starting and end line
                start_line_number = self.getSelection()[0] + 1
                end_line_number = self.getSelection()[2] + 1
                # Apply the function to the lines
                new_line_list = []
                function_returns_none = False
                for line in self.line_list[start_line_number:end_line_number]:
                    new_line = in_func(line)
                    if new_line is None:
                        function_returns_none = True
                        continue
                    new_line_list.append(new_line)
                if function_returns_none == False:
                    # Assign the new list over the old one
                    self.line_list[start_line_number:end_line_number] = (
                        new_line_list
                    )
            except Exception as ex:
                self.main_form.display.display_message_with_type(
                    "'for_each_line' has an error:\n" + str(ex),
                    message_type=data.MessageType.ERROR,
                )
                return

    def remove_empty_lines(self):
        new_line_list = []
        for line in self.line_list:
            if line.strip() != "":
                new_line_list.append(line)
        # Assign the new list over the old one
        self.line_list = new_line_list

    def set_cursor_to_start_of_selection(self):
        if self.hasSelectedText():
            line_from, index_from, line_to, index_to = self.getSelection()
            self.setCursorPosition(line_from, index_from)

    def find_matching_brace(self):
        result, brace, other = self.findMatchingBrace(
            qt.QsciScintilla.BraceMatch.SloppyBraceMatch
        )
        if result:
            if brace > other:
                other += 1
            self.goto_index(other)

    """
    Search and replace functions
    """

    def find_text(
        self,
        search_text,
        case_sensitive=False,
        search_forward=True,
        regular_expression=False,
        incremental=False,
    ):
        """(SAME AS THE QSciScintilla.find, BUT THIS RETURNS A RESULT)

        Function to find an occurrence of text in the current tab of a basic widget:
            - Python reguler expressions are used, not the Scintilla built in ones
            - function executes cyclically over the scintilla document, when it reaches the end of the document
            ! THERE IS A BUG WHEN SEARCHING FOR UNICODE STRINGS, THESE ARE ALWAYS CASE SENSITIVE
        """

        def focus_entire_found_text():
            """Nested function for selection the entire found text."""
            # Save the currently found text selection attributes
            position = self.getSelection()
            # Set the cursor to the beginning of the line, so that in case the
            # found string index is behind the previous cursor index, the whole
            # found text is shown!
            self.setCursorPosition(position[0], 0)
            self.setSelection(
                position[0], position[1], position[2], position[3]
            )

        # If incremental find is active, place the cursor in front
        # of the selection, if there is selected text in the document
        if incremental:
            self.set_cursor_to_start_of_selection()
        # Set focus to the tab that will be searched
        self._parent.setCurrentWidget(self)
        if regular_expression == True:
            # Get the absolute cursor index from line/index position
            line, index = self.getCursorPosition()
            absolute_position = self.positionFromLineIndex(line, index)
            # Compile the search expression according to the case sensitivity
            if case_sensitive == True:
                compiled_search_re = re.compile(search_text)
            else:
                compiled_search_re = re.compile(search_text, re.IGNORECASE)
            # Search based on the search direction
            if search_forward == True:
                # Regex search from the absolute position to the end for the search expression
                search_result = re.search(
                    compiled_search_re, self.text()[absolute_position:]
                )
                if search_result is not None:
                    # Select the found expression
                    result_start = absolute_position + search_result.start()
                    result_end = result_start + len(search_result.group(0))
                    self.setCursorPosition(0, result_start)
                    self.setSelection(0, result_start, 0, result_end)
                    # Return successful find
                    return data.SearchResult.FOUND
                else:
                    # Begin a new search from the top of the document
                    search_result = re.search(compiled_search_re, self.text())
                    if search_result is not None:
                        # Select the found expression
                        result_start = search_result.start()
                        result_end = result_start + len(search_result.group(0))
                        self.setCursorPosition(0, result_start)
                        self.setSelection(0, result_start, 0, result_end)
                        self.main_form.display.write_to_statusbar(
                            "Reached end of document, started from the top again!"
                        )
                        # Return cycled find
                        return data.SearchResult.CYCLED
                    else:
                        self.main_form.display.write_to_statusbar(
                            "Text was not found!"
                        )
                        return data.SearchResult.NOT_FOUND
            else:
                # Move the cursor one character back when searching backard
                # to not catch the same search result again
                cursor_position = self.get_absolute_cursor_position()
                search_text = self.text()[:cursor_position]
                # Regex search from the absolute position to the end for the search expression
                search_result = [
                    m for m in re.finditer(compiled_search_re, search_text)
                ]
                if search_result != []:
                    # Select the found expression
                    result_start = search_result[-1].start()
                    result_end = search_result[-1].end()
                    self.setCursorPosition(0, result_start)
                    self.setSelection(0, result_start, 0, result_end)
                    # Return successful find
                    return data.SearchResult.FOUND
                else:
                    # Begin a new search from the top of the document
                    search_result = [
                        m for m in re.finditer(compiled_search_re, self.text())
                    ]
                    if search_result != []:
                        # Select the found expression
                        result_start = search_result[-1].start()
                        result_end = search_result[-1].end()
                        self.setCursorPosition(0, result_start)
                        self.setSelection(0, result_start, 0, result_end)
                        self.main_form.display.write_to_statusbar(
                            "Reached end of document, started from the top again!"
                        )
                        # Return cycled find
                        return data.SearchResult.CYCLED
                    else:
                        self.main_form.display.write_to_statusbar(
                            "Text was not found!"
                        )
                        return data.SearchResult.NOT_FOUND
        else:
            # Move the cursor one character back when searching backard
            # to not catch the same search result again
            if search_forward == False:
                line, index = self.getCursorPosition()
                self.setCursorPosition(line, index - 1)
            # "findFirst" is the QScintilla function for finding text in a document
            search_result = self.findFirst(
                search_text,
                False,
                case_sensitive,
                False,
                False,
                forward=search_forward,
            )
            if search_result == False:
                # Try to find text again from the top or at the bottom of
                # the scintilla document, depending on the search direction
                if search_forward == True:
                    s_line = 0
                    s_index = 0
                else:
                    s_line = len(self.line_list) - 1
                    s_index = len(self.text())
                inner_result = self.findFirst(
                    search_text,
                    False,
                    case_sensitive,
                    False,
                    False,
                    forward=search_forward,
                    line=s_line,
                    index=s_index,
                )
                if inner_result == False:
                    self.main_form.display.write_to_statusbar(
                        "Text was not found!"
                    )
                    return data.SearchResult.NOT_FOUND
                else:
                    self.main_form.display.write_to_statusbar(
                        "Reached end of document, started from the other end again!"
                    )
                    focus_entire_found_text()
                    # Return cycled find
                    return data.SearchResult.CYCLED
            else:
                # Found text
                self.main_form.display.write_to_statusbar(
                    'Found text: "' + search_text + '"'
                )
                focus_entire_found_text()
                # Return successful find
                return data.SearchResult.FOUND

    def find_all(
        self,
        search_text,
        case_sensitive=False,
        regular_expression=False,
        text_to_bytes=False,
        whole_words=False,
        text_range=None,
    ):
        """Find all instances of a string and return a list of (line,
        index_start, index_end)"""
        used_text = self.text()
        if text_range is not None:
            fr, to = text_range
            used_text = self.text()[fr:to]
        # Find all instances of the search string and return the list
        matches = functions.index_strings_in_text(
            search_text,
            used_text,
            case_sensitive,
            regular_expression,
            text_to_bytes,
            whole_words,
        )
        return matches

    def find_and_replace(
        self,
        search_text: str,
        replace_text: str,
        case_sensitive: bool = False,
        search_forward: bool = True,
        regular_expression: bool = False,
    ) -> bool:
        """Find next instance of the search string and replace it with the
        replace string."""
        if regular_expression:
            # Check if expression exists in the document
            search_result = self.find_text(
                search_text=search_text,
                case_sensitive=case_sensitive,
                search_forward=search_forward,
                regular_expression=regular_expression,
            )
            if search_result != data.SearchResult.NOT_FOUND:
                if case_sensitive:
                    compiled_search_re = re.compile(search_text)
                else:
                    compiled_search_re = re.compile(search_text, re.IGNORECASE)
                # The search expression is already selected from the find_text function
                found_expression = self.selectedText()
                # Save the found selected text line/index information
                saved_selection = self.getSelection()
                # Replace the search expression with the replace expression
                replacement = re.sub(
                    compiled_search_re, replace_text, found_expression
                )
                # Replace selected text with replace text
                self.replaceSelectedText(replacement)
                # Select the newly replaced text
                # self.main_form.display.display_message_with_type(replacement)
                self.setSelection(
                    saved_selection[0],
                    saved_selection[1],
                    saved_selection[2],
                    saved_selection[1] + len(replacement),
                )
                return True
            else:
                # Search text not found
                self.main_form.display.write_to_statusbar("Text was not found!")
                return False
        else:
            # Check if string exists in the document
            search_result = self.find_text(search_text, case_sensitive)
            if search_result != data.SearchResult.NOT_FOUND:
                # Save the found selected text line/index information
                saved_selection = self.getSelection()
                # Replace selected text with replace text
                self.replaceSelectedText(replace_text)
                # Select the newly replaced text
                self.setSelection(
                    saved_selection[0],
                    saved_selection[1],
                    saved_selection[2],
                    saved_selection[1] + len(replace_text),
                )
                return True
            else:
                # Search text not found
                self.main_form.display.write_to_statusbar("Text was not found!")
                return False
        return False

    def replace_all(
        self,
        search_text: str,
        replace_text: str,
        case_sensitive: bool = False,
        regular_expression: bool = False,
    ) -> None:
        """Replace all occurences of a string in a scintilla document."""
        # Store the current cursor position
        current_position = self.getCursorPosition()
        current_first_line = self.firstVisibleLine()
        # Move cursor to the top of the document, so all the search string instances will be found
        self.setCursorPosition(0, 0)
        # Clear all previous highlights
        self.clear_highlights()
        # Setup the indicator style, the replace indicator is 1
        self.set_indicator("replace")
        # Correct the displayed file name
        if self.save_name is None or self.save_name == "":
            file_name = self._parent.tabText(self._parent.currentIndex())
        else:
            file_name = os.path.basename(self.save_name)
        # Check if there are any instances of the search text in the document
        # based on the regular expression flag
        search_result = None
        if regular_expression:
            # Check case sensitivity for regular expression
            if case_sensitive:
                compiled_search_re = re.compile(search_text)
            else:
                compiled_search_re = re.compile(search_text, re.IGNORECASE)
            search_result = re.search(compiled_search_re, self.text())
        else:
            search_result = self.find_text(search_text, case_sensitive)
        if search_result == data.SearchResult.NOT_FOUND:
            message = "No matches were found in '{:s}'!".format(file_name)
            self.main_form.display.display_message_with_type(
                message, message_type=data.MessageType.WARNING
            )
            return
        # Use the re module to replace the text
        text = self.text()
        matches, replaced_text = functions.replace_and_index(
            input_string=text,
            search_text=search_text,
            replace_text=replace_text,
            case_sensitive=case_sensitive,
            regular_expression=regular_expression,
        )
        # Check if there were any matches or
        # if the search and replace text were equivalent!
        if matches is not None:
            # Replace the text
            self.replace_entire_text(replaced_text)
            # Matches can only be displayed for non-regex functionality
            if regular_expression:
                # Build the list of matches used by the highlight_raw function
                corrected_matches: List[Tuple[int, int, int, int]] = []
                for i in matches:
                    index = self.positionFromLineIndex(i, 0)
                    corrected_matches.append(
                        (
                            0,
                            index,
                            0,
                            index + len(self.text(i)),
                        )
                    )
                # Display the replacements in the REPL tab
                if (
                    len(corrected_matches)
                    < settings.editor["maximum_highlights"]
                ):
                    message = "{:s} replacements:".format(file_name)
                    self.main_form.display.display_message_with_type(
                        message, message_type=data.MessageType.SUCCESS
                    )
                    for match in corrected_matches:
                        line = self.lineIndexFromPosition(match[1])[0] + 1
                        index = self.lineIndexFromPosition(match[1])[1]
                        message = "    replacement made in line:{:d}".format(
                            line
                        )
                        self.main_form.display.display_message_with_type(
                            message, message_type=data.MessageType.SUCCESS
                        )
                else:
                    message = "{:d} replacements made in {:s}!\n".format(
                        len(corrected_matches), file_name
                    )
                    message += "Too many to list individually!"
                    self.main_form.display.display_message_with_type(
                        message, message_type=data.MessageType.WARNING
                    )
                # Highlight and display the line difference between the old and new texts
                # self.set_indicator("replace") (problem see https://forum.embeetle.com/t/highlighting-replaced-text-not-working/1017)
                self.highlight_raw(corrected_matches)
            else:
                # Display the replacements in the REPL tab
                if len(matches) < settings.editor["maximum_highlights"]:
                    message = "{:s} replacements:".format(file_name)
                    self.main_form.display.display_message_with_type(
                        message, message_type=data.MessageType.SUCCESS
                    )
                    for match in matches:
                        line = self.lineIndexFromPosition(match[1])[0] + 1
                        index = self.lineIndexFromPosition(match[1])[1]
                        message = '    replaced "{:s}" in line:{:d} column:{:d}'.format(
                            search_text, line, index
                        )
                        self.main_form.display.display_message_with_type(
                            message, message_type=data.MessageType.SUCCESS
                        )
                else:
                    message = "{:d} replacements made in {:s}!\n".format(
                        len(matches), file_name
                    )
                    message += "Too many to list individually!"
                    self.main_form.display.display_message_with_type(
                        message, message_type=data.MessageType.WARNING
                    )
                # Highlight and display the replaced text
                # self.set_indicator("replace") (problem see https://forum.embeetle.com/t/highlighting-replaced-text-not-working/1017)
                self.highlight_raw(matches)
            # Restore the previous cursor position
            self.setCursorPosition(current_position[0], current_position[1])
            self.setFirstVisibleLine(current_first_line)
        else:
            message = "The search string and replace string are equivalent!\n"
            message += "Change the search/replace string or change the case sensitivity!"
            self.main_form.display.display_message_with_type(
                message, message_type=data.MessageType.ERROR
            )
        return

    def replace_in_selection(
        self,
        search_text: str,
        replace_text: str,
        case_sensitive: bool = False,
        regular_expression: bool = False,
    ) -> None:
        """Replace all occurences of a string in the current selection in the
        scintilla document."""
        # Get the start and end point of the selected text
        start_line, start_index, end_line, end_index = self.getSelection()
        # Get the currently selected text and use the re module to replace the text
        selected_text = self.selectedText()
        replaced_text = functions.regex_replace_text(
            selected_text,
            search_text,
            replace_text,
            case_sensitive,
            regular_expression,
        )
        # Check if any replacements were made
        if replaced_text != selected_text:
            # Put the text back into the selection space and select it again
            self.replaceSelectedText(replaced_text)
            new_end_line = start_line
            new_end_index = start_index + len(bytearray(replaced_text, "utf-8"))
            self.setSelection(
                start_line, start_index, new_end_line, new_end_index
            )
        else:
            message = "No replacements were made!"
            self.main_form.display.display_message_with_type(
                message, message_type=data.MessageType.WARNING
            )
        return

    def replace_entire_text(self, new_text):
        """Replace the entire text of the document."""
        if self.isReadOnly():
            self.setText(new_text)
        else:
            # Select the entire text
            self.selectAll(True)
            # Replace the text with the new
            self.replaceSelectedText(new_text)

    def convert_case(self, uppercase=False):
        """Convert selected text in the scintilla document into the selected
        case letters."""
        # Get the start and end point of the selected text
        start_line, start_index, end_line, end_index = self.getSelection()
        # Get the currently selected text
        selected_text = self.selectedText()
        # Convert it to the selected case
        if uppercase == False:
            selected_text = selected_text.lower()
        else:
            selected_text = selected_text.upper()
        # Replace the selection with the new upercase text
        self.replaceSelectedText(selected_text)
        # Reselect the previously selected text
        self.setSelection(start_line, start_index, end_line, end_index)

    """
    Highligting functions
    """

    def highlight_text(
        self,
        highlight_text,
        case_sensitive=False,
        regular_expression=False,
    ) -> None:
        """Highlight all instances of the selected text with a selected
        colour."""
        # Setup the indicator style, the highlight indicator will be 0
        self.set_indicator("highlight")
        # Get all instances of the text using list comprehension and the re module
        matches = self.find_all(
            search_text=highlight_text,
            case_sensitive=case_sensitive,
            regular_expression=regular_expression,
            text_to_bytes=True,
        )
        # Check if the match list is empty
        if matches:
            # Use the raw highlight function to set the highlight indicators
            self.highlight_raw(matches)
            self.main_form.display.display_message_with_type(
                "{:d} matches highlighted".format(len(matches))
            )
            # Set the cursor to the first highlight
            self.find_text(
                highlight_text, case_sensitive, True, regular_expression
            )
        else:
            self.main_form.display.display_message_with_type(
                "No matches found!", message_type=data.MessageType.WARNING
            )
        return

    def highlight_raw(
        self,
        highlight_list: List[Tuple[int, int, int, int]],
    ) -> None:
        """
        Core highlight function that uses Scintilla messages to style indicators.
        QScintilla's fillIndicatorRange function is to slow for large numbers of
        highlights!
        INFO:   This is done using the scintilla "INDICATORS" described in the official
                scintilla API (http://www.scintilla.org/ScintillaDoc.html#Indicators)

        Items have the form:
            (line_start, index_start, line_end, index_end)
        """
        scintilla_command = qt.QsciScintillaBase.SCI_INDICATORFILLRANGE
        for highlight in highlight_list:
            start = highlight[1]
            length = highlight[3] - start
            self.SendScintilla(scintilla_command, start, length)
        return

    def __highlight_selection(
        self,
        highlight_text,
        case_sensitive=False,
        regular_expression=False,
    ) -> None:
        """Same as the highlight_text function, but adapted for the use with the
        __selection_changed functionality."""
        # Setup the indicator style, the highlight indicator will be 0
        self.set_indicator("selection")
        # Get all instances of the text using list comprehension and the re module
        matches = self.find_all(
            search_text=highlight_text,
            case_sensitive=case_sensitive,
            regular_expression=regular_expression,
            text_to_bytes=True,
            whole_words=True,
        )
        # Check if the match list is empty
        if matches:
            # Use the raw highlight function to set the highlight indicators
            self.highlight_raw(matches)
        return

    def clear_highlights(self):
        """Clear all highlighted text."""
        # Clear the indicators
        for ind in self.indicators:
            self.clearIndicatorRange(
                0, 0, self.lines(), self.lineLength(self.lines() - 1), ind
            )

    def clear_highlight_indicator(self):
        # Clear only the highlight indicator
        self.clearIndicatorRange(
            0,
            0,
            self.lines(),
            self.lineLength(self.lines() - 1),
            self.HIGHLIGHT_INDICATOR,
        )

    def clear_selection_highlights(self):
        # Clear the selection indicators
        self.clearIndicatorRange(
            0,
            0,
            self.lines(),
            self.lineLength(self.lines() - 1),
            self.SELECTION_INDICATOR,
        )

    def clear_symbol_highlights(self):
        # Clear the symbol indicators
        self.clearIndicatorRange(
            0,
            0,
            self.lines(),
            self.lineLength(self.lines() - 1),
            self.SYMBOL_INDICATOR,
        )
        self.clearIndicatorRange(
            0,
            0,
            self.lines(),
            self.lineLength(self.lines() - 1),
            self.SYMBOL_UNDERLINE_INDICATOR,
        )

    def clear_background_selection(self):
        # Clear the symbol indicators
        self.clearIndicatorRange(
            0,
            0,
            self.lines(),
            self.lineLength(self.lines() - 1),
            self.BACKGROUND_SELECTION_INDICATOR,
        )
        self.background_selection = None

    def set_indicator(self, indicator: str) -> None:
        """Select the indicator that will be used for use with Scintilla's
        indicator functionality."""
        if indicator == "symbol":
            self.__set_indicator(
                indicator=self.SYMBOL_INDICATOR,
                fore_color=indicator,
                color_text=True,
            )
        elif indicator == "underline":
            self.__set_indicator(
                indicator=self.SYMBOL_UNDERLINE_INDICATOR,
                fore_color="symbol",
                underline=True,
            )
        elif indicator == "background_selection":
            self.__set_indicator(
                indicator=self.BACKGROUND_SELECTION_INDICATOR,
                fore_color=indicator,
            )
        else:
            indicator_index = self.__get_indicator_index(indicator)
            self.__set_indicator(
                indicator=indicator_index,
                fore_color=indicator,
            )
        return

    def __set_indicator(
        self,
        indicator,
        fore_color,
        color_text=False,
        underline=False,
    ) -> None:
        """Set the indicator settings."""
        if color_text:
            self.indicatorDefine(qt.QsciScintillaBase.INDIC_TEXTFORE, indicator)
        elif underline:
            self.indicatorDefine(qt.QsciScintillaBase.INDIC_PLAIN, indicator)
        else:
            self.indicatorDefine(
                qt.QsciScintillaBase.INDIC_STRAIGHTBOX, indicator
            )
        self.setIndicatorForegroundColor(
            qt.QColor(data.theme["indication"][fore_color]), indicator
        )
        self.SendScintilla(
            qt.QsciScintillaBase.SCI_SETINDICATORCURRENT, indicator
        )
        return

    def __get_indicator_index(self, indicator: str) -> int:
        """
        NOTE: I commented out the indicators that are not used right now.
        """
        if indicator == "highlight":
            return self.HIGHLIGHT_INDICATOR
        elif indicator == "selection":
            return self.SELECTION_INDICATOR
        elif indicator == "replace":
            return self.REPLACE_INDICATOR
        # elif indicator == "find":
        #     return self.FIND_INDICATOR
        elif indicator == "symbol":
            return self.SYMBOL_INDICATOR
        elif indicator == "underline":
            return self.SYMBOL_UNDERLINE_INDICATOR
        # elif indicator == "blink":
        #     return self.BLINK_INDICATOR
        # elif indicator == "error":
        #     return self.ERROR_INDICATOR
        # elif indicator == "warning":
        #     return self.WARNING_INDICATOR
        elif indicator == "background_selection":
            return self.BACKGROUND_SELECTION_INDICATOR
        else:
            raise Exception(f"Unknown indicator: {indicator}")
        return 0

    """
    Various CustomEditor functions
    """

    def check_line_numbering(self, line_number):
        """Check if the line number is in the bounds of the current document and
        return the filtered line number."""
        # Convert the line numbering from the displayed 1-to-n to the array numbering of python 0-to-n
        line_number -= 1
        # Check if the line number is below the index 0
        if line_number < 0:
            line_number = 0
        elif line_number > self.lines() - 1:
            line_number = self.lines() - 1
        return line_number

    def save_document(
        self, saveas=False, last_dir=None, encoding="utf-8", line_ending=None
    ):
        """Save a document to a file."""
        if self.save_name == "" or saveas != False:
            # Tab has an empty directory attribute or "SaveAs" was invoked, select file using the QfileDialog
            file_dialog = qt.QFileDialog
            # Check if the custom editors last browsed dir was previously set
            if self.last_browsed_dir == "" and last_dir is not None:
                self.last_browsed_dir = last_dir
            # Get the filename from the QfileDialog window
            temp_save_name = file_dialog.getSaveFileName(
                self,
                "Save File",
                self.last_browsed_dir + self.save_name,
                "All Files(*)",
            )
            temp_save_name = temp_save_name[0]
            # Check if the user has selected a file
            if temp_save_name == "":
                return
            # Replace back-slashes to forward-slashes on windows
            if os_checker.is_os("windows"):
                temp_save_name = functions.unixify_path(temp_save_name)
            # Save the chosen file name to the document "save_name" attribute
            self.save_name = temp_save_name
        # Update the last browsed directory to the class/instance variable
        self.last_browsed_dir = os.path.dirname(self.save_name)
        # Set the tab name by filtering it out from the QFileDialog result
        self.name = os.path.basename(self.save_name)
        # Change the displayed name of the tab in the basic widget
        self._parent.set_tab_name(self, self.name)
        # Check if a line ending was specified
        if line_ending is None:
            # Write contents of the tab into the specified file
            save_result = functions.write_to_file(
                self.text(), self.save_name, encoding
            )
        else:
            # The line ending has to be a string
            if isinstance(line_ending, str) == False:
                self.main_form.display.display_error(
                    "Line ending has to be a string!"
                )
                return
            else:
                # Correct the line endings if needed
                separator = functions.get_separator(self.text())
                if separator != "\n":
                    self.replace_all(separator, "\n")

                # Convert the text into a list and join it together with the specified line ending
                text_list = self.line_list
                converted_text = line_ending.join(text_list)
                save_result = functions.write_to_file(
                    converted_text, self.save_name, encoding
                )
        # Check result of the functions.write_to_file function
        if save_result == True:
            # Saving has succeded
            self._parent.reset_text_changed(self._parent.indexOf(self))
            # Update the lexer for the document only if the lexer is not set
            if isinstance(self.lexer(), lexers.Text):
                file_type = functions.get_file_type(self.save_name)
                self.choose_lexer(file_type)
            # Update the settings manipulator with the new file
            self.main_form.settings.update_recent_files_list(self.save_name)
        else:
            # Saving has failed
            error_message = "Error while trying to write file to disk:\n"
            error_message += str(save_result)
            self.main_form.display.display_message_with_type(
                error_message, message_type=data.MessageType.ERROR
            )
            self.main_form.display.write_to_statusbar(
                "Saving to file failed, check path and disk space!"
            )

    def refresh_lexer(self):
        """Refresh the current lexer (used by themes)"""
        self.set_theme(data.theme)
        self.lexer().set_theme(data.theme)

    def choose_lexer(self, file_type):
        """Choose the lexer from the file type parameter for the scintilla
        document."""
        # Set the lexer for syntax highlighting according to file type
        self.current_file_type, lexer = lexers.get_lexer_from_file_type(
            file_type
        )
        # Check if a lexer was chosen
        if lexer is not None:
            self.set_lexer(lexer, file_type)
            if isinstance(lexer, lexers.Makefile):
                if settings.editor["makefile_uses_tabs"]:
                    self.setIndentationsUseTabs(True)
                if settings.editor["makefile_whitespace_visible"]:
                    self.setWhitespaceVisibility(
                        qt.QsciScintilla.WhitespaceVisibility.WsVisible
                    )
            # Initialize autocompletions
            self.autocompletion_init()
        else:
            self.main_form.display.display_error(
                "Error while setting the lexer!"
            )

    def clear_lexer(self) -> None:
        """Remove the lexer from the editor."""
        # Try to clean up the threading functionality
        _lexer: qt.QsciLexer = self.lexer()
        if hasattr(_lexer, "terminate_parsing_thread"):
            _lexer.terminate_parsing_thread()
        if isinstance(_lexer, lexers.CustomC):
            _lexer.self_destruct()
        # Destroy the lexer
        if _lexer is not None:
            _lexer.deleteLater()
            _lexer.setParent(None)  # noqa
            self.setLexer(None)
        return

    def set_lexer(self, lexer, file_type):
        """Function that actually sets the lexer."""
        #        wrapped_lexer = lexers.ProxyLexer(lexer, lexer.parent())
        # First clear the lexer
        self.clear_lexer()
        # Save the current file type to a string
        self.current_file_type = file_type.upper()
        # Set the lexer default font family
        lexer.setDefaultFont(data.get_general_font())
        # Set the comment options
        result = lexers.get_comment_style_for_lexer(lexer)
        lexer.open_close_comment_style = result[0]
        lexer.comment_string = result[1]
        lexer.end_comment_string = result[2]
        # Set the lexer for the current scintilla document
        lexer.setParent(self)
        self.setLexer(lexer)
        # Reset the brace matching color
        self.setMatchedBraceBackgroundColor(
            qt.QColor(settings.editor["brace_color"])
        )
        #        # Enable code folding for the file type
        #        self.setFolding(qt.QsciScintilla.FoldStyle.PlainFoldStyle)
        #        self.setFolding(qt.QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        # Special case
        if isinstance(lexer, lexers.CustomC):
            # Set the margin font
            self.setMarginsFont(
                qt.QFont(
                    data.editor_font_name,
                    data.get_general_font_pointsize(),
                    weight=qt.QFont.Weight.Bold,
                )
            )
        # Get the icon according to the file type
        self.current_icon: qt.QIcon = iconfunctions.get_qicon(
            iconfunctions.get_language_icon_relpath(file_type)
        )
        # Update the icon on the parent basic widget
        self.icon_manipulator.update_icon(self)
        # Set the theme
        self.set_theme(data.theme)
        # Update corner icons
        self.icon_manipulator.update_corner_button_icon(self.current_icon)
        self.icon_manipulator.update_icon(self)

    def clear_editor(self):
        """Clear the text from the scintilla document."""
        self.SendScintilla(qt.QsciScintillaBase.SCI_CLEARALL)

    def tabs_to_spaces(self):
        """Convert all tab(\t) characters to spaces."""
        spaces = " " * settings.editor["tab_width"]
        self.setText(self.text().replace("\t", spaces))

    def undo_all(self):
        """Repeat undo until there is something to undo."""
        while self.isUndoAvailable() == True:
            self.undo()

    def redo_all(self):
        """Repeat redo until there is something to redo."""
        while self.isRedoAvailable() == True:
            self.redo()

    def update_margin(self):
        """Update margin width according to the number of lines in the
        document."""
        line_count = self.lines()
        # Set line and bookmark margin width
        self.setMarginWidth(self.MARGINS["line"], str(line_count) + "0")
        self.setMarginWidth(self.MARGINS["symbol"], "99")
        if data.debugging_active:
            self.setMarginWidth(self.MARGINS["debug"], "99")
        else:
            self.setMarginWidth(self.MARGINS["debug"], 0)
        # Set the folding margin width
        #        self.setMarginWidth(self.MARGINS["fold"], "99")
        self.setMarginWidth(self.MARGINS["fold"], 0)

    def update_statusbar_status(self, read_only_highlighted=True):
        """Show relevant editor data in the statusbar."""
        cursor_line, cursor_column = self.getCursorPosition()
        position = self.positionFromLineIndex(cursor_line, cursor_column)
        item_list = []
        # Lexer
        if self.lexer() is not None:
            item_list.append(self.lexer().language())
        else:
            return
        # Cursor line/index
        if cursor_line is None and cursor_column is None:
            cursor_line = "X"
            cursor_column = "X"
            position = "X"
        else:
            cursor_line += 1
            cursor_column += 1
        text_line_index = "Line: {} Column: {} Index: {}".format(
            cursor_line, cursor_column, position
        )
        item_list.append(text_line_index)
        # Encoding
        encoding = "UTF-8"
        item_list.append(encoding)
        # Readonly mode check
        if self.isReadOnly():
            if read_only_highlighted:
                item_list.append('<font color="#ff0000">Read-Only</font>')
            else:
                item_list.append("Read-Only")
        else:
            # Overwrite mode
            write_mode = "Insert-Mode"
            if self.overwriteMode():
                write_mode = "Overwrite-Mode"
            item_list.append(write_mode)
        # Special file type
        if self.file_location != data.FileType.Standard:
            item_list.append(data.filelocations[self.file_location])
        # Display the list
        if self.main_form is not None:
            try:
                self.main_form.display.statusbar_show(" | ".join(item_list))
            except:
                pass

    def edge_marker_show(self):
        """Show the marker at the specified column number."""
        # Set the marker color to blue
        marker_color = qt.QColor(settings.editor["edge_marker_color"])
        # Set the column number where the marker will be shown
        marker_column = settings.editor["edge_marker_column"]
        # Set the marker options
        self.setEdgeColor(marker_color)
        self.setEdgeColumn(marker_column)
        self.setEdgeMode(qt.QsciScintilla.EdgeMode.EdgeLine)

    def edge_marker_hide(self):
        """Hide the column marker."""
        self.setEdgeMode(qt.QsciScintilla.EdgeMode.EdgeNone)

    def is_file_content_different(self):
        """Check the content of the file on disk with the editor content and see
        if it matches."""
        try:
            if os.path.isfile(self.save_name):
                with open(
                    self.save_name, "r", encoding="utf-8", errors="replace"
                ) as file:
                    text = file.read()
                return text != self.text()
        except:
            traceback.print_exc()
        return False

    def reload_file(self):
        """Reload current document from disk."""
        # Check if file was loaded from or saved to disk
        if self.save_name == "":
            self.main_form.display.display_warning(
                "Document has no file on disk!"
            )
            self.main_form.display.write_to_statusbar(
                "Document has no file on disk!", 3000
            )
            return
        # Check the file status
        if self.save_status == data.FileStatus.MODIFIED:
            # Display the close notification
            reload_message = (
                "Document '{}' has been modified!\n"
                + "Reload it from disk anyway?"
            ).format(self.name)
            reply = gui.dialogs.popupdialog.PopupDialog.question(reload_message)
            if reply == qt.QMessageBox.StandardButton.No:
                # Cancel tab file reloading
                return
        # Check if the name of the document is valid
        if self.name == "" or self.name is None:
            self.main_form.display.display_warning(
                "Reloading file '{}'\n failed".format(self.save_name)
                + "because it doesn't have a proper name!"
            )
            return
        # Open the file and read the contents
        try:
            disk_file_text = functions.read_file_to_string(self.save_name)
        except Exception as ex:
            self.main_form.display.display_error(
                "Error reloading file: {}".format(str(ex))
            )
            self.main_form.display.write_to_statusbar(
                "Error reloading file!", 3000
            )
            return
        # Save the current cursor position
        temp_position = self.getCursorPosition()
        temp_first_line = self.firstVisibleLine()
        # Reload the file
        self.replace_entire_text(disk_file_text)
        # Restore saved cursor position
        self.setCursorPosition(*temp_position)
        self.setFirstVisibleLine(temp_first_line)
        # Reset the '*' in the tab and set save status
        self.save_status = data.FileStatus.OK
        index = self._parent.indexOf(self)
        if "*" in self._parent.tabText(index):
            self._parent.setTabText(index, self.name)
        # Resend the file to the source analyzer
        if not self.isReadOnly():
            basename = os.path.basename(self.save_name)
            if basename not in data.FILE_RELOAD_EXCLUDES:
                self.__sai.reload_file(self.save_name)
        # Display success
        self.main_form.display.display_message(
            f"File '{self.name}' successfully reloaded from disk."
        )

    def copy_self(self, new_editor):
        """Copy everything needed from self to the destination editor."""
        if new_editor is None:
            return
        # Copy all of the settings
        lexer_copy = self.lexer().__class__(new_editor)
        new_editor.set_lexer(lexer_copy, self.current_file_type)
        new_editor.setText(self.text())

    def toggle_wordwrap(self):
        """Toggle word wrap on/off."""
        if self.wrapMode() == qt.QsciScintilla.WrapMode.WrapNone:
            self.set_wordwrap(True)
        else:
            self.set_wordwrap(False)

    def set_wordwrap(self, state):
        """
        Wrap modes:
            qt.QsciScintilla.WrapMode.WrapNone - Lines are not wrapped.
            qt.QsciScintilla.WrapMode.WrapWord - Lines are wrapped at word boundaries.
            qt.QsciScintilla.WrapMode.WrapCharacter - Lines are wrapped at character boundaries.
            qt.QsciScintilla.WrapMode.WrapWhitespace - Lines are wrapped at whitespace boundaries.
        Wrap visual flags:
            qt.QsciScintilla.WrapVisualFlag.WrapFlagNone - No wrap flag is displayed.
            qt.QsciScintilla.WrapVisualFlag.WrapFlagByText - A wrap flag is displayed by the text.
            qt.QsciScintilla.WrapVisualFlag.WrapFlagByBorder - A wrap flag is displayed by the border.
            qt.QsciScintilla.WrapVisualFlag.WrapFlagInMargin - A wrap flag is displayed in the line number margin.
        Wrap indentation:
            qt.QsciScintilla.WrapIndentMode.WrapIndentFixed - Wrapped sub-lines are indented by the amount set by setWrapVisualFlags().
            qt.QsciScintilla.WrapIndentMode.WrapIndentSame - Wrapped sub-lines are indented by the same amount as the first sub-line.
            qt.QsciScintilla.WrapIndentMode.WrapIndentIndented - Wrapped sub-lines are indented by the same amount as the first sub-line plus one more level of indentation.
        """
        if state:
            self.setWrapMode(qt.QsciScintilla.WrapMode.WrapWord)
            self.setWrapVisualFlags(
                qt.QsciScintilla.WrapVisualFlag.WrapFlagByText
            )
            self.setWrapIndentMode(
                qt.QsciScintilla.WrapIndentMode.WrapIndentSame
            )
        else:
            self.setWrapMode(qt.QsciScintilla.WrapMode.WrapNone)
            self.setWrapVisualFlags(
                qt.QsciScintilla.WrapVisualFlag.WrapFlagNone
            )

    def set_cursor_line_visibility(self, new_state: bool) -> None:
        """"""
        self.setCaretLineVisible(new_state)
        if new_state:
            self.setCaretLineBackgroundColor(
                qt.QColor(data.theme["cursor_line_overlay"])
            )
            if data.theme["cursor_line_frame"]:
                self.setCaretLineFrameWidth(2)
        return

    def toggle_cursor_line_highlighting(self) -> None:
        """"""
        new_state = bool(not self.SendScintilla(self.SCI_GETCARETLINEVISIBLE))
        self.set_cursor_line_visibility(new_state)
        if new_state:
            self.main_form.display.display_message_with_type(
                "Cursor line highlighted", message_type=data.MessageType.WARNING
            )
        else:
            self.main_form.display.display_message_with_type(
                "Cursor line not highlighted",
                message_type=data.MessageType.WARNING,
            )
        return

    def copy(self):
        line_from, index_from, line_to, index_to = self.getSelection()
        if (line_from, index_from, line_to, index_to) != (-1, -1, -1, -1):
            super().copy()
            fvl = self.firstVisibleLine()
            self.setCursorPosition(line_to, index_to)
            self.setFirstVisibleLine(fvl)

    """
    Debugger functionality
    """
    debugger_marker_cache_position = {}
    debugger_marker_cache_breakpoint = {}

    @staticmethod
    def debugger_clear_position_marker():
        for k in list(CustomEditor.debugger_marker_cache_position.keys()):
            try:
                editor = CustomEditor.debugger_marker_cache_position[k][
                    "editor"
                ]
                editor.markerDeleteAll(
                    CustomEditor.MARKERS["debugging-position"]["number"]
                )
            except:
                print(
                    "[CustomEditor] Editor disposed, skipping marker deletion!"
                )
            CustomEditor.debugger_marker_cache_position.pop(k)

    def debugger_show_position_marker(self, line):
        # Clear previous
        CustomEditor.debugger_clear_position_marker()

        # Add current
        scintilla_line = line - 1
        handle = self.markerAdd(scintilla_line, self.debugging_position_marker)
        CustomEditor.debugger_marker_cache_position[handle] = {
            "handle": handle,
            "line": line,
            "file": self.save_name,
            "editor": self,
        }

    def debugger_breakpoint_insert(self, line, number):
        scintilla_line = line
        handle = self.markerAdd(
            scintilla_line, self.debugging_breakpoint_marker
        )
        CustomEditor.debugger_marker_cache_breakpoint[handle] = {
            "handle": handle,
            "number": number,
            "line": line,
            "file": self.save_name,
            "editor": self,
        }

    def debugger_breakpoint_delete(self, line, number):
        scintilla_line = line
        self.markerDelete(scintilla_line, self.debugging_breakpoint_marker)
        delete_handle = None
        for k, v in CustomEditor.debugger_marker_cache_breakpoint.items():
            if (
                v["line"] == line
                and v["number"] == number
                and v["editor"] == self
            ):
                delete_handle = k
                break
        if delete_handle is not None:
            CustomEditor.debugger_marker_cache_breakpoint.pop(delete_handle)

    @staticmethod
    def debugger_breakpoint_delete_all():
        for k, v in CustomEditor.debugger_marker_cache_breakpoint.items():
            try:
                editor = v["editor"]
                editor.markerDeleteHandle(k)
            except:
                # traceback.print_exc()
                pass
        for k in list(CustomEditor.debugger_marker_cache_breakpoint.keys()):
            try:
                CustomEditor.debugger_marker_cache_breakpoint.pop(k)
            except:
                # traceback.print_exc()
                pass

    """
    CustomEditor autocompletion functions
    """

    def autocompletion_init(self):
        # API initialization
        if hasattr(self, "__autocomplete_api"):
            self.__autocomplete_api.clear()
            self.__autocomplete_api.apiPreparationFinished.disconnect()
            self.__autocomplete_api = None
        self.__autocomplete_api = qt.QsciAPIs(self.lexer())
        self.__autocomplete_api.apiPreparationFinished.connect(
            self.__autocompletion_show
        )
        # Initialize autocompletion images
        self.__autocomplete_images: dict[str, qt.QPixmap] = {
            "base": iconfunctions.get_qpixmap(
                "icons/symbols/symbol_kind/type.png"
            )
        }
        # Create images and reverse dictionary
        count = 0
        self.__autocomplete_image_lookup = {}
        for name, pixmap in self.__autocomplete_images.items():
            scaled_pixmap = pixmap.scaled(
                qt.create_qsize(
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                )
            )
            self.registerImage(count, scaled_pixmap)
            self.__autocomplete_image_lookup[name] = count
            count += 1

    def autocompletion_enable(self):
        """Enable the CustomEditor autocompletions."""
        # Set state
        self.__autocompletion_enabled = True
        # Set type
        self.setAutoCompletionThreshold(-1)
        # Set the source from where the autocompletions will be fetched
        self.setAutoCompletionSource(
            qt.QsciScintilla.AutoCompletionSource.AcsAPIs
        )
        # Set autocompletion case sensitivity
        self.setAutoCompletionCaseSensitivity(False)

    def autocompletion_disable(self):
        """Disable the CustomEditor autocompletions."""
        # Set state
        self.__autocompletion_enabled = False
        self.setAutoCompletionThreshold(-1)

    def set_autocompletion(self, state):
        if state:
            self.autocompletion_enable()
        else:
            self.autocompletion_disable()

    def toggle_autocompletions(self):
        """Toggle autocompletions for the CustomEditor."""
        # Initilize the document name for displaying
        if self.save_name is None or self.save_name == "":
            document_name = self._parent.tabText(self._parent.currentIndex())
        else:
            document_name = os.path.basename(self.save_name)
        # Check the autocompletion source
        if (
            self.autoCompletionSource()
            == qt.QsciScintilla.AutoCompletionSource.AcsAPIs
        ):
            self.autocompletion_disable()
        else:
            self.autocompletion_enable()

    def __autocompletion_execute(self) -> None:
        line_number, index = self.getCursorPosition()
        position: int = self.positionFromLineIndex(line_number, index)
        context: str = self.text(position - 1000, position)
        result = self.__sai.get_completions(self.save_name, position, context)
        if result is not None:
            insert_position, completions = result
            self.__autocomplete_api.clear()
            if len(completions) > 0:
                for c in completions:
                    self.__autocomplete_api.add(c + "?0")
                self.__autocomplete_api.prepare()

    def __autocompletion_show(self):
        self.autoCompleteFromAPIs()

    def __zoom_changed(self):
        new_zoom_factor = self.SendScintilla(self.SCI_GETZOOM)
        settings.editor["zoom_factor"] = new_zoom_factor
        # The below line also automatically stores all settings without restyling
        components.thesquid.TheSquid.update_options_on_all_editors()

    """
    Click & jump
    """

    def click_and_jump(self):
        if not self.is_valid_file():
            return
        display = self.main_form.display.display_message
        warning = self.main_form.display.display_warning
        line, index = self.getCursorPosition()
        offset = self.positionFromLineIndex(line, index)
        click_global_position = qt.QCursor.pos()
        if not self.__sai.is_engine_on():
            self.main_form.display.display_warning(
                "Clang engine not running! Click&Jump cannot work!"
            )
            return
        symbol = self.__sai.get_entity_data(self.save_name, offset)
        if symbol:

            def create_symbol_popup():
                self.main_form.symbol_popup.generate_symbol_information(symbol)
                self.main_form.symbol_popup.display_at_position(
                    click_global_position
                )

            if isinstance(symbol, str):
                path = symbol
                self.main_form.open_file(path)
            else:
                defs = self.__sai.get_definitions(symbol)
                if len(defs) > 1:
                    # Multiple definitions
                    create_symbol_popup()

                elif len(defs) == 1:
                    # One definition
                    d = defs[0]
                    path = functions.unixify_path(d.file.path)
                    if not os.path.isfile(path):
                        message = f"Definition location is not a file: '{d.file.path}'"
                        self.main_form.display.display_error(message)
                        return
                    begin = d.begin_offset
                    end = d.end_offset
                    self.main_form.open_file(path)
                    editor = self.main_form.get_tab_by_save_name(path)
                    editor.goto_index(begin)

                else:
                    decls = symbol.declarations
                    if len(decls) > 1:
                        # Multiple declarations
                        create_symbol_popup()

                    elif len(decls) == 1:
                        # One declaration
                        d = decls[0]
                        path = functions.unixify_path(d.file.path)
                        if not os.path.isfile(path):
                            message = f"Declaration location is not a file: '{d.file.path}'"
                            self.main_form.display.display_error(message)
                            return
                        begin = d.begin_offset
                        end = d.end_offset
                        self.main_form.open_file(path)
                        editor = self.main_form.get_tab_by_save_name(path)
                        editor.goto_index(begin)

                    else:
                        message = (
                            f"I don't know what's going on, but symbol '{symbol.name}'"
                            "has neither any definitions, nor declarations!"
                        )
                        self.main_form.display.display_error(message)

        else:
            display("Nothing found!")


class Autocompletion(qt.QObject):
    pass


class Bookmarks:
    """Bookmark functionality."""

    def __init__(self, parent):
        """Initialization of the Editing object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent

    def toggle(self):
        """Add/Remove a bookmark at the current line."""
        # Get the cursor line position
        current_line = self._parent.getCursorPosition()[0] + 1
        # Toggle the bookmark
        self.toggle_at_line(current_line)

    def toggle_at_line(self, line):
        """Toggle a bookmarks at the specified line (Line indexing has to be
        1..lines)"""
        # MarkerAdd function needs the standard line indexing
        scintilla_line = line - 1
        # Check if the line is already bookmarked
        bookmarks: gui.forms.mainwindow.MainWindow.Bookmarks = (
            self._parent.main_form.bookmarks
        )
        if bookmarks.check(self._parent, line) is None:
            new_marker_index = bookmarks.add(self._parent, line)
            if new_marker_index is not None:
                handle = self._parent.markerAdd(
                    scintilla_line, self._parent.bookmark_marker
                )
                self._parent.main_form.bookmarks.marks[new_marker_index][
                    "handle"
                ] = handle
        else:
            self._parent.main_form.bookmarks.remove_by_reference(
                self._parent, line
            )
            self._parent.markerDelete(
                scintilla_line, self._parent.bookmark_marker
            )

    def add_marker_at_line(self, line):
        # MarkerAdd function needs the standard line indexing
        scintilla_line = line - 1
        handle = self._parent.markerAdd(
            scintilla_line, self._parent.bookmark_marker
        )
        return handle

    def remove_marker_at_line(self, line):
        # MarkerAdd function needs the standard line indexing
        scintilla_line = line - 1
        self._parent.markerDelete(scintilla_line, self._parent.bookmark_marker)


class Keyboard:
    """Keyboard command assignment, ...

    Relevant Scintilla items:
        SCI_ASSIGNCMDKEY(int keyDefinition, int sciCommand)
        SCI_CLEARCMDKEY(int keyDefinition)
        SCI_CLEARALLCMDKEYS
        SCI_NULL
    """

    _parent = None
    # GNU/linux and windows bindings copied from Scintila source 'KeyMap.cxx'
    bindings = None
    scintilla_keys = None
    valid_modifiers = None
    custom_shortcuts = None

    def init_bindings(self):
        self.bindings = {
            settings.keys["editor"][
                "linedown"
            ]: qt.QsciScintillaBase.SCI_LINEDOWN,
            settings.keys["editor"][
                "linedownextend"
            ]: qt.QsciScintillaBase.SCI_LINEDOWNEXTEND,
            settings.keys["editor"][
                "linescrolldown"
            ]: qt.QsciScintillaBase.SCI_LINESCROLLDOWN,
            settings.keys["editor"][
                "linedownrectextend"
            ]: qt.QsciScintillaBase.SCI_LINEDOWNRECTEXTEND,
            settings.keys["editor"]["lineup"]: qt.QsciScintillaBase.SCI_LINEUP,
            settings.keys["editor"][
                "lineupextend"
            ]: qt.QsciScintillaBase.SCI_LINEUPEXTEND,
            settings.keys["editor"][
                "linescrollup"
            ]: qt.QsciScintillaBase.SCI_LINESCROLLUP,
            settings.keys["editor"][
                "lineuprectextend"
            ]: qt.QsciScintillaBase.SCI_LINEUPRECTEXTEND,
            settings.keys["editor"]["paraup"]: qt.QsciScintillaBase.SCI_PARAUP,
            settings.keys["editor"][
                "paraupextend"
            ]: qt.QsciScintillaBase.SCI_PARAUPEXTEND,
            settings.keys["editor"][
                "paradown"
            ]: qt.QsciScintillaBase.SCI_PARADOWN,
            settings.keys["editor"][
                "paradownextend"
            ]: qt.QsciScintillaBase.SCI_PARADOWNEXTEND,
            settings.keys["editor"][
                "charleft"
            ]: qt.QsciScintillaBase.SCI_CHARLEFT,
            settings.keys["editor"][
                "charleftextend"
            ]: qt.QsciScintillaBase.SCI_CHARLEFTEXTEND,
            settings.keys["editor"][
                "wordleft"
            ]: qt.QsciScintillaBase.SCI_WORDLEFT,
            settings.keys["editor"][
                "wordleftextend"
            ]: qt.QsciScintillaBase.SCI_WORDLEFTEXTEND,
            settings.keys["editor"][
                "charleftrectextend"
            ]: qt.QsciScintillaBase.SCI_CHARLEFTRECTEXTEND,
            settings.keys["editor"][
                "charright"
            ]: qt.QsciScintillaBase.SCI_CHARRIGHT,
            settings.keys["editor"][
                "charrightextend"
            ]: qt.QsciScintillaBase.SCI_CHARRIGHTEXTEND,
            settings.keys["editor"][
                "wordright"
            ]: qt.QsciScintillaBase.SCI_WORDRIGHT,
            settings.keys["editor"][
                "wordrightextend"
            ]: qt.QsciScintillaBase.SCI_WORDRIGHTEXTEND,
            settings.keys["editor"][
                "charrightrectextend"
            ]: qt.QsciScintillaBase.SCI_CHARRIGHTRECTEXTEND,
            settings.keys["editor"][
                "wordpartleft"
            ]: qt.QsciScintillaBase.SCI_WORDPARTLEFT,
            settings.keys["editor"][
                "wordpartleftextend"
            ]: qt.QsciScintillaBase.SCI_WORDPARTLEFTEXTEND,
            settings.keys["editor"][
                "wordpartright"
            ]: qt.QsciScintillaBase.SCI_WORDPARTRIGHT,
            settings.keys["editor"][
                "wordpartrightextend"
            ]: qt.QsciScintillaBase.SCI_WORDPARTRIGHTEXTEND,
            settings.keys["editor"]["vchome"]: qt.QsciScintillaBase.SCI_VCHOME,
            settings.keys["editor"][
                "vchomeextend"
            ]: qt.QsciScintillaBase.SCI_VCHOMEEXTEND,
            settings.keys["editor"][
                "go_to_start"
            ]: qt.QsciScintillaBase.SCI_DOCUMENTSTART,
            settings.keys["editor"][
                "select_to_start"
            ]: qt.QsciScintillaBase.SCI_DOCUMENTSTARTEXTEND,
            settings.keys["editor"][
                "homedisplay"
            ]: qt.QsciScintillaBase.SCI_HOMEDISPLAY,
            settings.keys["editor"][
                "vchomerectextend"
            ]: qt.QsciScintillaBase.SCI_VCHOMERECTEXTEND,
            settings.keys["editor"][
                "lineend"
            ]: qt.QsciScintillaBase.SCI_LINEEND,
            settings.keys["editor"][
                "lineendextend"
            ]: qt.QsciScintillaBase.SCI_LINEENDEXTEND,
            settings.keys["editor"][
                "go_to_end"
            ]: qt.QsciScintillaBase.SCI_DOCUMENTEND,
            settings.keys["editor"][
                "select_to_end"
            ]: qt.QsciScintillaBase.SCI_DOCUMENTENDEXTEND,
            settings.keys["editor"][
                "lineenddisplay"
            ]: qt.QsciScintillaBase.SCI_LINEENDDISPLAY,
            settings.keys["editor"][
                "lineendrectextend"
            ]: qt.QsciScintillaBase.SCI_LINEENDRECTEXTEND,
            settings.keys["editor"][
                "scroll_up"
            ]: qt.QsciScintillaBase.SCI_PAGEUP,
            settings.keys["editor"][
                "select_page_up"
            ]: qt.QsciScintillaBase.SCI_PAGEUPEXTEND,
            settings.keys["editor"][
                "pageuprectextend"
            ]: qt.QsciScintillaBase.SCI_PAGEUPRECTEXTEND,
            settings.keys["editor"][
                "scroll_down"
            ]: qt.QsciScintillaBase.SCI_PAGEDOWN,
            settings.keys["editor"][
                "select_page_down"
            ]: qt.QsciScintillaBase.SCI_PAGEDOWNEXTEND,
            settings.keys["editor"][
                "pagedownrectextend"
            ]: qt.QsciScintillaBase.SCI_PAGEDOWNRECTEXTEND,
            settings.keys["editor"]["clear"]: qt.QsciScintillaBase.SCI_CLEAR,
            settings.keys["editor"][
                "delete_end_of_word"
            ]: qt.QsciScintillaBase.SCI_DELWORDRIGHT,
            settings.keys["editor"][
                "delete_end_of_line"
            ]: qt.QsciScintillaBase.SCI_DELLINERIGHT,
            settings.keys["editor"][
                "edittoggleovertype"
            ]: qt.QsciScintillaBase.SCI_EDITTOGGLEOVERTYPE,
            settings.keys["editor"]["cancel"]: qt.QsciScintillaBase.SCI_CANCEL,
            settings.keys["editor"][
                "deleteback"
            ]: qt.QsciScintillaBase.SCI_DELETEBACK,
            settings.keys["editor"][
                "deleteback_word"
            ]: qt.QsciScintillaBase.SCI_DELETEBACK,
            settings.keys["editor"][
                "delete_start_of_word"
            ]: qt.QsciScintillaBase.SCI_DELWORDLEFT,
            settings.keys["editor"][
                "delete_start_of_line"
            ]: qt.QsciScintillaBase.SCI_DELLINELEFT,
            settings.keys["editor"]["undo"]: qt.QsciScintillaBase.SCI_UNDO,
            settings.keys["editor"]["redo"]: qt.QsciScintillaBase.SCI_REDO,
            settings.keys["editor"]["cut"]: qt.QsciScintillaBase.SCI_CUT,
            #                settings.keys['editor']['copy'] : qt.QsciScintillaBase.SCI_COPY,
            settings.keys["editor"]["paste"]: qt.QsciScintillaBase.SCI_PASTE,
            settings.keys["editor"][
                "select_all"
            ]: qt.QsciScintillaBase.SCI_SELECTALL,
            settings.keys["editor"]["indent"]: qt.QsciScintillaBase.SCI_TAB,
            settings.keys["editor"][
                "unindent"
            ]: qt.QsciScintillaBase.SCI_BACKTAB,
            settings.keys["editor"][
                "newline"
            ]: qt.QsciScintillaBase.SCI_NEWLINE,
            settings.keys["editor"][
                "newline2"
            ]: qt.QsciScintillaBase.SCI_NEWLINE,
            settings.keys["editor"]["zoomin"]: qt.QsciScintillaBase.SCI_ZOOMIN,
            settings.keys["editor"][
                "zoomout"
            ]: qt.QsciScintillaBase.SCI_ZOOMOUT,
            settings.keys["editor"][
                "setzoom"
            ]: qt.QsciScintillaBase.SCI_SETZOOM,
            settings.keys["editor"][
                "line_cut"
            ]: qt.QsciScintillaBase.SCI_LINECUT,
            settings.keys["editor"][
                "line_delete"
            ]: qt.QsciScintillaBase.SCI_LINEDELETE,
            settings.keys["editor"][
                "line_copy"
            ]: qt.QsciScintillaBase.SCI_LINECOPY,
            settings.keys["editor"][
                "line_transpose"
            ]: qt.QsciScintillaBase.SCI_LINETRANSPOSE,
            settings.keys["editor"][
                "line_selection_duplicate"
            ]: qt.QsciScintillaBase.SCI_SELECTIONDUPLICATE,
            settings.keys["editor"][
                "lowercase"
            ]: qt.QsciScintillaBase.SCI_LOWERCASE,
            settings.keys["editor"][
                "uppercase"
            ]: qt.QsciScintillaBase.SCI_UPPERCASE,
        }
        self.scintilla_keys = {
            "down": qt.QsciScintillaBase.SCK_DOWN,
            "up": qt.QsciScintillaBase.SCK_UP,
            "left": qt.QsciScintillaBase.SCK_LEFT,
            "right": qt.QsciScintillaBase.SCK_RIGHT,
            "home": qt.QsciScintillaBase.SCK_HOME,
            "end": qt.QsciScintillaBase.SCK_END,
            "pageup": qt.QsciScintillaBase.SCK_PRIOR,
            "pagedown": qt.QsciScintillaBase.SCK_NEXT,
            "delete": qt.QsciScintillaBase.SCK_DELETE,
            "insert": qt.QsciScintillaBase.SCK_INSERT,
            "escape": qt.QsciScintillaBase.SCK_ESCAPE,
            "backspace": qt.QsciScintillaBase.SCK_BACK,
            "tab": qt.QsciScintillaBase.SCK_TAB,
            "return": qt.QsciScintillaBase.SCK_RETURN,
            "add": ord("+"),  # qt.QsciScintillaBase.SCK_ADD,
            "subtract": ord("-"),  # qt.QsciScintillaBase.SCK_SUBTRACT,
            "divide": ord("/"),  # qt.QsciScintillaBase.SCK_DIVIDE,
            "win": qt.QsciScintillaBase.SCK_WIN,
            "rwin": qt.QsciScintillaBase.SCK_RWIN,
            "menu": qt.QsciScintillaBase.SCK_MENU,
        }
        self.valid_modifiers = [
            qt.QsciScintillaBase.SCMOD_NORM,
            qt.QsciScintillaBase.SCMOD_SHIFT,
            qt.QsciScintillaBase.SCMOD_CTRL,
            qt.QsciScintillaBase.SCMOD_ALT,
            qt.QsciScintillaBase.SCMOD_SUPER,
            qt.QsciScintillaBase.SCMOD_META,
        ]
        self.custom_shortcuts = {
            settings.keys["editor"]["copy"]: self._parent.copy,
        }

    def __init__(self, parent):
        """Initialization of the Keyboard object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Assign keyboard commands
        self.reassign_keyboard_bindings()

    def reassign_keyboard_bindings(self):
        self.init_bindings()
        self.clear_all_keys()
        bindings = self.bindings
        set_key_combination = self.set_key_combination
        for keys in bindings:
            if keys.strip() == "":
                continue
            set_key_combination(keys, bindings[keys])

    def _parse_key_string(self, key_string):
        """Parse a '+' delimited string for a key combination."""
        split_keys = key_string.replace(" ", "").lower().split("+")
        if "++" in key_string:
            split_keys.append("+")
            split_keys = [x for x in split_keys if x.strip() != ""]
        # Check for to many keys in binding
        if len(split_keys) > 4:
            raise ValueError("Too many items in key string!")
        # Parse the items
        modifiers = []
        key_combination = 0
        if "ctrl" in split_keys:
            modifiers.append(qt.QsciScintillaBase.SCMOD_CTRL)
            split_keys.remove("ctrl")
        if "alt" in split_keys:
            modifiers.append(qt.QsciScintillaBase.SCMOD_ALT)
            split_keys.remove("alt")
        if "shift" in split_keys:
            modifiers.append(qt.QsciScintillaBase.SCMOD_SHIFT)
            split_keys.remove("shift")
        if "meta" in split_keys:
            modifiers.append(qt.QsciScintillaBase.SCMOD_META)
            split_keys.remove("meta")
        base_key = split_keys[0]
        if len(split_keys) == 0:
            raise ValueError("Key string has to have a base character!")
        if len(base_key) != 1:
            if base_key in self.scintilla_keys.keys():
                key_combination = self.scintilla_keys[base_key]
            else:
                raise ValueError(
                    "Unknown base key: '{}' (key string: '{}')".format(
                        base_key, key_string
                    )
                )
        else:
            key_combination = ord(base_key.upper())
        if modifiers != []:
            for m in modifiers:
                key_combination += m << 16
        return key_combination

    def _check_keys(self, key, modifier=None):
        """Check the validity of the key and modifier."""
        if isinstance(key, str) == True:
            if len(key) != 1:
                if modifier is not None:
                    raise ValueError(
                        "modifier argument has to be 'None' with a key string!"
                    )
                # key argument is going to be parsed as a combination
                key = self._parse_key_string(key)
            else:
                if key in self.scintilla_keys:
                    key = self.scintilla_keys[key]
                else:
                    key = ord(key)
        if modifier is None:
            key_combination = key
        else:
            if not (modifier in self.valid_modifiers):
                raise ValueError(
                    "The keyboard modifier is not valid: {}".format(modifier)
                )
            key_combination = key + (modifier << 16)
        return key_combination

    def clear_all_keys(self):
        """Clear all mappings from the internal Scintilla mapping table."""
        self._parent.standardCommands().clearKeys()
        self._parent.standardCommands().clearAlternateKeys()

    def clear_key_combination(self, key, modifier=None):
        """Clear the key combination from the internal Scintilla Mapping Raw
        example of clearing the CTRL+X (Cut text function) combination:
        cmain.SendScintilla( qt.QsciScintillaBase.SCI_CLEARCMDKEY,

        ord('X') + (qt.QsciScintillaBase.SCMOD_CTRL << 16) )
        """
        try:
            key_combination = self._check_keys(key, modifier)
        except Exception as ex:
            self._parent.main_form.display.display_error(str(ex))
            return
        self._parent.SendScintilla(
            qt.QsciScintillaBase.SCI_CLEARCMDKEY, key_combination
        )

    def set_key_combination(self, key, command, modifier=None):
        """Assign a key combination to a command.

        Parameters:
            key - character or key string combination
            command - Scintilla command that will execute on the key combination
            modifier - Ctrl, Alt, ...
        Raw example of assigning CTRL+D to the Cut function:
            cmain.SendScintilla(
                qt.QsciScintillaBase.SCI_ASSIGNCMDKEY,
                ord('D') + (qt.QsciScintillaBase.SCMOD_CTRL << 16),
                qt.QsciScintillaBase.SCI_CUT
            )
        """
        try:
            key_combination = self._check_keys(key, modifier)
        except Exception as ex:
            self._parent.main_form.display.display_error(str(ex))
            return
        self._parent.SendScintilla(
            qt.QsciScintillaBase.SCI_ASSIGNCMDKEY, key_combination, command
        )


class DiagnosticsHandler:
    """Handler for showing/hiding diagnostic messages in the editor."""

    _parent = None
    storage = None

    def __init__(self, parent):
        self._parent = parent
        self.storage = {}
        self.storage["errors"] = {}
        self.storage["fatals"] = {}
        self.storage["warnings"] = {}

    def __set_marker(self, action, line, marker_type):
        # MarkerAdd function needs the standard line indexing
        scintilla_line = line - 1
        # Get marker from name
        marker = None
        if marker_type == "fatal":
            marker = self._parent.fatal_marker
        elif marker_type == "error":
            marker = self._parent.error_marker
        elif marker_type == "warning":
            marker = self._parent.warning_marker
        else:
            raise Exception(f"Unknown marker type: '{marker_type}'")
        # Check what to do with the marker
        result = None
        if action == "add":
            result = self._parent.markerAdd(scintilla_line, marker)
        elif action == "remove":
            result = self._parent.markerDelete(scintilla_line, marker)
        else:
            raise Exception(f"Unknown marker action: '{action}'")

    def __get_line_from_index(self, index):
        line, line_index = self._parent.lineIndexFromPosition(index)
        return line + 1, line_index

    def __get_line_column_from_message(self, message):
        return self.__get_line_from_index(message.offset)

    def get_diagnostic_at_line(self, line):
        line += 1
        if line in self.storage["errors"].keys():
            return self.storage["errors"][line]
        elif line in self.storage["fatals"].keys():
            return self.storage["fatals"][line]
        elif line in self.storage["warnings"].keys():
            return self.storage["warnings"][line]
        else:
            return None

    def show_fatal(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["fatals"][line] = message
        self.__set_marker("add", line, "fatal")

    def hide_fatal(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["fatals"].pop(line, None)
        self.__set_marker("remove", line, "fatal")

    def show_error(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["errors"][line] = message
        self.__set_marker("add", line, "error")

    def hide_error(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["errors"].pop(line, None)
        self.__set_marker("remove", line, "error")

    def show_warning(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["warnings"][line] = message
        self.__set_marker("add", line, "warning")

    def hide_warning(self, message):
        line, column = self.__get_line_column_from_message(message)
        self.storage["warnings"].pop(line, None)
        self.__set_marker("remove", line, "warning")

    def delete_all(self):
        self._parent.markerDeleteAll(self._parent.fatal_marker)
        self._parent.markerDeleteAll(self._parent.error_marker)
        self._parent.markerDeleteAll(self._parent.warning_marker)
        self.storage["fatals"] = {}
        self.storage["errors"] = {}
        self.storage["warnings"] = {}
