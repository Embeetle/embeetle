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

import importlib
import multiprocessing


def main():
    """Main function of embeetle."""
    import os
    import sys
    import traceback
    import qt
    import data
    import purefunctions
    import iconfunctions
    import serverfunctions
    import os_checker

    # $ PARSE ARGUMENTS
    options = purefunctions.parse_arguments()

    # $ HANDLE OUTPUT STREAM
    if options.debug_mode:
        # Initialize colorama
        data.redirecting_output = False
        purefunctions.init_colorama()
    else:
        # Redirect output
        data.redirecting_output = True
        try:
            purefunctions.redirect_output(options.open_project)
        except:
            traceback.print_exc()
            purefunctions.reset_output()
            data.redirecting_output = False

    # Fix paths before importing anything: PYTHONPATH needs to be correct for imports
    purefunctions.fix_paths_for_embeetle_and_restore_global_environment()

    # Check arguments
    if options.debug_mode:
        data.debug_mode = True
        if os_checker.is_os("windows") and getattr(sys, "frozen", False):
            # Running from a compiled application, no console
            data.debug_mode = False
    if options.filetree_progbar_mode:
        data.filetree_progbar_mode = True
    if options.makefile_version:
        data.makefile_version_new_projects = options.makefile_version
    if options.logging_mode:
        data.logging_mode = True
    file_arguments = options.files
    if options.single_file is not None:
        if file_arguments is not None:
            file_list = file_arguments.split(";")
            file_list.append(options.single_file)
            file_arguments = ";".join(file_list)
        else:
            file_arguments = [options.single_file]
    if options.source_analysis_only:
        data.source_analysis_only = True
        if options.open_project is None:
            raise Exception(
                f'The "source_analysis_only" flag has to have a '
                f'"project" flag also!'
            )
    if file_arguments == [""]:
        file_arguments = None

    # New mode for testing
    data.new_mode = options.new_mode

    # Clone sys directory content if needed
    if os.path.exists(data.sys_directory):
        print(f"INFO: 'sys' directory found at '{data.sys_directory}'")
        print(f"INFO: Launch Embeetle...\n")
    else:
        print(f"INFO: 'sys' directory not found at '{data.sys_directory}'")
        print(f"INFO: Clone 'sys' directory from GitHub...")
        import subprocess
        import importlib
        import shutil
        import stat
        import time
        import os

        def run(args, cwd=None):
            print(f"$ {' '.join(args)}")
            try:
                subprocess.run(args, cwd=cwd, check=True)
            except FileNotFoundError as e:
                raise RuntimeError(
                    "`git` was not found. Install Git and ensure it is on PATH."
                ) from e
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Command failed (exit {e.returncode}): {' '.join(args)}"
                ) from e

        repo_url = f"https://github.com/Embeetle/sys-{os_checker.get_os_with_arch()}.git"

        # Clone
        run(
            ["git", "clone", "--branch", "master", repo_url, data.sys_directory]
        )

        # Import
        if data.sys_directory not in sys.path:
            sys.path.insert(0, data.sys_directory)
        importlib.invalidate_caches()
        print("")
        print("INFO: Launch Embeetle ... (check taskbar icons)\n")


    # Combine the application path with the embeetle icon file name
    # (the icon file name is set in the global module)
    data.application_icon_abspath = os.path.realpath(
        os.path.join(data.resources_directory, "icons_static/beetle_face.png")
    ).replace("\\", "/")

    # Combine the application path with the embeetle information file name
    # (the information file name is set in the global module)
    data.about_image = iconfunctions.get_icon_abspath(
        data.about_image, skip_style_check=True
    )

    # Environment variable adjustments
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = qt.QApplication(sys.argv)
    # app.setAttribute(qt.Qt.AA_DisableHighDpiScaling)
    # app.setAttribute(qt.Qt.AA_EnableHighDpiScaling)
    # Save the Qt application to the global reference
    data.application = app

    if options.logging_mode:
        # Install global event filter
        app.installEventFilter(app)

    # Store the QPainter()
    data.painter = qt.QPainter()

    custom_style = qt.QProxyStyle("Fusion")
    data.application.setStyle(custom_style)

    # PyQt splash for Linux
    if options.open_project is None and options.show_splash == True:

        splash_pixmap = iconfunctions.get_qpixmap(
            "figures/splash/splash_screen_normal.png"
        )
        splash = qt.QSplashScreen(splash_pixmap)
        splash.showMessage(
            "Embeetle is starting up ...",
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignTop,
        )
        splash.show()

        def __close(*args):
            result = app.exit()

        qt.QTimer.singleShot(10, __close)
        app.exec()

    """
    Set the default theme, as the gui package needs it set.
    """
    import themes
    import settings

    settings_manipulator = settings.SettingsFileManipulator(
        data.beetle_core_directory,
        data.resources_directory,
    )
    settings_manipulator.load_settings()
    # The importing of the gui package has to be delayed
    # as the functions module (which it imports) causes a
    # massive delay
    import gui.fonts.fontloader

    # Set the application font
    gui.fonts.fontloader.set_application_font()

    if options.testing_mode:
        # TESTING
        #        import gui.helpers.advancedcombobox
        #        gui.helpers.advancedcombobox.test_acb(app)

        #        import gui.forms.terminal
        #        gui.forms.terminal.test()

        import chipconfigurator.testing

        chipconfigurator.testing.main()

    else:
        import functions
        import components.signaldispatcher

        # Initialize the global signal dispatcher
        data.signal_dispatcher = (
            components.signaldispatcher.GlobalSignalDispatcher()
        )

        # Flag for canceling application
        cancel_flag = False

        # Server respose timing check
        data.embeetle_base_url = serverfunctions.determine_base_url()
        data.signal_dispatcher.base_url_override_change.connect(
            serverfunctions.determine_base_url
        )

        # Check location
        installation_dir = os.path.realpath(
            os.path.normpath(os.path.join(data.beetle_core_directory, ".."))
        ).replace("\\", "/")
        check_result = purefunctions.is_ascii_only_and_safe(installation_dir)
        if check_result != "safe":
            import gui.dialogs.popupdialog

            err_msg = str(
                f"The path to your Embeetle installation:\n"
                f"'{installation_dir}'\n"
                f"is not safe: '{check_result}'\n"
                f"\n"
                f"To ensure that Embeetle and all its tools (compiler, openocd, etc.) work properly,\n"
                f"please move Embeetle to a folder without unsafe characters in the path. If your\n"
                f"username includes Chinese or other non-ascii characters, it's best to avoid locations\n"
                f"in your home directory.\n"
                f"\n"
                f"Suggested path:\n"
                f"  C:/embeetle\n"
                f"\n"
                f"After creating this folder, make sure your user account has write access to it.\n"
                f"Right-click the folder, select 'Properties > Security,' and grant full control\n"
                f"for your user account.\n"
            )
            gui.dialogs.popupdialog.PopupDialog.ok(
                text=err_msg, title_text="Unsafe Embeetle path!"
            )
            return

        # Create the main window, pass the filename that may have
        # been passed as an argument
        if options.open_project is not None:
            data.application_type = data.ApplicationType.Project

            # Check project validity
            project_directory = options.open_project
            check_result = purefunctions.is_ascii_only_and_safe(
                project_directory
            )
            if check_result != "safe":
                import gui.dialogs.popupdialog

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

            import gui.forms.mainwindow

            data.is_home = False
            data.is_updater = False
            main_window = gui.forms.mainwindow.MainWindow(
                options,
                logging=data.logging_mode,
                file_arguments=file_arguments,
                startup_project=options.open_project,
                name="Project Window",
                source_analysis_only=options.source_analysis_only,
                source_analysis_result_file=options.source_analysis_result_file,
            )
            main_window.import_user_functions()
            main_window.show()
        else:
            data.application_type = data.ApplicationType.Home

            import helpdocs
            import gui.forms.homewindow

            # Splash functionality
            purefunctions.create_startup_file()

            if not functions.license_agreement_check():
                # Initial styling selection
                result = initial_theme_choice(settings_manipulator)
                if result == qt.QMessageBox.StandardButton.Ok:
                    settings_manipulator.load_settings()

                    result = helpdocs.help_texts.show_license(
                        parent=None,
                        txt=functions.get_license_text(),
                        typ="accept_decline",
                    )
                    if (result == qt.QMessageBox.StandardButton.Ok) or (
                        result == "ACCEPT"
                    ):
                        functions.license_agreement_create()
                    else:
                        cancel_flag = True
                else:
                    cancel_flag = True
            else:
                if not functions.license_agreement_compare():
                    text = "The Embeetle license has changed:\n\n"
                    text += functions.get_license_text()
                    result = helpdocs.help_texts.show_license(
                        parent=None, txt=text, typ="accept_decline"
                    )
                    if (result == qt.QMessageBox.StandardButton.Ok) or (
                        result == "ACCEPT"
                    ):
                        functions.license_agreement_create()
                    else:
                        cancel_flag = True

            if not cancel_flag:
                data.is_home = True
                data.is_updater = False
                home_window = gui.forms.homewindow.HomeWindow(options)

                home_window.show()

            # PyQt splash for Linux
            if options.show_splash == True:
                splash.finish(home_window)

        if not cancel_flag:
            return_code = int(app.exec())
            sys.exit(return_code)


def initial_theme_choice(settings_manipulator):
    import gui.dialogs.popupdialog

    message = (
        "Choose your theme and scaling:\n\n"
        + "This can be changed at any time in the 'Preferences' tab."
    )
    result = gui.dialogs.popupdialog.PopupDialog.style_selector(
        message,
        settings_manipulator,
        text_centered=True,
        scroll_layout=False,
    )
    return result[0]


# Check if this is the main executing script
if "__main__" in __name__:
    multiprocessing.freeze_support()
    multiprocessing.Process(target=main).start()
