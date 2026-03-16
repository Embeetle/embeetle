/*
 *-----------------------------------------------------------------------------
 * The confidential and proprietary information contained in this file may
 * only be used by a person authorised under and to the extent permitted
 * by a subsisting licensing agreement from ARM Limited.
 *
 *            (C) COPYRIGHT 2010-2013 ARM Limited.
 *                ALL RIGHTS RESERVED
 *
 * This entire notice must be reproduced on all copies of this file
 * and copies of this file may only be made by a person if such person is
 * permitted to do so under the terms of a subsisting license agreement
 * from ARM Limited.
 *
 *      SVN Information
 *
 *      Checked In          : $Date: $
 *
 *      Revision            : $Revision: $
 *
 *      Release Information : Cortex-M System Design Kit-r1p0-00rel0
 *-----------------------------------------------------------------------------
 */
/* Linker script to configure memory regions.
 * Need modifying for a specific board.
 *   FLASH.ORIGIN: starting address of flash
 *   FLASH.LENGTH: length of flash
 *   RAM.ORIGIN: starting address of RAM bank 0
 *   RAM.LENGTH: length of RAM bank 0
 *
 * 0x10000000  ┌────────────────────┐
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░UFLASH░░░░░░░░│ UFLASH_LEN
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░░░░░░░░░░░░░│
 * 0x10000000  │░░░░░░░░░░░░░░░░░░░░│
 * +UFLASH_LEN ├────────────────────┤
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░USER░░░░░░░░│ USER_LEN
 * 0x10000000  │░░░░░░░░░░░░░░░░░░░░│
 * +UFLASH_LEN ├────────────────────┤
 * +USER_LEN   │░░░░░░░░░░░░░░░░░░░░│
 *             │░░░░░░░░NVDS░░░░░░░░│ NVDS_LEN
 * 0x10000000  │░░░░░░░░░░░░░░░░░░░░│
 * +UFLASH_LEN ├────────────────────┤
 * +USER_LEN   │░░░░░░░░░░░░░░░░░░░░│
 * +NVDS_LEN   │░░░░░░░░MPR░░░░░░░░░│ MPR_LEN
 *             │░░░░░░░░░░░░░░░░░░░░│
 *             └────────────────────┘
 *
 */

HIDDEN(USER_LEN = DEFINED(USER_SIZE) ? USER_SIZE : 0);
HIDDEN(NVDS_LEN = DEFINED(NVDS_SIZE) ? NVDS_SIZE : 0x8000);
HIDDEN(MPR_LEN = DEFINED(MPR_SIZE) ? MPR_SIZE : 0);
HIDDEN(UFLASH_LEN = (DEFINED(FLASH_SIZE) ? FLASH_SIZE : 0x80000) - NVDS_LEN - USER_LEN - MPR_LEN);
HIDDEN(URAM_ORG = DEFINED(URAM_START) ? URAM_START : 0x20014000);
HIDDEN(URAM_LEN = DEFINED(URAM_SIZE) ? URAM_SIZE : 0x4000); /* 16K */

MEMORY
{
    FLASH (rx)  : ORIGIN =        0x0, LENGTH = 0x40000 /* 256K */
    UFLASH (rx) : ORIGIN = 0x10000000, LENGTH = UFLASH_LEN
    USER (rwx)  : ORIGIN = 0x10000000 + UFLASH_LEN, LENGTH = USER_LEN
    NVDS (rwx)  : ORIGIN = 0x10000000 + UFLASH_LEN + USER_LEN, LENGTH = NVDS_LEN
    MPR (rwx)   : ORIGIN = 0x10000000 + UFLASH_LEN + USER_LEN + NVDS_LEN, LENGTH = MPR_LEN
    RAM (rwx)   : ORIGIN = 0x20000000, LENGTH = 0x14000 /*  80K */
    URAM (rwx)  : ORIGIN = URAM_ORG, LENGTH = URAM_LEN
}

