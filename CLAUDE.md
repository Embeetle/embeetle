# EMBEETLE CODE ASSISTANT GUIDELINES
You are "Claude Code" or in short "Claude". I am the user.

## Environment Notes
This computer possibly has three environments:

  1. Your environment:
  You run in Git for Windows' bundled MSYS2 environment (aka "Git Bash"),
  probably located at `C:\Program Files\Git\`.

  2. My MSYS2 environment:
  The user (me) might have a separate standalone MSYS2, probably located at
  `C:\msys64\`.

  3. Embeetle IDE runs in a native Windows CMD, so it runs in the native Windows
  environment.

What you need to know about these environments:

- These environments have different Python versions and packages.
- For that reason, always ask the user to run tests when Python is involved.
- Don't rely on tools like `pip show` or Python version checks.
- Windows-style paths (e.g., `C:\msys64\...`) work with your tools (Read, Write, etc.). But always normalize to forward slashes when you have the chance (e.g., `C:/msys64/...`). Windows can usually deal with forward slashes now.
- In Bash commands, paths use Unix-style format (e.g., `/c/msys64/...`).

A special note about Git commands:
- Read-only commands are allowed (e.g., `git status`, `git log`, `git diff`).
- Commands that modify local or upstream state are NOT allowed (e.g., `git commit`, `git push`, `git pull`, `git checkout`, `git reset`). Ask the user to run these.

## Code Style Guidelines
- Code formatting: Use Black with 80 character line width.
- Line endings: Use Linux-style line endings `\n`.
- File encoding: Use UTF-8 , but no need to put `# -*- coding: utf-8 -*-` header.
- Imports: Standard library first, then project modules.
- Classes: PascalCase (e.g., `GlobalSignalDispatcher`).
- Functions/Variables: snake_case (e.g., `get_user_profile`).
- Constants: ALL_CAPS (e.g., `LINUX_LINE_ENDING`).
- Docstrings: Use triple double quotes `"""` with parameter descriptions, formatted with docformatter.
- Type hints: Required for parameters and return values.
- Error handling: Use try/except with proper traceback reporting.
- Path handling: Always normalize to forward slashes.
- Sections: Use comment markers (`#^`, `#&`, `#$`) for logical grouping.
- PyQt signals: Use descriptive names with clear connection patterns.
- Functions: end every function implementation with a return statement, even if there is nothing to return.
- Add the following copyright notice at the top of each `.py` file:
```
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
```

## Repository Organization

The `embeetle` repository consists of the following toplevel folders:

- `beetle_splash`
- `licenses`
- `pio_scripts`
- `sys`
- `beetle_core`

Let's consider them one-by-one

### Folder `beetle_splash`
Introductory splash windows to start the application.

### Folder `licenses`
License texts for all third party modules we use in the application.

### Folder `pio_scripts`
Scripts to deal with PlatformIO projects in Embeetle IDE. Work in progress.

### Folder `sys`
Third party binaries needed by the application to run, as well as the Source Analyzer (aka "SA") binary and supportive python scripts to interact with the binary.
If you analyze the `sys` folder, I suggest you skip the binaries and just focus on the python scripts in `sys/esa` ("esa" stands for "Embeetle Source Analyzer", we use that abbreviation as well as just "sa" or "Source Analyzer").

### Folder `beetle_core`

#### Application Structure
- `beetle_core/embeetle.py`: Main entry point that initializes the application and handles startup
- `beetle_core/data.py`: Global data and state management
- `beetle_core/qt.py`: Qt libraries and integration
- `beetle_core/purefunctions.py`: Pure utility functions that don't depend on application state
- `beetle_core/functions.py`: General utility functions that may depend on application state
- `beetle_core/constants.py`: Application-wide constants

#### User Interface Components
- `beetle_core/gui/`: Primary UI framework
  - `forms/`: Major UI components and windows
    - `mainwindow.py`: Main project window
    - `homewindow.py`: Home window shown when no project is loaded
    - `customeditor.py`: Code editor component
    - `newfiletree.py`: File tree browser component
    - `tabwidget.py`: Tab management for editor
    - `settingswindow.py`: Settings/preferences window
  - `helpers/`: UI utility classes and widgets
  - `templates/`: Base classes for UI components
  - `dialogs/`: Dialog windows
  - `stylesheets/`: CSS-like styling for UI components
  - `styles/`: Custom styles for Qt widgets
  - `fonts/`: Font loading and management

#### Dashboard
- `beetle_core/dashboard/`: Project configuration control center
  - `chassis/`: Main dashboard structure
  - `items/`: Dashboard items (chip, board, probe, etc.)
  - `contextmenus/`: Right-click menus for dashboard items

#### Filetree
- `beetle_core/gui/forms/newfiletree.py`: File tree browser implementation
- `beetle_core/components/newfiletreehandler.py`: Backend logic for file tree

#### Editor
- `beetle_core/gui/forms/customeditor.py`: Code editor implementation
- `beetle_core/lexers/`: Syntax highlighting for different languages
  - Support for C, C++, Python, Assembly, and other languages

#### Console
- `beetle_core/beetle_console/`: Terminal and serial console implementation
  - `console_widget.py`: Main console widget
  - `serial_console.py`: Serial port communication
  - `make_console.py`: Console for build output
  - `mini_console.py`: Lightweight console implementation

#### Debugger
- `beetle_core/debugger/`: Debugging tools and interfaces
  - `debugger.py`: Main debugger interface
  - `debuggerwindow.py`: Debugger UI
  - `openocdworker.py`: OpenOCD integration
  - `breakpointwidget.py`: Breakpoint management
  - `memoryviews.py`: Memory inspection
  - `stackframewidget.py`: Stack frame examination

#### Library Manager
- `beetle_core/libmanager/`: Library management system
  - `libmanager.py`: Main library management class
  - `libobj.py`: Library objects
  - `libfilter.py`: Library filtering functionality
- `beetle_core/home_libraries/`: Library UI in home window
  - `chassis/`: Main structure
  - `items/`: Library item representations

#### Source Analyzer
- `beetle_core/components/sourceanalyzerinterface.py`: Interface to the Source Analyzer engine
- `beetle_core/components/source_analyzer.pyi`: Type definitions for Source Analyzer
- `beetle_core/sa_tab/`: Source Analyzer UI tab implementation
  - `chassis/sa_tab.py`: Main Source Analyzer tab

#### Hardware API
- `beetle_core/hardware_api/`: Hardware component abstraction layer
  - `hardware_api.py`: Main API interface
  - `chip_unicum.py`: Microcontroller chip representation
  - `board_unicum.py`: Development board representation
  - `probe_unicum.py`: Debug probe representation
  - `treepath_unicum.py`: File path representation

#### Project Management
- `beetle_core/project/`: Project handling and configuration
  - `project.py`: Project representation and management
  - `segments/`: Project components (board, chip, path segments, etc.)
  - `startup/`: Project loading and creation
  - `elf_reader.py`: ELF file parsing
  - `readelf.py`: Wrapper for the readelf tool

#### Tools Management
- `beetle_core/toolmanager/`: Development tools management
  - `toolmanager.py`: Tool management system
  - `version_extractor.py`: Tool version detection
- `beetle_core/home_toolbox/`: Toolbox UI in home window

#### Chip Configuration
- `beetle_core/chipconfigurator/`: Microcontroller configuration system
  - `chipconfigurator.py`: Chip configuration interface
  - `basebuilder.py`: Base builder for chip configurations
  - `widgets.py`: UI widgets for chip configuration

#### MCU Configuration
- `beetle_core/mcuconfig/`: Low-level MCU configuration
  - `config.py`: Configuration handling
  - `svd2json.py`: SVD to JSON conversion
  - `load_svd.py`: SVD file loader
  - `clock_layout.py`: Clock tree configuration

#### Path Handling
- `beetle_core/bpathlib/`: Enhanced path handling
  - `path_obj.py`: Path object implementation
  - `path_power.py`: Path utilities
  - `file_power.py`: File operations
  - `treepath_obj.py`: Tree path representation

#### Project Generation
- `beetle_core/generators_and_importers/`: Project generation tools
  - Vendor-specific generators (STM, NXP, Arduino, etc.)
  - Project import utilities
- `beetle_core/project_generator/`: Core project generation functionality
  - `generator/project_generator.py`: Main project generator

#### Wizards
- `beetle_core/wizards/`: Step-by-step setup assistants
  - `intro_wizard/`: First-time setup wizard
  - `lib_wizard/`: Library setup wizard
  - `tool_wizard/`: Tool configuration wizard
  - `serial_wizard/`: Serial port configuration wizard
  - `upgrade_proj_wizard/`: Project upgrade wizard

#### Parse and Analysis
- `beetle_core/parsing/`: Code parsing utilities
  - `ctagsparser.py`: CTags integration
  - `fileparser.py`: File parsing functionality
  - `parsedatabase.py`: Parsed code database

#### Settings
- `beetle_core/settings/`: Application settings
  - `settings.py`: Settings management
  - `constants.py`: Settings constants
  - `newsmanipulator.py`: News feed handling

#### Components
- `beetle_core/components/`: Shared utility components
  - `signaldispatcher.py`: Signal/event system
  - `singleton.py`: Singleton pattern implementation
  - `diagnostics.py`: Diagnostic tools
  - `symbolhandler.py`: Symbol management
  - `thesquid.py`: The Squid component (help system)
  - `thread_switcher.py`: Thread management

#### Resources
- `beetle_core/resources/`: Static resources
  - `icons_plump_color/`: UI icons
  - `figures_plump_color/`: UI graphics
  - `themes/`: UI themes
  - `fonts/`: Font files
  - `hardware/`: Hardware definitions
    - Manufacturer, board, chip, and probe definitions

#### Contextual Menus
- `beetle_core/contextmenu/`: Right-click menu system
  - `contextmenu.py`: Base context menu
  - `contextmenu_launcher.py`: Context menu activation
  - `path_contextmenu.py`: Path-specific context menus

#### Themes
- `beetle_core/themes/`: Theming system
  - Theme definitions and management

#### Help Documentation
- `beetle_core/helpdocs/`: Help documentation system
  - `help_subjects/`: Help content by topic
  - `help_texts.py`: Help text management

#### Utilities
- `beetle_core/components/`: Shared components and utilities
  - `fifo_queue.py`: FIFO queue implementation
  - `filechecker.py`: File validation
  - `history.py`: Command history
  - `hotspots.py`: UI hotspots
  - `reader.py`: File reading utilities
  - `iconmanipulator.py`: Icon management
  - `communicator.py`: Inter-component communication
  - `decorators.py`: Python decorators

#### Terminal Handling
- `beetle_core/ptyprocess/`: Pseudo-terminal handling
  - Process execution in a pseudo-terminal

#### GDB Integration
- `beetle_core/pygdbmi/`: GDB machine interface
  - `gdbcontroller.py`: GDB control interface
  - `gdbmiparser.py`: GDB machine interface parser