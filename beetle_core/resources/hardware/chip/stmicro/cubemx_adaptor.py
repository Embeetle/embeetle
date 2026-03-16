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
import os, difflib
import regex as re

q = "'"
dq = '"'
bsl = "\\"


def get_new_adapted_cubemx_mainfile(
    proj_rootpath: str,
    chipname: str,
    chip_dict: Dict[str, Any],
    boardname: str,
    board_dict: Dict[str, Any],
    cor_boardname: str,
    cor_boarddict: Dict[str, Any],
    freertos: bool,
    printfunc: Callable,
    *args,
    **kwargs,
) -> Optional[str]:
    """This function reads the 'main.c' file and modifies it to let an LED
    blink.

    Return None if something fails.
    """
    mainpath = f"{proj_rootpath}/Src/main.c"
    if not os.path.isfile(mainpath):
        for _r_, _d_, _f_ in os.walk(proj_rootpath):
            for fname in _f_:
                if fname == "main.c":
                    mainpath = f"{_r_}/main.c"
                    _d_[:] = []
                    _f_[:] = []
                    break
                continue
            if os.path.isfile(mainpath):
                break
            continue
    if not os.path.isfile(mainpath):
        print(f"ERROR: Cannot find {q}main.c{q}!")
        input(f"Press any key to continue...")

    #! -----------[ HELP FUNCTIONS ]----------- !#
    def check_params(*_args) -> bool:
        "Check parameter validity."
        if chipname == "custom":
            printfunc(
                f"\nERROR: CHIP is CHIP({q}custom{q}).\n" "#ef2929",
            )
            return False
        chip_mf = chip_dict["manufacturer"]
        if (chip_mf is None) or (chip_mf.lower() != "stmicro"):
            printfunc(
                f"\nERROR: get_new_adapted_cubemx_mainfile() is only for stmicro chips.\n",
                "#ef2929",
            )
            return False
        return True

    def get_file_content(filepath: str) -> Optional[str]:
        "Get content from given file."
        content = None
        if not os.path.isfile(filepath):
            printfunc(
                f"\nERROR: Cannot find {q}{filepath}{q}\n",
                "#ef2929",
            )
            return None
        try:
            with open(
                filepath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                content = f.read().replace("\r\n", "\n")
        except:
            printfunc(
                f"\nERROR: Cannot read {q}{filepath}{q}\n",
                "#ef2929",
            )
            return None
        return content

    def get_curly_codeblock(head: str, source: str) -> Optional[str]:
        "Get content like {...}"
        head = head.replace("*", r"\*")
        head = head.replace("(", r"\s*\(\s*")
        head = head.replace(")", r"\s*\)\s*")
        head = head.replace(" ", r"\s+")
        content = None
        p = re.compile(head + r"({(?>[^{}]|(?1))*})", re.MULTILINE)
        m = p.search(source)
        try:
            content = m.group(1)
        except:
            printfunc(
                f"\nERROR: Cannot find {q}{head}{q} codeblock.\n",
                "#ef2929",
            )
            return None
        return content

    def apply_mod_on_code(
        origtxt: str, newtxt: str, code_content: str, codename: str
    ) -> Optional[str]:
        "Replace origtxt with nextxt in the code_content"
        if (origtxt is None) or (newtxt is None) or (code_content is None):
            return None
        temp = code_content.replace(origtxt, newtxt, 1)
        if temp == code_content:
            printfunc(
                f"\nERROR: Failed to apply modification on main.c.\n",
                "#ef2929",
            )
            return None
        eq = difflib.SequenceMatcher(None, code_content, temp).ratio()
        diff = f"{1 - eq:.3%}"
        code_content = temp
        printfunc(
            f"    Modification successful," f"{codename} changed by {diff}.\n",
            "#ffffff",
        )
        return code_content

    #! -----------[ MAIN FUNCTIONS ]----------- !#
    def start(*_args) -> Optional[str]:
        success = check_params()
        mainfile_content = get_file_content(mainpath)
        mainfile_content = (
            enable_gpio_portclock(mainfile_content)
            if mainfile_content is not None
            else None
        )
        mainfile_content = (
            configure_gpio_outputs(mainfile_content)
            if mainfile_content is not None
            else None
        )
        mainfile_content = (
            adapt_infiniteloop(mainfile_content)
            if mainfile_content is not None
            else None
        )
        mainfile_content = (
            remove_snippets(mainfile_content)
            if mainfile_content is not None
            else None
        )
        return mainfile_content

    def enable_gpio_portclock(mainfile_content: str) -> Optional[str]:
        printfunc(
            f"\n1. Enable GPIO clocks in MX_GPIO_Init(void)\n",
            "#edd400",
        )
        mx_gpio_init_cont: str = get_curly_codeblock(
            head="MX_GPIO_Init(void)",
            source=mainfile_content,
        )
        mx_gpio_init_cont_orig: str = mx_gpio_init_cont
        if mx_gpio_init_cont is None:
            return None

        # $ 1. List port clocks that are already enabled.
        portclock_done_list = []
        p = re.compile(r"__HAL_RCC_GPIO(\w)_CLK_ENABLE\(\);", re.MULTILINE)
        m_all: Iterator[Match] = p.finditer(mx_gpio_init_cont)
        for m in m_all:
            portchar = m.group(1)
            assert len(portchar) == 1
            portclock_done_list.append(portchar)

        # $ 2. List port clocks in need to get enabled.
        portclock_needed_list = []
        ledlist: Optional[List[Tuple[str, int, str]]] = None
        if boardname.lower() == "custom":
            # Find corresponding Nucleo/Disco board
            ledlist = __get_user_leds(cor_boardname, cor_boarddict)
        else:
            ledlist = __get_user_leds(boardname, board_dict)
        assert ledlist is not None
        for port in ledlist:
            portchar = port[0]
            pinnr = int(port[1])
            ledname = port[2]
            assert len(portchar) == 1
            if portchar in portclock_done_list:
                printfunc(f"    Clock for GPIO ", "#edd400")
                printfunc(f"P{portchar}{pinnr} ", "#ffffff")
                printfunc(f"(", "#edd400")
                printfunc(f"{ledname}", "#ffffff")
                printfunc(f") already enabled.\n", "#edd400")
            else:
                printfunc(f"    Clock for GPIO ", "#fcaf3e")
                printfunc(f"P{portchar}{pinnr} ", "#ffffff")
                printfunc(f"(", "#fcaf3e")
                printfunc(f"{ledname}", "#ffffff")
                printfunc(f") not yet enabled.\n", "#fcaf3e")
                assert portchar not in portclock_done_list
                if portchar not in portclock_needed_list:
                    portclock_needed_list.append(portchar)
        if len(portclock_needed_list) == 0:
            return mainfile_content

        # $ 3. Apply modifications to 'mx_gpio_init_cont'.
        assert mx_gpio_init_cont.startswith("{")
        for portchar in portclock_needed_list:
            m = p.search(mx_gpio_init_cont)  # find first clk enable statement
            addline = f"__HAL_RCC_GPIO{portchar}_CLK_ENABLE();"
            printfunc(f"    Enable GPIO clock: ", "#edd400")
            printfunc(f"{addline}\n", "#ffffff")
            if m is None:
                mx_gpio_init_cont = (
                    f"{{\n  {addline}\n  {mx_gpio_init_cont[1:]}"
                )
            else:
                mx_gpio_init_cont = mx_gpio_init_cont.replace(
                    m.group(0),
                    f"{addline}\n  {m.group(0)}",
                )  # put before first one

        # $ 4. Apply modifications to 'main.c'
        mainfile_content = apply_mod_on_code(
            origtxt=mx_gpio_init_cont_orig,
            newtxt=mx_gpio_init_cont,
            code_content=mainfile_content,
            codename="main.c file  ",
        )
        return mainfile_content

    def configure_gpio_outputs(mainfile_content: str) -> Optional[str]:
        printfunc(
            f"\n2. Configure GPIO outputs in MX_GPIO_Init(void)\n",
            "#edd400",
        )
        mx_gpio_init_cont = get_curly_codeblock(
            head="MX_GPIO_Init(void)",
            source=mainfile_content,
        )
        mx_gpio_init_cont_orig = mx_gpio_init_cont
        if mx_gpio_init_cont is None:
            return None

        # $ 1. Add configuration settings.
        ledlist: Optional[List[Tuple[str, int, str]]] = None
        if boardname.lower() == "custom":
            # Find corresponding Nucleo/Disco board
            ledlist = __get_user_leds(cor_boardname, cor_boarddict)
        else:
            ledlist = __get_user_leds(boardname, board_dict)
        assert mx_gpio_init_cont.endswith("}")
        mx_gpio_init_cont = mx_gpio_init_cont[0:-1]
        mx_gpio_init_cont += f"  //EMBEETLE INSERTS\n"
        mx_gpio_init_cont += f"  //----------------\n"
        if "GPIO_InitTypeDef" not in mx_gpio_init_cont:
            mx_gpio_init_cont += (
                f"  GPIO_InitTypeDef GPIO_InitStruct = {{0}};\n"
            )
        for port in ledlist:
            portchar = port[0]
            pinnr = int(port[1])
            ledname = port[2]
            #! GPIO_InitStruct might not yet been defined ! (GPIO_InitTypeDef GPIO_InitStruct = {0};)
            mx_gpio_init_cont += (
                f"  /* Configure GPIO P{portchar}{pinnr} ({ledname}) */\n"
            )
            mx_gpio_init_cont += f"  GPIO_InitStruct.Pin = GPIO_PIN_{pinnr};\n"
            mx_gpio_init_cont += (
                f"  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;\n"
            )
            mx_gpio_init_cont += f"  GPIO_InitStruct.Pull = GPIO_NOPULL;\n"
            mx_gpio_init_cont += (
                f"  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;\n"
            )
            mx_gpio_init_cont += (
                f"  HAL_GPIO_Init(GPIO{portchar}, & GPIO_InitStruct);\n"
            )
            mx_gpio_init_cont += "\n"
        mx_gpio_init_cont += "}"

        # $ 2. Apply modifications to 'main.c'.
        mainfile_content = apply_mod_on_code(
            origtxt=mx_gpio_init_cont_orig,
            newtxt=mx_gpio_init_cont,
            code_content=mainfile_content,
            codename="main.c file  ",
        )
        return mainfile_content

    def adapt_infiniteloop(mainfile_content: str) -> Optional[str]:
        printfunc(
            f"\n3. Adapt infinite loop in ",
            "#edd400",
        )
        func_head = ""
        if freertos:
            func_head = "void StartDefaultTask(void const * argument)"
        else:
            func_head = "int main(void)"
        printfunc(f"{func_head}\n", "#ffffff")
        func_cont = get_curly_codeblock(
            head=func_head,
            source=mainfile_content,
        )
        func_cont_orig = func_cont
        if func_cont is None:
            return None

        # $ 1. Determine loopheader and extract loop content.
        loopheader = None
        if freertos:
            loopheader = "for(;;)"
        else:
            loopheader = "while(1)"
        infiniteloop_cont = get_curly_codeblock(
            head=loopheader,
            source=func_cont,
        )
        infiniteloop_cont_orig = infiniteloop_cont
        if infiniteloop_cont is None:
            return None

        # $ 2. Adapt infinite loop.
        ledlist: Optional[List[Tuple[str, int, str]]] = None
        if boardname.lower() == "custom":
            # Find corresponding Nucleo/Disco board
            ledlist = __get_user_leds(cor_boardname, cor_boarddict)
        else:
            ledlist = __get_user_leds(boardname, board_dict)
        delayline = None
        if freertos:
            delayline = "osDelay(200);"
        else:
            delayline = "HAL_Delay(200);"
        assert infiniteloop_cont.endswith("}")
        infiniteloop_cont = infiniteloop_cont[0:-1]
        infiniteloop_cont += "\n"
        infiniteloop_cont += f"    //EMBEETLE INSERTS\n"
        infiniteloop_cont += f"    //----------------\n"
        if len(ledlist) > 1:
            for n in range(len(ledlist)):
                j = 0
                for port in ledlist:
                    portchar = port[0]
                    pinnr = int(port[1])
                    ledname = port[2]
                    infiniteloop_cont += f'    HAL_GPIO_WritePin(GPIO{portchar}, GPIO_PIN_{pinnr:<2}, {1 if j==n else 0});    // {ledname} {"on" if j==n else "off"}\n'
                    j += 1
                infiniteloop_cont += f"    {delayline}\n"
        elif len(ledlist) == 1:
            port = ledlist[0]
            portchar = port[0]
            pinnr = int(port[1])
            ledname = port[2]
            infiniteloop_cont += f'    HAL_GPIO_WritePin(GPIO{portchar}, GPIO_PIN_{pinnr:<2}, {1});    // {ledname} {"on" }\n'
            infiniteloop_cont += f"    {delayline}\n"
            infiniteloop_cont += f'    HAL_GPIO_WritePin(GPIO{portchar}, GPIO_PIN_{pinnr:<2}, {0});    // {ledname} {"off"}\n'
            infiniteloop_cont += f"    {delayline}\n"
        else:
            assert False
        infiniteloop_cont += "  }"

        # $ 3. Apply modifications to 'main.c'
        func_cont = apply_mod_on_code(
            origtxt=infiniteloop_cont_orig,
            newtxt=infiniteloop_cont,
            code_content=func_cont,
            codename=func_head,
        )
        mainfile_content = apply_mod_on_code(
            origtxt=func_cont_orig,
            newtxt=func_cont,
            code_content=mainfile_content,
            codename="main.c file  ",
        )
        return mainfile_content

    def remove_snippets(mainfile_content: str) -> Optional[str]:
        printfunc(
            f"\n4. Remove code parts from int main(void)\n",
            "#edd400",
        )
        mainfunc_cont = get_curly_codeblock(
            head="int main(void)",
            source=mainfile_content,
        )
        mainfunc_cont_orig = mainfunc_cont
        pattern = "MX_ETH_Init();"
        mainfunc_cont = mainfunc_cont.replace(pattern, f"/* {pattern} */")
        if mainfunc_cont == mainfunc_cont_orig:
            printfunc(f"    Nothing to remove.\n", "#ffffff")
        else:
            mainfile_content = apply_mod_on_code(
                origtxt=mainfunc_cont_orig,
                newtxt=mainfunc_cont,
                code_content=mainfile_content,
                codename="main.c file  ",
            )
        return mainfile_content

    return start()


def __get_user_leds(
    boardname: str,
    board_dict: Dict[str, Any],
) -> List[Tuple[str, int, str]]:
    """
    Get a list like:
        [ ('B', 0 ,'LD1') , ('B', 7 ,'LD2') ]
            |   |    |
            |   |    L ledname
            |   L pinnr
            L portchar
    """
    if boardname.lower() == "custom":
        return []
    user_leds = board_dict["user_leds"]
    if user_leds is None:
        return []
    if len(user_leds) == 0:
        return []

    # OPTION 1: In the old system, the "user_leds" value is a list like:
    #           ["PA5_LD1", "PA3_LD2", ... ]
    if isinstance(user_leds, list):
        _list_ = []
        for ledstr in user_leds:
            ledport = ledstr.split("_")[0]
            p = re.compile(r"\d+", re.MULTILINE)
            pinnr = int(p.search(ledport).group(0))
            p = re.compile(r"P(\w)", re.MULTILINE)
            portchar = p.search(ledport).group(1)
            ledname = ledstr.split("_")[1]
            _list_.append((portchar, pinnr, ledname))
        return _list_

    # OPTION 2: In the new system, the "user_leds" value is a dict like:
    #           { "LD1": "PA5" , "LD2": "PA3", ... }
    _list_ = []
    for ledname in user_leds.keys():
        ledport = user_leds[ledname]
        p = re.compile(r"\d+", re.MULTILINE)
        pinnr = int(p.search(ledport).group(0))
        p = re.compile(r"P(\w)", re.MULTILINE)
        portchar = p.search(ledport).group(1)
        _list_.append((portchar, pinnr, ledname))
    return _list_
