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

q = "'"
dq = '"'
bsl = "\\"


def get_linkerscript(
    chipname: str,
    chip_dict: Dict[str, Any],
    *args,
    **kwargs,
) -> str:
    """The 'chip_dict' passed here is already overridden by the board
    dictionary."""
    mem_data = chip_dict["linkerscript"]["memory"]

    # $ Construct MEMORY regions
    memlines = [
        f'{memname} ({mem_data[memname]["rights"]}): '
        f'ORIGIN = {mem_data[memname]["origin"]}, '
        f'LENGTH = {mem_data[memname]["length"]}\n'
        for memname in mem_data.keys()
    ]
    memory = "    " + "    ".join(memlines)

    # $ Define main memory regions
    # FLASH
    main_flash_name: Optional[str] = None
    for name in mem_data.keys():
        if "flash" in name.lower():
            main_flash_name = name
            break
        continue
    else:
        main_flash_name = "FLASH"
    # RAM
    main_ram_name: Optional[str] = None
    for name in mem_data.keys():
        if "ram" in name.lower():
            main_ram_name = name
            break
        continue
    else:
        main_ram_name = "RAM"

    # $ Define SNIPPETS
    ccmram_snippet = ""
    ramfunc_snippet = ""
    mb_mem_snippet = ""
    if chipname in (
        "stm32f303k8",
        "stm32f303vc",
        "stm32f407vg",
        "stm32f429zi",
    ):
        ccmram_snippet = __get_ccmram_snippet()
    if chipname in (
        "stm32f103c8",
        "stm32wb55rg",
        "stm32wb55cg",
    ):
        ramfunc_snippet = __get_ramfunc_snippet()
    if chipname in (
        "stm32wb55rg",
        "stm32wb55cg",
    ):
        mb_mem_snippet = __get_mb_mem_snippet()

    # $ Get general linkerscript
    return __get_general_linkerscript(
        chipname=chipname,
        memory=memory,
        main_flash_name=main_flash_name,
        main_ram_name=main_ram_name,
        estack=chip_dict["linkerscript"]["params"].get("ESTACK"),
        min_heap_size=chip_dict["linkerscript"]["params"].get("MIN_HEAP_SIZE"),
        min_stack_size=chip_dict["linkerscript"]["params"].get(
            "MIN_STACK_SIZE"
        ),
        ccmram_snippet=ccmram_snippet,
        ramfunc_snippet=ramfunc_snippet,
        mb_mem_snippet=mb_mem_snippet,
    )


def __get_mb_mem_snippet() -> str:
    """"""
    return """MAPPING_TABLE (NOLOAD) : { *(MAPPING_TABLE) } >RAM_SHARED
    MB_MEM1 (NOLOAD)       : { *(MB_MEM1) } >RAM_SHARED
    /* used by the startup to initialize .MB_MEM2 data */
    _siMB_MEM2 = LOADADDR(.MB_MEM2);
    .MB_MEM2 :
    {
        _sMB_MEM2 = . ;
        *(MB_MEM2) ;
        _eMB_MEM2 = . ;
    } >RAM_SHARED AT> FLASH
"""


def __get_ramfunc_snippet() -> str:
    """"""
    content = str(
        "        *(.RamFunc)        /* .RamFunc sections */\n"
        "        *(.RamFunc*)       /* .RamFunc* sections */\n"
    )
    return content


def __get_ccmram_snippet() -> str:
    """"""
    content = f"""
    _siccmram = LOADADDR(.ccmram);

    /* CCM-RAM section
    *
    * IMPORTANT NOTE!
    * If initialized variables will be placed in this section,
    * the startup code needs to be modified to copy the init-values.
    */
    .ccmram :
    {{
        . = ALIGN(4);
        _sccmram = .;       /* create a global symbol at ccmram start */
        *(.ccmram)
        *(.ccmram*)
        . = ALIGN(4);
        _eccmram = .;       /* create a global symbol at ccmram end */
    }} >CCMRAM AT> FLASH
"""
    return content


def __get_general_linkerscript(
    chipname: str,
    memory: str,
    main_flash_name: str,
    main_ram_name: str,
    estack: str,
    min_heap_size: str,
    min_stack_size: str,
    ccmram_snippet: str,
    ramfunc_snippet: str,
    mb_mem_snippet: str,
    *args,
    **kwargs,
) -> str:
    """"""
    content = f"""/*
********************************************************************************
**                                                                            **
**                    LINKERSCRIPT FOR {q}{chipname}{q}
**                                                                            **
********************************************************************************
** Please consult the COPYRIGHT(c) notice at the bottom of the file.
**
*/

/* Entry Point */
ENTRY(Reset_Handler)

/* Highest address of the user mode stack */
_estack = {estack};    /* end of RAM */
/* Generate a link error if heap and stack don't fit into RAM */
_Min_Heap_Size = {min_heap_size};      /* required amount of heap  */
_Min_Stack_Size = {min_stack_size};    /* required amount of stack */

/* Define memory regions. */
MEMORY
{{
{memory}
}}

/* Define output sections */
SECTIONS
{{
    /* The startup code goes first into {main_flash_name} */
    .isr_vector :
    {{
        . = ALIGN(8);
        KEEP(*(.isr_vector)) /* Startup code */
        . = ALIGN(8);
    }} >{main_flash_name}

    /* The program code and other data goes into {main_flash_name} */
    .text :
    {{
        . = ALIGN(8);
        *(.text)           /* .text sections (code) */
        *(.text*)          /* .text* sections (code) */
        *(.glue_7)         /* glue arm to thumb code */
        *(.glue_7t)        /* glue thumb to arm code */
        *(.eh_frame)

        KEEP (*(.init))
        KEEP (*(.fini))

        . = ALIGN(8);
        _etext = .;        /* define a global symbols at end of code */
    }} >{main_flash_name}

    /* Constant data goes into {main_flash_name} */
    .rodata :
    {{
        . = ALIGN(8);
        *(.rodata)         /* .rodata sections (constants, strings, etc.) */
        *(.rodata*)        /* .rodata* sections (constants, strings, etc.) */
        . = ALIGN(8);
    }} >{main_flash_name}

    .ARM.extab :
    {{
        . = ALIGN(8);
        *(.ARM.extab* .gnu.linkonce.armextab.*)
        . = ALIGN(8);
    }} >{main_flash_name}

    .ARM : {{
        . = ALIGN(8);
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
        . = ALIGN(8);
    }} >{main_flash_name}

    .preinit_array :
    {{
        . = ALIGN(8);
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP (*(.preinit_array*))
        PROVIDE_HIDDEN (__preinit_array_end = .);
        . = ALIGN(8);
    }} >{main_flash_name}

    .init_array :
    {{
        . = ALIGN(8);
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP (*(SORT(.init_array.*)))
        KEEP (*(.init_array*))
        PROVIDE_HIDDEN (__init_array_end = .);
        . = ALIGN(8);
    }} >{main_flash_name}

    .fini_array :
    {{
        . = ALIGN(8);
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP (*(SORT(.fini_array.*)))
        KEEP (*(.fini_array*))
        PROVIDE_HIDDEN (__fini_array_end = .);
        . = ALIGN(8);
    }} >{main_flash_name}

    /* used by the startup to initialize data */
    _sidata = LOADADDR(.data);

    /* Initialized data sections goes into {main_ram_name}, load LMA copy after code */
    .data :
    {{
        . = ALIGN(8);
        _sdata = .;        /* create a global symbol at data start */
        *(.data)           /* .data sections */
        *(.data*)          /* .data* sections */
{ramfunc_snippet}

        . = ALIGN(8);
        _edata = .;        /* define a global symbol at data end */
    }} >{main_ram_name} AT> {main_flash_name}
{ccmram_snippet}
    /* Uninitialized data section */
    . = ALIGN(8);
    .bss :
    {{
        /* This is used by the startup in order to initialize the .bss section */
        _sbss = .;         /* define a global symbol at bss start */
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)

        . = ALIGN(8);
        _ebss = .;         /* define a global symbol at bss end */
        __bss_end__ = _ebss;
    }} >{main_ram_name}

    /* User_heap_stack section, used to check that there is enough RAM left */
    ._user_heap_stack :
    {{
        . = ALIGN(8);
        PROVIDE ( end = . );
        PROVIDE ( _end = . );
        . = . + _Min_Heap_Size;
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
    }} >{main_ram_name}

    /* Remove information from the standard libraries */
    /DISCARD/ :
    {{
        libc.a ( * )
        libm.a ( * )
        libgcc.a ( * )
    }}

    .ARM.attributes 0 : {{ *(.ARM.attributes) }}
    {mb_mem_snippet}
}}


/*
*****************************************************************************
** This linkerscript is auto-generated by Embeetle (https://embeetle.com).
** We have inspired our linkerscript template upon a collection of
** linkerscripts from Ac6 (http://www.openstm32.org/HomePage), having the
** following copyright notice:
**
** COPYRIGHT(c) 2014 Ac6
**
** Redistribution and use in source and binary forms, with or without modification,
** are permitted provided that the following conditions are met:
**   1. Redistributions of source code must retain the above copyright notice,
**      this list of conditions and the following disclaimer.
**   2. Redistributions in binary form must reproduce the above copyright notice,
**      this list of conditions and the following disclaimer in the documentation
**      and/or other materials provided with the distribution.
**   3. Neither the name of Ac6 nor the names of its contributors
**      may be used to endorse or promote products derived from this software
**      without specific prior written permission.
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
** AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
** IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
** DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
** FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
** DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
** SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
** CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
** OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
**
*****************************************************************************
** Concerning all the changes with respect to the original linkerscripts (the
** ones from which we've taken inspiration), we apply the following copyright
** notice:
**
** COPYRIGHT(c) 2023 Embeetle
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
** AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
** IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
** DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
** FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
** DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
** SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
** CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
** OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
**
*****************************************************************************
*/"""
    return content
