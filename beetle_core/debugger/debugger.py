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

import os
import os_checker
import enum
import traceback
import pygdbmi
import pygdbmi.gdbcontroller
import qt
import data
import functions
import debugger.openocdworker


class DebuggerState(enum.Enum):
    Disconnected = enum.auto()
    Connected = enum.auto()


class Debugger(qt.QObject):
    # Constants
    COMMAND_TIMEOUT = 2.0
    EXTRA_COMMAND_TIMEOUT = 0.1
    EXECUTION_RETRY_COUNT = 1
    TOKENS = {
        "symbol-value": 0,
        "general-register-names": 1,
        "general-register-values": 2,
        "raw-memory": 3,
        "stack-list": 5,
        "stack-variables": 6,
        "variable-object-create": 7,
        "variable-object-delete": 8,
        "variable-object-delete-all": 9,
        "variable-object-update": 10,
    }

    # Signals
    openocd_started = qt.pyqtSignal()
    openocd_stdout_received = qt.pyqtSignal(str)
    openocd_telnet_received = qt.pyqtSignal(str)
    openocd_terminate = qt.pyqtSignal()
    data_received_signal = qt.pyqtSignal(object)
    error_response_signal = qt.pyqtSignal(str)

    # Private class variables
    __state = DebuggerState.Disconnected
    __openocd_worker = None
    __openocd_thread = None

    # Class variables
    _parent = True
    show_messages = True
    gdbmi = None
    openocd_path = None
    openocd_probe_path = None
    openocd_chip_path = None

    def __init__(
        self,
        parent,
        gdb_path,
        openocd_path,
        openocd_probe_path,
        openocd_chip_path,
        command_completed_signal,
    ):
        super().__init__(parent)
        self._parent = parent
        if os_checker.is_os("windows"):
            path = os.environ.get("PATH")
            if path:
                path = "{}{}{}".format(path, os.pathsep, data.sys_lib)
            else:
                path = data.sys_lib
            custom_environment = {**os.environ, "PATH": path}
        else:
            ld_path = os.environ.get("LD_LIBRARY_PATH")
            if ld_path:
                ld_path = "{}{}{}".format(ld_path, os.pathsep, data.sys_lib)
            else:
                ld_path = data.sys_lib
            custom_environment = {**os.environ, "LD_LIBRARY_PATH": ld_path}
        self.gdbmi = pygdbmi.gdbcontroller.GdbController(
            command=[gdb_path, "--interpreter=mi2"],
            custom_environment=custom_environment,
        )
        self.gdbmi.data_received_signal.connect(self.__check_response)
        self.openocd_path = openocd_path
        self.openocd_probe_path = openocd_probe_path
        self.openocd_chip_path = openocd_chip_path
        self.command_completed_signal = command_completed_signal

    def echo(self, *messages):
        if self.show_messages:
            class_name = self.__class__.__name__
            print(f"[{class_name}]", *messages)

    def get_state(self):
        return self.__state

    def set_state(self, new_state):
        self.__state = new_state
        self.echo(f"State changed to: {new_state.name}")

    def set_state_connected(self):
        self.set_state(DebuggerState.Connected)

    def set_state_disconnected(self):
        self.set_state(DebuggerState.Disconnected)

    def __check_response(self, response):
        """Parsed Output Format.

        Each parsed gdb response consists of a list of dictionaries.
        Each dictionary has keys message, payload, token, and type.

        message:
            contains a textual message from gdb, which is not always present. When missing, this is None.

        payload:
            contains the content of gdb's output, which can contain any of the following: dictionary, list, string.
            This too is not always present, and can be None depending on the response.

        token:
            If an input command was prefixed with a (optional) token then the corresponding output
            for that command will also be prefixed by that same token.
            This field is only present for pygdbmi output types nofity and result. When missing, this is None.

        The type is defined based on gdb's various mi output record types, and can be:
            result - the result of a gdb command, such as done, running, error, etc.
            notify - additional async changes that have occurred, such as breakpoint modified
            console - textual responses to cli commands
            log - debugging messages from gdb's internals
            output - output from target
            target - output from remote target
            done - when gdb has finished its output
        """
        for item in response:
            message = item["message"]
            if message == "error":
                payload = item["payload"]
                msg = payload["msg"]
                self.error_response_signal.emit(
                    f"[{self.__class__.__name__}] {msg}"
                )
                return
        self.data_received_signal.emit(response)

    """
    OpenOCD
    """

    def openocd_start(self):
        self.__openocd_worker = debugger.openocdworker.OpenOCDWorker(
            self.openocd_path,
            self.openocd_probe_path,
            self.openocd_chip_path,
        )
        self.__openocd_worker.started.connect(self.openocd_started)
        self.__openocd_worker.stdout_received.connect(
            self.__openocd_stdout_received
        )
        self.__openocd_worker.telnet_received.connect(
            self.__openocd_telnet_received
        )
        self.openocd_terminate.connect(self.__openocd_worker.shutdown)
        self.__openocd_thread = qt.QThread(self)
        self.__openocd_worker.moveToThread(self.__openocd_thread)
        self.__openocd_thread.started.connect(self.__openocd_worker.start)
        self.__openocd_worker.stopped.connect(self.__openocd_thread.quit)
        self.__openocd_thread.finished.connect(
            self.__openocd_thread.deleteLater
        )
        self.__openocd_thread.finished.connect(self.__openocd_worker.shutdown)
        self.__openocd_thread.start()

    @qt.pyqtSlot()
    def __openocd_started(self):
        self.openocd_started.emit()

    @qt.pyqtSlot(str)
    def __openocd_stdout_received(self, str):
        self.openocd_stdout_received.emit(str)

    @qt.pyqtSlot(str)
    def __openocd_telnet_received(self, str):
        self.openocd_telnet_received.emit(str)

    def openocd_shutdown(self):
        if self.__openocd_worker is not None:
            self.__openocd_worker.shutdown()
        if self.__openocd_thread is not None and not qt.sip.isdeleted(
            self.__openocd_thread
        ):
            self.__openocd_thread.quit()
            self.__openocd_thread.wait()

    def openocd_send_command(self, command):
        self.__openocd_worker.send_command(command)

    def openocd_halt(self):
        self.openocd_send_command("halt")

    def openocd_reset_halt(self):
        self.openocd_send_command("reset halt")
        #        self.openocd_send_command("reset init") # !!Causes the error handler to fire on STM boards!!
        qt.QTimer.singleShot(0, self.init)

    def openocd_monitor_halt(self):
        self.openocd_send_command("monitor halt")

    """
    GDB
    """

    def execute(self, command):
        functions.performance_timer_start()

        if isinstance(command, list) or isinstance(command, tuple):
            commands = command
        else:
            commands = [
                command,
            ]
        success = False
        safety_counter = 0
        while not success:
            try:
                response = self.gdbmi.write(
                    #                    commands, timeout_sec=self.COMMAND_TIMEOUT
                    commands
                )
                success = True
            except pygdbmi.constants.GdbTimeoutError as ex:
                safety_counter += 1
                #                print("RETRY")
                if safety_counter > self.EXECUTION_RETRY_COUNT:
                    raise ex
            except Exception as ex:
                traceback.print_exc()
                raise ex

        functions.performance_timer_show()

        return response

    """
    High-level API
    """

    def init(self, target=None):
        response = self.connect(target)
        return response

    def self_destruct(self):
        self.openocd_shutdown()
        self.gdbmi.exit()

    def connect(self, target=None):
        if target is None:
            #            target = "remote localhost:3333"
            target = "extended-remote localhost:3333"
        self.execute(f"-target-select {target}")

    def load_symbol_file(self, file_path):
        self.execute(f'-file-symbol-file "{file_path}"')

    def continue_execution(self):
        self.execute("-exec-continue")

    def stop_execution(self):
        self.execute("-exec-interrupt")

    def execute_user_command(self, user_command):
        if user_command.startswith("-"):
            self.execute(user_command)
        else:
            self.execute(f'-interpreter-exec console "{user_command}"')

    ## Stack
    def stack_frame(self):
        self.execute("-stack-info-frame")

    def stack_depth(self):
        self.execute("-stack-info-depth")

    def stack_frame_list(self):
        token = self.TOKENS["stack-list"]
        self.execute(f"{token}-stack-list-frames")

    def stack_variable_list(self):
        token = self.TOKENS["stack-variables"]
        self.execute(f"{token}-stack-list-variables --all-values")

    ## Stepping
    def step(self):
        self.execute("-exec-step")

    def step_instruction(self):
        self.execute("-exec-step-instruction")

    def next(self):
        self.execute("-exec-next")

    def next_instruction(self):
        self.execute("-exec-next-instruction")

    def finish(self):
        self.execute("-exec-finish")

    ## Breakpoints
    def breakpoint_insert(self, filename, line_number):
        self.execute(f"-break-insert {filename}:{line_number}")

    def breakpoint_delete(self, number):
        if isinstance(number, list) or isinstance(number, tuple):
            numbers_string = " ".join((str(x) for x in number))
            self.execute(f"-break-delete {numbers_string}")
        else:
            self.execute(f"-break-delete {number}")

    def delete_all_watch_and_break_points(self):
        self.execute("-break-delete")

    def breakpoint_show_list(self):
        self.execute("-break-list")

    ## Watchpoints
    def watchpoint_insert(self, symbol_name):
        self.execute(f"-break-watch {symbol_name}")

    ## Stack
    def get_stack_frames(self, *switches):
        if len(switches) > 0:
            command = f"-stack-list-frames {' '.join(switches)}"
            response = self.execute(command)
        else:
            response = self.execute("-stack-list-frames")
        for item in response:
            if isinstance(item, dict) and "payload" in item.keys():
                payload = item["payload"]
                if isinstance(payload, dict) and "stack" in payload.keys():
                    stack = payload["stack"]
                    return stack
        else:
            raise Exception(
                f"[{self.__class__.__name__}] "
                "Stack frame information not found!"
            )

    def get_stack_variables(self, thread=1, frame=0):
        response = self.execute(
            "-stack-list-variables "
            + f"--thread {thread} "
            + f"--frame {frame} "
            + "--all-values"
        )
        for r in response:
            for k, v in r.items():
                if k == "message" and v == "done":
                    payload = r["payload"]
                    if "variables" in payload.keys():
                        stack_locals = payload["variables"]
                        return stack_locals
        else:
            raise Exception(
                f"[{self.__class__.__name__}] " "Variables not found!"
            )

    ## Threads
    def get_thread_information(self, thread_id=None):
        if thread_id:
            response = self.execute(f"-thread-info {thread_id}")
        else:
            response = self.execute("-thread-info")
        for r in response:
            for k, v in r.items():
                if k == "message" and v == "done":
                    payload = r["payload"]
                    stack_locals = []
                    if "threads" in payload.keys():
                        thread_information = payload
                        return thread_information
        else:
            raise Exception(
                f"[{self.__class__.__name__}] " "No thread information!"
            )

    ## Registers
    def get_register_names(self, *switches):
        if len(switches) > 0:
            command = f"-data-list-register-names {' '.join(switches)}"
            response = self.execute(command)
        else:
            response = self.execute("-data-list-register-names")
        for item in response:
            if isinstance(item, dict) and "payload" in item.keys():
                payload = item["payload"]
                if "register-names" in payload:
                    register_names = payload["register-names"]
                    result = {}
                    for i in range(len(register_names)):
                        result[i] = register_names[i]
                    return result
        else:
            raise Exception(
                f"[{self.__class__.__name__}] "
                "Register name information not found!"
            )

    def get_register_values(self, _format="x"):
        """
        Formats:
            x - Hexadecimal
            o - Octal
            t - Binary
            d - Decimal
            r - Raw
            N - Natural
        """
        token_0 = self.TOKENS["general-register-names"]
        token_1 = self.TOKENS["general-register-values"]
        self.execute(
            [
                f"{token_0}-data-list-register-names",
                f"{token_1}-data-list-register-values --skip-unavailable {_format}",
            ]
        )

    ## Functions
    def get_function_list(self):
        response = self.execute(f'-interpreter-exec console "info functions"')
        results = {"files": {}}
        file_flag = False
        non_debug_flag = False
        file_name = None
        for r in response:
            payload = r["payload"]
            if payload is not None:
                payload = (
                    payload.replace("\\n", "")
                    .replace("\\r", "")
                    .replace("\\t", "")
                    .strip()
                )
                print("payload", f"'{payload}'")
                if payload == "File":
                    file_flag = True
                elif payload == "All defined functions:":
                    file_flag = False
                    file_name = None
                elif payload == "Non-debugging symbols:":
                    non_debug_flag = True
                    results["non-debug-symbols"] = []
                elif file_flag:
                    file_flag = False
                    file_name = payload
                    results["files"][file_name] = []
                elif non_debug_flag:
                    results["non-debug-symbols"].append(payload)
                else:
                    line, name = payload.split(":")
                    results["files"][file_name].append(
                        {
                            "function": name,
                            "line-number": line,
                        }
                    )
        return results

    ## Frame
    def get_current_frame(self):
        #        response = self.execute("frame")
        response = self.execute("-stack-info-frame")
        self.__check_response(response)
        result = None
        #        pprint(response)
        for r in response:
            if r["message"] == "done" and r["type"] == "result":
                result = r["payload"]["frame"]
                break
        return result

    ## Memory
    def get_memory(self, region_name, address, count):
        """
        Use 'data.current_project.get_chip().get_complete_memory_structure()'
        to get chip's entire memory structure. Example:

        {
            'FLASH': {
                'type': 'MEMTYPE.FLASH',
                'rights': 'rx',
                'origin': '0x8000000',
                'length': '0x10000',
                'sections': {
                    '.vectors': {
                        'usage': '0xcc'
                    },
                    '.text': {
                        'usage': '0x45c'
                    },
                    '.rodata': {
                        'usage': '0x0'
                    },
                    '.ARM.extab': {'usage': '0x0'},
                    '.ARM': {'usage': '0x0'},
                    '.ARM.attributes': {'usage': '0x2c'},
                    '.preinit_array': {'usage': '0x0'},
                    '.init_array': {'usage': '0x4'},
                    '.fini_array': {'usage': '0x4'},
                    '.data': {'usage': '0x4'}
                }
            },
            'RAM': {
                'type': 'MEMTYPE.RAM',
                'rights': 'xrw',
                'origin': '0x20000000',
                'length': '0x2000',
                'sections': {
                    '.data': {
                        'usage': '0x4'
                    },
                    '.bss': {
                        'usage': '0x20'
                    }
                }
            }
        }
        """
        token = self.TOKENS[region_name]
        command = "{}-data-read-memory-bytes {} {}".format(
            token,
            address,
            count,
        )
        self.execute(command)

    ## Symbols
    def get_global_variables(self, source_file):
        #        command = f"-symbol-list-lines {source_file}"
        #        command = '-interpreter-exec console "info functions"'
        command = '-interpreter-exec console "info functions"'
        response = self.execute(command)
        self.__check_response(response)
        payload = response[0]["payload"]
        return payload

    ## Runtime
    def symbol_value(self, name: str) -> None:
        token = self.TOKENS["symbol-value"]
        self.execute(f"{token}-data-evaluate-expression {name}")

    ## Variable objects
    def variable_object_create(self, name: str) -> None:
        token = self.TOKENS["variable-object-create"]
        expression = name
        if name.startswith("*"):
            expression = name
            name = name[1:] + "$"
        self.execute(f"{token}-var-create {name} * {expression}")

    def variable_object_delete(self, name: str) -> None:
        token = self.TOKENS["variable-object-delete"]
        self.execute(f"{token}-var-delete {name}")

    def variable_object_update(self) -> None:
        token = self.TOKENS["variable-object-update"]
        self.execute(f"{token}-var-update --all-values *")
