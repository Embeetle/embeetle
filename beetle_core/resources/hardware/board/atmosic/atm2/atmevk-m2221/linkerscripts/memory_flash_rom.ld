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
 */

HIDDEN(USER_LEN = DEFINED(USER_SIZE) ? USER_SIZE : 0);
HIDDEN(NVDS_LEN = DEFINED(NVDS_SIZE) ? NVDS_SIZE : 0x2000);
HIDDEN(FLASH_LEN = (DEFINED(FLASH_SIZE) ? FLASH_SIZE : 0x80000) - NVDS_LEN - USER_LEN);

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = FLASH_LEN
    USER (rwx)  : ORIGIN = 0x0000000 + FLASH_LEN, LENGTH = USER_LEN
    NVDS (rwx)  : ORIGIN =  FLASH_LEN + USER_LEN, LENGTH = NVDS_LEN
    RAM (rwx)   : ORIGIN = 0x20000000, LENGTH = 0x18000 /*  96K */
}
