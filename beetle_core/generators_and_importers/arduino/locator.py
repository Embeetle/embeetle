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

from typing import *
import os
import sys
import pathlib
import purefunctions
import os_checker

try:
    import filefunctions
except:
    # Add parental paths to retrieve the 'filefunctions.py' module. This is only needed if you run
    # this script as standalone outside Embeetle.
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import filefunctions
if os_checker.is_os("windows"):
    import winshell
q = "'"


__arduino_executable_path_cache: Optional[str] = None


def find_arduino_executable() -> Optional[str]:
    """"""
    # $ Check cache
    global __arduino_executable_path_cache
    if __arduino_executable_path_cache:
        if __arduino_executable_path_cache == "not found":
            return None
        return __arduino_executable_path_cache

    # $ Find Arduino executable path
    if os_checker.is_os("windows"):
        result = __find_arduino_executable_windows()
    else:
        result = __find_arduino_executable_linux()

    # $ Store it in the cache and return result
    if result is None:
        __arduino_executable_path_cache = "not found"
    else:
        __arduino_executable_path_cache = result
    return result


__arduino_installdir_cache: Optional[str] = None


def find_arduino_installdir() -> Optional[str]:
    """Return the absolute path to the Arduino installation on the user's
    computer.

    Return None if not found.
    """
    # $ Check cache
    global __arduino_installdir_cache
    if __arduino_installdir_cache:
        if __arduino_installdir_cache == "not found":
            return None
        return __arduino_installdir_cache

    # $ Find Arduino executable
    arduino_executable: Optional[str] = find_arduino_executable()
    if arduino_executable is None:
        __arduino_installdir_cache = "not found"
        return None

    # $ Return parent or grandparent folder
    arduino_installdir: str = (
        os.path.dirname(arduino_executable).replace("\\", "/").rstrip("/")
    )
    if arduino_installdir.endswith("/bin"):
        arduino_installdir = (
            os.path.dirname(arduino_installdir).replace("\\", "/").rstrip("/")
        )
    __arduino_installdir_cache = arduino_installdir
    return arduino_installdir


__arduino15_path_cache: Optional[str] = None


def find_arduino15() -> Optional[str]:
    """Find the 'Arduino15' folder."""
    # $ Check cache
    global __arduino15_path_cache
    if __arduino15_path_cache:
        if __arduino15_path_cache == "not found":
            return None
        return __arduino15_path_cache

    # $ Find Arduino15 folder
    if os_checker.is_os("windows"):
        result = __find_arduino15_windows()
    else:
        result = __find_arduino15_linux()

    # $ Store it in the cache and return result
    if result is None:
        __arduino15_path_cache = "not found"
    else:
        __arduino15_path_cache = result
    return result


__arduino_sketchbooks_cache: List[str] = []


def list_arduino_sketchbooks() -> List[str]:
    """Arduino puts an "Arduino Sketchbook" in your Documents or home folder.
    It's the default location for your sketches, as well as your stored
    libraries and other Arduino-related files.

    Just to play on the safe side, we'll look for more than one Arduino
    sketchbook and return them in a list.
    """
    # Check cache
    global __arduino_sketchbooks_cache
    if __arduino_sketchbooks_cache and len(__arduino_sketchbooks_cache) > 0:
        return __arduino_sketchbooks_cache

    arduino_sketchbooks: List[str] = []

    def check_for_sketchbook(_folder: str) -> Optional[str]:
        # Check if the given folder has an immediate subfolder named 'Arduino' (or 'arduino') which
        # we'll then suppose to be an Arduino Sketchbook folder. The parameter '_folder' is supposed
        # to be a Documents folder (Windows) or a homedir folder (Linux).
        _candidates = [
            os.path.join(_folder, "Arduino").replace("\\", "/").rstrip("/"),
            os.path.join(_folder, "arduino").replace("\\", "/").rstrip("/"),
        ]
        for _candidate in _candidates:
            try:
                if os.path.isdir(_candidate):
                    return _candidate
            except:
                pass
            continue
        return None

    # & Documents
    # Loop over all the Documents folders and check if the Arduino Sketchbook is in there. This is
    # typically the case for Windows systems.
    for folder in filefunctions.list_all_documents_folders():
        sketchbook = check_for_sketchbook(folder)
        if sketchbook:
            arduino_sketchbooks.append(sketchbook)
        continue

    # & User Profile Folders
    # Loop over all the user profile folders and check if the Arduino Sketchbook is in there. This
    # is typical for Linux.
    for folder in filefunctions.list_user_profile_folders():
        sketchbook = check_for_sketchbook(folder)
        if sketchbook:
            arduino_sketchbooks.append(sketchbook)
        continue
    return arduino_sketchbooks


__arduino_libcollection_folders_cache: Optional[Dict[str, List[str]]] = None


def list_arduino_libraries() -> Dict[str, List[str]]:
    """Arduino stores its libraries in several places. These are the locations
    to look out for:

    1. Embeetle
    -----------
    Embeetle can also store (Arduino) libraries. Those would end up in the '~/.embeetle/' folder.

    2. Arduino Sketchbook
    ---------------------
    The Arduino sketchbook is located at 'C:/Users/krist/Documents/Arduino' on Windows and at
    '~/Arduino' on Linux.
    The Sketchbook folder should have a subfolder 'libraries'.

    3. Arduino15
    ------------
    The Arduino15 folder is located at:
    'C:/Users/krist/AppData/Local/Arduino15'
    It should have a subfolder 'libraries', but that isn't necessarily a direct one. For example:
        - '<arduino15>/staging/libraries'
        - '<arduino15>/packages/arduino/hardware/avr/1.8.6'
        - ...

    4. Arduino Installation
    -----------------------
    The Arduino installation directory is at 'C:/Program Files/Arduino IDE' or
    'C:/Program Files (x86)/Arduino'. It can contain a 'libraries' folder nested in there.
    """
    global __arduino_libcollection_folders_cache
    if __arduino_libcollection_folders_cache:
        return __arduino_libcollection_folders_cache
    library_paths_dict: Dict[str, List[str]] = {
        "dot_embeetle": [],
        "arduino_sketchbook": [],
        "arduino15": [],
        "arduino_installation": [],
    }

    # & 1. Embeetle
    # Embeetle can store libraries in the '~/.embeetle/libraries/' folder.
    dotembeetle_folder: Optional[str] = None
    try:
        import data

        dotembeetle_folder = data.settings_directory
    except:
        pass
    try:
        if dotembeetle_folder is None:
            homedir = filefunctions.get_curuser_profile_folder()
            dotembeetle_folder = (
                os.path.join(homedir, ".embeetle")
                .replace("\\", "/")
                .rstrip("/")
            )
        dotembeetle_libraries = (
            os.path.join(
                dotembeetle_folder,
                "libraries",
            )
            .replace("\\", "/")
            .rstrip("/")
        )
        if not os.path.isdir(dotembeetle_libraries):
            filefunctions.makedirs(
                folderpath=dotembeetle_libraries,
                verbose=True,
            )
        assert os.path.isdir(dotembeetle_libraries)
        library_paths_dict["dot_embeetle"].append(dotembeetle_libraries)
    except Exception as e:
        print(
            f"Error when trying to look into or create the ~/.embeetle/libraries folder: {e}"
        )

    # & 2. Arduino Sketchbook
    # Look for a 'libraries' folder in the Arduino Sketchbook (or Sketchbooks if there is more than
    # one, which shouldn't be the case). The 'libraries' subfolder should be directly in there.
    # Note: the Sketchbook folder itself should be inside a Documents folder on Windows and directly
    # in the user profile folder on Linux. But that's not relevant in the scope of the code snippet
    # below.
    try:
        for folder in list_arduino_sketchbooks():
            lib_path = (
                os.path.join(folder, "libraries").replace("\\", "/").rstrip("/")
            )
            try:
                if os.path.isdir(lib_path):
                    library_paths_dict["arduino_sketchbook"].append(lib_path)
            except:
                pass
            continue
    except Exception as e:
        print(f"Error while looping over the Arduino Sketchbook(s): {e}")

    # & 3. Arduino15
    # Look for a 'libraries' folder in the Arduino15 folder. It can be nested.
    arduino15_folder = find_arduino15()
    try:
        if arduino15_folder and os.path.isdir(arduino15_folder):
            for root, dirs, files in os.walk(arduino15_folder):
                something_found = False
                for d in dirs:
                    if d.lower() == "libraries":
                        library_paths_dict["arduino15"].append(
                            os.path.join(root, d).replace("\\", "/").rstrip("/")
                        )
                        something_found = True
                        break
                    continue
                if something_found:
                    dirs[:] = []
                continue
            # endif
    except Exception as e:
        print(f"Error when walking through {arduino15_folder}: {e}")

    # & 4. Arduino Installation
    # First check for a 'libraries' folder directly in the installation directory. Then dig a bit
    # deeper in the 'hardware' subfolder, if present.
    arduino_installdir = find_arduino_installdir()
    try:
        if arduino_installdir and os.path.isdir(arduino_installdir):
            # Check in toplevel folder
            lib_path = (
                os.path.join(arduino_installdir, "libraries")
                .replace("\\", "/")
                .rstrip("/")
            )
            if os.path.isdir(lib_path):
                library_paths_dict["arduino_installation"].append(lib_path)
            # Dig a bit deeper
            if os.path.isdir(f"{arduino_installdir}/hardware"):
                for root, dirs, files in os.walk(
                    f"{arduino_installdir}/hardware"
                ):
                    something_found = False
                    for d in dirs:
                        if d.lower() == "libraries":
                            library_paths_dict["arduino_installation"].append(
                                os.path.join(root, d)
                                .replace("\\", "/")
                                .rstrip("/")
                            )
                            something_found = True
                            break
                        continue
                    if something_found:
                        dirs[:] = []
                    continue
                # endif
            # endif
    except Exception as e:
        print(f"Error when walking through {arduino_installdir}: {e}")

    __arduino_libcollection_folders_cache = library_paths_dict
    return library_paths_dict


# % ----------------------------------------------------------------------------------------------- #
# %                               H E L  P       F  U N C T I O N S                                 #
# % ----------------------------------------------------------------------------------------------- #
def __find_arduino_executable_windows() -> Optional[str]:
    """Return the absolute path to the Arduino executable on the user's
    computer.

    Return None if not found.
    """

    def is_executable_file(path: pathlib.Path) -> bool:
        try:
            return path.is_file() and path.suffix.lower() == ".exe"
        except Exception as e:
            print(
                f"Error while checking if file {q}{path}{q} is an executable:"
                f"{e}"
            )
        return False

    def search_common_directories() -> Optional[pathlib.Path]:
        # Check the most common directories to find the Arduino executable. More in particular,
        # check the folders 'C:/Program Files' and 'C:/Program Files (x86)'. Iterate over their sub-
        # folders and look further in each subfolder that contains the string 'arduino' in its name
        # for an Arduino executable.
        program_files_folderlist: List[pathlib.Path] = [
            pathlib.Path(os.environ.get("ProgramFiles", "C:/Program Files")),
            pathlib.Path(
                os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")
            ),
        ]
        for program_files_folder in program_files_folderlist:
            try:
                if program_files_folder.name.strip() == "":
                    continue
                if not program_files_folder.is_dir():
                    continue
                for program_files_subfolder in program_files_folder.iterdir():
                    if not program_files_subfolder.is_dir():
                        continue
                    if "arduino" not in program_files_subfolder.name.lower():
                        continue
                    for entry in program_files_subfolder.iterdir():
                        if "arduino" not in entry.name.lower():
                            continue
                        if not is_executable_file(entry):
                            continue
                        # Arduino executable found
                        return entry
                    continue
                continue
            except FileNotFoundError as e:
                print(
                    f"ERROR: FileNotFoundError while searching {q}{program_files_folder}{q}:\n"
                    f"{e}"
                )
            except PermissionError as e:
                print(
                    f"ERROR: PermissionError while searching {q}{program_files_folder}{q}:\n"
                    f"{e}"
                )
            except Exception as e:
                print(
                    f"ERROR: Exception while searching {q}{program_files_folder}{q}:\n"
                    f"{e}"
                )
            continue
        # Arduino executable not found
        return None

    def search_desktop_for_shortcut() -> Optional[pathlib.Path]:
        # Search for Arduino shortcuts on the desktop and extract the path to an Arduino executable
        # if possible.
        desktop: pathlib.Path = pathlib.Path(winshell.desktop())
        for shortcut in desktop.glob("*.lnk"):
            if "arduino" not in shortcut.stem.lower():
                continue
            shortcut_path_str: str = winshell.shortcut(str(shortcut)).path
            shortcut_path: pathlib.Path = pathlib.Path(shortcut_path_str)
            if "arduino" not in shortcut_path.stem.lower():
                continue
            if is_executable_file(shortcut_path):
                # Arduino executable found
                return shortcut_path
            continue
        # Arduino executable not found
        return None

    def search_path_for_arduino() -> Optional[pathlib.Path]:
        # Search the PATH environment variable for an Arduino executable
        for path_str in os.environ.get("PATH", "").split(os.pathsep):
            if path_str.strip() == "":
                continue
            for file in pathlib.Path(path_str).glob("*arduino*.exe"):
                if is_executable_file(file):
                    # Arduino executable probably found. However, be careful about the
                    # 'arduinoOTA.exe' in the GNU AVR toolchain.
                    if file.stem.lower() == "arduinoota":
                        continue
                    return file
                continue
            continue
        # Arduino executable not found
        return None

    # $ START SEARCH
    # $ ------------
    arduino_path: Optional[pathlib.Path] = None
    arduino_path_str: Optional[str] = None

    # $ Check common installation directories
    arduino_path = search_common_directories()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Check for Arduino shortcuts on the desktop
    arduino_path = search_desktop_for_shortcut()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Check in PATH environment variable
    arduino_path = search_path_for_arduino()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # Avoid doing a deep search. That would be too resource intensive. Just assume at this point
    # that the user has no Arduino installation.
    return None


def __find_arduino_executable_linux() -> Optional[str]:
    """Return the absolute path to the Arduino executable on the user's
    computer.

    Return None if not found.
    """

    def is_executable_file(path: pathlib.Path) -> bool:
        try:
            return path.is_file() and os.access(path, os.X_OK)
        except Exception as e:
            print(
                f"Error while checking if file {q}{path}{q} is an executable:"
                f"{e}"
            )
        return False

    def search_common_symlinks() -> Optional[pathlib.Path]:
        # Check common symlink locations for the presence of an Arduino executable
        user_home: pathlib.Path = pathlib.Path.home()
        common_symlinks: List[pathlib.Path] = [
            pathlib.Path("/usr/bin/arduino"),
            pathlib.Path("/usr/local/bin/arduino"),
            pathlib.Path("/usr/local/sbin/arduino"),
            pathlib.Path("/opt/arduino"),
            user_home / ".local" / "bin" / "arduino",
            pathlib.Path("/sbin/arduino"),
            pathlib.Path("/usr/sbin/arduino"),
            user_home / "bin" / "arduino",
        ]
        # Make sure the list of common symlinks has entries that point to a potential Arduino
        # executable, not something else.
        common_symlinks = [
            symlink
            for symlink in common_symlinks
            if "arduino" in symlink.name.lower()
        ]
        # Resolve the symlinks one-by-one and return the resolved symlink if it is an executable
        for symlink in common_symlinks:
            if not symlink.is_symlink():
                continue
            resolved_path: pathlib.Path = symlink.resolve()
            if is_executable_file(resolved_path):
                # Arduino executable found
                return resolved_path
            continue
        # Arduino executable not found
        return None

    def search_common_directories() -> Optional[pathlib.Path]:
        # Search for an Arduino executable in common directories
        common_dirs: List[pathlib.Path] = [
            pathlib.Path("/usr/bin"),
            pathlib.Path("/usr/local/bin"),
            pathlib.Path.home() / ".local" / "bin",
        ]
        for dir_path in common_dirs:
            try:
                if not dir_path.is_dir():
                    continue
                for file in dir_path.iterdir():
                    if not is_executable_file(file):
                        continue
                    if "arduino" in file.name.lower():
                        # Arduino executable found
                        return file
                    continue
                continue
            except FileNotFoundError as e:
                print(
                    f"ERROR: FileNotFoundError while searching {q}{dir_path}{q}:\n"
                    f"{e}"
                )
            except PermissionError as e:
                print(
                    f"ERROR: PermissionError while searching {q}{dir_path}{q}:\n"
                    f"{e}"
                )
            except Exception as e:
                print(
                    f"ERROR: Exception while searching {q}{dir_path}{q}:\n"
                    f"{e}"
                )
            continue
        # Arduino executable not found
        return None

    def search_path_for_arduino() -> Optional[pathlib.Path]:
        # Search the PATH environment variable for an Arduino executable
        for path_str in os.environ.get("PATH", "").split(":"):
            if path_str.strip() == "":
                continue
            path = pathlib.Path(path_str)
            if not path.is_dir():
                continue
            for file in path.iterdir():
                if is_executable_file(file) and "arduino" in file.name.lower():
                    # Arduino executable found
                    return file
                continue
            continue
        # Arduino executable not found
        return None

    def search_desktop_for_shortcut() -> Optional[pathlib.Path]:
        # Search for Arduino shortcuts on the desktop and extract the path to an Arduino executable
        # if possible.

        # First define two helpful functions for this task.
        def parse_desktop_file(
            desktop_file_path: pathlib.Path,
        ) -> Optional[pathlib.Path]:
            # Parse the given desktop file. Find and return an executable in its content. Return
            # None if nothing can be found.
            try:
                with open(desktop_file_path, "r", encoding="utf-8") as _f:
                    for _line in _f:
                        if not _line.lower().startswith("exec="):
                            continue
                        try:
                            # Split the line at '=' and then at spaces to isolate the executable path
                            _exec_cmd_parts = (
                                _line.split("=", 1)[1].strip().split(" ")
                            )
                            # Extract the first segment (executable path)
                            _exec_path_str = _exec_cmd_parts[0].strip(" \"'")
                            # Handle potential environment variable in the path
                            if _exec_path_str.startswith("$"):
                                env_var, _, remainder = (
                                    _exec_path_str.partition("/")
                                )
                                env_var = env_var[1:]  # Remove the '$'
                                env_var_value = os.getenv(env_var)
                                if env_var_value:
                                    _exec_path_str = os.path.join(
                                        env_var_value, remainder
                                    )
                            # Turn the path into a pathlib.Path() object
                            _exec_path = pathlib.Path(_exec_path_str)
                            # Check if it is an executable file and return the result
                            if is_executable_file(_exec_path):
                                return _exec_path
                        except:
                            # Unable to handle the line
                            print(
                                f"ERROR: Unable to handle this line:\n"
                                f"{q}{_line}{q}\n"
                                f"in the desktop file:\n"
                                f"{q}{desktop_file_path}{q}"
                            )
                        continue
            except IOError as e:
                print(
                    f"ERROR: Unable to read the file {q}{desktop_file_path}{q}:\n"
                    f"{e}"
                )
            except Exception as e:
                print(
                    f"ERROR: Unexpected error occured while parsing the desktop file "
                    f"{q}{desktop_file_path}{q}:\n"
                    f"{e}"
                )
            return None

        def search_folder_for_desktop_shortcuts(
            desktop_folder: pathlib.Path,
        ) -> Optional[pathlib.Path]:
            # Search the given folder for desktop shortcuts that can potentially point to an Arduino
            # executable.
            try:
                if not desktop_folder.is_dir():
                    # Arduino executable not found because folder doesn't exist
                    return None
                for file in desktop_folder.iterdir():
                    if not file.is_file() or not file.name.lower().endswith(
                        ".desktop"
                    ):
                        continue
                    if not "arduino" in file.stem.lower():
                        continue
                    exec_path: Optional[pathlib.Path] = parse_desktop_file(file)
                    if exec_path is None:
                        continue
                    assert is_executable_file(exec_path)
                    if "arduino" in exec_path.name.lower():
                        # The variable 'exec_path' matches all the conditions we were
                        # looking for:
                        #   - It's pathlib.Path object
                        #   - It's an executable file
                        #   - It contains the string 'arduino' in its path
                        #   - The path was found in the content of a desktop file
                        #   - The desktop file also contains the string 'arduino' in its name
                        return exec_path
                    continue
                # Arduino executable not found
                return None
            except PermissionError:
                # Permission denied. Unable to access the given desktop folder.
                pass
            # Arduino executable not found because of permission error
            return None

        # Now construct a list of folders that can potentially contain '.desktop' files.
        user_home: pathlib.Path = pathlib.Path.home()
        desktop_folder_list: List[pathlib.Path] = [
            pathlib.Path("/usr/share/applications/"),
            pathlib.Path("/usr/local/share/applications/"),
            user_home / ".local/share/applications/",
            user_home / "Desktop",
            user_home / "desktop",
            pathlib.Path("/usr/share/app-install/"),
            pathlib.Path("/var/lib/snapd/desktop/applications/"),
        ]

        # Loop over the folders in the list and check each of them for '.desktop' files
        for folder in desktop_folder_list:
            try:
                if not folder.is_dir():
                    continue
                arduino_exec_path = search_folder_for_desktop_shortcuts(folder)
                if arduino_exec_path is not None:
                    # Arduino executable found
                    return arduino_exec_path
                continue
            except PermissionError:
                # Permission denied. Unable to access the desktop folder.
                pass
            continue
        # Arduino executable not found
        return None

    def search_downloads_folder() -> Optional[pathlib.Path]:
        # Search for an Arduino executable in the downloads folder. The user might have downloaded
        # the Arduino IDE and never bothered to move it around.
        user_home: pathlib.Path = pathlib.Path.home()
        downloads_folder: pathlib.Path = user_home / "Downloads"
        if not downloads_folder.is_dir():
            downloads_folder = user_home / "downloads"
        if not downloads_folder.is_dir():
            return None
        for folder in downloads_folder.iterdir():
            if not folder.is_dir():
                continue
            if not "arduino" in folder.name.lower():
                continue
            for file in folder.iterdir():
                if is_executable_file(file) and "arduino" in file.name.lower():
                    # Arduino executable found
                    return file
                continue
            continue
        # Arduino executable not found
        return None

    # $ START SEARCH
    # $ ------------
    arduino_path: Optional[pathlib.Path] = None
    arduino_path_str: Optional[str] = None

    # $ Check common symlinks
    arduino_path = search_common_symlinks()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Check common installation directories
    arduino_path = search_common_directories()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Check in PATH environment variable
    arduino_path = search_path_for_arduino()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Search in the Arduino shortcuts on the desktop
    arduino_path = search_desktop_for_shortcut()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # $ Search in the downloads folder
    arduino_path = search_downloads_folder()
    if arduino_path:
        return str(arduino_path).replace("\\", "/").rstrip("/")

    # Avoid doing a deep search. That would be too resource intensive. Just assume at this point
    # that the user has no Arduino installation.
    return None


def __find_arduino15_windows() -> Optional[str]:
    """Find the 'Arduino15' folder on a Windows computer."""

    def check_folder(_folderpath: str) -> Optional[str]:
        # Check if the 'Arduino15' folder is a subfolder of the given folderpath. Try a few folder-
        # names that could represent an Arduino15 folder.
        _names = ("Arduino15", "arduino15", ".arduino15")
        for _name in _names:
            _arduino15_path: str = os.path.join(_folderpath, _name).replace(
                "\\", "/"
            )
            if os.path.isdir(_arduino15_path):
                return _arduino15_path
            continue
        return None

    # & AppData
    # Check inside the base AppData folders, such as:
    # - 'C:/Users/krist/AppData/Roaming'
    # - 'C:/Users/krist/AppData/Local'
    appdata_roaming: str = os.getenv(
        "APPDATA",
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming").replace(
            "\\", "/"
        ),
    ).replace("\\", "/")
    appdata_local: str = os.path.join(
        os.path.dirname(appdata_roaming), "Local"
    ).replace("\\", "/")
    for appdata_path in (appdata_local, appdata_roaming):
        result = check_folder(appdata_path)
        if result:
            # Arduino15 folder found
            return result
        continue

    # & IDE installation directory
    # If an Arduino IDE executable path is provided, check near that location
    arduino_exe_path = find_arduino_executable()
    if arduino_exe_path:
        ide_parent_path_candidates = (
            os.path.dirname(arduino_exe_path).replace("\\", "/"),
            os.path.dirname(os.path.dirname(arduino_exe_path)).replace(
                "\\", "/"
            ),
        )
        for folderpath in ide_parent_path_candidates:
            result = check_folder(folderpath)
            if result:
                # Arduino15 folder found
                return result
            continue

    # & Documents
    # Check in the Documents folder
    for documents_folder in filefunctions.list_all_documents_folders():
        result = check_folder(documents_folder)
        if result:
            # Arduino15 folder found
            return result
        continue

    # Arduino15 folder not found
    return None


def __find_arduino15_linux() -> Optional[str]:
    """Find the '.arduino15' folder on a Linux computer."""

    def check_folder(_folderpath: str) -> Optional[str]:
        # Check if the 'Arduino15' folder is a subfolder of the given folderpath. Try a few folder-
        # names that could represent an Arduino15 folder.
        _names = ("Arduino15", "arduino15", ".arduino15")
        for _name in _names:
            _arduino15_path: str = os.path.join(_folderpath, _name).replace(
                "\\", "/"
            )
            if os.path.isdir(_arduino15_path):
                return _arduino15_path
            continue
        return None

    # & Home
    # Check the user's home directory
    home_dir = os.path.expanduser("~")
    result = check_folder(home_dir)
    if result:
        return result

    # & Common directories
    # If the IDE is installed for all users, check common directories
    for common_dir in (
        "/opt",
        "/usr/local",
        "/usr",
        "/snap",
        "/etc",
        os.path.expanduser("~/.var/app"),
    ):
        result = check_folder(common_dir)
        if result:
            return result
        continue

    # & Env variables
    # Check environment variables for any custom paths
    for key, value in os.environ.items():
        if "arduino" not in key.lower():
            continue
        result = check_folder(value)
        if result:
            return result
        continue

    # Arduino15 folder not found
    return None


if __name__ == "__main__":
    print(
        f"Arduino installation folder: {q}{find_arduino_installdir()}{q}\n"
        f"Arduino executable:          {q}{find_arduino_executable()}{q}\n"
        f"Arduino15:                   {q}{find_arduino15()}{q}\n"
        f"Arduino Sketchbook(s): {list_arduino_sketchbooks()}\n"
    )
    print("Arduino Libraries:")
    for i, j in list_arduino_libraries().items():
        print(f"    - {q}{i}{q} : {j}")
    sys.exit(0)
