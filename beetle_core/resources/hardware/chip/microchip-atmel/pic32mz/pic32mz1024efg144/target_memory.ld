/***********************************************************************
 *
 * target.memory
 *
 * System dependent part of the primary loader linker script. Maps the
 * output sections to the memory regions available on the system, and
 * is included from the linker script bootROM.ld
 *
 ************************************************************************/

/*
 * All origins are virtual addresses in kseg0 (cached) region.
 * Primary loader runs uncached till I$ is initialized.
 *
 * Reserve top of the SRAM for the status and data sections + stack:
 *
  * ----------
 * | STATUS |
 * ----------
 * |  DATA  |
 * ----------
 * | STACK  |
 * ----------
 * | unused |
 * ----------
 */

/*
  20201210: The full AHB_SRAM allocates to rodata&data&bss&stack.
  For CPU test and peripherals test.
*/

/*
    ROM:     0xBFC00000 ~ 0xBFC3FFFF , 64K   , 0x10000
    AHBRAM:  0x82A00000 ~ 0x82A1FFFF , 128K  , 0x20000
    AXIRAM1: 0x84000000 ~ 0x84200000 , 2048K , 0x200000
    DPSRAM:  0xBFC80000 ~ 0xBFC8FFFF , 64K   , 0x10000
*/

MEMORY
{
    ROM (RX):    ORIGIN = 0xbfc00000, LENGTH = 64k
    TEXT (RX):   ORIGIN = 0x9d000000, LENGTH = 64k
    DPSRAM (RW): ORIGIN = 0xA0060000, LENGTH = 64k

    /* put status in the uncached region */
    STATUS (RW): ORIGIN = 0xA007FFFC, LENGTH = 4

    /* .. followed by data and stack, 4KB reserved */
    DATA (W!X):   ORIGIN = 0x8007c000, LENGTH = 16k
    STACK (RW):   ORIGIN = 0x80040000, LENGTH = 16k
    AXIRAM1 (RW): ORIGIN = 0x80000000, LENGTH = 256k
}

/* put .text and .rodata in ROM, all other sections in RAM */
REGION_ALIAS("REGION_TEXT", TEXT);
REGION_ALIAS("REGION_ROM", ROM);
REGION_ALIAS("REGION_AHBRAM", AXIRAM1);
REGION_ALIAS("REGION_STATUS", STATUS);
REGION_ALIAS("REGION_STACK", STACK);
REGION_ALIAS("REGION_DATA", DATA)
REGION_ALIAS("REGION_HEAP", DPSRAM);
