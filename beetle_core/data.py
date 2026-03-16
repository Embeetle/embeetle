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

import qt
import sys
import os
import enum
import pathlib
import threading
import os_checker

from typing import *
from various.kristofstuff import *

if TYPE_CHECKING:
    import project
    import project.project
    import gui
    import gui.forms
    import gui.forms.newfiletree
    import gui.forms.mainwindow
    import gui.forms.homewindow
    import gui.helpers
    import gui.helpers.buttons
    import gui.helpers.advancedcombobox
    import beetle_console
    import beetle_console.serial_console
    import toolmanager
    import toolmanager.toolmanager
    import toolmanager.version_extractor
    import home_toolbox
    import home_toolbox.chassis
    import home_toolbox.chassis.home_toolbox
    import libmanager
    import libmanager.libmanager
    import home_libraries
    import home_libraries.chassis
    import home_libraries.chassis.home_libraries
    import wizards
    import wizards.zipped_lib_wizard
    import wizards.zipped_lib_wizard.zipped_lib_wizard
    import wizards.lib_wizard
    import wizards.lib_wizard.lib_wizard
    import dashboard.chassis.dashboard as _dashboard_
    import new_dashboard.new_dashboard as _new_dashboard_
    import new_dashboard.dashboard_data as _dashboard_data_
    import components
    import components.signaldispatcher


# Constants
DEBUGGER_ENABLED = True
PINCONFIG_ENABLED = False
PIECES_ENABLED = False
NEW_DASHBOARD_ENABLED = True
CHIPCONFIGURATOR_ENABLED = True
ICON_EXPERIMENT = False

# Internet connectivity status
# This flag is set to True if internet connectivity is detected as down
# Functions in serverfunctions.py should check this flag and exit early when True
internet_down = False

# Store the QPainter()
painter: Optional[qt.QPainter] = None

filetree_file_aliases: Dict = {
    "c": ("c",),
    "cpp": ("c++", "cc", "cpp", "cxx"),
    "h": ("h",),
    "hpp": ("h++", "hh", "hpp", "hxx", "H"),
    "txt": ("txt", "text"),
    "bat": ("bat", "batch"),
    "bin": ("bin",),
    "py": ("py", "pyw", "pyi", "scons"),
    "pyx": ("pyx", "pxd", "pxi"),
    "cfg": ("cfg",),
    "ioc": ("ioc",),
    "d": ("d",),
    "elf": ("elf",),
    "btl": ("btl",),
    "git": ("git", "gitignore"),
    "json": ("json",),
    "ld": ("ld", "linkerscript"),
    "md": ("md",),
    "mk": ("make", "mk", "makefile"),
    "o": ("o",),
    "s": ("s", "asm", "S"),
    "lib": ("lib",),
    "tcl": ("tcl",),
    "zip": (
        "zip",
        "7z",
    ),
}

filetree_file_aliases_inv: Dict = {
    a: k for k, v in filetree_file_aliases.items() for a in v
}

h_ext: Tuple = filetree_file_aliases["h"] + filetree_file_aliases["hpp"]
h_dot_ext: Tuple = tuple([f".{el}" for el in h_ext])
c_ext: Tuple = (
    filetree_file_aliases["c"]
    + filetree_file_aliases["cpp"]
    + filetree_file_aliases["s"]
)
c_dot_ext: Tuple = tuple([f".{el}" for el in c_ext])
cfg_ext: Tuple = filetree_file_aliases[
    "mk"
]  # + filetree_file_aliases['ld'] + filetree_file_aliases['cfg'] + filetree_file_aliases['tcl']
cfg_dot_ext: Tuple = tuple([f".{el}" for el in cfg_ext])
illegal_name_symbols: Tuple = ("<", ">", ":", '"', "/", "\\", "|", "?", "*")

mk_dot_ext: Tuple = tuple([f".{el}" for el in filetree_file_aliases["mk"]])
ld_dot_ext: Tuple = tuple([f".{el}" for el in filetree_file_aliases["ld"]])
"""
================================================================================
                                GLOBAL ENUMS
================================================================================
"""


class FileStatus:
    OK = 0
    MODIFIED = 1


class CanSave:
    YES = 0
    NO = 1


class SearchResult:
    NOT_FOUND = None
    FOUND = 1
    CYCLED = 2


class WindowMode:
    THREE = 0
    ONE = 1


class MainWindowSide:
    LEFT = 0
    RIGHT = 1


class ReplType:
    SINGLE_LINE = 0
    MULTI_LINE = 1


class Direction:
    LEFT = 0
    RIGHT = 1


class SpinDirection:
    CLOCKWISE = 0
    COUNTER_CLOCKWISE = 1


class MessageType:
    NORMAL = 0
    ERROR = 1
    WARNING = 2
    SUCCESS = 3
    DIFF_UNIQUE_1 = 4
    DIFF_UNIQUE_2 = 5
    DIFF_SIMILAR = 6


class HexButtonFocus:
    NONE = 0
    TAB = 1
    WINDOW = 2


class NodeDisplayType:
    DOCUMENT = 0
    TREE = 1


class TreeDisplayType:
    NODES = 0
    FILES = 1
    FILES_WITH_LINES = 2


class ProgramState(enum.Enum):
    Unknown = enum.auto()
    Edited = enum.auto()
    Saved = enum.auto()
    Built = enum.auto()
    Flashed = enum.auto()


class FileType(enum.Enum):
    Standard = enum.auto()
    StandardIndicated = enum.auto()
    InsideCompiler = enum.auto()
    ExcludedFromProject = enum.auto()
    OutsideOfProject = enum.auto()


class ApplicationType(enum.Enum):
    Home = enum.auto()
    Project = enum.auto()


class ConsoleType(enum.Enum):
    Standard = enum.auto()
    Make = enum.auto()
    Serial = enum.auto()


"""
================================================================================
                                GLOBAL CONSTANTS
================================================================================
"""


class ReadOnlyDictionary(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError(f"Cannot modify {self.__class__.__name__}")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__  # type: ignore
    popitem = __readonly__  # type: ignore
    clear = __readonly__  # type: ignore
    update = __readonly__  # type: ignore
    setdefault = __readonly__  # type: ignore
    del __readonly__


filelocations = ReadOnlyDictionary(
    {
        FileType.Standard: "standard",
        FileType.StandardIndicated: "standard_indicated",
        FileType.InsideCompiler: "inside_compiler",
        FileType.ExcludedFromProject: "excluded_from_project",
        FileType.OutsideOfProject: "outside_project",
    }
)
"""
================================================================================
                                STORED SETTINGS
================================================================================
Various stored settings for global use. These are the DEFAULT values, override
them in the user configuration file!
"""
# * VARIOUS SETTINGS
# Startup switches
startup_log_libmanager = False
startup_log_toolmanager = False
startup_log_project_load = False
startup_log_project = False
startup_log_pio_engine = False
startup_log_intro_wiz = False
if (
    startup_log_libmanager
    or startup_log_toolmanager
    or startup_log_project_load
    or startup_log_project
    or startup_log_intro_wiz
):
    print(
        f"\n"
        f"Startup procedure logging activated. Switch located at\n"
        f"data.py -> line 343 -> variable {q}startup_log{q}\n"
        f"\n"
    )
source_analysis_only = False
logging_mode = False
debug_mode = False
new_mode = False
makefile_version_new_projects = None
latest_makefile_version_nr = None
heuristics_enabled = True
# Debugging variables
debugging_active = False
# Global referenc to the log display window, so it can be used anywhere.
log_window = None
# Global reference to the Qt application.
application = None
# Global reference to the application type
application_type = None
# Global reference to the main form, either HomeWindow or MainWindow.
main_form: Union[
    gui.forms.mainwindow.MainWindow, gui.forms.homewindow.HomeWindow, None
] = None
# Global reference to the file checker.
filechecker = None
# Global signal dispatcher
signal_dispatcher: Optional[
    components.signaldispatcher.GlobalSignalDispatcher
] = None
# Global booleans to indicate code environment.
is_updater: bool = False
is_home: bool = False
# Show PyQt/QScintilla version that is being used and if running in
# QScintilla compatibility mode
LIBRARY_VERSIONS: str = "PyQt{} / QScintilla{}".format(
    qt.PyQt.QtCore.PYQT_VERSION_STR, qt.PyQt.Qsci.QSCINTILLA_VERSION_STR
)
# Folder color
foldercol: str = "yellow"
# Original color acquired from '.beetle/filetree_config.btl'
origfoldercol: Optional[str] = None


# * DIRECTORY LOCATIONS

# $ BEETLE_CORE
# Unfrozen
beetle_core_directory = os.path.realpath(
    os.path.dirname(os.path.realpath(__file__))
).replace("\\", "/")
if getattr(sys, "frozen", False):
    # frozen (executing via cx_freeze or Nuitka)
    beetle_core_directory = os.path.realpath(
        os.path.dirname(sys.executable)
    ).replace("\\", "/")
# Check if embeetle runs as a cx_freeze executable
# (the path will contain library.zip)
if (
    beetle_core_directory.endswith(".zip")
    or beetle_core_directory.endswith(".7z")
    or beetle_core_directory.endswith(".tar")
):
    beetle_core_directory = os.path.dirname(beetle_core_directory)

# $ USERS DIRECTORY
user_directory = os.path.realpath(str(pathlib.Path.home())).replace("\\", "/")

# $ .EMBEETLE
# User configuration files.
settings_directory = os.path.realpath(
    os.path.join(user_directory, ".embeetle")
).replace("\\", "/")

# $ RESOURCES
resources_directory = os.path.realpath(
    os.path.join(str(beetle_core_directory), "resources")
).replace("\\", "/")

# $ BEETLE_TOOLS
beetle_tools_directory = os.path.realpath(
    os.path.normpath(
        os.path.join(str(settings_directory), "beetle_tools")
    )
).replace("\\", "/")

# $ PROJECT_GENERATOR_FOLDER
beetle_project_generator_folder = os.path.realpath(
    os.path.normpath(
        os.path.join(
            str(beetle_core_directory), "..", "beetle_project_generator"
        )
    )
).replace("\\", "/")

# $ TOPLEVEL FOLDER
embeetle_toplevel_folder = os.path.realpath(
    os.path.normpath(os.path.join(str(beetle_core_directory), ".."))
).replace("\\", "/")

# $ LICENSES
beetle_licenses_directory = os.path.realpath(
    os.path.normpath(os.path.join(str(beetle_core_directory), "..", "licenses"))
).replace("\\", "/")

# $ BEETLE_UPDATER
# Global string with the 'beetle_updater' directory.
beetle_updater_directory = os.path.realpath(
    os.path.normpath(
        os.path.join(
            str(beetle_core_directory),
            "..",
            f"beetle_updater",
        )
    )
)

# $ SYSTEM DIRECTORIES
# 'sys/' directory
sys_directory = os.path.realpath(
    os.path.normpath(os.path.join(str(beetle_core_directory), "..", f"sys/"))
).replace("\\", "/")

# Subdirectories in 'sys/' try flat layout first, then OS-arch-specific, then
# OS-specific
def _find_sys_subdir(subdir: str) -> str:
    _root = os.path.realpath(
        os.path.normpath(os.path.join(str(beetle_core_directory), ".."))
    ).replace("\\", "/")
    _candidates = [
        f"{_root}/sys/{subdir}",
        f"{_root}/sys/{os_checker.get_os_with_arch()}/{subdir}",
        f"{_root}/sys/{os_checker.get_os()}/{subdir}",
    ]
    for _candidate in _candidates:
        if os.path.exists(_candidate):
            print(f"INFO: '{subdir}' found at '{_candidate}'")
            return _candidate
    return _candidates[0]

sys_lib = _find_sys_subdir("lib")
sys_bin = _find_sys_subdir("bin")
sys_esa = _find_sys_subdir("esa")

# local keypath
local_keypath = os.path.join(user_directory, ".ssh/id_rsa").replace("\\", "/")



# $ KNOWN HOSTS AND CLIENT ID
# The local file it is downloaded to.
known_hosts_filepath: Optional[str] = None
# The local file it is downloaded to. Only relevant for downstream.
client_id_rsa_filepath: Optional[str] = None

# $ DEFAULT DIRECTORIES
default_project_create_directory: str = ""
default_project_open_directory: str = ""
default_project_import_directory: str = ""


def get_default_project_directory():
    global default_project_create_directory
    if default_project_create_directory is not None and os.path.isdir(
        default_project_create_directory
    ):
        return default_project_create_directory
    else:
        default_project_create_directory = user_directory
        return default_project_create_directory


# $ NON-DELETE FOLDERS
# Some folders should never be deleted! All folders here
# are lowercased, because the comparisons are always done
# on lowercase samples.
important_linux_folders = [
    "/bin",
    "/boot",
    "/cdrom",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib32",
    "/lib64",
    "/libx32",
    "/lost+found",
    "/media",
    "/mnt",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/snap",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
    "/usr/bin",
    "/usr/local/bin",
    "/usr/sbin",
    "/etc/rc.d",
    "/usr/share/doc",
    "/usr/man",
    "/var/log",
    "/var/spool/mail",
    "/usr/lib",
    "/tmp",
    "/boot",
]

important_windows_folders = [
    "/program files",
    "/program files (x86)",
    "/windows",
    "/windows/system32",
    "/windows/winsxs",
    "/system volume information",
    "/appdata/local",
]

# Default user configuration file content
default_config_file_content = '''

##  FILE DESCRIPTION:
##      Normal module with a special name that holds custom user functions/variables.
##      To manipulate the editors/windows, take a look at the QScintilla details at:
##      http://pyqt.sourceforge.net/Docs/QScintilla2
##
##  NOTES:
##      Built-in special function escape sequence: "lit#"
##          (prepend it to escape built-ins like: cmain, set_all_text, lines, ...)

"""
# These imports are optional as they are already imported 
# by the REPL, I added them here for clarity.
import data
import functions
import settings
import helper_forms

# Imported for less typing
from forms import *


# Initialization function that gets executed only ONCE at startup
def first_scan():
    pass

# Example function definition with defined autocompletion string
def delete_files_in_dir(extension=None, directory=None):
    # Delete all files with the selected file extension from the directory
    if isinstance(extension, str) == False:
        print("File extension argument must be a string!")
        return
    if directory is None:
        directory = os.getcwd()
    elif os.path.isdir(directory) == False:
        return
    print("Deleting '{:s}' files in:".format(extension))
    print(directory)
    for file in os.listdir(directory):
        file_extension = os.path.splitext(file)[1].lower()
        if file_extension == extension or file_extension == "." + extension:
            os.remove(os.path.join(directory, file))
            print(" - deleted file: {:s}".format(file))
    print("DONE")
delete_files_in_dir.autocompletion = "delete_files_in_dir(extension=\"\", directory=None)"
"""

'''


# Application icon image that will be displayed on all Qt widgets
application_icon_relpath = "icons_static/beetle_face.png"
application_icon_abspath = ""
# embeetle information image displayed when "About embeetle
# action is clicked in the menubar "Help" menu
about_image = "figures/beetle/beetle_with_chip.png"
# Terminal console program used on GNU/linux
terminal = "lxterminal"
# RSS feed stuff
rss_feed_url = "https://embeetle.com/rss.xml"
rss_feed_cache = os.path.realpath(
    os.path.join(settings_directory, "rss_feed.btl")
).replace("\\", "/")
rss_local_file = os.path.realpath(
    os.path.join(settings_directory, "rss_cache.xml")
).replace("\\", "/")
rss_feed_datetime_format = "%Y.%m.%d %H:%M"
# Function information that is used between modules
global_function_information = {}
# Current theme
theme = None

# Current icon style
# ------------------
# The icon style must be one of the keys from the 'icon_styles' dictionary in 'iconfunctions.py':
# either 'plump_color' or 'plump_color_light'.
icon_style: Optional[str] = None

# Diagnostic cap
diagnostic_cap = 65536
# The style of the toolbar
ribbon_style_toolbar = True
# Redirecting stdout to file flag
redirecting_output = False
# Tab properties for coloring
logodict = {
    "adafruit": "icons/logo/adafruit.png",
    "arduino": "icons/logo/arduino.png",
    "arm": "icons/logo/arm.png",
    "atmel": "icons/logo/microchip-atmel.png",
    "embeetle": "icons/logo/beetle_face.png",
    "bitsquared": "icons/logo/bitsquared.png",
    "espressif": "icons/logo/espressif.png",
    "giga": "icons/logo/giga.png",
    "gnu": "icons/logo/gnu.png",
    "infineon": "icons/logo/infineon.png",
    "linux": "icons/logo/linux.png",
    "maxim": "icons/logo/maxim.png",
    "microchip": "icons/logo/microchip.png",
    "nordic": "icons/logo/nordic.png",
    "nuvoton": "icons/logo/nuvoton.png",
    "nxp": "icons/logo/nxp.png",
    "segger": "icons/logo/segger.png",
    "silicon_labs": "icons/logo/silicon_labs.png",
    "sparkfun": "icons/logo/sparkfun.png",
    "stmicro": "icons/logo/stmicro.png",
    "texas_instruments": "icons/logo/ti.png",
    "windows": "icons/logo/windows.png",
}
"""
================================================================================
                                   SCALING
================================================================================
"""
# * GLOBAL SCALE FACTOR
global_scale: float = 100.0


def global_decorator(func):
    def decorator(*args, **kwargs):
        return int(func(*args, **kwargs) * global_scale / 100)

    return decorator


def get_global_scale():
    return global_scale / 100


# ^ 1. TOPLEVEL GROUP
# ===================
# Group includes:
#   - Toplevel menus
#   - Tab headers.
toplevel_font_scale: float = 100.0
toplevel_menu_scale: float = 100.0


@global_decorator
def get_toplevel_menu_pixelsize():
    return int(toplevel_menu_scale * 16 / 100)


@global_decorator
def get_toplevel_font_pointsize():
    return int(toplevel_font_scale * 9 / 100)


def get_toplevel_font() -> qt.QFont:
    font = qt.QFontDatabase.font(
        current_font_name,
        current_font_attributes,
        get_toplevel_font_pointsize(),
    )
    font.setStyleHint(qt.QFont.StyleHint.Monospace)
    return font


def get_toplevel_font_width():
    font = get_toplevel_font()
    font_metric = qt.QFontMetrics(font)
    # .width() of QFontMetrics has been renamed to .horizontalAdvance()
    return font_metric.horizontalAdvance(" ")


def get_toplevel_font_height():
    font = get_toplevel_font()
    font_metric = qt.QFontMetrics(font)
    return font_metric.height()


@global_decorator
def get_general_font_pointsize():
    return int(general_font_scale * 9 / 100)


def get_general_font() -> qt.QFont:
    font = qt.QFontDatabase.font(
        current_font_name, current_font_attributes, get_general_font_pointsize()
    )
    font.setStyleHint(qt.QFont.StyleHint.Monospace)
    return font


def get_general_font_width():
    font = get_general_font()
    font_metric = qt.QFontMetrics(font)
    # .width() of QFontMetrics has been renamed to .horizontalAdvance()
    return font_metric.horizontalAdvance(" ")


def get_general_font_height():
    font = get_general_font()
    font_metric = qt.QFontMetrics(font)
    return font_metric.height()


current_font_name: str = "Fira Code"
current_font_attributes: str = ""
editor_font_name: str = "Fira Code"
editor_font_attributes: str = ""


def get_global_font_family():
    return current_font_name


def get_editor_font() -> qt.QFont:
    return qt.QFontDatabase.font(
        editor_font_name, editor_font_attributes, get_toplevel_font_pointsize()
    )


def get_editor_font_name():
    return editor_font_name


# ^ 2. GENERAL GROUP
# ==================
# Group includes:
#   - Editor
#   - Console
#   - Serial Monitor
#   - Filetree
#   - Dashboard
#   - Search results
general_font_scale: float = 100.0
general_icon_scale: float = 100.0


@global_decorator
def get_general_icon_pixelsize(is_inner: bool = True) -> int:
    """Icons used in Console, Serial Monitor, Filetree and Dashboard.

    :param is_inner:    True => Return the size of the icons.
                        False => Return the size of the button holding the icon.

    The size of the button holding the icon should - in most circumstances - be equal to the icon
    itself. However, if the font size is pretty large, this causes issues in the tree widgets. Then
    it is desirable to make the buttons larger.
    """
    if is_inner:
        return int(general_icon_scale * 19 / 100)
    else:
        icon_font_factor = max(
            1.1,
            1.2 * (get_general_font_height() / get_general_icon_pixelsize()),
        )
        return int(general_icon_scale * icon_font_factor * 18 / 100)


@global_decorator
def get_libtable_icon_pixelsize():
    return max(25, int(general_icon_scale * 18 / 100))


# ^ 3. TOOLBAR GROUP
# ==================
toolbar_scale: float = 100.0


@global_decorator
def get_toolbar_pixelsize():
    return int(toolbar_scale * 16 / 100)


# ^ 4. OTHER
# ==========
# Custom basic widget tab icon size
custom_tab_scale: float = 100.0


@global_decorator
def get_custom_tab_pixelsize():
    return int(custom_tab_scale * 16 / 100)


# Home window scale
home_window_button_scale: float = 100.0


@global_decorator
def get_home_window_button_pixelsize():
    return int(home_window_button_scale * 28 / 100)


scrollbar_zoom: float = 100.0
progressbar_zoom: float = 100.0


@global_decorator
def get_scrollbar_zoom_pixelsize():
    return int(scrollbar_zoom * 1.00)


@global_decorator
def get_progressbar_zoom_pixelsize():
    return int(progressbar_zoom * 15 / 100)


splitter_pixelsize: int = 2


def get_splitter_pixelsize():
    return splitter_pixelsize


window_radius: float = 100.0


@global_decorator
def get_window_radius_pixelsize():
    return int(window_radius * 0.06)


mouse_scale: float = 100.0


@global_decorator
def get_mouse_pixelsize():
    return max(int(mouse_scale * 0.16), 4)


# linux specific things
MENUBAR_HEIGHT: int = 30
"""
================================================================================
                              EMBEETLE SPECIFIC STUFF
================================================================================
"""
#! Stored reference to the current active project
current_project: Optional[project.project.Project] = None
project_embeetle_directory: str = ".beetle"
filetree: Optional[gui.forms.newfiletree.NewFiletree] = None
dashboard: Optional[_dashboard_.Dashboard] = None
dashboard_data: Optional[_dashboard_data_.DashboardData] = None
new_dashboard: Optional[_new_dashboard_.NewDashboard] = None
serial_console: Optional[beetle_console.serial_console.SerialConsole] = None
sa_tab: Optional[sa_tab.chassis.sa_tab.SATab] = None
alert_buttons: Optional[Dict[str, gui.helpers.buttons.CustomPushButton]] = None
alert_labels: Optional[Dict[str, qt.QLabel]] = None
serial_port_combobox: Optional[
    gui.helpers.advancedcombobox.AdvancedComboBox
] = None
#! Stored reference to the toolmanager (only accessible through Home Window)
toolman: Optional[toolmanager.toolmanager.Toolmanager] = None
toolversion_extractor: Optional[
    toolmanager.version_extractor.VersionExtractor
] = None
toolbox_widg: Optional[home_toolbox.chassis.home_toolbox.Toolbox] = None
#! Stored reference to Home Library Manager
libman: Optional[libmanager.libmanager.LibManager] = None
libman_widg: Optional[home_libraries.chassis.home_libraries.LibManager] = None
libman_wizard: Optional[wizards.lib_wizard.lib_wizard.LibWizard] = None
libman_zipwizard: Optional[
    wizards.zipped_lib_wizard.zipped_lib_wizard.ZippedLibWizard
] = None
# Global program state
program_state = ProgramState.Saved

# $ IMPORTANT FILENAMES
license_agreement_filename = "license_agreement.txt"
config_filename = "user_functions.btl"
filetree_config_relative_path = os.path.join(
    project_embeetle_directory, "filetree_config.btl"
).replace("\\", "/")
settings_filename = {
    "mk0": "embeetle.btl",
    "mk1": "beetle.btl",
}

# Chip configurator information
chipconfigurator_series_filename = "chip_config.json5"
chipconfigurator_data_file = os.path.join(
    project_embeetle_directory, "chipconfig_data.json"
).replace("\\", "/")
chipconfigurator_code_generation_directory = "source/chipconfig"

# Stored reference to the parsing filetree containing all project tags
tag_database = None
# Tab names for widgets
tab_names = {
    "filetree": "Filetree",
    "dashboard": "Dashboard",
    "source-analyzer": "Source Analyzer",
    "diagnostics": "Diagnostics",
    "symbols": "Symbols",
    "messages": "Messages",
    "debugger": "Debugger",
    "general-registers": "General Registers View",
    "raw-memory": "Memory View - {}",
    "variable-watch": "Monitor View",
    "pin-configurator": "Config",
    "pieces": "Pieces AI",
    "new-dashboard": "New Dashboard",
    "chip-configurator": "Chip Configurator",
    "preferences": "Preferences",
    "serial-console": "Serial Monitor",
}
# Click&Jump indicator constant
CLICK_AND_JUMP_INDICATOR: int = 5
CLICK_AND_JUMP_INDICATOR_UNDERLINE: int = 10
CLICK_AND_JUMP_INDICATOR_VALUE: int = 1122
# Special file extensions
VALID_SOURCE_FILE_EXTENSIONS = (
    ".asm",
    ".s",  # Assembly files
    ".c",
    ".cpp",
    ".c++",
    ".cc",  # C source files
    ".a",  # Archives
)
VALID_HEADER_FILE_EXTENSIONS = (
    ".h",
    ".hpp",
    ".h++",  # C header files
)
FILE_RELOAD_EXCLUDES = ("filetree.mk",)
# Symbol icons
SYMBOL_ICONS = {
    "name": "icons/symbols/occurrence_kind/name.png",
    "definition": "icons/symbols/occurrence_kind/definition.png",
    "weak definition": "icons/symbols/occurrence_kind/weakdef.png",
    "tentative definition": "icons/symbols/occurrence_kind/tentdef.png",
    "declaration": "icons/symbols/occurrence_kind/declaration.png",
    "usage": "icons/symbols/occurrence_kind/usage.png",
    "constant": "icons/symbols/symbol_kind/constant.png",
    "global function": "icons/symbols/symbol_kind/global_function.png",
    "local function": "icons/symbols/symbol_kind/local_function.png",
    "header": "icons/symbols/occurrence_kind/header.png",
    "macro": "icons/symbols/symbol_kind/macro.png",
    "struct": "icons/symbols/symbol_kind/struct.png",
    "field": "icons/symbols/symbol_kind/struct_field.png",
    "type": "icons/symbols/symbol_kind/type.png",
    "global variable": "icons/symbols/symbol_kind/global_variable.png",
    "local variable": "icons/symbols/symbol_kind/local_variable.png",
    "variable": "icons/symbols/symbol_kind/local_variable.png",
    "unknown": "icons/symbols/symbol_kind/other.png",
}
# Base Embeetle websites
BASE_URLS = (
    "https://embeetle.com",
    "https://embeetle.cn",
)
# Selected base URL
embeetle_base_url: Optional[str] = None
embeetle_base_url_override: Optional[str] = None
# $ COM-ports
# Data structure obtained from functions.list_serial_ports()
serial_port_data: Optional[Dict[str, Dict[str, str]]] = None
"""
================================================================================
                         GLOBAL FUNCTIONS AND ROUTINES
================================================================================
"""


def print_log(*args, **kwargs):
    """Internal module function that runs the append_message method of the log
    window."""
    if log_window is not None:
        log_window.append_message(*args)  # noqa


"""
================================================================================
                                 GLOBAL MUTEXES
================================================================================
"""

#! user_lock
# This lock should allow critical user-invoked-actions to complete before anoth-
# er one can start. Example: Opening a folder should complete before another one
# (or the same one) can be opened/closed.
user_lock: threading.Lock = threading.Lock()
