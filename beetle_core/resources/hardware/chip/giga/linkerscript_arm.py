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
import itertools

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

    content = f"""/*
********************************************************************************
**                                                                            **
**                    LINKERSCRIPT FOR {q}{chipname}{q}
**                                                                            **
********************************************************************************
**
*/

/* Entry Point */
ENTRY(Reset_Handler)

/* Define memory regions. */
MEMORY
{{
{memory}
}}

/* Define output sections */
SECTIONS
{{
    __stack_size = DEFINED(__stack_size) ? __stack_size : 2K;
    
    /* ISR vectors: startup code goes first into {main_flash_name} */
    .vectors :
    {{
        . = ALIGN(4);
        KEEP(*(.vectors))
        . = ALIGN(4);
        __Vectors_End = .;
        __Vectors_Size = __Vectors_End - __gVectors;
    }} >{main_flash_name}

    /* The program code and other data goes into {main_flash_name} */
    .text :
    {{
        . = ALIGN(4);
        *(.text)      /* .text sections (code) */
        *(.text*)     /* .text* sections (code) */
        *(.glue_7)    /* glue arm to thumb code */
        *(.glue_7t)   /* glue thumb to arm code */
        *(.eh_frame)
        
        KEEP (*(.init))
        KEEP (*(.fini))
        
        . = ALIGN(4);
        _etext = .;    /* define a global symbol at end of code */
    }} >{main_flash_name}

    /* Constant data goes into {main_flash_name} */
    .rodata :
    {{
        . = ALIGN(4);
        *(.rodata)   /* .rodata sections (constants, strings, etc.) */
        *(.rodata*)  /* .rodata* sections (constants, strings, etc.) */
        . = ALIGN(4);
    }} >{main_flash_name}


    .ARM.extab :
    {{ 
        *(.ARM.extab* .gnu.linkonce.armextab.*) 
    }} >{main_flash_name}
  
    .ARM :
    {{
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    }} >{main_flash_name}

    .ARM.attributes :
    {{
        *(.ARM.attributes)
    }} >{main_flash_name}

    .preinit_array :
    {{
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP (*(.preinit_array*))
        PROVIDE_HIDDEN (__preinit_array_end = .);
    }} >{main_flash_name}
  
    .init_array :
    {{
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP (*(SORT(.init_array.*)))
        KEEP (*(.init_array*))
        PROVIDE_HIDDEN (__init_array_end = .);
    }} >{main_flash_name}
  
    .fini_array :
    {{
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP (*(.fini_array*))
        KEEP (*(SORT(.fini_array.*)))
        PROVIDE_HIDDEN (__fini_array_end = .);
    }} >{main_flash_name}

    /* used by the startup to initialize data */
    _sidata = LOADADDR(.data);
    /* Initialized data sections go into {main_ram_name}, load LMA copy after code */
    .data :
    {{
        . = ALIGN(4);
        _sdata = .;    /* create a global symbol at data start */
        *(.data)       /* .data sections */
        *(.data*)      /* .data* sections */
        . = ALIGN(4);
        _edata = .;    /* define a global symbol at data end */
    }} >{main_ram_name} AT>{main_flash_name}

    /* Uninitialized data section */
    . = ALIGN(4);
    .bss :
    {{
        /* This is used by the startup in order to initialize the .bss secion */
        _sbss = .;         /* define a global symbol at bss start */
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;         /* define a global symbol at bss end */
        __bss_end__ = _ebss;
    }} >{main_ram_name}

    . = ALIGN(8);
    PROVIDE ( end = _ebss );
    PROVIDE ( _end = _ebss );
  
    /* Stack section */
    .stack ORIGIN({main_ram_name}) + LENGTH({main_ram_name}) - __stack_size :
    {{
        PROVIDE( _heap_end = . ); 
        . = __stack_size;  
        PROVIDE( _sp = . ); 
    }} >{main_ram_name} AT>{main_ram_name}
}}

/* input sections */
GROUP(libgcc.a libc.a libm.a libnosys.a)"""
    return content
