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
import time
import queue
import datetime
import functools
import traceback
import purefunctions
import serverfunctions
import qt
import data
import functions
import iconfunctions
import gui.dialogs.popupdialog
import gui.dialogs.projectcreationdialogs
import gui.dialogs.scalingdialog
import gui.helpers.popupbubble
import gui.helpers.rssfeedparser
import gui.templates.baseappwindow
import gui.templates.basemenu
import gui.templates.baseprogressbar
import gui.templates.treewidget
import gui.templates.widgetgenerator
import gui.stylesheets.button
import gui.stylesheets.combobox
import gui.stylesheets.tooltip
import gui.stylesheets.scrollbar
import gui.stylesheets.textedit
import gui.stylesheets.splitter
import gui.stylesheets.table
import gui.stylesheets.tabbar
import gui.stylesheets.tabwidget
import gui.stylesheets.treewidget
import gui.stylesheets.menubar
import components.actionfilter
import components.thesquid
import settings
import helpdocs.help_texts
import helpdocs.help_subjects.home_window
import hardware_api.chip_unicum
import hardware_api.board_unicum
import hardware_api.hardware_api
import importer
from various.kristofstuff import *


class HomeWindow(gui.templates.baseappwindow.BaseAppWindow):
    DEFAULT_WIDTH = 650
    DEFAULT_HEIGHT = 560

    name: Optional[str] = None
    menubar: Optional[qt.QMenuBar] = None
    tray_icon: Optional[qt.QSystemTrayIcon] = None
    stored_actions: Dict[str, qt.QAction]
    stored_options: Dict[str, qt.QGroupBox]
    cmd_options = None

    project_created = qt.pyqtSignal()

    def self_destruct(self) -> None:
        """"""
        super().self_destruct()
        # Tray icon
        if self.tray_icon is not None:
            self.tray_icon.setParent(None)  # noqa
        self.tray_icon = None
        return

    def __init__(self, cmd_options) -> None:
        """

        :param cmd_options:
        """
        super().__init__("home-window")
        self._basic_initialization("Home Window", "HomeWindow", "Embeetle Home")
        self.corner_logo_enabled = True
        self.no_config_file_flag = False
        self.stored_options = {}
        self.cmd_options = cmd_options
        # Initialize namespaces
        self.display = Display(self)
        self.settings = Settings(self)
        self.view = View(self)
        self.wcomm = WindowCommunication(self)
        self.projects = Projects(self)

        default_size = self.get_default_size()
        self.resize(default_size)

        # Initialize repl interpreter
        def print_func(*args):
            # print(*args)
            pass

        self._init_interpreter(
            lambda: ({}, {}, {}),
            print_func,
            print_func,
            print_func,
            print_func,
        )
        # Initialize statusbar
        self._init_statusbar()
        # Initialize the menubar
        self._init_menubar()
        # Initialize the main groupbox
        self.view.init_all_widgets()
        self.view._set_fixed_policy(self)
        self._set_flags(self.windowFlags())
        # Set the style
        components.thesquid.TheSquid.init_home_form(self)
        # Connect to the communicator signals
        self.connect_received_signal(self._data_received)

        # Restore settings
        def __restore(*args):
            self.settings.restore(
                restyle=False,
                emit_update_signal=False,
            )

        qt.QTimer.singleShot(0, __restore)
        # Reset the life sign flag
        self.life_sign_sender = True
        self.life_sign_received = False
        qt.QTimer.singleShot(20, self._life_check)
        if self.no_config_file_flag:

            def show_popup():
                self.view.scaling_bubble_show()

            qt.QTimer.singleShot(40, show_popup)
        # Connect global signal dispatcher signals
        data.signal_dispatcher.update_styles.connect(self.settings.restore)
        data.signal_dispatcher.restart_needed_notify.connect(
            self.__restart_notification_received
        )

        # Add a custom event filter
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == qt.QEvent.Type.StatusTip:
            if self.display.statusbar_message_blocked_flag:
                event.ignore()
                return True
        return False

    def __restart_notification_received(self, message):
        if message == "Theme changed":
            text = (
                "Embeetle needs to be restarted in order for all the\n"
                + "theme settings to upgrade. You can continue to use Embeetle,\n"
                + "but some things might not be styled according to the theme\n"
                + "you currently selected."
            )
        else:
            text = message

        def show_popup(*args):
            gui.dialogs.popupdialog.PopupDialog.ok(
                parent=self,
                icon_path="icons/dialog/info.png",
                title_text="WARNING",
                text=text,
            )

        qt.QTimer.singleShot(10, show_popup)

    def get_tab_by_name(self, tab_name):
        """Find a tab using its name in the tab widgets."""
        raise NotImplementedError()

    @qt.pyqtSlot(object)
    def _data_received(self, _data: object) -> None:
        #        functions.echo("HomeWindow received:", _data)
        _from, message = _data
        if message == "pong":
            self.received_pong = True
        elif message == "show-home-window":
            self._show()
            self.send("home-window-shown")
        elif "switch-tab" in message:
            try:
                command, argument = message.split()
                index = 0
                if argument == "tools":
                    index = 3
                self.view.tab_widget.setCurrentIndex(index)
            except:
                functions.echo(
                    f"[COMM-HomeWindow] Unknown 'switch-tab' argument: {argument}"
                )
                traceback.print_exc()
        elif message == "life-check" and self.life_sign_sender == False:
            self._show()
            self.send("life-flag")
        elif self.life_sign_sender == True and message == "life-flag":
            self.life_sign_received = True
        elif message == "restyle":
            if _from != self.communicator.name:
                self.settings.restore(restyle=False)
        elif message == "geometry":
            geometries = {}
            geometries["home_window"] = functions.get_geometry(self)
            for k, v in self.display.dialogs.items():
                dialog = getattr(self, k)
                if dialog is not None and dialog.isVisible():
                    geometries[k] = functions.get_geometry(dialog)
            self.send(functions.json_encode(geometries))
        elif "add_tool_blink(" in message:
            try:
                msg = message[15:-1]
                data.toolman.receive_add_tool_blink_msg(msg)
            except Exception as e:
                functions.echo(f"ERROR: Cannot interpret message {message}")
                self.receive_queue.put(_data)
        elif "add_tool(" in message:
            try:
                msg = message[9:-1]
                data.toolman.receive_add_tool_msg(msg)
            except Exception as e:
                functions.echo(f"ERROR: Cannot interpret message {message}")
                self.receive_queue.put(_data)
        elif "delete_tool(" in message:
            try:
                msg = message[12:-1]
                data.toolman.receive_delete_tool_msg(msg)
            except Exception as e:
                functions.echo(f"ERROR: Cannot interpret message {message}")
                self.receive_queue.put(_data)
        else:
            self.receive_queue.put(_data)

    def _send_ping(self):
        self.received_pong = False
        self.send("ping")
        timer = qt.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(500)
        timer.start()
        while timer.isActive():
            functions.process_events(10)
        return self.received_pong

    def _life_check(self, *args):
        """Check if a home window is already alive on the system."""
        if not hasattr(self, "end_time") or self.end_time is None:
            self.life_sign_received = False
            self.send("life-check")
            self.end_time = datetime.datetime.now() + datetime.timedelta(
                microseconds=1000000
            )
        if self.life_sign_received:
            self.exit()
        elif datetime.datetime.now() < self.end_time:
            qt.QTimer.singleShot(20, self._life_check)
        else:
            self.life_sign_sender = False

    def _no_config_callback(self):
        self.no_config_file_flag = True

    def _init_menubar(self) -> None:
        """Initialize the menubar ("QAction.triggered.connect" signals first
        parameter is always "checked: bool").

        This is a very long function that should be trimmed sometime!
        """
        self.menubar = self.MenuBar(self)

        # Function for creating menus
        self.menubar.stored_menus = {}

        def add_menubar_menu(name):
            new_menu = gui.templates.basemenu.BaseMenu(name, self.menubar)
            self.menubar.addMenu(new_menu)
            self.menubar.stored_menus[name] = new_menu
            return new_menu

        # ^ =============================[ FILE ]============================= ^#
        def construct_file_menu():
            file_menu = add_menubar_menu("&File")
            # Create actions
            exit_action = self.create_action(
                "exit",
                "Exit\tAlt+F4",
                None,
                "Exit application",
                "Exit application",
                "icons/system/log_out.png",
                self.exit,
            )
            file_menu.addAction(exit_action)

        # ^ =============================[ HELP ]============================= ^#
        def construct_help_menu():

            #! ----------------------[ About Embeetle ]---------------------- !#
            def show_about():
                helpdocs.help_texts.about(self)
                return

            help_menu = add_menubar_menu("&Help")
            about_action = self.create_action(
                "help-about-embeetle",
                "About Embeetle",
                None,
                "Embeetle Information",
                "Embeetle Information",
                "icons/logo/beetle_face.png",
                show_about,
            )
            help_menu.addAction(about_action)

            #! -----------------------[ View License ]----------------------- !#
            def show_license():
                helpdocs.help_texts.show_license(
                    parent=self,
                    txt=functions.get_license_text(),
                    typ="ok",
                )
                return

            license_action = self.create_action(
                "help-view-license",
                "View License",
                None,
                "View License Agreement",
                "View License Agreement",
                "icons/gen/certificate.png",
                show_license,
            )
            help_menu.addAction(license_action)
            return

        # ^ ============================[ TESTING ]=========================== ^#
        def construct_test_menu():
            test_menu = add_menubar_menu("&Testing")

            #! ----------------------[ ESP32 experiment ]-------------------- !#
            def esp32_experiment(*args):
                import project_generator.esp.espressif_importer as _esp_

                _esp_.EspressifImporter().esp32_experiment(
                    callback=print,
                    callbackArg="\nesp32 experiment finished\n",
                )

            esp32_exp = self.create_action(
                "esp32-experiment",
                "ESP32 experiment",
                None,
                "",
                "",
                f"icons/logo/espressif.png",
                esp32_experiment,
            )
            test_menu.addAction(esp32_exp)

            # #! --------------------[ Standalone TextDiffer ]----------------- !#
            # def standalone_diff_test(*args):
            #     gui.various.create_standalone_diff(
            #         'Standalone TextDiffer',
            #         'icons/logo/beetle_face.ico',
            #         'Some text 0',
            #         'Text in next window',
            #         'TEXT 0',
            #         'TEXT 1',
            #         initial_size=(1000, 480)
            #     )
            # diff_tester = self.create_action(
            #     'standalone-diff',
            #     'Standalone Differ',
            #     None,
            #     'Test the standalone text differ',
            #     'Test the standalone text differ',
            #     f"icons/menu_edit/compare_text.png",
            #     standalone_diff_test
            # )
            # test_menu.addAction(diff_tester)

            #! --------------------[ Popup Custom Buttons ]------------------ !#
            def popup_custom_test():
                result, checkbox_data = (
                    gui.dialogs.popupdialog.PopupDialog.custom_buttons(
                        "TEST <a href='click_here' style=\"color: #729fcf;\">click here </a>",
                        title_text="PopupTest",
                        buttons=[
                            ("SOMETHING Long here sanda danjfasdbnfoasidnf", 1),
                            ("ELSE", 2),
                        ],
                        parent=self,
                    )
                )
                functions.echo(result)
                functions.echo(checkbox_data)

            test = self.create_action(
                "popup-custom-buttons",
                "Popup Custom Buttons",
                None,
                "test",
                "test",
                "icons/dialog/help.png",
                popup_custom_test,
            )
            test_menu.addAction(test)

            def test_popup():
                gui.dialogs.popupdialog.PopupDialog.ok_cancel(
                    icon_path="icons/dialog/stop.png",
                    title_text="INTERNAL ERROR",
                    text="simple-popup-test",
                )

            test = self.create_action(
                "simple-popup-test",
                "simple-popup-test",
                None,
                "test",
                "test",
                "icons/dialog/help.png",
                test_popup,
            )
            test_menu.addAction(test)

        # Construct the menubar
        construct_file_menu()
        construct_help_menu()
        if data.debug_mode:
            construct_test_menu()

        # Add the menubar to the MainWindow
        self.setMenuBar(self.menubar)

    def get_default_size(self):
        return qt.create_qsize(
            self.DEFAULT_WIDTH * data.get_global_scale(),
            self.DEFAULT_HEIGHT * data.get_global_scale(),
        )

    def changeEvent(self, event):
        typ = event.type()
        if typ == qt.QEvent.Type.WindowStateChange:
            window_state = self.windowState()
            if window_state == qt.Qt.WindowState.WindowMinimized:
                self.hide()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.self_destruct()
        qt.QApplication.quit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update_popup_bubbles()
        if self.corner_logo_enabled:
            self.position_corner_banner()

    def update_popup_bubbles(self, *args):
        if self.view.update_bubble_flag:
            self.view.update_bubble_show()
        if self.view.scaling_bubble_flag:
            self.view.scaling_bubble_show()

    def reassign_shortcuts(self, update_preferences_window=True):
        super().reassign_shortcuts()
        if update_preferences_window:
            data.signal_dispatcher.update_settings.emit()

    def update_custom_styles(self):
        # Update popup bubbles
        self.update_popup_bubbles()

        if self.corner_logo_enabled:
            self.position_corner_banner()

    """
    Painting
    """
    BANNER_SIZE = (40, 40)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.corner_logo_enabled and hasattr(self.view, "tab_widget"):
            current_tab_text = self.view.tab_widget.tabText(
                self.view.tab_widget.currentIndex()
            )
            if current_tab_text == "News":
                self.embeetle_label.hide()
            else:
                if (
                    hasattr(self, "embeetle_label") == False
                    or self.embeetle_label is None
                ):
                    self.initialize_corner_banner()
                self.embeetle_label.show()
                self.embeetle_label.raise_()

    def initialize_corner_banner(self):
        # Create image
        embeetle_image = "icons/logo/beetle_face.png"
        embeetle_label = self._create_label(
            image=embeetle_image,
            parent=self,
        )
        embeetle_label.setFixedSize(
            qt.create_qsize(self.BANNER_SIZE[0], self.BANNER_SIZE[1])
        )
        embeetle_label.setParent(self)
        self.embeetle_label = embeetle_label
        self.embeetle_label.raise_()
        self.embeetle_label.show()
        self.position_corner_banner()

    def position_corner_banner(self) -> None:
        if (
            hasattr(self, "embeetle_label") == False
            or self.embeetle_label is None
        ):
            return
        offset = int(data.get_scrollbar_zoom_pixelsize() * 0.12)
        paint_position = qt.create_qpoint(
            self.view.tab_widget.width()
            - self.embeetle_label.size().width()
            - 2
            - offset,
            self.menuBar().height()
            + self.view.tab_widget.tabBar().height()
            + 2
            + int(offset / 2),
        )
        self.embeetle_label.setGeometry(
            paint_position.x(),
            paint_position.y(),
            self.embeetle_label.size().width(),
            self.embeetle_label.size().height(),
        )


class Settings:
    """Functions for manipulating the application settings (namespace/nested
    class to MainWindow)"""

    # Class varibles
    _parent = None
    # Custom object for manipulating the settings of Embeetle
    manipulator: settings.SettingsFileManipulator = None
    news_manipulator: settings.NewsManipulator = None

    def __init__(self, parent):
        """Initialization of the Settings object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Initialize the Embeetle settings object with the current working directory
        self.manipulator = settings.SettingsFileManipulator(
            data.beetle_core_directory, data.resources_directory, parent
        )
        # News
        self.news_manipulator = settings.NewsManipulator()

    def restore(self, restyle=False, emit_update_signal=True):
        """Restore the previously stored settings."""
        # Load the settings from the initialization file
        result = self.manipulator.load_settings()
        data.theme = self.manipulator.theme
        # Adjust icon style according to theme
        iconfunctions.update_style()
        # Update recent files and projects lists in the menubar
        self._parent.view.refresh_all_widgets(adjust=True)
        # Update the styles
        components.thesquid.TheSquid.update_home_form()
        # Emit update-settings signal
        if emit_update_signal:
            data.signal_dispatcher.update_settings.emit()
        # Display message in statusbar
        self._parent.display.write_to_statusbar("Restored settings", 1000)
        # Display the settings load error AFTER the theme has been set
        # Otherwise the error text color will not be styled correctly
        if result == False:
            functions.echo(
                "Error loading the settings file, using the "
                + "default settings values!\n"
                + "THE SETTINGS FILE WILL NOT BE UPDATED!"
            )
        else:
            if restyle:
                self._parent.send("restyle")

    def save(self, restyle=True):
        """Save the current settings."""
        try:
            self.manipulator.save_settings()
        except:
            msg = traceback.format_exc()
            self._parent.display.display_error(msg)
            return
        # Display message in statusbar
        self._parent.display.write_to_statusbar("Saved settings", 1000)
        if restyle == True:
            self._parent.send("restyle")

    def update_recent_projects_list(self, new_project_path=None):
        # Update the file manipulator
        if new_project_path is not None:
            self.manipulator.add_recent_project(new_project_path)
        # Refresh the list
        self._parent.view.refresh_all_widgets()


class Display:
    def __init__(self, parent):
        """Initialization of the Display object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Initialize the dialog list
        self.dialogs = {
            "one_project_wizard": (
                gui.dialogs.projectcreationdialogs.OneWindowProjectWizard
            ),
            "project_import_options": (
                gui.dialogs.projectcreationdialogs.ImportWizard
            ),
            "scaling_dialog": gui.dialogs.scalingdialog.ScalingDialog,
        }
        # Create all the dialogs
        self.dialogs_init()

    """
    Statusbar
    """
    statusbar_message_blocked_flag = False

    def write_to_statusbar(self, message, msec=0):
        """Write a message to the statusbar."""
        if not self.statusbar_message_blocked_flag:
            self.statusbar_message_blocked_flag = True
            self._parent.statusbar_label_left.hide()
            self._parent.statusbar.showMessage(message)
            qt.QTimer.singleShot(msec, self.__reset_write_to_statusbar)

    def __reset_write_to_statusbar(self):
        self.statusbar_message_blocked_flag = False
        self._parent.statusbar.clearMessage()
        self._parent.statusbar_label_left.show()

    def __reset_statusbar_show(self):
        self.statusbar_message_blocked_flag = False
        self._parent.statusbar.clearMessage()

    def statusbar_show(self, message, msec=0):
        """Write a message to the statusbar (NORMAL PRIORITY)"""
        if not self.statusbar_message_blocked_flag:
            self.statusbar_message_blocked_flag = True
            self._parent.statusbar_label_left.setText(message)
            self._parent.statusbar_label_left.show()
            qt.QTimer.singleShot(msec, self.__reset_statusbar_show)

    """
    Dialogs
    """

    def dialogs_init(self):
        parent = self._parent
        for d in self.dialogs:
            setattr(parent, d, None)

    def _dialog_show(self, dialog, init_class, *args, **kwargs):
        parent = self._parent
        self.hide_other_dialogs(getattr(parent, dialog))
        if self.dialog_test(dialog) == True:
            if getattr(parent, dialog).isVisible() == False:
                self._dialog_hide(dialog)
        if getattr(parent, dialog) is None:
            setattr(parent, dialog, init_class(parent, *args, **kwargs))
        show_dialog = getattr(parent, dialog)
        # Modal dialog
        #            try:
        #                show_dialog.exec()
        #            except:
        #                show_dialog.show()
        #                show_dialog.activateWindow()
        #                show_dialog.raise_()
        # Normal dialog
        show_dialog.show()
        show_dialog.activateWindow()
        show_dialog.raise_()
        # Check boundaries
        position = show_dialog.pos()
        if position.x() < 0:
            show_dialog.move(0, position.y())
        if position.y() < 0:
            show_dialog.move(position.x(), 0)
        return show_dialog

    def _dialog_hide(self, dialog):
        parent = self._parent
        _dialog: Union[
            gui.dialogs.projectcreationdialogs.OneWindowProjectWizard,
            gui.dialogs.projectcreationdialogs.ImportWizard,
            gui.dialogs.scalingdialog.ScalingDialog,
        ] = getattr(parent, dialog)
        if _dialog is not None:
            _dialog.hide()
            _dialog.self_destruct()
            setattr(parent, dialog, None)
        return

    def dialog_check(self, dialog):
        if not (dialog in self.dialogs):
            raise Exception("Dialog {} is invalid!".format(dialog))

    def dialog_test(self, dialog):
        self.dialog_check(dialog)
        return getattr(self._parent, dialog) is not None

    def hide_other_dialogs(self, dialog=None):
        parent = self._parent
        for d in self.dialogs:
            if not (dialog is getattr(parent, d)):
                self._dialog_hide(d)

    def dialog_show_arduino_import_prefilled(
        self, sketch_name: str, sketch_abspath: str, parent_dirpath: str
    ) -> None:
        dialog_widget = self.dialog_show(
            "project_import_options",
            "arduino",
        )
        # Prefill the path to the sketch file
        dialog_widget.input_directory_textbox.setText(sketch_abspath)
        dialog_widget.input_directory_textbox.setReadOnly(True)
        dialog_widget.input_directory_button.hide()
        dialog_widget.checkbox_input_directory.hide()
        # Hide the box with the replace/keep choice
        dialog_widget.stored_gboxes["input_type"].hide()
        # Prefill the new project's parent directory
        # [don't do this anymore]
        # dialog_widget.project_directory_textbox.setText(parent_dirpath)
        # Prefill the new project's name
        dialog_widget.project_name_textbox.setText(sketch_name)
        # Resize the dialog widget
        dialog_widget.update_check_size()
        dialog_widget.resize(
            int(dialog_widget.main_layout.sizeHint().width() * 1.1),
            int(dialog_widget.main_layout.sizeHint().height() * 1.1),
        )
        dialog_widget.center_to_parent()
        return

    def dialog_show(self, dialog_type, *args, **kwargs):
        dialog_widget = None
        self.dialog_check(dialog_type)
        if dialog_type in self.dialogs.keys():
            if dialog_type in self.dialogs.keys():
                dialog_widget = self._dialog_show(
                    dialog_type,
                    self.dialogs[dialog_type],
                    *args,
                    **kwargs,
                )
            else:
                raise Exception(f"Unknown dialog type: {dialog_type}")
        return dialog_widget

    def dialog_hide(self, dialog):
        self.dialog_check(dialog)
        self._dialog_hide(dialog)

    def progressbar_show(self, value, minimum, maximum):
        # Progress bar
        if hasattr(self._parent, "progressbar") == False:
            self._parent.progressbar = (
                gui.templates.baseprogressbar.BaseProgressBar(color="green")
            )
        progressbar = self._parent.progressbar
        progressbar.setMinimum(minimum)
        progressbar.setMaximum(maximum)
        progressbar.setValue(value)
        progressbar.setTextVisible(False)
        progressbar.setFixedHeight(15)
        progressbar.show()
        # Display widgets
        self._parent.statusbar.addPermanentWidget(progressbar)

    def progressbar_hide(self):
        if self._parent.progressbar is not None:
            self._parent.progressbar.hide()
        if self.progress_label is not None:
            self.progress_label.hide()


class View:
    MINIMAL_WIDTH = 400

    def __init__(self, parent):
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        self.project_groupbox = None
        self.updater_groupbox = None
        self.preferences_widget = None
        self.gb_cache = {}
        self.update_bubble_flag = False
        self.scaling_bubble_flag = False
        self.feed_widget = None

        # Connect the news updating signal
        self._parent.settings.news_manipulator.check_completed.connect(
            self.__check_news_updates
        )

    def _set_fixed_policy(self, widget):
        widget.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Fixed, qt.QSizePolicy.Policy.Fixed
            )
        )

    def _reset_fixed_policy(self, widget):
        widget.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding
            )
        )

    def __create_gb(self, name, icon):
        new_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                vertical=True,
                borderless=True,
                spacing=0,
                margins=(0, 0, 0, 0),
                h_size_policy=qt.QSizePolicy.Policy.Expanding,
                v_size_policy=qt.QSizePolicy.Policy.Expanding,
            )
        )
        new_groupbox.setObjectName(name)
        new_groupbox.name = name
        new_groupbox.savable = False
        new_groupbox.current_icon = iconfunctions.get_qicon(icon)
        return new_groupbox

    def __toolbox_creation_routine(self, tab_widget, *args):
        module_toolbox = functions.import_module("toolmanager.toolmanager")
        module_toolbox_widget = functions.import_module(
            "home_toolbox.chassis.home_toolbox"
        )
        module_toolbox_version_extractor = functions.import_module(
            "toolmanager.version_extractor"
        )
        data.toolbox_widg = module_toolbox_widget.Toolbox(
            self._parent,
            self.tab_widget,
        )
        data.toolbox_widg.setObjectName("Toolbox")
        data.toolversion_extractor = (
            module_toolbox_version_extractor.VersionExtractor()
        )
        data.toolman = module_toolbox.Toolmanager("home")
        data.toolman.init_all(
            callback=nop,
            callbackArg=None,
        )
        return data.toolbox_widg

    def __library_manager_creation_routine(self, tab_widget, *args):
        module_library_manager = functions.import_module(
            "libmanager.libmanager"
        )
        module_library_manager_widget = functions.import_module(
            "home_libraries.chassis.home_libraries"
        )
        data.libman_widg = module_library_manager_widget.LibManager(
            self._parent,
            self.tab_widget,
        )
        data.libman_widg.setObjectName("Libraries")
        data.libman = module_library_manager.LibManager()
        data.libman.fill_libman_widg()
        data.libman.initialize(
            libtable=None,
            progbar=None,
            origins=["local_abspath"],
            callback=nop,
            callbackArg=None,
        )
        return data.libman_widg

    def __preferences_creation_routine(self, tab_widget, *args):
        module_settings = functions.import_module("gui.forms.settingswindow")
        self.preferences_widget = module_settings.SettingsWindow(
            tab_widget,
            tab_widget.main_form,
        )
        return self.preferences_widget

    def __init_containers(self):
        # Main Groupbox
        main_groupbox = (
            gui.templates.widgetgenerator.create_borderless_groupbox()
        )
        #            self._set_fixed_policy(main_groupbox)
        main_groupbox_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        main_groupbox_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        #            main_groupbox_layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetMinimumSize)
        main_groupbox.setLayout(main_groupbox_layout)
        main_groupbox.setObjectName("MainGroupbox")
        self.main_groupbox = main_groupbox
        self.main_groupbox.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.frame = gui.templates.widgetgenerator.create_scroll_area()
        self.frame.setObjectName("ScrollArea")
        self.frame.setWidget(self.main_groupbox)
        self._parent.setCentralWidget(self.frame)

        # Main splitter between RSS feed and tabs
        self.main_splitter = qt.QSplitter(
            qt.Qt.Orientation.Horizontal, self.main_groupbox
        )
        self.main_splitter.setStyleSheet(
            gui.stylesheets.splitter.get_transparent_stylesheet()
        )
        self.main_splitter.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding
            )
        )
        main_groupbox_layout.addWidget(self.main_splitter)

        # Tabwidget that will hold everything
        tab_widget = gui.templates.widgetgenerator.create_tabs(
            "Tabs", self._parent, self._parent
        )
        tab_widget.indication_set()
        tab_widget.setMovable(False)
        self.tab_widget = tab_widget

        # * Project groupbox that holds New, Open, ...
        project_groupbox = self.__create_gb(
            "Projects", f"icons/folder/closed/folder.png"
        )
        project_groupbox.layout().setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )
        self.project_groupbox = project_groupbox

        # * Update groupbox
        updater_groupbox = self.__create_gb("Updates", "icons/gen/download.png")
        updater_groupbox.layout().setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )
        self.updater_groupbox = updater_groupbox

        # * Toolmanager groupbox
        self.toolbox_placeholder = (
            gui.templates.widgetgenerator.create_placeholder(
                name="Toolbox",
                icon=iconfunctions.get_qicon("icons/tools/toolbox.png"),
                creation_routine=lambda *args: self.__toolbox_creation_routine(
                    tab_widget
                ),
            )
        )

        # * Library Manager groupbox
        self.library_manager_placeholder = gui.templates.widgetgenerator.create_placeholder(
            name="Libraries",
            icon=iconfunctions.get_qicon("icons/gen/book.png"),
            creation_routine=lambda *args: self.__library_manager_creation_routine(
                tab_widget
            ),
        )

        # Preferences (Settings)
        self.preferences_placeholder = gui.templates.widgetgenerator.create_placeholder(
            name="Preferences",
            icon=iconfunctions.get_qicon("icons/gen/gear.png"),
            creation_routine=lambda *args: self.__preferences_creation_routine(
                tab_widget
            ),
        )

        # News
        #        self.feed_widget = gui.helpers.newsdisplay.NewsDisplay(
        #            main_form=self._parent,
        #            parent=self.tab_widget,
        #            name="News",
        #        )
        #        # Check news updates
        #        qt.QTimer.singleShot(1000, self.check_news_updates)
        # Feed
        if data.new_mode:
            data.rss_feed_url = "https://new.embeetle.com/rss.xml"
        self.feed_widget = gui.helpers.rssfeedparser.RSSFeedParser(
            name="News",
            parent=tab_widget,
            main_form=self._parent,
            feed_url=data.rss_feed_url,
            feed_cache=data.rss_feed_cache,
        )
        qt.QTimer.singleShot(1000, self.check_news_updates)

        self.tab_names = {
            "projects": "Projects",
            "updates": "Updates",
            "toolbox": "Toolbox",
            "libraries": "Libraries",
            "preferences": "Preferences",
            "news": "News",
        }
        tabs = (
            (
                project_groupbox,
                self.tab_names["projects"],
                "Create, import and open projects",
            ),
            (
                updater_groupbox,
                self.tab_names["updates"],
                "Updates and general information about Embeetle",
            ),
            (
                self.feed_widget,
                self.tab_names["news"],
                "News about Embeetle",
            ),
            (
                self.toolbox_placeholder,
                self.tab_names["toolbox"],
                "Select compiler, build and flashtools",
            ),
            (
                self.library_manager_placeholder,
                self.tab_names["libraries"],
                "View cached libraries",
            ),
            (
                self.preferences_placeholder,
                self.tab_names["preferences"],
                "Customize preferences",
            ),
        )
        for i, t in enumerate(tabs):
            widget, name, tooltip = t
            new_tab = tab_widget.addTab(widget, name)
            tab_widget.update_tab_icon(widget)
            tab_widget.custom_tab_bar.setTabToolTip(i, tooltip)
        # Set the index to projects
        tab_widget.setCurrentIndex(0)
        tab_widget.currentChanged.connect(self.__current_changed)

        # Add the Inner groupbox
        self.main_splitter.addWidget(tab_widget)

        self.main_splitter.setSizes(
            [
                int(self._parent.DEFAULT_HEIGHT / 3),
                int(self._parent.DEFAULT_HEIGHT * 2 / 3),
            ]
        )

    def version_check(self, remote_version):
        local_version = functions.get_embeetle_version()
        release_notes_string, release_notes_func = (
            helpdocs.help_texts.home_window_release_notes()
        )
        update_needed = False
        download_error = False
        if (remote_version is None) or (
            remote_version.strip().lower() == "none"
        ):
            download_error = True
        elif local_version != remote_version:
            update_needed = functions.is_larger_than(
                remote_version, local_version
            )

        if update_needed:
            button_tooltip = "Click to update"
            button_icon = "icons/gen/download.png"
            button_enabled = True
            main_icon = None
            label_text = ""
            help_refresh_show = False
            help_icon = "icons/dialog/help.png"
            help_func = functools.partial(
                helpdocs.help_texts.home_window_info,
                self._parent,
                "update_available",
            )
        else:
            button_tooltip = "Update is not needed"
            button_icon = "icons/gen/download(dis).png"
            button_enabled = False
            main_icon = "icons/dialog/checkmark.png"
            label_text = helpdocs.help_subjects.home_window.updated()
            help_refresh_show = True
            help_icon = "icons/dialog/info.png"
            help_func = functools.partial(
                helpdocs.help_texts.home_window_info,
                self._parent,
                "update_disabled",
            )

        if download_error:
            button_tooltip = "Update not possible"
            button_icon = "icons/gen/download(err).png"
            button_enabled = False
            label_text = "Cannot connect to server"
            help_refresh_show = True
            help_icon = "icons/dialog/help.png"
            help_func = functools.partial(
                helpdocs.help_texts.home_window_info,
                self._parent,
                "update_error",
            )

        # Reset the tree widget
        self.updates_tree.clear()

        # Add local information
        main_item = self.updates_tree.add(
            text="Current version information:",
            icon_path="icons/dialog/info.png",
        )
        main_item.setExpanded(True)
        # Version
        item = self.updates_tree.add(
            text=f"Version number: {local_version}",
            parent=main_item,
        )
        tooltip = "The version number of the current Embeetle"
        item.setToolTip(0, tooltip)
        item.setStatusTip(0, tooltip)
        # Date
        item = self.updates_tree.add(
            text=f"Release date:   {functions.get_embeetle_builddate()}",
            parent=main_item,
        )
        tooltip = "The release date of the current Embeetle"
        item.setToolTip(0, tooltip)
        item.setStatusTip(0, tooltip)

        # Release notes
        tooltip = "Opens the release notes in the default web-browser"
        new_item = self.updates_tree.add(parent=main_item)
        widget = self.updates_tree.create_button_option(
            "Display release notes",
            "SHOW",
            tooltip,
            release_notes_func,
            "icons/dialog/info.png",
        )
        self.updates_tree.setItemWidget(new_item, 0, widget)
        new_item.setToolTip(0, tooltip)
        new_item.setStatusTip(0, tooltip)
        self.gb_cache["release_notes"] = widget

        # Add update information
        main_item = self.updates_tree.add(
            text="Update information:",
            icon_path="icons/gen/world.png",
        )
        main_item.setExpanded(True)
        if update_needed:
            tooltip = "Displays the available server version for updating"
            new_item = self.updates_tree.add(parent=main_item)
            widget = self.updates_tree.create_button_option(
                f"New version available: {remote_version}",
                "UPDATE",
                tooltip,
                self._update_embeetle,
                "icons/gen/download.png",
            )
            self.updates_tree.setItemWidget(new_item, 0, widget)
            new_item.setToolTip(0, tooltip)
            new_item.setStatusTip(0, tooltip)
            self.gb_cache["update"] = widget

            # Signal updates with tab text
            self.tab_widget.setTabText(1, "* " + self.tab_names["updates"])
            self.update_bubble_show()
            qt.QTimer.singleShot(10, self._parent.update_popup_bubbles)

            # Show the update button
            self.updates_gb.setVisible(True)

        else:
            # Status
            item = self.updates_tree.add(
                parent=main_item, text=label_text, icon_path=main_icon
            )
            tooltip = button_tooltip
            item.setToolTip(0, tooltip)
            item.setStatusTip(0, tooltip)
            # Last check
            date = datetime.datetime.now().strftime("%Y-%b-%d %H:%M")
            item = self.updates_tree.add(
                text=f"Last checked:   {date}",
                parent=main_item,
            )
            tooltip = "Displays the last time checking for a new version"
            item.setToolTip(0, tooltip)
            item.setStatusTip(0, tooltip)
            # Reset updates signal
            self.tab_widget.setTabText(1, self.tab_names["updates"])
            self.update_bubble_hide()

            # Hide the update button
            self.updates_gb.setVisible(False)

        # Additional information
        if not update_needed:
            tooltip = (
                "Display additional information about the "
                + "current Embeetle version"
            )
            new_item = self.updates_tree.add(parent=main_item)
            widget = self.updates_tree.create_button_option(
                "Display additional information",
                "INFO",
                tooltip,
                help_func,
                help_icon,
            )
            self.updates_tree.setItemWidget(new_item, 0, widget)
            new_item.setToolTip(0, tooltip)
            new_item.setStatusTip(0, tooltip)
            self.gb_cache["additional_information"] = widget

        # Recheck
        def recheck(*args):
            try:
                if not hasattr(self, "lock_recheck"):
                    self.lock_recheck = True
                else:
                    if self.lock_recheck == True:
                        return
                    self.lock_recheck = True
                self.gb_cache["recheck"].label.setText(
                    "Checking for updates ..."
                )
                self.gb_cache["recheck"].button.setVisible(False)
                qt.QTimer.singleShot(
                    500,
                    functools.partial(
                        serverfunctions.get_remote_embeetle_version,
                        self.version_check,
                    ),
                )
            finally:
                self.lock_recheck = False

        new_item = self.updates_tree.add(parent=main_item)
        widget = self.updates_tree.create_button_option(
            "Recheck for updates",
            "RECHECK",
            tooltip,
            recheck,
            "icons/dialog/refresh.png",
        )
        self.updates_tree.setItemWidget(new_item, 0, widget)
        new_item.setToolTip(0, tooltip)
        new_item.setStatusTip(0, tooltip)
        self.gb_cache["recheck"] = widget

        self.updates_tree.header().setSectionResizeMode(
            qt.QHeaderView.ResizeMode.ResizeToContents
        )
        self.updates_tree.header().setStretchLastSection(True)

    def __current_changed(self, index):
        widget = self.tab_widget.widget(index)
        name = widget.objectName()
        if name in ("Toolbox", "Libraries", "Preferences"):
            widget.replace()

        # News update
        if "News" in name:
            self._parent.settings.news_manipulator.cached_news_update()
            self.feed_widget.news_hide()
            self.feed_widget.blink_icon_stop()
            self.tab_widget.setTabText(
                self.tab_widget.indexOf(self.feed_widget), "News"
            )

    def __add_special_row_to_tree_item(
        self,
        item,
        tree,
        text,
        first_button_icon=None,
        first_button_func=None,
        first_button_tooltip=None,
        extra_button_icon=None,
        extra_button_tooltip=None,
        extra_button_func=None,
    ):
        gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
            borderless=True,
            vertical=False,
        )
        original_update_style = gb.update_style
        gb.setSizePolicy(
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Maximum,
        )
        layout = gb.layout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 1, 3, 1)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetNoConstraint)
        first_button = None
        # First Button
        if first_button_icon:
            layout.setContentsMargins(1, 1, 0, 1)
            # First button
            first_button = gui.templates.widgetgenerator.create_pushbutton(
                parent=None,
                name="first_button",
                tooltip=first_button_tooltip,
                icon_name=first_button_icon,
                size=(
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                ),
                click_func=first_button_func,
            )
            if first_button_func is None:
                first_button.setStyleSheet(
                    gui.stylesheets.button.get_simple_toggle_stylesheet()
                )
            first_button.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Minimum,
            )
            layout.addWidget(first_button)
            layout.setAlignment(
                first_button,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
            # Clickable label
            label = gui.templates.widgetgenerator.create_label(
                text=text,
                selectable_text=False,
                tooltip=first_button_tooltip,
                statustip=first_button_tooltip,
            )
            label.set_colors(
                background_color="transparent",
            )
            label.setSizePolicy(
                qt.QSizePolicy.Policy.Fixed,
                qt.QSizePolicy.Policy.Preferred,
            )
            if first_button_func is not None:
                label.click_signal.connect(first_button_func)
            layout.addWidget(label)
            layout.setAlignment(
                label,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
        else:
            # Label
            label = gui.templates.widgetgenerator.create_label(
                text=text,
                selectable_text=False,
                tooltip=first_button_tooltip,
                statustip=first_button_tooltip,
            )
            label.set_colors(
                background_color="transparent",
            )
            label.setSizePolicy(
                qt.QSizePolicy.Policy.Fixed,
                qt.QSizePolicy.Policy.Preferred,
            )
            if first_button_func is not None:
                label.click_signal.connect(first_button_func)
            layout.addWidget(label)
            layout.setAlignment(
                label,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
        # Button
        offset = 3
        button = gui.templates.widgetgenerator.create_pushbutton(
            parent=None,
            name="tree_button",
            tooltip=extra_button_tooltip,
            icon_name=extra_button_icon,
            size=(
                data.get_general_icon_pixelsize() - offset,
                data.get_general_icon_pixelsize() - offset,
            ),
            click_func=extra_button_func,
        )
        button.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        layout.addWidget(button)
        layout.setAlignment(
            button,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Spacing
        layout.addSpacerItem(
            qt.QSpacerItem(0, 0, hPolicy=qt.QSizePolicy.Policy.Expanding)
        )
        tree.setItemWidget(item, 0, gb)

        def update_style(*args) -> None:
            original_update_style()
            # First button
            if first_button is not None:
                button_size = data.get_general_icon_pixelsize() - offset
                first_button.update_style((button_size, button_size))
            # Label
            label.update_style()
            # Button
            button.update_style()
            button_size = data.get_general_icon_pixelsize() - offset
            icon_size = int(data.get_general_icon_pixelsize() * 0.8) - offset
            button.setFixedSize(qt.create_qsize(button_size, button_size))
            button.setIconSize(qt.create_qsize(icon_size, icon_size))
            # Groupbox
            gb.setMinimumWidth(
                label.sizeHint().width() + button.sizeHint().width() * 3
            )
            return

        def self_destruct(*args) -> None:
            label.setParent(None)
            button.setParent(None)
            gb.setParent(None)
            return

        # Restyle
        update_style()
        # Assing the needed widgets to be accessible throught the groupbbox.
        gb.label = label
        gb.button = button
        gb.update_style = update_style
        gb.self_destruct = self_destruct
        return gb

    def check_news_updates(self):
        self._parent.settings.news_manipulator.check_news()

    def __check_news_updates(self, news_data):
        if news_data is not None:
            self.feed_widget.news_show()
            self.feed_widget.blink_icon_start()
            self.tab_widget.setTabText(
                self.tab_widget.indexOf(self.feed_widget), f"* News"
            )
        else:
            self.feed_widget.news_hide()
            self.tab_widget.setTabText(
                self.tab_widget.indexOf(self.feed_widget), "News"
            )

    def update_bubble_show(self):
        try:
            self.update_bubble_flag = True
            if hasattr(self, "pop_update"):
                self.pop_update.setParent(None)
            tab_bar = self.tab_widget.tabBar()
            geo = tab_bar.geometry()
            width = geo.width()
            height = geo.height()
            pos = tab_bar.mapTo(self.frame, qt.create_qpoint(geo.x(), geo.y()))
            self.pop_update = gui.helpers.popupbubble.PopupBubble(
                parent=self.frame, corner="top-left"
            )
            self.pop_update.click.connect(self.update_bubble_hide)
            self.pop_update.setText("Updates are available!")
            self.pop_update.show()
            self.pop_update.setVisible(True)
            popup_geo = self.pop_update.geometry()
            left_offset = (
                tab_bar.tabRect(0).width() + tab_bar.tabRect(1).width() / 2
            )
            self.pop_update.move(
                int(pos.x() + left_offset), int(pos.y() + height / 2)
            )
            self.pop_update.raise_()
        except:
            #            traceback.print_exc()
            pass

    def update_bubble_hide(self):
        self.update_bubble_flag = False
        if hasattr(self, "pop_update"):
            self.pop_update.hide()
            self.pop_update.setParent(None)

    def scaling_bubble_show(self):
        try:
            self.scaling_bubble_flag = True
            if hasattr(self, "pop_scaling"):
                self.pop_scaling.setParent(None)
            tab_bar = self.tab_widget.tabBar()
            geo = tab_bar.geometry()
            width = geo.width()
            height = geo.height()
            pos = tab_bar.mapTo(self.frame, qt.create_qpoint(geo.x(), geo.y()))
            # Show bubble
            self.pop_scaling = gui.helpers.popupbubble.PopupBubble(
                parent=self._parent, corner="top-right"
            )
            self.pop_scaling.click.connect(self.scaling_bubble_hide)
            self.pop_scaling.setText(
                "Select 'Preferences > Scaling'<br>to adjust sizes to your needs!"
            )
            self.pop_scaling.show()
            self.pop_scaling.setVisible(True)
            popup_geo = self.pop_scaling.geometry()
            self.pop_scaling.move(
                int(pos.x() + (width * 0.54)), int(pos.y() + (height * 1.30))
            )
            self.pop_scaling.raise_()
        except:
            traceback.print_exc()
            pass

    def scaling_bubble_hide(self):
        self.scaling_bubble_flag = False
        if hasattr(self, "pop_scaling"):
            self.pop_scaling.hide()
            self.pop_scaling.setParent(None)

    def _update_embeetle(self, *args) -> None:
        gui.dialogs.popupdialog.PopupDialog.ok(
            text=str(
                f"We are working on a new update mechanism. For now, please\n"
                f"delete your Embeetle installation and download it\n"
                f"again at {serverfunctions.get_base_url_wfb()}\n"
                f"We{q}re sorry for the inconvenience."
            ),
            title_text="Update error",
            text_click_func=None,
            icon_path="icons/dialog/error.png",
            parent=self._parent,
        )
        return

    def __new_info_func(self, *args):
        helpdocs.help_texts.home_window_info(self._parent, None, "new_project")

    def __open_info_func(self, *args):
        helpdocs.help_texts.home_window_info(self._parent, None, "open_project")

    def __project_wizard_func(self, *args):
        self._parent.display.dialog_show(
            "one_project_wizard",
        )
        return

    def __empty_project_wizard_func(self, *args):
        self._parent.display.dialog_show(
            "one_project_wizard", empty_project=True
        )

    def __import_sample_proj_from_library_func(self, *args):
        helpdocs.help_texts.import_from_library(self._parent)
        return

    def __arduino_import_func(self, *args):
        self._parent.display.dialog_show(
            "project_import_options",
            "arduino",
        )
        return

    def __stm_import_func(self, *args):
        self._parent.display.dialog_show(
            "project_import_options",
            "stm",
        )
        return

    def __open_func(self, *args):
        self._parent.projects.open_project()

    def __recent_projects_info_func(self, *args):
        helpdocs.help_texts.home_window_info(
            self._parent, None, "recent_projects"
        )

    def __add_tray_action(self, menu, name, icon, func):
        action = qt.QAction(name)
        action.setIcon(iconfunctions.get_qicon(icon))
        action.setEnabled(True)
        action.triggered.connect(func)
        self._parent.stored_actions[name] = action
        menu.addAction(action)

    def init_all_widgets(self):
        self.__init_containers()

        # Projects
        project_layout = self.project_groupbox.layout()
        # Tree widget
        self.project_tree = gui.templates.treewidget.TreeWidget(
            self.project_groupbox, self._parent, "Projects", None
        )

        project_layout.addWidget(self.project_tree)
        # New project
        item = self.project_tree.add(
            icon_path="icons/folder/closed/new_folder.png"
        )
        tooltip = "New project options"
        item.setToolTip(0, tooltip)
        item.setStatusTip(0, tooltip)
        self.gb_cache["new_project"] = self.__add_special_row_to_tree_item(
            item,
            self.project_tree,
            "New project",
            extra_button_icon="icons/dialog/help.png",
            extra_button_tooltip="Show more information on creating a new project.",
            extra_button_func=self.__new_info_func,
        )

        subitems = (
            (
                "Generate project",  #'Download sample project from Embeetle server',
                "icons/logo/beetle_face.png",
                self.__project_wizard_func,
                "Generate project using the project creation wizard",  #'Download sample project from the Embeetle server',
                "CREATE",
            ),
            #                (
            #                    'Create empty project',
            #                    'icons/chip/chip.png',
            #                    self.__empty_project_wizard_func,
            #                    'Create an empty project',
            #                    "EMPTY",
            #                ),
            (
                "Import sample project from Arduino library",
                "icons/gen/book.png",
                self.__import_sample_proj_from_library_func,
                "Import sample project from a specific library",
                "IMPORT",
            ),
            (
                "Import Arduino sketch",
                "icons/logo/arduino.png",
                self.__arduino_import_func,
                "Import project from an Arduino project",
                "IMPORT",
            ),
            (
                "Import STM project",
                "icons/logo/stmicro.png",
                self.__stm_import_func,
                "Import project from an STM (CubeMX) project",
                "IMPORT",
            ),
        )
        for si in subitems:
            text, icon, func, tooltip, button_text = si
            new_item = self.project_tree.add(
                parent=item,
                in_data={},
            )

            widget = self.project_tree.create_button_option(
                text,
                button_text,
                tooltip,
                func,
                icon,
            )
            self.project_tree.setItemWidget(new_item, 0, widget)
            self.gb_cache[text] = widget

            new_item.setToolTip(0, tooltip)
            new_item.setStatusTip(0, tooltip)
        item.setExpanded(True)

        # Open project
        open_item = self.project_tree.add(
            icon_path="icons/folder/open/chip.png"
        )
        tooltip = "Open project options"
        open_item.setToolTip(0, tooltip)
        open_item.setStatusTip(0, tooltip)
        self.gb_cache["open_project_options"] = (
            self.__add_special_row_to_tree_item(
                open_item,
                self.project_tree,
                "Open project",
                extra_button_icon="icons/dialog/help.png",
                extra_button_tooltip="Show more information on opening a new project.",
                extra_button_func=self.__open_info_func,
            )
        )

        item = self.project_tree.add(parent=open_item)
        tooltip = "Open an existing project"
        item.setToolTip(0, tooltip)
        item.setStatusTip(0, tooltip)

        text = "Open an existing project"
        button_text = "OPEN"
        icon = f"icons/folder/closed/folder.png"
        widget = self.project_tree.create_button_option(
            text,
            button_text,
            tooltip,
            self.__open_func,
            icon,
        )
        self.project_tree.setItemWidget(item, 0, widget)
        self.gb_cache["open_project"] = widget
        open_item.setExpanded(True)

        # Recent projects
        item = self.project_tree.add(icon_path=f"icons/folder/open/file.png")
        tooltip = "A list of recently opened projects."
        item.setToolTip(0, tooltip)
        item.setStatusTip(0, tooltip)
        self.gb_cache["recent_projects"] = self.__add_special_row_to_tree_item(
            item,
            self.project_tree,
            "Recent projects",
            extra_button_icon="icons/dialog/help.png",
            extra_button_tooltip="Show more information on the recent project list.",
            extra_button_func=self.__recent_projects_info_func,
        )
        self.recent_projects_item = item

        # Updates
        updater_layout = self.updater_groupbox.layout()
        # Update button
        self.updates_gb = (
            gui.templates.widgetgenerator.create_alert_groupbox_with_button(
                text="Press to update Embeetle",
                bold=True,
                tooltip="Press to update Embeetle",
                style="good",
                click_func=self._update_embeetle,
                parent=None,
                statusbar=None,
            )
        )
        self.updates_gb.setVisible(False)
        updater_layout.addWidget(self.updates_gb)
        # Tree widget
        self.updates_tree = gui.templates.treewidget.TreeWidget(
            self.updater_groupbox, self._parent, "Updates", None
        )
        updater_layout.addWidget(self.updates_tree)
        # Check remote version
        serverfunctions.get_remote_embeetle_version(self.version_check)

        # Tray icon
        self._parent.stored_actions = {}
        menu = gui.templates.basemenu.BaseMenu(self._parent)
        tray_icon = qt.QSystemTrayIcon(self._parent)
        tray_icon.setIcon(qt.QIcon(data.application_icon_abspath))
        tray_icon.setToolTip("Embeetle IDE")
        # Show home window
        self.__add_tray_action(
            menu,
            "Show home window",
            "icons/menu_view/fullscreen.png",
            self._parent._show,
        )
        # Exit
        self.__add_tray_action(
            menu, "Exit", "icons/system/log_out.png", self._parent.exit
        )
        tray_icon.setContextMenu(menu)
        self._parent.tray_menu = menu
        tray_icon.activated.connect(self._tray_icon_activated)
        tray_icon.show()
        self._parent.tray_icon = tray_icon

    def refresh_all_widgets(self, adjust=False):
        # Update recent Projects
        self.add_recent_projects()
        # Resize all
        self.resize_items()

    def _create_information_context_menu(
        self, parent, project_name, project_path
    ):
        menu = gui.templates.basemenu.BaseMenu(parent)
        menu.setToolTipsVisible(True)
        # Copy project name
        path_action = qt.QAction("Copy project name to clipboard", menu)
        path_action.setToolTip(f"'{project_name}'\n")
        path_action.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
        )

        def clipboard_copy_name():
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(project_name, mode=cb.Mode.Clipboard)

        path_action.triggered.connect(clipboard_copy_name)
        menu.addAction(path_action)
        
        # Copy full project path
        path_action = qt.QAction("Copy project path to clipboard", menu)
        path_action.setToolTip(
            f"Full path for project '{project_name}':\n'{project_path}'"
        )
        path_action.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
        )

        def clipboard_copy_path():
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(project_path, mode=cb.Mode.Clipboard)

        path_action.triggered.connect(clipboard_copy_path)
        menu.addAction(path_action)
        # Open in explorer
        explorer_action = qt.QAction("Open in the default file explorer", menu)

        def show_explorer_func():
            try:
                functions.open_file_folder_in_explorer(project_path)
            except Exception as ex:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    str(ex),
                    title_text="System filetree error",
                    text_click_func=None,
                    icon_path="icons/dialog/warning.png",
                    parent=self._parent,
                )

        explorer_action.setToolTip(
            "Open project in the system's file explorer."
        )
        explorer_action.setIcon(
            iconfunctions.get_qicon(f"icons/folder/open/file.png")
        )
        explorer_action.triggered.connect(show_explorer_func)
        menu.addAction(explorer_action)
        # Remove from recent project list
        delete_action = qt.QAction("Remove from recent projects list", menu)

        def delete_func():
            self._parent.settings.manipulator.recent_projects.remove(
                project_path
            )
            self._parent.settings.save()
            self._parent.settings.update_recent_projects_list()

        delete_action.setToolTip(
            "Delete the project from the recent projects list."
        )
        delete_action.setIcon(iconfunctions.get_qicon("icons/dialog/fatal.png"))
        delete_action.triggered.connect(delete_func)
        menu.addAction(delete_action)

        return menu

    def add_recent_projects(self) -> qt.QGroupBox:
        # Projects
        def is_project_valid(path):
            if os.path.isdir(path) == False:
                return False
            config_file = os.path.join(rp, ".beetle/dashboard_config.btl")
            if os.path.isfile(config_file) == False:
                config_file = os.path.join(rp, ".beetle/project_config.btl")
                if os.path.isfile(config_file) == False:
                    return False
                else:
                    functions.echo(
                        "!!! WARNING: The opened project uses a deprecated configuration file named\n"
                        + "!!!          'project_config.btl'. We recently switched to 'dashboard_config.btl\n"
                    )
            return True

        projects = self._parent.settings.manipulator.recent_projects
        used_projects = []
        project_counter = 0
        for i, rp in enumerate(reversed(projects)):
            if is_project_valid(rp) == False:
                continue
            project_counter += 1
            #                if project_counter > 100:
            #                    break
            used_projects.append(rp)

        def options_func(name, path):
            menu = self._create_information_context_menu(
                self.project_tree, name, path
            )
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        def open_project_func(recent_project, project_id):
            # Lock to prevent quick opening of multiple projects
            if not hasattr(self, "open_lock"):
                self.open_lock = False
            if self.open_lock:
                return
            self.open_lock = True

            item = self.project_tree.get(project_id)
            item.setText(0, item.text(0) + " -> opening ...")
            #                item.setIcon(
            #                    0,
            #                    iconfunctions.get_qicon("icons/folder/open/folder.png")
            #                )

            self._parent.wcomm.open_project(recent_project)

            def update_projects():
                self._parent.settings.update_recent_projects_list(
                    functions.unixify_path(os.path.realpath(recent_project))
                )
                self.open_lock = False

            qt.QTimer.singleShot(2000, update_projects)

        # Remove all previous recent projects
        for i in self.recent_projects_item.takeChildren():
            del i
        # Add valid projects
        items = []
        for i, pp in enumerate(used_projects):
            project_name = functions.get_last_directory_from_path(pp)
            project_info = self.__get_project_information(pp)
            #            project_id = i + 1
            project_id = self.project_tree.get_node_id_counter() + i + 1
            new_item = {
                "text": project_name,
                "id": project_id,
                "parent": self.recent_projects_item,
                "data": {
                    "info_func": functools.partial(
                        options_func, project_name, pp
                    ),
                    "click_func": functools.partial(
                        open_project_func, pp, project_id
                    ),
                },
                "tooltip": "PATH: " + pp,
                "statustip": pp,
            }
            if project_info["manufacturer-icon"] is not None:
                new_item["icon"] = project_info["manufacturer-icon"]
            items.append(new_item)
        self.project_tree.multi_add(items)
        self.recent_projects_item.setExpanded(True)

    def __get_project_information(self, path):
        info = {
            "manufacturer-name": None,
            "manufacturer-icon": None,
            "chip-name": "standard",
            "chip-icon": "resources/icons/logo/beetle_face.png",
            "board-name": None,
            "board-icon": None,
        }
        try:
            # Get the dashboard file
            config_file = functions.unixify_path_join(
                path, ".beetle/dashboard_config.btl"
            )
            line_list = functions.read_file_to_list(config_file)
            chip_name = None
            board_name = None
            for l in line_list:
                if l.strip().startswith("chip_name"):
                    sl = l.split("=")
                    chip_name = sl[1].strip().replace("'", "")
                if l.strip().startswith("board_name =") or l.strip().startswith(
                    "board ="
                ):
                    sl = l.split("=")
                    board_name = sl[1].strip().replace("'", "")

            info["chip-name"] = chip_name
            info["board-name"] = board_name

            # Get icon from the vendor
            chip_unicum: hardware_api.chip_unicum.CHIP = (
                hardware_api.chip_unicum.CHIP(chip_name)
            )
            chip_manufacturer: str = chip_unicum.get_chip_dict(board=None)[
                "manufacturer"
            ]
            chip_manufacturer_iconpath: (
                str
            ) = hardware_api.hardware_api.HardwareDB().get_manufacturer_dict(
                chip_manufacturer
            )[
                "icon"
            ]
            chip_iconpath: str = chip_unicum.get_chip_dict(board=None)["icon"]
            info["chip-icon"] = chip_iconpath
            info["manufacturer-name"] = (
                chip_manufacturer if chip_manufacturer is not None else "none"
            )
            info["manufacturer-icon"] = chip_manufacturer_iconpath

            # Get icon from the board
            board_unicum: hardware_api.board_unicum.BOARD = (
                hardware_api.board_unicum.BOARD(board_name)
            )
            board_icon = board_unicum.get_board_dict()["icon"]
            info["board-icon"] = board_icon

            # Try getting the board icon
            board_unicum: hardware_api.board_unicum.BOARD = (
                hardware_api.board_unicum.BOARD(board_name)
            )
            board_manufacturer: str = board_unicum.get_board_dict()[
                "manufacturer"
            ]
            board_manufacturer_iconpath: (
                str
            ) = hardware_api.hardware_api.HardwareDB().get_manufacturer_dict(
                board_manufacturer
            )[
                "icon"
            ]
            info["manufacturer-icon"] = board_manufacturer_iconpath
        except:
            #            traceback.print_exc()
            pass
        return info

    def _tray_icon_activated(self, reason):
        #            if reason == qt.QSystemTrayIcon.ActivationReason.DoubleClick:
        if reason == qt.QSystemTrayIcon.ActivationReason.Trigger:
            self._parent._show()

    def set_style_sheet(self):
        style_sheet = """
#HomeWindow {{
    background-color: {};
    background-image: url({});
    border: none;
}}
#ScrollArea {{
    background: transparent;
    border: none;
}}
#MainGroupbox {{
    background: transparent;
    border: none;
}}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
{}
            """.format(
            data.theme["form_background"],
            iconfunctions.get_icon_abspath(data.theme["form_background_file"]),
            gui.stylesheets.tooltip.get_default(),
            gui.stylesheets.statusbar.get_default(),
            gui.stylesheets.tabwidget.get_dynamic_style(),
            gui.stylesheets.tabbar.get_scrollbutton_style(),
            # Tab-widget tab-bar scroll buttons
            gui.stylesheets.button.get_tab_scroll_stylesheet(
                "#TabScrollLeft",
                "icons/arrow/triangle/triangle_left.png",
                "icons/arrow/triangle/triangle_full_left.png",
            ),
            gui.stylesheets.button.get_tab_scroll_stylesheet(
                "#TabScrollRight",
                "icons/arrow/triangle/triangle_right.png",
                "icons/arrow/triangle/triangle_full_right.png",
            ),
            gui.stylesheets.button.get_tab_scroll_stylesheet(
                "#TabScrollDown",
                "icons/arrow/triangle/triangle_down.png",
                "icons/arrow/triangle/triangle_full_down.png",
            ).replace(
                "border-style: solid;", "border-style: solid; border-left: 0px;"
            ),
            # Menubar
            gui.stylesheets.menubar.get_default(),
            # Tree-widget
            gui.stylesheets.treewidget.get_default(),
            # Scrollbars
            gui.stylesheets.scrollbar.get_general(),
            # TextEdit
            gui.stylesheets.textedit.get_default(),
            # Splitter
            gui.stylesheets.splitter.get_transparent_stylesheet(),
            # Table
            gui.stylesheets.table.get_default_style(),
            # Combobox
            gui.stylesheets.combobox.get_default(),
        )
        self._parent.setStyleSheet(style_sheet)
        self._parent.update_statusbar_style()

    def resize_items(self):
        # Scrollbars
        self.frame.horizontalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_horizontal()
        )
        self.frame.verticalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_vertical()
        )
        self.frame.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.frame.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        #        # Feed widget
        #        if self.feed_widget is not None:
        #            self.feed_widget.update_style()
        # Options
        for opt in self._parent.stored_options.keys():
            option = self._parent.stored_options[opt]
            option.update_style(data.get_general_icon_pixelsize())
        self.tab_widget.update_style()
        # Project
        self.project_groupbox.update_style()
        self.project_tree.update_style()
        # Updates
        self.updates_tree.update_style()
        for k, v in self.gb_cache.items():
            v.update_style()
        self.updater_groupbox.update_style()
        self.updates_gb.update_style()
        # Preferences
        if self.preferences_widget:
            self.preferences_widget.update_style()
        # Managers
        if data.toolbox_widg:
            data.toolbox_widg.update_style()
        if data.libman_widg:
            data.libman_widg.update_style()

    def update_style(
        self, adjust=False, force_resize=False, center_to_screen=False
    ):
        self.resize_items()

        if adjust:
            self._parent.adjustSize()
        if self._parent.width() < self.MINIMAL_WIDTH:
            self._parent.resize(int(self.MINIMAL_WIDTH), self._parent.height())

        new_size = self._parent.get_default_size()

        # Embeetle label
        width = 500 * data.get_global_scale()
        height = width / 4.4
        label_size = qt.create_qsize(width, height)

        # Tab widget
        self.tab_widget.customize_tab_bar()
        # Tab bar
        tab_bar_width = self.tab_widget.tabBar().sizeHint().width()
        tabs_visible_size = tab_bar_width + (1.8 * tab_bar_width * 0.05)
        if new_size.width() < tabs_visible_size:
            new_size = qt.create_qsize(tabs_visible_size, new_size.height())

        combined_height = (
            label_size.height() + self.tab_widget.sizeHint().height()
        ) * 1.8
        if new_size.height() < combined_height:
            new_size = qt.create_qsize(new_size.width(), combined_height)

        # Safety check
        position = self._parent.pos()
        desktop_width, desktop_height = functions.get_desktop_size()
        if (position.x() + new_size.width()) > desktop_width:
            new_size = qt.create_qsize(
                desktop_width - position.x() - 80, new_size.height()
            )
        if (position.y() + new_size.height()) > desktop_height:
            new_size = qt.create_qsize(
                new_size.width(), desktop_height - position.y() - 80
            )

        # Resize form
        if force_resize:
            self._parent.resize(new_size)

        # Center window to the screen
        if center_to_screen:
            if self._parent.isVisible():
                functions.center_to_current_screen(self._parent)


class WindowCommunication:
    def __init__(self, parent) -> None:
        self._parent = parent

    def open_project(self, project_path: str) -> None:
        self._parent.receive_queue_clear()

        # Check project validity
        project_directory = project_path
        check_result = purefunctions.is_ascii_only_and_safe(project_directory)
        if check_result != "safe":
            err_msg = str(
                f"The path to your Embeetle project:\n"
                f"'{project_directory}'\n"
                f"is not safe: '{check_result}'\n"
                f"\n"
                f"To ensure that Embeetle and all its tools (compiler, openocd, etc.) work properly,\n"
                f"please move the project to a folder without unsafe characters in the path.\n"
            )
            gui.dialogs.popupdialog.PopupDialog.ok(
                text=err_msg, title_text="Unsafe Embeetle path!"
            )
            return

        self._parent.send("show-project::{}".format(project_path))
        self._parent.display.write_to_statusbar(
            "Waiting for response from the project window ...", 2000
        )
        for i in range(10):
            # Test if project window returned a response
            functions.process_events(delay=0.05)
            try:
                _from, _message = self._parent.receive_queue.get_nowait()
                if _message == "project-found":
                    break
            except queue.Empty:
                pass
        else:
            # Project window is not alive, create a new one
            switches = []
            switches.append(f"--project={project_path}")
            if data.new_mode:
                switches.append("--new_mode")
            if data.debug_mode:
                switches.append("--debug")
            functions.open_embeetle(switches)
            self._parent.display.write_to_statusbar(
                "Opening the project ...", 4000
            )
        self._parent.receive_queue_clear()


class Projects:
    # Class varibles
    _parent = None

    def __init__(self, parent: HomeWindow) -> None:
        """Get the reference to the HomeWindow parent object instance."""
        self._parent: HomeWindow = parent
        return

    def import_project(
        self,
        import_data: Dict[str, Any],
        import_wizard: gui.dialogs.projectcreationdialogs.ImportWizard,
    ) -> None:
        """
        Input data holds all relevant information for
        importing a project.
        Vendor specific data:
            STM:
                'vendor'            -> vendor string
                'input_directory'   -> directory to import from
                'project_directory' -> directory to create the new project in
                'replace'           -> flag to import and create the project
                                        directly in the "input_directory"

            Arduino:
                Same as STM, with additional fields:
                    'board' -> board string
                    'chip'  -> chip string

        """
        vendor: str = import_data["vendor"]
        assert (vendor == "arduino") or (vendor == "stm")
        if import_data["replace"]:
            import_data["project_directory"] = import_data["input_directory"]

        def finish(*args) -> None:
            import_wizard.hide_dialog()
            self._callback_finished(True, import_data["project_directory"])
            return

        # * PREPARE THE CONSOLE
        console = import_wizard.get_importer_console()
        functions.importer_printfunc_ = console.get_print_func()
        import_wizard.repurpose_cancel_next_buttons(
            cancel_en=False,
            next_en=False,
        )

        # * DO THE IMPORT
        # & Arduino
        if vendor.lower() == "arduino":
            if os.path.isfile(import_data["project_directory"]):
                import_data["project_directory"] = os.path.dirname(
                    import_data["project_directory"]
                ).replace("\\", "/")
            success = importer.import_project(
                manufacturer="arduino",
                src=import_data["input_directory"],
                dst=import_data["project_directory"],
                boardname=import_data["board"],
                chipname=import_data["chip"],
                probename="usb-to-uart-converter",
                convert_encoding=False,
                convert_line_endings=True,
            )
        # & STMicro
        elif vendor.lower() == "stm":
            success = importer.import_project(
                manufacturer="stmicro",
                src=import_data["input_directory"],
                dst=import_data["project_directory"],
                boardname=None,
                chipname=None,
                probename=None,
                convert_encoding=False,
                convert_line_endings=True,
            )
        # & Other
        else:
            raise NotImplementedError(f"Unknown vendor: {vendor}")

        # * PREPARE THE 'FINISH' (OR 'ABORT') BUTTON
        projpath = import_data["project_directory"]
        # $ Success
        success = True
        if success:
            import_wizard.repurpose_cancel_next_buttons(
                next_name="FINISH",
                next_func=finish,
                next_en=True,
                cancel_en=True,
            )
            functions.importer_printfunc(f"\nProject imported into:")
            functions.importer_printfunc(
                f"{q}{projpath}{q}", color="blue", bright=True
            )
            functions.importer_printfunc(f"Click ", end="")
            functions.importer_printfunc(
                f"{q}FINISH{q} ", color="yellow", bright=True, end=""
            )
            functions.importer_printfunc(f"to launch project.")
            functions.importer_printfunc_ = None
            return
        # $ Failure
        import_wizard.repurpose_cancel_next_buttons(
            next_name="ABORT",
            next_func=import_wizard.close,
            next_en=True,
            cancel_en=True,
        )
        functions.importer_printfunc(f"\nProject import into:")
        functions.importer_printfunc(
            f"{q}{projpath}{q}", color="blue", bright=True
        )
        functions.importer_printfunc(
            f"Failed! Copy the output in this console and send"
        )
        functions.importer_printfunc(f"it to the Embeetle support:")
        functions.importer_printfunc(
            f"info@embeetle.com", color="blue", bright=True
        )
        functions.importer_printfunc(f"Click ", end="")
        functions.importer_printfunc(
            f"{q}ABORT{q} ", color="yellow", bright=True, end=""
        )
        functions.importer_printfunc(f"to quit.")
        functions.importer_printfunc_ = None
        return

    def open_project(
        self,
        input_path: Optional[str] = None,
    ) -> None:
        """
        :param input_path:
        :return:
        """
        embeetle_dir = ".beetle"

        if input_path:
            directory = input_path
        else:
            dir_dialog = qt.QFileDialog(self._parent)
            dir_dialog.setFileMode(qt.QFileDialog.FileMode.Directory)
            directory = dir_dialog.getExistingDirectory(
                self._parent,
                "Open Project",
                data.default_project_open_directory,
            )
        # Pick only the first element of the returned file list
        if directory:

            # Check project validity
            project_directory = directory
            check_result = purefunctions.is_ascii_only_and_safe(
                project_directory
            )
            if check_result != "safe":
                err_msg = str(
                    f"The path to your Embeetle project:\n"
                    f"'{project_directory}'\n"
                    f"is not safe: '{check_result}'\n"
                    f"\n"
                    f"To ensure that Embeetle and all its tools (compiler, openocd, etc.) work properly,\n"
                    f"please move the project to a folder without unsafe characters in the path.\n"
                )
                gui.dialogs.popupdialog.PopupDialog.ok(
                    text=err_msg, title_text="Unsafe Embeetle path!"
                )
                return

            def open(path):
                data.default_project_open_directory = functions.unixify_path(
                    os.path.dirname(path)
                )
                self._parent.settings.save()
                self._parent.wcomm.open_project(path)
                self._parent.settings.update_recent_projects_list(
                    functions.unixify_path(path)
                )

            file = None
            search_dir = os.path.join(directory, embeetle_dir)
            if os.path.isdir(search_dir):
                eo_path = search_dir
                for f in os.listdir(eo_path):
                    file = os.path.join(eo_path, f)
                    if os.path.isfile(file) and file.lower().endswith(".btl"):
                        open(directory)
                        break
                else:
                    open(directory)
            else:
                open(directory)
        return

    def _callback_finished(
        self,
        success: bool,
        rootpath: str,
    ) -> None:
        """"""
        if not success:
            return
        self._parent.project_created.emit()
        # Create a new project window.
        self._parent.wcomm.open_project(rootpath)
        data.default_project_open_directory = rootpath
        self._parent.settings.update_recent_projects_list(
            functions.unixify_path(rootpath)
        )
        return
