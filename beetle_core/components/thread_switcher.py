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
import qt, threading, functools, gc, random
from various.kristofstuff import *

thread_dict: Dict[str, qt.QThread] = {}
switcher_list: List = []
switcher_cleaner_started = False


class Switcher(qt.QObject):
    def __init__(self) -> None:
        super().__init__()
        self.switch_mutex = threading.Lock()
        self.keep_alive_mutex = threading.Lock()
        return

    def get_switch_mutex(self) -> threading.Lock:
        return self.switch_mutex

    @qt.pyqtSlot(object, object, object, object)
    def switch_slot(
        self,
        qthread: qt.QThread,
        callback: Optional[Callable],
        callbackArg: Any,
        switch_finished: Callable,
    ) -> None:
        """Slot used for switching to qthread."""
        assert qt.QThread.currentThread() is qthread
        if get_name(qthread) == "main":
            assert threading.current_thread() is threading.main_thread()
        callback(callbackArg)
        qt.QTimer.singleShot(
            random.randint(1, 5), functools.partial(switch_finished, self)
        )
        return

    @qt.pyqtSlot(object, object, object)
    def switch_slot_new(
        self,
        qthread: qt.QThread,
        callback: Optional[Callable],
        args: Union[object, Tuple],
    ) -> None:
        """Slot used for switching to qthread."""
        assert qt.QThread.currentThread() is qthread
        if get_name(qthread) == "main":
            assert threading.current_thread() is threading.main_thread()
        if isinstance(args, tuple):
            callback(*args)
        else:
            callback(args)
        self.keep_alive_mutex.release()
        return

    @qt.pyqtSlot(object, object, object, object)
    def switch_slot_modern(
        self, qthread: qt.QThread, callback: Optional[Callable], args, kwargs
    ) -> None:
        """Slot used for switching to qthread."""
        assert qt.QThread.currentThread() is qthread
        if get_name(qthread) == "main":
            assert threading.current_thread() is threading.main_thread()
        callback(*args, **kwargs)
        self.keep_alive_mutex.release()
        return


def start_switcher_cleaner(*args) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    global switcher_cleaner_started
    if switcher_cleaner_started:
        return
    qt.QTimer.singleShot(1000, clean_switchers)
    return


def clean_switchers(*args) -> None:
    """"""
    assert threading.current_thread() is threading.main_thread()
    global switcher_list
    for switcher in switcher_list:
        if switcher.keep_alive_mutex.locked():
            continue
        if qt.sip.isdeleted(switcher):
            pass
        else:
            switcher.deleteLater()
        switcher_list.remove(switcher)
    qt.QTimer.singleShot(random.randint(1000, 5000), clean_switchers)
    return


def register_thread(name: str, qthread: qt.QThread) -> None:
    """
    :param name:        Given name.
    :param qthread:     QThread()-instance.
    """
    global thread_dict
    assert isinstance(qthread, qt.QThread)
    thread_dict[name] = qthread
    # print("QThread register: {0!s} = {1!s}".format(name, qthread))
    return


def remove_thread(qthread: qt.QThread) -> None:
    global thread_dict
    name = None
    for e in thread_dict.items():
        if e[1] is qthread:
            name = e[0]
            break
    # print("QThread remove: {0!s} = {1!s}".format(name, qthread))
    del thread_dict[name]
    return


def get_qthread(name: str) -> qt.QThread:
    """"""
    global thread_dict
    return thread_dict[name]


def get_name(qthread: qt.QThread) -> str:
    """"""
    global thread_dict
    for e in thread_dict.items():
        if e[1] is qthread:
            return e[0]
    raise RuntimeError()


def switch_thread(
    qthread: qt.QThread,
    callback: Optional[Callable],
    callbackArg: Any,
    notifycaller: Optional[Callable],
) -> None:
    """
    :param qthread:         The QThread() you want to switch to.

    :param callback:        Runs in qthread.

    :param callbackArg:     Argument to be inserted in the callback.

    :param notifycaller:    Runs in original thread.
                            Callback (without arguments) to notify the caller
                            that the switch has been made.

    """
    global thread_dict
    origthread = qt.QThread.currentThread()
    if origthread is qthread:
        callback(callbackArg)
        notifycaller() if notifycaller is not None else nop()
        return
    switcher = Switcher()
    switcher.moveToThread(qthread)

    def start():
        "[origthread]"
        assert qt.QThread.currentThread() is origthread
        if not switcher.get_switch_mutex().acquire(blocking=False):
            raise RuntimeError()
        qt.QTimer.singleShot(
            1,
            functools.partial(
                switcher.switch_slot,
                qthread,
                callback,
                callbackArg,
                switch_finished,
            ),
        )
        finished()
        return

    def switch_finished(_switcher):
        "[qthread]"
        if qt.sip.isdeleted(_switcher):
            return
        assert qt.QThread.currentThread() is qthread
        assert qthread is not origthread
        _switcher.get_switch_mutex().release()
        return

    def finished():
        "[origthread]"
        if qt.sip.isdeleted(switcher):
            return
        assert qt.QThread.currentThread() is origthread
        if switcher.get_switch_mutex().locked():
            qt.QTimer.singleShot(random.randint(5, 10), finished)
            return
        switcher.deleteLater()
        notifycaller() if notifycaller is not None else nop()
        return

    start()
    return


def switch_thread_new(
    qthread: qt.QThread,
    callback: Optional[Callable],
    args: Optional[Union[object, Tuple]] = None,
) -> None:
    """
    :param qthread:         The QThread() you want to switch to.

    :param callback:        Runs in qthread.

    :param args:            Argument to be inserted in the callback. If tuple,
                            it gets unraveled. If ordinary object, it's just
                            passed to the callback unchanged.

    """
    global thread_dict
    origthread = qt.QThread.currentThread()
    # $ Check if origthread == qthread
    if origthread is qthread:
        if isinstance(args, tuple):
            callback(*args)
        else:
            callback(args)
        return
    # $ Create and store switcher
    switcher = Switcher()
    switcher.moveToThread(qthread)
    switcher.keep_alive_mutex.acquire()
    global switcher_list
    switcher_list.append(switcher)
    # $ Perform switch
    qt.QTimer.singleShot(
        1,
        functools.partial(
            switcher.switch_slot_new,
            qthread,
            callback,
            args,
        ),
    )
    return


def switch_thread_modern(
    qthread: qt.QThread,
    callback: Optional[Callable],
    *args,
    **kwargs,
) -> None:
    """
    :param qthread:         The QThread() you want to switch to.
    :param callback:        Runs in qthread.
    """
    global thread_dict
    origthread = qt.QThread.currentThread()
    # $ Check if origthread == qthread
    if origthread is qthread:
        callback(*args, **kwargs)
        return
    # $ Create and store switcher
    switcher = Switcher()
    switcher.moveToThread(qthread)
    switcher.keep_alive_mutex.acquire()
    global switcher_list
    switcher_list.append(switcher)
    # $ Perform switch
    qt.QTimer.singleShot(
        1,
        functools.partial(
            switcher.switch_slot_modern,
            qthread,
            callback,
            args,
            kwargs,
        ),
    )
    return


def switch_thread_packed(
    qthread: qt.QThread, callback: Optional[Callable], args, kwargs
) -> None:
    """Pass the args and kwargs as Tuple and Dict respectively."""
    global thread_dict
    origthread = qt.QThread.currentThread()
    # $ Check if origthread == qthread
    if origthread is qthread:
        callback(*args, **kwargs)
        return
    # $ Create and store switcher
    switcher = Switcher()
    switcher.moveToThread(qthread)
    switcher.keep_alive_mutex.acquire()
    global switcher_list
    switcher_list.append(switcher)
    # $ Perform switch
    qt.QTimer.singleShot(
        1,
        functools.partial(
            switcher.switch_slot_modern,
            qthread,
            callback,
            args,
            kwargs,
        ),
    )
    return


def get_new_mortal_thread_and_worker(
    self, WorkerClass
) -> Tuple[qt.QThread, qt.QObject]:
    """Get a 'QThread()' and 'MortalWorker()' object."""
    assert threading.current_thread() is threading.main_thread()
    assert hasattr(self, "__mortal_worker_list__")
    assert hasattr(self, "__mortal_thread_list__")
    assert hasattr(self, "__mortal_i__")
    mortal_thread: qt.QThread = qt.QThread()
    mortal_worker: qt.QObject = WorkerClass()

    @qt.pyqtSlot()
    def thread_started(*args):
        assert threading.current_thread() is threading.main_thread()
        return

    @qt.pyqtSlot()
    def worker_finished(*args):
        nonlocal mortal_worker
        assert threading.current_thread() is threading.main_thread()
        try:
            self.__mortal_worker_list__.remove(mortal_worker)
        except Exception as e:
            print("Try again to remove mortal_worker from list...")
            qt.QTimer.singleShot(10, worker_finished)
            return
        if qt.sip.isdeleted(mortal_worker):
            return
        mortal_worker.deleteLater()
        mortal_worker = None
        mortal_thread.quit()
        return

    @qt.pyqtSlot()
    def thread_finished(*args):
        assert threading.current_thread() is threading.main_thread()
        nonlocal mortal_thread
        assert mortal_thread.isFinished()
        assert not mortal_thread.isRunning()
        remove_thread(qthread=mortal_thread)
        try:
            self.__mortal_thread_list__.remove(mortal_thread)
        except Exception as e:
            print("Try again to remove mortal_thread from list...")
            qt.QTimer.singleShot(10, thread_finished)
            return
        if qt.sip.isdeleted(mortal_thread):
            return
        mortal_thread.deleteLater()
        mortal_thread = None
        gc.collect()
        return

    register_thread(
        name=f"{WorkerClass.__name__}_mortal_{self.__mortal_i__}",
        qthread=mortal_thread,
    )
    self.__mortal_i__ += 1
    mortal_worker.moveToThread(mortal_thread)
    mortal_thread.started.connect(thread_started)  # type: ignore
    mortal_worker.die_signal.connect(worker_finished)  # type: ignore
    mortal_thread.finished.connect(thread_finished)  # type: ignore
    # Keep them alive for a while
    self.__mortal_thread_list__.append(mortal_thread)
    self.__mortal_worker_list__.append(mortal_worker)
    # Start thread
    mortal_thread.start()
    return mortal_thread, mortal_worker


class RunOutsideMain:
    __obj_dict__ = {}

    def __init__(self, method, name="not_known") -> None:
        """
        See OPTION 3 at
        https://stackoverflow.com/questions/63416226/how-to-access-variables-from-a-class-decorator-from-within-the-method-its-appli

        WARNING: Objects from __obj_dict__ never
                 get deleted => fix memory leak
        """
        functools.update_wrapper(self, method)
        self.method = method
        self.method_name = name
        self.origthread: Optional[qt.QThread] = None
        self.nonmainthread: Optional[qt.QThread] = None
        self._args_: Optional[Tuple[Any, ...]] = None
        self._kwargs_: Optional[Dict[str, Any]] = None
        self.mutex = threading.Lock()
        return

    def __get__(self, obj, objtype) -> object:
        """
        self:    The RunOutsideMain()-instance that serves as the
                 wrapper factory.
        obj:     The obj whose method we want to wrap (eg. Foobar())
        objtype: The class of the said object (eg. Foobar)
        """
        if obj in RunOutsideMain.__obj_dict__.keys():
            # Return existing RunOutsideMain() instance for
            # the given object-method_name combination, and make
            # sure it holds a bound method.
            if self.method_name in RunOutsideMain.__obj_dict__[obj].keys():
                m = RunOutsideMain.__obj_dict__[obj][self.method_name]
                return m
            else:
                # Create a new RunOutsideMain() instance WITH a bound
                # method, and store it in the dictionary.
                m = type(self)(
                    self.method.__get__(obj, objtype), self.method_name
                )
                RunOutsideMain.__obj_dict__[obj][self.method_name] = m
                return m

        # Create a new RunOutsideMain() instance WITH a bound
        # method, and store it in the dictionary.
        m = type(self)(self.method.__get__(obj, objtype), self.method_name)
        RunOutsideMain.__obj_dict__[obj] = {}
        RunOutsideMain.__obj_dict__[obj][self.method_name] = m
        return m

    def __call__(self, *args, **kwargs) -> None:
        """The __call__ method of an object only comes into play when the object
        is invoked like a function."""

        # $ Grab mutex.
        # Avoid this invocation from modifying anything before it
        # grabbed the mutex!
        def _reenter_(_origthread_, _args, _kwargs):
            switch_thread_packed(
                _origthread_,
                self.__call__,
                _args,
                _kwargs,
            )
            return

        if not self.mutex.acquire(blocking=False):
            print(
                f"Wrapper for method {self.method.__qualname__} "
                f"cannot grab mutex"
            )
            qt.QTimer.singleShot(
                random.randint(100, 200),
                functools.partial(
                    _reenter_,
                    qt.QThread.currentThread(),
                    args,
                    kwargs,
                ),
            )
            return

        # $ Store args and kwargs
        self._args_ = args
        self._kwargs_ = kwargs
        # $ Check if 'origthread' is already registered
        self.origthread = qt.QThread.currentThread()
        try:
            get_name(qthread=self.origthread)
        except Exception as e:
            if threading.current_thread() is threading.main_thread():
                register_thread(
                    name="main",
                    qthread=self.origthread,
                )
            else:
                register_thread(
                    name=f"not_known_thread_{id(self.origthread)}",
                    qthread=self.origthread,
                )
        # print(f"Enter {self.method.__qualname__} from"
        #       f"thread {get_name(self.origthread)}")

        # $ Just run method if already outside main
        if threading.current_thread() is not threading.main_thread():
            self.nonmainthread = self.origthread
            self.run_method()
            return

        # $ nonmainthread setup
        self.nonmainthread = qt.QThread()
        register_thread(
            name=f"{self.method.__qualname__}_thread",
            qthread=self.nonmainthread,
        )
        self.nonmainthread.started.connect(nop)  # type: ignore
        self.nonmainthread.finished.connect(self.delete_nonmainthread)  # type: ignore
        self.nonmainthread.start()

        switch_thread_new(
            qthread=self.nonmainthread,
            callback=self.run_method,
            args=None,
        )
        return

    def run_method(self, *args) -> None:
        """Run the wrapped method in self.nonmainthread."""
        assert qt.QThread.currentThread() is self.nonmainthread
        retval = self.method(*self._args_, **self._kwargs_)
        assert retval is None
        return

    def invoke_callback_in_origthread(self, callback, *args, **kwargs) -> None:
        """Invoke the callback in self.origthread.

        If self.nonmainthread differs from the original thread, clean it up.
        """
        assert qt.QThread.currentThread() is self.nonmainthread

        def invoke_after_threadswitch(*_args_):
            assert qt.QThread.currentThread() is self.origthread
            assert self.nonmainthread is not self.origthread
            # Kill self.nonmainthread
            self.nonmainthread.quit()
            # Keep self.origthread and self.nonmainthread stored
            # until self.nonmainthread gets destroyed.
            self._args_ = None
            self._kwargs_ = None
            # Don't release the mutex yet - wait
            # for the destruction of self.nonmainthread!
            # Invoke callback
            callback(*args, **kwargs)
            return

        # $ Directly invoke the callback
        if self.nonmainthread is self.origthread:
            assert qt.QThread.currentThread() is self.origthread
            # Reset all variables, except the mutex and
            # the method
            self.origthread = None
            self.nonmainthread = None
            self._args_ = None
            self._kwargs_ = None
            # Release the mutex
            self.mutex.release()
            # Invoke callback
            callback(*args, **kwargs)
            return
        # $ Perform thread switch first
        switch_thread_modern(
            qthread=self.origthread,
            callback=invoke_after_threadswitch,
        )
        return

    def delete_nonmainthread(self) -> None:
        """Tied to the 'finished' signal from self.nonmainthread, which gets
        triggered if you invoke: self.nonmainthread.quit()

        The mutex gets released here to ensure that this self.nonmainthread
        destruction doesn't apply on a new QThread() born in a new __call__()
        invocation!
        """
        assert qt.QThread.currentThread() is self.origthread
        assert self.nonmainthread is not self.origthread
        remove_thread(self.nonmainthread)
        self.nonmainthread.deleteLater()
        self.nonmainthread = None
        self.origthread = None
        self.mutex.release()
        return

    def reenter(self, millisec=-1) -> None:
        """Reenter the wrapped method in x milliseconds."""
        assert qt.QThread.currentThread() is self.nonmainthread
        if millisec == -1:
            millisec = random.randint(100, 200)
        print(f"Reenter {self.method.__qualname__}")
        qt.QTimer.singleShot(millisec, self.run_method)
        return


def run_outside_main(name="not_known"):
    def _wrapper_(method):
        return RunOutsideMain(method, name)

    return _wrapper_
