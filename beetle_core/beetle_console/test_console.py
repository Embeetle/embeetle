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
import threading
import serial_port as _serial_port_
import interactive_command as _interactive_command_
import sys
import time


# This file contains sample code used to test the 'serial_port' and
# 'interactive_command' modules in the context of a simple console.
# The code below does not rely on a GUI framework.  It reads user input from
# standard input line per line using the `input` function, and writes output to
# standard output.
# In a GUI context, output from the serial port or command can be synchronized
# with user input or other events using the GUI's event queue.  Here, we use a
# simple mutex instead.
# Both 'serial_port.SerialPort' and 'interactive_command.Command' need a
# "handler" for callbacks.  The handler is any Python object that implements the
# necessary callback methods.  The names and signatures of these callback
# methods have been carefully chosen to be compatible, so that the same console
# object (e.g. the one defined below) can be used for both.
class Console:
    """"""

    def __init__(self):
        """
        Create a basic console.  The target - a serial port or command - can be
        set later.

        The target is set in functions 'open_serial_port()' and 'run_command()'.
        This object lives until:

            -> 'close()' function is invoked to stop the command or close
               the serial port.

            -> 'receive_exit()' callback is invoked - commands only.

        After the 'close()' or 'receive_exit()' calls, the target object is no
        longer useful. It cannot be restarted. So it must be thrown away.

        """
        self.__mutex = threading.Lock()
        self.__target: Union[
            _serial_port_.SerialPort, _interactive_command_.Command, None
        ] = None
        self.__is_running = False
        return

    def open_serial_port(self, port: str) -> bool:
        """Open a serial port. Return True if successful.

        :param port: A string naming the serial port to be opened; e.g.
            /deb/ttyUSB0 on Linux or COM2 on Windows.
        """
        assert not self.__target
        self.__is_running = False
        try:
            # Create and start the port with default parameter values.  See
            # 'serial_port.SerialPort' for available parameters and default
            # values.
            self.__target = _serial_port_.SerialPort(port)
            self.__is_running = True
            self.__target.start(self)
        except _serial_port_.Error as error:
            print(f"!! {error}")
        return self.__is_running

    def run_command(self, command: List[str]) -> bool:
        """Run a command. Return True if successful.

        :param command: A list of strings. The first item of the list is the
            program to execute, and the following items are the pro- gram
            arguments. If you start from a single string, use something like
            'shlex.split' to convert it to a list, taking into account OS-
            specific conventions.
        """
        assert not self.__target
        try:
            # Create and start the command with default parameter values.  See
            # 'interactive_command.Command' for available parameters and default
            # values.
            self.__target = _interactive_command_.Command(command)
            self.__is_running = True
            self.__target.start(self)
            return True
        except _interactive_command_.Error as error:
            print(f"!! {error}")
        return False

    def close(self) -> None:
        """Stop the command or close the serial port.

        The target object becomes useless after this, so it's destroyed.
        """
        assert self.__target
        self.__target.close()
        self.__target = None
        return

    def send(self, bytes_to_send: Union[bytes, bytearray]) -> None:
        """Send bytes to the serial port or command.

        Do *not* lock the mutex while sending bytes to avoid deadlocks.  Bytes
        can be received asynchronously also while sending. Depending on the com-
        mand or application running on th eother side of the serial link, if too
        much data is received while the mutex is locked, buffers may become full
        and it may become impossible to send the bytes until received bytes are
        processed. Therefore, received bytes must be handled without waiting for
        the send call to return.

        @Johan: I changed the parameter name from 'bytes' into 'bytes_to_send',
        to avoid overriding the builtin-type 'bytes'.
        """
        if self.__target:
            try:
                self.__target.send(bytes_to_send)
            except _serial_port_.Error as error:
                print(f"!> {error}")
        return

    def receive(self, bytes_received: bytes, is_stderr: bool = False) -> None:
        """Callback called asynchronously (from another thread) when data is re-
        ceived from the serial port or command.

        The data is provided as a byte string. It must be decoded to convert it
        to a normal string.  The 'decode' function has an 'encoding' parameter
        that defaults to UTF-8,  which is fine for most applications.

        Only commands supply the 'is_stderr' argument. To allow a single method
        to implement callbacks from both serial ports and commands, we provide a
        default value here.  This default value is only used when receiving data
        from a serial port.
        """
        with self.__mutex:
            if is_stderr:
                print(f"[ERR|{bytes_received.decode()}]", end="")
            else:
                print(f"{bytes_received.decode()}", end="")
        return

    def receive_error(
        self,
        error: Union[_serial_port_.Error, _interactive_command_.Error],
        is_stderr: bool = False,
    ) -> None:
        """Callback called asynchronously (from another thread) when an
        exception occurs while receiving data from the serial port or command.

        :param error: The exception that was raised. Both 'serial_port.py' and
            'interactive_command.py' define an Error() base class to encapsulate
            all thrown exceptions.
        :param is_stderr: Only commands supply this argument. To allow a single
            method to implement callbacks from both serial ports and commands,
            we provide a default value here. This default value is only used
            when receiving data from a serial port.
        """
        with self.__mutex:
            print(f"<! {error}")
        return

    def receive_exit(self, exit_code: int) -> None:
        """COMMANDS ONLY.

        Callback called asynchronously (from another thread) when the command
        exits.

        After this call, the command is not automatically closed.  'close()'
        still needs to be called to cleanup. The reason is that 'close()' cannot
        be called asynchronously.

        :param exit_code: Zero if exit without errors. Otherwise, the value
            depends on the command and should be mentioned in the command's
            documentation.
        """
        with self.__mutex:
            print(f"{self.__target.command[0]}: exit code {exit_code}")
            self.__is_running = False

    def disconnect(self) -> None:
        """SERIAL PORTS ONLY.

        callback called asynchronously (from another thread) when the serial
        port is disconnected.

        NOTE: disconnecting a port will not automatically close it. The port will
        try to reconnect by default, unless you close it.
        """
        print(f"{self.__target.port}: disconnected")
        return

    def reconnect(self) -> None:
        """SERIAL PORTS ONLY.

        Serial ports only: callback called asynchronously (from another thread)
        when the serial port is reconnected.
        """
        print(f"{self.__target.port}: reconnected")
        return

    def run(self) -> None:
        """Repeatedly read input and send it to the serial port or command until
        the command exits or an exception occurs."""
        while True:
            try:
                data = input()
                with self.__mutex:
                    if not self.__is_running:
                        break
                if data == "error":
                    bytes = b"\xc3\x28"
                else:
                    if data == "smile":
                        data = "😀 ∑ Π ∫ ∂ √"
                    bytes = (data + "\n").encode()
                self.send(bytes)
            except EOFError:
                break
        return

    @property
    def name(self):
        return self.__target.name


# Test code: try opening some serial ports or running some commands.  Run the
# first one that succeeds, then exit when it is closed.  Note: it is perfectly
# possible to reuse the console by opening another serial port or starting
# another command;  this is currently not done here.
if __name__ == "__main__":
    print("Hello world")
    console = Console()
    # When an exception occurs, it is essential that the console is closed.
    # Otherwise, background threads continue to run and the whole console
    # program will refuse to stop even when the main thread exits. Here, we use
    # a 'try ... finally' clause to achieve that.
    try:
        console.open_serial_port("/dev/ttyUSB0") or console.open_serial_port(
            "/dev/ttyUSB1"
        ) or console.open_serial_port(
            "/dev/ttyUSB2"
        ) or console.open_serial_port(
            "COM1"
        ) or console.open_serial_port(
            "COM2"
        ) or console.open_serial_port(
            "COM3"
        ) or console.run_command(
            ["bash"]
        ) or console.run_command(
            ["cmd"]
        ) or sys.exit(
            1
        )
        # or console.run_command(['ls', '-Alh']) \
        print(f"Opened {console.name}")
        console.run()
    finally:
        print(f"Closing {console.name} ...")
        console.close()
        print("Bye")
