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
import traceback
from typing import *
import serial
import threading
import functools
import time
import qt
import data
import functions

q = "'"


class Error(Exception):
    """Base class for all exceptions thrown for serial ports.  Exceptions of
    other.

    classes - thrown for example from lower-level software used while accessing
    a serial port - are caught and converted into an exception of this class.
    This makes it easy to catch all serial port related exceptions.

    The original exception is available as 'self.error'. The serial port's name
    is available as 'self.port'.
    """

    def __init__(self, port, error):
        self.error = error
        self.port = port
        super().__init__()

    def __str__(self):
        return f"{str(self.error)}"

    @property
    def name(self):
        return self.port


class SerialPort:
    """Class to conveniently access serial ports.

    Data received from the serial port is handled by a separate thread that per-
    forms a callback when enough data is received or after a timeout. Any ex-
    ception thrown while receiving data is also handled by a callback. There is
    no need to regularly poll for new data or use asynchronous IO.

    Since callbacks are performed from a background thread, callback implemen-
    tation will need some mechanism to synchronize the callbacks with other
    operations.  The appropriate mechanism depends on the application. For GUI
    applications (e.g. Qt based), this can consist of adding an event to the
    event queue (e.g. by sending a signal in Qt); the event queue will implicit-
    ly serialize events. For other applications, it may require the use of a
    mutex or similar synchronisation primitive.
    """

    # Allowed values for serial port configuration parameters.
    BAUDRATES = [
        50,
        75,
        110,
        134,
        150,
        200,
        300,
        600,
        1200,
        1800,
        2400,
        4800,
        9600,
        19200,
        38400,
        57600,
        115200,
        230400,
        460800,
        500000,
        576000,
        921600,
        1000000,
        1152000,
        1500000,
        2000000,
        2500000,
        3000000,
        3500000,
        4000000,
    ]
    BYTESIZES = [5, 6, 7, 8]
    PARITIES = ["N", "E", "O", "M", "S"]
    PARITY_NAMES = ["none", "even", "odd", "mark", "space"]
    STOPBITS = [1, 1.5, 2]

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: Union[int, float] = 1,
    ) -> None:
        """Open a serial port.

        :param port:        A string naming the serial port to be opened;
                            e.g. /deb/ttyUSB0 on Linux or COM2 on Windows.
        :param baudrate:    Serial port setting.
        :param bytesize:    Serial port setting.
        :param parity:      Serial port setting.
        :param stopbits:    Serial port setting.

        NOTES:
         - Allowed values are listed above.

         - This call can throw exceptions. Relevant exceptions will be of the
           Error class declared above.  Other exceptions indicate bugs.
        """
        print(
            f"\nSerialPort("
            f"\n    port = {port},"
            f"\n    baudrate = {baudrate},"
            f"\n    bytesize = {bytesize},"
            f"\n    parity = {parity},"
            f"\n    stopbits = {stopbits},"
            f"\n)\n"
        )
        self.port = port

        def open_port():
            self.__dev = serial.Serial(
                port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
            )

        self.__open_port = open_port
        self._dev: Optional[serial.Serial] = None
        self.__is_closed = False
        try:
            open_port()
        except (IOError, ValueError, serial.SerialException) as error:
            raise Error(port, error)
        return

    @property
    def name(self):
        return self.port

    def start(
        self,
        handler: Any,
        receive_max_bytes: int = 1024,
        receive_timeout: float = 0.02,
        reconnect_period=1,
    ) -> None:
        """Start receiving data from this serial port using callbacks.

        :param handler:  An object with the following methods implementing
                         callbacks:

            - receive(bytes): Called asynchronously when bytes are received from
                              the serial port. 'bytes' is a non-empty byte
                              string.

            - receive_error(error): Called asynchronously when an exception oc-
                                    curs while trying to read from the serial
                                    port.
                                    'error' > instance of serial_port.Error
                                    'error.error' > the original exception.

            - disconnect(): Called asynchronously when the serial port is dis-
                            connected. NOTE: disconnecting a port will not auto-
                            matically close it. The port will try to reconnect
                            by default, unless you close it.

            - reconnect(): Called asynchronously when the serial port is recon-
                           nected.


        :param receive_max_bytes:  The maximum number of bytes that will be
                                   passed in one call of handler.receive(bytes).

        :param receive_timeout:    The maximum delay in seconds between receiv-
                                   ing bytes and calling handler.receive(bytes).

        :param reconnect_period:   The time in seconds between attempts to re-
                                   connect to the port when reading fails.

        WARNING:
        All callbacks are launched from a background thread.
        """
        self.__dev.timeout = receive_timeout

        def receive():
            while not self.__is_closed:
                try:
                    bytes = self.__dev.read(receive_max_bytes)
                    if self.__is_closed:
                        break
                    if bytes:
                        handler.receive(bytes)
                except Exception as error:
                    # Don't report exceptions when the serial port is closed.
                    # Exceptions are to be expected in that case,  and should
                    # silently exit the receive loop.
                    if self.__is_closed:
                        break
                    handler.receive_error(Error(self.port, error))
                    if isinstance(error, serial.SerialException):
                        # Disconnected;  try to reconnect.
                        handler.disconnect()
                        self.__dev.close()
                        while not self.__is_closed:
                            time.sleep(reconnect_period)
                            try:
                                self.__open_port()
                                self.__dev.timeout = receive_timeout
                                handler.reconnect()
                                break
                            except serial.SerialException as error:
                                pass
                    else:
                        break
            return

        threading.Thread(
            name=f"{self.port}#receiver",
            target=receive,
            daemon=True,
        ).start()
        return

    def send(self, bytes_to_send: Union[bytes, bytearray]) -> None:
        """Send bytes to the serial port.

        :param bytes_to_send:   The bytes to be sent, from type 'bytes' or
                                'bytearray'.

        NOTES:
          - This call can throw exceptions. Relevant exceptions will be of the
            Error() class declared above.

          - @Johan:
            I changed the parameter name from 'bytes' into 'bytes_to_send', to
            avoid overriding the builtin-type 'bytes'.

        WARNING:
        Do *not* lock the mutex while sending bytes to avoid deadlocks. Bytes
        can be received asynchronously also while sending. The receive() call-
        back should therefore be able to run (not locked) while waiting for this
        send() function to return!
        """
        assert not self.__is_closed
        try:
            self.__dev.write(bytes_to_send)
        except IOError as error:
            raise Error(self.port, error)
        return

    def close(self) -> None:
        """Stop receiving data from this port and close it.

        Once stopped, 'send()' cannot be called anymore and the port cannot be
        restarted; you will need to create a new serial port.

        Call this when you no longer need the serial port, so that it is free
        for use by other programs.  Serial ports are not locked, so another
        program can open the same serial port at any time, but data arriving at
        the serial port will be randomly received by one of the programs trying
        to read from it, causing confusion.
        """
        assert not self.__is_closed
        self.__is_closed = True
        self.__dev.close()
        self.__dev = None
        return


def touch_serial_port(
    port: str,
    baudrate: int,
    printfunc: Callable,
    callback: Callable,
) -> None:
    """Open and immediately close the given serial port.

    :param port: A string naming the serial port to be opened; e.g.
        '/deb/ttyUSB0' on Linux or 'COM2' on Windows.
    :param baudrate: Serial port setting.
    :param printfunc: Function used to print output.
    :param callback: Callback to be invoked 0.4 seconds after closing the serial
        port (required by SAM-BA based boards).
    """
    printfunc(f"  > Open and close immediately port {q}{port}{q}...\n")
    try:
        s = serial.Serial(
            port=port,
            baudrate=baudrate,
        )
        s.setDTR(False)
        s.close()
    except:
        printfunc(f"  > Failed:\n")
        printfunc(traceback.format_exc())
        printfunc("\n")
        qt.QTimer.singleShot(
            400,
            callback,
        )
        return
    printfunc(f"  > Done.\n")
    qt.QTimer.singleShot(
        400,
        callback,
    )
    return


def wait_for_new_serial_port(
    before_portnames: List[str],
    fallback_portname: str,
    printfunc: Callable,
    callback: Callable,
) -> None:
    """While waiting, check regularly the available serial ports. If one of them
    is new (it wasn't available in the 'before_portnames' listing), then return
    it in the callback.

    If after some waiting, no new port is found, just return the fallback port
    in the callback.

    Before returning anything, try to open-and-close the found/fallback serial
    port. If that fails, wait for another second and then return the port in the
    callback.

    :param before_portnames: List of available serial port names before this
        function was invoked.
    :param fallback_portname: The port name to be returned (in the callback) if
        no new port could be detected in the given time.
    :param printfunc: Function used to print output.
    :param callback: Callback to be invoked as soon as the new port is found (or
        1 second after finding it).
    """
    printfunc(f"  > Waiting for new port to appear...\n")
    elapsed = 0

    def next_try(*args) -> None:
        nonlocal before_portnames, elapsed
        if elapsed > 5:
            check_fallback_port()
            return
        now_portnames = list(functions.list_serial_ports().keys())
        for p in now_portnames:
            if p not in before_portnames:
                found_port(p)
                return
        before_portnames = now_portnames
        elapsed += 0.25
        printfunc(f"  > Waiting...\n")
        qt.QTimer.singleShot(250, next_try)
        return

    def found_port(portname: str) -> None:
        # A new port was found.
        printfunc(f"  > New port detected: {q}{portname}{q}\n")
        finish(portname)
        return

    def check_fallback_port(*args) -> None:
        # No new port was found. Check if the fallback port is still
        # available.
        printfunc(
            f"  > No new port detected, use fallback "
            f"port: {q}{fallback_portname}{q}\n"
        )
        now_portnames = functions.list_serial_ports().keys()
        for p in now_portnames:
            if p == fallback_portname:
                break
        else:
            # The fallback port is no longer available.
            printfunc(
                f"  > Port {q}{fallback_portname}{q} no longer available.\n"
            )
            printfunc(
                f"\n"
                f"Error: Couldn{q}t find a board on port {q}{fallback_portname}{q}. "
                f"Check that you have the correct port selected. "
                f"If it is correct, try pressing the board{q}s reset "
                f"button after initiating the upload.\n",
                f"#ef2929",
            )
            finish(None)
            return
        # The fallback port is still there. Use it.
        finish(fallback_portname)
        return

    def finish(portname: Optional[str]) -> None:
        if portname is None:
            callback(None)
            return
        try:
            printfunc(
                f"  > Open and close port {q}{portname}{q} to "
                f"check if it works.\n"
            )
            s = serial.Serial(portname)
            s.close()
        except serial.SerialException:
            # Opening and closing the serial port failed,
            # wait one second before returning the serial
            # port in the callback.
            printfunc(f"  > It doesn{q}t work. Wait one second...\n")
            qt.QTimer.singleShot(
                1000,
                functools.partial(
                    callback,
                    portname,
                ),
            )
            return
        # No need to wait.
        printfunc(f"  > It works.\n")
        callback(portname)
        return

    next_try()
    return
