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

#!python

import sys
import os
import pathlib
import subprocess
import re
import shutil


def usage():
    """Print usage information for this package from the command line.

    Also provides basic information to understand the functions provided in this
    package.
    """

    excluded_sdk_path_list = "\n        ".join(excluded_sdk_paths)
    if sdk_env:
        supported_boards = "\n        ".join(get_supported_boards())
        supported_build_types = "\n        ".join(get_supported_build_types())
    else:
        supported_boards = (
            "(depends on HPMicro SDK tree run with two args to get the list)"
        )
        supported_build_types = (
            "(depends on HPMicro SDK tree run with two args to get the list)"
        )

    print(
        f"""
Usage: {os.path.basename(sys.argv[0])} <dest-tree> <top-of-HPMicro-tree> <board> <build-type> [samples/<project> ...]

    Generate self-contained sample projects from an HPMicro SDK tree.

    The HPMicro SDK tree is a directory that contains, amongst others, the
    following subdirectories:
        {sdk_version}
        {sdk_version}/hpm_sdk
        {sdk_version}/hpm_sdk/samples

    The destination tree is where the generated projects will be created. It
    will be created if it does not exist.  Existing files will not be removed.
    The generate a clean tree,  remove any existing files at that location.
    A typical value for Embeetle projects is <project>/source/samples.

    Generated projects will be in subdirectories of the destination tree
    matching the subdirectories of {sdk_version}/hpm_sdk/samples in which they
    are found. They will contain any source files and headers from the original
    directory, as well as any source files and headers used by the project from
    subdirectories that are normally not present or excluded in an Embeetle
    HPMicro project:
    
        {excluded_sdk_path_list}

    This allows the Embeetle user to select a project by force-excluding the
    source/samples subdirectory of his project, and then setting the project
    directory to automatic.

    Note that setting all excluded folders to automatic in Embeetle does not
    work, as some files conflict. Making self-contained projects is a
    work-around, until we can add a project selection widget to the Embeetle
    dashboard.

    Available boards are:
        {supported_boards}

    Available build types are:
        {supported_build_types}

    Suggested build type is flash_xip.

    The paths of sample projects to be generated, each starting with 'samples/',
    can be listed on the command line. If no projects are listed explicitly, all
    projects compatible with the specified board and build type will be
    generated.  """
    )
    sys.exit(1)


def set_sdk_env(new_sdk_env):
    """For most of the functions in this package, the HPMicro SDK to be used
    must be set first.

    Only one SDK can be active at any time, because we set some environment
    variables based on the SDK path. See init_sdk_env_vars().
    """
    global sdk_env, gnuriscv_toolchain_path, gnuriscv_gcc_exe, hpm_sdk_base
    global generate_project

    sdk_env = normalize_path(os.path.abspath(new_sdk_env))
    if not os.path.isdir(sdk_env + "/hpm_sdk"):
        report_error(f"Error: not an HPMicro SDK directory: {new_sdk_env}")

    gnuriscv_toolchain_path = f"{sdk_env}/toolchains/{toolchain_name}"
    gnuriscv_gcc_exe = (
        f"{gnuriscv_toolchain_path}/bin/riscv32-unknown-elf-gcc.exe"
    )
    hpm_sdk_base = f"{sdk_env}/hpm_sdk"
    generate_project = f"{sdk_env}/tools/scripts/generate_project.cmd"

    # Set the environment variables that are also set by start_cmd.cmd in the
    # HPMicro SDK tree. There is no easy way to directly reuse that CMD script.
    os.environ["PATH"] = (
        f"{sdk_env}/tools/cmake/bin;"
        f"{sdk_env}/toolchains/rv32imac-ilp32-multilib-win/bin;"
        f"{sdk_env}/tools/python3;"
        f"{sdk_env}/tools/Python3/Scripts;"
        f"{sdk_env}/tools/ninja;"
        f"{sdk_env}/tools/openocd;"
        f"{sdk_env}/tools/scripts;"
        "C:/Windows;C:/Windows/System32"
    )
    os.environ["PYTHONPATH"] = f"{sdk_env}/tools/Python3/Lib/site-packages"
    os.environ["TOOLCHAIN_NAME"] = toolchain_name
    os.environ["GNURISCV_TOOLCHAIN_PATH"] = gnuriscv_toolchain_path
    os.environ["HPM_SDK_BASE"] = hpm_sdk_base
    os.environ["HPM_SDK_TOOLCHAIN_VARIANT"] = ""
    os.environ["LONG_PATH_ENABLED"] = "true"
    os.environ["SDK_ENV_EXPECTED_GCC_BIN"] = gnuriscv_gcc_exe


def generate_sample_project_tree(dest_tree, board, build_type, samples):
    """Once the HPMicro SDK tree has been selected using set_sdk_env(), this
    function generates a sample project tree (dest_tree) for the given board,
    build type and sample projects.

    See description in usage() function.
    """
    print(f"{len(samples)} sample projects")
    generated_samples = []
    for sample in samples:
        print(f"\nGenerating {sample} ...")
        gen_project = run(
            f"cd {hpm_sdk_base}/{sample} & "
            f"{generate_project} -f -b {board} -t {build_type}"
        )
        # print("stderr: " + gen_project.stderr)
        # print("stdout: " + gen_project.stdout)
        if f" {board} can not support this sample" in gen_project.stderr:
            print(f" `-> not supported on {board}")
            continue
        if (
            f" target {build_type} has been excluded for this example"
            in gen_project.stderr
        ):
            print(f" `-> not supported with build type {build_type}")
            continue
        if gen_project.stderr:
            print(f" `-> error output:\n{gen_project.stderr}")
            report_error(f"Cannot generate {sample} for {board}")
        print(gen_project.stdout)
        generated_samples.append(sample)
        build_dir = f"{hpm_sdk_base}/{sample}/{board}_build"
        ninja = run(f"cd {build_dir} & ninja -v -n")
        # print(ninja.stdout)
        ninja_lines = ninja.stdout.splitlines()
        compilation_commands = [
            line.split(" ", 1)[1].replace("\\", "/").replace('/"', '\\"')
            for line in ninja_lines
            if line.endswith((".c", ".S"))
        ]
        # for command in compilation_commands:
        #    print(command)

        project_files = set()
        sdk_files_needed_locally = set()

        def use_file(abs_path):
            sdk_rel_path = abs_path.removeprefix(f"{hpm_sdk_base}/")
            if sdk_rel_path.startswith(f"{sample}/"):
                project_files.add(sdk_rel_path)
            elif sdk_rel_path.startswith(excluded_sdk_paths):
                sdk_files_needed_locally.add(sdk_rel_path)

        for command in compilation_commands:
            # print(f"command: {command}")
            source = normalize_path(command.split()[-1])
            if "/build_tmp/" in source:
                continue
            use_file(source)

            aux_command = command.replace(
                " CMakeFiles/", f" {build_dir}/CMakeFiles/"
            )
            for header in get_included_headers(aux_command):
                use_file(header)

        copy_files(project_files, hpm_sdk_base, f"{dest_tree}")
        print(f"{len(project_files)} project files copied")

        copy_files(
            sdk_files_needed_locally, hpm_sdk_base, f"{dest_tree}/{sample}"
        )
        print(f"{len(sdk_files_needed_locally)} SDK files copied")
    print(
        f"Generated {len(generated_samples)} sample projects"
        f" for {board} using {build_type}:"
    )
    for sample in generated_samples:
        print(f"  {sample}")


def get_sample_project_paths():
    """Return the list of all sample project paths in the current HPMicro SDK
    tree.

    Each sample project path is a string starting with 'sample/' representing
    the path of a sample project in the SDK tree.
    """
    samples_dir = "samples"
    marker = "CMakeLists.txt"
    return [
        samples_dir + "/" + path[: -(len(marker) + 1)]
        for path in find(hpm_sdk_base + "/" + samples_dir, marker)
    ]


def get_supported_boards():
    """Return the list of all HPMicro boards supported by the current HPMicro
    SDK tree.

    This returns a list of strings.
    """
    boards_result = run_in_sdk(f"{generate_project} -list")
    if boards_result.stderr:
        print(f"Error output:\n{boards_result.stderr}")
        report_error("cannot run generate_project -list for boards list")
    return boards_result.stdout.splitlines()


def get_supported_build_types():
    """Return the list of all build types supported by the current HPMicro SDK
    tree.

    This returns a list of strings.
    """
    result = run_in_sdk(f"{generate_project}")
    if result.stderr:
        print(f"Error output:\n{result.stderr}")
        report_error("cannot run generate_project for build types list")
    return [
        line.split()[1]
        for line in result.stdout.splitlines()
        if line.startswith("   -  ")
    ]


# The following paths are assumed to be absent or force-excluded in Embeetle
# projects.  Files from the HPMicro SDK on these paths are copied into the local
# project.
excluded_sdk_paths = (
    "samples/",
    "middleware/",
    "components/enet_phy/",
    "drivers/src/hpm_enet_drv.c",
    "drivers/src/hpm_enet_drv.c",
)

# Some parameters of the current HPMicro SDK tree. These are initialized in
# set_sdk_env().
sdk_version = "sdk_env_v1.1.0"
toolchain_name = "rv32imac-ilp32-multilib-win"
sdk_env = None
gnuriscv_toolchain_path = None
gnuriscv_gcc_exe = None
hpm_sdk_base = None
generate_project = None


def run_in_sdk(command):
    """Run a CMD cshell command with all settings needed for the HPMicro SDK,
    from the top of the SDK tree."""
    return run(f"{sdk_env}/hpm_sdk/env.cmd & " f"cd {sdk_env} & {command}")


def get_included_headers(command):
    """Get the absolute paths of all header files included by the given
    compilation command."""
    # -c requests compilation only
    # -E requests preprocessing only
    # -H requests a list of included header files on stderr.
    header_command = command.replace(" -c ", " ") + " -E -H"
    result = run(header_command)
    if result.returncode:
        print(header_command)
        print(result.stderr)
        report_error(f"Cannot extract headers (exit code {result.returncode})")
    return {
        normalize_path(line.split(" ", 1)[1])
        for line in result.stderr.splitlines()
        if line.startswith(".")
    }


class HPMicroException(Exception):
    """Exception raised by any errors detected in this module."""

    pass


def report_error(message):
    """Report an error message.

    Intended for use of this package from the command line.
    """
    raise HPMicroException(message)


def find(dir, glob_pattern):
    """Return the list of all files in the given directory path matching the
    given glob expression.

    A glob expression is a string containing * (match anything except /), [x-y]
    (match any character in the range x-y), ? (match any single character) or **
    (match anything including /).

    The returned list contains paths relative to the given directory.
    """
    dir_path = pathlib.Path(dir)
    return [
        normalize_path(str(path.relative_to(dir_path)))
        for path in dir_path.glob("**/" + glob_pattern)
    ]


def run(command):
    """Run a shell command and capture stdout and stderr."""
    return subprocess.run(command, shell=True, capture_output=True, text=True)


def copy_files(relative_paths, from_dir, to_dir):
    """Copy files with given relative paths (a list of strings) from one
    directory to another directory.

    Creates the necessary subdirectories of the target directories of they don't
    exist.
    """
    for path in relative_paths:
        # print(f"copy {from_dir}/{path} to {to_dir}/{path}")
        dir = os.path.dirname(path)
        if dir:
            os.makedirs(f"{to_dir}/{dir}", exist_ok=True)
        shutil.copy(f"{from_dir}/{path}", f"{to_dir}/{path}")


def normalize_path(path):
    """Normalize a path, so that paths can be compared.

    This lowercases the path and replaces any backslashes by slashes. There is
    currently no need to normalize /./ or /../ occurrences.
    """
    return path.lower().replace("\\", "/")


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            usage()
        dest_tree = sys.argv[1]
        set_sdk_env(f"{sys.argv[2]}/{sdk_version}")
        print(f"dest tree: {dest_tree}")
        print(f"HPMicro tree: {sdk_env}")

        if len(sys.argv) < 5:
            usage()

        boards = get_supported_boards()
        board = sys.argv[3]
        if not board in boards:
            board_names = " ".join(boards)
            report_error(f"unknown board {board} - use one of {board_names}")

        build_types = get_supported_build_types()
        build_type = sys.argv[4]
        if not build_type in build_types:
            build_type_names = " ".join(build_types)
            report_error(
                f"unknown build type {build_type} "
                f"- use one of {build_type_names}"
            )

        if len(sys.argv) > 5:
            generate_sample_project_tree(
                dest_tree, board, build_type, sys.argv[5:]
            )
        else:
            generate_sample_project_tree(
                dest_tree, board, build_type, get_sample_project_paths()
            )

    except HPMicroException as error:
        print(error, file=sys.stderr)
        sys.exit(1)
