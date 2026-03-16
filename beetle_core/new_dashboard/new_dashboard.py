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

"""Dashboard implementation using the Tile System.

This module implements a dashboard using the Tile System defined in
tile_widget.py. The NewDashboard class extends TileTabWidget to create a
dashboard with three tile containers:

- COMMANDS:             Contains command tiles like Build, Clean, Flash
- TOOLS & PLACEHOLDERS: Contains tool tiles like GCC, Make, OpenOCD, Python
- ENV VARIABLES:        Contains env variable tiles like PATH, PROJECT_DIR

Each of them is a TileContainer, which manages draggable tiles.

DATA MODEL:
    Strict model-view separation is ensured. The following global references can
    be used:

        - data.new_dashboard: Globally accessible `NewDashboard()`-widget. This
                              widget will *never* modify the global dashboard
                              data! It merely displays it.

        - data.dashboard_data: Globally accessible `DashboardData()`-instance.
"""

# Standard library
from __future__ import annotations
from typing import *
import copy

# Local
import qt
import data
import os_checker
import widget_cleanup
import gui.templates.baseobject
import gui.templates.widgetgenerator
import new_dashboard.tile_widget
import new_dashboard.dashboard_data

if TYPE_CHECKING:
    import gui.forms.mainwindow
    import gui.forms.homewindow


class CommandTile(new_dashboard.tile_widget.Tile):
    """Implementation for tiles representing shell commands with terminal-like
    display
    """

    class ClickableCommandLbl(widget_cleanup.WidgetCleaner, qt.QLabel):
        """A clickable label for those parts of a command between angled
        brackets.
        """

        clicked = qt.pyqtSignal(str)

        def __init__(self, text: str, parent: qt.QWidget = None) -> None:
            """ """
            super().__init__(text, parent)
            self.setCursor(qt.Qt.CursorShape.PointingHandCursor)
            self.__set_normal_stylesheet()
            return

        def __set_normal_stylesheet(self) -> None:
            """Set normal style"""
            self.setStyleSheet(f"""
                color: {data.theme["console"]["fonts"]["blue"]};
                """)
            self.setFont(data.get_general_font())
            return

        def update_style(self) -> None:
            """Update the label's style based on the current theme."""
            if qt.sip.isdeleted(self):
                return
            self.__set_normal_stylesheet()
            return

        def mousePressEvent(self, event: qt.QMouseEvent) -> None:
            if event.button() == qt.Qt.MouseButton.LeftButton:
                self.clicked.emit(self.text())
            return super().mousePressEvent(event)

    class RegularCommandLbl(widget_cleanup.WidgetCleaner, qt.QLabel):
        """A regular label for the regular parts of a command"""

        def __init__(self, text: str, parent: qt.QWidget = None) -> None:
            """ """
            super().__init__(text, parent)
            self.__set_normal_stylesheet()
            return

        def __set_normal_stylesheet(self) -> None:
            """Set normal style"""
            self.setStyleSheet(f"""
                color: {data.theme["console"]["fonts"]["default"]};
                """)
            self.setFont(data.get_general_font())
            return

        def update_style(self) -> None:
            """Update the label's style based on the current theme."""
            if qt.sip.isdeleted(self):
                return
            self.__set_normal_stylesheet()
            return

    def __init__(
        self,
        parent: qt.QWidget,
        tile_id: str,
        icon_path: Optional[str] = None,
        commands: Optional[List[str]] = None,
    ) -> None:
        """Initialize a command tile with an icon and terminal-like display.

        Args:
            parent:    The parent widget
            tile_id:   Unique identifier for the tile
            icon_path: Path to the icon (relative path, e.g.,
                       "icons/gen/build.svg")
            commands:  List of command strings (e.g., ["cd <project>/build",
                       "<make> clean -f ../config/makefile"])
        """
        super().__init__(parent=parent, tile_id=tile_id, title=None)

        # Set minimum height to fit content
        self.setMinimumHeight(80)

        # Create a horizontal layout for the icon and terminal
        main_layout = qt.QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(15)

        # Add icon if provided
        if icon_path:
            icon_size = data.get_general_icon_pixelsize()
            self.__icon_label = gui.templates.widgetgenerator.create_label(
                parent=self,
                image=icon_path,
                selectable_text=False,
                transparent_background=True,
            )
            self.__icon_label.setFixedSize(icon_size, icon_size)
            main_layout.addWidget(
                self.__icon_label, 0, qt.Qt.AlignmentFlag.AlignTop
            )

        # Create terminal-like display for commands
        self.__terminal_frame = qt.QFrame(self)
        terminal_layout = qt.QVBoxLayout(self.__terminal_frame)
        terminal_layout.setContentsMargins(10, 10, 10, 10)
        terminal_layout.setSpacing(2)

        # Store commands
        self.__commands = commands if commands else []
        self.__clickable_labels = {}

        # Add command lines
        if commands:
            for command in commands:
                command_layout = qt.QHBoxLayout()
                command_layout.setContentsMargins(0, 0, 0, 0)
                command_layout.setSpacing(0)

                # Add prompt
                prompt_label = CommandTile.RegularCommandLbl(
                    "> ", self.__terminal_frame
                )
                command_layout.addWidget(prompt_label)

                # Parse command parts
                parts = self._parse_command(command)
                for part in parts:
                    if part.startswith("<") and part.endswith(">"):
                        # Create clickable placeholder
                        clickable = CommandTile.ClickableCommandLbl(
                            part, self.__terminal_frame
                        )
                        clickable.clicked.connect(self._on_placeholder_clicked)
                        command_layout.addWidget(clickable)
                        self.__clickable_labels[part] = clickable
                    else:
                        # Regular command part
                        text_label = CommandTile.RegularCommandLbl(
                            part, self.__terminal_frame
                        )
                        command_layout.addWidget(text_label)

                # Add stretch to push everything to the left
                command_layout.addStretch(1)
                terminal_layout.addLayout(command_layout)

        # Add the terminal to the main layout and give it stretch priority
        main_layout.addWidget(self.__terminal_frame, 1)

        # Add the main layout to the tile's layout
        cast(qt.QVBoxLayout, self.layout()).addLayout(main_layout)
        self.__set_normal_style()
        return

    def __set_normal_style(self) -> None:
        """Set normal style"""
        self.__terminal_frame.setStyleSheet(f"""
            background-color: {data.theme["console"]["background"]};
            border-radius: 4px;
            """)
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        super().update_style()
        self.__set_normal_style()
        for child in self.__terminal_frame.findChildren(qt.QLabel):
            if hasattr(child, "update_style"):
                child.update_style()
        self.__icon_label.update_icon_style()
        return

    def _parse_command(self, command: str) -> List[str]:
        """Parse a command string into parts, identifying placeholders."""
        parts = []
        current_part = ""
        in_placeholder = False

        for char in command:
            if char == "<" and not in_placeholder:
                # Start of a placeholder
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                current_part = "<"
                in_placeholder = True
            elif char == ">" and in_placeholder:
                # Placeholder ends here
                current_part += ">"
                parts.append(current_part)
                current_part = ""
                in_placeholder = False
            else:
                # Regular character
                current_part += char

        # Add any remaining part
        if current_part:
            parts.append(current_part)

        return parts

    def _on_placeholder_clicked(self, placeholder: str) -> None:
        """Handle clicks on placeholders."""
        # Here you would implement actions when placeholders are clicked
        # For example, open a dialog to select or edit the placeholder value
        print(f"Placeholder clicked: {placeholder}")

    def get_commands(self) -> List[str]:
        """Get the commands displayed in the terminal.

        Returns:
            List of command strings
        """
        return self.__commands.copy()

    def set_commands(self, commands: List[str]) -> None:
        """Set new commands to display in the terminal.

        Args:
            commands: List of command strings

        Note:
            This would require rebuilding the UI to implement properly.
            For a real implementation, you would clear the terminal_layout and rebuild it.
        """
        self.__commands = commands.copy()
        # A real implementation would rebuild the terminal display here
        return


class ToolPlaceholderTile(new_dashboard.tile_widget.Tile):
    """Implementation for tiles representing tools"""

    class ClickableNameLbl(widget_cleanup.WidgetCleaner, qt.QLabel):
        """A clickable label for the name of this Tile"""

        clicked = qt.pyqtSignal(str)

        def __init__(self, text: str, parent: qt.QWidget = None) -> None:
            """ """
            super().__init__(text, parent)
            self.setCursor(qt.Qt.CursorShape.PointingHandCursor)
            self.__set_normal_stylesheet()
            return

        def __set_normal_stylesheet(self) -> None:
            """Set normal style"""
            self.setStyleSheet(f"""
                color: {data.theme["fonts"]["blue"]["color"]};
                text-decoration: underline;
                """)
            self.setFont(data.get_general_font())
            return

        def update_style(self) -> None:
            """Update the label's style based on the current theme."""
            if qt.sip.isdeleted(self):
                return
            self.__set_normal_stylesheet()
            return

        def mousePressEvent(self, event: qt.QMouseEvent) -> None:
            if event.button() == qt.Qt.MouseButton.LeftButton:
                self.clicked.emit(self.text())
            return super().mousePressEvent(event)

    def __init__(
        self,
        parent: qt.QWidget,
        tile_id: str,
        title: Optional[str] = None,
        value: Optional[str] = None,
        unique_id: Optional[str] = None,
    ) -> None:
        """"""
        # Call parent with no title since we'll handle it ourselves
        super().__init__(parent=parent, tile_id=tile_id, title=None)
        self.__name = title or ""
        self.__value = value or ""
        self.__unique_id = unique_id or ""

        # Create layout
        content_layout = qt.QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        line_layout_list: List[qt.QHBoxLayout] = []
        for i in range(4):
            line_layout = qt.QHBoxLayout()
            line_layout.setContentsMargins(0, 0, 0, 0)
            line_layout.setSpacing(10)
            line_layout_list.append(line_layout)
            continue

        line_layout_02 = qt.QHBoxLayout()
        line_layout_02.setContentsMargins(0, 0, 0, 0)
        line_layout_02.setSpacing(10)

        # $ NAME LABEL
        # Create name label with angle brackets and styling
        self.__name_label = ToolPlaceholderTile.ClickableNameLbl(
            f"<{self.__name}>", self
        )
        self.__name_label.clicked.connect(self._on_name_clicked)

        # $ FOLDER BUTTON
        # Create a folder button using the standard widget generator
        self.__folder_button = gui.templates.widgetgenerator.create_pushbutton(
            name="folder",
            icon_name="icons/folder/closed/folder.svg",
            text="",
            tooltip="Choose tool location",
        )
        self.__folder_button.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
            qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
        )
        self.__folder_button.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        self.__folder_button.mousePressEvent = self._on_folder_button_clicked

        # $ VALUE TEXT FIELD
        # Create value text field (as a QLineEdit)
        self.__value_field = gui.templates.widgetgenerator.create_textbox(
            name=f"{tile_id}_value",
            read_only=True,
            parent=self,
        )
        self.__value_field.setText(self.__value)
        self.__value_field.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred, qt.QSizePolicy.Policy.Fixed
        )
        self.__value_field.setMinimumWidth(
            self.__value_field.fontMetrics().horizontalAdvance(self.__value)
            + 20
        )

        # $ UNIQUE_ID BUTTON
        self.__unique_id_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                name="unique_id",
                icon_name="icons/tool_cards/card_name.svg",
                text="",
                tooltip="Tool Unique ID",
            )
        )
        self.__unique_id_button.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
            qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
        )
        self.__unique_id_button.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        self.__unique_id_button.mousePressEvent = (
            self._on_unique_id_button_clicked
        )

        # $ UNIQUE_ID TEXT FIELD
        self.__unique_id_field = gui.templates.widgetgenerator.create_textbox(
            name=f"{tile_id}_unique_id",
            read_only=True,
            parent=self,
        )
        self.__unique_id_field.setText(self.__unique_id)
        self.__unique_id_field.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred, qt.QSizePolicy.Policy.Fixed
        )
        self.__unique_id_field.setMinimumWidth(
            self.__unique_id_field.fontMetrics().horizontalAdvance(
                self.__unique_id
            )
            + 20
        )

        # $ DOWNLOAD BUTTON
        self.__download_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                name="download",
                icon_name="icons/gen/download.svg",
                text="Download",
                tooltip="Download new tool",
                no_border=False,
                style="light",
            )
        )
        self.__download_button.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
            qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
        )
        self.__download_button.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        self.__download_button.mousePressEvent = (
            self._on_download_button_clicked
        )

        # $ REMOVE BUTTON
        self.__remove_button = gui.templates.widgetgenerator.create_pushbutton(
            name="remove",
            icon_name="icons/gen/trash.svg",
            text="Remove",
            tooltip="Remove tool from Dashboard",
            no_border=False,
            style="light",
        )
        self.__remove_button.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
            qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
        )
        self.__remove_button.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        self.__remove_button.mousePressEvent = self._on_remove_button_clicked

        # Add widgets to layout, give stretch priority to value fields
        cast(qt.QVBoxLayout, self.layout()).addLayout(content_layout)
        content_layout.addLayout(line_layout_list[0])
        content_layout.addLayout(line_layout_list[1])
        content_layout.addLayout(line_layout_list[2])
        content_layout.addLayout(line_layout_list[3])
        line_layout_list[0].addWidget(self.__name_label)
        line_layout_list[0].addWidget(self.__folder_button)
        line_layout_list[0].addWidget(self.__value_field, 1)
        spacer_widget = qt.QWidget()
        spacer_widget.setFixedWidth(self.__name_label.sizeHint().width())
        line_layout_list[1].addWidget(spacer_widget)
        line_layout_list[1].addWidget(self.__unique_id_button)
        line_layout_list[1].addWidget(self.__unique_id_field, 1)
        line_layout_list[2].addWidget(self.__download_button)
        line_layout_list[2].addSpacerItem(
            qt.QSpacerItem(0, 0, hPolicy=qt.QSizePolicy.Policy.Expanding)
        )
        line_layout_list[3].addWidget(self.__remove_button)
        line_layout_list[3].addSpacerItem(
            qt.QSpacerItem(0, 0, hPolicy=qt.QSizePolicy.Policy.Expanding)
        )
        self.__set_normal_style()
        return

    def __set_normal_style(self) -> None:
        """Set normal style"""
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        super().update_style()
        self.__name_label.update_style()
        self.__folder_button.update_style()
        self.__value_field.update_style()
        self.__unique_id_button.update_style()
        self.__unique_id_field.update_style()
        self.__download_button.update_style()
        self.__remove_button.update_style()
        return

    def _on_folder_button_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the folder button."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            print(f"Folder clicked: <{self.__name}>")
        super().mousePressEvent(event)
        return

    def _on_unique_id_button_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the unique id button."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            print(f"Unique ID clicked: <{self.__name}>")
        super().mousePressEvent(event)
        return

    def _on_name_clicked(self, *args, **kwargs) -> None:
        """Handle clicks on the placeholder name."""
        print(f"Placeholder clicked: <{self.__name}>")
        return

    def _on_download_button_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the placeholder name."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            print(f"Download clicked: <{self.__name}>")
        super().mousePressEvent(event)
        return

    def _on_remove_button_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the placeholder name."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            print(f"Remove clicked: <{self.__name}>")
        super().mousePressEvent(event)
        return

    def get_name(self) -> str:
        """Get the placeholder name (without angle brackets)."""
        return self.__name

    def get_value(self) -> str:
        """Get the current value of the placeholder."""
        return self.__value

    def set_value(self, value: str) -> None:
        """Set the value of the placeholder."""
        self.__value = value
        self.__value_field.setText(value)
        # Update the width to fit the new text
        self.__value_field.setMinimumWidth(
            self.__value_field.fontMetrics().horizontalAdvance(value) + 20
        )
        return


class PathPlaceholderTile(new_dashboard.tile_widget.Tile):
    """Implementation for tiles representing placeholders with name and value."""

    class ClickableNameLbl(widget_cleanup.WidgetCleaner, qt.QLabel):
        """A clickable label for the name of this Tile"""

        clicked = qt.pyqtSignal(str)

        def __init__(self, text: str, parent: qt.QWidget = None) -> None:
            """ """
            super().__init__(text, parent)
            self.setCursor(qt.Qt.CursorShape.PointingHandCursor)
            self.__set_normal_stylesheet()
            return

        def __set_normal_stylesheet(self) -> None:
            """Set normal style"""
            self.setStyleSheet(f"""
                color: {data.theme["fonts"]["blue"]["color"]};
                text-decoration: underline;
                """)
            self.setFont(data.get_general_font())
            return

        def update_style(self) -> None:
            """Update the label's style based on the current theme."""
            if qt.sip.isdeleted(self):
                return
            self.__set_normal_stylesheet()
            return

        def mousePressEvent(self, event: qt.QMouseEvent) -> None:
            if event.button() == qt.Qt.MouseButton.LeftButton:
                self.clicked.emit(self.text())
            return super().mousePressEvent(event)

    def __init__(
        self,
        parent: qt.QWidget,
        tile_id: str,
        title: Optional[str] = None,
        value: Optional[str] = None,
    ) -> None:
        """Initialize a placeholder tile with a name and value display.

        Args:
            parent: The parent widget
            tile_id: Unique identifier for the tile
            title: The title/name of the placeholder (without <> brackets)
            value: The current value of the placeholder
        """
        # Call parent with no title since we'll handle it ourselves
        super().__init__(parent=parent, tile_id=tile_id, title=None)
        self.__name = title or ""
        self.__value = value or ""

        # Create layout
        content_layout = qt.QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # $ NAME LABEL
        # Create name label with angle brackets and styling
        self.__name_label = PathPlaceholderTile.ClickableNameLbl(
            text=f"<{self.__name}>",
            parent=self,
        )
        self.__name_label.clicked.connect(self._on_name_clicked)

        # $ FOLDER BUTTON
        # Create a folder button using the standard widget generator
        self.__folder_button = gui.templates.widgetgenerator.create_pushbutton(
            name="folder",
            icon_name="icons/folder/closed/folder.svg",
            text="",
            tooltip="Choose path location",
        )
        self.__folder_button.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
            qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
        )
        self.__folder_button.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        self.__folder_button.mousePressEvent = self._on_folder_button_clicked

        # $ VALUE TEXT FIELD
        # Create value text field (as a QLineEdit)
        self.__value_field = gui.templates.widgetgenerator.create_textbox(
            name=f"{tile_id}_value",
            read_only=True,
            parent=self,
        )
        self.__value_field.setText(self.__value)
        self.__value_field.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred, qt.QSizePolicy.Policy.Fixed
        )
        self.__value_field.setMinimumWidth(
            self.__value_field.fontMetrics().horizontalAdvance(self.__value)
            + 20
        )

        # Add widgets to layout, give stretch priority to value field
        content_layout.addWidget(self.__name_label)
        content_layout.addWidget(self.__folder_button)
        content_layout.addWidget(self.__value_field, 1)
        cast(qt.QVBoxLayout, self.layout()).addLayout(content_layout)
        return

    def __set_normal_style(self) -> None:
        """Set normal style"""
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        super().update_style()
        self.__name_label.update_style()
        self.__folder_button.update_style()
        self.__value_field.update_style()
        return

    def _on_folder_button_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the folder button."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            # Print for now, but this would open a dialog or similar
            print(f"Folder clicked: <{self.__name}>")
        # Pass the event to the parent class method
        super().mousePressEvent(event)
        return

    def _on_name_clicked(self, *args, **kwargs) -> None:
        """Handle clicks on the placeholder name."""
        print(f"Placeholder clicked: <{self.__name}>")
        return

    def get_name(self) -> str:
        """Get the placeholder name (without angle brackets)."""
        return self.__name

    def get_value(self) -> str:
        """Get the current value of the placeholder."""
        return self.__value

    def set_value(self, value: str) -> None:
        """Set the value of the placeholder."""
        self.__value = value
        self.__value_field.setText(value)
        # Update the width to fit the new text
        self.__value_field.setMinimumWidth(
            self.__value_field.fontMetrics().horizontalAdvance(value) + 20
        )
        return


class EnvTile(new_dashboard.tile_widget.Tile):
    """Implementation for tiles representing environment variables"""

    class ClickableNameLbl(widget_cleanup.WidgetCleaner, qt.QLabel):
        """A clickable label for the name of this Tile"""

        clicked = qt.pyqtSignal(str)

        def __init__(self, text: str, parent: qt.QWidget = None) -> None:
            """ """
            super().__init__(text, parent)
            self.setCursor(qt.Qt.CursorShape.PointingHandCursor)
            self.__set_normal_stylesheet()
            return

        def __set_normal_stylesheet(self) -> None:
            """Set normal style"""
            self.setStyleSheet(f"""
                color: {data.theme["fonts"]["blue"]["color"]};
                text-decoration: underline;
                """)
            self.setFont(data.get_general_font())
            return

        def update_style(self) -> None:
            """Update the label's style based on the current theme."""
            if qt.sip.isdeleted(self):
                return
            self.__set_normal_stylesheet()
            return

        def mousePressEvent(self, event: qt.QMouseEvent) -> None:
            if event.button() == qt.Qt.MouseButton.LeftButton:
                self.clicked.emit(self.text())
            return super().mousePressEvent(event)

    def __init__(
        self,
        parent: qt.QWidget,
        tile_id: str,
        title: Optional[str] = None,
        value: Optional[str] = None,
    ) -> None:
        """Initialize an environment variable tile with name and values display.

        Args:
            parent: The parent widget
            tile_id: Unique identifier for the tile
            title: The title/name of the environment variable
            value: The current value(s) of the environment variable
        """
        # Call parent with no title since we'll handle it ourselves
        super().__init__(parent=parent, tile_id=tile_id, title=None)
        self.__name = title or ""
        self.__value = value or ""
        self.__separator = ";" if os_checker.is_os("windows") else ":"
        self.__value_fields: List[gui.templates.widgetgenerator.TextBox] = []

        # Create main layout
        content_layout = qt.QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Create header layout
        header_layout = qt.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # $ NAME LABEL
        # Create name label with angle brackets and styling
        self.__name_label = EnvTile.ClickableNameLbl(
            text=f"{self.__name}",
            parent=self,
        )
        self.__name_label.clicked.connect(self._on_name_clicked)

        # Add header widgets to layout
        header_layout.addWidget(self.__name_label)
        header_layout.addStretch(1)  # Push widgets to the left

        # Add header layout to main layout
        content_layout.addLayout(header_layout)

        # $ VALUES LAYOUT
        self.__values_layout = qt.QVBoxLayout()
        self.__values_layout.setContentsMargins(0, 0, 0, 0)
        self.__values_layout.setSpacing(5)

        # Parse and add value fields
        if value:
            self._parse_and_display_values(value)

        # Add values layout to main layout
        content_layout.addLayout(self.__values_layout)

        # Add the main layout to the tile's layout
        cast(qt.QVBoxLayout, self.layout()).addLayout(content_layout)
        return

    def __set_normal_style(self) -> None:
        """Set normal style"""
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        super().update_style()
        self.__name_label.update_style()
        for field in self.__value_fields:
            field.update_style()
        return

    def _parse_and_display_values(self, value_str: str) -> None:
        """Parse a multi-value string and create text fields for each value.

        Args:
            value_str: The string containing one or multiple values
        """
        # Clear existing value fields
        self._clear_value_fields()

        # Split the value string by the separator if it contains any
        values = (
            value_str.split(self.__separator)
            if self.__separator in value_str
            else [value_str]
        )

        # Create a text field for each value
        for i, val in enumerate(values):
            if val.strip():  # Only add non-empty values
                self._add_value_field(val, i)
        return

    def _add_value_field(self, value: str, index: int) -> None:
        """Add a single value field.

        Args:
            value: The value to display in the field
            index: The position index of this value
        """
        # Create a horizontal layout for this value
        value_row_layout = qt.QHBoxLayout()
        value_row_layout.setContentsMargins(0, 0, 0, 0)
        value_row_layout.setSpacing(5)

        # Create value text field
        value_field = gui.templates.widgetgenerator.create_textbox(
            name=f"{self.get_id()}_value_{index}",
            read_only=True,
            parent=self,
        )
        value_field.setText(value)
        value_field.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )

        # Add the text field to the row layout
        value_row_layout.addWidget(
            value_field, 1
        )  # Give stretch priority to the text field

        # Add the row layout to the values layout
        self.__values_layout.addLayout(value_row_layout)

        # Keep track of the field
        self.__value_fields.append(value_field)
        return

    def _clear_value_fields(self) -> None:
        """Clear all value fields and their layouts."""
        # Clear our list of fields
        self.__value_fields = []

        # Remove all items from values layout
        while self.__values_layout.count():
            item = self.__values_layout.takeAt(0)
            if item.layout():
                # If it's a layout, remove all its widgets
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            if item.widget():
                item.widget().deleteLater()
        return

    def _update_value(self) -> None:
        """Update the internal value string from the text fields."""
        values = [field.text() for field in self.__value_fields]
        self.__value = self.__separator.join(values)
        return

    def _on_name_clicked(self, *args, **kwargs) -> None:
        """Handle clicks on the environment variable name."""
        print(f"Env var name clicked: <{self.__name}>")
        return

    def get_name(self) -> str:
        """Get the environment variable name."""
        return self.__name

    def get_value(self) -> str:
        """Get the current value of the environment variable."""
        return self.__value

    def set_value(self, value: str) -> None:
        """Set the value of the environment variable.

        Args:
            value: The new value(s) of the environment variable
        """
        self.__value = value
        self._parse_and_display_values(value)
        return


class NewDashboard(new_dashboard.tile_widget.TileTabWidget):
    """Dashboard implementation using the Tile System.

    DATA MODEL:
        Strict model-view separation is ensured. The following global references
        can be used:

            - data.new_dashboard: Globally accessible `NewDashboard()`-widget.
                                  This widget will *never* modify the global
                                  dashboard data! It merely displays it.

            - data.dashboard_data: Globally accessible `DashboardData()`-
                                   instance.

    NOTE:
        This `NewDashboard()`-widget stores a copy of the dashboard data
        internally, purely for displaying purposes.
    """

    # Something changed to the internally stored data, due to invocation of an
    # an add, update or remove method, defined further down this class.
    data_changed_programmatically = qt.pyqtSignal(
        new_dashboard.dashboard_data.DashboardData, str
    )  # data, section

    # Something changed to the internally stored data, due to user interaction
    # with the GUI.
    data_changed_in_gui = qt.pyqtSignal(
        new_dashboard.dashboard_data.DashboardData, str
    )  # data, section

    def __init__(
        self,
        parent: Union[qt.QTabWidget, qt.QFrame, qt.QMainWindow, None],
        main_form: Union[
            gui.forms.mainwindow.MainWindow, gui.forms.homewindow.HomeWindow
        ],
        dashboard_data: Optional[
            new_dashboard.dashboard_data.DashboardData
        ] = None,
    ) -> None:
        """Initialize the dashboard.

        Args:
            parent:         The parent widget.

            main_form:      The main window or home window (obviously, main
                            window must be provided).

            dashboard_data: Optional dashboard data, see `DashboardData`
                            dataclass in `dashboard_data.py`. If not provided,
                            it defaults to an empty `DashboardData()`-instance.
        """
        super().__init__(parent, main_form)

        # Initialize dashboard data
        self.__dashboard_data: new_dashboard.dashboard_data.DashboardData = (
            dashboard_data
            if dashboard_data is not None
            else new_dashboard.dashboard_data.DashboardData()
        )

        # Create and add containers to layout, then populate them with Tiles
        # that present the data.
        self.__create_containers()
        self.__add_containers_to_layout()
        self.__populate_dashboard()
        return

    def update_style(self) -> None:
        """Update the dashboard's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        super().update_style()
        return

    def self_destruct(self) -> None:
        """Properly destroy this widget"""
        data.new_dashboard = None
        super().self_destruct()
        return

    def __create_containers(self) -> None:
        """Create the tile containers for the dashboard."""
        # Commands container
        self.__commands_container = new_dashboard.tile_widget.TileContainer(
            self, title="COMMANDS", container_id="commands"
        )

        # Placeholders container
        self.__placeholder_container = new_dashboard.tile_widget.TileContainer(
            self, title="PLACEHOLDERS", container_id="tools"
        )

        # Environment variables container
        self.__env_container = new_dashboard.tile_widget.TileContainer(
            self, title="ENV VARIABLES", container_id="env_variables"
        )
        return

    def __add_containers_to_layout(self) -> None:
        """Set up the dashboard layout."""
        # Add the commands container
        self.get_main_frame().layout().addWidget(self.__commands_container)
        self.get_main_frame().layout().addItem(
            qt.QSpacerItem(
                10,
                10,
                hPolicy=qt.QSizePolicy.Policy.Fixed,
                vPolicy=qt.QSizePolicy.Policy.Fixed,
            )
        )

        # Add the placeholders container
        self.get_main_frame().layout().addWidget(self.__placeholder_container)
        self.get_main_frame().layout().addItem(
            qt.QSpacerItem(
                10,
                10,
                hPolicy=qt.QSizePolicy.Policy.Fixed,
                vPolicy=qt.QSizePolicy.Policy.Fixed,
            )
        )

        # Add the environment variables container
        self.get_main_frame().layout().addWidget(self.__env_container)
        self.get_main_frame().layout().addItem(
            qt.QSpacerItem(
                10,
                10,
                hPolicy=qt.QSizePolicy.Policy.Expanding,
                vPolicy=qt.QSizePolicy.Policy.Expanding,
            )
        )
        return

    def __populate_dashboard(self) -> None:
        """Populate dashboard with data from `self.__dashboard_data`"""
        # Add command tiles
        for (
            command_name,
            command_data,
        ) in self.__dashboard_data.commands.items():
            self.__commands_container.add_tile(
                CommandTile(
                    parent=self,
                    tile_id=command_name,
                    icon_path=command_data.icon_path,
                    commands=command_data.commands,
                )
            )

        # Add path placeholder tiles
        for (
            path_placeholder_name,
            path_placeholder_data,
        ) in self.__dashboard_data.path_placeholders.items():
            self.__placeholder_container.add_tile(
                PathPlaceholderTile(
                    parent=self,
                    tile_id=path_placeholder_name,
                    title=path_placeholder_name,
                    value=path_placeholder_data.value,
                )
            )

        # Add tool placeholder tiles
        for (
            tool_placeholder_name,
            tool_placeholder_data,
        ) in self.__dashboard_data.tool_placeholders.items():
            self.__placeholder_container.add_tile(
                ToolPlaceholderTile(
                    parent=self,
                    tile_id=tool_placeholder_name,
                    title=tool_placeholder_name,
                    value=tool_placeholder_data.value,
                    unique_id=tool_placeholder_data.unique_id,
                )
            )

        # Add environment variable tiles
        for (
            env_var_name,
            env_var_data,
        ) in self.__dashboard_data.env_variables.items():
            self.__env_container.add_tile(
                EnvTile(
                    parent=self,
                    tile_id=env_var_name,
                    title=env_var_name,
                    value=env_var_data.value,
                )
            )
        return

    def __clear_dashboard(self) -> None:
        """Clear all tiles and dashboard containers."""
        layout = self.get_main_frame().layout()
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            child = item.widget()  # None for spacers
            if child is not None:
                if qt.sip.isdeleted(child):
                    pass
                elif callable(getattr(child, "self_destruct", None)):
                    child.self_destruct()  # noqa
                elif isinstance(child, qt.QWidget):
                    child.setParent(None)
                    child.deleteLater()
            qt.sip.delete(item)
            continue
        self.__create_containers()
        self.__add_containers_to_layout()
        return

    # * ENTIRE DASHBOARD *
    # * ================ *
    # Methods to get or set the data from the entire dashboard. Both the getter
    # and setter methods first take a copy of the data.
    #
    def get_dashboard_data(self) -> new_dashboard.dashboard_data.DashboardData:
        """Get the complete dashboard data.

        Returns:
            The dashboard data
        """
        return copy.deepcopy(self.__dashboard_data)

    def set_dashboard_data(
        self, dashboard_data: new_dashboard.dashboard_data.DashboardData
    ) -> None:
        """Set new dashboard data and refresh the dashboard.

        Args:
            dashboard_data: The new dashboard data. The most common use-case
                            here would be:
                                data.new_dashboard.set_dashboard_data(
                                    data.dashboard_data
                                )
        """
        # Update the data
        self.__dashboard_data = copy.deepcopy(dashboard_data)

        # Clear and repopulate the dashboard
        self.__clear_dashboard()
        self.__populate_dashboard()

        # Emit data changed signal
        self.data_changed_programmatically.emit(
            self.get_dashboard_data(), "all"
        )
        return

    # * COMMANDS SECTION *
    # * ================ *
    # Methods to get, add, update and remove command tiles. Parameters are:
    #
    # - command_name: Name of the command, as shown in the command tile and in
    #                 the top ribbon. The `command_name` is used to identify a
    #                 command within the project scope. Common names are:
    #                 "clean", "build" and "flash".
    #
    # - command_data: Command()-instance as defined in the Command dataclass in
    #                 `dashboard_data.py`.
    #
    def get_command(
        self, command_name: str
    ) -> Optional[new_dashboard.dashboard_data.Command]:
        """Get command"""
        command = self.__dashboard_data.commands.get(command_name)
        return copy.deepcopy(command) if command else None

    def add_command(
        self,
        command_name: str,
        command_data: new_dashboard.dashboard_data.Command,
    ) -> None:
        """Add command"""
        # Add to data model
        self.__dashboard_data.commands[command_name] = command_data

        # Add to view
        self.__commands_container.add_tile(
            CommandTile(
                parent=self,
                tile_id=command_name,
                icon_path=command_data.icon_path,
                commands=command_data.commands,
            )
        )

        # Emit data changed signal
        self.data_changed_programmatically.emit(
            self.get_dashboard_data(), "commands"
        )
        return

    def update_command(
        self,
        command_name: str,
        command_data: new_dashboard.dashboard_data.Command,
    ) -> None:
        """Update command"""
        # Update data model
        if command_name in self.__dashboard_data.commands:
            self.__dashboard_data.commands[command_name] = command_data

            # Update view (for now, clear and repopulate the command section)
            # TODO: Implement a method to update a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "commands"
            )
        return

    def remove_command(self, command_name: str) -> None:
        """Remove command"""
        # Remove from data model
        if command_name in self.__dashboard_data.commands:
            del self.__dashboard_data.commands[command_name]

            # Update view (for now, clear and repopulate the command section)
            # TODO: Implement a method to remove a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "commands"
            )
        return

    # * PATH PLACEHOLDERS SECTION *
    # * ========================= *
    # Methods to get, add, update and remove path placeholder tiles. Parameters
    # are:
    #
    # - path_placeholder_name: Name of the path placeholder, as shown in the
    #                          path placeholder tile, wrapped in `<>` (the
    #                          angled brackets are not part of the name,
    #                          though). The name is used to identify a path
    #                          placeholder within project scope. Common names
    #                          are: "project" and "beetle_tools".
    #
    # - path_placeholder_data: PathPlaceholder()-instance as defined in the
    #                          PathPlaceholder dataclass in `dashboard_data.py`.
    #
    def get_path_placeholder(
        self, path_placeholder_name: str
    ) -> Optional[new_dashboard.dashboard_data.PathPlaceholder]:
        """Get path placeholder"""
        placeholder = self.__dashboard_data.path_placeholders.get(
            path_placeholder_name
        )
        return copy.deepcopy(placeholder) if placeholder else None

    def add_path_placeholder(
        self,
        path_placeholder_name: str,
        path_placeholder_data: new_dashboard.dashboard_data.PathPlaceholder,
    ) -> None:
        """Add path placeholder"""
        # Add to data model
        self.__dashboard_data.path_placeholders[path_placeholder_name] = (
            path_placeholder_data
        )

        # Add to view
        self.__placeholder_container.add_tile(
            PathPlaceholderTile(
                parent=self,
                tile_id=path_placeholder_name,
                title=path_placeholder_name,
                value=path_placeholder_data.value,
            )
        )

        # Emit data changed signal
        self.data_changed_programmatically.emit(
            self.get_dashboard_data(), "path_placeholders"
        )
        return

    def update_path_placeholder(
        self,
        path_placeholder_name: str,
        path_placeholder_data: new_dashboard.dashboard_data.PathPlaceholder,
    ) -> None:
        """Update path placeholder"""
        # Update data model
        if path_placeholder_name in self.__dashboard_data.path_placeholders:
            self.__dashboard_data.path_placeholders[path_placeholder_name] = (
                path_placeholder_data
            )

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to update a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "path_placeholders"
            )
        return

    def remove_path_placeholder(self, path_placeholder_name: str) -> None:
        """Remove path placeholder"""
        # Remove from data model
        if path_placeholder_name in self.__dashboard_data.path_placeholders:
            del self.__dashboard_data.path_placeholders[path_placeholder_name]

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to remove a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "path_placeholders"
            )
        return

    # * TOOL PLACEHOLDERS SECTION *
    # * ========================= *
    # Methods to get, add, update and remove tool placeholder tiles. Parameters
    # are:
    #
    # - tool_placeholder_name: Name of the tool placeholder, as shown in the
    #                          tool placeholder tile, wrapped in `<>` (the
    #                          angled brackets are not part of the name,
    #                          though). The name is used to identify a tool
    #                          placeholder within project scope. Common names
    #                          are: "gcc", "make" and "openocd".
    #
    #      WARNING: Do not confuse with the tool's `unique_id`, which is an
    #      identifier beyond the project's scope! For example:
    #          tool_placeholder_name = "gcc"
    #          tool_unique_id        = "gnu_arm_toolchain_10.3.1_20210824_32b"
    #
    # - tool_placeholder_data: PathPlaceholder()-instance as defined in the
    #                          PathPlaceholder dataclass in `dashboard_data.py`.
    #
    def get_tool_placeholder(
        self, tool_placeholder_name: str
    ) -> Optional[new_dashboard.dashboard_data.ToolPlaceholder]:
        """Get tool placeholder"""
        tool = self.__dashboard_data.tool_placeholders.get(
            tool_placeholder_name
        )
        return copy.deepcopy(tool) if tool else None

    def add_tool_placeholder(
        self,
        tool_placeholder_name: str,
        tool_placeholder_data: new_dashboard.dashboard_data.ToolPlaceholder,
    ) -> None:
        """Add tool placeholder"""
        # Add to data model
        self.__dashboard_data.tool_placeholders[tool_placeholder_name] = (
            tool_placeholder_data
        )

        # Add to view
        self.__placeholder_container.add_tile(
            ToolPlaceholderTile(
                parent=self,
                tile_id=tool_placeholder_name,
                title=tool_placeholder_name,
                value=tool_placeholder_data.value,
                unique_id=tool_placeholder_data.unique_id,
            )
        )

        # Emit data changed signal
        self.data_changed_programmatically.emit(
            self.get_dashboard_data(), "tool_placeholders"
        )
        return

    def update_tool_placeholder(
        self,
        tool_placeholder_name: str,
        tool_placeholder_data: new_dashboard.dashboard_data.ToolPlaceholder,
    ) -> None:
        """Update tool placeholder"""
        # Update data model
        if tool_placeholder_name in self.__dashboard_data.tool_placeholders:
            self.__dashboard_data.tool_placeholders[tool_placeholder_name] = (
                tool_placeholder_data
            )

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to update a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "tool_placeholders"
            )
        return

    def remove_tool_placeholder(self, tool_placeholder_name: str) -> None:
        """Remove tool placeholder"""
        # Remove from data model
        if tool_placeholder_name in self.__dashboard_data.tool_placeholders:
            del self.__dashboard_data.tool_placeholders[tool_placeholder_name]

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to remove a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "tool_placeholders"
            )
        return

    # * ENV VARIABLES SECTION *
    # * ===================== *
    # Methods to get, add, update and remove env variable tiles. Parameters
    # are:
    #
    # - env_var_name: Name of the env variable, as shown in the tile. The name
    #                 is used to identify an env variable within project scope.
    #                 Common names are "PATH" and "HOME".
    #
    # - env_var_data: EnvVariable()-instance as defined in the EnvVariable
    #                 dataclass in `dashboard_data.py`.
    #
    def get_env_variable(
        self, env_var_name: str
    ) -> Optional[new_dashboard.dashboard_data.EnvVariable]:
        """Get env var"""
        env = self.__dashboard_data.env_variables.get(env_var_name)
        return copy.deepcopy(env) if env else None

    def add_env_variable(
        self,
        env_var_name: str,
        env_var_data: new_dashboard.dashboard_data.EnvVariable,
    ) -> None:
        """Add env var"""
        # Add to data model
        self.__dashboard_data.env_variables[env_var_name] = env_var_data

        # Add to view
        self.__env_container.add_tile(
            EnvTile(
                parent=self,
                tile_id=env_var_name,
                title=env_var_name,
                value=env_var_data.value,
            )
        )

        # Emit data changed signal
        self.data_changed_programmatically.emit(
            self.get_dashboard_data(), "env_variables"
        )
        return

    def update_env_variable(
        self,
        env_var_name: str,
        env_data: new_dashboard.dashboard_data.EnvVariable,
    ) -> None:
        """Update env var"""
        # Update data model
        if env_var_name in self.__dashboard_data.env_variables:
            self.__dashboard_data.env_variables[env_var_name] = env_data

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to update a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "env_variables"
            )
        return

    def remove_env_variable(self, env_var_name: str) -> None:
        """Remove env var"""
        # Remove from data model
        if env_var_name in self.__dashboard_data.env_variables:
            del self.__dashboard_data.env_variables[env_var_name]

            # Update view (for now, clear and repopulate)
            # TODO: Implement a method to remove a specific tile
            self.__clear_dashboard()
            self.__populate_dashboard()

            # Emit data changed signal
            self.data_changed_programmatically.emit(
                self.get_dashboard_data(), "env_variables"
            )
        return

    # def __add_modify_commands_button(self) -> None:
    #     """Add a button to modify or add command tiles to the commands
    #     container.
    #     """
    #     # Create a button using the standard widget generator
    #     button = gui.templates.widgetgenerator.create_pushbutton(
    #         name="modify_commands_button",
    #         icon_name="icons/menu_edit/edit.svg",
    #         text="MODIFY/ADD COMMANDS",
    #         tooltip="Modify existing commands or add new ones",
    #         click_func=self.__on_modify_commands_clicked,
    #     )
    #
    #     # Set size policy to not stretch horizontally
    #     button.setSizePolicy(
    #         qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
    #         qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
    #     )
    #
    #     # Add the button to the container at the bottom (default)
    #     self.__commands_container.add_button(button, position="top")
    #     return
    #
    # def __add_modify_tools_button(self) -> None:
    #     """Add a button to modify or add tools & placeholders."""
    #     # Create a button using the standard widget generator
    #     button = gui.templates.widgetgenerator.create_pushbutton(
    #         name="modify_tools_button",
    #         icon_name="icons/menu_edit/edit.svg",
    #         text="MODIFY/ADD TOOLS & PLACEHOLDERS",
    #         tooltip="Modify existing tools & placeholders or add new ones",
    #         click_func=self.__on_modify_tools_clicked,
    #     )
    #
    #     # Set size policy to not stretch horizontally
    #     button.setSizePolicy(
    #         qt.QSizePolicy.Policy.Preferred,  # Horizontal - uses preferred size
    #         qt.QSizePolicy.Policy.Fixed,  # Vertical - fixed size
    #     )
    #
    #     # Add the button to the container at the top
    #     self.__placeholder_container.add_button(button, position="top")
    #     return
    #
    # def __on_modify_commands_clicked(self) -> None:
    #     """Handle click on the modify/add commands button."""
    #     # Just print something for now
    #     print("MODIFY/ADD COMMANDS button clicked")
    #     return
    #
    # def __on_modify_tools_clicked(self) -> None:
    #     """Handle click on the modify/add tools & placeholders button."""
    #     # Just print something for now
    #     print("MODIFY/ADD TOOLS & PLACEHOLDERS button clicked")
    #     return
