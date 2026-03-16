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

"""Dashboard data module.

This module defines the format for the Dashboard data, using dataclasses.

DATA MODEL:
    Strict model-view separation is ensured. The following global references can
    be used:

        - data.new_dashboard: Globally accessible `NewDashboard()`-widget. This
                              widget will *never* modify the global dashboard
                              data! It merely displays it.

        - data.dashboard_data: Globally accessible `DashboardData()`-instance.
"""

import os
import json
import traceback
import dataclasses
from dataclasses import field, dataclass
import typing
from collections import OrderedDict
import data
from purefunctions import (
    write_json_file_with_comments,
    load_json_file_with_comments,
)


@dataclass
class Command:
    # name: str         # 'name' attribute not needed, it would only duplicate
    #                   # the key in the dictionary stored in DashboardData()
    icon_path: str
    commands: typing.List[str] = field(default_factory=list)


@dataclass
class PathPlaceholder:
    # name: str         # 'name' attribute not needed, it would only duplicate
    #                   # the key in the dictionary stored in DashboardData()
    value: str


@dataclass
class ToolPlaceholder:
    # name: str         # 'name' attribute not needed, it would only duplicate
    #                   # the key in the dictionary stored in DashboardData()
    value: str
    unique_id: str


@dataclass
class EnvVariable:
    # name: str         # 'name' attribute not needed, it would only duplicate
    #                   # the key in the dictionary stored in DashboardData()
    value: str


@dataclass
class DashboardData:
    commands: typing.OrderedDict[str, Command] = field(
        default_factory=OrderedDict
    )
    path_placeholders: typing.OrderedDict[str, PathPlaceholder] = field(
        default_factory=OrderedDict
    )
    tool_placeholders: typing.OrderedDict[str, ToolPlaceholder] = field(
        default_factory=OrderedDict
    )
    env_variables: typing.OrderedDict[str, EnvVariable] = field(
        default_factory=OrderedDict
    )


def get_env_variables() -> typing.OrderedDict[str, EnvVariable]:
    """Get environment variables from the system.

    Returns a dictionary of environment variables, with priority variables
    first.
    """
    env_vars = OrderedDict()

    # First add the most important ones in a specific order
    priority_vars = ["PATH", "HOME", "USER", "PROJECT_DIR"]
    for var_name in priority_vars:
        if var_name not in os.environ:
            continue
        env_vars[var_name.lower().replace(" ", "_")] = EnvVariable(
            value=os.environ[var_name],
        )

    # Then add all other environment variables (sorted alphabetically)
    for var_name, value in sorted(os.environ.items()):
        if var_name in priority_vars:
            continue
        env_vars[var_name.lower().replace(" ", "_")] = EnvVariable(
            value=value,
        )

    return env_vars


def get_default_dashboard_data() -> DashboardData:
    """Get a default DashboardData()-instance.
    The sane way to use this function, is to assign its return value to
    `data.dashboard_data`.
    """
    return DashboardData(
        # COMMANDS SECTION
        commands=OrderedDict(
            clean=Command(
                icon_path="icons/gen/clean.svg",
                commands=[
                    "cd <project>/build",
                    "<make> clean -f ../config/makefile",
                ],
            ),
            build=Command(
                icon_path="icons/gen/build.svg",
                commands=[
                    "cd <project>/build",
                    "<make> build -f ../config/makefile TOOLPREFIX=<gcc>/arm-none-eabi-",
                ],
            ),
            flash=Command(
                icon_path="icons/gen/flash.svg",
                commands=[
                    "cd <project>/build",
                    "<make> flash -f ../config/makefile FLASHTOOL=<openocd>",
                ],
            ),
        ),
        # PATH PLACEHOLDERS SECTION
        path_placeholders=OrderedDict(
            project=PathPlaceholder(
                value="C:/Users/krist/beetle_projects/my_project",
            ),
            beetle_tools=PathPlaceholder(
                value="C:/Users/krist/.embeetle/beetle_tools",
            ),
        ),
        # TOOL PLACEHOLDERS SECTION
        tool_placeholders=OrderedDict(
            gcc=ToolPlaceholder(
                value="<beetle_tools>/gnu_arm_toolchain_10.3.1_20210824_32b/bin",
                unique_id="gnu_arm_toolchain_10.3.1_20210824_32b",
            ),
            make=ToolPlaceholder(
                value="<beetle_tools>/gnu_make_4.2.1_64b",
                unique_id="gnu_make_4.2.1_64b",
            ),
            openocd=ToolPlaceholder(
                value="<beetle_tools>/openocd_geehy_0.12.0_dev20231026_64b/bin",
                unique_id="openocd_geehy_0.12.0_dev20231026_64b",
            ),
        ),
        # ENV VARIABLES SECTION
        env_variables=get_env_variables(),
    )


def store_dashboard_data(dashboard_data: DashboardData) -> bool:
    """Store the dashboard data to a JSON5 file in the project directory.

    Args:
        dashboard_data: The DashboardData instance to store, typically
                        data.dashboard_data

    Returns:
        bool: True if successfully stored, False otherwise
    """
    if data.current_project is None:
        return False

    try:
        # Create the storage path
        storage_path = f"{data.current_project.get_proj_rootpath()}/.beetle"
        os.makedirs(storage_path, exist_ok=True)

        # Convert the entire DashboardData structure to a dictionary. Then
        # delete the environment variables form the dict. There's no point in
        # saving them.
        dashboard_dict = dataclasses.asdict(dashboard_data)
        del dashboard_dict["env_variables"]

        # Add schema version for future compatibility
        dashboard_dict["schema_version"] = 1

        # Write to file
        file_path = f"{storage_path}/new_dashboard.json5"
        comment = str(
            "Embeetle New Dashboard configuration. This file "
            "stores dashboard commands, placeholders, and environment "
            "variables."
        )
        write_json_file_with_comments(file_path, dashboard_dict, comment)
        return True
    except Exception:
        # In a production environment, log the error here
        return False


def restore_dashboard_data() -> typing.Optional[DashboardData]:
    """Restore the dashboard data from a JSON5 file in the project directory.

    Returns:
        A DashboardData instance if the file exists and is valid, None otherwise.
    """
    assert data.current_project is not None
    if data.current_project is None:
        return None

    file_path = str(
        f"{data.current_project.get_proj_rootpath()}/.beetle/"
        f"new_dashboard.json5"
    )
    if not os.path.exists(file_path):
        return None

    # Create an empty `DashboardData()`-instance
    dashboard_data = DashboardData()

    try:
        json_data = load_json_file_with_comments(file_path)
        section_classes: dict[
            str, typing.Type[Command | PathPlaceholder | ToolPlaceholder]
        ] = {
            "commands": Command,
            "path_placeholders": PathPlaceholder,
            "tool_placeholders": ToolPlaceholder,
        }

        # Process each section
        for section_name, section_class in section_classes.items():
            if section_name not in json_data or section_name not in vars(
                dashboard_data
            ):
                continue

            section_dict = json_data[section_name]
            target_dict = getattr(dashboard_data, section_name)

            for item_name, item_data in section_dict.items():
                try:
                    assert dataclasses.is_dataclass(section_class)
                    # Filter the data to only include fields defined in the dataclass
                    filtered_data = {
                        k: v
                        for k, v in item_data.items()
                        if k in section_class.__dataclass_fields__
                    }

                    # Create the instance
                    target_dict[item_name] = section_class(**filtered_data)
                except (KeyError, TypeError, ValueError):
                    # Skip invalid entries but continue processing others
                    traceback.print_exc()
                continue
            continue
    except json.JSONDecodeError:
        # Handle JSON parsing errors specifically
        return None
    except:
        # Handle all other errors
        traceback.print_exc()
        return None

    return dashboard_data


# def initialize_dashboard() -> None:
#     """Initialize the new dashboard"""
#     assert data.new_dashboard is not None
#     data.new_dashboard.set_dashboard_data(data.dashboard_data)
#     return
#
#
# def initialize_dashboard_() -> None:
#     """Initialize the new dashboard section-by-section"""
#     assert data.new_dashboard is not None
#     for (
#         command_name,
#         command_data,
#     ) in data.dashboard_data.commands.items():
#         data.new_dashboard.add_command(
#             command_name=command_name,
#             command_data=command_data,
#         )
#         continue
#
#     for (
#         path_placeholder_name,
#         path_placeholder_data,
#     ) in data.dashboard_data.path_placeholders.items():
#         data.new_dashboard.add_path_placeholder(
#             path_placeholder_name=path_placeholder_name,
#             path_placeholder_data=path_placeholder_data,
#         )
#         continue
#
#     for (
#         tool_placeholder_name,
#         tool_placeholder_data,
#     ) in data.dashboard_data.tool_placeholders.items():
#         data.new_dashboard.add_tool_placeholder(
#             tool_placeholder_name=tool_placeholder_name,
#             tool_placeholder_data=tool_placeholder_data,
#         )
#         continue
#
#     for (
#         env_var_name,
#         env_var_data,
#     ) in data.dashboard_data.env_variables.items():
#         data.new_dashboard.add_env_variable(
#             env_var_name=env_var_name,
#             env_var_data=env_var_data,
#         )
#         continue
#     return
