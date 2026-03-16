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

import socket
import time
import qt
import functions
import functools
import traceback
import multiprocessing
import multiprocessing.connection

DEBUG_MODE = False
STATUS_MODE = False


def debug_echo(obj, *messages):
    if DEBUG_MODE:
        print(
            "[{}-{}]".format(obj.__class__.__name__, obj.name),
            " ".join([str(x) for x in messages]),
        )


def status_echo(obj, *messages):
    if STATUS_MODE:
        print(
            "[{}-{}]".format(obj.__class__.__name__, obj.name),
            " ".join([str(x) for x in messages]),
        )


class CommClient:
    ADDRESS = "localhost"
    PORT = 19191
    PASSWORD = "embeetle"
    connection = None
    # Callbacks
    receive_callback = None

    def self_destruct(self) -> None:
        """"""
        self.__del__()

    def __init__(self, name, receive_callback):
        self.running = False
        self.name = name
        self.receive_callback = receive_callback
        self.initialized = False
        functions.create_thread(self.reinitialize)

    def __del__(self):
        self.running = False
        if self.connection is not None:
            self.connection.close()

    def reinitialize(self):
        self.initialized = False
        while self.initialized == False:
            try:
                self.connection = multiprocessing.connection.Client(
                    (self.ADDRESS, self.PORT),
                    authkey=self.PASSWORD.encode("utf-8"),
                )
                self.initialized = True
                functions.create_thread(self.recv_loop)
            except KeyboardInterrupt as ke:
                raise ke
            except Exception as ex:
                debug_echo(self, "init error, trying again ...")

    def recv_loop(self):
        try:
            debug_echo(self, "[CommClient] Receiving ...")
            self.running = True
            while self.running == True:
                if self.connection.poll():
                    status_echo(self, "recv")
                    _data = self.connection.recv()
                    status_echo(self, "recv success")
                    debug_echo(self, "Received:\n{}".format(_data))
                    self.receive_callback(_data)
                else:
                    time.sleep(0.1)
        except Exception as ex:
            debug_echo(self, "recv loop error:\n{}".format(str(ex)))
            self.reinitialize()

    def send(self, message):
        if self.initialized:
            self.connection.send(message)


class CommListener:
    ADDRESS = "localhost"
    PORT = 19191
    PASSWORD = "embeetle"
    running = False
    stored_connections = None
    connection = None
    # Callbacks
    stopped_callback = None

    def self_destruct(self) -> None:
        """"""
        self.__del__()

    def __init__(self, name, stopped_callback):
        self.running = False
        self.name = name
        self.stored_connections = []
        self.connection = None
        self.stopped_callback = stopped_callback
        try:
            functions.create_thread(self.connecting_loop)
        except:
            debug_echo(self, traceback.format_exc())

    def __del__(self):
        self.running = False
        if self.connection is not None:
            self.connection.close()
        for c in self.stored_connections:
            c[0].close()

    def connecting_loop(self):
        try:
            with multiprocessing.connection.Listener(
                (self.ADDRESS, self.PORT), authkey=self.PASSWORD.encode("utf-8")
            ) as listener:
                debug_echo(self, "Listening ...")
                self.running = True
                #                    listener._listener._socket.settimeout(1.0)
                while self.running == True:
                    try:
                        conn = listener.accept()
                        self._create_listening_thread(
                            conn, listener.last_accepted
                        )
                    except socket.timeout:
                        pass
        except Exception as ex:
            #            debug_echo(self, ex)
            self.running = False
            time.sleep(0.1)
            try:
                self.stopped_callback()
            except:
                debug_echo(self, traceback.format_exc())

    def _create_listening_thread(self, connection, last_accepted):
        self.stored_connections.append((connection, last_accepted))
        functions.create_thread(self._listen, connection, last_accepted)

    def _listen(self, conn, last_accepted):
        status_echo(self, "START")
        try:
            while self.running:
                status_echo(self, "listen")
                self.connection = conn
                _data = conn.recv()
                self.connection = None
                status_echo(self, "listen success")
                #                debug_echo(self, "received data:", _data)
                # Resend to all connections
                self.send(_data)
        except:
            self.connection = None
            status_echo(self, "listen error")
            debug_echo(self, f"Connection '{last_accepted[1]}' broken!")
            self.stored_connections.remove((conn, last_accepted))
        status_echo(self, "END")

    def send(self, message):
        for co, info in self.stored_connections:
            co.send(message)

    def close_connections(self):
        for co, info in self.stored_connections:
            co.close()


class Communicator(qt.QObject):
    """Object for passing messages between processes/applications."""

    # Signals
    received: qt.pyqtSignal = qt.pyqtSignal(object)
    # Attributes
    name = None
    client = None
    listener = None
    comm_thread = None

    def self_destruct(self) -> None:
        """"""
        self.__del__()

    def __init__(self, name):
        super().__init__()

        self.comm_thread = qt.QThread()
        self.moveToThread(self.comm_thread)
        # Connect the startup function of communicator
        self.comm_thread.started.connect(
            functools.partial(self.initialize, name)
        )
        # Start the process
        self.comm_thread.start()

    def __del__(self):
        self.comm_thread.exit()
        if self.client:
            self.client.self_destruct()
        if self.listener:
            self.listener.self_destruct()
        del self.client
        del self.listener

    def initialize(self, name):
        self.name = name
        self.client = CommClient(self.name, self.receive)
        self.listener = CommListener(self.name, self.listener_stopped)

    def listener_stopped(self):
        self.listener = CommListener(self.name, self.listener_stopped)

    def receive(self, message):
        self.received.emit(message)

    def send_to_server(self, message):
        self.client.send((self.name, message))

    def multisend(self, message):
        self.listener.send((self.name, message))

    @qt.pyqtSlot(object)
    def send(self, message):
        if self.listener.running == True:
            self.multisend(message)
        else:
            self.send_to_server(message)
