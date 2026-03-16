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
from components.singleton import Singleton
import os, traceback
import qt, data, purefunctions
import bpathlib.file_power as _fp_
import beetle_console.make_console as _make_console_
import helpdocs.help_texts as _ht_
import os_checker

if TYPE_CHECKING:
    import beetle_console.serial_console as _serial_console_


class MakefileTargetExecuter(metaclass=Singleton):

    def __init__(self) -> None:
        """"""
        super().__init__()
        return

    def get_make_command_list(
        self,
        target: Optional[str],
        role: str,
    ) -> List[str]:
        """
        IMPORTANT:
        Check that this function doesn't crash when any of the tools is None!

        role == 'console':
        ==================
        Assumptions:
            - Console will expand variables like '$(MAKE)', '$(TOOLPREFIX)', ...
            - Console starts in toplevel folder.

        role == 'clang':
        ================
        Assumptions:
            - Clang engine starts in build folder.
            - Since the command is given as a 'List of strings', there is no need to quote indivi-
              dual elements, even if they contain a space!
        """
        assert role == "console" or role == "clang"
        if role == "clang":
            assert target is None
        projObj = data.current_project
        try:
            # $ makefile_relpath
            makefile_relpath = os.path.relpath(
                path=projObj.get_treepath_seg().get_abspath("MAKEFILE"),
                start=projObj.get_treepath_seg().get_abspath("BUILD_DIR"),
            ).replace("\\", "/")

            # $ make_abspath
            make_abspath = projObj.get_toolpath_seg().get_abspath(
                "BUILD_AUTOMATION"
            )
            if (make_abspath is None) or (make_abspath.lower() == "none"):
                make_abspath = "make"

            # $ builddir_relpath
            builddir_relpath = os.path.relpath(
                path=projObj.get_treepath_seg().get_abspath("BUILD_DIR"),
                start=projObj.get_proj_rootpath(),
            )

            # $ toolprefix
            toolprefix = (
                projObj.get_toolpath_seg()
                .get_toolpathObj("COMPILER_TOOLCHAIN")
                .get_toolprefix()
            )
            if (toolprefix is None) or (toolprefix.lower() == "none"):
                toolprefix = None

            # $ flashtool
            flashtool = projObj.get_toolpath_seg().get_abspath("FLASHTOOL")
            if (flashtool is None) or (flashtool.lower() == "none"):
                flashtool = None

            # $ COM-port
            comport = None
            try:
                comport = data.current_project.get_probe().get_comport_name()
                if os_checker.is_os("windows"):
                    nr = int(comport.replace("COM", ""))
                    if nr < 10:
                        comport = f"COM{nr}"
                    else:
                        if (
                            projObj.get_toolpath_seg().get_unique_id(
                                "FLASHTOOL"
                            )
                            is not None
                        ) and any(
                            s
                            in projObj.get_toolpath_seg()
                            .get_unique_id("FLASHTOOL")
                            .lower()
                            for s in ("avrdude", "bossac", "fermionic")
                        ):
                            # avrdude, bossac and fermionic don't like backslashes in the COM-port.
                            # Note: this code is copied in 'console_widget.py'!
                            comport = f"COM{nr}"
                        else:
                            comport = "\\" + f"\\.\\COM{nr}"
                elif os_checker.is_os("linux"):
                    # Nothing to change
                    pass
                else:
                    raise EnvironmentError("Unsupported platform")
            except Exception as e:
                comport = None

            mk_command_list: Optional[List] = None

            # * Command for console
            use_old_com_convention = False
            if projObj.dashboard_mk_uses_COM_or_FLASH_PORT() == "COM":
                use_old_com_convention = True
            if role == "console":
                # Most variables will be expanded in the console itself, such
                # as:
                #     - $(MAKE)
                #     - $(TOOLPREFIX)
                #     - $(COM) or $(FLASH_PORT)
                #     - $(OCD)/$(FLASHTOOL)
                # So there is no need to fill them in now.
                mk_command_list = [
                    f"$(MAKE)",
                    f"{target}",
                    f"-C",
                    f"{builddir_relpath}",
                    f"-f",
                    f"{makefile_relpath}",
                    f"TOOLPREFIX=$(TOOLPREFIX)",
                ]

                if projObj.get_probe().get_probe_dict()["needs_serial_port"]:
                    if use_old_com_convention:
                        mk_command_list.append(f"COM=$(COM)")
                    else:
                        mk_command_list.append(f"FLASH_PORT=$(FLASH_PORT)")

                    # Special case for Arduino Leonardo
                    if projObj.get_chip().get_name().lower() == "atmega32u4":
                        if use_old_com_convention:
                            mk_command_list.append(f"BOOT_COM=$(BOOT_COM)")
                        else:
                            mk_command_list.append(
                                f"BOOT_FLASH_PORT=$(BOOT_FLASH_PORT)"
                            )

                    if flashtool is not None:
                        mk_command_list.append(f"FLASHTOOL=$(FLASHTOOL)")
                else:
                    version = projObj.get_makefile_interface_version()
                    if isinstance(version, int):
                        if version >= 4:
                            if flashtool is not None:
                                mk_command_list.append(
                                    f"FLASHTOOL=$(FLASHTOOL)"
                                )
                        else:
                            mk_command_list.append(f"OCD=$(OCD)")
                    else:
                        if flashtool is not None:
                            mk_command_list.append(f"FLASHTOOL=$(FLASHTOOL)")

            # * Command for SA
            elif role == "clang":
                # The variables need to be expanded before entering the SA!
                mk_command_list = [
                    f"{make_abspath}",
                    f"-f",
                    f"{makefile_relpath}",
                ]
                if toolprefix is not None:
                    mk_command_list.append(f"TOOLPREFIX={toolprefix}")
                if projObj.get_probe().get_probe_dict()["needs_serial_port"]:
                    if comport is not None:
                        if use_old_com_convention:
                            mk_command_list.append(f"COM={comport}")
                        else:
                            mk_command_list.append(f"FLASH_PORT={comport}")
                else:
                    if flashtool is not None:
                        version = projObj.get_makefile_interface_version()
                        if isinstance(version, int):
                            if version >= 4:
                                mk_command_list.append(f"FLASHTOOL={flashtool}")
                            else:
                                mk_command_list.append(f"OCD={flashtool}")
                        else:
                            mk_command_list.append(f"FLASHTOOL={flashtool}")

        except Exception as e:
            purefunctions.printc(
                "\nERROR: Cannot generate make command!\n",
                color="error",
            )
            traceback.print_exc()
            print("\n")
            mk_command_list = []

        return mk_command_list

    def execute_makefile_targets(
        self,
        console: _make_console_.MakeConsole,
        target: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        :param console:     Console()-object.
        :param target:      Makefile target to be executed.
        :param callback:    Called when target has finished.
        :param callbackArg: Provide object to be stuffed in the callback.

        RESULT
        ======
        If you provide a callback function (and optionally an argument to be passed into it), then
        this function will invoke your callback with the following parameters:

            > callback(success, callbackArg)

        success:     True if the command completed successfully, False otherwise.
        callbackArg: Whatever you passed to the 'callbackArg' parameter. Pass None if you don't need
                     this.

        Make sure your callback can process two parameters - even if callbackArg is None!


        THIS IS THE WAY WE CONSTRUCT THE MAKE COMMAND:
        ===============================================
        ```python
        f'
            {make} {target}
            -C {builddir_relpath}
            -f {makefile_relpath}
            "TOOLPREFIX={toolprefix}"
            "FLASHTOOL={flashtool}"
        '
        ```

        And here are the variables that get filled in:

        - 'make': Absolute(!) path to the make executable,
                  eg. 'C:/Users/krist/.embeetle/beetle_tools/gnu_make_4.2.0_64b/make.exe'

        - 'target': The 'makefile' target, such as 'build'/'clean'/... .

        - 'builddir_relpath': Relative path to the 'build' directory. If the command runs in the
                              toplevel folder, then this relative path is simply 'build'.

        - 'makefile_relpath': Relative path to the makefile starting from the build directory.

        - 'toolprefix': Absolute(!) path to the tool executable, including the prefix, eg.
                        'C:/Users/krist/.embeetle/beetle_tools/gnu_arm_toolchain_9.2.1_9-2019-q4-
                        major_32b/bin/arm-none-eabi-'

        - 'flashtool': Absolute(!) path to the OpenOCD or PyOCD executable, eg.
                       'C:/Users/krist/.embeetle/beetle_tools/openocd_0.10.0_dev01138_32b/bin/openocd.exe'

        **Conclusion**
        We pass 3 absolute paths to the 'makefile': the path to:
        - Gnu make
        - Compiler Toolchain
        - OpenOCD (or other flashtool)

        In itself, that is okay when all these tools are stored in the 'beetle_tools' folder. That's
        because Embeetle knows the location of its 'beetle_tools' folder at startup. So these three
        absolute paths are computed *on the spot* based on the location of the 'beetle_tools' folder
        *at that moment*. In other words - there is no problem here. The situation becomes different
        for tools that are located elsewhere.
        """

        def execute_target(success: bool, *args) -> None:
            if not success:
                abort()
                return
            mk_command = self.get_make_command_list(target, "console")
            if any(t in target.lower() for t in ("flash", "load")):
                serial_tab: _serial_console_.SerialConsole = (
                    data.main_form.get_tab_by_name("Serial Monitor")
                )
                if serial_tab:
                    try:
                        if serial_tab.is_serial_port_open():
                            print("\nINFO: Close serial connection\n")
                            serial_tab.toggle_serial_connection()
                    except Exception as e:
                        purefunctions.printc(
                            f"\nERROR: Cannot close serial connection!\n"
                            f"{traceback.format_exc()}\n",
                            color="error",
                        )
            console.run_command(
                commandlist=mk_command,
                callback=finish,
            )
            return

        def abort(*args) -> None:
            # Even though Johan takes care of linkerscript parsing now, it's still valid to call the
            # refresh function here, because I have to fill in the usages from the produced elf-
            # file.
            data.current_project.get_chip().repair_memregion_list(
                callback=abort_post,
                callbackArg=None,
            )
            return

        def abort_post(*args) -> None:
            if callback is not None:
                try:
                    callback(False, callbackArg)
                except:
                    traceback.print_exc()
                return
            return

        def finish(success: bool, *args) -> None:
            if not success:
                abort()
                return
            # Even though Johan takes care of linkerscript parsing now, it's still valid to call the
            # refresh function here, because I have to fill in the usages from the produced elf-
            # file.
            data.current_project.get_chip().repair_memregion_list(
                callback=finish_post,
                callbackArg=None,
            )
            return

        def finish_post(*args) -> None:
            if callback is not None:
                try:
                    callback(True, callbackArg)
                except:
                    traceback.print_exc()
                return
            return

        # * Start
        # Check if running makefile target can start
        self.__std_prechecker(
            callback=execute_target,
            callbackArg=None,
        )
        return

    def __std_prechecker(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """
        Perform standard checks before running a makefile target:
            - Does the 'build' directory exist?
            - Is something busy?
        """
        projObj = data.current_project

        def check_busy(cntr: int = 0) -> None:
            "Busy check must ALWAYS happen"
            # Unless aborted..
            if cntr > 7:
                yes = _ht_.beetle_busy_yes_no(
                    "Do you want to execute the command "
                    "as soon as the beetle<br>has time "
                    "for it?<br>"
                )
                if yes:
                    keep_waiting()
                    return
                abort(False)
                return
            # if _sa_to_dashboard_.SAToDashboard().is_feeder_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_sa_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_digester_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_filetree_folder_init_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_filetree_save_load_busy():
            #     qt.QTimer.singleShot(100, functools.partial(check_busy, cntr+1))
            #     return
            save()
            return

        def keep_waiting(*args) -> None:
            "User wants to wait"
            # if _sa_to_dashboard_.SAToDashboard().is_feeder_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_sa_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_digester_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_filetree_folder_init_busy() or \
            #         _sa_to_dashboard_.SAToDashboard().is_filetree_save_load_busy():
            #     qt.QTimer.singleShot(600, keep_waiting)
            #     return
            save()
            return

        def save(*args) -> None:
            "Save must ALWAYS happen"
            # Unless aborted..
            projObj.save_project(
                save_editor=True,
                save_dashboard=True,
                ask_permissions=True,
                forced_files=[],
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(success: bool, *args) -> None:
            "Checks okay"
            if success != True:  # noqa
                abort(True)
                return
            if callback is not None:
                callback(True, callbackArg)
            return

        def abort(show_message: bool = False) -> None:
            "Something wrong"
            if show_message:
                _ht_.save_failed("So the command cannot be executed.")
            if callback is not None:
                callback(False, callbackArg)
            return

        # * Start
        # Check builddir must ALWAYS happen
        builddir = projObj.get_treepath_seg().get_abspath("BUILD_DIR")
        if (builddir is None) or (builddir.lower() == "none"):
            _ht_.where_is_builddir()
            abort(False)
            return
        if os.path.isdir(builddir):
            check_busy()
            return
        s = _fp_.make_dir(
            dir_abspath=builddir,
            printfunc=print,
            catch_err=True,
            overwr=False,
        )
        if not s:
            _ht_.cannot_create_builddir()
            abort(False)
            return
        check_busy()
        return
