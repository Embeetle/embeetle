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
import sys
import time
import queue
import selectors
import threading
import subprocess
import multiprocessing


class StandardConsole:
    """Basic console object for redirecting input/output."""

    running = False
    in_queue = None
    out_queue = None
    exit_queue = None
    process = None

    def __init__(self):
        super().__init__()
        self.running = True
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
        self.exit_queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=self.process_loop,
        )
        self.process.daemon = True
        self.process.start()

    def send_command(self, command):
        self.in_queue.put(command)

    def std_loop(self, sub_process):
        while self.running:
            retcode = sub_process.poll()

            available = len(sub_process.stdout.peek())
            if available > 0:
                byte_text = sub_process.stdout.read1(available)
                encoded_text = byte_text.decode("utf-8", "replace")
                self.out_queue.put(encoded_text)

            if retcode is not None:
                self.exit_queue.put("process-end")
                break

    def process_loop(self):
        try:
            sub_process = subprocess.Popen(
                #                [ "gdb" ],
                ["cmd.exe"],
                #                [ "powershell.exe" ],
                bufsize=10,
                shell=False,
                cwd=None,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # subprocess.PIPE | subprocess.STDOUT
            )

            def send_command(command):
                sub_process.stdin.write(
                    bytes(f"{command}\r\n", encoding="utf-8")
                )
                sub_process.stdin.flush()

            # Testing
            #            send_command("dir")
            #            send_command("cmake")
            #            send_command("cd ..")

            t = threading.Thread(
                target=self.std_loop,
                args=[sub_process],
                daemon=True,
            )
            t.start()

            while self.running:
                try:
                    line = self.in_queue.get_nowait()
                    send_command(line)
                except queue.Empty:
                    time.sleep(0.01)

        except Exception as E:
            print("    Error: cannot run the command: %s" % E)

        print("[StandardConsole] Stopped.")

    def stop(self):
        self.running = False
