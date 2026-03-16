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
##  General form used for dialogs
##
from typing import *
import traceback
import qt
import data
import purefunctions
import functions
import iconfunctions
import gui.templates.baseslider
import gui.stylesheets.groupbox
import gui.stylesheets.statusbar
import gui.stylesheets.scrollbar
import gui.stylesheets.tooltip
import os_checker

if TYPE_CHECKING:
    import gui.forms
    import gui.forms.homewindow
    import gui.forms.mainwindow
    import gui.templates.widgetgenerator


class GeneralDialog(qt.QDialog):
    savable = data.CanSave.NO
    theme_name = None
    background_image = None
    scroll_area = None
    main_form = None
    main_groupbox = None
    name = None

    @staticmethod
    def check_theme_state():
        return GeneralDialog.theme_name != data.theme["name"]

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """
        :param additional_clean_list:   Additional list of attributes to clean up.
        :param death_already_checked:   Set True if the status of 'self.dead' has already been
                                        checked. The variable 'self.dead' exists to ensure that
                                        an object can only be killed once.
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill GeneralDialog() twice!")
            self.dead = True

        # & Delete additional attributes
        if additional_clean_list is not None:

            def delete_attribute(att_name: str) -> None:
                attr = getattr(self, att_name)
                attr.setParent(None)
                attr.deleteLater()
                delattr(self, att_name)
                return

            self_destruct_list = additional_clean_list
            for att in self_destruct_list:
                delete_attribute(att)

        # * MODE 1: Clean layout - no callback
        # Invoke 'functions.clean_layout()' on the main layout. No callback is provided. Just run
        # the function, close and deparent oneself, then quit.
        if callback is None:
            # $ Clean up self
            if hasattr(self, "main_layout"):
                try:
                    functions.clean_layout(self.main_layout)
                    self.main_layout = None
                except:
                    purefunctions.printc(
                        "\nERROR: GeneralDialog().self_destruct() failed to clean its main "
                        "layout!\n",
                        color="error",
                    )
                    traceback.print_exc()
            else:
                # Nothing to clean up
                pass

            # $ Close and deparent oneself
            try:
                self.close()
                self.setParent(None)  # noqa
                self.deleteLater()
            except:
                purefunctions.printc(
                    "\nERROR: GeneralDialog().self_destruct() failed to close itself, or to "
                    "deparent and delete itself!\n",
                    color="error",
                )
                traceback.print_exc()
            # No callback, just quit
            return

        # * MODE 2: Clean layout - with callback
        # A callback is provided and should be invoked when 'functions.clean_layout()' has com-
        # pleted.
        assert callback is not None

        def finish(*args) -> None:
            self.main_layout = None
            try:
                # $ Close and deparent oneself
                self.close()
                self.setParent(None)  # noqa
                self.deleteLater()
            except:
                purefunctions.printc(
                    "\nERROR: GeneralDialog().self_destruct().finish() failed to close itself, or "
                    "to deparent and delete itself!\n",
                    color="error",
                )
                traceback.print_exc()
            callback(callbackArg)
            return

        # $ Clean up self
        if hasattr(self, "main_layout"):
            try:
                functions.clean_layout((self.main_layout, finish, None))
            except:
                purefunctions.printc(
                    "\nERROR: GeneralDialog().self_destruct(), with callback, failed to clean its "
                    "main layout!\n",
                    color="error",
                )
                traceback.print_exc()
                finish()
            # The finish() submethod will run, because it's either invoked in the try or except
            # block.
            return
        # Nothing to clean up. Just invoke the finish() submethod.
        finish()
        return

    def __init__(
        self,
        parent,
        statusbar=False,
        scroll_layout=True,
    ) -> None:
        """Initialization of dialog and background."""
        super().__init__(parent=parent)
        # I added the variable 'self.dead' to indicate if this GeneralDialog() has died. Normally,
        # it can die only once: when you invoke the self_destruct() method.
        self.dead = False
        self.main_form: Union[
            gui.forms.homewindow.HomeWindow,
            gui.forms.mainwindow.MainWindow,
        ] = parent  # noqa
        self.setObjectName("Dialog")
        self.name = "Dialog"
        self.widget_generator: gui.templates.widgetgenerator = (
            purefunctions.import_module("gui.templates.widgetgenerator")
        )
        # Set the icon to embeetle by default
        # self.setWindowIcon(iconfunctions.get_qicon(data.application_icon_relpath))
        self.setWindowIcon(qt.QIcon(data.application_icon_abspath))
        # Set the special dialog properties
        # self.setWindowFlags(qt.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(
            qt.Qt.WindowType.Dialog
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowSystemMenuHint
            | qt.Qt.WindowType.WindowCloseButtonHint
            | qt.Qt.WindowType.Tool
        )
        # Set the initial opacity
        self.setWindowOpacity(1.0)
        # Dialog geometry
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding
        )
        # Main group box that will be the dialog's main widget
        self._init_main_groupbox(
            statusbar=statusbar,
            scroll_layout=scroll_layout,
        )
        self.scroll_layout = scroll_layout
        # Load images
        self.ok_image = iconfunctions.get_qpixmap("icons/dialog/checkmark.png")
        self.error_image = iconfunctions.get_qpixmap("icons/dialog/cross.png")
        self.warning_image = iconfunctions.get_qpixmap(
            "icons/dialog/warning.png"
        )
        self.write_error_image = iconfunctions.get_qpixmap(
            "icons/gen/no_write_permission.png"
        )

    def _init_background(self):
        background_image = iconfunctions.get_icon_abspath(
            data.theme["form_background_file"]
        )
        style_sheet = """
QDialog {{
    background-color: {0};
    background-image: url({1});
    margin: 0px;
    spacing: 0px;
    padding: 0px;
}}
{2}
{3}
{4}
            """.format(
            data.theme["fonts"]["default"]["background"],
            background_image,
            gui.stylesheets.tooltip.get_default(),
            gui.stylesheets.scrollbar.get_horizontal(),
            gui.stylesheets.scrollbar.get_vertical(),
        )
        self.setStyleSheet(style_sheet)
        if self.scroll_area:
            self.scroll_area.setStyleSheet(f"""
QScrollArea {{
    background: transparent;
    margin: 0px;
    spacing: 3px;
    padding: 0px;
}}
            """)

        self.main_groupbox.update_style()

    def _reset_fixed_size(self):
        policy = qt.QSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.MinimumExpanding,
        )
        self.setSizePolicy(policy)

    def _init_main_groupbox(
        self,
        statusbar=False,
        scroll_layout=True,
    ):
        """"""
        top_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            self.widget_generator.create_layout(vertical=True),
        )
        self.top_layout = top_layout
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSizeConstraint(
            qt.QLayout.SizeConstraint.SetMinimumSize
        )
        self.top_layout.setSpacing(0)
        self.setLayout(top_layout)

        self.upper_groupbox: qt.QGroupBox = (
            self.widget_generator.create_borderless_groupbox(
                name="UpperGroupBox",
                parent=self,
            )
        )
        self.upper_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.MinimumExpanding,
        )
        upper_layout: qt.QVBoxLayout = self.widget_generator.create_layout(
            vertical=True
        )
        self.upper_layout = upper_layout
        self.upper_layout.setContentsMargins(10, 10, 10, 10)
        self.upper_layout.setSizeConstraint(
            qt.QLayout.SizeConstraint.SetMinimumSize
        )
        self.upper_layout.setSpacing(0)
        self.upper_groupbox.setLayout(upper_layout)

        self.main_groupbox: qt.QGroupBox = (
            self.widget_generator.create_borderless_groupbox(
                name="MainGroupBox",
                parent=self,
                transparent_background=False,
            )
        )
        self.main_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.MinimumExpanding,
        )
        upper_layout.addWidget(self.main_groupbox)

        if scroll_layout:
            self.scroll_area = self.widget_generator.create_scroll_area()
            self.scroll_area.setSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
            self.scroll_area.setWidget(self.upper_groupbox)
            top_layout.addWidget(self.scroll_area)
        else:
            top_layout.addWidget(self.upper_groupbox)
        if statusbar:
            self.add_statusbar()
        self._init_background()
        return

    def _create_groupbox(self, name: str, text: str) -> qt.QGroupBox:
        """"""
        groupbox = self.widget_generator.create_groupbox(
            name, text, parent=self.main_groupbox
        )
        return groupbox

    def _create_groupbox_with_layout(
        self,
        name=None,
        text=None,
        vertical=True,
        borderless=False,
        background_color=None,
        spacing=None,
        margins=None,
        h_size_policy=None,
        v_size_policy=None,
        adjust_margins_to_text=False,
    ):
        if h_size_policy is None:
            h_size_policy = qt.QSizePolicy.Policy.Expanding
        if v_size_policy is None:
            v_size_policy = qt.QSizePolicy.Policy.Expanding
        return self.widget_generator.create_groupbox_with_layout(
            name=name,
            text=text,
            vertical=vertical,
            borderless=borderless,
            background_color=background_color,
            spacing=spacing,
            margins=margins,
            h_size_policy=h_size_policy,
            v_size_policy=v_size_policy,
            adjust_margins_to_text=adjust_margins_to_text,
        )

    def _create_vertical_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignVCenter
        )
        return layout

    def _create_horizontal_layout(self):
        layout = qt.QHBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignVCenter
        )
        return layout

    def _create_textbox(
        self,
        name,
        parent=None,
        func=None,
        read_only=False,
        enabled=True,
        h_size_policy=None,
        v_size_policy=None,
        no_border=False,
        ints_only=False,
        max_length=None,
    ) -> "gui.templates.widgetgenerator.TextBox":
        """

        :param name:
        :param parent:
        :param func:
        :param read_only:
        :param enabled:
        :param h_size_policy:
        :param v_size_policy:
        :param no_border:
        :param ints_only:
        :param max_length:
        :return:
        """
        if h_size_policy is None:
            h_size_policy = qt.QSizePolicy.Policy.Expanding
        if v_size_policy is None:
            v_size_policy = qt.QSizePolicy.Policy.Expanding
        textbox = self.widget_generator.create_textbox(
            name,
            parent=parent,
            func=func,
            read_only=read_only,
            enabled=enabled,
            h_size_policy=h_size_policy,
            v_size_policy=v_size_policy,
            no_border=no_border,
            ints_only=ints_only,
            max_length=max_length,
        )
        return textbox

    def _create_combobox(self, name, minimum_size=(340, 22)):
        combobox = qt.QComboBox()
        combobox.setFont(data.get_general_font())
        combobox.setObjectName(name)
        combobox.setMinimumSize(*minimum_size)
        return combobox

    def _create_label(self, text=None, bold=False):
        label = self.widget_generator.create_label()
        font = data.get_general_font()
        font.setBold(bold)
        label.setFont(font)
        label.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        if text is not None:
            label.setText(text)
        return label

    def _create_check_label(self, name, size):
        check_label = self.widget_generator.create_label()
        check_label.setFixedSize(*(int(x) for x in size))
        check_label.setPixmap(self.error_image)
        check_label.setScaledContents(True)
        check_label.setObjectName(name)

        def mouseReleaseEvent(event: qt.QMouseEvent) -> None:
            try:
                # Try with passing a QPoint() as first parameter
                point = functions.get_position(event)
                if isinstance(point, qt.QPointF):
                    point = point.toPoint()
                qt.QToolTip.showText(
                    point, check_label.toolTip(), check_label, qt.QRect(), 0
                )
            except:
                # Try with passing a QPointF() as first parameter
                point = functions.get_position(event)
                if isinstance(point, qt.QPoint):
                    point = qt.QPointF(point)
                qt.QToolTip.showText(
                    point,  # noqa
                    check_label.toolTip(),
                    check_label,
                    qt.QRect(),
                    0,
                )
            return

        check_label.mouseReleaseEvent = mouseReleaseEvent
        return check_label

    def _create_check_box(self, parent, name, size):
        check_box = gui.helpers.buttons.CheckBox(parent, name, size)
        return check_box

    def _set_widget_message(self, widget, message):
        def enter(event):
            if widget.isEnabled() == True:
                if hasattr(self, "display_message"):
                    self.display_message(message)
                if hasattr(self, "statusbar"):
                    self.statusbar.showMessage(message)

        def leave(event):
            if widget.isEnabled() == True:
                if hasattr(self, "display_message"):
                    self.display_message("")
                if hasattr(self, "statusbar"):
                    self.statusbar.showMessage("")

        widget.enterEvent = enter
        widget.leaveEvent = leave
        widget.setToolTip(message)
        widget.setStatusTip(message)

    def _create_pushbutton(
        self, name, tool_tip, icon_name, size, checkable=False
    ):
        button = gui.helpers.buttons.CustomPushButton(
            parent=self,
            icon_path=icon_name,
            icon_size=qt.create_qsize(size[0] - 6, size[1] - 6),
        )
        if checkable == True:
            button.setCheckable(True)
        button.setToolTip(tool_tip)

        def enter_func():
            if button.isEnabled() == True:
                self.display_message(tool_tip)

        button.set_enter_function(enter_func)

        def leave_func():
            if button.isEnabled() == True:
                self.display_message("")

        button.set_leave_function(leave_func)
        button.enable()
        return button

    def _create_tabwidget(self, name):
        tabs = qt.QTabWidget()
        tabs.setObjectName(name)
        return tabs

    def _create_search_replace_tabwidget(self, name):
        class CustomTabBar(qt.QTabBar):
            """Custom tab bar used to color the tabs according to the
            functionality."""

            mouseHover = qt.pyqtSignal(int)

            def __init__(self, parent=None):
                super().__init__(parent)

            def paintEvent(self, event):
                super().paintEvent(event)
                parent = self.parent_reference
                painter = qt.QStylePainter(self)
                original_brush = painter.brush()
                opt = qt.QStyleOptionTab()
                painter.save()

                for i in range(self.count()):
                    self.initStyleOption(opt, i)
                    # Check if the file is a project directory file
                    if parent.current_index == i:
                        painter.setPen(qt.QPen(qt.QColor("#ffffffff")))
                        if i == 0:
                            painter.setBrush(qt.QBrush(qt.QColor("#fffce94f")))
                        elif i == 1:
                            painter.setBrush(qt.QBrush(qt.QColor("#ff8ae234")))
                        elif i == 2:
                            painter.setBrush(qt.QBrush(qt.QColor("#ff729fcf")))
                        else:
                            painter.setBrush(qt.QBrush(qt.QColor("#ffad7fa8")))
                        #                        opt.palette.setBrush(
                        #                            qt.QPalette.ColorRole.WindowText,
                        #                            qt.QColor("#ffffffff")
                        #                        )
                        painter.drawRect(opt.rect)
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                        )
                    #                        painter.drawItemText(
                    #                            opt.rect, 0, opt.palette, True, opt.text
                    #                        )
                    else:
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabShape, opt
                        )
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTab, opt
                        )
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                        )
                painter.restore()

            def event(self, event):
                result = super().event(event)
                if isinstance(event, qt.QHoverEvent):
                    tab_number = self.tabAt(event.pos())
                    self.mouseHover.emit(tab_number)
                return result

            def __init__(self, parent):
                # Initialize superclass
                super().__init__(parent)
                # Store the main form reference
                self.parent_reference = parent

        tabs = self._create_tabwidget(name)
        tabs.current_index = 0
        custom_tab_bar = CustomTabBar(tabs)
        tabs.setTabBar(custom_tab_bar)
        return tabs

    def _set_fixed_policy(self, widget):
        widget.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Fixed,
                qt.QSizePolicy.Policy.Fixed,
            )
        )

    def _create_slider(self, *args) -> gui.templates.baseslider.BaseSlider:
        """"""
        slider = gui.templates.baseslider.BaseSlider(*args)
        return slider

    def _create_ticked_slider(
        self,
        *args,
        units_per_tick: int = 10,
    ) -> gui.templates.baseslider.TickedSlider:
        """"""
        slider = gui.templates.baseslider.TickedSlider(
            *args, units_per_tick=units_per_tick
        )
        return slider

    def add_statusbar(self):
        self.statusbar = qt.QStatusBar(self)
        self.statusbar.setStyleSheet(gui.stylesheets.statusbar.get_default())
        self.top_layout.addWidget(self.statusbar)
        self.top_layout.setAlignment(
            self.statusbar, qt.Qt.AlignmentFlag.AlignBottom
        )
        return self.statusbar

    def write_to_statusbar(self, message, msec=0, color=None):
        if color is None:
            color = data.theme["fonts"]["default"]["color"]
        self.statusbar.setStyleSheet(
            gui.stylesheets.statusbar.get_default(color)
        )
        self.statusbar.showMessage(message, msec)

    def progressbar_show(self, value, minimum, maximum):
        # Progress bar
        if hasattr(self, "progressbar") == False:
            self.progressbar = gui.templates.baseprogressbar.BaseProgressBar(
                color="green"
            )
        if hasattr(self, "progress_label") == False:
            self.progress_label = None
        progressbar = self.progressbar
        progressbar.setMinimum(minimum)
        progressbar.setMaximum(maximum)
        progressbar.setValue(value)
        progressbar.setTextVisible(False)
        progressbar.setFixedHeight(15)
        progressbar.show()
        # Display widgets
        self.statusbar.addPermanentWidget(progressbar)

    def progressbar_hide(self):
        if self.progressbar is not None:
            self.progressbar.hide()
        if self.progress_label is not None:
            self.progress_label.hide()

    """
    Overridden functions
    """

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        pressed_key = e.key()
        if pressed_key == qt.Qt.Key.Key_Escape:
            self.main_form.display.hide_other_dialogs()

    def center_to_parent(self):
        if self.main_form is not None:
            global_position = self.main_form.mapToGlobal(
                self.main_form.rect().center()
            )
            self.move(
                int(global_position.x() - self.width() / 2),
                int(global_position.y() - self.height() / 2),
            )

    def resize_and_center(
        self,
        width_percentage: float = 1.1,
        height_percentage: float = 1.1,
    ) -> None:
        """"""
        self.resize(
            qt.QSize(
                int(self.main_groupbox.sizeHint().width() * width_percentage),
                int(self.main_groupbox.sizeHint().height() * height_percentage)
                + data.MENUBAR_HEIGHT,
            )
        )
        self.center_to_parent()
        return

    def lock_size(self, lock: bool = True) -> Tuple[int, int]:
        """"""
        width = (
            self.main_groupbox.sizeHint().width()
            + gui.stylesheets.scrollbar.get_bar_width()
        )
        height = self.main_groupbox.sizeHint().height()
        if os_checker.is_os("linux"):
            height += data.MENUBAR_HEIGHT
        if functions.get_screen_size() is not None:
            screen_height = functions.get_screen_size().height()
            height_limit = int(screen_height * 9 / 10)
            if height > height_limit:
                height = height_limit
        height *= 1.01
        if lock:
            self.setFixedSize(int(width), int(height))
        else:
            self.resize(int(width), int(height))
        return int(width), int(height)

    def showEvent(self, event: qt.QShowEvent) -> None:
        """"""
        super().showEvent(event)
        self.lock_size(lock=False)
        self.center_to_parent()
        return
