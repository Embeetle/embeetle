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

"""Modular Tile System for creating customizable dashboards with draggable
tiles.

This module implements a flexible, reusable tile system that can be used to
create customizable dashboards. The implementation is built around the following
key components:

1. Tile:
   - Subclassed from qt.QFrame
   - Base draggable tile component that can be reordered within a container
   - Implements drag functionality through mousePressEvent and mouseMoveEvent
   - Uses QDrag and QMimeData to create a draggable representation
   - Stores container_title and tile_id in mime data for identification
   - Uses QGraphicsOpacityEffect to become semi-transparent during drag
     operations
   - Creates visual feedback with both drag pixmap and semi-transparent original

2. TileDropIndicator:
   - Subclassed from qt.QFrame
   - Visual indicator showing the potential insertion point during drag
     operations
   - Appears as a horizontal blue line at drop locations
   - Uses absolute positioning to avoid disrupting the layout

3. TileContainer:
   - Subclassed from qt.QFrame
   - Main user-facing widget for creating tile sections
   - Provides a visual frame with a header and scrollable content
   - Manages a collection of tiles within a specific container
   - Handles drag and drop events for reordering tiles
   - Uses a biased drop zone system (60/40) for more natural drop targeting
   - Prevents dropping a tile onto itself and handles edge cases
   - Exposes simplified API for adding tiles

4. TileTabWidget:
   - Subclassed from qt.QStackedWidget and gui.templates.baseobject.BaseObject
   - Base widget that serves as a container for the tile system
   - Extends QStackedWidget for potential multi-page dashboard implementations
   - Handles recursive finding and sizing of nested QSplitter widgets

NOTES:
    - Every widget gets its own `update_style()` method, which gets called on a
      theme change. It should update the style of the widget itself, and all its
      children.
"""

# Standard library
from __future__ import annotations
from typing import *

# Local
import qt
import widget_cleanup
import gui.templates.baseobject
import gui.templates.textmanipulation
import gui.templates.widgetgenerator
import data

if TYPE_CHECKING:
    import gui.forms.mainwindow
    import gui.forms.homewindow


class Tile(widget_cleanup.WidgetCleaner, qt.QFrame):
    """A draggable tile for the dashboard.

    The tile can be dragged up and down within its container but not between
    different containers. To differentiate between containers, each tile saves
    the ID of the container it belongs to (see the `self.__container_id`
    variable).
    """

    def __init__(
        self,
        parent: qt.QWidget,
        tile_id: str,
        title: Optional[str] = None,
    ) -> None:
        """Initialize the dashboard tile.

        Args:
            parent:  The parent widget.
            tile_id: A unique identifier for this tile.
            title:   [Optional] The title of the tile. If provided, a QLabel()
                     with this text is created and added to the layout of this
                     Tile().

        NOTE 1:
            Aside from its own `tile_id`, a Tile() also stores a `container_id`.
            It is not passed in the constructor, but later on when the Tile() is
            added to the layout of a container (see the `set_container_id()`
            method).

        NOTE 2:
            The parent parameter is not important. The Tile()-instance gets
            reparented in the `TileContainer().add_tile()` method anyway, which
            adds it to the layout of the internal tile content widget. Passing
            `None` for the parent would be acceptable, but not advisable as it
            slows down PyQt6.
        """
        super().__init__(parent)
        self.__tile_id = tile_id
        self.__container_id = None
        self.__drag_start_position = None
        # self.setMinimumHeight(50)
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Minimum,
        )
        self.setLayout(qt.QVBoxLayout())
        self.layout().setContentsMargins(10, 5, 10, 5)
        self.layout().setSpacing(5)
        self.__set_normal_style()
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        # & TITLE LABEL
        if title:
            self.layout().addWidget(
                gui.templates.widgetgenerator.create_label(
                    text=title,
                    bold=True,
                    selectable_text=False,
                )
            )
        return

    def __set_normal_style(self) -> None:
        """Set the normal appearance of the tile."""
        # Remove any opacity effect and set normal stylesheet
        self.setGraphicsEffect(None)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {data.theme["shade"][3]};
                border: none;
                border-radius: 2px;
            }}
            """
        )
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        self.__set_normal_style()
        return

    def set_container_id(self, container_id: str) -> None:
        """Set the ID of the container this tile belongs to.

        Args:
            container_id: The unique identifier of the container.
        """
        # Use assertion to make sure this function only runs once
        assert self.__container_id is None
        self.__container_id = container_id
        return

    def get_container_id(self) -> str:
        """Get the ID of the container this tile belongs to.

        Returns:
            The container's ID.
        """
        return self.__container_id

    def get_id(self) -> str:
        """Get the tile's unique identifier.

        Returns:
            The tile's ID.
        """
        return self.__tile_id

    def __set_transparent_style(self) -> None:
        """Set the transparent appearance of the tile for drag operations."""
        # Create a QGraphicsOpacityEffect for proper transparency
        opacity_effect = qt.QGraphicsOpacityEffect(self)
        opacity_effect.setOpacity(0.3)  # 30% opacity (70% transparent)
        self.setGraphicsEffect(opacity_effect)
        return

    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        """Handle mouse press events to start dragging."""
        if event.button() == qt.Qt.MouseButton.LeftButton:
            self.__drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
        return

    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
        """Handle mouse move events for dragging."""
        if (
            not (event.buttons() & qt.Qt.MouseButton.LeftButton)
            or not self.__drag_start_position
        ):
            return super().mouseMoveEvent(event)

        # Check if the drag distance is far enough to start a drag
        if (
            event.position().toPoint() - self.__drag_start_position
        ).manhattanLength() < qt.QApplication.startDragDistance():
            return super().mouseMoveEvent(event)

        # Start the drag operation
        drag = qt.QDrag(self)
        mime_data = qt.QMimeData()

        # Store the source container ID and tile ID in the mime data
        assert self.__container_id is not None
        mime_data.setText(f"{self.__container_id}|{self.__tile_id}")
        drag.setMimeData(mime_data)

        # Create a pixmap of the tile for visual feedback during drag
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())

        # Make the original tile transparent during drag
        self.__set_transparent_style()

        # Execute the drag - this blocks until the drag is done
        drop_action = drag.exec(qt.Qt.DropAction.MoveAction)

        # Restore the tile's normal appearance if it wasn't successfully moved
        # (This won't happen if the tile was successfully moved because the tile
        # will be repositioned with normal styling)
        if drop_action == qt.Qt.DropAction.IgnoreAction:
            self.__set_normal_style()
        return

    def dropEvent(self, event: qt.QDropEvent) -> None:
        """Handle drop events."""
        if event.mimeData().hasText():
            container_id, source_tile_id = event.mimeData().text().split("|", 1)

            # Only accept if from the same container and not this tile
            if (
                container_id == self.__container_id
                and source_tile_id != self.__tile_id
            ):
                # Emit a signal to the parent container to reorder the tiles
                parent = self.parent()
                if hasattr(parent, "handle_tile_reorder"):
                    parent.handle_tile_reorder(source_tile_id, self.__tile_id)
                event.acceptProposedAction()
        return


class TileDropIndicator(widget_cleanup.WidgetCleaner, qt.QFrame):
    """A visual indicator for the drop position."""

    def __init__(self, parent: qt.QWidget) -> None:
        """Initialize the drop indicator widget.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setFixedHeight(6)  # Thin line
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )
        self.__set_normal_style()
        self.setVisible(False)
        return

    def __set_normal_style(self) -> None:
        """Set the normal appearance of the drop indicator."""
        self.setStyleSheet(
            f"""
            background-color: {data.theme.get('dock_point_color_active', '#4a90e2')};
            border-radius: 3px;
            """
        )
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        self.__set_normal_style()
        return


class TileContainer(widget_cleanup.WidgetCleaner, qt.QFrame):
    """Container for a group of related tiles.

    This is the main user-facing widget for creating tile sections in the
    dashboard. It provides a section with a header and a scrollable area for
    tiles.
    """

    def __init__(
        self,
        parent: qt.QWidget,
        title: str,
        container_id: str = None,
    ) -> None:
        """Initialize the tile container.

        Args:
            parent:       The parent widget.
            title:        The title text for the section header.
            container_id: A unique identifier for this container. If not
                          provided, the title will be used as the ID.
        """
        super().__init__(parent)
        self.__container_id = (
            container_id if container_id is not None else title
        )
        self.__container_title = title
        self.__tiles: Dict[str, Tile] = {}
        self.__current_drag_source_id: Optional[str] = None
        self.__drop_index: Optional[int] = None
        self.__is_collapsed = True

        # Create main layout
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetDefaultConstraint)
        self.setLayout(layout)

        # Create header with title and chevron icon
        self.__header_frame = gui.templates.widgetgenerator.create_frame(
            name=f"{title.replace(' ', '')}HeaderFrame",
            layout_vertical=False,
            layout_margins=(5, 5, 5, 5),
            layout_spacing=5,
        )
        self.__header_frame.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )

        # Create clickable header layout with chevron and title
        self.__header_widget = qt.QWidget(self.__header_frame)
        self.__header_widget.setCursor(qt.Qt.CursorShape.PointingHandCursor)
        header_layout = qt.QHBoxLayout(self.__header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Add chevron icon (using right by default since we're collapsed)
        self.__chevron_icon = gui.templates.widgetgenerator.create_label(
            parent=self.__header_widget,
            image="icons/arrow/chevron/chevron_right.svg",
            selectable_text=False,
            transparent_background=True,
        )
        # Set fixed size for the icon
        self.__chevron_icon.setFixedSize(
            data.get_general_icon_pixelsize(),
            data.get_general_icon_pixelsize(),
        )
        header_layout.addWidget(self.__chevron_icon)

        # Add title label
        self.__title_label = gui.templates.widgetgenerator.create_label(
            parent=self.__header_widget,
            text=title,
            bold=True,
            alignment=qt.Qt.AlignmentFlag.AlignLeft
            | qt.Qt.AlignmentFlag.AlignVCenter,
            selectable_text=False,
            transparent_background=True,
        )
        header_layout.addWidget(self.__title_label, 1)  # Give stretch priority

        # Add mouse press event to header widget
        self.__header_widget.mousePressEvent = (
            lambda event: self.__on_header_clicked(event)
        )

        # Add header widget to header frame
        cast(qt.QVBoxLayout, self.__header_frame.layout()).addWidget(
            self.__header_widget
        )
        cast(qt.QVBoxLayout, self.__header_frame.layout()).addStretch(1)

        # Create content area
        self.__content_frame = gui.templates.widgetgenerator.create_frame(
            name=f"{self.__container_id.replace(' ', '')}ContentFrame",
            layout_vertical=True,
            layout_margins=(5, 5, 5, 5),
            layout_spacing=0,
        )

        # Create tile container widget inside the content frame (this replaces
        # _TileContainerWidget)
        self.__tiles_widget = qt.QWidget(self.__content_frame)

        # Set up the tiles widget layout
        self.__tiles_widget.setLayout(qt.QVBoxLayout())
        self.__tiles_widget.layout().setContentsMargins(0, 6, 0, 0)
        self.__tiles_widget.layout().setSpacing(6)  # Standard spacing

        # Add a spacer at the end to push tiles to the top
        cast(qt.QVBoxLayout, self.__tiles_widget.layout()).addStretch(1)

        # Create a drop indicator
        self.__drop_indicator = TileDropIndicator(self.__tiles_widget)

        # Enable drops and mouse tracking
        self.__tiles_widget.setAcceptDrops(True)
        self.__tiles_widget.setMouseTracking(True)

        # Install event filter to handle drag and drop events
        self.__tiles_widget.installEventFilter(self)

        # Hide tiles initially since we start collapsed
        self.__tiles_widget.setVisible(False)
        self.__content_frame.layout().addWidget(self.__tiles_widget)

        # Add header and content to main frame
        self.layout().addWidget(self.__header_frame)
        self.layout().addWidget(self.__content_frame)
        self.__set_normal_style()
        return

    def __set_normal_style(self) -> None:
        """Set the normal appearance"""
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            """
        )
        self.__header_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
            """
        )
        self.__content_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
            """
        )
        return

    def update_style(self) -> None:
        """Update the tile's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        self.__set_normal_style()
        self.__chevron_icon.update_style()
        self.__chevron_icon.update_icon_style()
        self.__title_label.update_style()
        for tile_id, tile in self.__tiles.items():
            if hasattr(tile, "update_style"):
                tile.update_style()
        return

    def get_id(self) -> str:
        """Get the container's unique identifier.

        Returns:
            The container's ID.
        """
        return self.__container_id

    def add_tile(self, tile: Tile) -> None:
        """Add a new tile to this section.

        Args:
            tile: The Tile()-instance to add
        """
        # Set the container ID in the tile
        tile.set_container_id(self.__container_id)

        # Find the position before the spacer
        spacer_index = self.__tiles_widget.layout().count() - 1

        # Insert the tile before the spacer
        cast(qt.QVBoxLayout, self.__tiles_widget.layout()).insertWidget(
            spacer_index, tile
        )

        # Store it in our dictionary
        self.__tiles[tile.get_id()] = tile
        return

    def add_button(
        self, button: qt.QPushButton, position: str = "bottom"
    ) -> qt.QPushButton:
        """Add a button to this container, either at the top or bottom.

        This method adds a button that appears either above all tiles (at the
        top) or below all tiles (at the bottom) in the scrollable area. The
        button is not draggable like the tiles and will always maintain its
        position relative to the tiles.

        Args:
            button:   An existing QPushButton to add
            position: Where to add the button - "top" or "bottom" (default:
                      "bottom")

        Returns:
            The button that was added
        """
        # Get parent frame that contains the tiles_widget
        content_frame = self.__tiles_widget.parentWidget()

        # Create a frame to contain the button with proper spacing
        button_frame = qt.QFrame(content_frame)
        # Set name for identification (includes position)
        button_frame.setObjectName(f"ButtonFrame_{position}")
        button_frame.setLayout(qt.QHBoxLayout())
        button_frame.layout().setContentsMargins(
            0, 0, 5, 5
        )  # Reduced top margin

        # Set alignment to left-align the button without stretching it
        button_frame.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        button_frame.layout().addWidget(button)

        # Make the button frame ignore drag events
        button_frame.setAcceptDrops(False)

        # Add the button to the tiles widget layout
        layout = cast(qt.QVBoxLayout, self.__tiles_widget.layout())

        # First, remove the stretch spacer if it exists
        spacer_index = layout.count() - 1
        if spacer_index >= 0:
            layout_item = layout.itemAt(spacer_index)
            if layout_item and not layout_item.widget():  # It's likely a spacer
                layout.removeItem(layout_item)

        # Add the button at the appropriate position
        if position.lower() == "top":
            # Add at index 0 (before all tiles)
            layout.insertWidget(0, button_frame)
        else:
            # Add at the end (after all tiles)
            layout.addWidget(button_frame)

        # Re-add the stretch spacer to keep everything pushed to the top
        layout.addStretch(1)

        return button

    def __find_drop_position(self, pos: qt.QPoint) -> int:
        """Find the best position to insert a tile based on mouse position.

        If there are buttons at the top or bottom of the tiles, then the tiles
        are draggable only in the area between them. This method is aware of
        button positioning:
        - It identifies both minimum and maximum tile indices to respect buttons
          at both top and bottom
        - It excludes button frames from tile boundary calculations
        - It ensures tiles can only be dropped in the area between top and
          bottom buttons

              Args:
                  pos: The current mouse position in container coordinates.

              Returns:
                  The layout index where a tile should be inserted.
        """
        # Find the tile nearest to the current position
        closest_tile = None
        closest_distance = float("inf")
        closest_position = "above"

        # Find the first and last index that contains actual tiles (not button
        # frames). This allows us to respect buttons at both top and bottom
        min_tile_index = -1
        max_tile_index = -1
        first_tile_found = False
        layout = self.__tiles_widget.layout()

        # Scan the layout to identify the tile boundaries
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Check if it's a ButtonFrame
                if isinstance(
                    widget, qt.QFrame
                ) and widget.objectName().startswith("ButtonFrame_"):
                    continue  # Skip buttons

                # If it's a tile, update boundaries
                if isinstance(widget, Tile):
                    if not first_tile_found:
                        min_tile_index = i
                        first_tile_found = True
                    max_tile_index = i

        for tile_id, tile in self.__tiles.items():
            if tile_id == self.__current_drag_source_id:
                continue  # Skip the source tile

            tile_rect = tile.geometry()

            # Add a bias zone - only consider it "below" if we're in the bottom
            # 40% of the tile. This creates a larger target for "above" (60%)
            # and smaller for "below" (40%) which makes the UI feel more stable
            # when dragging
            bias_point = tile_rect.top() + tile_rect.height() * 0.6

            if pos.y() < bias_point:
                # We're in the top 60% of the tile - consider as "above"
                distance = abs(pos.y() - tile_rect.top())
                if distance < closest_distance:
                    closest_tile = tile
                    closest_distance = distance
                    closest_position = "above"
            else:
                # We're in the bottom 40% of the tile - consider as "below"
                distance = abs(pos.y() - tile_rect.bottom())
                if distance < closest_distance:
                    closest_tile = tile
                    closest_distance = distance
                    closest_position = "below"

        if closest_tile is not None:
            # Get insert position based on closest tile and position
            insert_index = self.__tiles_widget.layout().indexOf(closest_tile)
            if closest_position == "below":
                insert_index += 1

            # Make sure we don't insert past the last tile or before the first
            # tile. This ensures we respect top and bottom buttons
            if insert_index > max_tile_index + 1:
                insert_index = max_tile_index + 1
            elif insert_index < min_tile_index and min_tile_index >= 0:
                insert_index = min_tile_index

            return insert_index

        # If no tiles found (or only the source tile), still respect tile
        # boundaries
        if max_tile_index >= 0:
            # Insert at the end of the tiles section
            return max_tile_index + 1
        elif min_tile_index >= 0:
            # Insert at the beginning of the tiles section
            return min_tile_index

        # If no tiles at all, find the first valid position (after top buttons
        # if any)
        for i in range(self.__tiles_widget.layout().count()):
            item = self.__tiles_widget.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if (
                    isinstance(widget, qt.QFrame)
                    and widget.objectName() == "ButtonFrame_top"
                ):
                    continue  # Skip top buttons
                return i  # First non-button position

        # Fallback to first position if nothing else found
        return 0

    def __update_drop_indicator(self, pos: qt.QPoint) -> None:
        """Update the position of the drop indicator.

        Args:
            pos: The current mouse position in container coordinates.
        """
        # Find the position to insert the tile
        self.__drop_index = self.__find_drop_position(pos)

        # Position the drop indicator at the insertion point
        if self.__drop_index < self.__tiles_widget.layout().count():
            item = self.__tiles_widget.layout().itemAt(self.__drop_index)
            if item and item.widget():
                # Position at the top of the target widget
                target_widget = item.widget()
                self.__drop_indicator.setGeometry(
                    0,  # x position
                    target_widget.geometry().top() - 6,  # y position (3px
                    # above the widget)
                    self.__tiles_widget.width(),  # full width
                    6,  # height
                )
                self.__drop_indicator.raise_()  # Bring to front
                self.__drop_indicator.setVisible(True)
                return

        # If we're at the end, position after the last visible widget
        for i in range(
            self.__tiles_widget.layout().count() - 1, -1, -1
        ):  # Start from end, go backward
            item = self.__tiles_widget.layout().itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                # Position after this widget
                target_widget = item.widget()
                self.__drop_indicator.setGeometry(
                    0,  # x position
                    target_widget.geometry().bottom(),  # y position (below the
                    # widget)
                    self.__tiles_widget.width(),  # full width
                    6,  # height
                )
                self.__drop_indicator.raise_()  # Bring to front
                self.__drop_indicator.setVisible(True)
                return

        # Fallback - hide the indicator
        self.__drop_indicator.setVisible(False)
        return

    def handle_tile_reorder(
        self, source_tile_id: str, target_tile_id: str
    ) -> None:
        """Handle a tile being reordered within this container.

        Args:
            source_tile_id: The ID of the tile being moved.
            target_tile_id: The ID of the tile to move before/after.
        """
        # Only proceed if both tiles exist in this container
        if (
            source_tile_id not in self.__tiles
            or target_tile_id not in self.__tiles
        ):
            return

        # Get the tile widgets
        source_tile = self.__tiles[source_tile_id]
        target_tile = self.__tiles[target_tile_id]

        # Get their current positions
        layout = cast(qt.QVBoxLayout, self.__tiles_widget.layout())
        source_index = layout.indexOf(source_tile)
        target_index = layout.indexOf(target_tile)

        # Don't do anything if they're already adjacent in the correct order
        if source_index == target_index - 1:
            return

        # Remove the source tile from its current position
        layout.removeWidget(source_tile)

        # Insert it at the new position (before the target tile)
        layout.insertWidget(target_index, source_tile)

        # Remove any opacity effect
        source_tile.setGraphicsEffect(None)

        # Hide the drop indicator
        self.__drop_indicator.setVisible(False)
        return

    def __on_header_clicked(self, event: qt.QMouseEvent) -> None:
        """Handle clicks on the container header.

        Args:
            event: The mouse event.
        """
        if event.button() == qt.Qt.MouseButton.LeftButton:
            # Toggle collapsed state
            self.__is_collapsed = not self.__is_collapsed

            # Update chevron icon
            if self.__is_collapsed:
                self.__chevron_icon.set_image(
                    "icons/arrow/chevron/chevron_right.svg"
                )
            else:
                self.__chevron_icon.set_image(
                    "icons/arrow/chevron/chevron_down.svg"
                )

            # Toggle visibility of all tiles
            self.__tiles_widget.setVisible(not self.__is_collapsed)

            # Print for debugging
            print(
                f"Container {self.__container_title} header clicked, collapsed: {self.__is_collapsed}"
            )
        return

    def eventFilter(self, obj: qt.QObject, event: qt.QEvent) -> bool:
        """Filter events for the tile container widget.

        Args:
            obj: The object that received the event.
            event: The event that was received.

        Returns:
            True if the event should be filtered out, False otherwise.
        """
        if obj is self.__tiles_widget:
            if event.type() == qt.QEvent.Type.DragEnter:
                self.__handle_drag_enter(cast(qt.QDragEnterEvent, event))
                return True
            elif event.type() == qt.QEvent.Type.DragMove:
                self.__handle_drag_move(cast(qt.QDragMoveEvent, event))
                return True
            elif event.type() == qt.QEvent.Type.DragLeave:
                self.__handle_drag_leave(cast(qt.QDragLeaveEvent, event))
                return True
            elif event.type() == qt.QEvent.Type.Drop:
                self.__handle_drop(cast(qt.QDropEvent, event))
                return True

        # Let the parent class handle the event
        return super().eventFilter(obj, event)

    def __handle_drag_enter(self, event: qt.QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasText():
            container_id, source_tile_id = event.mimeData().text().split("|", 1)

            # Only accept if from the same container
            if container_id == self.__container_id:
                self.__current_drag_source_id = source_tile_id
                event.acceptProposedAction()

                # Update the drop indicator position
                self.__update_drop_indicator(event.position().toPoint())
        return

    def __handle_drag_move(self, event: qt.QDragMoveEvent) -> None:
        """Handle drag move events."""
        if event.mimeData().hasText():
            container_id, source_tile_id = event.mimeData().text().split("|", 1)

            # Only accept if from the same container
            if container_id == self.__container_id:
                event.acceptProposedAction()

                # Update the drop indicator position
                self.__update_drop_indicator(event.position().toPoint())
        return

    def __handle_drag_leave(self, event: qt.QDragLeaveEvent) -> None:
        """Handle drag leave events."""
        # Hide the drop indicator when drag leaves
        self.__drop_indicator.setVisible(False)
        self.__current_drag_source_id = None
        return

    def __handle_drop(self, event: qt.QDropEvent) -> None:
        """Handle drop events on the container."""
        if event.mimeData().hasText():
            container_id, source_tile_id = event.mimeData().text().split("|", 1)

            # Only accept if from the same container
            if container_id == self.__container_id:
                event.acceptProposedAction()

                # If we don't have a specific drop index, just add at the end
                if self.__drop_index is None:
                    return

                # Get the source tile
                if source_tile_id not in self.__tiles:
                    return
                source_tile = self.__tiles[source_tile_id]

                # Get layout
                layout = cast(qt.QVBoxLayout, self.__tiles_widget.layout())
                source_index = layout.indexOf(source_tile)

                # If trying to insert at the source index or right after, do
                # nothing
                if (
                    self.__drop_index == source_index
                    or self.__drop_index == source_index + 1
                ):
                    # Remove any opacity effect
                    source_tile.setGraphicsEffect(None)
                    self.__drop_indicator.setVisible(False)
                    return

                # Adjust the insert index if it's after the source
                target_index = self.__drop_index
                if target_index > source_index:
                    target_index -= 1

                # Remove and reinsert the tile
                layout.removeWidget(source_tile)
                layout.insertWidget(target_index, source_tile)

                # Remove any opacity effect
                source_tile.setGraphicsEffect(None)

                # Hide the drop indicator
                self.__drop_indicator.setVisible(False)

        # Reset state
        self.__current_drag_source_id = None
        self.__drop_index = None
        return


class TileTabWidget(
    widget_cleanup.WidgetCleaner,
    qt.QStackedWidget,
    gui.templates.baseobject.BaseObject,
):
    """Base widget that serves as a container for the tile system."""

    def __init__(
        self,
        parent: Union[qt.QTabWidget, qt.QFrame, qt.QMainWindow, None],
        main_form: Union[
            gui.forms.mainwindow.MainWindow, gui.forms.homewindow.HomeWindow
        ],
    ) -> None:
        """Initialize the tile tab widget.

        Args:
            parent: The parent widget.
            main_form: The main window or home window.
        """
        qt.QStackedWidget.__init__(self, None)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="NewDashboard",
            icon="icons/gen/dashboard.svg",
        )

        # & MAIN FRAME
        # Contains everything
        self.__main_frame = gui.templates.widgetgenerator.create_frame(
            name="MainFrame",
            parent=self,
            layout_vertical=True,
        )

        scroll_area = gui.templates.widgetgenerator.create_scroll_area()
        scroll_area.setWidget(self.__main_frame)
        self.addWidget(scroll_area)
        self.__set_normal_style()
        return

    def __set_normal_style(self) -> None:
        """Set the normal appearance"""
        self.__main_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize()}pt;
                color: {data.theme["fonts"]["default"]["color"]};
            }}
            """
        )
        return

    def update_style(self) -> None:
        """Update the widget's style based on the current theme."""
        if qt.sip.isdeleted(self):
            return
        # BaseObject doesn't have an update_style method, so we don't call the
        # parent implementation

        # Update main frame style
        self.__set_normal_style()

        # Update styles of all children widgets that have update_style method
        for widget in self.findChildren(qt.QWidget):
            if hasattr(widget, "update_style"):
                widget.update_style()
        return

    def get_main_frame(self) -> qt.QFrame:
        """Get access to the main QFrame() of this tab widget"""
        return self.__main_frame

    def self_destruct(self) -> None:
        """

        :return:
        """
        print("TileTabWidget().self_destruct()")
        super().self_destruct()
        return
