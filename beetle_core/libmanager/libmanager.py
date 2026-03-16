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
from components.singleton import Singleton
from itertools import islice
import threading, weakref, os, sys, traceback, re, json, datetime, functools
import qt, data, functions, purefunctions, serverfunctions, gui
import components.thread_switcher as _sw_
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import project_generator.generator.project_generator as _project_generator_
import libmanager.libfilter as _json_filter_
import libmanager.libobj as _libobj_
import beetle_console.mini_console as _mini_console_
import helpdocs.help_texts as _ht_
import home_libraries.items.lib_root_item as _lib_root_item_
import home_libraries.items.lib_add_item as _lib_add_item_
import home_libraries.items.lib_refresh_item as _lib_refresh_item_
import home_libraries.items.lib_help_item as _lib_help_item_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.hardware_api as _hardware_api_
import generators_and_importers.arduino.locator as _arduino_locator_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import wizards.lib_wizard.lib_table as _lib_table_
    import wizards.lib_wizard.gen_widgets.progbar as _progbar_
from various.kristofstuff import *


class LibManager(metaclass=Singleton):
    """
    ============================================================================
    |                                 DATABASE                                 |
    ============================================================================
    After completing the 'initialize()' method, this LibManager()-instance holds
    three important dictionaries with LibObj()s:
        - self.__unfiltered_remote_libs
        - self.__unfiltered_stored_libs
        - self.__unfiltered_proj_libs

    They are merged into:
        - self.__unfiltered_merged_libs

    DATABASE PARTS
    ==============
    Each of them looks like this:
        ┌───────────────────────────────────────┐
        │  self.__unfiltered_remote_libs =      │
        │  {                                    │
        │      'AudioZero':                     │
        │      [                                │
        │          ('1.0.1', <LibObj>),         │
        │          ('1.1.1', <LibObj>),         │
        │      ],                               │
        │      'Heltec ESP32 Dev-Boards':       │
        │      [                                │
        │          ('1.1.0', <LibObj>),         │
        │          ('0.0.9', <LibObj>),         │
        │      ],                               │
        │      ...                              │
        │  }                                    │
        └───────────────────────────────────────┘

    In other words:
        * Each library name is a key in the dictionary.
        * Per library, the dictionary keeps a list-of-tuples (liblist):
             - 1st tuple item is the version
             - 2nd tuple item is the LibObj()

    Rules:
        * The remote dictionary can have several tuples per 'liblist'. That's
          because there can be several libraries with the same name, but dif-
          ferent version.

        * The stored dictionary can even go one step further: it can have se-
          veral libraries with the same name *and* same version! This happens if
          you duplicated a library over several locations.

        * The project dictionary should only have one tuple per 'liblist'. In
          other words - no duplicates in name!


    MERGED DATABASE
    ===============
    The merged database looks like this:
        ┌───────────────────────────────────────┐
        │  self.__unfiltered_merged_libs =      │
        │  {                                    │
        │      'Heltec ESP32 Dev-Boards':       │
        │      {                                │
        │          'zip_url':                   │
        │          [                            │
        │              ('0.0.8', <LibObj>),     │
        │              ('0.0.9', <LibObj>),     │
        │          ],                           │
        │          'local_abspath':             │
        │          [                            │
        │              ('0.0.8', <LibObj>),     │
        │              ('0.0.9', <LibObj>),     │
        │              ('0.0.9', <LibObj>),     │
        │          ],                           │
        │          'proj_relpath':              │
        │          [                            │
        │              ('0.0.7', <LibObj>),     │
        │              ('0.0.7', <LibObj>),     │
        │              ('0.0.9', <LibObj>),     │
        │          ],                           │
        │      },                               │
        │      ...                              │
        │  }                                    │
        │                                       │
        └───────────────────────────────────────┘
    It features an extra level of keys to indicate the 'origin' of the listed
    libraries.

    ============================================================================
    |                                 FILTERS                                  |
    ============================================================================
    For each 'unfiltered' dictionary, the LibManager() keeps a corresponding
    'filtered' dictionary - even for the merged one!
    The 'filtered' dictionaries get filled only after an explicit command. This
    command should be invoked when the filter-object is modified to ones wishes.

    When filling the 'filtered' dictionaries, no new LibObj()s will be created.
    Only references to the existing ones in the 'unfiltered' dictionaries get
    copied.

    ============================================================================
    |                           VISUAL REPRESENTATION                          |
    ============================================================================
    This LibManager()-singleton also directs the visual representation in the
    Home Windows' LIBRARIES tab. It holds several Root()-items for that purpose:
        - self._v_rootItem_dict['Communication']
        - self._v_rootItem_dict['Data Processing']
        - self._v_rootItem_dict['Data Storage']
        - ...
        - self._v_libAddRootItem

    The LIBRARIES Chassis is defined in 'home_libraries/chassis/home_libraries.py'
    and the shown Items in 'home_libraries/items/...'. Very much like the dash-
    board chassis and items.
    The dashboard items are *directed* by the project segments. In the same way,
    the home library items are *directed* by this LibManager()-singleton.
    """

    def __init__(self) -> None:
        """Create the LibManager()-singleton."""
        super().__init__()
        if data.startup_log_libmanager:
            print("[startup] libmanager.py -> LibManager.__init__()")

        # * General variables
        self.__json_filepath = _pp_.rel_to_abs(
            rootpath=data.settings_directory,
            relpath="libraries/library_index.json",
        )

        # $ Remote origins
        self.__remote_origins = [
            "https://downloads.arduino.cc/libraries/library_index.json",
        ]

        # $ Local origins
        # List all the 'libcollection' folders to be found on the user's system,
        # into the attribute self.__local_origins. For example:
        # self.__local_origins = [
        #     '<usr>/.embeetle/libraries',                                     -> 'dot_embeetle'
        #     '<usr>/Documents/Arduino/libraries',                             -> 'arduino_sketchbook'
        #                                                                      ┐
        #     '<arduino15>/cache/downloads.arduino.cc/libraries',              │
        #     '<arduino15>/packages/arduino/hardware/avr/1.8.3/libraries',     ├ 'arduino15'
        #     '<arduino15>/packages/arduino/hardware/megaavr/1.8.7/libraries', │
        #                                                                      ┘
        #     '<prog_files>/Arduino/libraries',                                ┬ 'arduino_installation'
        #     '<prog_files>/Arduino/hardware/arduino/avr/libraries',           ┘
        # ]
        # Each part of this list is obtained by invoking the function
        # 'get_potential_libcollection_folder()' with the right parameter.
        # NOTE:
        # For brevity, just in this comment:
        # '<usr>'        = 'C:/Users/Kristof'
        # '<arduino15>'  = 'C:/Users/Kristof/AppData/Local/Arduino15'
        # '<prog_files>' = 'C:/Program Files (x86)'
        arduino_installation_libcollections = (
            self.get_potential_libcollection_folder("arduino_installation")
        )
        arduino15_libcollections = self.get_potential_libcollection_folder(
            "arduino15"
        )
        if arduino_installation_libcollections is None:
            arduino_installation_libcollections = []
        if arduino15_libcollections is None:
            arduino15_libcollections = []
        self.__local_origins = [
            self.get_potential_libcollection_folder("dot_embeetle"),
            self.get_potential_libcollection_folder("arduino_sketchbook"),
            *arduino15_libcollections,
            *arduino_installation_libcollections,
        ]
        self.__remote_initialized = False
        self.__stored_initialized = False
        self.__proj_initialized = False

        # $ Database parts
        self.__unfiltered_remote_libs: Dict = {}  # 'zip_url'
        self.__filtered_remote_libs: Dict = {}
        self.__unfiltered_stored_libs: Dict = {}  # 'local_abspath'
        self.__filtered_stored_libs: Dict = {}
        self.__unfiltered_proj_libs: Dict = {}  # 'proj_relpath'

        self.__unfiltered_merged_libs: Dict = {}
        self.__filtered_merged_libs: Dict = {}
        self.__unfiltered_merged_list: List = []
        self.__filtered_merged_list: List = []

        self.__given_slice: int = 0
        self.__total_len: int = 0
        self.__json_filter = _json_filter_.Libfilter()

        # $ Reference to LibraryTable()
        self.__libtable_ref = None

        # $ Reference to LibraryProgbar()
        self.__progbar_ref = None

        # $ Mutexes
        self.__adding_rows_mutex = threading.Lock()
        self.__stop_adding_rows = False
        self.__search_dependencies_mutex = threading.Lock()
        self.__libs_already_recursed_for_dependencies = []
        self.__nav_mutex = threading.Lock()
        self.__init_mutex = threading.Lock()

        # $ Mini console
        self.__mini_console: Optional[_mini_console_.MiniConsole] = None

        # * Home Window LIBRARIES tab
        # This LibManager()-singleton also directs the visual representation in
        # the Home Windows' LIBRARIES tab. It holds several Root()-items for
        # that purpose:
        self._v_rootItem_dict: Optional[
            Dict[str, _lib_root_item_.LibCategoryRootItem]
        ] = None
        return

    def fill_libman_widg(self) -> None:
        """"""
        assert data.is_home

        # $ Toplevel category root-items
        # Instantiate the toplevel category root-items. Then add them to the
        # widget.
        self._v_rootItem_dict = {
            "Communication": _lib_root_item_.LibCategoryRootItem(
                "Communication"
            ),
            "Data Processing": _lib_root_item_.LibCategoryRootItem(
                "Data Processing"
            ),
            "Data Storage": _lib_root_item_.LibCategoryRootItem("Data Storage"),
            "Device Control": _lib_root_item_.LibCategoryRootItem(
                "Device Control"
            ),
            "Display": _lib_root_item_.LibCategoryRootItem("Display"),
            "Sensors": _lib_root_item_.LibCategoryRootItem("Sensors"),
            "Signal Input-Output": _lib_root_item_.LibCategoryRootItem(
                "Signal Input-Output"
            ),
            "Timing": _lib_root_item_.LibCategoryRootItem("Timing"),
            "Other": _lib_root_item_.LibCategoryRootItem("Other"),
        }
        for cat, rootitem in self._v_rootItem_dict.items():
            # Add the category root-items to the widget. This widget gets
            # created *before* this LibManager()-instance.
            data.libman_widg.add_root(rootitem)
            # For each category, provide an 'Add library' sub-item.
            # As there are none yet to be killed (replaced), this
            # happens instantaneously.
            self.replace_add_item(
                category=rootitem.get_name(),
                callback=None,
                callbackArg=None,
            )
            continue

        # $ Toplevel 'Add library' root-item
        toplvl_additem = _lib_add_item_.LibAddRootItem()
        downloaditem = _lib_add_item_.DownloadItem(
            rootdir=toplvl_additem,
            parent=toplvl_additem,
            category=None,
        )
        zipitem = _lib_add_item_.ZipItem(
            rootdir=toplvl_additem,
            parent=toplvl_additem,
            category=None,
        )
        toplvl_additem.add_child(
            child=downloaditem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        toplvl_additem.add_child(
            child=zipitem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        data.libman_widg.add_root(toplvl_additem)

        # $ Toplevel 'Refresh' root-item
        toplvl_refreshitem = _lib_refresh_item_.LibRefreshRootItem()
        data.libman_widg.add_root(toplvl_refreshitem)

        # $ Toplevel 'Help' root-item
        toplvl_helpitem = _lib_help_item_.LibHelpRootItem()
        data.libman_widg.add_root(toplvl_helpitem)
        return

    def lock_adding_rows_mutex(self) -> bool:
        if not self.__adding_rows_mutex.acquire(blocking=False):
            return False
        return True

    def release_adding_rows_mutex(self) -> None:
        self.__stop_adding_rows = False
        self.__adding_rows_mutex.release()
        return

    def stop_adding_rows(self) -> None:
        self.__stop_adding_rows = True

    def get_json_filter(self) -> _json_filter_.Libfilter:
        return self.__json_filter

    def link(
        self,
        libtable: _lib_table_.LibTable,
        progbar: _progbar_.TableProgbar,
    ) -> None:
        """Link this LibManager() instance to:

        - LibraryTable() to present all the data
        - LibraryProgbar()
        """
        # $ Progbar
        if self.__progbar_ref is not None:
            if (
                (self.__progbar_ref() is not None)
                and (not qt.sip.isdeleted(self.__progbar_ref()))
                and (not self.__progbar_ref().is_dead())
            ):
                assert (
                    self.__progbar_ref() is progbar
                ), f"{self.__progbar_ref()}, {progbar}"
            else:
                self.__progbar_ref = weakref.ref(progbar)
        else:
            self.__progbar_ref = weakref.ref(progbar)

        # $ Libtable
        if self.__libtable_ref is not None:
            if (
                (self.__libtable_ref() is not None)
                and (not qt.sip.isdeleted(self.__libtable_ref()))
                and (not self.__libtable_ref().is_dead())
            ):
                assert (
                    self.__libtable_ref() is libtable
                ), f"{self.__libtable_ref()}, {libtable}"
            else:
                self.__libtable_ref = weakref.ref(libtable)
                libtable.want_more_data.connect(self.give_more_data)
        else:
            self.__libtable_ref = weakref.ref(libtable)
            libtable.want_more_data.connect(self.give_more_data)
        return

    def unlink(
        self,
        libtable: _lib_table_.LibTable,
        progbar: _progbar_.TableProgbar,
    ) -> None:
        """Unlink this LibManager() instance to:

        - LibraryTable() to present all the data
        - LibraryProgbar()
        """
        assert (
            self.__progbar_ref() is progbar
        ), f"{self.__progbar_ref()}, {progbar}"
        assert (
            self.__libtable_ref() is libtable
        ), f"{self.__libtable_ref()}, {libtable}"
        self.__progbar_ref = None
        self.__libtable_ref = None
        return

    # ^                INITIALIZATION AND REFRESHMENT FUNCTIONS                    ^#
    # % ========================================================================== %#
    # % Functions to initialize the database, to refresh parts of it and/or        %#
    # % apply filters.                                                             %#
    # %                                                                            %#

    #! ===============================[ GROUPED ]================================ !#
    #! Grouped actions - on several parts of the database.                        !#
    #!                                                                            !#
    def is_initialized(self, origins: List[str]) -> bool:
        """Check if the given database part(s) is/are initialized."""
        for origin in origins:
            if origin == "zip_url":
                if not self.__remote_initialized:
                    return False
            elif origin == "local_abspath":
                if not self.__stored_initialized:
                    return False
            elif origin == "proj_relpath":
                if not self.__proj_initialized:
                    return False
            else:
                assert False
        return True

    def get_uninitialized_origins(self) -> List[str]:
        """Return a list of all origins for which the initialization procedure
        didn't run yet.

        Return an empty list if everything is already init- ialized.
        """
        origins = []
        if not self.__remote_initialized:
            origins.append("zip_url")
        if not self.__stored_initialized:
            origins.append("local_abspath")
        if not self.__proj_initialized:
            origins.append("proj_relpath")
        return origins

    def initialize(
        self,
        libtable: Union[_lib_table_.LibTable, None],
        progbar: Union[_progbar_.TableProgbar, None],
        origins: List[str],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Prepare oneself:
          - self.__download_json()              'zip_url' in origins
          - self.__initialize_remote_libs()     'zip_url' in origins
          - self.__initialize_stored_libs()     'local_abspath' in origins
          - self.__initialize_proj_libs()       'proj_relpath' in origins
          - self.__refresh_merged_libs()
        """
        if data.startup_log_libmanager:
            print("[startup] libmanager.py -> initialize()")

        if not self.__init_mutex.acquire(blocking=False):
            purefunctions.printc(
                f"\nWARNING: LibManager().initialize({origins}) could not "
                f"acquire mutex.\n",
                color="warning",
            )
            qt.QTimer.singleShot(
                150,
                functools.partial(
                    self.initialize,
                    libtable,
                    progbar,
                    origins,
                    callback,
                    callbackArg,
                ),
            )
            return
        assert (libtable is None) == (progbar is None)
        if libtable is not None:
            assert progbar is not None
            self.link(
                libtable=libtable,
                progbar=progbar,
            )

        def finish_download(success: bool, *args) -> None:
            if data.startup_log_libmanager:
                print(
                    f"[startup] libmanager.py -> initialize().finish_download({success})"
                )
            if not success:
                contact_link = f"{serverfunctions.get_base_url_wfb()}/#contact"
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="ERROR",
                    text=str(
                        f"Embeetle experienced an error while trying to access<br>"
                        f"the online database of libraries. As a consequence,<br>"
                        f"all functionalities related to libraries won{q}t work<br>"
                        f"properly. Please restart Embeetle and try again.<br>"
                        f"<br>"
                        f'<a href="{contact_link}" style="color: #729fcf;">Contact us</a> if this problem persists.<br>'
                    ),
                    text_click_func=functions.open_url,
                )
                init_proj_relpath()
                return
            init_proj_relpath()
            return

        def init_proj_relpath(*args) -> None:
            if data.startup_log_libmanager:
                print(
                    f"[startup] libmanager.py -> initialize().init_proj_relpath()"
                )
            if "proj_relpath" in origins:
                if self.__proj_initialized:
                    purefunctions.printc(
                        f"WARNING: Attempt to initialize {q}proj_relpath{q} "
                        f"twice in LibManager()!",
                        color="warning",
                    )
                    init_local_abspath()
                    return
                assert not self.__proj_initialized
                self.__initialize_proj_libs(
                    callback=init_local_abspath,
                    callbackArg=None,
                )
                return
            init_local_abspath()
            return

        def init_local_abspath(*args) -> None:
            if data.startup_log_libmanager:
                print(
                    f"[startup] libmanager.py -> initialize().init_local_abspath()"
                )
            if "local_abspath" in origins:
                if self.__stored_initialized:
                    purefunctions.printc(
                        f"WARNING: Attempt to initialize {q}local_abspath{q} "
                        f"twice in LibManager()!",
                        color="warning",
                    )
                    init_zip_url()
                    return
                assert not self.__stored_initialized
                self.__initialize_stored_libs(
                    callback=init_zip_url,
                    callbackArg=None,
                )
                return
            init_zip_url()
            return

        def init_zip_url(*args) -> None:
            if data.startup_log_libmanager:
                print(f"[startup] libmanager.py -> initialize().init_zip_url()")
            if "zip_url" in origins:
                if self.__remote_initialized:
                    purefunctions.printc(
                        f"WARNING: Attempt to initialize {q}zip_url{q} twice "
                        f"in LibManager()! (init phase)",
                        color="warning",
                    )
                    finish()
                    return
                assert not self.__remote_initialized
                self.__initialize_remote_libs(
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            if data.startup_log_libmanager:
                print(f"[startup] libmanager.py -> initialize().finish()")
            self.__refresh_merged_libs()
            if "zip_url" in origins:
                assert self.__remote_initialized
            if "local_abspath" in origins:
                assert self.__stored_initialized
            if "proj_relpath" in origins:
                assert self.__proj_initialized
            self.__init_mutex.release()
            callback(callbackArg)
            return

        if "zip_url" in origins:
            if self.__remote_initialized:
                purefunctions.printc(
                    f"WARNING: Attempt to initialize {q}zip_url{q} twice "
                    f"in LibManager()! (download phase)",
                    color="warning",
                )
                finish_download(True)
                return
            assert not self.__remote_initialized
            self.__download_json(
                force=False,
                callback=finish_download,
                callbackArg=None,
            )
            return
        finish_download(True)
        return

    def apply_filters(self) -> None:
        """"""
        self.__apply_filters_on_remote_data()
        self.__apply_filters_on_stored_data()
        self.__refresh_merged_libs()
        return

    def refresh(
        self,
        origins: List[str],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Refresh existing parts of the database.

        This only applies on the unfil- tered parts! Filters still need to be
        applied after refreshing to ensure the filtered parts of the database
        being up-to-date.
        """
        if not self.__init_mutex.acquire(blocking=False):
            purefunctions.printc(
                f"\nWARNING: LibManager().refresh({origins}) could not "
                f"acquire mutex.\n",
                color="warning",
            )
            qt.QTimer.singleShot(
                150,
                functools.partial(
                    self.refresh,
                    origins,
                    callback,
                    callbackArg,
                ),
            )
            return

        def refresh_proj_relpath(*args):
            if "proj_relpath" in origins:
                if not data.is_home:
                    assert self.__proj_initialized
                    self.__refresh_proj_libs(
                        callback=refresh_local_abspath,
                        callbackArg=None,
                    )
                    return
                purefunctions.printc(
                    f"WARNING: Trying to refresh {q}proj_relpath{q} in "
                    f"LibManager() while there is no current project!",
                    color="warning",
                )
            refresh_local_abspath()
            return

        def refresh_local_abspath(*args):
            if "local_abspath" in origins:
                assert self.__stored_initialized
                self.__refresh_stored_libs(
                    callback=refresh_zip_url,
                    callbackArg=None,
                )
                return
            refresh_zip_url()
            return

        def refresh_zip_url(*args):
            if "zip_url" in origins:
                assert self.__remote_initialized
                # For now, we don't need to refresh this. Remote changes
                # don't happen often enough.
                pass
            finish()
            return

        def finish(*args):
            self.__refresh_merged_libs()
            self.__init_mutex.release()
            callback(callbackArg) if callback is not None else nop()
            return

        refresh_proj_relpath()
        return

    #! ===========================[ INITLIALIZATIONS ]=========================== !#
    #! Initialize database parts for the first time in this session.              !#
    #!                                                                            !#

    @_sw_.run_outside_main("__download_json")
    def __download_json(
        self,
        force: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Download 'library_index.json' from the Arduino server. This should
        only be done once in a session.

        :param force: Force the download, even if there is a recent file
            available.
        """
        origthread = self.__download_json.origthread
        nonmainthread = self.__download_json.nonmainthread
        assert origthread is _sw_.get_qthread("main")

        def start(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            # $ Compare timestamps
            if os.path.isfile(self.__json_filepath):
                last_modified_time = datetime.datetime.fromtimestamp(
                    os.path.getmtime(self.__json_filepath)
                )
                current_time = datetime.datetime.now()
                last_modified_time_printout = last_modified_time.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
                current_time_printout = current_time.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
                if (
                    (not force)
                    and (current_time.year == last_modified_time.year)
                    and (current_time.month == last_modified_time.month)
                    and (current_time.day == last_modified_time.day)
                ):
                    print(
                        f"\n"
                        f"Current timestamp: {current_time_printout}\n"
                        f"Last modified {q}library_index.json{q}: {last_modified_time_printout}\n"
                        f"=> The existing {q}library_index.json{q} is recent enough.\n"
                        f"\n"
                    )
                    # Shortcut to finish!
                    finish()
                    return
                else:
                    print(
                        f"\n"
                        f"Current timestamp: {current_time_printout}\n"
                        f"Last modified {q}library_index.json{q}: {last_modified_time_printout}\n"
                        f"=> Update {q}library_index.json{q}\n"
                        f"\n"
                    )

            # Briefly switch to the main thread
            # just to create a MiniConsole() instance
            # there!
            _sw_.switch_thread_modern(
                qthread=origthread,
                callback=create_miniconsole,
            )
            return

        def create_miniconsole(*args):
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole(
                "Download Arduino Library Database"
            )
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=print_intro,
            )
            return

        def print_intro(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n")
            self.__mini_console.printout(
                "DOWNLOAD ARDUINO LIBRARY DATABASE\n", "#ad7fa8"
            )
            self.__mini_console.printout(
                "=================================\n", "#ad7fa8"
            )
            download()
            return

        def download(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            json_url = (
                "https://downloads.arduino.cc/libraries/library_index.json"
            )
            self.__mini_console.download_file(
                url=json_url,
                show_prog=True,
                callback=write_file,
                callbackArg=None,
            )
            return

        def write_file(success, error_description, filepath, *args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            # $ Check download success
            if not success:
                abort()
                return
            # $ Delete old json file if present
            if os.path.isfile(self.__json_filepath):
                self.__mini_console.printout(
                    "\nDelete old database file:\n",
                    "#ad7fa8",
                )
                success = _fp_.delete_file(
                    file_abspath=self.__json_filepath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                )
                if not success:
                    abort()
                    return
            # $ Create subfolder if needed
            subfolder = _pp_.standardize_abspath(
                os.path.dirname(self.__json_filepath)
            )
            if not os.path.isdir(subfolder):
                success = _fp_.make_dir(
                    dir_abspath=subfolder,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                    overwr=False,
                )
                if not success:
                    abort()
                    return
            # $ Move new json file to proper place
            self.__mini_console.printout(
                "\nMove downloaded database file:\n",
                "#ad7fa8",
            )
            success = _fp_.move_file(
                sourcefile_abspath=filepath,
                targetfile_abspath=self.__json_filepath,
                printfunc=self.__mini_console.printout,
                catch_err=True,
                overwr=False,
            )
            if not success:
                abort()
                return
            finish()
            return

        def abort(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n" "Database download and overwrite failed.\n",
                "#ef2929",
            )
            self.__mini_console.printout(
                "Please copy the contents of this console,\n"
                "and paste it in a mail to ",
                "#ffffff",
            )
            self.__mini_console.printout(
                "info@embeetle.com\n",
                "#729fcf",
            )
            self.__download_json.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return

        def finish(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if self.__mini_console is not None:
                self.__mini_console.printout("\n\n")
                self.__mini_console.printout("FINISH \n", "#fcaf3e")
                self.__mini_console.printout("-------\n", "#fcaf3e")
                self.__mini_console.printout(
                    "Congratulations! You downloaded the database successfully.\n",
                    "#73d216",
                )
                self.__mini_console.printout("\n")

            def delayed_finish(*_args):
                "[non-main thread]"
                assert qt.QThread.currentThread() is nonmainthread
                if self.__mini_console is not None:
                    self.__mini_console.close()
                self.__download_json.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(500, delayed_finish)
            return

        start()
        return

    def __initialize_remote_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Process the downloaded json file and load its data."""
        assert not self.__remote_initialized
        assert len(self.__filtered_remote_libs) == 0
        assert len(self.__unfiltered_remote_libs) == 0
        PIECE_LEN: int = 800

        try:
            progbar = self.__progbar_ref()
        except TypeError as e:
            # Progbar is not yet initialized. This can happen if this
            # function is called by the dashboard before the Library Manager
            # has started.
            progbar = None

        def start(*args):
            # Open json file
            if not os.path.isfile(self.__json_filepath):
                purefunctions.printc(
                    f"ERROR: JSON file doesn{q}t exist: {self.__json_filepath}",
                    color="error",
                )
                self.__filtered_remote_libs = {}
                self.__unfiltered_remote_libs = {}
                finish()
                return
            try:
                with open(self.__json_filepath, "r", errors="replace") as f:
                    json_list = json.load(f)["libraries"]
                # Cut json list in pieces of
                # PIECE_LEN entries each
                length = len(json_list)
                if progbar is not None:
                    progbar.set_progbar_value(0)
                    progbar.set_progbar_max(1 + int(length / PIECE_LEN))
                list_of_json_lists = purefunctions.cut_list_in_pieces(
                    my_list=json_list,
                    piece_len=PIECE_LEN,
                )
                extract(iter(list_of_json_lists))
            except Exception as _e:
                purefunctions.printc(
                    f"ERROR: Cannot parse JSON file: {self.__json_filepath}",
                    color="error",
                )
                traceback.print_exc()
                self.__filtered_remote_libs = {}
                self.__unfiltered_remote_libs = {}
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="ERROR",
                    text=str(
                        f"Embeetle experienced an error while parsing the online<br>"
                        f"database of libraries. Please check if the downloaded<br>"
                        f"database is a valid JSON file:<br>"
                        f"{self.__json_filepath}"
                    ),
                )
                finish()
                return
            return

        def extract(json_iter, *args):
            try:
                json_list_piece = next(json_iter)
            except StopIteration:
                finish()
                return
            try:
                for entry in json_list_piece:
                    # The 'entry' represents one 'property dict'
                    # that belongs to a specific library with
                    # specific version.

                    # $ Sanity check
                    libname = entry["name"] if "name" in entry else None
                    version = entry["version"] if "version" in entry else None
                    if (libname is None) or (version is None):
                        purefunctions.printc(
                            f"ERROR: Cannot parse following entry in json file: \n"
                            f"{entry}",
                            color="error",
                        )
                        # Sanity check failed, continue to next entry.
                        continue

                    # $ Figure out architectures
                    architectures: Optional[List] = []
                    if "architectures" in entry:
                        temp = entry["architectures"]
                        if isinstance(temp, str):
                            temp = [
                                temp,
                            ]
                        if isinstance(temp, list):
                            for t in temp:
                                t = t.strip()
                                if (
                                    (t != "*")
                                    and (t.lower() != "all")
                                    and (t != '"*"')
                                    and (t != "")
                                ):
                                    architectures.append(t)
                    if len(architectures) == 0:
                        architectures = None

                    # $ Figure out dependencies
                    dependencies: Optional[List] = []
                    if "dependencies" in entry:
                        dependencies = [
                            d["name"] for d in entry["dependencies"]
                        ]
                    if len(dependencies) == 0:
                        dependencies = None

                    # $ Create new entry
                    new_libobj = _libobj_.LibObj(
                        name=libname,
                        version=version,
                        author=entry["author"],
                        sentence=entry["sentence"],
                        paragraph=(
                            entry["paragraph"]
                            if "paragraph" in entry
                            else "None"
                        ),
                        mod_name=None,
                        mod_author=None,
                        mod_sentence=None,
                        mod_paragraph=None,
                        depends=dependencies,
                        category=entry["category"],
                        web_url=(
                            entry["website"] if "website" in entry else None
                        ),
                        architectures=architectures,
                        proj_relpath=None,
                        local_abspath=None,
                        zip_url=entry["url"],
                        origin="zip_url",
                    )
                    # $ Add libobj to 'self.__unfiltered_remote_libs'
                    if libname not in self.__unfiltered_remote_libs:
                        self.__unfiltered_remote_libs[libname] = []
                    # Check there is no duplicate version
                    for v, p in self.__unfiltered_remote_libs[libname]:
                        if v == version:
                            purefunctions.printc(
                                "ERROR: duplicate entry!!!",
                                color="error",
                            )
                    self.__unfiltered_remote_libs[libname].append(
                        (version, new_libobj)
                    )
                    continue
                # All entries in this piece
                # of json have been handled
                if progbar is not None:
                    progbar.inc_progbar_value()
                qt.QTimer.singleShot(10, functools.partial(extract, json_iter))
                return
            except Exception as _e:
                purefunctions.printc(
                    f"ERROR: Cannot parse JSON file: {self.__json_filepath}",
                    color="error",
                )
                traceback.print_exc()
                self.__filtered_remote_libs = {}
                self.__unfiltered_remote_libs = {}
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="ERROR",
                    text=str(
                        f"Embeetle experienced an error while parsing the online<br>"
                        f"database of libraries. Please check if the downloaded<br>"
                        f"database is a valid JSON file:<br>"
                        f"{self.__json_filepath}"
                    ),
                )
                finish()
                return
            assert False

        def finish(*args):
            self.__remote_initialized = True
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return

    def __initialize_stored_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load all stored libraries.

        Also show them in the Home Window LIBRARIES
        tab - if this code runs in the Home Window.
        """
        assert not self.__stored_initialized
        assert len(self.__unfiltered_stored_libs) == 0
        assert len(self.__filtered_stored_libs) == 0

        def add_next_wait(libobj_iter: Iterator[_libobj_.LibObj]) -> None:
            qt.QTimer.singleShot(
                10,
                functools.partial(
                    add_next_a,
                    libobj_iter,
                ),
            )
            return

        def add_next_a(libobj_iter: Iterator[_libobj_.LibObj]) -> None:
            try:
                libobj = next(libobj_iter)
            except StopIteration:
                finish()
                return
            try:
                category = libobj.get_category()
                if category == "Signal Input/Output":
                    category = "Signal Input-Output"
                rootitem = self._v_rootItem_dict[category]
            except KeyError:
                rootitem = self._v_rootItem_dict["Other"]
            rootitem.add_child(
                child=libobj.get_hometab_item(rootitem),
                alpha_order=False,
                show=False,
                callback=add_next_b,
                callbackArg=(rootitem, libobj_iter),
            )
            return

        def add_next_b(
            arg: Tuple[
                _lib_root_item_.LibCategoryRootItem,
                Iterator[_libobj_.LibObj],
            ],
        ) -> None:
            rootitem, libobj_iter = arg
            self.replace_add_item(
                category=rootitem.get_name(),
                callback=add_next_wait,
                callbackArg=libobj_iter,
            )
            return

        def finish(*args):
            self.__stored_initialized = True
            if not data.is_home:
                # There is no Home Window
                callback(callbackArg) if callback is not None else nop()
                return
            data.libman_widg.refresh_all_recursive(
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # * Loop over library collections
        for libcollection_abspath in self.__local_origins:
            # A 'libcollection_abspath' is a folder that probably contains
            # several libraries.
            if libcollection_abspath is None:
                continue
            if not os.path.isdir(libcollection_abspath):
                continue

            # * Loop over individual libraries
            for foldername in os.listdir(libcollection_abspath):
                found_libpath = _pp_.rel_to_abs(
                    rootpath=libcollection_abspath,
                    relpath=foldername,
                )
                if not os.path.isdir(found_libpath):
                    continue
                found_propfile = _pp_.rel_to_abs(
                    rootpath=found_libpath,
                    relpath="library.properties",
                )
                if not os.path.isfile(found_propfile):
                    continue
                new_libobj = self.__create_libobj_from_properties_file(
                    found_propfile
                )
                if new_libobj is None:
                    purefunctions.printc(
                        f"\nERROR: Cannot parse file: "
                        f"{q}{found_propfile}{q}\n",
                        color="error",
                    )
                    continue
                # $ Extract name and version
                found_libname = new_libobj.get_name()
                found_version = new_libobj.get_version()
                # $ Add entry to 'self.__unfiltered_stored_libs'
                if found_libname not in self.__unfiltered_stored_libs:
                    self.__unfiltered_stored_libs[found_libname] = []
                self.__unfiltered_stored_libs[found_libname].append(
                    (found_version, new_libobj)
                )
                continue
            continue

        # * Add libobjs to Home Window LIBRARIES tab
        if not data.is_home:
            # There is no Home Window
            finish()
            return
        libobj_list = [
            libobj
            for libname, liblist in self.__unfiltered_stored_libs.items()
            for version, libobj in liblist
            if ".embeetle/libraries" in libobj.get_local_abspath()
        ]
        add_next_wait(iter(libobj_list))
        return

    def __initialize_proj_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load all project libraries.

        This only makes sense in Project-mode.
        """
        assert not self.__proj_initialized
        assert len(self.__unfiltered_proj_libs) == 0

        # * Home Window
        if data.is_home:
            self.__unfiltered_proj_libs = {}
            self.__proj_initialized = True
            callback(callbackArg)
            return

        # * Project Window
        # Loop over all rootpaths to extract the properties files.
        try:
            propfiles = []
            for rootpath in data.current_project.get_all_rootpaths():
                propfiles.extend(
                    [
                        _pp_.rel_to_abs(dirpath, f)
                        for dirpath, dirs, files in os.walk(rootpath)
                        for f in files
                        if f.lower() == "library.properties"
                    ]
                )
            # Loop over all properties files to create a LibObj() for each of them.
            # Store these LibObj()s in 'self.__unfiltered_proj_libs'.
            for propfile_abspath in propfiles:
                new_libobj = self.__create_libobj_from_properties_file(
                    propfile_abspath
                )
                if new_libobj is None:
                    purefunctions.printc(
                        f"ERROR: Cannot parse file: "
                        f"{q}{propfile_abspath}{q}",
                        color="error",
                    )
                    continue
                found_libname = new_libobj.get_name()
                found_version = new_libobj.get_version()
                if found_libname not in self.__unfiltered_proj_libs:
                    self.__unfiltered_proj_libs[found_libname] = []
                self.__unfiltered_proj_libs[found_libname].append(
                    (found_version, new_libobj)
                )
                continue
            self.__proj_initialized = True
        except:
            traceback.print_exc()
            raise
        callback(callbackArg)
        return

    #! =============================[ REFRESHMENTS ]============================= !#
    #! Refresh existing parts of the database.                                    !#
    #!                                                                            !#
    def __refresh_hdd_libs(
        self,
        propfiles: List[str],
        dict_to_modify: Dict,
        in_project: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Help function, to be used for both the 'stored' libraries and the
        'project' libraries.

        :param propfiles:      List of absolute paths to 'library.properties'
                               files that must be examined.

        :param dict_to_modify: The dictionary to be modified:
                                  - self.__unfiltered_stored_libs
                                  - self.__unfiltered_proj_libs
        """

        def delete_libobj_from_database(
            _libobj: _libobj_.LibObj, cb, cba
        ) -> None:
            "Help function used in the next one"
            # Delete the LibObj() from the database. The 'self_destruct()' method is
            # invoked on the object, which also kills its GUI elements.
            _libname = _libobj.get_name()
            _liblist = dict_to_modify[_libname]
            for i, t in enumerate(_liblist):
                if _libobj is t[1]:
                    del _liblist[i]
                    break
            else:
                assert False
            if len(_liblist) == 0:
                del dict_to_modify[_libname]
            # Kill the libobj
            _libobj.self_destruct(
                callback=cb,
                callbackArg=cba,
            )
            return

        def check_next_libobj_for_deletion(
            libobj_iter: Iterator[_libobj_.LibObj],
        ) -> None:
            "Check next libobj to decide if it must be deleted"
            try:
                _libobj: _libobj_.LibObj = next(libobj_iter)
            except Exception as e:
                take_care_of_gui()
                return

            # Extract the paths from the LibObj(). Assign the relevant one to
            # the variable 'abspath'.
            abspath: Optional[str] = None
            origin = _libobj.get_origin()
            if origin == "proj_relpath":
                if _libobj.get_proj_rootpath() is None:
                    # $ CASE 1: [proj only] propfile in removed external folder
                    # This LibObj() belonged to an external folder that no long-
                    # er exists! We know that because requesting the rootpath
                    # failed: it is no longer known to the Project()-instance.
                    delete_libobj_from_database(
                        _libobj=_libobj,
                        cb=check_next_libobj_for_deletion,
                        cba=libobj_iter,
                    )
                    return
                else:
                    abspath = _libobj.get_proj_abspath()
            elif origin == "local_abspath":
                abspath = _libobj.get_local_abspath()
            else:
                raise RuntimeError(f"Unknown origin: {q}{origin}{q}")

            # $ CASE 2: abspath is None
            # This shouldn't happen!
            if abspath is None:
                purefunctions.printc(
                    f"\nERROR: LibObj() {_libobj.get_name()} has no abspath!",
                    color="error",
                )
                delete_libobj_from_database(
                    _libobj=_libobj,
                    cb=check_next_libobj_for_deletion,
                    cba=libobj_iter,
                )
                return

            # Deduce where the 'library.properties' file for this library should
            # be.
            _propfile = _pp_.rel_to_abs(
                rootpath=abspath,
                relpath="library.properties",
            )

            # $ CASE 3: propfile doesn't exist
            # The 'library.properties' file no longer exists. It's clear that
            # this LibObj() must be destroyed!
            if not os.path.isfile(_propfile):
                delete_libobj_from_database(
                    _libobj=_libobj,
                    cb=check_next_libobj_for_deletion,
                    cba=libobj_iter,
                )
                return

            propdict = self.__parse_properties_file(_propfile)

            # $ CASE 4: propfile is invalid
            # The 'library.properties' file seems to be no longer valid, so this
            # LibObj() must be destroyed.
            if (
                propdict is None
                or (propdict["name"] is None)
                or (propdict["name"].lower() == "none")
            ):
                purefunctions.printc(
                    f"\nWARNING: Library with properties file \n"
                    f"at {q}{_propfile}{q} \n"
                    f"has not a valid format!\n",
                    color="warning",
                )
                delete_libobj_from_database(
                    _libobj=_libobj,
                    cb=check_next_libobj_for_deletion,
                    cba=libobj_iter,
                )
                return

            # $ CASE 5: propfile reports other name
            # The library name reported by 'library.properties' differs from the
            # name stored in this LibObj(). That must have resulted in a new
            # LibObj() spawn with that new name (see top of the 'start' proced-
            # ure).
            # The LibObj() being examined here is no longer valid and should be
            # destroyed.
            if propdict["name"] != _libobj.get_name():
                purefunctions.printc(
                    f"\nWARNING: Library name changed "
                    f"from {_libobj.get_name()} into "
                    f'{propdict["name"]}\n',
                    color="warning",
                )
                delete_libobj_from_database(
                    _libobj=_libobj,
                    cb=check_next_libobj_for_deletion,
                    cba=libobj_iter,
                )
                return

            # $ Keep the LibObj()
            # By this point, the examined LibObj() is valid. Check the next one
            # from the iterator. There can be (potentially) many LibObj()s, so
            # its unsafe to invoke this method directly (stack overflow)!
            qt.QTimer.singleShot(
                5,
                functools.partial(
                    check_next_libobj_for_deletion,
                    libobj_iter,
                ),
            )
            return

        def take_care_of_gui(*args) -> None:
            "Take care of GUI stuff"
            # By this point, we did:
            #   > Add new LibObj()s from the given propfiles (GUI ignored)
            #   > Update all existing LibObj()s with the given propfiles (GUI
            #     ignored).
            #   > Delete deprecated LibObj()s (GUI okay).
            # So some tasks for the GUI are not yet taken care of. That's what
            # will be done here.
            if not data.is_home:
                # There is no Home Window. For the dashboard, this task is taken
                # care of in:
                # 'lib_seg.py' -> trigger_dashboard_refresh()
                finish()
                return
            assert data.is_home
            libobjs_to_be_added_list: List[_libobj_.LibObj] = []
            for _libobj in self.list_local_libobjs():
                # Weed out the local libraries that are not in the .embeetle
                # cache folder.
                if _libobj.get_local_abspath() is None:
                    continue
                if ".embeetle/libraries" not in _libobj.get_local_abspath():
                    continue
                if not os.path.exists(_libobj.get_local_abspath()):
                    purefunctions.printc(
                        f"ERROR: While trying to visualize the libraries in the\n"
                        f"Home Window LIBRARIES tab, it turns out that the fol-\n"
                        f"lowing library doesn{q}t have a valid local abspath:\n"
                        f"{_libobj.get_name()}: {q}{_libobj.get_local_abspath()}{q}\n",
                        color="error",
                    )
                    continue
                # Figure out to what rootitem this LibObj() belongs.
                try:
                    category = _libobj.get_category()
                    if category == "Signal Input/Output":
                        category = "Signal Input-Output"
                    rootitem = self._v_rootItem_dict[category]
                except KeyError:
                    rootitem = self._v_rootItem_dict["Other"]
                # Is this LibObj() already added to that rootitem?
                if (
                    _libobj.get_hometab_item(rootitem)
                    in rootitem.get_childlist()
                ):
                    # Move on to the next
                    continue
                libobjs_to_be_added_list.append(_libobj)
                continue
            add_next_wait(iter(libobjs_to_be_added_list))
            return

        def add_next_wait(
            libobjs_to_be_added: Iterator[_libobj_.LibObj],
        ) -> None:
            qt.QTimer.singleShot(
                10,
                functools.partial(
                    add_next_a,
                    libobjs_to_be_added,
                ),
            )
            return

        def add_next_a(libobjs_to_be_added: Iterator[_libobj_.LibObj]) -> None:
            "Add next LibObj() to Home LIBRARIES tab"
            assert data.is_home
            try:
                _libobj = next(libobjs_to_be_added)
            except StopIteration:
                qt.QTimer.singleShot(10, refresh_all)
                return
            # Figure out to what rootitem this LibObj() belongs.
            try:
                category = _libobj.get_category()
                if category == "Signal Input/Output":
                    category = "Signal Input-Output"
                rootitem = self._v_rootItem_dict[category]
            except KeyError:
                rootitem = self._v_rootItem_dict["Other"]
            rootitem.add_child(
                child=_libobj.get_hometab_item(rootitem),
                alpha_order=True,
                show=True,
                callback=add_next_b,
                callbackArg=(rootitem, libobjs_to_be_added),
            )
            return

        def add_next_b(
            arg: Tuple[
                _lib_root_item_.LibCategoryRootItem, Iterator[_libobj_.LibObj]
            ],
        ) -> None:
            rootitem, libobjs_to_be_added = arg
            self.replace_add_item(
                category=rootitem.get_name(),
                callback=add_next_wait,
                callbackArg=libobjs_to_be_added,
            )
            return

        def refresh_all(*args) -> None:
            "Refresh the whole Home LIBRARIES tab"
            assert data.is_home
            data.libman_widg.refresh_all_recursive(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        #! ============================[ Start ]============================= !#
        # * 1. New and existing LibObj()s
        # Loop over all the given 'library.properties' files. Observe them and
        # try to modify the given 'dict_to_modify' accordingly (either 'self.
        # __unfiltered_stored_libs' or 'self.__unfiltered_proj_libs'):
        #   > Add new LibObj()s for those properties files that
        #     are unknown to the 'dict_to_modify' or whose lib-
        #     name has changed.
        #   > Modify existing LibObj()s from observing the cor-
        #     responding properties files.
        # NOTES:
        # - Ignore for now the deletion of LibObj()s.
        # - Ignore for now the GUI side of things.
        for found_propfile in propfiles:
            # Observe the 'library.properties' file and extract a propdict from
            # it.
            assert os.path.isfile(found_propfile)
            found_propdict = self.__parse_properties_file(found_propfile)
            if found_propdict is None:
                purefunctions.printc(
                    f"ERROR: Cannot parse file: " f"{q}{found_propfile}{q}",
                    color="error",
                )
                continue
            found_libname = found_propdict["name"]
            found_version = found_propdict["version"]
            found_origin = found_propdict["origin"]
            if found_libname not in dict_to_modify:
                dict_to_modify[found_libname] = []

            # Extract the relevant 'liblist' from the 'dict_to_modify'. A 'lib-
            # list' is a list of tuples, pairing versions to LibObj()s.
            liblist = dict_to_modify[found_libname]

            # $ New libname => add new LibObj()
            # The libname found in the properties dict was unknown to the 'dict_
            # to_modify', so a new empty liblist was formed. Create a new(!)
            # LibObj() and put it in the liblist.
            if len(liblist) == 0:
                new_libobj = self.__create_libobj_from_propdict(found_propdict)
                liblist.append((found_version, new_libobj))
                continue

            # $ Existing libname => modify existing LibObj()
            # There is already a liblist with LibObj()s. Check if one of these
            # LibObj()s corresponds to the properties dict that was extracted
            # above. If yes, there's no need to create a new LibObj()! The exis-
            # ting LibObj() can be modified with the extracted propdict.
            for version, libobj in liblist:
                if libobj.get_origin() == found_origin:
                    if (found_origin == "local_abspath") and (
                        libobj.get_local_abspath()
                        == found_propdict["local_abspath"]
                    ):
                        libobj.modify_from_propdict(found_propdict)
                        break
                    if (found_origin == "proj_relpath") and (
                        libobj.get_proj_relpath()
                        == found_propdict["proj_relpath"]
                    ):
                        libobj.modify_from_propdict(found_propdict)
                        break

            # $ Existing libname, but not same loc => add new LibObj()
            # Although there is already a liblist for the given libname, there
            # is no existing LibObj() inside with the same harddrive location.
            else:
                new_libobj = self.__create_libobj_from_propdict(found_propdict)
                liblist.append((found_version, new_libobj))
            continue

        # * 2. Destroy LibObj()s
        # By now, all LibObj()s should be updated and new ones added where need-
        # ed (although the GUI side of things has not been taken care of yet).
        # However, there might still be LibObj()s present for libraries that no
        # longer exist, or in external folders that are no longer part of the
        # project.
        # Start the procedure to weed out those deprecated LibObj()s.
        libobj_list = []
        for libname, liblist in dict_to_modify.items():
            for version, libobj in liblist:
                libobj_list.append(libobj)
        check_next_libobj_for_deletion(iter(libobj_list))
        return

    def __refresh_stored_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Refresh the stored libraries dictionaries."""
        assert self.is_initialized(["local_abspath"])
        propfiles = []
        # $ Loop over library collections
        for libcollection_abspath in self.__local_origins:
            # 'libcollection_abspath' is a folder that
            # probably contains several libraries.
            if libcollection_abspath is None:
                continue
            if not os.path.isdir(libcollection_abspath):
                continue
            # $ Loop over individual libraries
            for foldername in os.listdir(libcollection_abspath):
                found_libpath = _pp_.rel_to_abs(
                    rootpath=libcollection_abspath,
                    relpath=foldername,
                )
                if not os.path.isdir(found_libpath):
                    continue
                found_propfile = _pp_.rel_to_abs(
                    rootpath=found_libpath,
                    relpath="library.properties",
                )
                if not os.path.isfile(found_propfile):
                    continue
                propfiles.append(found_propfile)
                continue
            continue
        self.__refresh_hdd_libs(
            propfiles=propfiles,
            dict_to_modify=self.__unfiltered_stored_libs,
            in_project=False,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def __refresh_proj_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Refresh the part of the database that holds the project LibObj()s.
        Roughly speaking, three kinds of operations will happen:

            1. LibObj()s deleted:   LibObj()s for no-longer-existing properties
                                    files get deleted from the database. Also,
                                    their self_destruct() methods are called, which
                                    deletes them from the dashboard as well,
                                    because the self_destruct is propagated to the
                                    _v_dashboard_item(s).

            2. LibObj()s modified:  LibObj()s get modified according to new
                                    content in the 'library.properties' file.
                                    These modifications will automatically
                                    trickle down to the dashboard items, as soon
                                    as they refresh: upon their refreshment,
                                    these dashboard items pull the needed info
                                    from their 'projSegment', which is the
                                    LibObj()-instance.

            3. LibObj()s added:     LibObj()s get added to the database, but
                                    this won't automatically add them to the
                                    dashboard!

        In other words - action must be taken only for case nr. 3 to ensure the
        dashboard remains in sync with the LibManager() database!
        """
        assert self.is_initialized(["proj_relpath"])
        # * Home Window
        if data.is_home:
            self.__unfiltered_proj_libs = {}
            return

        # * Project Window
        propfiles = []
        for rootpath in data.current_project.get_all_rootpaths():
            propfiles.extend(
                [
                    _pp_.rel_to_abs(dirpath, f)
                    for dirpath, dirs, files in os.walk(rootpath)
                    for f in files
                    if f.lower() == "library.properties"
                ]
            )
        self.__refresh_hdd_libs(
            propfiles=propfiles,
            dict_to_modify=self.__unfiltered_proj_libs,
            in_project=True,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def __refresh_merged_libs(self) -> None:
        """Refresh the merged dictionaries."""
        # * Filtered
        remote_libs = self.__filtered_remote_libs
        stored_libs = self.__filtered_stored_libs
        self.__filtered_merged_libs = {
            k: {
                "zip_url": remote_libs[k] if k in remote_libs else None,
                "local_abspath": stored_libs[k] if k in stored_libs else None,
                "proj_relpath": None,
            }
            for k in set().union(
                remote_libs.keys(),
                stored_libs.keys(),
            )
        }
        self.__filtered_merged_list = sorted(
            self.__filtered_merged_libs.items()
        )
        self.__total_len = len(self.__filtered_merged_list)

        # * Unfiltered
        unfiltered_stored_libs = self.__unfiltered_stored_libs
        unfiltered_remote_libs = self.__unfiltered_remote_libs
        unfiltered_proj_libs = self.__unfiltered_proj_libs
        self.__unfiltered_merged_libs = {
            k: {
                "zip_url": (
                    unfiltered_remote_libs[k]
                    if k in unfiltered_remote_libs
                    else None
                ),
                "local_abspath": (
                    unfiltered_stored_libs[k]
                    if k in unfiltered_stored_libs
                    else None
                ),
                "proj_relpath": (
                    unfiltered_proj_libs[k]
                    if k in unfiltered_proj_libs
                    else None
                ),
            }
            for k in set().union(
                unfiltered_remote_libs.keys(),
                unfiltered_stored_libs.keys(),
                unfiltered_proj_libs.keys(),
            )
        }
        self.__unfiltered_merged_list = sorted(
            self.__unfiltered_merged_libs.items()
        )
        return

    #! ============================[ APPLY FILTERS ]============================= !#
    #! Apply the filters on parts of the database.                                !#
    #!                                                                            !#

    def __libobj_passes_filters(self, libobj: _libobj_.LibObj) -> bool:
        """Return True if the given LibObj()-instance passes current filters.

        Also add the needed modi-
        fied variables (mod_name, mod_author, ...) to the LibObj() to show highlights (eg. yellow
        marker).
        """
        # $ Extract data from libobj
        author: str = libobj.get_author()
        category: str = libobj.get_category()
        name: str = libobj.get_name()
        sentence: str = libobj.get_sentence()
        paragraph: str = libobj.get_paragraph()

        for e in (author, category, name, sentence, paragraph):
            if not isinstance(e, str):
                purefunctions.printc(
                    f"ERROR: libobj corrupted:\n"
                    f"    libobj.get_author()    = {author}\n"
                    f"    libobj.get_category()  = {category}\n"
                    f"    libobj.get_name()      = {name}\n"
                    f"    libobj.get_sentence()  = {sentence}\n"
                    f"    libobj.get_paragraph() = {paragraph}\n",
                    color="error",
                )
                return False

        # $ patterns/filters
        search_p: Optional[re.Pattern] = self.__json_filter.get_search_pattern()
        author_p: Optional[re.Pattern] = self.__json_filter.get_author_pattern()
        topic_p: Optional[re.Pattern] = self.__json_filter.get_topic_pattern()
        gen_subst: str = self.__json_filter.get_search_pattern_subst()
        author_subst: str = self.__json_filter.get_author_pattern_subst()

        # * Check if libobj passes filters
        # $ author
        if author_p is not None:
            if author_p.search(author) is None:
                # No match
                return False
        # $ topic
        if topic_p is not None:
            if topic_p.search(category) is None:
                # No match
                return False
        # $ search
        if search_p is not None:
            for text in (name, author, category, sentence, paragraph):
                if search_p.search(text) is not None:
                    # Match -> break out of this inner for-loop and skip
                    # the else statement.
                    break
            else:
                # No break statement encountered -> no match!
                return False

        # * Highlighting (and wrapping)
        # $ Prepare variables
        mod_name = name
        mod_author = author
        mod_sentence = sentence
        mod_paragraph = paragraph
        # $ Apply modifications
        mod_author = (
            mod_author.replace("\\u003c", "<")
            .replace("\\u003e", ">")
            .replace("<", " <")
        )
        # $ Highlight search keyword
        if search_p is not None:
            mod_name = search_p.sub(
                gen_subst,
                mod_name,
            )
            mod_author = search_p.sub(
                gen_subst,
                mod_author,
            )
            mod_sentence = search_p.sub(
                gen_subst,
                mod_sentence,
            )
            mod_paragraph = search_p.sub(
                gen_subst,
                mod_paragraph,
            )
        # $ Highlight author keyword
        if author_p is not None:
            mod_author = author_p.sub(
                author_subst,
                mod_author,
            )
        libobj.set_mod_name(mod_name)
        libobj.set_mod_author(mod_author)
        libobj.set_mod_sentence(mod_sentence)
        libobj.set_mod_paragraph(mod_paragraph)
        return True

    def __apply_filters_on_remote_data(self) -> None:
        """The downloaded json-file cannot change in just one session.

        Therefore, this function is mainly to re-apply the filter.
        """
        assert self.is_initialized(["zip_url"])
        # $ Reset
        self.__given_slice = 0
        self.__total_len = 0

        # Check if user wants the online database
        if (
            "https://downloads.arduino.cc/libraries/library_index.json"
            not in self.__json_filter.get_origin_filter()
        ):
            self.__filtered_remote_libs = {}
            return

        self.__filtered_remote_libs = {
            name: [
                (version, libobj)
                for version, libobj in self.__unfiltered_remote_libs[name]
                if self.__libobj_passes_filters(libobj)
            ]
            for name in self.__unfiltered_remote_libs.keys()
        }

        self.__filtered_remote_libs = {
            name: self.__filtered_remote_libs[name]
            for name in self.__filtered_remote_libs.keys()
            if len(self.__filtered_remote_libs[name]) > 0
        }
        return

    def __apply_filters_on_stored_data(self) -> None:
        """Re-apply the filter."""
        assert self.is_initialized(["local_abspath"])
        # $ Reset
        self.__given_slice = 0
        self.__total_len = 0
        self.__filtered_stored_libs = {}
        for name, liblist in self.__unfiltered_stored_libs.items():
            for version, libobj in liblist:
                parent_folder = os.path.dirname(
                    libobj.get_local_abspath()
                ).replace("\\", "/")
                if parent_folder in self.__json_filter.get_origin_filter():
                    if self.__libobj_passes_filters(libobj):
                        if name not in self.__filtered_stored_libs:
                            self.__filtered_stored_libs[name] = []
                        self.__filtered_stored_libs[name].append(
                            (version, libobj)
                        )
        return

    # def push_libobj_to_source_analyzer(self,
    #                                    libobj:_libobj_.LibObj,
    #                                    callback:Optional[Callable],
    #                                    callbackArg:Any,
    #                                    ) -> None:
    #     '''
    #     Push each '.c' and '.h' file from the given library to the source ana-
    #     lyzer.
    #     USE
    #     ===
    #     This function must ONLY be called when an existing library is being
    #     overwritten. For *new* libraries being added, there is no point in cal-
    #     ling this function, as the filetree already takes care of *discovered*
    #     folders.
    #     TODO: Check if this should be implemented
    #     '''

    # ^                            DATABASE REQUESTS                               ^#
    # % ========================================================================== %#
    # % All kinds of requests to get data from the database.                       %#
    # %                                                                            %#

    #! ===========================[ SIMPLE REQUESTS ]============================ !#
    #! Simple database requests.                                                  !#
    #!                                                                            !#

    def get_nr_of_proj_libs(self) -> Optional[int]:
        """"""
        assert self.is_initialized(["proj_relpath"])
        if data.is_home:
            return None
        return len(self.__unfiltered_proj_libs)

    def list_proj_libs_names(self) -> Optional[List[str]]:
        """List the names of all libraries in the current project."""
        assert self.is_initialized(["proj_relpath"])
        if data.is_home:
            return None
        return [key for key in self.__unfiltered_proj_libs.keys()]

    def list_proj_libobjs(self) -> Optional[List[_libobj_.LibObj]]:
        """List all the LibObj()s belonging to the current project."""
        assert self.is_initialized(["proj_relpath"])
        if data.is_home:
            return None
        result_list = []
        for libname, liblist in self.__unfiltered_proj_libs.items():
            if len(liblist) > 1:
                purefunctions.printc(
                    f"WARNING: The current project has more than one library "
                    f"named {q}{libname}{q}",
                    color="warning",
                )
            for version, libobj in liblist:
                result_list.append(libobj)
        return result_list

    def list_local_libobjs(self) -> Optional[List[_libobj_.LibObj]]:
        """List all the LibObj()s on the local harddrive (but not in the
        project)."""
        assert self.is_initialized(["local_abspath"])
        result_list = []
        for libname, liblist in self.__unfiltered_stored_libs.items():
            for version, libobj in liblist:
                result_list.append(libobj)
        return result_list

    def list_cached_libs_names(self) -> Optional[List[_libobj_.LibObj]]:
        """List all the Library names present in the '~/.embeetle/libraries'
        folder."""
        assert self.is_initialized(["local_abspath"])
        libname_list = [
            libobj.get_name()
            for libname, liblist in self.__unfiltered_stored_libs.items()
            for version, libobj in liblist
            if ".embeetle/libraries" in libobj.get_local_abspath()
        ]
        return list(set(libname_list))

    def get_libobj_from_merged_libs(
        self,
        libname: str,
        libversion: Optional[str],
        origins: List[str],
    ) -> Optional[_libobj_.LibObj]:
        """When given the library name and version, this function looks up the
        LibObj() and returns None if nothing was found.

        :param libname:     Library to look for.

        :param libversion:  Library version to look for. If None, just take the
                            most recent one. To find the most recent one, look
                            both online and on harddrive!

        :param origins:     Only look in those database-parts corresponding to
                            the given origins.

        USE CASES
        =========
        - The version widget uses this function to fetch new sentence and para-
          graph contents after the user selects another version.

        - The listing of dependencies uses this function to read the 'depends'
          value from the propdict for a given library.

        NOTES
        =====
        - The lookups are done in 'self._unfiltered_merged_libs'. Filtering
          would only lower the chance of finding something!

        - When there are multiple hits, just one LibObj() will be returned.
          After all, the propertiesdict should be the same for these multiple
          hits (with exception of the 'zip_url' and/or 'libpath' fields).

        - Priority order: 'local_abspath' > 'zip_url' > 'proj_relpath'
        """
        # * Sanitize input
        assert self.is_initialized(origins)
        if libname not in self.__unfiltered_merged_libs:
            return None

        # * Create temporary data list
        # Create the liblist 'totaldata' for the given 'libname'. It's a list of
        # tuples, pairing version nrs with LibObj()s.
        temp = self.__unfiltered_merged_libs[libname]
        remote_data = temp["zip_url"]
        stored_data = temp["local_abspath"]
        proj_data = temp["proj_relpath"]
        totaldata = []
        if stored_data is not None:
            if "local_abspath" in origins:
                totaldata += stored_data
        if remote_data is not None:
            if "zip_url" in origins:
                totaldata += remote_data
        if proj_data is not None:
            if "proj_relpath" in origins:
                totaldata += proj_data

        # * Libversion given
        # If the 'libversion' is given, it's easy to pick the right LibObj()
        # from the 'totaldata' liblist. If there would be more than one LibObj()
        # with that version, the first one is taken.
        if libversion is not None:
            for v, libobj in totaldata:
                if v == libversion:
                    return libobj
            return None

        # * Libversion not given
        assert libversion is None
        most_recent_version: Optional[str] = None
        most_recent_libobj: Optional[_libobj_.LibObj] = None
        for v, libobj in totaldata:
            if most_recent_version is None:
                most_recent_version = v
                most_recent_libobj = libobj
            if purefunctions.is_more_recent_than(
                v1=v,
                v2=most_recent_version,
            ):
                most_recent_version = v
                most_recent_libobj = libobj
            continue
        if most_recent_libobj is None:
            return None
        return most_recent_libobj

    def get_online_library_zip_url(
        self,
        libname: str,
        libversion: str,
    ) -> Optional[str]:
        """Get URL to zipfile for the online library with given 'libname' and
        'libversion'."""
        assert self.is_initialized(["zip_url"])
        if libname not in self.__unfiltered_remote_libs:
            return None
        for v, libobj in self.__unfiltered_remote_libs[libname]:
            if v.strip() == libversion.strip():
                return libobj.get_zip_url()
        return None

    def __get_most_recent_version(self, libname: str) -> Optional[str]:
        """Given the library name, this function searches in 'self._remote_libs'
        for the latest version.

        Return None if the library is not found.
        """
        assert self.is_initialized(["zip_url"])
        if libname not in self.__unfiltered_remote_libs:
            print(f"{q}{libname}{q} not found in {q}self._remote_libs{q}!")
            return None
        recent_version = None
        for version, propdict in self.__unfiltered_remote_libs[libname]:
            if recent_version is None:
                recent_version = version
                continue
            if purefunctions.is_more_recent_than(version, recent_version):
                recent_version = version
            continue
        return recent_version

    #! ==========================[ FILL LIBRARY TABLE ]========================== !#
    #! Give data to the library table.                                            !#
    #!                                                                            !#

    def give_more_data(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Acquire the next data slice (eg. with SLICE_LEN = 100, so a hundred
        libraries) and present this data in the LibraryTable().

        The data is presented in several 'bursts' with 50ms in between them.
        The size of one burst is given by ROWS_PER_BURST (eg. 10).

        USE:
        ====
        Connected to 'want_more_data' signal from LibTable().

        MUTEX:
        ======
        Adding rows to the table is protected with a mutex. Warning: this
        function won't attempt a restart when the mutex is not available!
        """
        if not self.__adding_rows_mutex.acquire(blocking=False):
            return
        SLICE_LEN = 100
        ROWS_PER_BURST = 10
        progbar: _progbar_.TableProgbar = self.__progbar_ref()
        libtable: _lib_table_.LibTable = self.__libtable_ref()

        def get_next_data_slice(*args):
            "Get next slice of data in list-of-tuples format"
            # A total of SLICE_LEN libraries (each of them potentially with more
            # than one version) are cut.
            _start = self.__given_slice
            _stop = self.__given_slice + SLICE_LEN
            if _start >= self.__total_len:
                # print('NO MORE DATA TO GIVE')
                return None
            if _stop >= self.__total_len:
                # print('GIVING LAST SLICE')
                pass
            result = list(
                islice(
                    self.__filtered_merged_list,
                    _start,
                    _stop,
                )
            )
            self.__given_slice = _stop
            return result

        def show_next_burst(data_iter, *args):
            "Push one data burst (eg. 10 rows) to the table widget"
            try:
                databurst = next(data_iter)
            except StopIteration:
                finish()
                return
            for libname, remote_and_stored_data in databurst:
                remote_data = remote_and_stored_data["zip_url"]
                stored_data = remote_and_stored_data["local_abspath"]
                # $ Push remote data
                if remote_data is not None:
                    recent_version = None
                    recent_libobj = None
                    versionlist = []
                    for version, libobj in remote_data:
                        versionlist.append(version)
                        assert isinstance(version, str), f"version = {version}"
                        if recent_version is None:
                            recent_version = version
                            recent_libobj = libobj
                        else:
                            assert isinstance(
                                version, str
                            ), f"version = {version}"
                            assert isinstance(
                                recent_version, str
                            ), f"recent_version = {recent_version}"
                            if purefunctions.is_more_recent_than(
                                version, recent_version
                            ):
                                recent_version = version
                                recent_libobj = libobj
                        continue
                    libtable.add_row(
                        libobj=recent_libobj,
                        versionlist=purefunctions.sort_versions_high_to_low(
                            versionlist
                        ),
                    )
                # $ Push stored data
                if stored_data is not None:
                    for version, libobj in stored_data:
                        assert isinstance(version, str), f"version = {version}"
                        libtable.add_row(
                            libobj=libobj,
                            versionlist=None,
                        )
                        continue
                continue
            progbar.inc_progbar_value()
            if self.__stop_adding_rows:
                # Kill the iterator, clear the
                # flag and take shortcut to the
                # finish.
                del data_iter
                self.__stop_adding_rows = False
                finish()
                return
            qt.QTimer.singleShot(
                50,
                functools.partial(
                    show_next_burst,
                    data_iter,
                ),
            )
            return

        def finish(*args):
            "Close the table widget"
            libtable.finish_adding_rows()
            progbar.hide()
            self.__adding_rows_mutex.release()
            callback(callbackArg) if callback is not None else nop()
            return

        # Initialize table widget, collect data slice and cut it in bursts
        dataslice = get_next_data_slice()
        if dataslice is None:
            libtable.add_end_row()
            finish()
            return
        total_len = len(dataslice)
        progbar.show()
        progbar.set_progbar_value(0)
        progbar.set_progbar_max(1 + int(total_len / ROWS_PER_BURST))
        data_list = purefunctions.cut_list_in_pieces(
            my_list=dataslice,
            piece_len=ROWS_PER_BURST,
        )
        libtable.start_adding_rows()
        show_next_burst(iter(data_list))
        return

    #! =========================[ DEPENDENCIES LISTING ]========================= !#
    #! Functions related to dependencies listing.                                 !#
    #!                                                                            !#

    def list_dependencies_recursively(
        self,
        libobj: _libobj_.LibObj,
        initial_call: bool,
    ) -> Optional[List[str]]:
        """List all dependencies from the given LibObj()-instance. To find
        depen- dencies, this function will look in all available origins.

        :param libobj: The LibObj() representing the library to list de-
            pendencies from.
        :param initial_call: True -> The first call False -> A recursive call
        """
        origins_to_look_into = []
        if not data.is_home:
            assert self.is_initialized(
                ["zip_url", "local_abspath", "proj_relpath"]
            )
            origins_to_look_into = ["zip_url", "local_abspath", "proj_relpath"]
        else:
            assert self.is_initialized(["zip_url", "local_abspath"])
            origins_to_look_into = ["zip_url", "local_abspath"]
        if initial_call:
            self.__libs_already_recursed_for_dependencies = []
            if not self.__search_dependencies_mutex.acquire(blocking=False):
                raise RuntimeError(
                    f"{q}list_dependencies_recursively{q} cannot be called"
                    f"multiple times simultaneously!"
                )
        self.__libs_already_recursed_for_dependencies.append(libobj.get_name())
        assert self.__search_dependencies_mutex.locked()
        resulting_list = []

        # $ List own dependencies
        dependencies_list = libobj.get_depends()
        if (dependencies_list is None) or (len(dependencies_list) == 0):
            if initial_call:
                self.__search_dependencies_mutex.release()
            return None
        resulting_list += dependencies_list

        # $ Recurse
        for _libname_ in dependencies_list:
            if _libname_ in self.__libs_already_recursed_for_dependencies:
                continue
            # Find libobj belonging to _libname_
            if _libname_ not in self.__unfiltered_merged_libs:
                purefunctions.printc(
                    f"ERROR: Cannot find {q}{_libname_}{q} while "
                    f"listing dependencies!\n\n",
                    color="error",
                )
                continue
            found_libobj = self.get_libobj_from_merged_libs(
                libname=_libname_,
                libversion=None,
                origins=origins_to_look_into,
            )
            temp = self.list_dependencies_recursively(
                libobj=found_libobj,
                initial_call=False,
            )
            if temp is not None:
                resulting_list += temp
            continue

        # $ Return result
        if initial_call:
            self.__search_dependencies_mutex.release()
        if len(resulting_list) == 0:
            return None
        return list(set(resulting_list))

    def show_dependencies_recursively(
        self,
        libobj: _libobj_.LibObj,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """List all dependencies from the given library. If 'libversion' is
        None, select the most recent one online or from harddrive.

        Unlike previous function(s), this one doesn't return a listing, but
        shows them in a popup window!
        """

        def show_dependencies(*args):
            "Show all dependencies of given LibObj()"
            css = purefunctions.get_css_tags()
            red = css["red"]
            green = css["green"]
            grey = css["grey"]
            end = css["end"]
            dependencies: Optional[List[str]] = None
            try:
                dependencies = self.list_dependencies_recursively(
                    libobj=libobj,
                    initial_call=True,
                )
            except Exception as e:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="ERROR",
                    text=str(
                        f"Embeetle experienced an error while figuring out the<br>"
                        f"dependencies for your library. Contact us if this happens<br>"
                        f"again.<br>"
                    ),
                )
                return
            if dependencies is None or len(dependencies) == 0:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/gen/book.png",
                    title_text="DEPENDENCIES",
                    text=str(f"This library has no dependencies."),
                )
                return
            libs_in_project = []
            libs_in_cache = []
            if not data.is_home:
                libs_in_project = self.list_proj_libs_names()
            else:
                libs_in_cache = self.list_cached_libs_names()
            text = str(
                f"Embeetle recursively parsed the {q}library.properties{q} files<br>"
                f"and found the following dependencies:<br>"
            )
            for libname in dependencies:
                line = ""
                if (libname in libs_in_project) or (libname in libs_in_cache):
                    line = f"&nbsp;&nbsp;- {green}" + libname + f"{end}<br>"
                else:
                    comment = "(not in project)"
                    if data.is_home:
                        comment = "(not in cache)"
                    line = (
                        f"&nbsp;&nbsp;- {red}"
                        + libname
                        + f"{end}&nbsp;&nbsp;{grey}{comment}{end}<br>"
                    )
                text += line
                continue
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/book.png",
                title_text="DEPENDENCIES",
                text=text,
            )
            callback(callbackArg) if callback is not None else nop()

        # Make sure all origins are initialized
        origins = self.get_uninitialized_origins()
        if len(origins) > 0:
            self.initialize(
                libtable=None,
                progbar=None,
                origins=origins,
                callback=show_dependencies,
                callbackArg=None,
            )
            return
        show_dependencies()
        return

    #! =======================[ SAMPLE PROJECTS LISTING ]======================== !#
    #! Functions related to listing sample projects.                              !#
    #!                                                                            !#

    def list_sample_sketches(self, libobj: _libobj_.LibObj) -> Optional[Dict]:
        """List all sample projects (sketch files) found for the given LibObj()-
        instance in a dictionary.

        :param libobj: The LibObj() representing the library to list sample
                       projects from

        Below is the dictionary taken from the sample projects at
        '~/.embeetle/libraries/Heltec_ESP32_Dev-Boards/examples/':
        ┌──────────────────────────────────────────────────────────────────────┐
        │ {                                                                    │
        │     'Low_Power'        : 'Low_Power.ino',                            │
        │     'TimeNTP_ESP32WiFi': 'TimeNTP_ESP32WiFi.ino',                    │
        │     'ESP32':                                                         │
        │     {                                                                │
        │         'ADC_Read_Voltage':                                          │
        │         {                                                            │
        │             'ADC_Read_Accurate': 'ADC_Read_Accurate.ino',            │
        │             'ADC_Read_Simple'  : 'ADC_Read_Simple.ino',              │
        │             'Battery_power'    : 'Battery_power.ino',                │
        │         },                                                           │
        │        'ESP32_Dual_Core':                                            │
        │        {                                                             │
        │            'Movecore' : 'Movecore.ino',                              │
        │            'Showcore' : 'Showcore.ino',                              │
        │            'SpeedTest': 'SpeedTest.ino',                             │
        │        },                                                            │
        │     },                                                               │
        │     'Factory_Test':                                                  │
        │     {                                                                │
        │         'WIFI_Kit_32_FactoryTest'        : 'WIFI_Kit_32_FactoryTest.ino',
        │         'WiFi_LoRa_32FactoryTest'        : 'WiFi_LoRa_32FactoryTest.ino',
        │         'Wireless_Stick_FactoryTest'     : 'Wireless_Stick_FactoryTest.ino',
        │         'Wireless_Stick_Lite_FactoryTest': 'Wireless_Stick_Lite_FactoryTest.ino',
        │     },                                                               │
        │     ...                                                              │
        │ }                                                                    │
        └──────────────────────────────────────────────────────────────────────┘
        """
        assert self.is_initialized(["local_abspath"])
        assert libobj.get_origin() == "local_abspath"
        if libobj.get_local_abspath() is None:
            purefunctions.printc(
                f"ERROR: Library {libobj.get_name()} has no local abspath!",
                color="error",
            )
            return None
        examples_folder = _pp_.rel_to_abs(
            rootpath=libobj.get_local_abspath(),
            relpath="examples",
        )
        if not os.path.isdir(examples_folder):
            return None
        found_sketch_files = []
        for dirpath, dirs, files in os.walk(examples_folder):
            for f in files:
                if f.endswith(".ino"):
                    found_sketch_files.append(
                        _pp_.rel_to_abs(
                            rootpath=dirpath,
                            relpath=f,
                        )
                    )

        sketch_dict = {}
        for sketch_file in found_sketch_files:
            # Compute the relative path to the sketch file,
            # starting from the 'examples' folder.
            sketch_file_relpath = _pp_.abs_to_rel(
                rootpath=examples_folder,
                abspath=sketch_file,
            )
            # Cut the relative path in pieces.
            sketch_cut = sketch_file_relpath.split("/")

            # Throw away the subfolders named 'examples', but
            # don't throw away their content. Act as if the
            # content is moved up one level.
            # sketch_cut = [
            #     cutout for cutout in sketch_cut if cutout.lower() != 'examples'
            # ]
            # => It was a nice idea, but makes it far more difficult
            #    to reconstruct the original sketch abspath later.

            # Fill the 'sketch_dict' hierarchically.
            subdict = sketch_dict
            for i in range(len(sketch_cut) - 1):
                if i == len(sketch_cut) - 2:
                    subdict[sketch_cut[i]] = sketch_cut[i + 1]
                    break
                if sketch_cut[i] not in subdict:
                    subdict[sketch_cut[i]] = {}
                if isinstance(subdict[sketch_cut[i]], dict):
                    subdict = subdict[sketch_cut[i]]
                else:
                    # The 'ArduinoMenu' Library caused an issue, ending up here. It has the
                    # following sketches:
                    #  - adafruitGfx_eTFT/TFT_eSPI/TFT_eSPI.ino
                    #  - adafruitGfx_eTFT/TFT_eSPI/ArduinoMenu_LilyGo_TTGO_T-display_demo/ArduinoMenu_LilyGo_TTGO_T-display_demo.ino
                    # I implemented a workaround here:
                    # 'beetle_core/dashboard/items/lib_items/lib_item_shared.py' line 611
                    pass
                continue
            continue
        return sketch_dict

    # ^                                    DOWNLOAD, MOVE, COPY                                        ^#
    # % ============================================================================================== %#
    # % These functions are intended to download and copy/replace libraries.                           %#
    # %                                                                                                %#

    def add_zipped_library(
        self,
        zipped_libfile: str,
        target_libcollection_dir: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        :param zipped_libfile: Absolute path to the zip-file containing the library.

        :param target_libcollection_dir: Absolute path to the folder where the library will end up
                                         as a subfolder.
        """
        # * Define all paths
        # These are all the parameters and other defined paths:
        # SOURCE:
        # > zipped_libfile                 => Zip-file containing the library,
        #   [param]                           eg. '<usr>/Downloads/foolib.7z'
        # TARGET:
        # > target_libcollection_dir       => Folder where the library ends up as a subfolder(!),
        #   [param]                           eg. 'C:/../my_project/libraries'
        # > target_libdir                  => Folder where the library ends up,
        #                                     eg. 'C:/../my_project/libraries/foolib'
        # CACHE:
        # > dot_embeetle_libcollection_dir => Cache-folder where the library ends up as a
        #                                     subfolder(!),
        #                                     eg. '<usr>/.embeetle/libraries'
        # > dot_embeetle_libdir            => Cache-folder where the library ends up,
        #                                     eg. '<usr>/.embeetle/libraries/foolib'
        # OTHER:
        # > rootpath_list                  => The list of rootpaths known to the project. Only
        #                                     applicable in Project-mode.
        libname: Optional[str] = None
        target_libdir: Optional[str] = None
        dot_embeetle_libcollection_dir: str = (
            self.get_potential_libcollection_folder("dot_embeetle")
        )
        dot_embeetle_libdir: Optional[str] = None
        library_existed: bool = False
        try:
            libname = self.__get_libname_from_zipped_library(
                zipped_libfile=zipped_libfile,
            )
            dot_embeetle_libdir: Optional[str] = _pp_.rel_to_abs(
                rootpath=dot_embeetle_libcollection_dir,
                relpath=libname,
            )
            target_libdir = _pp_.rel_to_abs(
                rootpath=target_libcollection_dir,
                relpath=libname,
            )
            if os.path.isdir(target_libdir):
                library_existed = True
        except:
            traceback.print_exc()
            libname = None
            dot_embeetle_libdir = None
            target_libdir = None

        def abort(reason: Optional[str] = None, *args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if reason is not None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="WARNING",
                    text=reason,
                )
            callback(False, callbackArg)
            return

        def finish(*args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(True, callbackArg)
            return

        # * ----------------[ STEP 1: Check input parameters ]---------------- *#
        # Perform all kinds of checks on the validity of the input parameters.

        # $ Basic checks
        # Variables 'libname', 'dot_embeetle_libdir' and 'target_libdir' are already determined by
        # now. Check if they are None.
        if (
            (libname is None)
            or (dot_embeetle_libdir is None)
            or (target_libdir is None)
        ):
            abort(
                f"Please select a valid library zipfile and a valid target<br>"
                f"folder where the library will be unzipped.<br>"
            )
            return

        # $ Check chosen zipfile
        # Check if the chosen zipfile exists.
        if not os.path.isfile(zipped_libfile):
            purefunctions.printc(
                f"\nERROR: Invalid library zipfile slipped through the "
                f"wizard: {q}{zipped_libfile}{q}\n",
                color="error",
            )
            abort("Please select a valid library zipfile.")
            return
        # Check if the chosen zipfile is actually a zipfile.
        if not (
            zipped_libfile.endswith(".zip") or zipped_libfile.endswith(".7z")
        ):
            purefunctions.printc(
                f"\nERROR: Invalid library zipfile slipped through the "
                f"wizard: {q}{zipped_libfile}{q}\n",
                color="error",
            )
            abort(f"Please select a valid library zipfile.")
            return

        # $ Check chosen target libcollection folder
        # Check if the chosen target libcollection folder exists.
        if not os.path.isdir(target_libcollection_dir):
            purefunctions.printc(
                f"\nERROR: Invalid library libcollection folder slipped "
                f"through the wizard: {q}{target_libcollection_dir}{q}\n",
                color="error",
            )
            abort(
                f"Please check if you have write access to this folder:<br>"
                f"{q}{target_libcollection_dir}{q}<br>"
            )
            return
        # For project mode, check if the chosen target libcollection folder is inside the project.
        if not data.is_home:
            if not any(
                target_libcollection_dir.startswith(_rootpath)
                for _rootpath in data.current_project.get_all_rootpaths()
            ):
                purefunctions.printc(
                    f"\nERROR: Invalid library libcollection folder slipped "
                    f"through the wizard: {q}{target_libcollection_dir}{q}\n",
                    color="error",
                )
                abort(
                    f"Please select a valid subfolder inside your project<br>"
                    f"to store the unzipped library.<br>"
                )
                return

        # * -------[ STEP 2: Ask overwrite permission (if applicable) ]------- *#
        # Ask permission to overwrite the library if it already exists at the target location.
        if not os.path.exists(target_libdir):
            assert not library_existed
        else:
            assert library_existed
            assert os.path.exists(target_libdir)
            css = purefunctions.get_css_tags()
            text = f"""
                The library already exists in:<br>
                {css['tab']}{css['green']}{target_libdir}{css['end']}<br>
                This library will be replaced with the one you are<br>
                going to unzip now. Click OK to continue.<br>
                <br>
                Click CANCEL to go back.
            """
            ok, _ = gui.dialogs.popupdialog.PopupDialog.ok_cancel(
                icon_path="icons/gen/book.png",
                title_text="Library already exists",
                text=text,
            )
            if ok != qt.QMessageBox.StandardButton.Ok:
                abort(None)
                return

        # * -----------[ STEP 3: Unzip into cache (and project) ]------------- *#
        # Both in home and project mode - the library needs to be unzipped first into the cache fol-
        # der. In home mode that's all. In project mode, the library should then be copied into the
        # project.

        # & -----------------[ PROCESS HOME MODE ]------------------ *#
        # Unzip into the cache folder. Then refresh the home libraries tab.
        if data.is_home:

            def refresh_hometab(success: bool, *args) -> None:
                "[main thread]"
                assert threading.current_thread() is threading.main_thread()
                assert data.is_home
                assert (
                    target_libcollection_dir == dot_embeetle_libcollection_dir
                )
                if not success:
                    # Cache unzip failed.
                    abort("An error occured while unzipping the library.")
                    return
                # The LibManager()-singleton 'refresh()' method goes one step further for the Home Win-
                # dow than it does for the Project Window. For the Project Window, this refresh() method
                # wouldn't visualize new LibObj()s in the dashboard, as this is taken care of by the
                # LibSeg()-instance, see 'lib_seg.py' > 'trigger_dashboard_refresh()'.
                # For the Home Window, the LibManager()-singleton goes all-the-way in the 'refresh()'
                # method, triggering a complete refresh of the LIBRARIES tab in the end.
                self.refresh(
                    origins=["local_abspath"],
                    callback=finish,
                    callbackArg=None,
                )
                return

            # Unzip into the cache folder.
            self.__unzip_library_to_dotembeetle(
                zipped_libfile=zipped_libfile,
                callback=refresh_hometab,
                callbackArg=None,
            )
            return

        # & ----------------[ PROCESS PROJECT MODE ]---------------- *#
        # Unzip into the cache folder. Then:
        #     - Copy the cached library into the project (without samples).
        #     - Refresh the Filetree (no longer needed).
        #     - Refresh the Dashboard.
        #     - Modify the corresponding icons in the Filetree (ignored for now).
        assert not data.is_home

        def copy_into_project(success: bool, *args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            assert target_libcollection_dir != dot_embeetle_libcollection_dir
            if not success:
                # Cache unzip failed.
                purefunctions.printc(
                    "ERROR: Could not unzip the library.",
                    color="error",
                )
                abort("An error occured while unzipping the library.")
                return
            self.__copy_local_library(
                libpath=dot_embeetle_libdir,
                targetpath=target_libdir,
                exclude_samples=True,
                callback=refresh_dashboard,
                callbackArg=None,
            )
            return

        def refresh_dashboard(*args) -> None:
            "[main thread]"
            # This function actually not only refreshes the dashboard, but also updates the
            # 'proj_relpath' part of the database!
            # But how?
            #   -> lib_seg.trigger_dashboard_refresh()
            #   -> lib_seg.update_states()
            #   -> LibManager().refresh(['proj_relpath'],)
            assert threading.current_thread() is threading.main_thread()
            data.current_project.refresh_all_lib_segs(
                callback=finish,
                callbackArg=None,
            )
            return

        # Unzip into the cache folder.
        self.__unzip_library_to_dotembeetle(
            zipped_libfile=zipped_libfile,
            callback=copy_into_project,
            callbackArg=None,
        )
        return

    def download_or_copy_libraries(
        self,
        selected_libobjs: Dict[int, _libobj_.LibObj],
        target_libcollection_dir: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """SUMMARY ======= This function will download or copy the selected
        libraries into the cache folder. If invoked in project mode, the
        selected libraries will *also* be copied into the project. This func-

        tion should run:
            - At the end of the library wizard.
            - When the user updates a library.

        It will also list the dependencies with the request to download/copy them too, as well as
        the incompatibilities with the choice to cancel the whole operation.

        PARAMETERS
        ==========
        :param selected_libobjs: Dictionary of all selected LibObj()s that are to be added. Keys are
                                 the row numbers in the library wizard.

        :param target_libcollection_dir: Eventual location for the libraries to end up. In home
                                         mode, this parameter should be equal to the cache folder.

        ABOUT THE GIVEN LIBOBJ()S DICTIONARY
        ====================================
        - The LibObj()s in this 'selected_libobjs' dictionary should be from one of these origins:
              > 'zip_url'
              > 'local_abspath'
          Their corresponding libraries will be downloaded/copied into the cache *and* the 'target_
          libcollection_dir' folder (in home mode both are equal).

        - The keys from 'selected_libobjs' are only relevant if called from a wizard. However, don't
          provide negative keys. They are reserved for additional LibObj()s for the dependencies.

        - The 'selected_libobjs' dictionary will be expanded with additional LibObj()s if the user
          agrees to add dependencies. These LibObj()s are searched for in the merged database. As
          their row numbers in the wizard are not known, they get negative row numbers as keys.

        ABOUT THE TARGET LOCATION
        =========================
        The 'target_libcollection_dir' represents the location where all given libraries will end up.
        It can be:
            > 'C:/Users/Kristof/.embeetle/libraries'
            > 'C:/../my_project/source/libraries'
            > 'C:/../ext_folder/libraries'

        In the first case, the libraries will just be unzipped/copied into the cache folder. In the
        latter case, they wil *also* be copied to the project (excluding the samples).

        CALLBACK
        ========
        The function ends with:
            > callback(success, callbackArg)
        """
        # * Define all paths
        # List of all libraries that some of the chosen ones depend on. Only library names are
        # listed.
        dependencies_list: List[str] = []
        # The path to '~/.embeetle/libraries'
        dot_embeetle_libcollection_dir = _pp_.rel_to_abs(
            rootpath=data.settings_directory, relpath=f"libraries"
        )
        css = purefunctions.get_css_tags()

        def abort(reason: Optional[str] = None, *args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if reason is not None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="WARNING",
                    text=reason,
                )
            if callback is not None:
                callback(False, callbackArg)
            return

        def finish(*args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(True, callbackArg)
            return

        # * ----------------[ STEP 1: Check input parameters ]---------------- *#
        # Perform all kinds of checks on the validity of the input parameters.

        # $ Basic checks
        if target_libcollection_dir is None:
            abort(
                f"Please select a valid target folder where the library<br>"
                f"will be unzipped.<br>"
            )
            return

        # $ Check chosen target libcollection folder
        # For home mode, check if the chosen target libcollection folder equals the cache.
        if data.is_home:
            if target_libcollection_dir != dot_embeetle_libcollection_dir:
                print(
                    f"\nThe function {q}download_or_copy_libraries(){q} was invoked "
                    f"for the Home Window, but the given target path doesn{q}t point "
                    f"to the cache folder."
                )
                abort(
                    f"\nThe function {q}download_or_copy_libraries(){q} was invoked<br>"
                    f"for the Home Window, but the given target path doesn{q}t point<br>"
                    f"to the cache folder."
                )
                return
        # For project mode, check if the chosen target libcollection folder is inside the project.
        if not data.is_home:
            if not any(
                target_libcollection_dir.startswith(_rootpath)
                for _rootpath in data.current_project.get_all_rootpaths()
            ):
                purefunctions.printc(
                    f"\nERROR: Invalid library libcollection folder slipped "
                    f"through the wizard: {q}{target_libcollection_dir}{q}\n",
                    color="error",
                )
                abort(
                    f"Please select a valid subfolder inside your project<br>"
                    f"to store the unzipped library.<br>"
                )
                return

        # * ------[ STEP 2a: Ask overwrite permission (if applicable) ]------- *#
        # Ask permission to overwrite the library if it already exists at the target location.

        # * ----[ STEP 2b: List dependencies and show incompatibilities ]----- *#
        # & LIST DEPENDENCIES
        # List all the dependencies from the given (selected) LibObj()s, in the form of a list-of-
        # libnames. After listing and filtering them, ask the user if he agrees to download all of
        # them.

        # $ List all dependencies
        # First list *all* the dependencies. Don't mind for now if they already exist in the project
        # (project mode) or in cache (home mode), or if the user has selected already some of them
        # in the wizard to be downloaded/copied.
        for r, libobj in selected_libobjs.items():
            temp: Optional[List[str]] = self.list_dependencies_recursively(
                libobj=libobj,
                initial_call=True,
            )
            if temp is not None:
                dependencies_list += temp

        # $ Remove dependencies that are already fulfilled
        # Now it's time to filter the dependencies list.
        existing_libnames: Optional[List[str]] = None
        # List those that are already in the project (project mode) or cache (home mode).
        if not data.is_home:
            # Project mode
            existing_libnames = self.list_proj_libs_names()
        else:
            # Home mode
            existing_libnames = self.list_cached_libs_names()
        # List those that are already selected
        for r, libobj in selected_libobjs.items():
            existing_libnames.append(libobj.get_name())
        # Do the removal
        for i, libname in reversed(list(enumerate(dependencies_list))):
            if libname in existing_libnames:
                del dependencies_list[i]
        # At this point, the 'dependencies_list' should only contain the library names of missing(!)
        # dependencies.

        # $ Ask user about missing dependencies
        # If the user agrees, the LibObj()s corresponding to the missing dependencies will be looked
        # up from the merged database and added to the 'selected_libobjs' dictionary (see parameter)
        # with negative keys. This will have the same effect as if the user had selected all the
        # dependencies manually in the wizard.
        if len(dependencies_list) > 0:
            text: str = ""
            if not data.is_home:
                text = f"""
                    The library(ies) you selected depend on others that are<br>
                    not yet in your project. Do you want to download them?<br>
                    Dependencies:<br>
                """
            else:
                text = f"""
                    The library(ies) you selected depend on others that are<br>
                    not yet stored by Embeetle. Do you want to download<br>
                    them?<br>
                    Note: default libraries storage place is:<br>
                    {css['green']}{q}{target_libcollection_dir}{q}{css['end']}<br>
                    <br>
                    Dependencies:<br>
                """
            _green = css["green"]
            for libname in dependencies_list:
                text += f"&nbsp;&nbsp;- {_green}{libname}</span><br>"

            reply = gui.dialogs.popupdialog.PopupDialog.question(
                parent=data.main_form,
                title_text="DOWNLOAD DEPENDENCIES?",
                icon_path="icons/gen/book.png",
                text=text,
            )
            if reply == qt.QMessageBox.StandardButton.Yes:
                for r, libname in enumerate(dependencies_list):
                    libobj = self.get_libobj_from_merged_libs(
                        libname=libname,
                        libversion=None,
                        origins=["zip_url", "local_abspath"],
                    )
                    # Give these LibObj()s a negative row number, to avoid overwriting other ones!
                    # Also avoid r == 0.
                    if libobj is not None:
                        n = -(r + 1)
                        if n in selected_libobjs.keys():
                            raise RuntimeError(
                                f"Cannot add library {q}{libname}{q}, its "
                                f"key {n} was already taken!"
                            )
                        selected_libobjs[n] = libobj
                    else:
                        purefunctions.printc(
                            f"\nERROR: Coud not find a LibObj() for "
                            f"{q}{libname}{q}\n",
                            color="error",
                        )
                    continue
            else:
                # Do not add the dependencies - just continue
                pass
        # At this point, there are either no dependencies, or they have all been handled - their
        # LibObj()s are added to the 'selected_libobjs' parameter.

        # & LIST INCOMPATIBLE LIBRARIES
        # This part doesn't change anything in the 'selected_libobjs' dictionary. Nor does it make
        # any changes elsewhere (eg. database, harddrive, ..). It's a simple check on each selected
        # LibObj() to see if it is compatible with the project (project mode) or with Embeetle it-
        # self (home mode). The user is warned and has the option to abort the whole download/copy
        # procedure before it even took place.

        # $ List incompatible libraries
        incompatible_libobjs = []
        if data.is_home:
            # Home mode
            for r, libobj in selected_libobjs.items():
                if libobj is None:
                    continue
                if not chip_exists_compatible_with_lib_archs(
                    libobj.get_architectures()
                ):
                    incompatible_libobjs.append(libobj)
                continue
        else:
            # Project mode
            for r, libobj in selected_libobjs.items():
                if libobj is None:
                    continue
                if not is_chip_compatible_with_lib_archs(
                    chip_unicum=data.current_project.get_chip().get_chip_unicum(),
                    archs=libobj.get_architectures(),
                ):
                    incompatible_libobjs.append(libobj)
                continue

        # $ Ask user about incompatible libraries
        if len(incompatible_libobjs) > 0:
            if data.is_home:
                text = f"""
                    Some of the libraries you selected are only compatible<br>
                    with microcontrollers that Embeetle doesn{q}t support yet.<br>
                    Do you want to continue?<br>
                    Incompatible libraries:<br>
                """
            else:
                text = f"""
                    Some of the libraries you selected are not compatible<br>
                    with the microcontroller from your current project:<br>
                    {css['tab']}{q}{data.current_project.get_chip().get_name()}{q}<br>
                    Do you want to continue?<br>
                    Incompatible libraries:<br>
                """
            _red = css["red"]
            for libobj in incompatible_libobjs:
                text += f"&nbsp;&nbsp;- {_red}{libobj.get_name()}</span><br>"
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                parent=data.main_form,
                title_text="CONTINUE WITH INCOMPATIBLE LIBRARIES?",
                icon_path="icons/gen/book.png",
                text=text,
            )
            if reply != qt.QMessageBox.StandardButton.Yes:
                abort()
                return
        # Reaching this point means that there are either no incompatibilities or the user was stub-
        # born and continued nonetheless.

        # * ----[ STEP 3: Download/Copy/Unzip into cache (and project) ]------ *#
        # Both in home and project mode - the libraries need to be downloaded/copied/unzipped first
        # into the cache folder. In home mode that's all. In project mode, the library should then
        # be copied into the project.

        # & -----------------[ PROCESS HOME MODE ]------------------ *#
        # Iterate over the LibObj()s from the 'selected_libobjs' dictionary. Download/Copy/Unzip the
        # corresponding libraries into the cache folder. Then update the Home Window when iteration
        # stops.
        if data.is_home:

            def process_next_libobj_for_hometab(
                success: bool,
                libobj_iter: Iterator[_libobj_.LibObj],
                *args,
            ) -> None:
                "[main thread]"
                assert threading.current_thread() is threading.main_thread()
                assert data.is_home
                assert (
                    target_libcollection_dir == dot_embeetle_libcollection_dir
                )
                if not success:
                    purefunctions.printc(
                        f"\nERROR: The previous library could not be processed.\n",
                        color="error",
                    )
                    abort()
                    return
                try:
                    _libobj = next(libobj_iter)
                except StopIteration:
                    update_hometab()
                    return
                _libname = _libobj.get_name()
                _libversion = _libobj.get_version()
                _liburl = _libobj.get_zip_url()
                _libpath = _libobj.get_local_abspath()
                _liborigin = _libobj.get_origin()
                emb_targetpath = _pp_.rel_to_abs(
                    rootpath=dot_embeetle_libcollection_dir,
                    relpath=_libname.replace(" ", "_"),
                )

                # $ ONLINE
                # Selected LibObj() represents an online library.
                if _liborigin == "zip_url":
                    self.__download_and_unzip_library(
                        liburl=_liburl,
                        targetpath=emb_targetpath,
                        callback=process_next_libobj_for_hometab,
                        callbackArg=libobj_iter,
                    )
                    return

                # $ LOCAL
                # Selected LibObj() represents a local library.
                assert _libpath is not None
                assert _liborigin == "local_abspath"
                self.__copy_local_library(
                    libpath=_libpath,
                    targetpath=emb_targetpath,
                    exclude_samples=True,
                    callback=process_next_libobj_for_hometab,
                    callbackArg=libobj_iter,
                )
                return

            def update_hometab(*args) -> None:
                "[main thread]"
                # The LibManager()-singleton 'refresh()' method goes one step further for the Home
                # Window than it does for the Project Window. For the Project Window, this refresh()
                # method wouldn't visualize new LibObj()s in the dashboard, as this is taken care of
                # by the LibSeg()-instance, see 'lib_seg.py' > 'trigger_dashboard_refresh()'.
                # For the Home Window, the LibManager()-singleton goes all-the-way in the method
                # 'refresh()', triggering a complete refresh of the LIBRARIES tab in the end.
                assert threading.current_thread() is threading.main_thread()
                assert (
                    target_libcollection_dir == dot_embeetle_libcollection_dir
                )
                self.refresh(
                    origins=["local_abspath"],
                    callback=finish,
                    callbackArg=None,
                )
                return

            # Iterate over the LibObj()s
            process_next_libobj_for_hometab(
                True, iter([libobj for r, libobj in selected_libobjs.items()])
            )
            return

        # & ----------------[ PROCESS PROJECT MODE ]---------------- *#
        # Iterate over the LibObj()s from the 'selected_libobjs' dictionary. For each of them:
        #     - Download/Copy/Unzip the library into the cache folder *and* into the project
        #       (without samples).
        #     - Refresh the Filetree (used to happen after each single library addition, but is no
        #       longer needed).
        # When iteration stops:
        #     - Refresh the Dashboard.
        #     - Modify the corresponding icons in the Filetree (ignored for now).
        assert not data.is_home
        assert target_libcollection_dir != dot_embeetle_libcollection_dir

        def process_next_libobj_for_project(
            success: bool,
            arg: Tuple[
                Optional[_libobj_.LibObj],
                Optional[bool],
                Iterator[_libobj_.LibObj],
            ],
            *args,
        ) -> None:
            "[main thread]"
            # Process the next LibObj() from the 'selected_libobjs' dictionary: download/copy the
            # corresponding library into the cache folder and into the requested location in the
            # project.
            assert threading.current_thread() is threading.main_thread()

            # $ CHECK PREVIOUS OPERATION
            # The LibObj() handled in the previous operation, its success and whether or not that
            # library pre-existed in the project, can all be extracted from the 'arg' parameter:
            #     - success:            The previous operation succeeded.
            #     - _prev_libobj:       The LibObj() processed in the previous round.
            #     - _prev_lib_existed:  The previously downloaded/copied/unzipped library already
            #                           existed in the project before said procedure.
            #     - _libobj_iter:       The remaining LibObj()s to iterate over.
            _prev_libobj, _prev_lib_existed, _libobj_iter = arg
            if not success:
                # Previous operation failed. Report failure in detail.
                assert _prev_libobj is not None
                assert _prev_lib_existed is not None
                _prev_libname = _prev_libobj.get_name()
                _prev_libversion = _prev_libobj.get_version()
                _prev_liburl = _prev_libobj.get_zip_url()
                _prev_libpath = _prev_libobj.get_local_abspath()
                _prev_liborigin = _prev_libobj.get_origin()
                _prev_emb_targetpath = _pp_.rel_to_abs(
                    rootpath=dot_embeetle_libcollection_dir,
                    relpath=_prev_libname.replace(" ", "_"),
                )
                _prev_proj_targetpath = _pp_.rel_to_abs(
                    rootpath=target_libcollection_dir,
                    relpath=_prev_libname.replace(" ", "_"),
                )
                err_msg = ""
                if _prev_liborigin == "zip_url":
                    err_msg = str(
                        f"The following library failed to download, unzip into\n"
                        f"the cache folder and copy to the project:\n"
                    )
                else:
                    err_msg = str(
                        f"The following local library failed to copy to the\n"
                        f"cache folder and to the project:\n"
                    )
                err_msg += str(
                    f"ERROR: The following library failed to download, unzip into\n"
                    f"the cache folder and copy to the project:\n"
                    f"    - name:           {_prev_libname}\n"
                    f"    - version:        {_prev_libversion}\n"
                    f"    - url:            {_prev_liburl}\n"
                    f"    - local path:     {_prev_libpath}\n"
                    f"    - origin:         {_prev_liborigin}\n"
                    f"    - cache target:   {_prev_emb_targetpath}\n"
                    f"    - project target: {_prev_proj_targetpath}\n"
                    f"    - library existed already in project: {_prev_lib_existed}\n"
                )
                purefunctions.printc(err_msg, color="error")
                abort(err_msg.replace("\n", "<br>").replace(" ", "&nbsp;"))
                return

            # $ START NEXT OPERATION
            # Extract the next LibObj() from the iterator and start the operation on it.
            try:
                _libobj = next(_libobj_iter)
            except StopIteration:
                # After processing all the LibObj()s, it's time to refresh the Dashboard.
                refresh_dashboard()
                return
            _libname = _libobj.get_name()
            _libversion = _libobj.get_version()
            _liburl = _libobj.get_zip_url()
            _libpath = _libobj.get_local_abspath()
            _liborigin = _libobj.get_origin()
            _emb_targetpath = _pp_.rel_to_abs(
                rootpath=dot_embeetle_libcollection_dir,
                relpath=_libname.replace(" ", "_"),
            )
            _proj_targetpath = _pp_.rel_to_abs(
                rootpath=target_libcollection_dir,
                relpath=_libname.replace(" ", "_"),
            )
            _lib_existed = os.path.isdir(_proj_targetpath)

            # $ ONLINE
            # Selected LibObj() represents an online library. The function '__download_and_unzip_
            # library()' will not only put the library into the final target folder, but also into
            # the cache.
            if _liborigin == "zip_url":
                self.__download_and_unzip_library(
                    liburl=_liburl,
                    targetpath=_proj_targetpath,
                    callback=process_next_libobj_for_project,
                    callbackArg=(_libobj, _lib_existed, _libobj_iter),
                )
                return

            # $ LOCAL
            # Selected LibObj() represents a local library. Copy it first into the cache folder,
            # then into the project.
            assert _libpath is not None
            assert _liborigin == "local_abspath"

            def copy_into_project(_success: bool, *_args) -> None:
                if not _success:
                    # Invoke the encapsulating function, just to ensure a detailed error message
                    # will be printed before aborting everyting.
                    process_next_libobj_for_project(
                        False, (_libobj, _lib_existed, _libobj_iter)
                    )
                    return
                self.__copy_local_library(
                    libpath=_libpath,
                    targetpath=_proj_targetpath,
                    exclude_samples=False,
                    callback=process_next_libobj_for_project,
                    callbackArg=(_libobj, _lib_existed, _libobj_iter),
                )
                return

            # The local library is actually already in the cache.
            # => Just copy it into the project.
            if _libpath.startswith(
                self.get_potential_libcollection_folder("dot_embeetle")
            ):
                copy_into_project(True)
                return

            # The local library is in some other random location.
            # => First copy to cache, then into project.
            self.__copy_local_library(
                libpath=_libpath,
                targetpath=_emb_targetpath,
                exclude_samples=False,
                callback=copy_into_project,
                callbackArg=None,
            )
            return

        def refresh_dashboard(*args) -> None:
            "[main thread]"
            # This subfunction not only refreshes the dashboard, but also updates the 'proj_relpath'
            # part of the database!
            assert threading.current_thread() is threading.main_thread()
            data.current_project.refresh_all_lib_segs(
                callback=finish,
                callbackArg=None,
            )
            return

        process_next_libobj_for_project(
            True,
            (
                None,
                None,
                iter([libobj for r, libobj in selected_libobjs.items()]),
            ),
        )
        return

    def check_for_updates(
        self,
        libobj: _libobj_.LibObj,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Check - for the given LibObj() - if there is a more recent version available online. If so,
        ask the user if he wants to download it to replace his library.

        The given LibObj() can be either from the current project (project mode) or from the cache
        folder (home mode).

            > callback(callbackArg)
        """
        # * Define all paths
        current_version = libobj.get_version()
        libname = libobj.get_name()
        if current_version is None:
            current_version = "none"
        lib_abspath: Optional[str] = None
        lib_relpath: Optional[str] = None
        if libobj.get_origin() == "local_abspath":
            assert data.is_home
            lib_abspath = libobj.get_local_abspath()
            lib_relpath = lib_abspath
        elif libobj.get_origin() == "proj_relpath":
            assert not data.is_home
            lib_abspath = libobj.get_proj_abspath()
            lib_relpath = libobj.get_proj_relpath()
        else:
            assert False, f"libobj.get_origin() = {libobj.get_origin()}"

        def finish(*args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(True, callbackArg)
            return

        def compare_versions(*args) -> None:
            "[main thread]"
            # Compare the most recent remote version with the version of the given LibObj(). If no
            # remote version was found or the found version is not newer, finish the whole opera-
            # tion.
            # Otherwise, offer the user a download. If he confirms, the 'self.__download_and_unzip_
            # library()' method will run.
            assert threading.current_thread() is threading.main_thread()
            remote_version: Optional[str] = self.__get_most_recent_version(
                libname=libname
            )

            # $ No remote version found
            if remote_version is None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="LIBRARY ISSUE",
                    icon_path="icons/gen/book.png",
                    text=str(
                        f"Embeetle could not locate the library in the database:<br>"
                        f"<br>"
                        f"https://downloads.arduino.cc/libraries/library_index.json<br>"
                    ),
                    text_click_func=nop,
                    parent=data.main_form,
                )
                finish()
                return

            # $ Remote version is same as current
            if remote_version.lower() == current_version.lower():
                _ht_.most_recent_version(
                    libname=libname,
                    libversion=current_version,
                )
                finish()
                return

            # $ Ask to download remote version
            answer = _ht_.new_version_available(
                libname=libname,
                current_version=current_version,
                recent_version=remote_version,
                libpath=lib_relpath,
            )
            # $ YES
            if answer == "upgrade":
                url_zipfile = self.get_online_library_zip_url(
                    libname=libname,
                    libversion=remote_version,
                )
                self.__download_and_unzip_library(
                    liburl=url_zipfile,
                    targetpath=lib_abspath,
                    callback=refresh_libobj,
                    callbackArg=None,
                )
                return
            # $ NO
            finish()
            return

        def refresh_libobj(*args) -> None:
            "[main thread]"
            # At this point, we know that a newer version was discovered online and the user gave
            # permission to download it. The 'self.__download_and_unzip_library()' method was invo-
            # ked, so the harddrive operations should be completed.
            # This section will refresh the LibObj() from the overwritten 'library.properties' file.
            # No refreshing in the Dashboard or Home Window takes place yet. Only the LibObj() is
            # taken care of right now.
            assert threading.current_thread() is threading.main_thread()
            propfile_abspath = _pp_.rel_to_abs(
                rootpath=lib_abspath,
                relpath="library.properties",
            )
            # $ 'library.properties' file vanished!
            if not os.path.isfile(propfile_abspath):
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="LIBRARY ISSUE",
                    icon_path="icons/gen/book.png",
                    text=str(
                        f"After replacing your library with the newest version,<br>"
                        f"Embeetle can no longer locate the {q}library.properties{q}<br>"
                        f"file. The library will no longer be visible in the<br>"
                        f"dashboard.<br>"
                    ),
                    text_click_func=nop,
                    parent=data.main_form,
                )
                # Don't return here. Refresh needed!

            # $ Update LibObj() with 'library.properties'
            else:
                success = self.__update_libobj_from_properties_file(
                    filepath=propfile_abspath,
                    libobj=libobj,
                )
                if not success:
                    # The properties file could not be parsed. Nothing was modified in the LibObj().
                    gui.dialogs.popupdialog.PopupDialog.ok(
                        title_text="LIBRARY ISSUE",
                        icon_path="icons/gen/book.png",
                        text=str(
                            f"After replacing your library with the newest version,<br>"
                            f"Embeetle cannot properly parse the {q}library.properties{q}<br>"
                            f"file. Please check if this file follows the conventions for<br>"
                            f"defining a library."
                        ),
                        text_click_func=nop,
                        parent=data.main_form,
                    )
                    # Don't return here. Refresh needed!

            if libobj.get_name() != libname:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="LIBRARY ISSUE",
                    icon_path="icons/gen/book.png",
                    text=str(
                        f"The name of the updated library seems to be different from<br>"
                        f"what it used to be before:<br>"
                        f"{q}{libname}{q} => {q}{libobj.get_name()}{q}<br>"
                        f"<br>"
                        f"This is very unusual behavior. The beetle strongly advises<br>"
                        f"you to close this project and restart it to ensure the library<br>"
                        f"databases are in sync with the new situation!<br>"
                    ),
                    text_click_func=nop,
                    parent=data.main_form,
                )
                # Don't return here. Refresh needed!

            # $ Proceed to refreshing
            if data.is_home:
                refresh_hometab()
                return
            refresh_dashboard()
            return

        # & ---------------------[ PROCESS FOR HOMETAB ]---------------------- *#
        if data.is_home:

            def refresh_hometab(*args) -> None:
                "[main thread]"
                # This LibManager()-singleton 'refresh()' method goes one step further for the Home
                # Window than it does for the Project Window. For the Project Window, this refresh()
                # method wouldn't visualize new LibObj()s in the dashboard, as this is taken care of
                # by the LibSeg()-instance, see 'lib_seg.py' > 'trigger_dashboard_refresh()'.
                # For the Home Window, this LibManager()-singleton goes all-the-way in the method
                # 'refresh()', triggering a complete refresh of the LIBRARIES tab in the end.
                assert threading.current_thread() is threading.main_thread()
                assert data.is_home
                self.refresh(
                    origins=["local_abspath"],
                    callback=finish,
                    callbackArg=None,
                )
                return

        # & ---------------------[ PROCESS FOR PROJECT ]---------------------- *#
        else:

            def refresh_dashboard(*args) -> None:
                "[main thread]"
                # This subfunction actually not only refreshes the dashboard but also updates the
                # 'proj_relpath' part of the database (which is not really needed here, because the
                # said ProjObj() is already modified).
                assert threading.current_thread() is threading.main_thread()
                data.current_project.refresh_all_lib_segs(
                    callback=finish,
                    callbackArg=None,
                )
                return

        # * Start
        # Make sure all origins are initialized.
        origins = self.get_uninitialized_origins()
        if len(origins) > 0:
            self.initialize(
                libtable=None,
                progbar=None,
                origins=origins,
                callback=compare_versions,
                callbackArg=None,
            )
            return
        compare_versions()
        return

    def offer_to_download(
        self,
        libname: str,
        proj_libcollection_folder: Optional[str],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Check - for the given library name - if there is a version available
        online. If so, ask the user if he wants to download it and put it in the
        project and/or cache.

        :param libname:                    Name of library that will be offered
                                           for download.

        :param proj_libcollection_folder:  [Optional] Folder path where this
                                           library will be unzipped if user ac-
                                           cepts offer. Leave empty for Home
                                           Window.
        """
        assert threading.current_thread() is threading.main_thread()
        dot_embeetle_libcollection: Optional[str] = None
        proj_target_folder: Optional[str] = None
        proj_target_folder_shown: Optional[str] = None

        def check_existence(*args) -> None:
            "[main thread]"
            # Try to find the library (as a LibObj()) in the database. Try first
            # the part of the database that lists the online libraries, then the
            # local ones.
            assert threading.current_thread() is threading.main_thread()
            found_libobj = self.get_libobj_from_merged_libs(
                libname=libname,
                libversion=None,
                origins=["zip_url"],
            )
            if found_libobj is None:
                found_libobj = self.get_libobj_from_merged_libs(
                    libname=libname,
                    libversion=None,
                    origins=["local_abspath"],
                )
                if found_libobj is None:
                    gui.dialogs.popupdialog.PopupDialog.ok(
                        parent=data.main_form,
                        title_text="LIBRARY ISSUE",
                        icon_path="icons/gen/book.png",
                        text=str(
                            f"Embeetle could not locate the library {q}{libname}{q}in the<br>"
                            f"database:<br>"
                            f"https://downloads.arduino.cc/libraries/library_index.json<br>"
                            f"<br>"
                            f"Nor in any local folder."
                        ),
                        text_click_func=nop,
                    )
                    finish()
                    return
            qt.QTimer.singleShot(
                50,
                functools.partial(
                    ask_about_found_libobj,
                    found_libobj,
                ),
            )
            return

        def ask_about_found_libobj(
            found_libobj: _libobj_.LibObj, *args
        ) -> None:
            "[main thread]"
            # Ask if the found library must be downloaded/copied. The choice for
            # download vs copy depends on where in the database the LibObj() was
            # found.
            assert threading.current_thread() is threading.main_thread()
            assert found_libobj is not None
            text = ""
            title = ""
            css = purefunctions.get_css_tags()
            blue = css["blue"]
            end = css["end"]

            # * Online
            if found_libobj.get_origin() == "zip_url":
                # $ Home Window
                if data.is_home:
                    title = "DOWNLOAD LIBRARY?"
                    text = str(
                        f"Do you want to download the library {q}{libname}{q}<br>"
                        f"and unzip it into the Embeetle library cache folder?<br>"
                        f"<br>"
                        f"Note: this cache folder is located at:<br>"
                        f"{blue}{q}{dot_embeetle_libcollection}{q}{end}<br>"
                    )
                # $ Project Window
                else:
                    title = "DOWNLOAD LIBRARY?"
                    text = str(
                        f"Do you want to download the library {q}{libname}{q}<br>"
                        f"and unzip it into your project?<br>"
                        f"<br>"
                        f"Note: it will be unzipped into the folder:<br>"
                        f"{blue}{q}{proj_target_folder_shown}{q}{end}<br>"
                    )

            # * Local
            else:
                # $ Home Window
                if data.is_home:
                    title = "COPY LIBRARY?"
                    text = str(
                        f"Do you want to copy the library {q}{libname}{q}<br>"
                        f"and unzip it into the Embeetle library cache folder?<br>"
                        f"<br>"
                        f"The library will be copied from:<br>"
                        f"{blue}{q}{found_libobj.get_local_abspath()}{q}{end}<br>"
                        f"to:<br>"
                        f"{blue}{q}{dot_embeetle_libcollection}{q}{end}<br>"
                    )
                # $ Project Window
                else:
                    title = "COPY LIBRARY?"
                    text = str(
                        f"Do you want to copy the library {q}{libname}{q}<br>"
                        f"and unzip it into your project?<br>"
                        f"<br>"
                        f"The library will be copied from:<br>"
                        f"{blue}{q}{found_libobj.get_local_abspath()}{q}{end}<br>"
                        f"to:<br>"
                        f"{blue}{q}{proj_target_folder_shown}{q}{end}<br>"
                    )
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                parent=data.main_form,
                title_text=title,
                icon_path="icons/gen/book.png",
                text=text,
            )
            if reply == qt.QMessageBox.StandardButton.Yes:
                # YES -> proceed
                process_found_libobj(found_libobj)
                return
            # NO -> abort early
            finish()
            return

        def process_found_libobj(libobj: _libobj_.LibObj) -> None:
            "[main thread]"
            # Invoke the 'download_or_copy_libraries()' function. This is the
            # same function that runs after completing the Library Wizard. It
            # needs a dictionary of libraries, with the keys being row numbers.
            # Just stuff it with the one and only LibObj() we're observing here.
            assert threading.current_thread() is threading.main_thread()
            if data.is_home:
                target_libcollection_dir = dot_embeetle_libcollection
            else:
                target_libcollection_dir = proj_libcollection_folder
            self.download_or_copy_libraries(
                selected_libobjs={
                    0: libobj,
                },
                target_libcollection_dir=target_libcollection_dir,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(callbackArg)
            return

        # * Home Window
        if data.is_home:
            dot_embeetle_libcollection: str = (
                self.get_potential_libcollection_folder("dot_embeetle")
            )

        # * Project Window
        else:
            proj_target_folder: Optional[str] = None
            if proj_libcollection_folder is None:
                raise RuntimeError(
                    f"Param {q}proj_libcollection_folder{q} not given for "
                    f"function {q}offer_to_download(){q}"
                )
            proj_target_folder = _pp_.rel_to_abs(
                rootpath=proj_libcollection_folder,
                relpath=libname.replace(" ", "_"),
            )
            proj_target_folder_shown = (
                data.current_project.abspath_to_prefixed_relpath(
                    abspath=proj_target_folder,
                    double_angle=False,
                    html_angles=True,
                )
            )

        # * Start procedure
        # Make sure all origins are initialized
        origins = self.get_uninitialized_origins()
        if len(origins) > 0:
            self.initialize(
                libtable=None,
                progbar=None,
                origins=origins,
                callback=check_existence,
                callbackArg=None,
            )
            return
        check_existence()
        return

    def __download_and_unzip_library(
        self,
        liburl: str,
        targetpath: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Download the library and unzip it to the '~/.embeetle/libraries'
        folder, so it's cached. Eventually, copy it to the requested location if
        that differs from the cache folder.

        :param liburl: URL to zipped folder online.
        :param targetpath: Absolute path to library in the project. The name of
            the library is already appended to this variable! >
            callback(success, callbackArg)
        """
        assert self.is_initialized(["zip_url", "local_abspath"])
        assert liburl is not None
        libname = targetpath.split("/")[-1]
        dot_embeetle_targetpath = _pp_.rel_to_abs(
            rootpath=data.settings_directory, relpath=f"libraries/{libname}"
        )

        def finish(success: bool, *args) -> None:
            if not success:
                callback(False, callbackArg)
                return
            if targetpath == dot_embeetle_targetpath:
                # It's now in the '~/.embeetle/libraries' folder and that's already the right loca-
                # tion. Time to quit.
                callback(True, callbackArg)
                return
            # Exclude sample projects from the copy if the target is in the current project.
            exclude_samples: bool = False
            if not data.is_home:
                if any(
                    _rootpath in targetpath
                    for _rootpath in data.current_project.get_all_rootpaths()
                ):
                    exclude_samples = True
            self.__copy_local_library(
                libpath=dot_embeetle_targetpath,
                targetpath=targetpath,
                exclude_samples=exclude_samples,
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # Use the most general 'download_and_unzip()' function for this purpose.
        _project_generator_.ProjectDiskGenerator().download_and_unzip(
            urlstr=liburl,
            target_dirpath=dot_embeetle_targetpath,
            erase_if_failed=False,
            callback=finish,
            callbackArg=None,
        )
        return

    @_sw_.run_outside_main("__unzip_library_to_dotembeetle")
    def __unzip_library_to_dotembeetle(
        self,
        zipped_libfile: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Unzip the library to the '~/.embeetle/libraries/' folder. A subfolder
        will be created with the name of the zipfile stripped off its suffix. So
        what you get is:
            '~/.embeetle/libraries/my_lib'

        :param zipped_libfile:  Absolute path to the library zipfile.

        WARNING: The existence of the targetfolder must be checked *before*
        calling this function. This function will simply clean any existing
        targetfolder without notice!

            > callback(success, callbackArg)
        """
        origthread = self.__unzip_library_to_dotembeetle.origthread
        nonmainthread = self.__unzip_library_to_dotembeetle.nonmainthread
        assert origthread is _sw_.get_qthread("main")
        zipped_libfile = zipped_libfile.replace("\\", "/")

        def start(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            # Briefly switch to the main thread
            # just to create a MiniConsole() instance
            # there!
            _sw_.switch_thread_modern(
                qthread=origthread,
                callback=create_miniconsole,
            )
            return

        def create_miniconsole(*args):
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole(
                "Unzip Library to ~/.embeetle/libraries"
            )
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=print_intro,
            )
            return

        def print_intro(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n"
                "UNZIP LIBRARY TO ~/.embeetle/libraries\n"
                "======================================\n",
                "#ad7fa8",
            )
            protocol = None
            if zipped_libfile.endswith(".7z"):
                protocol = ".7z"
            elif zipped_libfile.endswith(".zip"):
                protocol = ".zip"
            else:
                assert False
            # $ Determine (or create) folder
            # $ '~/.embeetle/libraries'
            dot_embeetle_libfolder = self.get_potential_libcollection_folder(
                "dot_embeetle"
            )
            # $ Determine library name
            libname = self.__get_libname_from_zipped_library(zipped_libfile)
            # $ Determine folder
            # $ '~/.embeetle/libraries/my_lib'
            # If it exists, it will be cleaned
            # without notice!
            target_libpath = _pp_.rel_to_abs(
                rootpath=dot_embeetle_libfolder,
                relpath=libname,
            )
            if os.path.isdir(target_libpath):
                success = _fp_.clean_dir(
                    dir_abspath=target_libpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                )
                if not success:
                    abort()
                    return
            elif os.path.isfile(target_libpath):
                success = _fp_.delete_file(
                    file_abspath=target_libpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                )
                if not success:
                    abort()
                    return
            else:
                success = _fp_.make_dir(
                    dir_abspath=target_libpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                )
                if not success:
                    abort()
                    return
            self.__mini_console.sevenunzip_file_to_dir(
                spath=zipped_libfile,
                dpath=target_libpath,
                show_prog=True,
                protocol=protocol,
                callback=finish_unzip,
                callbackArg=None,
                callbackThread=nonmainthread,
            )
            return

        def finish_unzip(arg):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if isinstance(arg, bool):
                success = arg
            else:
                success, _ = arg
            if not success:
                abort()
                return
            finish()
            return

        def abort(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n")
            self.__mini_console.printout(
                f"Embeetle failed to unzip the library to {q}~/.embeetle/libraries{q}.\n",
                "#ad7fa8",
            )
            self.__mini_console.printout(
                "Please copy the contents of this console,\n", "#ffffff"
            )
            self.__mini_console.printout(
                "and paste it in a mail to ", "#ffffff"
            )
            self.__mini_console.printout("info@embeetle.com\n", "#729fcf")
            self.__mini_console.printout(
                "We will try to fix the problem.\n", "#ffffff"
            )
            self.__unzip_library_to_dotembeetle.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return

        def finish(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n\n")
            self.__mini_console.printout("FINISH \n", "#fcaf3e")
            self.__mini_console.printout("-------\n", "#fcaf3e")
            self.__mini_console.printout(
                "Congratulations! You unzipped the library successfully.\n",
                "#73d216",
            )
            self.__mini_console.printout("\n")

            def delayed_finish(*_args):
                "[non-main thread]"
                assert qt.QThread.currentThread() is nonmainthread
                self.__mini_console.close()
                self.__unzip_library_to_dotembeetle.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(500, delayed_finish)
            return

        start()
        return

    @_sw_.run_outside_main("__copy_local_library")
    def __copy_local_library(
        self,
        libpath: str,
        targetpath: str,
        exclude_samples: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Copy the library to the project.

        :param libpath: Absolute path to locally stored library folder.
        :param targetpath: Absolute path to library in the project. The name of
            the library is already appended to this variable!
        :param exclude_samples: Exclude sample folders from the copy. >
            callback(success, callbackArg)
        """
        origthread = self.__copy_local_library.origthread
        nonmainthread = self.__copy_local_library.nonmainthread
        assert origthread is _sw_.get_qthread("main")
        assert qt.QThread.currentThread() is nonmainthread

        def create_miniconsole(*args):
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole(
                "Copy Library to Project"
            )
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=print_intro,
            )
            return

        def print_intro(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n" "COPY LIBRARY TO PROJECT\n" "=======================\n",
                "#ad7fa8",
            )
            copy_to_project()
            return

        def copy_to_project(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            exclusions: Optional[List[str]] = None
            if exclude_samples:
                exclusions = [
                    "examples",
                ]
            self.__mini_console.copy_folder(
                sourcedir_abspath=libpath,
                targetdir_abspath=targetpath,
                exclusions=exclusions,
                show_prog=True,
                delsource=False,
                callback=finish_copy,
                callbackArg=None,
            )
            return

        def finish_copy(success, *args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if not success:
                abort()
                return
            finish()
            return

        def abort(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n")
            self.__mini_console.printout(
                "Embeetle failed to copy the library in your project.\n",
                "#ad7fa8",
            )
            self.__mini_console.printout(
                "Please copy the contents of this console,\n", "#ffffff"
            )
            self.__mini_console.printout(
                "and paste it in a mail to ", "#ffffff"
            )
            self.__mini_console.printout("info@embeetle.com\n", "#729fcf")
            self.__mini_console.printout(
                "We will try to fix the problem.\n", "#ffffff"
            )
            self.__copy_local_library.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return

        def finish(*args):
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n\n")
            self.__mini_console.printout("FINISH \n", "#fcaf3e")
            self.__mini_console.printout("-------\n", "#fcaf3e")
            self.__mini_console.printout(
                "Congratulations! You copied the library successfully.\n",
                "#73d216",
            )
            self.__mini_console.printout("\n")

            def delayed_finish(*_args):
                "[non-main thread]"
                assert qt.QThread.currentThread() is nonmainthread
                self.__mini_console.close()
                self.__copy_local_library.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(500, delayed_finish)
            return

        # Briefly switch to the main thread, just to create a MiniConsole() in-
        # stance there!
        _sw_.switch_thread_modern(
            qthread=origthread,
            callback=create_miniconsole,
        )
        return

    # ^                             HELP FUNCTIONS                                 ^#
    # % ========================================================================== %#
    # % Mostly uncategorized functions.                                            %#
    # %                                                                            %#

    #! ===========================[ PROPERTIES FILE ]============================ !#
    #! Functions related to the 'library.properties' file, eg. parsing, ...       !#
    #!                                                                            !#

    def __parse_properties_file(self, filepath: str) -> Optional[Dict]:
        """Help-function.

        Parse 'library.properties' file and return a helpful dictionary. Return
        None in case of issues.
        """
        # * Sanitize input
        filepath = filepath.replace("\\", "/")
        if (filepath is None) or (not os.path.isfile(filepath)):
            return None
        content = None
        try:
            with open(
                filepath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                content = f.read()
        except Exception as e:
            purefunctions.printc(
                f"\nERROR: Cannot read file {q}{filepath}{q}\n",
                color="error",
            )
            traceback.print_exc()
            return None
        if content is None:
            return None
        if not isinstance(content, str):
            return None
        content = content.replace("\r\n", "\n")

        # * Read lines
        propdict = {}

        def remove_key(key, _line_):
            assert _line_.startswith(key)
            _line_ = _line_[len(key) :]
            _line_ = _line_.strip()
            if not _line_.startswith("="):
                # issue!
                return None
            _line_ = _line_[1:]
            return _line_.strip()

        keys = (
            "name",
            "version",
            "author",
            "maintainer",
            "sentence",
            "paragraph",
            "category",
            "url",
            "architectures",
            "includes",
            "depends",
        )
        for line in content.splitlines():
            line = line.strip()
            for i, k in enumerate(keys):
                if not line.startswith(k):
                    continue
                # key found
                result = remove_key(k, line)
                if result is None:
                    continue
                # key valid (followed by '=')
                if k == "depends":
                    # Extract a list from the result
                    propdict[k] = [
                        e.strip() for e in result.split(",") if e.strip() != ""
                    ]
                elif k == "architectures":
                    # Extract a list from the result
                    if result.strip() == "*":
                        propdict[k] = None
                    else:
                        propdict[k] = [
                            e.strip()
                            for e in result.split(",")
                            if (
                                (e.strip() != "")
                                and (e.strip() != "*")
                                and (e.strip() != '"*"')
                                and (e.strip().lower() != "all")
                            )
                        ]
                else:
                    propdict[k] = result
                break
            continue
        for k in keys:
            if k not in propdict:
                propdict[k] = None

        # * Sanity checks
        if (propdict["name"] is None) or (propdict["name"].lower() == "none"):
            return None
        if (propdict["version"] is None) or (
            propdict["version"].lower() == "none"
        ):
            return None
        if (propdict["author"] is None) or (
            propdict["author"].lower() == "none"
        ):
            return None

        # * Prepare certain values
        # $ URL
        url_content: Optional[str] = (
            propdict["url"] if "url" in propdict else None
        )
        web_url: Optional[str] = None
        zip_url: Optional[str] = None
        if url_content is not None and (
            url_content.endswith(".zip") or url_content.endswith(".7z")
        ):
            web_url = None
            zip_url = url_content
        else:
            web_url = url_content
            zip_url = None
        del propdict["url"]
        propdict["web_url"] = web_url
        propdict["zip_url"] = zip_url

        # $ path
        origin: Optional[str] = None
        local_abspath: Optional[str] = None
        proj_relpath: Optional[str] = None
        libpath: str = os.path.dirname(filepath).replace("\\", "/")
        if libpath.endswith("/"):
            libpath = libpath[0:-1]

        # HOME MODE
        if data.is_home:
            origin = "local_abspath"
            local_abspath = libpath
            proj_relpath = None

        # PROJECT MODE
        else:
            # Local library
            if not any(
                libpath.startswith(_rootpath)
                for _rootpath in data.current_project.get_all_rootpaths()
            ):
                origin = "local_abspath"
                local_abspath = libpath
                proj_relpath = None

            # Project library
            else:
                origin = "proj_relpath"
                local_abspath = None
                try:
                    proj_relpath = (
                        data.current_project.abspath_to_prefixed_relpath(
                            abspath=libpath,
                            double_angle=True,
                            html_angles=False,
                        )
                    )
                except:
                    traceback.print_exc()
                    raise
        assert origin is not None
        propdict["origin"] = origin
        propdict["local_abspath"] = local_abspath
        propdict["proj_relpath"] = proj_relpath
        return propdict

    def __create_libobj_from_propdict(
        self, propdict: Dict
    ) -> Optional[_libobj_.LibObj]:
        """Create a new LibObj() according to the given properties dictionary.

        WARNING
        =======
        If you change anything here, also change the functions:
            - 'modify_from_propdict()' in 'libobj.py'
            - '__update_libobj_from_properties_file()' below
        """
        new_libobj = _libobj_.LibObj(
            name=propdict["name"] if "name" in propdict else "None",
            version=propdict["version"] if "version" in propdict else "None",
            author=propdict["author"] if "author" in propdict else "None",
            sentence=propdict["sentence"] if "sentence" in propdict else "None",
            paragraph=(
                propdict["paragraph"] if "paragraph" in propdict else "None"
            ),
            mod_name=None,
            mod_author=None,
            mod_sentence=None,
            mod_paragraph=None,
            depends=propdict["depends"] if "depends" in propdict else None,
            category=propdict["category"] if "category" in propdict else None,
            web_url=propdict["web_url"] if "web_url" in propdict else None,
            architectures=(
                propdict["architectures"]
                if "architectures" in propdict
                else None
            ),
            proj_relpath=(
                propdict["proj_relpath"] if "proj_relpath" in propdict else None
            ),
            local_abspath=(
                propdict["local_abspath"]
                if "local_abspath" in propdict
                else None
            ),
            zip_url=propdict["zip_url"] if "zip_url" in propdict else None,
            origin=propdict["origin"],
        )
        return new_libobj

    def __create_libobj_from_properties_file(
        self,
        filepath: str,
    ) -> Optional[_libobj_.LibObj]:
        """Parse the 'library.properties' file and return a new LibObj().

        Return None if parsing fails.
        """
        propdict = self.__parse_properties_file(filepath)
        if propdict is None:
            return None
        return self.__create_libobj_from_propdict(propdict)

    def __update_libobj_from_properties_file(
        self,
        filepath: str,
        libobj: _libobj_.LibObj,
    ) -> bool:
        """Parse the 'library.properties' file and modify the given LibObj() ac-
        cordingly.

        Return True if modification worked. False otherwise.
        """
        propdict = self.__parse_properties_file(filepath)
        if propdict is None:
            return False
        libobj.modify(
            name=propdict["name"] if "name" in propdict else "None",
            version=propdict["version"] if "version" in propdict else "None",
            author=propdict["author"] if "author" in propdict else "None",
            sentence=propdict["sentence"] if "sentence" in propdict else "None",
            paragraph=(
                propdict["paragraph"] if "paragraph" in propdict else "None"
            ),
            mod_name=None,
            mod_author=None,
            mod_sentence=None,
            mod_paragraph=None,
            depends=propdict["depends"] if "depends" in propdict else None,
            category=propdict["category"] if "category" in propdict else None,
            web_url=propdict["web_url"] if "web_url" in propdict else None,
            architectures=(
                propdict["architectures"]
                if "architectures" in propdict
                else None
            ),
            proj_relpath=(
                propdict["proj_relpath"] if "proj_relpath" in propdict else None
            ),
            local_abspath=(
                propdict["local_abspath"]
                if "local_abspath" in propdict
                else None
            ),
            zip_url=propdict["zip_url"] if "zip_url" in propdict else None,
            origin=propdict["origin"],
        )
        return True

    def get_name_from_properties_file(self, filepath: str) -> Optional[str]:
        """Just return the name from the given 'library.properties' file. Return
        None if not found.

        USE CASES ========= Used in 'item.py' to figure out quickly the library
        name from a given 'library.properties' file.
        """
        # * Sanitize input
        # Return None in case of error
        if (filepath is None) or (not os.path.isfile(filepath)):
            return None
        # * Read file line-by-line
        try:
            with open(
                filepath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                for cnt, line in enumerate(f):
                    line = line.strip()
                    if line.lower().startswith("name"):
                        line = line[4:]
                        line = line.strip()
                        if not line.startswith("="):
                            # issue!
                            return None
                        line = line[1:]
                        return line.strip()
        except Exception as e:
            purefunctions.printc(
                f"\nERROR: Cannot read file {q}{filepath}{q}.\n",
                color="error",
            )
            traceback.print_exc()
            return None
        # * No name found
        return None

    #! ============================[ UNCATEGORIZED ]============================= !#
    #! Uncategorized functions.                                                   !#
    #!                                                                            !#

    def get_potential_libcollection_folder(
        self,
        name: str,
    ) -> Union[str, List[str], None]:
        """Given a name, this function returns the abspath to the corresponding
        'libraries' folder that contains a *collection* of libraries. This
        folder might or might not exist.

        :param name:    Choose one of these:
                            - 'dot_embeetle'
                            - 'arduino_sketchbook'
                            - 'arduino15'
                            - 'arduino_installation'

        WARNING:
        After invoking this function, please test the returned abspath for existence!

        NOTE:
        For 'arduino15' and 'arduino_installation', this function returns a list of string-paths,
        each of them being a libcollection folder.
        """
        arduino_libcollection_folders: Dict[str, List[str]] = (
            _arduino_locator_.list_arduino_libraries()
        )

        def get_dot_embeetle_libcollection(*args) -> Optional[str]:
            if len(arduino_libcollection_folders["dot_embeetle"]) > 0:
                return arduino_libcollection_folders["dot_embeetle"][0]
            return None

        def get_arduino_sketchbook_libcollection(*args) -> Optional[str]:
            if len(arduino_libcollection_folders["arduino_sketchbook"]) > 0:
                return arduino_libcollection_folders["arduino_sketchbook"][0]
            return None

        def get_arduino15_libcollection(*args) -> List[str]:
            return arduino_libcollection_folders["arduino15"]

        def get_arduino_installdir_libcollection(*args) -> List[str]:
            return arduino_libcollection_folders["arduino_installation"]

        funcs = {
            "dot_embeetle": get_dot_embeetle_libcollection,
            "arduino_sketchbook": get_arduino_sketchbook_libcollection,
            "arduino15": get_arduino15_libcollection,
            "arduino_installation": get_arduino_installdir_libcollection,
        }
        return funcs[name]()

    def get_arduino_installdir(self) -> Optional[str]:
        """Return the absolute path to the Arduino installation on the user's
        computer.

        Return None if not found.
        """
        return _arduino_locator_.find_arduino_installdir()

    def get_arduino15_dir(self) -> Optional[str]:
        """Get the Arduino15 directory, like:

        - 'C:/Users/Kristof/AppData/Local/Arduino15'
        - '~/.arduino15'
        """
        return _arduino_locator_.find_arduino15()

    def __get_libname_from_zipped_library(
        self,
        zipped_libfile: str,
    ) -> str:
        """Get the library name from a zipped library file."""
        libname = zipped_libfile.split("/")[-1]
        if zipped_libfile.endswith(".7z"):
            libname = libname[0:-3]
        elif zipped_libfile.endswith(".zip"):
            libname = libname[0:-4]
        else:
            assert False
        return libname

    def navigate_to_library(self, libobj: _libobj_.LibObj) -> None:
        """Navigate in the Filetree to the library folder represented by the
        given LibObj(). If called from the Home Window, this function will
        navigate to the library in the native file explo- rer.

        MUTEX ===== This function locks itself (not reentrant) while navigating
        to the library folder and blin- king it.
        """
        assert threading.current_thread() is threading.main_thread()
        if not self.__nav_mutex.acquire(blocking=False):
            return
        abspath: Optional[str]
        if libobj.get_origin() == "proj_relpath":
            abspath = libobj.get_proj_abspath()
        elif libobj.get_origin() == "local_abspath":
            abspath = libobj.get_local_abspath()
        else:
            assert False, f"libobj.get_origin() = {libobj.get_origin()}"

        # & Open in Filetree
        if libobj.get_origin() == "proj_relpath":
            assert not data.is_home
            data.filetree.goto_path(abspath)
            self.__nav_mutex.release()
            return

        # & Open in native file explorer
        success = functions.open_file_folder_in_explorer(abspath)
        if not success:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="Problem",
                text=str(f"Failed to open:<br> " f"{q}{abspath}{q}"),
            )
        self.__nav_mutex.release()
        return

    def replace_add_item(
        self,
        category: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Replace the 'Add library' item for the given category in the Home
        Win- dow.

        This is a quick way to ensure that the 'Add library' item always ends up
        at the bottom.
        """
        if category == "Signal Input/Output":
            category = "Signal Input-Output"
        rootitem = self._v_rootItem_dict[category]
        assert category == rootitem.get_name()
        show_immediately: bool = False

        def finish(*args):
            _additem = _lib_add_item_.CategoryAddItem(
                rootdir=rootitem,
            )
            _downloaditem = _lib_add_item_.DownloadItem(
                rootdir=rootitem,
                parent=_additem,
                category=category,
            )
            _additem.add_child(
                child=_downloaditem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _zipitem = _lib_add_item_.ZipItem(
                rootdir=rootitem,
                parent=_additem,
                category=category,
            )
            _additem.add_child(
                child=_zipitem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            rootitem.add_child(
                child=_additem,
                alpha_order=False,
                show=show_immediately,
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        additem: _lib_add_item_.CategoryAddItem = rootitem.get_child_byName(
            "CategoryAddItem"
        )
        if additem is not None:
            show_immediately = True
            additem.self_destruct(
                killParentLink=True,
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return


def is_chip_compatible_with_lib_archs(
    chip_unicum: _chip_unicum_.CHIP,
    archs: Optional[List[str]],
) -> bool:
    """Return True if the given CHIP()-instance is compatible with one of the
    given architectures."""
    if chip_unicum.get_name().lower() == "custom":
        return True
    if archs is None:
        return True
    arduino_params = chip_unicum.get_chip_dict(board=None).get("arduino_params")
    if arduino_params is None:
        return True
    chip_lib_archs = arduino_params.get("library_architectures")
    if chip_lib_archs is None:
        return True
    intersection = list(
        set([a.lower() for a in archs])
        & set([a.lower() for a in chip_lib_archs])
    )
    if len(intersection) > 0:
        return True
    return False


def chip_exists_compatible_with_lib_archs(archs: Optional[List[str]]) -> bool:
    """For the given list of architectures, does Embeetle have a chip that
    matches at least one?"""
    if archs is None:
        return True

    # $ Construct list of all architectures known to Embeetle
    beetle_arch_list = []
    for chip_unicum in _hardware_api_.HardwareDB().list_chips(
        return_unicums=True
    ):
        assert isinstance(chip_unicum, _chip_unicum_.CHIP)
        arduino_params = chip_unicum.get_chip_dict(board=None).get(
            "arduino_params"
        )
        if arduino_params is None:
            continue
        chip_lib_archs = arduino_params.get("library_architectures")
        if chip_lib_archs is None:
            continue
        beetle_arch_list.extend(chip_lib_archs)

    # $ Compute the intersection
    intersection = list(
        set([a.lower() for a in archs])
        & set([a.lower() for a in beetle_arch_list])
    )
    if len(intersection) > 0:
        return True
    return False
