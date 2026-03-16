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
import os
import textwrap
import data, purefunctions, functions, gui, iconfunctions, serverfunctions

q = "'"
dq = '"'


def __get_sa_about_text(*args) -> str:
    """Get a general description of what the SA does."""
    h = data.get_general_font_height()
    src = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/gen/source_analyzer.png",
        width=int(1.5 * h),
    )
    sa_link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/beetle-anatomy/source-analyzer"
    return f"""
    <p align="left">
        The {src} <b>Source Analyzer</b> - also called 'engine' - builds an internal<br>
        database with all the symbols defined in your source files (functions,<br>
        variables, ...). With this data, Embeetle provides important features<br>
        like:<br>
    </p>
    <ul>
        <li>
            <b>Click-and-jump:</b> Hold down the Ctrl-key and click on a symbol to<br>
            jump to its definition.<br>
        </li>
        <li>
            <b>Symbol information:</b> Right-click on a symbol to view info like<br>
            where it's defined, declared and used throughout the code. You<br>
            can also jump to any of these usages of the symbol.<br>
        </li>
        <li>
            <b>Autocompletion:</b> Under construction.<br>
        </li>
    </ul>
    <p align="left">
        <a href="{sa_link}" style="color: #729fcf;">Click here</a> for more information.
    </p>
    """


def source_analyzer_help(*args) -> None:
    """Help text shown for the source analyzer button."""
    css = purefunctions.get_css_tags()
    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def report_internal_error(
    msg: Optional[str], *args, wrap=False
) -> Tuple[str, Callable]:
    """Popup shown for internal error in source analyzer."""
    if msg is None:
        msg = ""

    # Replace line-breaks with HTML breaks
    msg = msg.replace("\n", "<br>")

    if wrap:
        msg = "<br>".join(textwrap.wrap(msg, width=80))

    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/beetle_sorry_01.png",
        width=int(7 * h),
    )
    forum_link = "https://forum.embeetle.com"
    css = purefunctions.get_css_tags()

    text = f"""
{css['h1']}INTERNAL ERROR{css['/hx']}
<p align="left">
    FATAL: internal error - save changes and restart Embeetle<br>
    {img}<br>
    Please report the bug on our forum:<br>
    <a href="{forum_link}" style="color: #729fcf;">{forum_link}</a><br>
    <br>
    Copy-paste the content from this file there:<br>
    &#60;project&#62;/.beetle/output.txt<br>
    <br>
    ERROR DETAILS:
</p>
{msg}
    """
    return text, functions.open_url


def sa_status_ok(*args) -> None:
    """User clicks the help button next to the SA status lineedit, which shows
    the SA to be okay."""
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Status{css['h2']}
    <p align="left">
        The <b>Source Analyzer</b> status seems okay. This means that it was able to<br>
        extract the compilation flags from your makefile and parse the source files<br>
        (C, C++ and asm) accordingly.<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def sa_launch_problem(*args) -> None:
    """User clicks the help button next to the SA status lineedit, which shows
    the SA to have a launch problem."""

    def catch_click(key: str, *_args, **_kwargs) -> None:
        if key is None:
            return
        if key.startswith("http"):
            functions.open_url(key)
        if key.lower() == "dashboard":
            data.main_form.projects.show_dashboard()
        return

    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    end = css["end"]

    launch_issues = (
        purefunctions.import_module("components.sourceanalyzerinterface")
        .SourceAnalysisCommunicator()
        .get_sa_launch_issues()
    )
    if launch_issues is None:
        purefunctions.printc(
            f"\nERROR: Function {q}sa_launch_problem(){q} invoked in {q}help/"
            f"help_subjects/source_analyzer.py{q} even though there are no "
            f"launch problems!\n",
            color="error",
        )
        sa_status_ok()
        return

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Status{css['h2']}
    <p align="left">
        A fundamental problem in your project prevents the <b>Source Analyzer</b> from<br>
        starting:<br>
        {tab}{red}{q}{launch_issues}{q}{end}<br>
    </p>
    <p align="left">
        Go to the <a href="dashboard" style="color: #729fcf;">Dashboard</a> to fix this problem.<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=catch_click,
    )
    return


def sa_internal_problem(*args) -> None:
    """User clicks the help button next to the SA status lineedit, which shows
    the SA to have an internal problem."""
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Status{css['h2']}
    <p align="left">
        The <b>Source Analyzer</b> crashed internally. Please restart Embeetle<br>
        and report this problem if it persists.<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def sa_project_err(*args) -> None:
    """User clicks the help button next to the SA status lineedit, which shows
    the SA to have a project error."""

    def catch_click(key: str, *_args, **_kwargs) -> None:
        if key is None:
            return
        if key.startswith("http"):
            functions.open_url(key)
        if key.lower() == "dashboard":
            data.main_form.projects.show_dashboard()
        if key.lower() == "diagnostics":
            data.main_form.projects.show_diagnostics()
        return

    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Status{css['h2']}
    <p align="left">
        The <b>Source Analyzer</b> could not parse one or more source files (C, C++,<br>
        asm), because it could not extract the compilation flags from the<br>
        makefile. Most probably the problem is situated in your makefile or<br>
        one of the files included in that makefile. Less likely, the problem<br>
        is related to the compiler tool or GNU make.<br>
    </p>
    <p align="left">
        Go to the <a href="diagnostics" style="color: #729fcf;">Diagnostics</a> tab to view more details about the problem. Also<br>
        check if everything is okay in the <a href="dashboard" style="color: #729fcf;">Dashboard</a>.<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=catch_click,
    )
    return


def sa_busy(*args) -> None:
    """User clicks the help button next to the SA status lineedit, which shows
    the SA to be busy."""
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Status{css['h2']}
    <p align="left">
        The <b>Source Analyzer</b> is still parsing your source files. When it{q}s finished,<br>
        you{q}ll enjoy all the features it provides.<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def sa_dependencies(*args) -> None:
    """User clicks the help button next to the SA dependencies root item."""

    def catch_click(key: str, *_args, **_kwargs) -> None:
        if key is None:
            return
        if key.startswith("http"):
            functions.open_url(key)
        if key.lower() == "dashboard":
            data.main_form.projects.show_dashboard()
        if key.lower() == "diagnostics":
            data.main_form.projects.show_diagnostics()
        if key.lower() == "dashboard/build_dir":
            data.dashboard.go_to_item(
                abspath=f"TreepathRootItem/BUILD_DIR",
                callback1=None,
                callbackArg1=None,
                callback2=None,
                callbackArg2=None,
            )
        if key.lower() == "dashboard/makefile":
            data.dashboard.go_to_item(
                abspath=f"TreepathRootItem/MAKEFILE",
                callback1=None,
                callbackArg1=None,
                callback2=None,
                callbackArg2=None,
            )
        if key.lower() == "dashboard/build_automation":
            data.dashboard.go_to_item(
                abspath=f"ToolRootItem/BUILD_AUTOMATION",
                callback1=None,
                callbackArg1=None,
                callback2=None,
                callbackArg2=None,
            )
        if key.lower() == "dashboard/compiler_toolchain":
            data.dashboard.go_to_item(
                abspath=f"ToolRootItem/COMPILER_TOOLCHAIN",
                callback1=None,
                callbackArg1=None,
                callback2=None,
                callbackArg2=None,
            )
        return

    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    h = data.get_general_font_height()
    build_folder = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/folder/closed/build.png",
        width=int(1.5 * h),
    )
    makefile = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/file/file_mk.png",
        width=int(1.5 * h),
    )
    build_automation = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/tools/build_automation.png",
        width=int(1.5 * h),
    )
    compiler_toolchain = iconfunctions.get_rich_text_pixmap_middle(
        pixmap_relpath="icons/tools/compiler_toolchain.png",
        width=int(1.5 * h),
    )

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Dependencies{css['h2']}
    <p align="left">
        The <b>Source Analyzer</b> extracts the compiler flags from the makefile, and<br>
        parses your source files (C, C++, asm) accordingly. For this to work<br>
        properly, your project must meet a few minimal requirements:
    </p>
    <ul>
        <li>
            {build_folder} <a href="dashboard/build_dir" style="color: #729fcf;"><b>Build folder:</b></a> The Source Analyzer should know where your build<br>
            folder is located. Make sure it{q}s properly defined in the dashboard.<br>
            <br>
            {tab}<b>NOTE 1:</b><br>
            {tab}The build folder is where build artefacts (.o files and the like)<br>
            {tab}end up during compilation. In the case of <b>shadow building</b>, this is<br>
            {tab}a separate folder, such as:<br>
            {tab}{tab}{green}{q}&#60;project&#62;/build{q}{end}<br>
            {tab}For <b>inline building</b>, it{q}s usually just the toplevel project folder<br>
            {tab}<br>
            {tab}<b>NOTE 2:</b><br>
            {tab}The Source Analyzer assumes that the build command happens from<br>
            {tab}the build folder location.<br>
        </li>
        <li>
            {makefile} <a href="dashboard/makefile" style="color: #729fcf;"><b>Makefile:</b></a> The Source Analyzer should know where your makefile is<br>
            located. Make sure it{q}s properly defined in the dashboard.<br>
            <br>
            {tab}<b>NOTE:</b><br>
            {tab}The Source Analyzer invokes GNU Make with the {green}{q}--dry-run{q}{end} flag.<br>
            {tab}This way, it tries to extract all the compiler flags per source<br>
            {tab}file. This step only works if it knows where the makefile is and<br>
            {tab}there are no errors in it.<br>
        </li>
        <li>
            {build_automation} <a href="dashboard/build_automation" style="color: #729fcf;"><b>Build Automation:</b></a> The Source Analyzer should know where your build<br>
            automation tool (eg. GNU Make) is located. Make sure it{q}s properly defined<br>
            in the dashboard.<br>
        </li>
        <li>
            {compiler_toolchain} <a href="dashboard/compiler_toolchain" style="color: #729fcf;"><b>Compiler Toolchain:</b></a> The Source Analyzer should know where your compiler<br>
            toolchain (eg. GNU ARM GCC) is located. Make sure it{q}s properly defined<br>
            in the dashboard.<br>
        </li>
    </ul>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=catch_click,
    )
    return


def sa_cpu_cores(*args) -> None:
    """User clicks the help button next to the SA cpu cores dropdown."""
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    red = css["red"]
    end = css["end"]
    nr_of_cores: Optional[str] = str(os.cpu_count())
    if nr_of_cores is None:
        nr_of_cores = f"{red}undetermined{end}"
    else:
        nr_of_cores = f"{green}{nr_of_cores} cores{end}"

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. CPU Cores{css['h2']}
    <p align="left">
        You can select the nr of threads you want to assign to the <b>Source<br>
        Analyzer</b>. Beware, increasing this number does not always result in<br>
        better performance. The optimal setting is the nr of CPU cores in your<br>
        computer. For your computer, that is:<br>
        <br>
        {tab}{nr_of_cores}<br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def sa_clear_cache(*args) -> None:
    """User clicks the help for the SA clear cache button."""
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    red = css["red"]
    end = css["end"]

    text = f"""
    {css['h1']}SOURCE ANALYZER{css['/hx']}
    {css['h2']}1. Clear cache{css['h2']}
    <p align="left">
        Clear the cache from the <b>Source Analyzer</b> and let it re-analyze everything<br>
        in your project. If you need to do this regularly, it means that something<br>
        doesn{q}t work properly. Please <a href="{serverfunctions.get_base_url_wfb()}/#contact" style="color: #729fcf;">report</a> it to us.<br> 
        <br>
    </p>
    {css['h2']}2. About the Source Analyzer{css['h2']}
    {__get_sa_about_text()}
    """
    popupdialog_module = purefunctions.import_module("gui.dialogs.popupdialog")
    popupdialog_module.PopupDialog.ok(
        icon_path="icons/gen/source_analyzer.png",
        title_text="SOURCE ANALYZER",
        text=text,
        text_click_func=functions.open_url,
    )
    return
