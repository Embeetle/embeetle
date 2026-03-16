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

##  FILE DESCRIPTION:
##      Locking functionality for single access functions

import os
import sys
import time
import datetime
import traceback
import multiprocessing
import data

"""
File locking
"""


class FileLock:
    __locks = {}
    debug = False
    RETRY_COUNT = 10
    SLEEP_INTERVAL = 0.2
    TIME_FORMAT = "%Y.%m.%d/%H:%M:%S"
    STORE_LIMIT_SECONDS = 3

    def __init__(self, name, debug=False):
        self.name = name
        self.file = os.path.join(data.settings_directory, name)
        self.debug = debug

    def __debug_echo(self, *messages):
        if self.debug:
            object_name = self.__class__.__name__
            print(f"[{object_name}]", *messages)

    def acquire(self):
        self.__debug_echo(f"Acquiring lock: '{self.name}'")
        for i in range(self.RETRY_COUNT):
            if not os.path.isfile(self.file):
                break
            else:
                # Check time inside file
                try:
                    self.__debug_echo(f"Reading lock time: '{self.name}'")
                    with open(self.file, "r", encoding="utf-8") as f:
                        content = f.read()
                        f.close()
                    stored = datetime.datetime.strptime(
                        content, self.TIME_FORMAT
                    )
                    now = datetime.datetime.now()
                    delta = now - stored
                    if delta.seconds > self.STORE_LIMIT_SECONDS:
                        os.remove(self.file)
                        time.sleep(self.SLEEP_INTERVAL)
                        break
                except Exception as ex:
                    self.__debug_echo(str(ex))
                    self.__debug_echo(
                        f"Error while trying to read date/time from lock file '{self.name}'!"
                    )
            time.sleep(self.SLEEP_INTERVAL)
        else:
            # Override - delete lock and recreate it
            self.__debug_echo(f"Override activated: '{self.name}'!")
            os.remove(self.file)
            time.sleep(self.SLEEP_INTERVAL)

        # Create the lock file
        with open(self.file, "w+", encoding="utf-8") as f:
            now = datetime.datetime.now().strftime(self.TIME_FORMAT)
            f.write(f"Locked at: {now}")
            f.close()

        FileLock.__locks[self.name] = now
        self.__debug_echo(f"Acquired lock: '{self.name}'")

    def release(self):
        self.__debug_echo(f"Releasing lock: '{self.name}'")
        try:
            os.remove(self.file)
        except Exception as ex:
            self.__debug_echo(str(ex))
            self.__debug_echo(f"Error while releasing lock '{self.name}'!")

        FileLock.__locks.pop(self.name, None)
        self.__debug_echo(f"Released lock: '{self.name}'")


def file_lock(lock_name):
    """Decorator for locking a function/method with a file lock."""

    def wrapper_func(func):
        def inner_func(*args, **kwargs):
            lock = FileLock(lock_name, debug=False)
            lock.acquire()
            try:
                result = func(*args, **kwargs)
                lock.release()
                return result
            except Exception as ex:
                lock.release()
                raise ex

        return inner_func

    return wrapper_func


"""
Function/method/... locking
"""

# Global lock dictionary
__locks = {}


def init(lock_dict):
    global __locks
    __locks = lock_dict


def create_lock():
    return multiprocessing.Lock()


def get_locks():
    return __locks


def get_lock(name):
    return __locks[name]


## Multiprocess lock - decorator
def inter_process_lock(lock_name):
    DEBUG = False

    def wrapper_func(func):
        def inner_func(*args, **kwargs):
            lock = get_lock(lock_name)
            if DEBUG:
                print("aquiring:", lock_name)
            lock.acquire()
            if DEBUG:
                print("locked:", lock_name)
            try:
                result = func(*args, **kwargs)
                lock.release()
                if DEBUG:
                    print("released:", lock_name)
                return result
            except Exception as ex:
                lock.release()
                if DEBUG:
                    print("released:", lock_name)
                raise ex

        return inner_func

    return wrapper_func


## Multiprocess lock with a cancel option
def cancelling_inter_process_lock(lock_name, cancel=False):
    DEBUG = False

    def wrapper_func(func):
        def inner_func(*args, **kwargs):
            lock = get_lock(lock_name)
            if cancel:
                if DEBUG:
                    print("aquiring:", lock_name)
                if lock.acquire(False):
                    if DEBUG:
                        print("locked:", lock_name)
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        lock.release()
                        if DEBUG:
                            print("released:", lock_name)
                else:
                    if DEBUG:
                        print("released:", lock_name)
                    return None
            else:
                if DEBUG:
                    print("aquiring:", lock_name)
                lock.acquire()
                if DEBUG:
                    print("locked:", lock_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    lock.release()
                    if DEBUG:
                        print("released:", lock_name)

        return inner_func

    return wrapper_func


class Locker:
    DEBUG = False

    def __init__(self, lock_name, skip=False, custom_name=""):
        self.__name = lock_name
        self.__lock = get_lock(lock_name)
        self.__skip = skip
        self.__custom_name = custom_name

    def __enter__(self):
        if self.DEBUG:
            if not self.__skip:
                print("Acquiring lock:", self.__name, self.__custom_name)
            else:
                print(
                    "Skipping acquiring lock:", self.__name, self.__custom_name
                )
        if not self.__skip:
            return self.__lock.acquire()

    def __exit__(self, *args):
        if self.DEBUG:
            if not self.__skip:
                print("Releasing lock:", self.__name, self.__custom_name)
            else:
                print(
                    "Skipping releasing lock:", self.__name, self.__custom_name
                )
        if not self.__skip:
            self.__lock.release()
