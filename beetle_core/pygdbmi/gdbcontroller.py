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

"""This module defines the `GdbController` class which runs gdb as a subprocess
and can write to it and read from it to get structured output."""

import logging
import subprocess
import shutil
from typing import Union, List, Optional
from pygdbmi.IoManager import IoManager
from pygdbmi.constants import (
    DEFAULT_GDB_TIMEOUT_SEC,
    DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC,
    USING_WINDOWS,
)

import qt
import functions

DEFAULT_GDB_LAUNCH_COMMAND = ["gdb", "--nx", "--quiet", "--interpreter=mi3"]
logger = logging.getLogger(__name__)


class GdbController(qt.QObject):
    data_received_signal = qt.pyqtSignal(object)

    def __init__(
        self,
        command: Optional[List[str]] = None,
        time_to_check_for_additional_output_sec=DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC,
        parent=None,
        custom_environment=None,
    ):
        """Run gdb as a subprocess. Send commands and receive structured output.
        Create new object, along with a gdb subprocess.

        Args:
            command: Command to run in shell to spawn new gdb subprocess
            time_to_check_for_additional_output_sec: When parsing responses, wait this amout of time before exiting (exits before timeout is reached to save time). If <= 0, full timeout time is used.
        Returns:
            New GdbController object
        """
        super().__init__(parent)

        self.custom_environment = custom_environment

        if command is None:
            command = DEFAULT_GDB_LAUNCH_COMMAND

        if not any([("--interpreter=mi" in c) for c in command]):
            logger.warning(
                "Adding `--interpreter=mi3` (or similar) is recommended to get structured output. "
                + "See https://sourceware.org/gdb/onlinedocs/gdb/Mode-Options.html#Mode-Options."
            )
        self.abs_gdb_path = None  # abs path to gdb executable
        self.command = command  # type: List[str]
        self.time_to_check_for_additional_output_sec = (
            time_to_check_for_additional_output_sec
        )
        self.gdb_process = None
        gdb_path = command[0]
        if not gdb_path:
            raise ValueError("a valid path to gdb must be specified")

        else:
            abs_gdb_path = shutil.which(gdb_path)
            if abs_gdb_path is None:
                raise ValueError(
                    'gdb executable could not be resolved from "%s"' % gdb_path
                )

            else:
                self.abs_gdb_path = abs_gdb_path

        self.spawn_new_gdb_subprocess()

    def spawn_new_gdb_subprocess(self):
        """Spawn a new gdb subprocess with the arguments supplied to the object
        during initialization.

        If gdb subprocess already exists, terminate
        it before spanwing a new one.
        Return int: gdb process id
        """
        if self.gdb_process:
            logger.debug(
                "Killing current gdb subprocess (pid %d)" % self.gdb_process.pid
            )
            self.exit()

        logger.debug(f'Launching gdb: {" ".join(self.command)}')

        # Use pipes to the standard streams
        # * Create the 'startupinfo' parameter.
        self.gdb_process = functions.subprocess_popen(
            self.command,
            shell=False,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=self.custom_environment,
        )

        self.io_manager = IoManager(
            self.gdb_process.stdin,
            self.gdb_process.stdout,
            self.gdb_process.stderr,
            parent=self,
        )
        self.io_manager.data_received_signal.connect(self.data_received_signal)
        return self.gdb_process.pid

    def write(
        self,
        mi_cmd_to_write: Union[str, List[str]],
    ) -> None:
        """Write command to gdb.

        See IoManager.write() for details
        """
        self.io_manager.write(mi_cmd_to_write)

    def exit(self) -> None:
        """Terminate gdb process."""
        self.io_manager.stop()

        if self.gdb_process:
            self.gdb_process.terminate()
            self.gdb_process.wait()
            self.gdb_process.communicate()
        self.gdb_process = None
        return None
