/***********************************************************************
 *
 *  link.ld
 *
 *  Linker script for startup code for simulator and M14Kc
 *
 * ######################################################################

Copyright (c) 2007-2018, MIPS Tech, LLC and/or its affiliated group companies or licensors

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list
of conditions and the following disclaimer in the documentation and/or other materials
provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be
used to endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

INCLUDE target_memory.ld

OUTPUT_ARCH(mips)

/**** Start point ****/
ENTRY(__reset_vector)

PROVIDE(_ebase_address = ORIGIN(REGION_TEXT) + 0xf000);

SECTIONS
{
    /* Boot ROM address */
    _boot_rom = ORIGIN(REGION_ROM);

    /************************************/
    /* Text section (code)              */
    /************************************/
    .text_init :
    AT( _boot_rom ) /* (Load address is start of Boot ROM.) */
    {
        _ftext_rom = ABSOLUTE(.);  /* Start of init code. */
        *start.*o (.text)           /* put reset entry point at the beggining of the .text section */
        *init_cp0.*o (.text)
        *init_caches.*o (.text)
        *init_gpr.*o (.text)
        *init_gp_sp.*o (.text)
        *init_isr.*o (.text)
        *init_tlb.*o (.text)
        *soc_specific.*o (.text)
        *gic_isr.*o (.text)
        *boot_error.*o (.text)
        . = ALIGN(8);
        _etext_rom = ABSOLUTE(.); /* End of init code. */
    } > REGION_ROM

    /**** "C" Code and read-only data ****/

    /* text offset in AHB_SRAM */
    _ftext_ram = ORIGIN(REGION_TEXT);

    .text_ram :             /* Need to copy code and read-only data to ram... */
    AT( _ftext_ram )        /* (Load address is after init code in Monitor Flash.) */
    {
        _ftext_ram = ABSOLUTE(.) ;    /* Start of code and read-only data */
        *(.text)*(.text.*)
        . = ALIGN(8);
        _etext_ram = ABSOLUTE(.);     /* End of code and read-only data */
    } > REGION_TEXT

    /************************************/
    /* read-only data section           */
    /************************************/
    _frodata_ram = .;
    .rodata :
    AT( _frodata_ram )        /* (Load address is after "C" code in Boot ROM.) */
    {
        rodata_start = ABSOLUTE(.);
        *(.rodata)
        *(.rodata.*)
        rodata_end = ABSOLUTE(.);
    } > REGION_TEXT

    .text_epc _ebase_address + 0x180:
    {
        KEEP(*(.text_epc))
    }

    .text_isr _ebase_address + 0x200:
    {
        KEEP(*(.text_isr))
    }
    /**** Initialised data ****/
    /* data offset in AHB_SRAM */
    _begin_data = .;
    _fdata_ram = .;

    /************************************/
    /* data section                     */
    /************************************/
    .data : ALIGN(16)
    {

        _fdata_ram = ABSOLUTE(.);    /* Start of initialised data */

        *(.data)
        *(.data.*)
        . = ALIGN(8);

    } > REGION_DATA AT> REGION_TEXT

    _gp = ALIGN(16) + 0x7ff0;    /* Base of small data */

    .sdata ALIGN(4) :
    {
        *(.lit8)
        *(.lit4)
        *(.sdata)
        *(.sdata.*)
        . = ALIGN(8);
    } > REGION_DATA AT> REGION_TEXT

    _edata_ram = ABSOLUTE(.);    /* End of initialised data */

    /**** Uninitialised data ****/

    _fbss = .;                   /* Start of uninitialised data */

    .sbss :
    {
        *(.sbss*)
        *(.scommon)
    } > REGION_DATA

    .bss :
    {
        *(.bss*)
        *(COMMON)
    } > REGION_DATA

    _end = .;        /* End of uninitialised data */

    .gptab.sdata : { *(.gptab.data) *(.gptab.sdata) }
    .gptab.sbss  : { *(.gptab.bss)  *(.gptab.sbss) }

    /DISCARD/ :
    {
        *(.reginfo)
        *(.MIPS.abiflags)
    }

    _freemem = .;

    /************************************/
    /* Stack symbols                    */
    /************************************/
    /* put stack pointer at the top of a stack region (stack is growing down) */
    _stack      = ORIGIN(REGION_STACK) + LENGTH(REGION_STACK);
    _stack_size = LENGTH(REGION_STACK);

    /************************************/
    /* Boot status.                     */
    /************************************/
    /* This is where the boot ROM will write error code if anything goes wrong */
    .boot_status (NOLOAD) :
    {
        _boot_status = ABSOLUTE(.);
        *(.boot_status)
    } > REGION_STATUS

    /************************************/
    /* HEAP.                            */
    /************************************/
    _malloc      = ORIGIN(REGION_HEAP);
    _malloc_size = LENGTH(REGION_HEAP);
}
