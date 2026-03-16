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
import functools
import qt
import data
import functions
import iconfunctions
import time
import gui.templates.baseobject
import gui.templates.widgetgenerator
import gui.stylesheets.scrollbar


def get_padding() -> int:
    return int((data.get_general_icon_pixelsize()) * 0.30)


class BasicDelegate(qt.QStyledItemDelegate):
    """Base delegate for normal tree widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_style()

    def sizeHint(self, option, index):
        original = super().sizeHint(option, index)
        return qt.create_qsize(
            original.width(), data.get_general_icon_pixelsize()
        )

    def __init_branch_icons(self):
        # Convert SVGs to pre-rendered QPixmaps at the necessary scale
        # This prevents issues with thin lines not being rendered properly
        size = data.get_general_icon_pixelsize()
        branch_pixmaps = {
            "t": iconfunctions.get_qpixmap(
                data.theme["tree_widget_branch_images"]["t"],
                width=size,
                height=size,
            ),
            "t-add": iconfunctions.get_qpixmap(
                data.theme["tree_widget_branch_images"]["t-add"],
                width=size,
                height=size,
            ),
            "l": iconfunctions.get_qpixmap(
                data.theme["tree_widget_branch_images"]["l"],
                width=size,
                height=size,
            ),
            "l-add": iconfunctions.get_qpixmap(
                data.theme["tree_widget_branch_images"]["l-add"],
                width=size,
                height=size,
            ),
            "i": iconfunctions.get_qpixmap(
                data.theme["tree_widget_branch_images"]["line"],
                width=size,
                height=size,
            ),
            "empty": iconfunctions.get_qpixmap(
                "icons/arrow/spacer/empty.png", width=size, height=size
            ),
        }

        # Convert pixmaps to icons
        self.branch_icons = {}
        for k, pixmap in branch_pixmaps.items():
            icon = qt.QIcon()
            icon.addPixmap(pixmap)
            self.branch_icons[k] = icon

        return

    def update_style(self, *args):
        self.__init_branch_icons()

    def get_branch_icon(self, index, level):
        model = self.parent().model()
        row = index.row()
        column = index.column()

        ## Get sibling states
        # Above
        has_siblings_above = False
        if row > 0:
            has_siblings_above = index.siblingAtRow(row - 1).isValid()
        # Below
        has_siblings_below = index.siblingAtRow(row + 1).isValid()

        if not has_siblings_below:
            if level == 0:
                if row == 0:
                    icon = self.branch_icons["l-add"]
                else:
                    icon = self.branch_icons["l"]
            else:
                icon = self.branch_icons["empty"]
        else:
            if level > 0:
                icon = self.branch_icons["i"]
            else:
                if row == 0:
                    icon = self.branch_icons["t-add"]
                else:
                    icon = self.branch_icons["t"]

        return icon

    def set_indentation_and_draw_branches(self, painter, option, index):
        level = -1
        level_images = []
        parent = index

        size = data.get_general_icon_pixelsize()

        while parent != self.parent().rootIndex():
            level += 1
            level_images.append(self.get_branch_icon(parent, level))
            parent = parent.parent()
        level_images.pop()
        indent = level * size
        x_base_offset = option.rect.x()
        option.rect.setX(x_base_offset + indent)

        # Draw branches
        x_offset = x_base_offset
        y_offset = option.rect.y()
        width = size
        height = size

        # Enable high-quality rendering to ensure thin lines are visible
        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(
            qt.QPainter.RenderHint.SmoothPixmapTransform, True
        )

        for i, li in enumerate(reversed(level_images)):
            branch_rect = qt.QRect(x_offset, y_offset, width, height)

            # Draw the branch icon
            li.paint(painter, branch_rect)

            # Adjust offset for next branch icon
            x_offset = x_base_offset + ((i + 1) * size)

        return level

    def manual_paint(self, painter, option, index, level, draw_text=True):
        # Initialize item
        item = self.parent().itemFromIndex(index)
        item_data = item.get_data()
        item_data["level"] = level

        # Initialize option
        option_v4 = qt.QStyleOptionViewItem(option)
        self.initStyleOption(option_v4, index)
        style = option.widget.style()
        if option_v4.state & qt.QStyle.StateFlag.State_MouseOver:
            option_v4.backgroundBrush = qt.QColor(
                data.theme["indication"]["hover"]
            )
        if option_v4.state & qt.QStyle.StateFlag.State_Selected:
            option_v4.palette.setColor(
                qt.QPalette.ColorRole.Highlight,
                qt.QColor(data.theme["indication"]["hover"]),
            )

        # Manual painting of icon, text and additional stuff
        padding = get_padding()
        painter.save()
        # Highlight
        starting_offset = option_v4.rect.x()
        if option_v4.state & qt.QStyle.StateFlag.State_MouseOver:
            if self.parent().symbol_click_type:
                if "mouse-position" in item_data.keys():
                    # Paint icon and text seperately on mouse hover
                    mouse_position = item_data["mouse-position"]
                    highlight_offset = starting_offset
                    highlight_width = option_v4.rect.width()
                    if mouse_position == "icon":
                        highlight_width = data.get_general_icon_pixelsize()
                    elif mouse_position == "text":
                        highlight_offset += data.get_general_icon_pixelsize()
                        highlight_width = (
                            highlight_width - data.get_general_icon_pixelsize()
                        )
                    highlight_rect = qt.QRect(
                        highlight_offset,
                        option_v4.rect.y() + 1,
                        highlight_width,
                        option_v4.rect.height() - 2,
                    )
                else:
                    highlight_rect = qt.QRect(
                        starting_offset,
                        option_v4.rect.y() + 1,
                        option_v4.rect.width(),
                        option_v4.rect.height() - 2,
                    )
            else:
                highlight_rect = qt.QRect(
                    starting_offset,
                    option_v4.rect.y() + 1,
                    option_v4.rect.width(),
                    option_v4.rect.height() - 2,
                )
            color = qt.QColor(data.theme["indication"]["hover"])
            painter.setPen(qt.QPen(color))
            painter.setBrush(qt.QBrush(color))
            painter.drawRect(highlight_rect)
            self.parent().update()

        elif "highlight" in item_data and item_data["highlight"] == True:
            highlight_rect = qt.QRect(
                starting_offset,
                option_v4.rect.y() + 1,
                option_v4.rect.width(),
                option_v4.rect.height() - 2,
            )
            color = qt.QColor(data.theme["indication"]["hover"])
            painter.setPen(qt.QPen(color))
            painter.setBrush(qt.QBrush(color))
            painter.drawRect(highlight_rect)

            def dehighlight(*args):
                item.get_data()["highlight"] = False
                self.parent().repaint()

            qt.QTimer.singleShot(1000, dehighlight)

        elif "selected" in item_data and item_data["selected"] == True:
            selected_rect = qt.QRect(
                starting_offset,
                option_v4.rect.y() + 1,
                option_v4.rect.width(),
                option_v4.rect.height() - 2,
            )
            color = qt.QColor(data.theme["indication"]["hover"])
            painter.setPen(qt.QPen(color))
            painter.setBrush(qt.QBrush(color))
            painter.drawRect(selected_rect)

        # Icon
        if option_v4.icon:
            starting_offset += 1
            icon_rect = qt.QRect(
                starting_offset,
                option_v4.rect.y() + 1,
                data.get_general_icon_pixelsize() - 2,
                data.get_general_icon_pixelsize() - 2,
            )
            starting_offset += data.get_general_icon_pixelsize() - 2
            option_v4.icon.paint(painter, icon_rect)
        # Expand button
        if item.childCount() > 0 and not item.isExpanded():
            expand_icon_rect = qt.QRect(
                starting_offset,
                option_v4.rect.y(),
                padding,
                data.get_general_icon_pixelsize(),
            )
            # Draw as icon
            painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(
                qt.QPainter.RenderHint.SmoothPixmapTransform, True
            )
            expand_icon = iconfunctions.get_qicon(
                data.theme["tree_widget_branch_images"]["expand_arrow"]
            )
            expand_icon.paint(painter, expand_icon_rect)
        starting_offset += padding + 1
        # Text
        if draw_text:
            if item.get_icon() is None:
                starting_offset = option_v4.rect.x()
            text_rect = qt.QRect(
                starting_offset,
                option_v4.rect.y(),
                option_v4.rect.width(),
                option_v4.rect.height(),
            )
            painter.setPen(
                qt.QPen(qt.QColor(data.theme["fonts"]["default"]["color"]))
            )
            painter.setFont(data.get_general_font())
            painter.drawText(
                text_rect,
                qt.Qt.AlignmentFlag.AlignLeft
                | qt.Qt.AlignmentFlag.AlignVCenter,
                option_v4.text,
            )

        painter.restore()

        return starting_offset

    def paint(self, painter, option, index):
        level = self.set_indentation_and_draw_branches(painter, option, index)
        self.manual_paint(painter, option, index, level)


class RichTextDelegate(BasicDelegate):
    """Generic HTML rendering delegate."""

    html_item_cache = {}

    def paint(self, painter, option, index):
        option_v4 = qt.QStyleOptionViewItem(option)

        self.initStyleOption(option_v4, index)
        item = self.parent().itemFromIndex(index)
        item_data = item.get_data()
        doc = self.make_text(item.id, item_data)

        # Indentation and branches
        level = self.set_indentation_and_draw_branches(
            painter, option_v4, index
        )

        style = option.widget.style()

        starting_offset = self.manual_paint(
            painter, option_v4, index, level, draw_text=False
        )

        painter.save()
        rect = style.subElementRect(
            qt.QStyle.SubElement.SE_ItemViewItemText, option_v4, None
        )
        rect.setX(starting_offset - 3)
        painter.translate(rect.topLeft())
        painter.setClipRect(rect.translated(-rect.topLeft()))
        context = qt.QAbstractTextDocumentLayout.PaintContext()
        if option_v4.state & qt.QStyle.StateFlag.State_Selected:
            context.palette.setColor(
                qt.QPalette.ColorRole.Text,
                option.palette.color(
                    qt.QPalette.ColorGroup.Active,
                    qt.QPalette.ColorRole.HighlightedText,
                ),
            )
        doc.documentLayout().draw(painter, context)
        painter.restore()

    def sizeHint(self, option, index):
        item = self.parent().itemFromIndex(index)
        item_data = item.get_data()
        doc = self.make_text(item.id, item_data)
        level = -1
        parent = index
        while parent != self.parent().rootIndex():
            level += 1
            parent = parent.parent()

        width = doc.idealWidth() + (level * data.get_general_icon_pixelsize())
        height = data.get_general_icon_pixelsize()
        return qt.create_qsize(width, height)

    def updateEditorGeometry(self, editor, option, index):
        size = data.get_general_icon_pixelsize()
        # Get the indentation level of the item
        model = self.parent().model()
        row = index.row()
        column = index.column()
        item = self.parent().itemFromIndex(index)
        level = 0
        parent = index.parent()
        while parent != self.parent().rootIndex():
            level += 1
            parent = parent.parent()
        # Get the text position of the item
        text_rect = option.widget.style().subElementRect(
            qt.QStyle.SubElement.SE_ItemViewItemText, option, None
        )
        # Set the editor position
        geo = qt.QRect(
            int(level * size),
            int(text_rect.y()) - 1,
            int(editor.geometry().width()) * 4,
            int(size),
        )
        editor.setGeometry(geo)

    def make_text(self, id, item_data):
        html_text = item_data["html"]
        key = id
        if key in self.html_item_cache.keys():
            if self.html_item_cache[key]["html-text-cache"] == html_text:
                return self.html_item_cache[key]["html-doc"]
        else:
            self.html_item_cache[key] = {}
        doc = qt.QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultStyleSheet(
            f"""
            td {{
                background-color: transparent;
                color: {data.theme["fonts"]["default"]["color"]};
                font-size: {data.get_general_font_pointsize()}pt;
                font-weight: normal;
                spacing: 0px;
                padding: 0px;
                padding-right: 2px;
                margin: 0px;
                vertical-align: middle;
                text-align: center;
            }}
            .image {{
                display: table-cell;
                vertical-align: bottom;
            }}
        """
        )
        doc.setDefaultFont(data.get_general_font())
        processed_text = self.process_text(html_text)
        doc.setHtml(processed_text)
        self.html_item_cache[key]["html-text-cache"] = html_text
        self.html_item_cache[key]["html-doc"] = doc
        return doc

    def process_text(self, in_text):
        size = int(data.get_general_icon_pixelsize() * 0.75)
        if "<<size-template>>" in in_text:
            template = 'width="{}" height="{}"'.format(size, size)
            out_text = in_text.replace("<<size-template>>", template)
        else:
            out_text = in_text
        return out_text

    def update_style(self, *args):
        super().update_style(*args)
        self.html_item_cache = {}
        self.parent().update()


class FileTreeTextDelegate(RichTextDelegate):
    """Used by the NewFileTree."""

    def make_text(self, id, item_data):
        html_text = item_data["html"]
        key = item_data["path"]
        if key in self.html_item_cache.keys():
            if self.html_item_cache[key]["html-text-cache"] == html_text:
                return self.html_item_cache[key]["html-doc"]
        else:
            self.html_item_cache[key] = {}
        doc = qt.QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultStyleSheet(
            f"""
            td {{
                background-color: transparent;
                color: {data.theme["fonts"]["default"]["color"]};
                font-size: {data.get_general_font_pointsize()}pt;
                font-weight: normal;
                spacing: 0px;
                padding: 0px;
                padding-right: 2px;
                margin: 0px;
                vertical-align: middle;
                text-align: center;
            }}
            .image {{
                display: table-cell;
                vertical-align: bottom;
            }}
        """
        )
        doc.setDefaultFont(data.get_general_font())
        processed_text = self.process_text(html_text)
        doc.setHtml(processed_text)
        self.html_item_cache[key]["html-text-cache"] = html_text
        self.html_item_cache[key]["html-doc"] = doc
        return doc


class TreeNode(qt.QTreeWidgetItem):
    __data = None
    id = None

    def __init__(self, parent, in_id=None, preceding=None):
        if parent is not None and qt.sip.isdeleted(parent):
            super().__init__()
            return

        if preceding:
            super().__init__(parent, preceding)
        else:
            super().__init__(parent)

        if parent is not None and qt.sip.isdeleted(parent):
            return

        # ID check
        if in_id is None:
            raise Exception(
                "[TreeNode] Node ID has to be a value, but it is: '{}'".format(
                    in_id
                )
            )

        self.id = in_id
        self.__data = {}
        self.__icon_path = None
        self.__icon = None

    def get_data(self):
        return self.__data

    def set_data(self, in_data):
        self.__data = in_data

    def set_icon(self, icon_path: str) -> None:
        if not isinstance(icon_path, str):
            raise Exception("Icon has to be a path, not: {}".format(icon_path))
        self.__icon_path = icon_path
        self.reset_icon()

    def reset_icon(self) -> None:
        if self.__icon_path is None:
            return
        icon = iconfunctions.get_qicon(self.__icon_path)
        self.setIcon(0, icon)
        self.__icon = icon

    def get_icon(self):
        return self.__icon


class FileSystemTreeNode(TreeNode):
    def __lt__(self, other):
        self_data = self.get_data()
        other_data = other.get_data()

        # Newly created nodes should go the bottom
        if self_data["type"] in ("new-file", "new-directory"):
            return False
        elif other_data["type"] in ("new-file", "new-directory"):
            return False

        # Filtering: first directories, then files
        result = True
        if (
            self_data["type"] == "directory"
            and other_data["type"] != "directory"
        ):
            result = False
        elif (
            self_data["type"] != "directory"
            and other_data["type"] == "directory"
        ):
            result = True
        elif self_data["type"] == other_data["type"]:
            if self_data["name"].lower() < other_data["name"].lower():
                result = False
        return result

    def __deepcopy__(self, memodict={}):
        # Used for when deep-copying dictionaries that contain this class
        return None


class TreeWidget(qt.QTreeWidget, gui.templates.baseobject.BaseObject):
    # Signals
    editor_closed = qt.pyqtSignal(object, object)
    mouse_press_signal = qt.pyqtSignal()
    no_item_right_click_signal = qt.pyqtSignal()
    no_item_left_click_signal = qt.pyqtSignal()

    # Variables
    __id_counter = 0
    _blink_counter = None
    item_cache = None
    boxes = None
    symbol_click_type = False

    def __init__(
        self,
        parent,
        main_form,
        name,
        icon,
        style="default",
        _type=None,
        click_type=None,
    ):
        qt.QTreeWidget.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self, parent=parent, main_form=main_form, name=name, icon=icon
        )
        self.boxes = []

        self.__node_id_reset()

        self.setObjectName(name)

        self.setMouseTracking(True)
        self.installEventFilter(self)

        self.setUniformRowHeights(True)
        self.setExpandsOnDoubleClick(False)

        self.setColumnCount(1)
        self.setHeaderLabels(["Items"])
        self.setHeaderHidden(True)
        self.header().setFont(data.get_general_font())
        self.header().setVisible(False)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            0, qt.QHeaderView.ResizeMode.ResizeToContents
        )

        # Add a custom item delegate
        self.base_node = TreeNode
        if _type == "rich-text":
            self.setItemDelegate(RichTextDelegate(self))
        elif _type == "file-tree":
            self.setItemDelegate(FileTreeTextDelegate(self))
            self.base_node = FileSystemTreeNode
        elif _type is None:
            self.setItemDelegate(BasicDelegate(self))
        elif _type is not None:
            raise Exception(f"[TreeWidget] Unknown tree widget type: {_type}")
        self.itemDelegate().closeEditor.connect(self.__editor_closed)

        # Set the special click type if applicable
        if click_type == "symbol-click":
            self.symbol_click_type = True

        # Update styles & sizes
        self.update_style()

        self.itemClicked.connect(self.__click)
        self.itemPressed.connect(self.__press)
        self.itemDoubleClicked.connect(self.__click_double)

        self._blink_counter = 0
        self.item_cache = {}

    def __node_id_reset(self, value=0):
        if not isinstance(value, int):
            raise Exception(
                f"[TreeWidget] Node id has to be an integer, but got '{value}/{value.__class__.__name__}'"
            )
        self.__id_counter = value

    def __node_id_check(self, value):
        if not isinstance(value, int):
            raise Exception(
                f"[TreeWidget] Node id has to be an integer, but got '{value}/{value.__class__.__name__}'"
            )
        if value > -1:
            if value >= self.__id_counter:
                self.__id_counter = value + 1

    #            elif value < self.__id_counter:
    #                raise Exception(
    #                    "[TreeWidget] Cannot add a node with 'id' lower than already " +
    #                    "previously used: {}/{}".format(value, self.__id_counter)
    #                )

    def __node_id_generate(self):
        _id = self.__id_counter
        self.__id_counter += 1
        return _id

    def get_node_id_counter(self):
        return self.__id_counter

    def drawRow(self, painter, option, index):
        if not isinstance(self.itemDelegate(), RichTextDelegate):
            model = self.model()
            row = index.row()
            column = index.column()
            item = self.itemFromIndex(index)
            widget = self.itemWidget(item, 0)
            if widget is not None:
                level = 0
                parent = index.parent()
                while parent != self.rootIndex():
                    level += 1
                    parent = parent.parent()
                geo = widget.geometry()
                if item.get_icon() is not None:
                    if level == 0:
                        indent = data.get_general_icon_pixelsize()
                    else:
                        indent = level * (data.get_general_icon_pixelsize() * 2)
                    indent += get_padding()
                else:
                    indent = level * data.get_general_icon_pixelsize()
                    if level == 0:
                        indent = 2
                # Adjust according to X scroll offset
                x_offset = self.horizontalScrollBar().value()
                # Set the geometry
                geo.setX(indent - x_offset)
                widget.setGeometry(geo)

        super().drawRow(painter, option, index)

    #        rect = self.visualRect(index)
    #        color = qt.QColor("red")
    #        painter.setPen(qt.QPen(color))
    #        painter.setBrush(qt.QBrush(color))
    #        painter.drawRect(option.rect)

    def __editor_closed(self, editor, hint):
        self.editor_closed.emit(editor, hint)

    def sizeHintForColumn(self, column):
        # Adjust column size, so that text on largest row is not cut off
        return int(super().sizeHintForColumn(column) * 1.15)

    #    def visualRect(self, index):
    #        print(super().visualRect(index))
    #        return super().visualRect(index)

    def get_node_tree(self, *args):
        #        timer_start = time.perf_counter()
        def get_node(
            index,
            model_list,
            previous_row_has_sibling,
            previous=[],
        ):
            model = self.model()
            rows = model.rowCount(index)
            cols = model.columnCount(index)
            current_item = self.itemFromIndex(index)

            model_list.append(previous.copy() + ["N", current_item])

            for i in range(rows):
                for j in range(cols):
                    next_index = model.index(i, j, index)
                    next_item = self.itemFromIndex(next_index)
                    row_has_sibling = i != (rows - 1)

                    nxt = previous.copy()
                    if previous_row_has_sibling:
                        nxt[-1] = "|"
                    elif len(nxt) > 0 and (nxt[-1] == "-" or nxt[-1] == "l-"):
                        nxt[-1] = " "
                    elif len(nxt) > 0 and nxt[-1] == ">":
                        nxt[-1] = "|"
                    elif len(nxt) > 0 and nxt[-1] == "+":
                        nxt[-1] = "|"
                    if i == (rows - 1):
                        if next_item.childCount() > 0:
                            nxt.append("l-")
                        else:
                            nxt.append("-")
                    else:
                        nxt.append(">")

                    if model.rowCount(next_index) > 0 and nxt[-1] == ">":
                        nxt[-1] = "+"

                    get_node(next_index, model_list, row_has_sibling, nxt)

        model_list = []
        get_node(self.rootIndex(), model_list, False)
        #        timer_duration = time.perf_counter() - timer_start
        #        print(timer_duration)
        return model_list

    def print_node_tree(self, *args):
        node_tree = self.get_node_tree()
        for item in node_tree:
            print(item)

    def __press(self, *args):
        item, state = args
        buttons = data.application.mouseButtons()
        if buttons == qt.Qt.MouseButton.LeftButton:
            item_data = item.get_data()
            if self.symbol_click_type:
                if item_data is not None and "click_func" in item_data.keys():
                    if "mouse-position" in item_data.keys():
                        mouse_position = item_data["mouse-position"]
                        if (
                            mouse_position == "text"
                            or mouse_position == "icon-text"
                        ):
                            func = item_data["click_func"]
                            if callable(func):
                                func()
            else:
                if item_data is not None and "click_func" in item_data.keys():
                    func = item_data["click_func"]
                    if callable(func):
                        func()

        elif buttons == qt.Qt.MouseButton.RightButton:
            item_data = item.get_data()
            if item_data is not None and "info_func" in item_data.keys():
                func = item_data["info_func"]
                if callable(func):
                    func()

    def __click(self, *args):
        item, column = args
        item_data = item.get_data()
        if self.symbol_click_type:
            if "mouse-position" in item_data.keys():
                mouse_position = item_data["mouse-position"]
                if mouse_position == "icon":
                    if item.childCount() > 0:
                        item.setExpanded(not item.isExpanded())
                elif mouse_position == "text":
                    pass
                else:
                    pass
        else:
            if item.childCount() > 0:
                item.setExpanded(not item.isExpanded())

    def __click_double(self, *args):
        pass

    def get(self, arg):
        arg_id = arg
        if isinstance(arg, self.base_node):
            arg_id = arg.id
        return self.item_cache[arg_id]

    def has(self, arg):
        arg_id = arg
        if isinstance(arg, self.base_node):
            arg_id = arg.id
        return arg_id in self.item_cache.keys()

    def add(
        self,
        text=None,
        _id=None,
        icon_path=None,
        tooltip=None,
        statustip=None,
        parent=None,
        in_data=None,
        index=None,
        insert_after=None,
        resize_all=True,
        implicit_parent=True,
        create_only=False,
    ):

        # Parent
        if isinstance(parent, int):
            parent = self.get(parent)
        _parent = None
        if implicit_parent:
            _parent = self
        if parent is not None:
            _parent = parent
        # Insertion check
        if insert_after is not None:
            _parent = insert_after.parent()
        if index is not None:
            _parent = None
        # ID check
        if _id is None:
            _id = self.__node_id_generate()
        else:
            self.__node_id_check(_id)
        new_item = self.base_node(_parent, in_id=_id, preceding=insert_after)

        # Text
        if text is not None:
            new_item.setText(0, text)

        # Icon
        if icon_path is not None:
            if isinstance(icon_path, str):
                new_item.set_icon(icon_path)
            else:
                raise Exception(
                    "[TreeWidget] Unknown icon type: {}".format(
                        icon_path.__class__.__name__
                    )
                )
        if tooltip is not None:
            new_item.setToolTip(0, tooltip)
        if statustip is not None:
            new_item.setStatusTip(0, statustip)
        if in_data is not None:
            new_item.set_data(in_data)
        if parent is None and implicit_parent:
            if not create_only:
                if index is not None:
                    self.insertTopLevelItem(index, new_item)
                else:
                    self.addTopLevelItem(new_item)
        else:
            if index is not None:
                parent.insertChild(index, new_item)

        self.item_cache[new_item.id] = new_item

        # Resize
        if resize_all:
            self.update_style()

        return new_item

    def multi_add(self, items):
        new_items = []
        for item in items:
            insert_after = None
            if "insert_after" in item.keys():
                insert_after = item["insert_after"]
            # Parent
            parent = item["parent"]
            if isinstance(parent, int):
                parent = self.get(parent)
            _parent = None
            if parent is not None:
                _parent = parent
            # Insertion check
            if insert_after is not None:
                _parent = insert_after.parent()
            if "index" in item.keys() and item["index"] is not None:
                _parent = None

            # ID check
            new_id = None
            if "id" in item.keys():
                new_id = item["id"]
            if new_id is None:
                new_id = self.__node_id_generate()
            else:
                self.__node_id_check(new_id)

            new_item = self.base_node(
                _parent, in_id=new_id, preceding=insert_after
            )
            if item["text"] is not None:
                new_item.setText(0, item["text"])
            if "icon" in item.keys():
                icon_path = item["icon"]
                if isinstance(icon_path, str):
                    new_item.set_icon(icon_path)
                else:
                    raise Exception(
                        "[TreeWidget] Unknown icon type: {}".format(
                            icon_path.__class__.__name__
                        )
                    )
            if "data" in item.keys():
                new_item.set_data(item["data"])
            if "tooltip" in item.keys():
                new_item.setToolTip(0, item["tooltip"])
            if "statustip" in item.keys():
                new_item.setStatusTip(0, item["statustip"])

            if item["parent"] is None:
                if (
                    parent is not None
                    and "index" in item.keys()
                    and item["index"] is not None
                ):
                    parent.insertTopLevelItem(item["index"], new_item)
                else:
                    self.addTopLevelItem(new_item)
            else:
                if "index" in item.keys() and item["index"] is not None:
                    parent.insertChild(item["index"], new_item)

            self.item_cache[new_item.id] = new_item
            new_items.append(new_item)

            if "expanded" in item.keys():
                new_item.setExpanded(item["expanded"])

        # Resize
        self.update_style()

        return new_items

    def remove(self, arg):
        arg_id = arg
        if isinstance(arg, self.base_node):
            arg_id = arg.id
        if arg_id in self.item_cache.keys():
            item = self.item_cache.pop(arg_id, None)
            if item is not None:
                try:
                    parent = item.parent()
                    if parent is not None:
                        if isinstance(parent, int):
                            parent = self.get(parent)
                        parent.removeChild(item)
                        item.set_data(None)
                        del item
                    else:
                        self.removeItemWidget(item, 0)
                        for i in range(self.topLevelItemCount()):
                            if item == self.topLevelItem(i):
                                item = self.takeTopLevelItem(i)
                                del item
                                break
                        else:
                            raise Exception(
                                "Item '{}' not found in cache!".format(arg_id)
                            )
                except:
                    item.set_data(None)
                    del item
        else:
            raise Exception("Item '{}' not in cache!".format(arg_id))

    def clear_and_reset(self):
        self.clear()
        self.__node_id_reset()

    def get_item_delegate_for_index(self, index):
        result = self.itemDelegate(index)
        return result

    def change_color(self, arg, html_color):
        arg_id = arg
        if isinstance(arg, self.base_node):
            arg_id = arg.id
        if arg_id in self.item_cache.keys():
            item = self.item_cache[arg_id]
            color = qt.QColor(html_color)
            item.setBackground(1, qt.QBrush(color))

    def _highlight(self, arg):
        arg_id = arg
        if not isinstance(arg_id, int):
            arg_id = arg_id.id
        if isinstance(arg, self.base_node):
            arg_id = arg.id
        if arg_id in self.item_cache.keys():
            item = self.item_cache[arg_id]
            # New style
            self.scrollToItem(item)
            self.clearSelection()
            self.__clear_selected_item()
            item.get_data()["highlight"] = True
            self.update()
        else:
            print(f"Cannot highlight: {arg_id}")

    selected_item_data = None

    def _select(self, arg):
        arg_id = arg
        if not isinstance(arg_id, int):
            arg_id = arg_id.id
        if arg_id in self.item_cache.keys():
            item = self.item_cache[arg_id]
            # New style
            self.scrollToItem(item)
            self.clearSelection()
            self.__clear_selected_item()
            item.get_data()["selected"] = True
            self.selected_item_data = item.get_data()
            self.update()
        else:
            print(f"Cannot select: {arg_id}")

    def __clear_selected_item(self):
        if self.selected_item_data is not None:
            self.selected_item_data.pop("selected", None)
            self.selected_item_data = None

    def sort(self, arg=None):
        def _sort(_arg):
            if _arg is not None:
                arg_id = _arg
                if isinstance(_arg, self.base_node):
                    arg_id = _arg.id
                if arg_id in self.item_cache.keys():
                    self.item_cache[arg_id].sortChildren(
                        0, qt.Qt.SortOrder.AscendingOrder
                    )
            else:
                self.sortItems(0, qt.Qt.SortOrder.AscendingOrder)

        if not hasattr(self, "sort_timer"):
            self.sort_timer = qt.QTimer(self)
            self.sort_timer.setInterval(300)
            self.sort_timer.setSingleShot(True)
            self.sort_timer.timeout.connect(lambda *args: _sort(arg))
        else:
            self.sort_timer.stop()
            try:
                self.sort_timer.timeout.disconnect()
            except:
                pass
            self.sort_timer.timeout.connect(lambda *args: _sort(arg))
        self.sort_timer.start()

    def get_child_count(self):
        count = 0
        iterator = qt.QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            count += 1
            iterator += 1
        return count

    def iterate_items(self, root=None):
        if root is not None:
            iterator = qt.QTreeWidgetItemIterator(root)
        else:
            iterator = qt.QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            yield item
            iterator += 1

    def create_groupbox(self):
        gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
            borderless=True,
            vertical=False,
        )
        gb.setSizePolicy(
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Maximum,
        )
        gb.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        layout = gb.layout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 1, 3, 1)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetMinimumSize)
        self.boxes.append(gb)
        return gb

    def create_label(self, text, tooltip):
        # Label
        label = gui.templates.widgetgenerator.create_label(
            text=text,
            selectable_text=False,
            tooltip=tooltip,
            statustip=tooltip,
        )
        label.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        label.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        return label

    def add_spacing(self, layout):
        fill = qt.QWidget()
        fill.setFixedWidth(50)
        layout.addWidget(fill)
        layout.addStretch()

    def create_button_option(
        self,
        label_text,
        button_text,
        tooltip,
        function,
        icon,
        extra_button=None,
        extra_button_custom_resize_func=None,
    ):
        gb = self.create_groupbox()

        # Layout reference
        layout = gb.layout()

        # Button
        h_padding = 10
        v_padding = 0
        height_offset = 4
        button_size = (
            functions.get_text_width(button_text)
            + data.get_general_icon_pixelsize()
            + h_padding,
            data.get_general_icon_pixelsize() - height_offset + v_padding,
        )
        button = gui.templates.widgetgenerator.create_pushbutton(
            parent=gb,
            name="tree-widget-button",
            tooltip=tooltip,
            icon_name=icon,
            size=button_size,
            click_func=function,
            text=button_text,
            style="tree-widget",
        )
        button.icon_scale = 0.75
        button.setToolTip(tooltip)
        button.setStatusTip(tooltip)
        layout.addWidget(button)
        layout.setAlignment(
            button,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        gb.button = button

        # Label
        label = self.create_label(label_text, tooltip)
        label.set_colors(
            background_color="transparent",
        )

        def click_func(*args):
            function()

        label.click_signal.connect(click_func)
        layout.addWidget(label)
        layout.setAlignment(
            label,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        gb.label = label

        # Extra button
        if extra_button is not None:
            layout.addWidget(extra_button)
            layout.setAlignment(
                extra_button,
                qt.Qt.AlignmentFlag.AlignLeft
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
            gb.extra_button = extra_button

        # Stretch to fill empty space
        self.add_spacing(layout)

        # Updating the style
        def update_style():
            if not qt.sip.isdeleted(label):
                label.update_style()
            if not qt.sip.isdeleted(button):
                button.update_style(
                    (
                        functions.get_text_width(button_text)
                        + data.get_general_icon_pixelsize()
                        + h_padding,
                        data.get_general_icon_pixelsize()
                        - height_offset
                        + v_padding,
                    )
                )
            if extra_button_custom_resize_func is not None:
                extra_button_custom_resize_func()

        gb.update_style = update_style
        return gb

    def update_style(self):
        self.setFont(data.get_general_font())
        self.setIconSize(
            qt.create_qsize(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            )
        )
        self.setIndentation(0)
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_horizontal()
        )
        self.verticalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_vertical()
        )

        # Update delegate
        if self.itemDelegate() is not None and hasattr(
            self.itemDelegate(), "update_style"
        ):
            self.itemDelegate().update_style()

        # Resize all groupboxes
        for gb in self.boxes:
            gb.update_style()

        # Reset all icons
        for item in self.iterate_items():
            item.reset_icon()

    def eventFilter(self, obj, event):
        if event.type() == qt.QEvent.Type.MouseMove:
            self.__check_cursor_position(event.pos())
        return gui.templates.baseobject.BaseObject.eventFilter(self, obj, event)

    def setItemWidget(self, item, column, widget):
        widget.setMouseTracking(True)
        for it in widget.children():
            if hasattr(it, "setMouseTracking"):
                it.setMouseTracking(True)
        super().setItemWidget(item, column, widget)

    def mousePressEvent(self, event):
        self.mouse_press_signal.emit()
        self.__check_no_item_click(event.pos())
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.symbol_click_type:
            self.__check_cursor_position(event.pos())

    def __check_cursor_position(self, position):
        item = self.itemAt(position)
        if item:
            cursor_position = functions.get_position(None)
            tree_position: Union[qt.QPoint, qt.QPointF] = self.mapFromGlobal(
                cursor_position
            )
            widget_position: Union[qt.QPoint, qt.QPointF] = self.visualItemRect(
                item
            ).topLeft()
            # Convert to QPointF()
            if isinstance(tree_position, qt.QPoint):
                tree_position = qt.QPointF(tree_position)
            if isinstance(widget_position, qt.QPoint):
                widget_position = qt.QPointF(widget_position)
            relative_position: qt.QPointF = tree_position - widget_position
            item_data = item.get_data()
            if "level" in item_data.keys():
                level = item_data["level"]
                x_position = relative_position.x()
                size = data.get_general_icon_pixelsize()
                if x_position < (level * size):
                    # Branch icons
                    item_data["mouse-position"] = "branch"
                elif x_position > (level * size) and x_position < (
                    (level + 1) * size
                ):
                    # Icon
                    if item.childCount() == 0:
                        item_data["mouse-position"] = "icon-text"
                    else:
                        item_data["mouse-position"] = "icon"
                elif x_position > ((level + 1) * size):
                    # Text
                    if item.childCount() == 0:
                        item_data["mouse-position"] = "icon-text"
                    else:
                        item_data["mouse-position"] = "text"

    def __check_no_item_click(self, position):
        item = self.itemAt(position)
        if not item:
            buttons = data.application.mouseButtons()
            if buttons == qt.Qt.MouseButton.LeftButton:
                self.no_item_left_click_signal.emit()
            elif buttons == qt.Qt.MouseButton.RightButton:
                self.no_item_right_click_signal.emit()
