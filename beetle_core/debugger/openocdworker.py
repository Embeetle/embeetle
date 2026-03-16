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

import time
import queue
import threading
import traceback
import subprocess
import multiprocessing
import qt
import os_checker
import functions

# Python 3.13 removed telnetlib from the standard library
# The code below provides compatibility for both Python 3.12- and 3.13+
import platform

PYTHON_VERSION = tuple(map(int, platform.python_version_tuple()))

if PYTHON_VERSION >= (3, 13):
    """Python 3.13+ Compatibility Layer.

    In Python 3.13, the telnetlib module was removed from the standard library.
    While telnetlib3 exists as a replacement, it has a completely different API
    that is primarily async-based, making it incompatible with the existing
    code.

    This compatibility layer provides a drop-in replacement for telnetlib.Telnet
    that works with Python 3.13+ by using raw socket communication with the same
    interface as the original telnetlib.Telnet class.
    """
    # Import telnetlib3 for future potential use, but we'll use our own implementation
    try:
        import telnetlib3.client as telnetlib3_client
    except ImportError:
        pass

    class CompatTelnet:
        """Compatibility class that mimics telnetlib.Telnet for Python 3.13+

        This class implements the same interface as telnetlib.Telnet but uses
        raw socket communication instead. It's designed to be a drop-in replacement
        for the removed telnetlib module in Python 3.13+.

        The implementation focuses on the specific methods used by the OpenOCDWorker:
        - read_very_eager(): Non-blocking read that collects all available data
        - write(): Sends data to the telnet server

        Args:
            host (str): The hostname or IP address of the telnet server
            port (int): The port number of the telnet server
        """

        def __init__(self, host, port):
            self.host = host
            self.port = port
            self.sock = None
            self.connected = False
            self._connect()

        def _connect(self):
            """Establishes a socket connection to the telnet server.

            Uses a standard synchronous socket connection instead of the async
            approach used by telnetlib3.
            """
            import socket

            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                self.connected = True
            except Exception as e:
                print(f"[CompatTelnet] Connection error: {e}")
                self.connected = False

        def read_very_eager(self):
            """Non-blocking read that collects all available data from the
            socket.

            This mimics the behavior of telnetlib.Telnet.read_very_eager()
            by doing a non-blocking read of all data waiting on the socket.

            Returns:
                bytes: The data read from the socket, or an empty bytes object if
                       no data is available or the connection is closed
            """
            if not self.connected:
                return b""

            import select

            data = b""
            try:
                # Use select to check if data is available without blocking
                readable, _, _ = select.select([self.sock], [], [], 0)
                if self.sock in readable:
                    chunk = self.sock.recv(4096)
                    if chunk:
                        data += chunk
            except Exception:
                # Any exception means we should return what we have so far
                pass
            return data

        def write(self, data):
            """Sends data to the telnet server.

            This mimics the behavior of telnetlib.Telnet.write() by sending
            data to the telnet server. It converts strings to bytes if needed.

            Args:
                data: The data to send (bytes or string)
            """
            if not self.connected:
                return

            try:
                # Convert string to bytes if needed
                if isinstance(data, bytes):
                    self.sock.sendall(data)
                else:
                    self.sock.sendall(str(data).encode("ascii"))
            except Exception as e:
                print(f"[CompatTelnet] Write error: {e}")
                self.connected = False

else:
    # For Python 3.12 and earlier, use standard telnetlib
    import telnetlib


class OpenOCDWorker(qt.QObject):
    # Constants
    DEBUG = True

    # Signals
    started = qt.pyqtSignal()
    stdout_received = qt.pyqtSignal(str)
    telnet_received = qt.pyqtSignal(str)
    stopped = qt.pyqtSignal()
    signal_error = qt.pyqtSignal(str)

    # Class variables
    __running = False
    __openocd_path = None
    __openocd_probe_path = None
    __openocd_chip_path = None
    __telnet_in_queue = None

    def __init__(
        self, openocd_path, openocd_probe_path, openocd_chip_path, parent=None
    ):
        super().__init__(parent)
        self.__openocd_path = openocd_path
        self.__openocd_probe_path = openocd_probe_path
        self.__openocd_chip_path = openocd_chip_path
        self.__running = True
        self.__telnet_in_queue = multiprocessing.Queue()

    def start(self):
        try:
            sub_process = functions.subprocess_popen(
                [
                    self.__openocd_path,
                    "-f",
                    self.__openocd_probe_path,
                    "-f",
                    self.__openocd_chip_path,
                    #                    "-s", "$(OCDSCRIPTS_ABS_LOC)",
                    #                    "-d3", # Debugging enabled
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if self.DEBUG:
                print("[OpenOCDWorker] OpenOCD process started.")
            time.sleep(0.3)

            ## Stdout reading
            self.__thread_stdout_read = threading.Thread(
                target=self.__stdout_read_loop,
                args=[sub_process],
                daemon=True,
            )
            self.__thread_stdout_read.start()

            ## Telnet connection
            # Connect to the telnet server using the appropriate implementation
            # based on Python version (Python 3.13+ needs special handling)
            host = "127.0.0.1" if os_checker.is_os("windows") else "localhost"
            port = 4444  # Default OpenOCD telnet port

            if PYTHON_VERSION >= (3, 13):
                if self.DEBUG:
                    print(
                        f"[OpenOCDWorker] Using CompatTelnet for Python {platform.python_version()}"
                    )
                # Use our custom compatibility class for Python 3.13+
                tn = CompatTelnet(host, port)
            else:
                if self.DEBUG:
                    print(
                        f"[OpenOCDWorker] Using standard telnetlib for Python {platform.python_version()}"
                    )
                # Use standard telnetlib for Python 3.12 and earlier
                tn = telnetlib.Telnet(host, port)
            # Read
            self.__thread_telnet_read = threading.Thread(
                target=self.__telnet_read_loop,
                args=[tn],
                daemon=True,
            )
            self.__thread_telnet_read.start()
            # Write
            self.__thread_telnet_write = threading.Thread(
                target=self.__telnet_write_loop,
                args=[tn],
                daemon=True,
            )
            self.__thread_telnet_write.start()
        except:
            traceback.print_exc()
            self.shutdown()

    def __stdout_read_loop(self, sub_process):
        if self.DEBUG:
            print("[OpenOCDWorker] Standard output read loop started.")
        self.started.emit()
        while self.__running:
            retcode = sub_process.poll()

            available = len(sub_process.stdout.peek())
            if available > 0:
                byte_text = sub_process.stdout.readline()
                encoded_text = byte_text.decode("utf-8", "replace")
                self.stdout_received.emit(encoded_text)

            if retcode is not None:
                break

        sub_process.terminate()
        sub_process.wait()
        self.stopped.emit()
        if self.DEBUG:
            print("[OpenOCDWorker] Standard output read loop stopped.")

    def __telnet_read_loop(self, tn):
        if self.DEBUG:
            print("[OpenOCDWorker] Telnet read loop started.")
        while self.__running:
            try:
                byte_text = tn.read_very_eager()
                if len(byte_text) > 0:
                    encoded_text = byte_text.decode("utf-8", "replace")
                    self.telnet_received.emit(encoded_text)
                else:
                    time.sleep(0.01)
            except Exception as ex:
                self.signal_error.emit(str(ex))
                print(ex)
        if self.DEBUG:
            print("[OpenOCDWorker] Telnet read loop stopped.")

    def __telnet_write_loop(self, tn):
        if self.DEBUG:
            print("[OpenOCDWorker] Telnet write loop started.")
        while self.__running:
            try:
                command_bytes = self.__telnet_in_queue.get_nowait()
                tn.write(command_bytes)
            except queue.Empty:
                time.sleep(0.01)
        if self.DEBUG:
            print("[OpenOCDWorker] Telnet write loop stopped.")

    @qt.pyqtSlot(str)
    def send_command(self, command):
        try:
            if self.DEBUG:
                print(
                    "[OpenOCDWorker] Sent command through Telnet: {}".format(
                        command
                    )
                )
            command_bytes = bytes(f"{command}\r\n", encoding="ascii")
            self.__telnet_in_queue.put(command_bytes)
        except Exception as ex:
            self.signal_error.emit(str(ex))

    @qt.pyqtSlot()
    def shutdown(self):
        self.__running = False
        self.__thread_stdout_read = None
        self.__thread_telnet_read = None
        self.__thread_telnet_write = None
        if self.DEBUG:
            print("[OpenOCDWorker] Shutting down everything.")
