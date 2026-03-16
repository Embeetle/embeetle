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

/* Architecture and Entry Point */

OUTPUT_ARCH( "riscv" )
ENTRY( _start )

/* Define memory regions. */
MEMORY
{{ 
{memory}
}}


SECTIONS
{{
    __stack_size = DEFINED(__stack_size) ? __stack_size : 2K;

    .init :
    {{
        KEEP (*(SORT_NONE(.init)))
    }} >{main_flash_name} AT>{main_flash_name}

    .ilalign :
    {{
        . = ALIGN(4);
        PROVIDE( _ilm_lma = . );
    }} >{main_flash_name} AT>{main_flash_name}

    .ialign :
    {{
        PROVIDE( _ilm = . );
    }} >{main_flash_name} AT>{main_flash_name}

    /* The program code and other data goes into {main_flash_name} */
    .text :
    {{
        *(.rodata .rodata.*)  
        *(.text.unlikely .text.unlikely.*)
        *(.text.startup .text.startup.*)
        *(.text .text.*)
        *(.gnu.linkonce.t.*)
    }} >{main_flash_name} AT>{main_flash_name}

    .fini :
    {{
        KEEP (*(SORT_NONE(.fini)))
    }} >{main_flash_name} AT>{main_flash_name}

    . = ALIGN(4);
    PROVIDE (__etext = .);
    PROVIDE (_etext = .); /*0x80022c8*/
    PROVIDE (etext = .);  /*0x80022c8*/
    PROVIDE( _eilm = . );

    .preinit_array :
    {{
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP (*(.preinit_array))
        PROVIDE_HIDDEN (__preinit_array_end = .);
    }} >{main_flash_name} AT>{main_flash_name}

    .init_array :
    {{
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP (*(SORT_BY_INIT_PRIORITY(.init_array.*) SORT_BY_INIT_PRIORITY(.ctors.*)))
        KEEP (*(.init_array EXCLUDE_FILE (*crtbegin.o *crtbegin?.o *crtend.o *crtend?.o ) .ctors))
        PROVIDE_HIDDEN (__init_array_end = .);
    }} >{main_flash_name} AT>{main_flash_name}

    .fini_array     :
    {{
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP (*(SORT_BY_INIT_PRIORITY(.fini_array.*) SORT_BY_INIT_PRIORITY(.dtors.*)))
        KEEP (*(.fini_array EXCLUDE_FILE (*crtbegin.o *crtbegin?.o *crtend.o *crtend?.o ) .dtors))
        PROVIDE_HIDDEN (__fini_array_end = .);
    }} >{main_flash_name} AT>{main_flash_name}

    /* Constructors */
    .ctors :
    {{
        /* gcc uses crtbegin.o to find the start of
           the constructors, so we make sure it is
           first.  Because this is a wildcard, it
           doesn't matter if the user does not
           actually link against crtbegin.o; the
           linker won't look for a file to match a
           wildcard.  The wildcard also means that it
           doesn't matter which directory crtbegin.o
           is in.  */
        KEEP (*crtbegin.o(.ctors))
        KEEP (*crtbegin?.o(.ctors))
        /* We don't want to include the .ctor section from
           the crtend.o file until after the sorted ctors.
           The .ctor section from the crtend file contains the
           end of ctors marker and it must be last */
        KEEP (*(EXCLUDE_FILE (*crtend.o *crtend?.o ) .ctors))
        KEEP (*(SORT(.ctors.*)))
        KEEP (*(.ctors))
    }} >{main_flash_name} AT>{main_flash_name} 

    /* Destructors */
    .dtors :
    {{
        KEEP (*crtbegin.o(.dtors))
        KEEP (*crtbegin?.o(.dtors))
        KEEP (*(EXCLUDE_FILE (*crtend.o *crtend?.o ) .dtors))
        KEEP (*(SORT(.dtors.*)))
        KEEP (*(.dtors))
    }} >{main_flash_name} AT>{main_flash_name}

    . = ALIGN(4);
    PROVIDE( _eilm = . );

    .lalign :
    {{
        . = ALIGN(4);
        PROVIDE( _data_lma = . );
    }} >{main_flash_name} AT>{main_flash_name}

    .dalign :
    {{
        . = ALIGN(4);
        PROVIDE( _data = . );
    }} >{main_ram_name} AT>{main_flash_name}
  
    /* Initialized data sections go into {main_ram_name}, load LMA copy after code */
    .data :
    {{
        *(.rdata) 
        
        *(.gnu.linkonce.r.*)
        *(.data .data.*)
        *(.gnu.linkonce.d.*)
        . = ALIGN(8);
        PROVIDE( __global_pointer$ = . + 0x800); 
        *(.sdata .sdata.*)
        *(.gnu.linkonce.s.*)
        . = ALIGN(8);
        *(.srodata.cst16)
        *(.srodata.cst8)
        *(.srodata.cst4)
        *(.srodata.cst2)
        *(.srodata .srodata.*)
    }} >{main_ram_name} AT>{main_flash_name}

    . = ALIGN(4);
    PROVIDE( _edata = . );
    PROVIDE( edata = . );

    /* Uninitialized data section */
    PROVIDE( _fbss = . ); /*0X200052A0  0X200002A0*/
    PROVIDE( __bss_start = . );
    .bss :
    {{
        *(.sbss*)
        *(.gnu.linkonce.sb.*)
        *(.bss .bss.*)
        *(.gnu.linkonce.b.*)
        *(COMMON)
        . = ALIGN(4);
    }} >{main_ram_name} AT>{main_ram_name}
    
    . = ALIGN(8);
    PROVIDE( _end = . ); /*0X2000,0340*/
    PROVIDE( end = . );

    /* Stack section */
    .stack ORIGIN({main_ram_name}) + LENGTH({main_ram_name}) - __stack_size :
    {{
        PROVIDE( _heap_end = . ); 
        . = __stack_size;  
        PROVIDE( _sp = . ); 
    }} >{main_ram_name} AT>{main_ram_name}
}}"""
    return content
