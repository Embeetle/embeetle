/*
 * cmsdk_cm0_user_flash.ld
 * Linker script for user application executing from external flash
 *
 * Copyright (C) Atmosic 2017-2021
 */

INCLUDE "lib-nosys.ld"
INCLUDE "memory.ld"

ENTRY(_user_entry)

SECTIONS
{
    .text :
    {
        __text_start__ = .;
        KEEP(*(.user_entry))
        *(.text*)
        KEEP(*(.KEEP.text*))

        KEEP(*(.init))
        KEEP(*(.fini))

        /* .ctors */
        *crtbegin.o(.ctors)
        *crtbegin?.o(.ctors)
        *(EXCLUDE_FILE(*crtend?.o *crtend.o) .ctors)
        *(SORT(.ctors.*))
        *(.ctors)

        /* .dtors */
         *crtbegin.o(.dtors)
         *crtbegin?.o(.dtors)
         *(EXCLUDE_FILE(*crtend?.o *crtend.o) .dtors)
         *(SORT(.dtors.*))
         *(.dtors)

        *(.rodata*)

        KEEP(*(.eh_frame*))
    } > UFLASH

    . = ALIGN(4);
    __atm_module_start = .;
    .ATM.module :
    {
        KEEP(*(SORT(.atm_module.*)))
    } > UFLASH
    __atm_module_end = .;

    . = ALIGN(4);
    __at_cmd_start = .;
    .ATCOMMAND :
    {
        KEEP(*(SORT(.at_cmd.*)))
    } > UFLASH
    __at_cmd_end = .;

    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } > UFLASH

    __exidx_start = .;
    .ARM.exidx :
    {
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
    } > UFLASH
    __exidx_end = .;

    . = ALIGN(4);
    __etext = .;

    .data : AT (__etext)
    {
        __data_start__ = .;

        *(vtable)
        *(.data*)

        . = ALIGN(4);
        /* preinit data */
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP(*(.preinit_array))
        PROVIDE_HIDDEN (__preinit_array_end = .);

        . = ALIGN(4);
        /* init data */
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array))
        PROVIDE_HIDDEN (__init_array_end = .);

        . = ALIGN(4);
        /* finit data */
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array))
        PROVIDE_HIDDEN (__fini_array_end = .);

        KEEP(*(.jcr*))

        . = ALIGN(4);
        /* All data end */
        __data_end__ = .;
    } > URAM

    /* Check if UFLASH overflowed */
    ASSERT((__etext - ORIGIN(UFLASH)) + (__data_end__ - __data_start__) < LENGTH(UFLASH), "section .data does not fit in region UFLASH")

    __NVDS_Flash = ORIGIN(NVDS);
    __NVDS_FlashEnd = ORIGIN(NVDS) + LENGTH(NVDS);

    __User_Flash = ORIGIN(USER);
    __User_FlashEnd = ORIGIN(USER) + LENGTH(USER);

    .bss :
    {
        . = ALIGN(4);
        __bss_start__ = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end__ = .;
    } > URAM

    .uninit (NOLOAD) :
    {
        . = ALIGN(4);
        *(.uninit*)
        . = ALIGN(4);
    } > URAM
}
