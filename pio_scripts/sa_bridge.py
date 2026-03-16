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

"""
Source Analyzer Bridge for PlatformIO

Run with `--help` to learn more.

IMPORTANT FIX in v0.1.7:
Fixed critical issue where CollectBuildFiles interception was disrupting SCons
VariantDir mechanism for header-only directories (e.g., Arduino variant dirs).
This was causing "file not found" errors for pins_arduino.h and similar headers.
The fix ensures VariantDir is properly set up even when no source files exist.

CRITICAL FIX in v0.2.0:
Fixed critical issue where env.Append() interception was breaking Arduino ESP32 builds.
Root cause: SCons relies on exact method identity/binding, and replacing env.Append
with any wrapper function breaks internal assumptions about method behavior.
Solution: Replaced real-time method interception with post-processing approach that
filters CPPPATH after all additions are complete using AddPostAction hooks.

v0.2.1:
Added debug prints to post-processing functions to diagnose execution issues.

v0.2.5:
FIXED framework_exclude_hdirs functionality using SPAWN interception.
Instead of trying to filter CPPPATH at the wrong time, now intercepts compilation
commands right before execution and filters -I flags in real-time. This approach:
- Avoids timing issues (runs at perfect moment before compilation)
- Doesn't break SCons internal mechanisms (no method interception)
- Works with any framework (intercepts final compilation commands)

v0.2.8:
CLEANUP: Removed all unused code from earlier unsuccessful attempts:
- Removed unused filter_hdirs() function (replaced by SPAWN interception)
- Removed unused method interception code (filter_append, filter_prepend, etc.)
- Removed unused compilation stage filtering and post-processing functions
- Streamlined intercept_source_file_operations() to only essential functionality

v0.2.9:
DOCUMENTATION: Updated filter hook docstring to clearly explain the current
implementation approach, filtering mechanisms, and configuration options.
"""

import os
import sys
import configparser
import argparse
import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Optional, Any, Tuple, TYPE_CHECKING, cast
from colorama import init, Style

# Extend the colorama color palette
# (pick from https://jonasjacek.github.io/colors)
from colorama import Fore as _Fore

_EXTRA_256 = {
    "TEAL": 37,
    "SPRINGGREEN": 48,
    "AQUA": 51,
    "INDIGO": 54,
    "STEEL": 67,
    "TURQUOISE": 80,
    "PURPLE": 93,
    "SKY": 117,
    "LIME": 118,
    "OLIVE": 142,
    "PLUM": 176,
    "GOLD": 178,
    "TAN": 180,
    "PINK": 205,
    "ORANGE": 208,
    "CORAL": 209,
    "ROSE": 211,
    "GRAY": 244,
}

# Attach new attributes to the existing Fore object
_name = _code = None
for _name, _code in _EXTRA_256.items():
    setattr(_Fore, _name, f"\033[38;5;{_code}m")
# keep globals tidy
del (
    _name,
    _code,
    _EXTRA_256,
)

# Tell static analysers that `Fore` HAS those attributes
if TYPE_CHECKING:

    class _ForeWith256:
        ORANGE: str
        PINK: str
        PURPLE: str
        TEAL: str
        LIME: str
        GRAY: str
        GOLD: str
        SKY: str
        TURQUOISE: str
        AQUA: str
        SPRINGGREEN: str
        OLIVE: str
        CORAL: str
        ROSE: str
        INDIGO: str
        STEEL: str
        TAN: str
        PLUM: str

    Fore = cast("_ForeWith256", _Fore)  # rebind for type checkers only
else:
    Fore = _Fore  # normal runtime name


def _help() -> None:
    """
    Print help message for the SA Bridge script.
    """
    B = Style.BRIGHT
    R = Style.RESET_ALL
    Y = Fore.YELLOW
    C = Fore.CYAN
    r = Fore.RED
    print(f"""
{B}SOURCE ANALYZER BRIDGE FOR PLATFORMIO{R}
{B}====================================={R}

Filters PlatformIO builds so only the files you want are compiled.


{B}TERMINOLOGY{R}
{B}-----------{R}
SOURCE
'source' means 'source file', such as: {Y}foo.c{R}, {Y}bar.cpp{R}, {Y}startup.s{R}, ...

HDIR
'hdir' means 'include directory with header files'. A hdir can be added to a
build command's include path with the {C}-I{R} prefix: {C}-I{R}{Y}src{R}, {C}-I{R}{Y}src/dir1{R}, ...

RELATIVE PATH
Unless otherwise stated, 'relative' means 'relative to project root'.


{B}QUICK START{R}
{B}-----------{R}
DRY-RUN
Launch dry-run and write commands to "<project>/.beetle/build_commands.json":

    {r}$ python{R} {Y}sa_bridge.py{R} [{C}--dir{R} {Y}PROJECT{R}] {C}--dry-run{R}

The dry-run still creates a build directory in the project, as well as some sub-
directories in there. However, the build commands are stopped such that they
remain empty.

INSTALL FILTER
Install filter in project such that builds launched afterwards ({r}$ pio run{R}) will
be filtered:

    {r}$ python{R} {Y}sa_bridge.py{R} [{C}--dir{R} {Y}PROJECT{R}]
        {C}--user-exclude-sources{R}      {Y}"[src/file1.c, src/file2.c]"{R}
        {C}--user-include-hdirs{R}        {Y}"[src/dir1, src/dir2]"{R}
        {C}--framework-exclude-sources{R} {Y}"[/abs/path/file1.c]"{R}
        {C}--framework-exclude-hdirs{R}   {Y}"[/abs/path/dir1]"{R}

Same as previous, but replace the exclude/include lists with sample filters for
testing:

    {r}$ python{R} {Y}sa_bridge.py{R} [{C}--dir{R} {Y}PROJECT{R}] {C}--test{R}

To apply the filtering, this script modifies the project's platformio.ini and
inserts PRE-scripts that are activated on every build.


{B}OPTIONS{R}
{B}-------{R}
  {C}-d{R}, {C}--dir PATH{R}     Project directory (default: cwd)
  {C}-v{R}, {C}--verbose{R}      Detailed output
  {C}-h{R}, {C}--help{R}         Show this help
  
  {C}--dry-run{R}          Only collect build info, write to
                     "<project>/.beetle/build_commands.json"

  {C}-t{R}, {C}--test{R}         Use sample filters for testing
          
  {C}--user-exclude-sources{R}      {Y}"[src/file1.c, src/file2.c, ...]"{R} (rel paths)
  {C}--user-include-hdirs{R}        {Y}"[src/dir1, src/dir2, ...]"{R}       (rel paths)
  {C}--framework-exclude-sources{R} {Y}"[/abs/path/file1.c, ...]"{R}        (abs paths)
  {C}--framework-exclude-hdirs{R}   {Y}"[/abs/path/dir1, ...]"{R}           (abspaths)

All filtering arguments force exclude files (and hdirs), except for argument
{C}--user-include-hdirs{R}. This one adds(!) user directories.
By default, only {Y}<project>/include{R} and {Y}<project>/src{R} are on the include path.
With {C}--user-include-hdirs{R} you can add more.


{B}WORKFLOW{R}
{B}--------{R}

          dry-run output
   ┌─────────────<─────────────────┐
   │                               │
┌──┴───┐                      ┌────┴──────┐
│  SA  │─────────>────────────│ SA Bridge │─┬───> Modify platformio.ini
└──────┘  list files/hdirs    └───────────┘ │     
          to be excluded                    │
                                            └───> Add required PRE-scripts


The two actions taken by the SA Bridge - modifying platformio.ini and adding
PRE-scripts - is what we mean by "apply filters".


{B}USAGE FROM PYTHON{R}
{B}-----------------{R}
Instead of running this script standalone, you can import it also directly in
python:

    {C}import{R} sa_bridge
    
    {Fore.GREEN}# 1. Dry-run{R}
    json_path = sa_bridge.{r}store_dry_run_output{R}({Y}"/path/to/project"{R})
    
    {Fore.GREEN}# 2. Analyse json...{R}
    
    {Fore.GREEN}# 3. Apply filters{R}
    sa_bridge.{r}apply_build_filters{R}(
        {Y}"/path/to/project"{R},
        user_exclude_sources      = [{Y}"src/file1.c"{R}],
        user_include_hdirs        = [{Y}"src/dir1"{R}],
        framework_exclude_sources = [{Y}"/abs/path/file1.c"{R}],
        framework_exclude_hdirs   = [{Y}"/abs/path/dir1"{R}],
    )


{B}BACKUPS{R}
{B}-------{R}
The script creates backups before modifying platformio.ini:
  - {Y}<project>/platformio.ini.bkp{R}                (user restoration)
  - {Y}<project>/.beetle/platformio_ini_orig.json{R}  (reference for tools)


{B}REQUIREMENT{R}
{B}-----------{R}
- A PlatformIO installation.
- A valid PlatformIO project containing platformio.ini.


{B}PRE-SCRIPT VERSIONING{R}
{B}---------------------{R}
Two auto-maintained scripts live in {Y}<project>/.beetle{R}
    - {Y}dry_run.py{R} - captures build commands
    - {Y}filter_hook.py{R} - applies source/include filters

They are created, updated, or left untouched as needed to stay current.
""")
    return


# SCRIPT OVERVIEW
# 1. Imports and help function
# 2. Main SourceAnalyzerBridge class
# 3. Convenience functions
# 4. Main CLI entry point
# 5. Embedded PRE-scripts

# PRE-SCRIPT VERSIONS
# Update this when making changes to the scripts at the bottom of this file.
SCRIPT_VERSION = "0.3.3"


def print_info(msg: str = "") -> None:
    if msg:
        print(f"{Fore.LIGHTBLUE_EX}[SA BRIDGE]{Fore.RESET} {msg}")
    return


def print_warn(msg: str = "") -> None:
    if msg:
        print(f"{Fore.ORANGE}[SA BRIDGE]{Fore.RESET} {msg}")
    return


def print_err(msg: str = "") -> None:
    if msg:
        print(f"{Fore.RED}[SA BRIDGE]{Fore.RESET} {msg}", file=sys.stderr)
    return


def print_list(items: List[Any]) -> None:
    if items:
        for item in items:
            print(Fore.YELLOW + f'    "{item}"')
    else:
        print(Fore.YELLOW + f"    None")
    return


def print_path(_path: Path | str) -> None:
    path_str = str(_path).replace("\\", "/")
    print(Fore.YELLOW + f'    "{path_str}"')
    return


class SourceAnalyzerBridge:

    def __init__(self, project_path: str):
        """
        Args:
            project_path: Path to project root
        """
        self.__project_path: Path = Path(project_path).resolve()
        self.__platformio_ini_path: Path = (
            self.__project_path / "platformio.ini"
        )
        self.__filter_hook_path: Path = (
            self.__project_path / ".beetle" / "filter_hook.py"
        )
        self.__dry_run_path: Path = (
            self.__project_path / ".beetle" / "dry_run.py"
        )
        self.__build_commands_path: Path = (
            self.__project_path / ".beetle" / "build_commands.json"
        )
        return

    def __load_config(self) -> Tuple[configparser.ConfigParser, str]:
        """
        Load `platformio.ini` to a ConfigParser()-instance. Then return that in
        tuple with comment at the top of the `platformio.ini` (empty string if
        no comment found).
        """
        config = configparser.ConfigParser(
            inline_comment_prefixes=("#", ";"), allow_no_value=True
        )
        if not self.__platformio_ini_path.exists():
            raise FileNotFoundError(
                f"No platformio.ini file found at:\n"
                f"    {Fore.YELLOW}{self.__platformio_ini_path}{Fore.RESET}"
            )
        header_comment = self.__extract_header_comment()
        try:
            with open(self.__platformio_ini_path, "r", encoding="utf-8") as f:
                config.read_file(f)
        except configparser.Error as exc:
            raise ValueError(
                f"Invalid platformio.ini:\n"
                f"    {self.__platformio_ini_path}\n"
                f"    {exc}"
            ) from exc

        return config, header_comment

    def store_dry_run_output(self, verbose: bool = False) -> Path:
        """
        See convenience function `store_dry_run_output(..)` for docs.
        """
        print("")
        print_info("Running dry-run build...")

        # & Preparations
        config, header_comment = self.__load_config()
        self.__ensure_pre_scripts_exist()
        self.__store_backup_platformio_ini(config, header_comment)
        self.__ensure_pre_scripts_referenced(config, header_comment)

        # $ Remove old build_commands.json
        if self.__build_commands_path.exists():
            self.__build_commands_path.unlink()

        # & Run dry-run build
        try:
            env = os.environ.copy()
            env["PIO_DRY_RUN"] = "1"
            # Preserve color output in subprocess
            env["FORCE_COLOR"] = "1"
            pio_executable = self.__find_pio_executable()
            print_info(f"Found pio executable at:")
            print_path(pio_executable)

            if verbose:
                print("\n\n--- START DRY RUN OUTPUT ---")
                # Stream output directly to preserve colors
                result = subprocess.run(
                    [pio_executable, "run", "-d", str(self.__project_path)],
                    env=env,
                    timeout=300,  # 5 minute timeout
                )
                print("--- END DRY RUN OUTPUT ---\n\n")
            else:
                # Capture output for error checking but don't print
                result = subprocess.run(
                    [pio_executable, "run", "-d", str(self.__project_path)],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

            if result.returncode != 0:
                if verbose:
                    # In verbose mode, error was already shown
                    raise RuntimeError(
                        f"Dry-run build failed with exit code "
                        f"{result.returncode}"
                    )
                else:
                    # In non-verbose mode, show captured error
                    raise RuntimeError(
                        f"Dry-run build failed with exit code "
                        f"{result.returncode}.\n"
                        f"stderr: {result.stderr}\n"
                    )

        except subprocess.TimeoutExpired:
            raise RuntimeError("Dry-run build timed out")

        # & Process Results
        # $ Check if build_commands.json was created
        if not self.__build_commands_path.exists():
            raise RuntimeError(
                f"build_commands.json not created at "
                f"{self.__build_commands_path}.\n"
                f"The dry-run build may have failed silently."
            )
        return self.__build_commands_path

    def apply_build_filters(
        self,
        user_exclude_sources_list: List[str],
        user_include_hdirs_list: List[str],
        framework_exclude_sources_list: List[str],
        framework_exclude_hdirs_list: List[str],
        verbose: bool = False,
    ) -> None:
        """
        See convenience function `apply_build_filters(..)` for docs.
        """
        print("")
        print_info("Applying filters on project...")

        # & Preparations
        config, header_comment = self.__load_config()
        self.__ensure_pre_scripts_exist()
        self.__store_backup_platformio_ini(config, header_comment)
        self.__ensure_pre_scripts_referenced(config, header_comment)

        # & Get environment sections
        # PlatformIO projects should have at least one 'environment section' in
        # the `platformio.ini` file.
        env_sections = [
            section
            for section in config.sections()
            if section.startswith("env:")
        ]
        if not env_sections:
            raise ValueError("No environment sections found in platformio.ini")

        # & Process each environment section
        for env_section in env_sections:
            print_info(f"Process {env_section}...")

            # $ Update `framework_exclude_sources`
            value_list: List[str] = []
            print_info("Framework source files to exclude:")
            value_list = self.__update_framework_exclude_sources(
                config, env_section, framework_exclude_sources_list
            )
            print_list(value_list)

            # $ Update `framework_exclude_hdirs`
            print_info("Framework hdirs to exclude:")
            value_list = self.__update_framework_exclude_hdirs(
                config, env_section, framework_exclude_hdirs_list
            )
            print_list(value_list)

            # $ Update `build_src_filter`
            print_info("User source files to exclude:")
            value_list = self.__update_build_src_filter(
                config, env_section, user_exclude_sources_list
            )
            print_list(value_list)

            # $ Update `build_flags`
            print_info("User hdirs to include(!):")
            value_list = self.__update_build_flags(
                config, env_section, user_include_hdirs_list
            )
            print_list(value_list)
            continue

        # & Save updated configuration
        # Write the updated config with preserved header
        with open(self.__platformio_ini_path, "w+", encoding="utf-8") as f:
            # Write header comment first if it exists
            if header_comment:
                f.write(header_comment)
                f.write("\n\n")
            config.write(f)
            # Post-processing cleanup:
            # Strips all trailing whitespace and ensure exactly one final
            # newline. This matches the behavior in PlatformIO's `save()`
            # method in `platformio/project/config.py`.
            f.seek(0)
            contents = f.read()
            f.seek(0)
            f.truncate()
            f.write(contents.strip() + "\n")
        print_info("Update platformio.ini successful, filters installed\n")
        return

    def __update_framework_exclude_sources(
        self,
        config: configparser.ConfigParser,
        env_section: str,
        framework_exclude_sources_list: List[str],
    ) -> List[str]:
        """
        Update `framework_exclude_sources` variable in the `config` parameter
        that represents `platformio.ini`.

        Args:
            config:                         ConfigParser object to modify
            env_section:                    Environment section name
            framework_exclude_sources_list: List of framework source files to
                                            exclude (absolute paths)

        Returns:
            List of values that belong to `framework_exclude_sources_list`

        IMPORTANT:
        This method updates the `framework_exclude_sources` variable in the
        `config` parameter. The returned list is solely for printing purposes.
        """
        # $ CONVERT
        # Convert absolute paths to framework-relative paths with wildcard
        # prefix, keep in `value_list`.
        value_list: List[str] = []
        if framework_exclude_sources_list:
            for abspath in framework_exclude_sources_list:
                value = self.__convert_to_framework_relpath(abspath)
                if value:
                    value_list.append(value)

        # $ STORE
        if value_list:
            value_str = "\n" + "\n".join(f"{v}" for v in value_list)
            config.set(env_section, "framework_exclude_sources", value_str)
        else:
            # Remove the option from `config`
            if config.has_option(env_section, "framework_exclude_sources"):
                config.remove_option(env_section, "framework_exclude_sources")
        return value_list

    def __update_framework_exclude_hdirs(
        self,
        config: configparser.ConfigParser,
        env_section: str,
        framework_exclude_hdirs_list: List[str],
    ) -> List[str]:
        """
        Update `framework_exclude_hdirs` variable in the `config` parameter
        that represents `platformio.ini`.

        Args:
            config:                       ConfigParser object to modify
            env_section:                  Environment section name
            framework_exclude_hdirs_list: List of framework directories to
                                          exclude (absolute paths)

        Returns:
            List of values that belong to `framework_exclude_hdirs`

        IMPORTANT:
        This method updates the `framework_exclude_hdirs` variable in the
        `config` parameter. The returned list is solely for printing purposes.
        """
        # $ CONVERT
        # Convert absolute paths to framework-relative paths with wildcard
        # prefix, keep in `value_list`.
        value_list = []
        if framework_exclude_hdirs_list:
            for abspath in framework_exclude_hdirs_list:
                value = self.__convert_to_framework_relpath(
                    abspath.rstrip("/\\")
                )
                if value:
                    value_list.append(value)

        # $ STORE
        if value_list:
            value_str = "\n" + "\n".join(f"{v}" for v in value_list)
            config.set(env_section, "framework_exclude_hdirs", value_str)
        else:
            # Remove the option from `config`
            if config.has_option(env_section, "framework_exclude_hdirs"):
                config.remove_option(env_section, "framework_exclude_hdirs")
        return value_list

    def __update_build_src_filter(
        self,
        config: configparser.ConfigParser,
        env_section: str,
        user_exclude_sources_list: List[str],
    ) -> List[str]:
        """
        Update `build_src_filter` variable in the `config` parameter that
        represents `platformio.ini`.

        Args:
            config:                    ConfigParser object to modify
            env_section:               Environment section name
            user_exclude_sources_list: List of user source files to exclude
                                       (relative to project root)

        Returns:
            List of values that belong to `build_src_filter`

        WARNING:
        > user_exclude_sources_list: Paths relative to project root
        > build_src_filter (in platformio.ini): Paths relative to project source
                                                (usually <project>/src)

        IMPORTANT:
        This method updates the `build_src_filter` variable in the `config`
        parameter. The returned list is only for printing purposes.
        """
        # $ CONVERT
        # Create exclusion pattern for each given source file.
        value_list: List[str] = []
        if user_exclude_sources_list:
            # Get the actual source directory from `platformio.ini`. Usually
            # that would be `<project>/src`, but can also be specified as
            # another folder by the user.
            proj_src_dir = self.__get_project_src_dir(config)

            for rel_to_proj_root in user_exclude_sources_list:
                abspath = (self.__project_path / rel_to_proj_root).resolve()
                try:
                    # $ STEP 1:
                    # Convert from 'relative to project root' to 'relative to
                    # project source folder'
                    rel_to_proj_src = abspath.relative_to(proj_src_dir)

                    # $ STEP 2:
                    # Wrap in '-<..>' (prefix '-<' and suffix '>')
                    value = f"-<{rel_to_proj_src.as_posix()}>"

                    # $ STEP 3:
                    # Store exclusion pattern in `value_list`
                    value_list.append(value)
                except ValueError:
                    print_warn(
                        f"Path not in source directory "
                        f'"<project>/{proj_src_dir.relative_to(self.__project_path)}", '
                        f"will be skipped:\n"
                        f"    {Fore.RED}{rel_to_proj_root}{Fore.RESET}"
                    )
                    continue

        # $ STORE
        if value_list:
            value_str = "\n+<*>\n" + "\n".join(f"{v}" for v in value_list)
            config.set(env_section, "build_src_filter", value_str)
        else:
            # Remove the option if no exclusions
            if config.has_option(env_section, "build_src_filter"):
                config.remove_option(env_section, "build_src_filter")
        return value_list

    def __update_build_flags(
        self,
        config: configparser.ConfigParser,
        env_section: str,
        user_include_hdirs_list: List[str],
    ) -> List[str]:
        """
        Update `build_flags` variable in the `config` parameter that represents
        `platformio.ini`.

        Args:
            config:                  ConfigParser object to modify
            env_section:             Environment section name
            user_include_hdirs_list: List of user hdirs to include(!)
                                     (relative paths)

        Returns:
            List of values that belong to `build_flags`

        IMPORTANT:
        This method updates the `build_flags` variable in the `config` para-
        meter. The returned list is solely for printing purposes.
        """
        # $ CONVERT
        # Prefix the given user include directories (relative to project root)
        # with '-I'. That's all what's needed to convert them to the required
        # flags.
        value_list: List[str] = []
        if user_include_hdirs_list:
            for hdir in user_include_hdirs_list:
                value = f"-I{hdir}"
                value_list.append(value)

        # $ STORE
        if value_list:
            value_str = "\n" + "\n".join(f"{v}" for v in value_list)
            config.set(env_section, "build_flags", value_str)
        else:
            # Remove the option from `config`
            if config.has_option(env_section, "build_flags"):
                config.remove_option(env_section, "build_flags")
        return value_list

    # ---------------------------[ HELP FUNCTIONS ]--------------------------- #

    def __store_backup_platformio_ini(
        self,
        config: configparser.ConfigParser,
        header_comment: str,
    ) -> None:
        """
        The first time(*) this `sa_bridge.py` script runs, it should backup the
        `<project>/platformio.ini` file to:
            1. `<project>/platformio.ini.bkp`
                  Backup for user

            2. `<project>/.beetle/platformio_ini_orig.json`
                  Backup for Johan's SA. Stores initial settings of project in
                  json-format for easy parsing.

        (*) To check if it's the first time this `sa_bridge.py` runs, it
        checks if the json-file already exists.

        Args:
            config: [Optional] The config of the current `platformio.ini` file.
                    Pass it here to avoid having to read it again.

        Raise:
            FileNotFoundError: platformio.ini was not found.

            ValueError: The platformio.ini file could not be parsed.
        """
        ini_bkp_path = self.__platformio_ini_path.with_suffix(".ini.bkp")
        json_bkp_path = (
            self.__project_path / ".beetle" / "platformio_ini_orig.json"
        )
        if json_bkp_path.exists():
            return

        # & JSON BACKUP
        config_dict = {}
        for section_name in config.sections():
            config_dict[section_name] = {}
            for option in config.options(section_name):
                config_dict[section_name][option] = config.get(
                    section_name, option
                )
        json_bkp_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_bkp_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        print_info("Create JSON backup at:")
        print_path(json_bkp_path)

        # & INI BACKUP
        if not ini_bkp_path.exists():
            shutil.copy2(self.__platformio_ini_path, ini_bkp_path)
            print_info("Create user backup at:")
            print_path(ini_bkp_path)
        else:
            print_info("User backup already exists at:")
            print_path(ini_bkp_path)
        return

    def __extract_header_comment(self) -> str:
        """
        Returns:
            Header comment block from platformio.ini as string, or empty string
            if none found.
        """
        if not self.__platformio_ini_path.exists():
            return ""

        header_lines = []
        try:
            with open(self.__platformio_ini_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    # Stop at first non-comment, non-empty line
                    if stripped_line and not stripped_line.startswith(
                        (";", "#")
                    ):
                        break
                    # Keep comment lines and empty lines at the start
                    header_lines.append(line.rstrip("\n\r"))

        except Exception:
            # If we can't read the file, return empty header
            return ""

        # Remove trailing empty lines from header
        while header_lines and not header_lines[-1].strip():
            header_lines.pop()

        return "\n".join(header_lines) if header_lines else ""

    def __extract_script_version(self, script_path: Path) -> Optional[str]:
        """
        Args:
            script_path:    Path to the script file

        Returns:
            Version string from PRE-script if found, None otherwise
        """
        if not script_path.exists():
            return None
        version_prefix = "SCRIPT_VERSION"

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                # Only check the first few lines for performance
                for i, line in enumerate(f):
                    if i > 10:
                        break

                    line = line.strip()
                    if line.startswith("#") and version_prefix in line:
                        # Extract version from line like:
                        # # SCRIPT_VERSION = "1.0.0"
                        if "=" in line:
                            version_part = line.split("=", 1)[1].strip()
                            version_part = version_part.strip("\"'")
                            return version_part

        except Exception as e:
            print_warn(
                f"Could not read version from:\n"
                f'    "{script_path}"\n'
                f"    {e}"
            )

        return None

    def __convert_to_framework_relpath(self, abspath: str) -> str:
        """
        Convert an absolute path to a framework-relative path with wildcard
        prefix.

        Examples:
            "C:/Users/krist/.platformio/packages/framework-wch-noneos-sdk/
                Peripheral/ch32v00x/src/ch32v00x_adc.c"

                -> "*/Peripheral/ch32v00x/src/ch32v00x_adc.c"

            "/home/user/.platformio/packages/framework-arduino-esp32/
                cores/esp32/Arduino.h"

                -> "*/cores/esp32/Arduino.h"
        """
        # Normalize path separators
        normalized_path = abspath.replace("\\", "/")

        # Look for framework directory pattern: */packages/framework-*
        packages_framework_pattern = "/packages/framework-"

        # Find the framework directory
        framework_start = normalized_path.find(packages_framework_pattern)
        if framework_start == -1:
            print_warn(
                f"Path not in framework directory, will be skipped:\n"
                f'    {Fore.RED}"{abspath}"{Fore.RESET}'
            )
            return ""

        # Find the end of the framework directory name
        # Framework directory ends at the next '/' after 'framework-'
        framework_name_start = framework_start + len(packages_framework_pattern)
        framework_end = normalized_path.find("/", framework_name_start)
        if framework_end == -1:
            # Path is the framework directory itself
            print_warn(
                f"Path is framework directory itself, will be skipped:\n"
                f'    {Fore.RED}"{abspath}"{Fore.RESET}'
            )
            return ""

        # Extract the relative path within the framework
        relpath = normalized_path[framework_end + 1 :]  # +1 to skip the '/'
        if not relpath:
            print_warn(
                f"No relative path found within framework, will be skipped:\n"
                f'    {Fore.RED}"{abspath}"{Fore.RESET}'
            )
            return ""

        # Return with wildcard prefix for pattern matching
        return f"*/{relpath}"

    def __ensure_pre_scripts_exist(self) -> None:
        """
        Ensure that both `dry_run.py` and `filter_hook.py` scripts exist in the
        `.beetle` directory and are up-to-date. Create or update them if missing
        or outdated.
        """
        # Create `<project>/.beetle` directory
        beetle_dir = self.__project_path / ".beetle"
        beetle_dir.mkdir(exist_ok=True)

        # & dry_run.py
        # Check and create/update `dry_run.py`
        dry_run_needs_update = False
        reason: Optional[str] = None
        if not self.__dry_run_path.exists():
            dry_run_needs_update = True
            reason = "missing"
        else:
            # Check version
            current_version = self.__extract_script_version(self.__dry_run_path)
            if current_version is None:
                dry_run_needs_update = True
                reason = "no version found (outdated)"
            elif current_version != SCRIPT_VERSION:
                dry_run_needs_update = True
                reason = str(
                    f"version mismatch (current: {current_version}, "
                    f"required: {SCRIPT_VERSION})"
                )

        if dry_run_needs_update:
            with open(self.__dry_run_path, "w", encoding="utf-8") as f:
                f.write(DRY_RUN_SCRIPT)
            print_info(f"Update dry_run.py (reason for update: {reason}):")
            print_path(self.__dry_run_path)

        # & filter_hook.py
        # Check and create/update `filter_hook.py`
        filter_hook_needs_update = False
        if not self.__filter_hook_path.exists():
            filter_hook_needs_update = True
            reason = "missing"
        else:
            # Check version
            current_version = self.__extract_script_version(
                self.__filter_hook_path
            )
            if current_version is None:
                filter_hook_needs_update = True
                reason = "no version found (outdated)"
            elif current_version != SCRIPT_VERSION:
                filter_hook_needs_update = True
                reason = str(
                    f"version mismatch (current: {current_version}, "
                    f"required: {SCRIPT_VERSION})"
                )

        if filter_hook_needs_update:
            with open(self.__filter_hook_path, "w", encoding="utf-8") as f:
                f.write(FILTER_HOOK_SCRIPT)
            print_info(f"Update filter_hook.py (reason for update: {reason}):")
            print_path(self.__filter_hook_path)
        return

    def __ensure_pre_scripts_referenced(
        self,
        config: configparser.ConfigParser,
        header_comment: str,
    ) -> None:
        """
        Ensure `platformio.ini` references `dry_run.py` and `filter_hook.py` for
        all env sections. Create if needed.

        Raise:
            FileNotFoundError: platformio.ini was not found.

            ValueError: The platformio.ini file could not be parsed.
        """
        env_sections = [
            section
            for section in config.sections()
            if section.startswith("env:")
        ]
        if not env_sections:
            raise ValueError("No environment sections found in platformio.ini")

        required_scripts = [
            "pre:.beetle/dry_run.py",
            "pre:.beetle/filter_hook.py",
        ]
        config_modified = False

        # Process all environment sections
        for env_section in env_sections:
            if config.has_option(env_section, "extra_scripts"):
                current_scripts = config.get(env_section, "extra_scripts")

                # Parse existing scripts (handle multiline format)
                if current_scripts:
                    scripts_list = [
                        script.strip()
                        for script in current_scripts.split("\n")
                        if script.strip()
                    ]
                else:
                    scripts_list = []

                # Check if required scripts are missing
                missing_scripts = [
                    script
                    for script in required_scripts
                    if script not in scripts_list
                ]

                if missing_scripts:
                    for script in reversed(missing_scripts):
                        scripts_list.insert(0, script)
                    extra_scripts_value = "\n" + "\n".join(
                        f"{script}" for script in scripts_list
                    )
                    config.set(
                        env_section, "extra_scripts", extra_scripts_value
                    )
                    config_modified = True
            else:
                # No extra_scripts yet, create it with both scripts
                extra_scripts_value = "\n" + "\n".join(
                    f"{script}" for script in required_scripts
                )
                config.set(env_section, "extra_scripts", extra_scripts_value)
                config_modified = True

        # Save changes if any modifications were made
        if config_modified:
            header_comment = self.__extract_header_comment()
            with open(self.__platformio_ini_path, "w+", encoding="utf-8") as f:
                if header_comment:
                    f.write(header_comment)
                    f.write("\n\n")
                config.write(f)
                # Post-processing cleanup
                f.seek(0)
                contents = f.read()
                f.seek(0)
                f.truncate()
                f.write(contents.strip() + "\n")
            print_info(f"Add PRE-script references to platformio.ini")
        else:
            print_info(f"PRE-script references already in platformio.ini")
        return

    def __find_pio_executable(self) -> str:
        """
        Returns:
            Path to pio executable

        Raises:
            FileNotFoundError: If pio executable not found
        """
        # First try the standard platformio location
        home_dir = Path.home()
        potential_paths = [
            home_dir / ".platformio" / "penv" / "Scripts" / "pio.exe",
            # Windows
            home_dir / ".platformio" / "penv" / "Scripts" / "pio",
            # Windows without .exe
            home_dir / ".platformio" / "penv" / "bin" / "pio",  # Linux/Mac
        ]

        for path in potential_paths:
            if path.exists():
                return str(path).replace("\\", "/")

        # Try to find pio on PATH
        pio_path = shutil.which("pio")
        if pio_path:
            return str(pio_path).replace("\\", "/")

        raise FileNotFoundError(
            f"Cannot find pio executable. Please ensure PlatformIO is "
            f"installed and either available on PATH or located at "
            f"~/.platformio/penv/Scripts/pio"
        )

    def __get_project_src_dir(self, config: configparser.ConfigParser) -> Path:
        """
        Get the actual source directory for this PlatformIO project. Usually
        `<project>/src`, unless the user specified `src_dir` in the project's
        `platformio.ini`, for example:

            ```ini
            [platformio]
            src_dir = firmware/src
            include_dir = firmware/include
            lib_dir = firmware/lib
            ```

        Args:
            config: ConfigParser object with platformio.ini loaded

        Returns:
            Path: Absolute path to the project's source directory
        """
        # Get src_dir from [platformio] section, default to "src"
        src_dir = "src"  # Default value

        if config.has_section("platformio") and config.has_option(
            "platformio", "src_dir"
        ):
            src_dir = config.get("platformio", "src_dir")

        # Handle variable substitution (basic ${PROJECT_DIR} replacement)
        src_dir = src_dir.replace("${PROJECT_DIR}", str(self.__project_path))

        # Convert to absolute path
        if os.path.isabs(src_dir):
            return Path(src_dir).resolve()
        return (self.__project_path / src_dir).resolve()


# ========================== CONVENIENCE FUNCTIONS =========================== #


def store_dry_run_output(
    project_path: Optional[str] = None,
    verbose: bool = False,
) -> Path:
    """
    CONVENIENCE FUNCTION

    Run a dry-run build and store the commands and file information in
    `<project>/.beetle/build_commands.json`.

    Args:
        verbose: Verbose output

    Returns:
        Absolute path to `build_commands.json`.

    Raises:
        FileNotFoundError: If dry_run.py script or pio executable not found
        RuntimeError:      If dry-run build fails or build_commands.json not
                           created
    """
    if not project_path:
        project_path = os.getcwd()
    try:
        bridge = SourceAnalyzerBridge(project_path)
        build_commands_path: Path = bridge.store_dry_run_output(verbose)
    except Exception as e:
        print_err(f"{e}\n")
        print("Run --help for more info\n")
        sys.exit(1)
    return build_commands_path


def apply_build_filters(
    project_path: Optional[str],
    user_exclude_sources: List[str],
    user_include_hdirs: List[str],
    framework_exclude_sources: List[str],
    framework_exclude_hdirs: List[str],
    verbose: bool = False,
) -> None:
    """
    CONVENIENCE FUNCTION

    Upon completion of this function, `platformio.ini` lists the exclude/include
    files and hdirs such that only relevant ones get compiled. The function also
    ensures that the required PRE-scripts are present in `<project>/.beetle`.

    Args:
        project_path:              [Optional] Path to the PlatformIO project
                                   directory. Defaults to CWD if not provided.

        user_exclude_sources:      List of user source files to exclude
                                   (relative paths)

        user_include_hdirs:        List of user hdirs to include(!)
                                   (relative paths)

        framework_exclude_sources: List of framework source files to exclude
                                   (absolute paths)

        framework_exclude_hdirs:   List of framework hdirs to exclude
                                   (absolute paths)

        verbose:                   Enable verbose output

    Raise:
        FileNotFoundError: platformio.ini was not found.

        ValueError: The platformio.ini file could not be parsed.

    Note that comments are lost when the configparser writes `platformio.ini`.
    That's consistent with PlatformIO's own behavior.
    """
    if not project_path:
        project_path = os.getcwd()
    try:
        bridge = SourceAnalyzerBridge(project_path)
        bridge.apply_build_filters(
            user_exclude_sources_list=user_exclude_sources,
            user_include_hdirs_list=user_include_hdirs,
            framework_exclude_sources_list=framework_exclude_sources,
            framework_exclude_hdirs_list=framework_exclude_hdirs,
            verbose=verbose,
        )
    except Exception as e:
        print_err(f"{e}\n")
        print("Run --help for more info\n")
        sys.exit(1)
    return


# ================ MAIN ENTRY FOR STANDALONE SCRIPT OPERATION ================ #


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Source Analyzer Bridge for PlatformIO",
        add_help=False,  # Disable default help to use custom help
    )

    # & ADD ARGUMENTS
    # & =============
    parser.add_argument(
        "-d",
        "--dir",
        dest="project_path",
        default=os.getcwd(),
        help=str(
            "Path to the PlatformIO project directory (default: current "
            "working directory)"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Show help message and exit",
    )
    # If --test is entered, no explicit filtering lists may be given.
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Provide test data for the exclude/include lists",
    )

    # If --dry-run is entered, no filtering lists may be given - not even the
    # test data.
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run dry-run build and print the output",
    )
    parser.add_argument(
        "--user-exclude-sources",
        type=str,
        default="",
        help=str(
            "User source files to exclude (relative paths)."
            'Format: "[src/file1.c, src/file2.c, ...]"'
        ),
        metavar='"[FILES,...]"',
    )
    parser.add_argument(
        "--user-include-hdirs",
        type=str,
        default="",
        help=str(
            "User hdirs to include(!) (relative paths)."
            'Format: "[src/dir1, src/dir2, ...]"'
        ),
        metavar='"[DIRS,...]"',
    )
    parser.add_argument(
        "--framework-exclude-sources",
        type=str,
        default="",
        help=str(
            "Framework source files to exclude (absolute paths)."
            'Format: "/abs/path/file1.c, /abs/path/file2.c, ...]"'
        ),
        metavar='"[FILES,...]"',
    )
    parser.add_argument(
        "--framework-exclude-hdirs",
        type=str,
        default="",
        help=str(
            "Framework header directories to exclude (absolute paths). "
            'Format: "[/abs/path/dir1, /abs/path/dir2, ...]"'
        ),
        metavar='"[DIRS,...]"',
    )
    args = parser.parse_args()

    # & PARSE ARGUMENTS AND RUN SCRIPT
    # & ==============================
    # $ HELP
    # Show help message and quit
    if args.help:
        _help()
        sys.exit(0)

    # $ DRY-RUN MODE
    # Check for ambiguous situation: --dry-run with other arguments
    if args.dry_run:
        # Check if user also provided conflicting arguments
        conflicting_args = []
        for action in parser._actions:
            if action.dest in [
                "test",
                "user_exclude_sources",
                "user_include_hdirs",
                "framework_exclude_sources",
                "framework_exclude_hdirs",
            ]:
                # Check if this argument was explicitly provided on command line
                if any(opt in sys.argv for opt in action.option_strings):
                    conflicting_args.extend(action.option_strings)

        if conflicting_args:
            print_err(
                "Cannot use --dry-run with other mode args:\n    "
                + "\n    ".join([f"  {arg}" for arg in conflicting_args])
            )
            print("")
            sys.exit(1)

        # Run dry-run and print output
        build_commands_path: Path = store_dry_run_output(
            project_path=args.project_path,
            verbose=args.verbose,
        )
        print_info("Dry-run output written to:")
        print_path(build_commands_path)
        if args.verbose:
            print_info("build_commands.json:")
            try:
                with open(build_commands_path, "r", encoding="utf-8") as f:
                    _dry_run_output = json.load(f)
            except json.JSONDecodeError as e:
                print_err(f"Invalid JSON in build_commands.json:\n{e}\n")
            print(Fore.GRAY + json.dumps(_dry_run_output, indent=2))
        else:
            print_info("Use --verbose to see the detailed output in stdout")
        print("")
        sys.exit(0)

    # $ TEST MODE
    # Check for ambiguous situation: --test with explicit list arguments
    if args.test:
        # Check if user also provided any of the SA input arguments
        conflicting_args = []
        for action in parser._actions:
            if action.dest in [
                "user_exclude_sources",
                "user_include_hdirs",
                "framework_exclude_sources",
                "framework_exclude_hdirs",
            ]:
                # Check if this argument was explicitly provided on command line
                if any(opt in sys.argv for opt in action.option_strings):
                    conflicting_args.extend(action.option_strings)

        if conflicting_args:
            print_err(
                "Cannot use --test mode with explicit filter args:\n    "
                + "\n    ".join([f"  {arg}" for arg in conflicting_args])
                + "\nEither use --test for sample data OR provide explicit "
                + "arguments, but not both."
            )
            print("")
            sys.exit(1)

        # Provide fake data if --test is entered (and no conflicts)
        args.user_exclude_sources = "[src/file1.c, src/file2.c]"
        args.user_include_hdirs = "[src/dir1, src/dir2]"
        tmp1 = "C:/Users/krist/.platformio/packages/framework-wch-noneos-sdk/Peripheral/ch32v00x/src/ch32v00x"
        tmp2 = "C:/Users/krist/.platformio/packages/framework-wch-noneos-sdk/Debug/ch32v00x"
        args.framework_exclude_sources = str(
            f"["
            f"{tmp1}_adc.c, "
            f"{tmp1}_dma.c, "
            f"{tmp1}_exti.c, "
            f"{tmp1}_i2c.c, "
            f"{tmp1}_spi.c, "
            f"{tmp1}_usart.c, "
            f"{tmp2}/debug.c"
            f"]"
        )
        args.framework_exclude_hdirs = str(f"[" f"{tmp2}" f"]")

    # $ PRODUCTION MODE
    # Verify required arguments are provided (unless --test or --dry-run mode is
    # used).
    if not args.test and not args.dry_run:
        # Check if these arguments were explicitly provided (not just defaults)
        provided_args = set()
        for action in parser._actions:
            if action.dest in [
                "user_exclude_sources",
                "user_include_hdirs",
                "framework_exclude_sources",
                "framework_exclude_hdirs",
            ]:
                # Check if this argument was actually provided on command line
                if any(opt in sys.argv for opt in action.option_strings):
                    provided_args.add(action.dest)

        required_args = {
            "user_exclude_sources": "--user-exclude-sources",
            "user_include_hdirs": "--user-include-hdirs",
            "framework_exclude_sources": "--framework-exclude-sources",
            "framework_exclude_hdirs": "--framework-exclude-hdirs",
        }

        missing_required = []
        for arg_dest, arg_name in required_args.items():
            if arg_dest not in provided_args:
                missing_required.append(arg_name)

        if missing_required:
            print("")
            print_info(
                "Missing arguments default to empty list:\n    "
                + "\n    ".join([f"  {arg} = []" for arg in missing_required])
            )

    def __parse_comma_separated_list(value: str) -> List[str]:
        # Parse comma-separated list from string format "[item1, item2, ...]" or
        # "item1, item2, ..." into list of strings.
        if not value or not value.strip():
            return []
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        items = []
        if value.strip():
            for item in value.split(","):
                item = item.strip()
                if item:
                    items.append(item)
        return items

    apply_build_filters(
        project_path=args.project_path,
        user_exclude_sources=__parse_comma_separated_list(
            args.user_exclude_sources,
        ),
        user_include_hdirs=__parse_comma_separated_list(
            args.user_include_hdirs,
        ),
        framework_exclude_sources=__parse_comma_separated_list(
            args.framework_exclude_sources,
        ),
        framework_exclude_hdirs=__parse_comma_separated_list(
            args.framework_exclude_hdirs,
        ),
        verbose=args.verbose,
    )
    sys.exit(0)


# =========================== PRE-SCRIPTS CONTENTS =========================== #
# CRITICAL:
# Remember to update the SCRIPT_VERSION variable at the top of this file when
# modifying the PRE-SCRIPTS below!

DRY_RUN_SCRIPT = (
    """#!/usr/bin/env python3\n"""
    + f'''# SCRIPT_VERSION = "{SCRIPT_VERSION}"'''
    + '''
# Copyright © 2018-2025 Johan Cockx, Matic Kukovec & Kristof Mulier

"""
PlatformIO PRE Script: True Dry Run Implementation
Implements --dry-run functionality by replacing SCons spawn with command
capture.

Usage:
    1. Set environment variable: PIO_DRY_RUN=1
    2. Run: pio run (commands will be logged instead of executed)

Output:
    `<project>/.beetle/build_commands.json` contains all commands
"""

import os
import sys
import json
from os.path import join, abspath
from typing import Any, List, Union, Callable
from colorama import init, Fore

# Import the SCons environment
Import("env")


def print_info(msg: str = "") -> None:
    if msg:
        print(f"{Fore.LIGHTGREEN_EX}[DRY RUN]{Fore.RESET} {msg}")
    return


def print_warn(msg: str = "") -> None:
    if msg:
        print(f"{Fore.LIGHTRED_EX}[DRY RUN]{Fore.RESET} {msg}")
    return


def print_err(msg: str = "") -> None:
    if msg:
        print(f"{Fore.RED}[DRY RUN]{Fore.RESET} {msg}", file=sys.stderr)
    return


def is_dry_run_enabled() -> bool:
    """
    Check if dry-run mode is enabled
    """
    # Check environment variable first
    if os.environ.get("PIO_DRY_RUN", "").lower() in ("1", "true", "yes"):
        return True
    return False


def get_dry_run_output_file() -> str:
    """
    Get the path for the dry-run output file, which is at:
    <project>/.beetle/build_commands.json
    """
    project_dir = env.get("PROJECT_DIR", "")
    if project_dir:
        return abspath(join(project_dir, ".beetle", "build_commands.json"))
    return abspath(join(".beetle", "build_commands.json"))


class DryRunCommandLogger:
    """
    Captures and logs build commands instead of executing them. Outputs to JSON
    format following the specified template.
    """

    def __init__(self, output_file):
        self.output_file = output_file
        self.command_count = 0
        self.commands = []  # List of command entries for JSON output
        self.path_prepend = []  # List of directories prepended to PATH

        print_info(f"Logging commands to {self.output_file}")

        # Initialize with empty lists
        self.commands = []
        self.path_prepend = []

    def log_spawn_command(
        self, sh, escape, cmd, args, env_vars, working_dir=None
    ):
        """
        Log a spawn command that would be executed.

        Args:
            sh: Shell
            escape: Escape function
            cmd: Command program
            args: Command arguments list
            env_vars: Environment variables
            working_dir: Working directory
        """
        self.command_count += 1

        # Convert args to command string
        if isinstance(args, (list, tuple)):
            cmd_str = " ".join(str(arg) for arg in args)
        else:
            cmd_str = str(args)

        # Determine command type
        description = "Shell command"
        if (
            "gcc" in cmd_str
            or "g++" in cmd_str
            or "riscv-none-embed-gcc" in cmd_str
        ):
            description = "Compile"
        elif "ar " in cmd_str or "ranlib" in cmd_str:
            description = "Archive"
        elif "objdump" in cmd_str:
            description = "Object dump"
        elif "objcopy" in cmd_str:
            description = "Object copy"

        # Parse command to extract file information
        source_file, output_file = self._parse_command_files(cmd_str)

        # Create JSON entry
        entry = {
            "command": cmd_str.replace("\\\\", "/"),
            "directory": (working_dir or os.getcwd()).replace("\\\\", "/"),
            "file": source_file,
            "output": output_file,
        }

        self.commands.append(entry)

        # Print to console
        print_info(f"Dry Run [{self.command_count}]: {description}")
        if len(cmd_str) > 120:
            print_info(f" {cmd_str[:120]}...")
        else:
            print_info(f" {cmd_str}")

        return 0  # Simulate successful execution

    def capture_path_prepend(self, env):
        """
        Capture the directories that PlatformIO prepends to PATH.

        Args:
            env: SCons environment object
        """
        try:
            # Get the current PATH from the SCons environment
            current_path = env.get("ENV", {}).get("PATH", "")
            if current_path:
                # Split PATH and normalize paths to use forward slashes
                path_dirs = current_path.split(os.pathsep)
                # Filter to only include PlatformIO package directories
                pio_dirs = []
                for path_dir in path_dirs:
                    normalized_dir = path_dir.replace("\\\\", "/")
                    # Include directories that are under .platformio/packages
                    if (
                        "/.platformio/packages/" in normalized_dir
                        or "\\\\.platformio\\\\packages\\\\" in path_dir
                    ):
                        pio_dirs.append(normalized_dir)

                self.path_prepend = pio_dirs
                print_info(
                    f"Captured {len(pio_dirs)} PlatformIO PATH directories"
                )
            else:
                print_warn("No PATH found in environment")
        except Exception as e:
            print_err(f"Error capturing PATH: {e}")

    def _parse_command_files(self, cmd_str):
        """
        Parse command string to extract source file and output file.

        Args:
            cmd_str: Command string to parse

        Returns:
            tuple: (source_file, output_file)
        """
        try:
            import shlex

            # Use shlex to properly parse quoted arguments
            args = shlex.split(cmd_str)
            source_file = ""
            output_file = ""

            # Parse arguments to find input and output files
            for i, arg in enumerate(args):
                # Find output file (after -o flag)
                if arg == "-o" and i + 1 < len(args):
                    output_file = abspath(args[i + 1].strip('"')).replace(
                        "\\\\", "/"
                    )
                # Find source file (file extensions, not starting with -)
                elif arg.endswith(
                    (".c", ".cpp", ".cc", ".cxx", ".S", ".s")
                ) and not arg.startswith("-"):
                    # Clean quotes and make absolute path
                    clean_arg = arg.strip('"')
                    if os.path.isabs(clean_arg):
                        source_file = clean_arg.replace("\\\\", "/")
                    else:
                        source_file = abspath(clean_arg).replace("\\\\", "/")
                # For linker commands, find .elf output
                elif arg.endswith(".elf"):
                    output_file = abspath(arg.strip('"')).replace("\\\\", "/")
                # For archive commands, find .a output
                elif arg.endswith(".a"):
                    output_file = abspath(arg.strip('"')).replace("\\\\", "/")
                # For objcopy/objdump with redirection, find output files
                elif i > 0 and args[i - 1] == ">":
                    output_file = abspath(arg.strip('"')).replace("\\\\", "/")

            # For linking commands, use the first object file as "file"
            if not source_file and ".o" in cmd_str:
                for arg in args:
                    if arg.endswith(".o") and not arg.startswith("-"):
                        source_file = abspath(arg.strip('"')).replace(
                            "\\\\", "/"
                        )
                        break

            # For archive commands, use the archive file as both input and
            # output
            if "ar " in cmd_str and not source_file:
                for arg in args:
                    if arg.endswith(".a"):
                        source_file = abspath(arg.strip('"')).replace(
                            "\\\\", "/"
                        )
                        break

            return source_file, output_file

        except Exception as e:
            print_err(f"Error parsing command files: {e}")
            return "", ""

    def finalize(self):
        """
        Write all commands to JSON file and finalize the dry run.
        """
        print_info(
            f"\\nDry Run Complete: {self.command_count} commands captured"
        )
        print_info(f"Commands logged to: {self.output_file}")

        # Create the output structure following the template
        output_data = {
            "path_prepend": self.path_prepend,
            "build_commands": self.commands,
        }

        # Write all data to JSON file
        if self.output_file:
            try:
                with open(self.output_file, "w") as f:
                    json.dump(output_data, f, indent=4)
                print_info(
                    f"JSON build commands written to: {self.output_file}"
                )
                print_info(
                    f"Captured {len(self.path_prepend)} PATH directories and "
                    f"{len(self.commands)} build commands"
                )
            except Exception as e:
                print_err(f"Error writing JSON file: {e}")


# Global dry run logger instance
dry_run_logger = None


def dry_run_execute(original_execute: Callable[..., int]) -> Callable[..., int]:
    """
    Wrapper for env.Execute() that logs commands instead of executing them.
    """

    def logged_execute(cmd: Union[str, List[str]], **kwargs: Any) -> int:
        if dry_run_logger:
            dry_run_logger.log_command(cmd, "Direct execute")
            return 0  # Simulate successful execution
        else:
            return original_execute(cmd, **kwargs)

    return logged_execute


def dry_run_spawn_hook() -> bool:
    """
    Install the core dry-run hook by replacing SCons spawn function.
    This is the key mechanism that captures commands without executing them.
    """
    global dry_run_logger

    # Get the current working directory for compile_commands.json
    project_dir = env.get("PROJECT_DIR", os.getcwd())

    def dry_run_spawn(sh, escape, cmd, args, env_vars):
        """
        Replacement spawn function that captures commands instead of executing
        them. This is called by SCons for every shell command execution.

        Args:
            sh: Shell to use
            escape: Escape function
            cmd: Command program
            args: List of command arguments
            env_vars: Environment variables

        Returns:
            int: Exit code (always 0 for success simulation)
        """
        if dry_run_logger:
            return dry_run_logger.log_spawn_command(
                sh, escape, cmd, args, env_vars, project_dir
            )
        else:
            # Fallback to original spawn if dry run logger not available
            return original_spawn(sh, escape, cmd, args, env_vars)

    # Store original spawn function
    global original_spawn
    original_spawn = env.get("SPAWN")

    # Replace spawn function with our dry-run version
    env["SPAWN"] = dry_run_spawn

    print_info("Installed SCons spawn hook (core mechanism)")
    return True


def dry_run_tempfile_hook() -> bool:
    """
    Hook tempfile creation to prevent temporary files during dry run.
    Based on SCons compilation_db tool approach.
    """

    def CompDBTEMPFILE(template, *args, **kwargs):
        """
        Custom tempfile function that returns the template directly.
        This prevents actual temp file creation during command string
        generation.
        """
        return template

    # Override TEMPFILE in environment to prevent temp file creation
    env["TEMPFILE"] = CompDBTEMPFILE
    print_info("Installed tempfile hook")
    return True


def dry_run_builder_hooks() -> bool:
    """
    Hook SCons builders to simulate successful completion.
    This ensures the build dependency graph is processed without actual
    execution.
    """
    # Hook common SCons builders to return mock nodes
    builders_to_hook = [
        "Object",
        "Program",
        "Library",
        "StaticLibrary",
        "SharedLibrary",
    ]

    for builder_name in builders_to_hook:
        if hasattr(env, builder_name):
            try:
                original_builder = getattr(env, builder_name)

                def make_dry_run_builder(orig_builder, name):
                    def dry_run_builder(*args, **kwargs):
                        if dry_run_logger:
                            # Let the builder process normally - spawn hook will
                            # capture commands. But we need to ensure nodes are
                            # created for dependency tracking.
                            try:
                                result = orig_builder(*args, **kwargs)
                                return result
                            except Exception as e:
                                # If builder fails, create a mock node
                                target = args[0] if args else "unknown"

                                class DryRunNode:
                                    def __init__(self, path):
                                        self.path = str(path)

                                    def __str__(self):
                                        return self.path

                                    def get_executor(self):
                                        return None

                                return DryRunNode(target)
                        else:
                            return orig_builder(*args, **kwargs)

                    return dry_run_builder

                setattr(
                    env,
                    builder_name,
                    make_dry_run_builder(original_builder, builder_name),
                )

            except Exception as e:
                print_warn(f"Could not hook {builder_name}: {e}")

    print_info("Installed builder hooks")
    return True


def dry_run_execute_hook() -> bool:
    """
    Hook env.Execute() for direct command execution.
    """
    if hasattr(env, "Execute"):
        original_execute = env.Execute

        def dry_run_execute(cmd, **kwargs):
            if dry_run_logger:
                # Convert command to string
                if isinstance(cmd, (list, tuple)):
                    cmd_str = " ".join(str(arg) for arg in cmd)
                else:
                    cmd_str = str(cmd)

                dry_run_logger.log_spawn_command(
                    None, None, None, cmd_str, None
                )
                return 0  # Simulate successful execution
            else:
                return original_execute(cmd, **kwargs)

        env.Execute = dry_run_execute
        print_info("Installed Execute hook")
        return True

    return False


# Global variables for the original spawn function
original_spawn = None


def install_dry_run_hooks() -> bool:
    """
    Install dry-run hooks into the SCons environment.
    Uses the core spawn replacement strategy for maximum effectiveness.
    """
    global dry_run_logger

    output_file = get_dry_run_output_file()
    dry_run_logger = DryRunCommandLogger(output_file)

    # Capture PATH information from the SCons environment
    dry_run_logger.capture_path_prepend(env)

    print_info("Installing True Dry Run hooks (SCons spawn replacement)")

    # CORE HOOK: Replace SCons spawn function
    # This is the main mechanism that captures ALL shell commands
    try:
        if dry_run_spawn_hook():
            print_info("Core spawn hook installed")
    except Exception as e:
        print_err(f"Failed to install core spawn hook: {e}")
        return False

    # SUPPORTING HOOKS: Additional mechanisms for completeness

    # Hook 1: Prevent tempfile creation (like compilation_db tool)
    try:
        if dry_run_tempfile_hook():
            print_info("Tempfile hook installed")
    except Exception as e:
        print_err(f"Tempfile hook failed: {e}")

    # Hook 2: Hook env.Execute() for direct command execution
    try:
        if dry_run_execute_hook():
            print_info("Execute hook installed")
    except Exception as e:
        print_err(f"Execute hook failed: {e}")

    # Hook 3: Hook builders for dependency tracking
    try:
        if dry_run_builder_hooks():
            print_info("Builder hooks installed")
    except Exception as e:
        print_err(f"Builder hooks failed: {e}")

    # Hook 4: Add exit handler to finalize dry run
    import atexit

    atexit.register(
        lambda: dry_run_logger.finalize() if dry_run_logger else None
    )

    print_info("All hooks installed successfully")
    return True


def check_and_enable_dry_run() -> bool:
    """
    Check if dry-run is enabled and install hooks if needed.
    """
    if is_dry_run_enabled():
        print("=" * 80)
        print_info("DRY RUN MODE ENABLED")
        print_info("Commands will be logged but not executed")
        print("=" * 80)

        install_dry_run_hooks()

        return True
    else:
        return False


# Initialize colorama
init(autoreset=True, strip=False, convert=False)

# Execute dry-run check
if check_and_enable_dry_run():
    print_info("Ready to capture build commands")
else:
    print_info("Not enabled (set PIO_DRY_RUN=1)")
'''
)

FILTER_HOOK_SCRIPT = (
    """#!/usr/bin/env python3\n"""
    + f'''# SCRIPT_VERSION = "{SCRIPT_VERSION}"'''
    + '''
# Copyright © 2018-2025 Johan Cockx, Matic Kukovec & Kristof Mulier

"""
PlatformIO PRE Script: PlatformIO Source File Filter Hook
Filters framework and user source files and include directories (aka 'hdirs') at
the SCons level.

FILTERING MECHANISMS:
1. Source File Filtering:
       Intercepts `env.BuildSources()` and `env.CollectBuildFiles()` - replacing
       them with `filter_build_sources(..)` and `filter_collect_build_files(..)`
       respectively - to filter out unwanted source files before compilation.
       Unwanted source files are extracted from `framework_exclude_sources` in
       the `platformio.ini` file (there can also be unwanted source files in
       `build_src_filter`, but they are handled automatically by PlatformIO
       itself, so we can ignore them).

2. Include Directory Filtering:
       aka:
         - hdir filtering
         - CPPPATH filtering (filtering the -I flags on the CPPPATH)

       Uses SPAWN interception to filter -I flags from compilation commands in
       real-time, removing include directories that match patterns in
       `framework_exclude_hdirs` while preserving directories added via
       `build_flags`.

CONFIGURATION:
Configure filtering in platformio.ini using these variables:
- framework_exclude_sources: Patterns for framework source files to exclude
- framework_exclude_hdirs: Patterns for framework include directories to exclude
- build_src_filter: Standard PlatformIO user source file filtering
- build_flags: Additional include directories to add (e.g., -Isrc/dir1)

This implementation uses SCons method interception for source files and SPAWN
interception for include directories, ensuring compatibility with SCons internal
mechanisms while providing comprehensive filtering capabilities.
"""

import os
import sys
import fnmatch
from os.path import basename
from typing import Any, Optional, List, Union, Tuple, Callable
from colorama import init, Fore

# Import the SCons environment
Import("env")


def print_info(msg: str = "") -> None:
    if msg:
        print(f"{Fore.LIGHTGREEN_EX}[FILT HOOK]{Fore.RESET} {msg}")
    return


def print_warn(msg: str = "") -> None:
    if msg:
        print(f"{Fore.LIGHTRED_EX}[FILT HOOK]{Fore.RESET} {msg}")
    return


def print_err(msg: str = "") -> None:
    if msg:
        print(f"{Fore.RED}[FILT HOOK]{Fore.RESET} {msg}", file=sys.stderr)
    return


# Cache for verbose flag to avoid redundant detection
_verbose_flag_cache: Optional[bool] = None

# Cache for configuration data to avoid redundant platformio.ini parsing
_cfg_cache: Optional[Tuple[List[str], List[str], bool]] = None


def get_verbose_flag() -> bool:
    """
    Extract verbose flag from multiple sources with improved detection.
    Cached to avoid redundant calls during the same build process
    """
    # $ Return cache if present
    global _verbose_flag_cache
    if _verbose_flag_cache is not None:
        return _verbose_flag_cache

    verbose: bool = False
    debug_info: List[str] = []

    try:
        # $ Method 1: Check environment variables that PlatformIO might set
        platformio_verbose = os.environ.get("PLATFORMIO_VERBOSE", "").lower()
        pio_verbose = os.environ.get("PIO_VERBOSE", "").lower()
        verbose_env = os.environ.get("VERBOSE", "").lower()

        env_verbose_detected = (
            platformio_verbose in ("1", "true", "yes")
            or pio_verbose in ("1", "true", "yes")
            or verbose_env in ("1", "true", "yes")
        )

        if env_verbose_detected:
            debug_info.append(
                f"ENV: PLATFORMIO_VERBOSE={platformio_verbose}, "
                f"PIO_VERBOSE={pio_verbose}, VERBOSE={verbose_env}"
            )

        # $ Method 2: Check sys.argv for verbose flags (FIXED)
        sys_argv_str = " ".join(sys.argv) if sys.argv else ""
        has_verbose_flag = (
            "--verbose" in sys_argv_str
            or " -v "
            in sys_argv_str  # Space before and after to avoid false positives
            or sys_argv_str.startswith("-v ")  # -v at start
            or sys_argv_str.endswith(" -v")  # -v at end
            or "PIOVERBOSE=1"
            in sys_argv_str  # PlatformIO sets this when --verbose is used
        )

        if sys_argv_str:
            debug_info.append(
                f"ARGV: '{sys_argv_str}' -> has_verbose_flag={has_verbose_flag}"
            )

        # $ Method 3: Check SCons environment for verbose settings
        scons_env_verbose = False
        if hasattr(env, "get"):
            scons_env_verbose = bool(env.get("VERBOSE", False)) or bool(
                env.get("verbose", False)
            )
            if scons_env_verbose:
                debug_info.append(
                    f"SCONS_ENV: VERBOSE={env.get('VERBOSE', False)}, verbose={env.get('verbose', False)}"
                )

        # $ Method 4: Check SCons command line options
        scons_verbose = False
        try:
            import SCons.Script

            if hasattr(SCons.Script, "GetOption"):
                # Check for SCons debug/verbose options
                try:
                    debug_explain = SCons.Script.GetOption("debug")
                    if debug_explain:
                        scons_verbose = True
                        debug_info.append(
                            f"SCONS_OPTIONS: debug={debug_explain}"
                        )
                except:
                    pass
        except:
            pass

        # & Combine all detection methods with priority
        verbose = (
            env_verbose_detected  # Highest priority: explicit env vars
            or has_verbose_flag  # Second: command line flags
            or scons_env_verbose  # Third: SCons environment
            or scons_verbose  # Lowest: SCons debug options
        )

        # $ Debug output when verbose detection methods are tested
        if debug_info:
            pass
            # print_info(f"DEBUG: {' | '.join(debug_info)}")

    except Exception as e:
        verbose = False
        print_info(f"DEBUG: Exception in verbose detection: {e}")

    # Cache the result for subsequent calls
    _verbose_flag_cache = verbose
    print_info(f"Detected verbose flag = {verbose} (cached)")
    return verbose


def get_exclude_patterns_from_cfg() -> Tuple[List[str], List[str], bool]:
    """
    Extract excluded file and hdir patterns from `platformio.ini`. Use caching
    to avoid redundant parsing during same build process.

    Returns:
        tuple: (
            excl_file_patterns,
            excl_hdir_patterns,
            verbose,
        )
    """
    # $ Return cache if present
    global _cfg_cache
    if _cfg_cache is not None:
        return _cfg_cache

    try:
        # $ Get config values
        excl_file_patterns_raw = env.GetProjectOption(
            "framework_exclude_sources",
            "",
        )
        excl_hdir_patterns_raw = env.GetProjectOption(
            "framework_exclude_hdirs",
            "",
        )
        verbose = get_verbose_flag()

        # $ Parse excluded source file patterns
        excl_file_patterns: List[str] = []
        if excl_file_patterns_raw:
            if isinstance(excl_file_patterns_raw, list):
                excl_file_patterns = [
                    normalize(item.strip())
                    for item in excl_file_patterns_raw
                    if item.strip()
                ]
            else:
                excl_file_patterns = [
                    normalize(item.strip())
                    for item in str(excl_file_patterns_raw).split("\\n")
                    if item.strip()
                ]

        # $ Parse excluded hdir patterns
        excl_hdir_patterns: List[str] = []
        if excl_hdir_patterns_raw:
            if isinstance(excl_hdir_patterns_raw, list):
                excl_hdir_patterns = [
                    normalize(item.strip())
                    for item in excl_hdir_patterns_raw
                    if item.strip()
                ]
            else:
                excl_hdir_patterns = [
                    normalize(item.strip())
                    for item in str(excl_hdir_patterns_raw).split("\\n")
                    if item.strip()
                ]

        # Cache the result for subsequent calls
        _cfg_cache = (
            excl_file_patterns,
            excl_hdir_patterns,
            verbose,
        )
        if not verbose:
            print_info(
                f"Configuration cached: "
                f"{Fore.YELLOW}{len(excl_file_patterns)}{Fore.RESET} file "
                f"patterns, "
                f"{Fore.YELLOW}{len(excl_hdir_patterns)}{Fore.RESET} hdir "
                f"patterns"
            )
        else:
            print_info(f"Configuration cached")
            msg = "\\n    ".join(
                [f"{Fore.YELLOW}{p}{Fore.RESET}" for p in excl_file_patterns]
            )
            print_info(
                f"{Fore.YELLOW}{len(excl_file_patterns)}{Fore.RESET} file "
                f"patterns:\\n"
                f"    {msg}"
            )
            msg = "\\n    ".join(
                [f"{Fore.YELLOW}{p}{Fore.RESET}" for p in excl_hdir_patterns]
            )
            print_info(
                f"{Fore.YELLOW}{len(excl_hdir_patterns)}{Fore.RESET} hdir "
                f"patterns:\\n"
                f"    {msg}"
            )
        return _cfg_cache

    except Exception as e:
        print_err(f"Error reading config: {e}")
        # Cache the error result to avoid repeated failures
        _cfg_cache = ([], [], False)
        return _cfg_cache


def normalize(file_path: str) -> str:
    """
    Unixify given path or pattern
    """
    return file_path.replace("\\\\", "/").strip()


def should_exclude_file(file_path: str) -> bool:
    """
    Filter function for source files.

    Args:
        file_path: Absolute path to the source file

    Returns:
        bool: True if file should be excluded from compilation
    """
    # Get configuration from platformio.ini
    excl_file_patterns, _, verbose = get_exclude_patterns_from_cfg()
    if not excl_file_patterns:
        return False

    # file_path should already be normalized, but play it safe
    file_path = normalize(file_path)

    # & Check pattern exclusions
    for p in excl_file_patterns:
        # pattern should already be normalized, but play it safe
        p = normalize(p)
        if fnmatch.fnmatch(file_path, p):
            if verbose:
                print_info(
                    f"EXCLUDING "
                    f"{Fore.YELLOW}{basename(file_path)}{Fore.RESET}\\n"
                    f"    matches pattern: {p}"
                )
            else:
                print_info(
                    f"EXCLUDING "
                    f"{Fore.YELLOW}{basename(file_path)}{Fore.RESET}"
                )
            return True
        continue

    # $ No match -> keep file
    return False


def should_exclude_hdir(hdir_path: str) -> bool:
    """
    Filter function for hdirs.

    Args:
        hdir_path: Path to the hdir (include directory)

    Returns:
        bool: True if hdir should be excluded from CPPPATH.
    """
    # Get configuration from platformio.ini
    _, excl_hdir_patterns, verbose = get_exclude_patterns_from_cfg()
    if not excl_hdir_patterns:
        return False

    # hdir_path should already be normalized, but play it safe
    hdir_path = normalize(hdir_path)

    # & Check pattern exclusions
    for p in excl_hdir_patterns:
        # pattern should already be normalized, but play it safe
        p = normalize(p)
        if fnmatch.fnmatch(hdir_path, p):
            # Always show exclusion for hdirs to debug the issue
            print_info(
                f"EXCLUDING "
                f"{Fore.YELLOW}{basename(hdir_path)}{Fore.RESET}"
            )
            return True
        continue

    # $ No match -> keep hdir
    return False


# def filter_hdirs() -> None:
#     """
#     Filter CPPPATH to remove excluded hdirs.
#     """
#     # & Check if filtering is needed at all
#     # If there are no `excl_hdir_patterns` given in the `platformio.ini` file,
#     # then no filtering is needed and this function can quit without updating
#     # CPPPATH.
#     _, excl_hdir_patterns, verbose = get_exclude_patterns_from_cfg()
#     if not excl_hdir_patterns:
#         # No filtering needed (because no filter set)
#         return
#
#     # & Get CPPPATH
#     original_cpppath = env.get("CPPPATH", [])
#     if not original_cpppath:
#         # No filtering needed (because CPPPATH is empty)
#         return
#
#     # & Filter CPPPATH to `filtered_cpppath`
#     filtered_cpppath = []
#     excl_cntr = 0
#     for hdir in original_cpppath:
#         # Resolve variables like $PROJECT_DIR
#         hdir_str = normalize(env.subst(str(hdir)))
#         if not should_exclude_hdir(hdir_str):
#             filtered_cpppath.append(hdir)
#         else:
#             excl_cntr += 1
#         continue
#
#     # & Update CPPPATH with `filtered_cpppath`
#     if excl_cntr > 0:
#         env.Replace(CPPPATH=filtered_cpppath)
#         if verbose:
#             print_info(
#                 f"Filtered CPPPATH: excluded "
#                 f"{Fore.YELLOW}{excl_cntr}{Fore.RESET} hdirs, kept "
#                 f"{Fore.YELLOW}{len(filtered_cpppath)}{Fore.RESET}"
#             )
#         else:
#             print_info(f"Filtered {Fore.YELLOW}{excl_cntr}{Fore.RESET} hdirs")
#     elif verbose:
#         print_info(f"No hdirs matched exclusion rules")
#     return


def filter_build_sources(
    original_func: Callable[
        [Union[str, Any], Union[str, Any], Optional[Any]], List[Any]
    ],
) -> Callable[[Union[str, Any], Union[str, Any], Optional[Any]], List[Any]]:
    """
    Wrapper function that intercepts `env.BuildSources()` calls and filters out
    unwanted files before they get processed.
    """

    def filtered_build_sources(
        target_dir: Union[str, Any],
        source_dir: Union[str, Any],
        src_filter: Optional[Any] = None,
    ) -> List[Any]:
        print_info(
            f"Intercepting "
            f"BuildSources({target_dir}, {source_dir}, {src_filter})"
        )

        # Call original function to get the source nodes
        result = original_func(target_dir, source_dir, src_filter)

        # & NO SOURCE FILES FOUND
        if not result:  # If no source files found
            # Return empty list
            return result

        # & SOURCE FILES FOUND
        # Filter the results based on Filter Hook decisions
        assert result
        filtered_result = []
        for node in result:
            file_path = str(node)
            if not should_exclude_file(file_path):
                filtered_result.append(node)
            else:
                print_info(
                    f"Filtered out "
                    f"{Fore.YELLOW}{basename(file_path)}{Fore.RESET} "
                    f"[{Fore.CYAN}env.BuildSources stage{Fore.RESET}]"
                )
            continue
        print_info(
            f"Kept {Fore.YELLOW}{len(filtered_result)}{Fore.RESET}/"
            f"{Fore.YELLOW}{len(result)}{Fore.RESET} files from "
            f"{Fore.YELLOW}{basename(source_dir)}{Fore.RESET}"
        )
        return filtered_result

    # --- END INNER FUNC ---#

    return filtered_build_sources


def filter_collect_build_files(
    original_func: Callable[[Union[str, Any], Union[str, Any], Any], List[Any]],
) -> Callable[[Union[str, Any], Union[str, Any], Any], List[Any]]:
    """
    Wrapper function that intercepts `env.CollectBuildFiles()` calls and filters
    out unwanted files at the collection stage.

    CRITICAL FIX: This function ensures that SCons VariantDir is properly set up
    even when no source files are found in a directory (e.g., Arduino variant
    directories that contain only header files). This prevents include path
    resolution issues that occur when VariantDir is not established.

    Root Cause Analysis:
    - CollectBuildFiles normally calls env.VariantDir() only when source files
      are found
    - Arduino variant directories (e.g., variants/lolin_s2_mini) contain only
      headers
    - When intercepted and no sources found, VariantDir is never set up
    - Include paths in CPPPATH become unresolvable, causing "file not found"
      errors
    - Solution: Force VariantDir setup for directories even when no sources
      exist
    """

    def filtered_collect_build_files(
        variant_dir: Union[str, Any],
        source_dir: Union[str, Any],
        src_filter: Any,
    ) -> List[Any]:
        print_info(
            f"Intercepting "
            f"CollectBuildFiles({variant_dir}, {source_dir}, {src_filter})"
        )

        # Call original function to get the file nodes AND ensure VariantDir is
        # set up
        result = original_func(variant_dir, source_dir, src_filter)

        # & NO SOURCE FILES FOUND
        if not result:  # If no source files found
            # CRITICAL: For directories that contain only headers (like Arduino
            # variants), we need to ensure VariantDir is set up. This is
            # essential for include path resolution in CPPPATH.
            src_dir = env.subst(str(source_dir))
            var_dir = env.subst(str(variant_dir))
            if src_dir and var_dir:
                try:
                    # Set up the variant directory mapping for SCons
                    # This is normally done inside CollectBuildFiles when
                    # sources exist
                    env.VariantDir(var_dir, src_dir, duplicate=False)
                    print_info(
                        f"Set up VariantDir mapping: "
                        f"{Fore.CYAN}{basename(var_dir)}{Fore.RESET} -> "
                        f"{Fore.CYAN}{basename(src_dir)}{Fore.RESET} "
                        f"(no sources, headers only)"
                    )
                except Exception as e:
                    # VariantDir might already be set up, which is fine
                    pass
            # Return empty list but VariantDir is now properly set up
            return result

        # & SOURCE FILES FOUND
        # Now apply filtering only to actual source files
        assert result
        filtered_result = []
        for node in result:
            file_path = normalize(str(node.srcnode()))
            if not should_exclude_file(file_path):
                filtered_result.append(node)
            else:
                print_info(
                    f"Filtered out "
                    f"{Fore.YELLOW}{basename(file_path)}{Fore.RESET} "
                    f"[{Fore.CYAN}env.CollectBuildFiles stage{Fore.RESET}]"
                )
            continue
        print_info(
            f"Kept {Fore.YELLOW}{len(filtered_result)}{Fore.RESET}/"
            f"{Fore.YELLOW}{len(result)}{Fore.RESET} files from "
            f"{Fore.YELLOW}{basename(source_dir)}{Fore.RESET}"
        )
        return filtered_result

    # --- END INNER FUNC ---#

    return filtered_collect_build_files


def hook_into_build_process() -> None:
    """
    Hook into the build process at multiple levels to ensure files are filtered.
    Uses a multi-layer approach for maximum compatibility.
    """
    print_info("Hooking into build process")

    # % 1. SOURCE FILE FILTERING
    print_info("Installing source file filters")

    # & 1.1 Intercept `env.BuildSources` (high-level)
    if hasattr(env, "BuildSources"):
        original_build_sources = env.BuildSources
        env.BuildSources = filter_build_sources(original_build_sources)
        print_info("Installed env.BuildSources filter")

    # & 1.2 Intercept `env.CollectBuildFiles` (low-level)
    if hasattr(env, "CollectBuildFiles"):
        original_collect_build_files = env.CollectBuildFiles
        env.CollectBuildFiles = filter_collect_build_files(
            original_collect_build_files
        )
        print_info("Installed env.CollectBuildFiles filter")

    # % 2. INCLUDE DIRECTORY FILTERING (CPPPATH FILTERING)
    # Use SPAWN interception for real-time CPPPATH filtering. This approach
    # intercepts compilation commands right before execution and filters -I
    # flags, avoiding timing issues with CPPPATH manipulation.
    print_info("[DEBUG] Setting up SPAWN interception for CPPPATH filtering...")
    original_spawn = env.get("SPAWN")

    def filter_spawn_cpppath(sh, escape, cmd, args, env_vars):
        """
        Intercept compilation commands and filter -I flags in real-time.
        This runs at the perfect time: right before command execution.
        Enhanced to handle response files used by ESP32 and other platforms.
        """
        try:
            # Check if this is a compilation command that we should filter
            if isinstance(args, (list, tuple)) and len(args) > 0:
                cmd_str = " ".join(str(arg) for arg in args)
                
                # Debug: Log all compilation commands to understand the format
                if any(compiler in cmd_str for compiler in ["gcc", "g++", "clang", "clang++"]):
                    print_info(f"[SPAWN-FILTER DEBUG] Args length: {len(args)}")
                    if len(args) <= 5:  # Only log short args lists to avoid clutter
                        print_info(f"[SPAWN-FILTER DEBUG] Args: {args}")
                
                # Check if this is a response file command (e.g., @tempfile.tmp)
                # Note: args might contain the compiler path and @file as separate elements
                response_file_arg = None
                for arg in args:
                    if isinstance(arg, str) and arg.startswith("@"):
                        response_file_arg = arg
                        break
                
                if response_file_arg:
                    # This is a response file - need to read and filter its contents
                    response_file = response_file_arg[1:]  # Remove @ prefix
                    print_info(f"[SPAWN-FILTER] Detected response file: {response_file}")
                    
                    try:
                        # Read the response file
                        with open(response_file, 'r', encoding='utf-8') as f:
                            response_content = f.read()
                        
                        # Parse the response file content into args
                        # Response files typically have one argument per line or space-separated
                        import shlex
                        response_args = shlex.split(response_content)
                        
                        print_info(f"[SPAWN-FILTER] Response file has {len(response_args)} arguments")
                        
                        # Check if this is a compilation command
                        # The response file contains all the compiler arguments, not the compiler itself
                        if "-c" in response_args:
                            print_info(f"[SPAWN-FILTER] Processing response file compilation command")
                            
                            # Get exclusion patterns
                            _, excl_hdir_patterns, verbose = get_exclude_patterns_from_cfg()
                            
                            if excl_hdir_patterns:
                                # Filter the arguments
                                filtered_args = []
                                skip_next = False
                                filtered_count = 0
                                
                                for i, arg in enumerate(response_args):
                                    if skip_next:
                                        skip_next = False
                                        filtered_count += 1
                                        continue
                                    
                                    # Check for -I flags
                                    if arg == "-I" and i + 1 < len(response_args):
                                        next_arg = response_args[i + 1]
                                        hdir_path = normalize(str(next_arg))
                                        if should_exclude_hdir(hdir_path):
                                            skip_next = True
                                            filtered_count += 1
                                            continue
                                        else:
                                            filtered_args.append(arg)
                                    elif isinstance(arg, str) and arg.startswith("-I"):
                                        hdir_path = normalize(arg[2:])
                                        if should_exclude_hdir(hdir_path):
                                            filtered_count += 1
                                            continue
                                        else:
                                            filtered_args.append(arg)
                                    else:
                                        filtered_args.append(arg)
                                
                                if filtered_count > 0:
                                    print_info(f"[SPAWN-FILTER] Filtered {filtered_count} -I flags from response file")
                                    if verbose:
                                        print_info(f"[NOTE] The verbose output above shows unfiltered include paths. Actual compilation uses filtered paths.")
                                    
                                    # Write the filtered content back to a new response file
                                    import tempfile
                                    fd, temp_response_file = tempfile.mkstemp(suffix='.tmp', text=True)
                                    try:
                                        with os.fdopen(fd, 'w', encoding='utf-8') as f:
                                            # Write filtered args back to temp file
                                            f.write(' '.join(shlex.quote(arg) for arg in filtered_args))
                                        
                                        # Update args to use the new response file
                                        args.clear()
                                        args.append("@" + temp_response_file)
                                        print_info(f"[SPAWN-FILTER] Created filtered response file: {temp_response_file}")
                                    except Exception as e:
                                        print_info(f"[SPAWN-FILTER] Error writing filtered response file: {e}")
                                        os.close(fd)
                    
                    except Exception as e:
                        print_info(f"[SPAWN-FILTER] Error processing response file: {e}")
                
                # Handle regular (non-response-file) commands
                elif any(compiler in cmd_str for compiler in ["gcc", "g++", "clang", "clang++"]) and "-c" in args:
                    # Get exclusion patterns
                    _, excl_hdir_patterns, verbose = get_exclude_patterns_from_cfg()

                    if excl_hdir_patterns:
                        # Filter -I flags from the arguments
                        filtered_args = []
                        skip_next = False
                        filtered_count = 0

                        for i, arg in enumerate(args):
                            if skip_next:
                                # Skip this argument (it was the path after -I)
                                skip_next = False
                                filtered_count += 1
                                if verbose:
                                    print_info(
                                        f"[SPAWN-FILTER] Excluded -I flag: "
                                        f"{arg}"
                                    )
                                continue

                            # Check for -I flags
                            if arg == "-I" and i + 1 < len(args):
                                # -I as separate argument: -I /path/to/include
                                next_arg = args[i + 1]
                                hdir_path = normalize(str(next_arg))
                                if should_exclude_hdir(hdir_path):
                                    skip_next = (
                                        True  # Skip both -I and the path
                                    )
                                    filtered_count += 1
                                    if verbose:
                                        print_info(
                                            f"[SPAWN-FILTER] Excluded -I flag: "
                                            f"{next_arg}"
                                        )
                                    continue
                                else:
                                    filtered_args.append(arg)
                            elif isinstance(arg, str) and arg.startswith("-I"):
                                # -I combined with path: -I/path/to/include
                                hdir_path = normalize(
                                    arg[2:]
                                )  # Remove -I prefix
                                if should_exclude_hdir(hdir_path):
                                    filtered_count += 1
                                    if verbose:
                                        print_info(
                                            f"[SPAWN-FILTER] Excluded -I flag: "
                                            f"{arg}"
                                        )
                                    continue
                                else:
                                    filtered_args.append(arg)
                            else:
                                filtered_args.append(arg)

                        if filtered_count > 0:
                            print_info(
                                f"[SPAWN-FILTER] Filtered {filtered_count} "
                                f"-I flags from compilation command"
                            )
                            if verbose:
                                print_info(f"[NOTE] The verbose output above shows unfiltered include paths. Actual compilation uses filtered paths.")

                            # CRITICAL: Modify args in-place to ensure SCons
                            # gets the filtered arguments
                            args.clear()
                            args.extend(filtered_args)

        except Exception as e:
            print_info(f"[SPAWN-FILTER] Error in CPPPATH filtering: {e}")

        # Call original spawn with potentially modified arguments
        return original_spawn(sh, escape, cmd, args, env_vars)

    # Replace spawn function with our filtering version
    env["SPAWN"] = filter_spawn_cpppath
    print_info("[DEBUG] SPAWN interception installed for CPPPATH filtering")

    # % 3. POST FILTERING
    # Also call post_framework_filter for completeness (file filtering)
    def post_framework_filter():
        """
        Also install a post-framework hook to catch any files that slip through
        """
        print_info("[POST-FRAMEWORK] Function called!")
        # Filter the main build files list if it exists
        if "PIOBUILDFILES" in env:
            print_info("[POST-FRAMEWORK] PIOBUILDFILES found, filtering...")
            original_files = env.get("PIOBUILDFILES", [])
            filtered_files = []
            for file_node in original_files:
                file_path = str(file_node)
                if not should_exclude_file(file_path):
                    filtered_files.append(file_node)
                else:
                    print_info(
                        f"Filtered out "
                        f"{Fore.YELLOW}{basename(file_path)}{Fore.RESET} "
                        f"[{Fore.CYAN}post-framework hook{Fore.RESET}]"
                    )
                continue
            if len(filtered_files) != len(original_files):
                env.Replace(PIOBUILDFILES=filtered_files)
                print_info(
                    f"Final filter - kept "
                    f"{Fore.YELLOW}{len(filtered_files)}{Fore.RESET}/"
                    f"{Fore.YELLOW}{len(original_files)}{Fore.RESET} files"
                )
        else:
            print_info("[POST-FRAMEWORK] PIOBUILDFILES not found")
        return

    try:
        post_framework_filter()
        print_info("[DEBUG] Post-framework filtering completed")
    except Exception as e:
        print_info(f"[DEBUG] Post-framework filtering error: {e}")

    print_info("[DEBUG] CPPPATH filtering setup complete")
    return


# Print intro
init(autoreset=True, strip=False, convert=False)
print_info("Framework file filtering active")
_excl_file_patterns, _excl_hdir_patterns, _verbose = (
    get_exclude_patterns_from_cfg()
)
if _excl_file_patterns or _excl_hdir_patterns:
    pass
else:
    print_info("No exclusion rules configured")

# Install filter
hook_into_build_process()
print_info("Ready to filter framework source files")
'''
)

if __name__ == "__main__":
    # Initialize colorama
    init(autoreset=True, strip=False, convert=False)
    # Launch
    main()
