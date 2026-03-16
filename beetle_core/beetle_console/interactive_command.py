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
import subprocess
import threading
import purefunctions
import os_checker
import data
import sys

q = "'"


class Error(Exception):
    """Base class for all exceptions thrown for interactive commands.
    Exceptions.

    of other classes - thrown for example from lower-level software used while
    accessing the interactive command - are caught and converted into an except-
    ion of this class.  This makes it easy to catch all interactive command re-
    lated exceptions.

    The original exception is available as 'self.error'. The command - a list of
    strings - is available as 'self.command'.
    """

    def __init__(self, command, error):
        self.command = command
        self.error = error
        super().__init__()

    def __str__(self):
        return f"{self.error}"

    @property
    def name(self):
        return self.command[0]


class Command:
    """Class to conveniently run an interactive command in the background.

    In this context, "interactive" means that data can be sent to and received
    from the command while it is running; it is not necessary to prepare input
    data beforehand or to wait until the command stops to process its output
    data.

    Data received from the command's standard output and standard error is
    handled by a separate thread that performs a callback as soon as data is
    received. Any exception thrown while receiving data is also handled by a
    callback. There is no need to regularly poll for new data or use asynchron-
    ous IO.

    Since callbacks are performed from a background thread, callback implemen-
    tation will need some mechanism to synchronize the callbacks with other
    operations. The appropriate mechanism depends on the application. For GUI
    applications (e.g. Qt based), this can consist of adding an event to the
    event queue (e.g. by sending a signal in Qt); the event queue will implicit-
    ly serialize events. For other applications, it may require the use of a
    mutex or similar synchronisation primitive.

    LIMITATION: Communication with the running command is currently implemented
    using basic pipes; no pseudo-terminal is created. As a result, some commands
    will react as if they are not running interactively; for example, they will
    not write a prompt when waiting for input. Pseudo-terminals may be implemen-
    ted in the future, if there is a concrete need for them.
    """

    def __init__(
        self,
        command: List[str],
        cwd: Union[str, None] = None,
        env: Union[Dict[str, str], None] = None,
    ) -> None:
        """Create a command. The command will run immediately. Output will be
        buf- fered until the 'start()' method is called.

        :param command: A list of strings. The first item is the program to
                        execute, and the following items are the arguments. If
                        you start from a single string, use something like
                        'shlex.split' to convert it to a list, taking into
                        account OS-specific conventions.

        :param cwd:     The working directory in which to execute the command,
                        or None for the current working directory.

        :param env:     A dictionary of environment variables to be passed to
                        the command, or None to use the environment variables of
                        the calling process.

        WARNINGS:

         - This call can throw exceptions. Relevant exceptions will be of the
           Error class declared above.

         - Always call the `close()` method before exiting the calling process.
           Otherwise, the process may hang or throw unexpected exceptions.  One
           way to ensure that the `close()` method is called is to use a `try
           ... finally` clause.
        """
        self.command = command
        self.__stdin_closed = False
        self.__terminated = False
        self.__mutex = threading.Lock()
        self.__handler = None
        self.__proc = None  # Default in case Popen fails.
        try:
            print(f"\n" f"command = {command}\n" f"\n" f"cwd = {cwd}\n" f"\n")
            self.__proc = purefunctions.subprocess_popen(
                command,
                cwd=cwd,
                env=env,
                bufsize=0,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise Error(command, error)
        return

    @property
    def name(self):
        return self.command[0]

    def start(self, handler: Any, receive_max_bytes: int = 1024) -> None:
        """Start receiving data from this command using callbacks.

        :param handler:  An object with the following methods implementing
                         callbacks:

            - receive(bytes, is_stderr): Called asynchronously when bytes are
                                    received from the command. 'bytes' is a non-
                                    -empty byte string.
                                    > 'is_stderr' is False for bytes received on
                                    standard output and True for bytes received
                                    on standard error.

            - receive_error(error, is_stderr): Called asynchronously when an
                                    exception occurs while trying to read from
                                    the command.
                                    > 'error' is an instance of the
                                    Error() class defined above. 'error.error'
                                    is the original exception.
                                    > 'is_stderr' is False for exceptions thrown
                                    while receiving from standard output and
                                    True for exceptions thrown while receiving
                                    from standard error.

            - receive_exit(exit_code): Called asynchronously when the command
                                    exits. 'exit_code' is the command's exit
                                    code. If the command stops due to a signal,
                                    it is minus the signal number. After this
                                    call, no more output or errors will be
                                    reported and `send` cannot be called
                                    anymore.

        :param receive_max_bytes:   The maximum number of bytes that will be
                                    passed in one call of handler.receive(bytes).
        """
        self.__handler = handler

        # Note: The 'receive()' nested function was type-annotated with:
        #    IO[AnyStr]
        # I believe this led to the following crash on Linux:
        #    NameError: name 'IO' is not defined
        def receive(stream, is_stderr):
            "Keep reading bytes from process"
            while True:
                try:
                    received_bytes = stream.read(receive_max_bytes)
                    if not received_bytes:
                        # 'read' returns zero bytes at end-of-file
                        break
                    # Report output, unless already terminated. When terminated,
                    # the handler does not expect any callback anymore so might
                    # fail.
                    with self.__mutex:
                        if not self.__terminated:
                            handler.receive(received_bytes, is_stderr)
                        else:
                            print("suppress output from terminated command")
                except (
                    IOError,
                    subprocess.SubprocessError,
                    ValueError,
                ) as error:
                    # Report error, unless already terminated. When terminated,
                    # the handler does not expect an error callback anymore so
                    # might fail.
                    with self.__mutex:
                        if not self.__terminated:
                            handler.receive_error(
                                Error(self.command, error), is_stderr
                            )
                    break
            return

        stdout_receiver = threading.Thread(
            name=f"{self.name}#receiver",
            target=receive,
            args=(self.__proc.stdout, False),  # Arguments given to receive()
        )
        stdout_receiver.start()

        stderr_receiver = threading.Thread(
            name=f"{self.name}#stderr#receiver",
            target=receive,
            daemon=True,
            args=(self.__proc.stderr, True),  # Arguments given to receive()
        )
        stderr_receiver.start()

        def wait(proc):
            # First wait until both receiver threads have exited.  Otherwise, we
            # risk telling the console that the process has exited before all
            # output data has been processed in the 'receive()' loop.  The
            # receive loop will exit as soon as it reaches end-of-file.
            stdout_receiver.join()
            stderr_receiver.join()
            # Now wait for the process to stop and report its exit status.
            # NOTE: There is no need for a timeout here.  When a process stops,
            # the OS guarantees that any reader of its output streams will reach
            # end-of-file.  If not, the above join calls will hang anyway, so
            # the problem - if any - needs to be solved in the receiver loop.
            # Most probably, when both receiver loop threads have exited, the
            # process has already exited too. The reason why we do a wait call
            # here anyway is that it is possible that a process closes its
            # output and error streams but continues to run, maybe writing to
            # some file or socket.  In that case,  there is no exit status yet.
            exit_code = proc.wait()

            # Report status, unless already terminated. When terminated, the
            # handler does not expect an exit status anymore so might fail.
            with self.__mutex:
                if not self.__terminated:
                    self.__terminated = True
                    handler.receive_exit(exit_code)
                else:
                    print(
                        f"suppress exit code {exit_code} "
                        "from terminated command"
                    )
            return

        # Wait in a separate thread, so that an exit status is reported as soon
        # as the command exits.
        self.__waiter = threading.Thread(
            name=f"{self.name}#waiter",
            target=wait,
            daemon=True,
            args=(self.__proc,),
        )
        self.__waiter.start()
        return

    def send(self, bytes_to_send: Union[bytes, bytearray]) -> None:
        """Send bytes to the command's standard input.

        :param bytes_to_send:  The bytes to be sent, from type 'bytes' or
                               'bytearray'.

        NOTES:
          - This call can throw exceptions. Relevant exceptions will be of the
            Error() class declared above.

          - @Johan:
            I changed the parameter name from 'bytes' into 'bytes_to_send', to
            avoid overriding the builtin-type 'bytes'.

        WARNING:
        Do *not* block callbacks during this call. For example, if you are using
        a mutex to synchronize callbacks, do not lock it. If you do so, a dead-
        lock may occur. The pipes used to communicate to and from the command
        have a finite buffer size; if all buffers are full, sending will block
        waiting for room in the buffers, but buffers cannot be emptied because
        you blocked the receive callbacks.
        """
        assert self.__proc
        try:
            self.__proc.stdin.write(bytes_to_send)
        except (IOError, subprocess.SubprocessError) as error:
            raise Error(self.command, error)
        return

    def send_end_of_file(self):
        """Send end-of-file to the command's input stream.

        After this call,  sending more data to the command will fail.
        """
        if not self.__stdin_closed:
            self.__proc.stdin.close()
            self.__stdin_closed = True

    def close(self, timeout: float = 5, timeout_exit_code=-128) -> None:
        """If the command is still running, stop it; then free any resources
        used.

        If you do not call `close()`, the command will continue to run, taking
        up resources, and it will *not* be garbage collected. In addition, the
        current process may refuse to stop or throw unexpected exceptions even
        when its main thread exits.  Make sure to call close() when you will no
        longer access the command.

        When the command stops, its exit code is reported.  Once stopped,
        'send()' cannot be called anymore and no more callbacks will be
        performed.

        If the command refuses to stop, it is killed after the specified
        timeout.  A killed command reports the exit status specified by
        'timeout_exit_code'.

        Do not call `close` from `receive_exit`, because `receive_exit` runs in
        a background thread, and one of the resources to be cleaned up is
        exactly that thread. Calling `close` from `receive_exit` would cause a
        deadlock. Also do not call it from Command.__del__(self), as that might
        run in the same background thread when the command exits. Also no need
        to call it there; the command has already exited, and resources will
        automatically be garbage collected.

        :param timeout:  Amount of time in seconds to wait for a process to stop
                         cleanly.  After this timeout, kill it.
        """
        assert self.__proc
        # Closing the input stream may automatically stop the command.
        self.send_end_of_file()
        if self.__is_running():
            print("send termination signal")
            self.__proc.terminate()
        self.__waiter.join(timeout=timeout)
        if self.__waiter.is_alive():
            # The command did not honor the termination request within the
            # specified timeout, so kill it.
            if self.__is_running():
                print("send kill signal")
                self.__proc.kill()

            # Join should return almost immediately if kill worked, as it
            # always should.  If not, there is nothing more we can do. The
            # timeout below is only meant as a safeguard to avoid waiting
            # forever when kill does not work.
            self.__waiter.join(timeout=timeout)

            # Windows only: final attempt to kill the process.
            if os_checker.is_os("windows"):
                if self.__is_running():
                    print(
                        f"subprocess.call(\n"
                        f"    [{q}taskkill{q}, {q}/F{q}, {q}/T{q}, "
                        f"{q}/PID{q}, {str(self.__proc.pid)}]\n"
                        f")\n"
                    )
                    subprocess.call(
                        ["taskkill", "/F", "/T", "/PID", str(self.__proc.pid)]
                    )

            # Set the terminated flag to ensure that no exit status is reported
            # if the command exits later. The handler does not expect any
            # callbacks after this function returns.
            with self.__mutex:
                if not self.__terminated:
                    print("subprocess refused to exit before timeout")
                    self.__terminated = True
                    self.__handler.receive_exit(timeout_exit_code)

        self.__proc.stdout.close()
        self.__proc.stderr.close()
        self.__proc = None
        return

    def __is_running(self):
        return self.__proc.poll() is None
