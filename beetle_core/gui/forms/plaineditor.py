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
import qt
import data
import lexers
import settings
import gui.templates.baseeditor
import gui.stylesheets.scrollbar as scrollbar
import components.actionfilter
import components.hotspots

"""
-----------------------------
Subclassed QScintilla widget used for displaying REPL messages, Python/C node trees, ...
-----------------------------
"""


class PlainEditor(gui.templates.baseeditor.BaseEditor):
    # Reference to the custom context menu
    context_menu = None
    """Namespace references for grouping functionality."""
    hotspots = None

    def self_destruct(self) -> None:
        """"""
        self.hotspots = None
        try:
            # Clean up the lexer
            self.lexer().setParent(None)
            self.setLexer(None)
        except:
            pass
        try:
            # REPL MESSAGES only clean up
            self.main_form.repl_messages_tab = None
        except:
            pass
        # Clean up the decorated mouse press event
        self.mousePressEvent = None
        # Clean up references
        self._parent = None
        self.main_form = None
        self.icon_manipulator = None
        # Destroy self
        self.setParent(None)
        self.deleteLater()
        return

    def __init__(self, parent, main_form, name) -> None:
        """"""
        # Initialize the superclass
        super().__init__(parent, main_form)
        # Store the main form and parent widget references
        self.name = name
        # Set encoding format to UTF-8 (Unicode)
        self.setUtf8(True)
        # Tabs are spaces by default
        self.setIndentationsUseTabs(False)
        # Initialize the namespace references
        self.hotspots = components.hotspots.Hotspots()
        # Set settings
        self.update_variable_settings()
        # Set the theme
        self.set_theme(data.theme)
        return

    def update_variable_settings(self):
        # Set font family and size
        self.setFont(data.get_editor_font())
        # Set brace matching
        self.setBraceMatching(qt.QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(
            qt.QColor(settings.editor["brace_color"])
        )
        # Set tab space indentation width
        self.setTabWidth(settings.editor["tab_width"])
        # Set line endings to be Unix style ('\n')
        self.setEolMode(settings.editor["end_of_line_mode"])
        # Set the initial zoom factor
        self.zoomTo(settings.editor["zoom_factor"])
        # Set cursor line visibility and color
        self.set_cursor_line_visibility(settings.editor["cursor_line_visible"])
        return

    def add_corner_buttons(self):
        def clear():
            self.main_form.display.repl_clear_tab()

        # Clear messages
        self.icon_manipulator.add_corner_button(
            "tango_icons/edit-clear.png", "Clear messages", clear
        )

    def set_cursor_line_visibility(self, new_state):
        self.setCaretLineVisible(new_state)
        if new_state == True:
            self.setCaretLineBackgroundColor(
                qt.QColor(data.theme["cursor_line_overlay"])
            )

    def delete_context_menu(self):
        # Clean up the context menu
        if self.context_menu is not None:
            self.context_menu.hide()
            for b in self.context_menu.button_list:
                b.setParent(None)
            self.context_menu.setParent(None)
            self.context_menu = None

    def contextMenuEvent(self, event):
        event.accept()

    def mousePressEvent(self, event):
        """Overloaded mouse click event."""
        # Execute the superclass mouse click event
        super().mousePressEvent(event)
        # Set focus to the clicked editor
        self.setFocus()
        # Set the last focused widget to the parent basic widget
        self.main_form.last_focused_widget = self.parent
        # Hide the function wheel if it is shown
        self.main_form.view.hide_all_overlay_widgets()
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()

    def enterEvent(self, enter_event):
        """Event that fires when the focus shifts to the TabWidget."""
        self.main_form.display.write_to_statusbar(self.name)

    def goto_line(self, line_number):
        """Set focus and cursor to the selected line."""
        # Move the cursor to the start of the selected line
        self.setCursorPosition(line_number, 0)
        # Move the first displayed line to the top of the viewving area
        self.SendScintilla(qt.QsciScintillaBase.SCI_GOTOLINE, line_number)

    def set_theme(self, theme):
        # Set the lexer
        self.setLexer(lexers.Text())
        self.setFont(data.get_editor_font())
        # Now the theme
        super().set_theme(theme)

    def refresh_lexer(self):
        self.set_theme(data.theme)
