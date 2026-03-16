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
import itertools
import inspect
import functools
import keyword
import re
import collections
import textwrap
import qt
import data
import components
import themes
import gui.forms.customeditor
import gui.forms.tabwidget
import functions
import settings
import lexers
import traceback
import gc

"""
-----------------------------------------------------
Scintilla class for inputting more than one line into the REPL
-----------------------------------------------------
"""


class ReplHelper(qt.QsciScintilla):
    """REPL scintilla box for inputting multiple lines into the REPL.

    MUST BE PAIRED WITH A ReplLineEdit OBJECT!
    """

    # Class variables
    parent = None
    repl_master = None
    name = None
    # The scintilla api object(qt.QsciAPIs) must be an instace variable, or the underlying c++
    # mechanism deletes the object and the autocompletions compiled with api.prepare() are lost
    api = None
    # Attribute for indicating if the REPL helper is indicated
    indicated = False
    # Reference to the custom context menu
    context_menu = None
    # LineList object copied from the gui.forms.customeditor.CustomEditor object
    line_list = None
    """
    Built-in and private functions
    """

    def __init__(self, parent, repl_master):
        # Initialize superclass, from which the current class is inherited, THIS MUST BE DONE SO THAT THE SUPERCLASS EXECUTES ITS __init__ !!!!!!
        super().__init__(parent)
        # Save the reference to the parent(main window)
        self.parent = parent
        self.name = "REPL_HELPER"
        # Save the reference to the REPL object
        self.repl_master = repl_master
        # Hide the horizontal and show the vertical scrollbar
        self.SendScintilla(qt.QsciScintillaBase.SCI_SETVSCROLLBAR, True)
        self.SendScintilla(qt.QsciScintillaBase.SCI_SETHSCROLLBAR, False)
        # Hide the margin
        self.setMarginWidth(1, 0)
        # Autoindentation enabled when using "Enter" to indent to the same level as the previous line
        self.setAutoIndent(True)
        # Tabs are spaces by default
        self.setIndentationsUseTabs(False)
        # Set tab space indentation width
        self.setTabWidth(settings.Editor.tab_width)
        # Set encoding format to UTF-8 (Unicode)
        self.setUtf8(True)
        # Set brace matching
        self.setBraceMatching(qt.QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(qt.QColor(255, 153, 0))
        # Tabs are spaces by default
        self.setIndentationsUseTabs(False)
        # Set backspace to delete by tab widths
        self.setBackspaceUnindents(True)
        # Disable drops
        self.setAcceptDrops(False)
        # Set line endings to be Unix style ("\n")
        self.setEolMode(settings.Editor.end_of_line_mode)
        # Set the initial zoom factor
        self.zoomTo(settings.Editor.zoom_factor)
        """Functionality copied from the gui.forms.customeditor.CustomEditor to
        copy some of the needed editing functionality like commenting, ..."""
        # Add the attributes needed to implement the line nist
        self.line_list = components.LineList(self, self.text())
        # Add the needed functions assigned from the gui.forms.customeditor.CustomEditor
        self.set_theme = functools.partial(
            gui.forms.customeditor.CustomEditor.set_theme, self
        )
        self.set_line = functools.partial(
            gui.forms.customeditor.CustomEditor.set_line, self
        )
        self.set_lines = functools.partial(
            gui.forms.customeditor.CustomEditor.set_lines, self
        )
        self.toggle_comment_uncomment = functools.partial(
            gui.forms.customeditor.CustomEditor.toggle_comment_uncomment, self
        )
        self.comment_line = functools.partial(
            gui.forms.customeditor.CustomEditor.comment_line, self
        )
        self.comment_lines = functools.partial(
            gui.forms.customeditor.CustomEditor.comment_lines, self
        )
        self.uncomment_line = functools.partial(
            gui.forms.customeditor.CustomEditor.uncomment_line, self
        )
        self.uncomment_lines = functools.partial(
            gui.forms.customeditor.CustomEditor.uncomment_lines, self
        )
        self.prepend_to_line = functools.partial(
            gui.forms.customeditor.CustomEditor.prepend_to_line, self
        )
        self.prepend_to_lines = functools.partial(
            gui.forms.customeditor.CustomEditor.prepend_to_lines, self
        )
        self.replace_line = functools.partial(
            gui.forms.customeditor.CustomEditor.replace_line, self
        )
        self.get_line = functools.partial(
            gui.forms.customeditor.CustomEditor.get_line, self
        )
        self.check_line_numbering = functools.partial(
            gui.forms.customeditor.CustomEditor.check_line_numbering, self
        )
        self.text_to_list = functools.partial(
            gui.forms.customeditor.CustomEditor.text_to_list, self
        )
        self.list_to_text = functools.partial(
            gui.forms.customeditor.CustomEditor.list_to_text, self
        )
        # Add the function and connect the signal to update the line/column positions
        self._signal_editor_cursor_change = functools.partial(
            gui.forms.tabwidget.TabWidget._signal_editor_cursor_change, self
        )
        self.cursorPositionChanged.connect(self._signal_editor_cursor_change)
        # Set the lexer to python
        self.set_lexer()
        # Set the initial autocompletions
        self.update_autocompletions()
        # Setup the LineList object that will hold the custom editor text as a list of lines
        self.line_list = components.LineList(self, self.text())
        self.textChanged.connect(self.text_changed)

    def _filter_keypress(self, key_event):
        """Filter keypress for appropriate action."""
        pressed_key = key_event.key()
        accept_keypress = False
        # Get key modifiers and check if the Ctrl+Enter was pressed
        key_modifiers = qt.QApplication.keyboardModifiers()
        if (
            key_modifiers == qt.Qt.KeyboardModifier.ControlModifier
            and pressed_key == qt.Qt.Key.Key_Return
        ) or pressed_key == qt.Qt.Key.Key_Enter:
            # ON MY KEYBOARD Ctrl+Enter CANNOT BE DETECTED!
            # Qt.KeyboardModifier.ControlModifier  MODIFIER SHOWS FALSE WHEN USING qt.QApplication.keyboardModifiers() + Enter
            self.repl_master.external_eval_request(self.text(), self)
            accept_keypress = True
        return accept_keypress

    def _filter_keyrelease(self, key_event):
        """Filter keyrelease for appropriate action."""
        return False

    """
    Qt QSciScintilla functions
    """

    def keyPressEvent(self, event):
        """QScintila keyPressEvent, to catch which key was pressed."""
        # Filter the event
        if self._filter_keypress(event) == False:
            # Execute the superclass method, if the filter ignored the event
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """QScintila KeyReleaseEvent, to catch which key was released."""
        # Execute the superclass method first, the same trick as in __init__ !
        super().keyReleaseEvent(event)
        # Filter the event
        self._filter_keyrelease(event)

    def mousePressEvent(self, event):
        # Execute the superclass mouse click event
        super().mousePressEvent(event)
        # Reset the main forms last focused widget
        self.parent.last_focused_widget = None
        # Set focus to the clicked helper
        self.setFocus()
        # Hide the function wheel if it is shown
        self.parent.view.hide_all_overlay_widgets()
        # Need to set focus to self or the repl helper doesn't get focused,
        # don't know why?
        self.setFocus()
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()

    def wheelEvent(self, wheel_event):
        """Overridden mouse wheel rotate event."""
        key_modifiers = qt.QApplication.keyboardModifiers()
        delta = wheel_event.angleDelta().y()
        if delta < 0:
            if key_modifiers == qt.Qt.KeyboardModifier.ControlModifier:
                # Zoom out the scintilla tab view
                self.zoomOut()
        else:
            if key_modifiers == qt.Qt.KeyboardModifier.ControlModifier:
                # Zoom in the scintilla tab view
                self.zoomIn()
        # Handle the event
        if key_modifiers != qt.Qt.KeyboardModifier.ControlModifier:
            # Execute the superclass method
            super().wheelEvent(wheel_event)
        else:
            # Propagate(send forward) the wheel event to the parent
            wheel_event.ignore()

    def delete_context_menu(self):
        # Clean up the context menu
        if self.context_menu is not None:
            self.context_menu.hide()
            for b in self.context_menu.button_list:
                b.setParent(None)
            self.context_menu.setParent(None)
            self.context_menu = None

    #    def contextMenuEvent(self, event):
    #        pass

    def set_lexer(self):
        if self.lexer() is not None:
            self.lexer().setParent(None)
            self.setLexer(None)
        # Create the new lexer
        lexer = lexers.Python()
        lexer.setParent(self)
        result = lexers.get_comment_style_for_lexer(lexer)
        lexer.open_close_comment_style = result[0]
        lexer.comment_string = result[1]
        lexer.end_comment_string = result[2]
        # Set the lexers default font
        lexer.setDefaultFont(data.get_general_font())
        # Set the lexer with the initial autocompletions
        self.setLexer(lexer)
        # Set the theme
        self.set_theme(data.theme)
        self.lexer().set_theme(data.theme)

    def refresh_lexer(self):
        # Set the theme
        self.set_theme(data.theme)
        self.lexer().set_theme(data.theme)

    def text_changed(self):
        """Event that fires when the scintilla document text changes."""
        # Update the line list
        self.line_list.update_text_to_list(self.text())

    """
    ReplHelper autocompletion functions
    """

    def update_autocompletions(self, new_autocompletions=[]):
        """Function for updating the ReplHelper autocompletions."""
        # Set the lexer
        self.refresh_lexer()
        # Set the scintilla api for the autocompletions (MUST BE AN INSTANCE VARIABLE)
        self.api = qt.QsciAPIs(self.lexer())
        # Populate the api with all of the python keywords
        for kw in keyword.kwlist:
            self.api.add(kw)
        for word in new_autocompletions:
            self.api.add(word)
        self.api.prepare()
        # Set how many characters must be typed for the autocompletion popup to appear
        self.setAutoCompletionThreshold(1)
        # Set the source from where the autocompletions will be fetched
        self.setAutoCompletionSource(
            qt.QsciScintilla.AutoCompletionSource.AcsAll
        )
        # Set autocompletion case sensitivity
        self.setAutoCompletionCaseSensitivity(False)
