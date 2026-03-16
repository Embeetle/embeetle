/*
 * Linker script for PIC24FJ64GU205
 * (c) Copyright 2013 Microchip Technology, Inc
 * Part support version 1.60.B(29-Sep-2020)
 *
 * This software is developed by Microchip Technology Inc. and its
 * subsidiaries ("Microchip").
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 * 1.      Redistributions of source code must retain the above copyright
 *         notice, this list of conditions and the following disclaimer.
 * 2.      Redistributions in binary form must reproduce the above
 *         copyright notice, this list of conditions and the following
 *         disclaimer in the documentation and/or other materials provided
 *         with the distribution. Publication is not required when
 *         this file is used in an embedded application.
 * 3.      Microchip's name may not be used to endorse or promote products
 *         derived from this software without specific prior written
 *         permission.
 *
 * THIS SOFTWARE IS PROVIDED BY MICROCHIP "AS IS" AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR PURPOSE ARE DISCLAIMED. IN NO EVENT
 * SHALL MICROCHIP BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING BUT NOT LIMITED TO
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWSOEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 */


OUTPUT_ARCH("24FJ64GU205")
#if __XC16_VERSION__ > 1027
CRT0_STARTUP(crt0_extended24.o)
CRT1_STARTUP(crt1_extended24.o)
#else
CRT0_STARTUP(crt0_extended.o)
CRT1_STARTUP(crt1_extended.o)
#endif
#if __XC16_VERSION__ > 1027
/*
 * Define how to startup, by default we initialize
 * everything as normal; change to crt_start_mode to
 * preserve preserved data on a restart
 *
 * Or define your own __crt_start_mode fucntion
 */
CRT_STARTMODE(crt_start_mode_normal)
#endif

OPTIONAL(-lpPIC24Fxxx)
OPTIONAL(-lfx)

/*
** Memory Regions
*/
MEMORY
{
  data  (a!xr)   : ORIGIN = 0x800,         LENGTH = 0x2000
  reset          : ORIGIN = 0x0,           LENGTH = 0x4
  ivt            : ORIGIN = 0x4,           LENGTH = 0xFC
  program (xr)   : ORIGIN = 0x100,         LENGTH = 0xAE00
  FSEC           : ORIGIN = 0xAF00,        LENGTH = 0x2
  FBSLIM         : ORIGIN = 0xAF10,        LENGTH = 0x2
  FSIGN          : ORIGIN = 0xAF14,        LENGTH = 0x2
  FOSCSEL        : ORIGIN = 0xAF18,        LENGTH = 0x2
  FOSC           : ORIGIN = 0xAF1C,        LENGTH = 0x2
  FWDT           : ORIGIN = 0xAF20,        LENGTH = 0x2
  FPOR           : ORIGIN = 0xAF24,        LENGTH = 0x2
  FICD           : ORIGIN = 0xAF28,        LENGTH = 0x2
  FDMTIVTL       : ORIGIN = 0xAF2C,        LENGTH = 0x2
  FDMTIVTH       : ORIGIN = 0xAF30,        LENGTH = 0x2
  FDMTCNTL       : ORIGIN = 0xAF34,        LENGTH = 0x2
  FDMTCNTH       : ORIGIN = 0xAF38,        LENGTH = 0x2
  FMDT           : ORIGIN = 0xAF3C,        LENGTH = 0x2
  FDEVOPT1       : ORIGIN = 0xAF40,        LENGTH = 0x2
}


/*
 * TPED support
 */

_iwri1 = 0x801024;
_iwri2 = 0x801028;

__FSEC = 0xAF00;
__FBSLIM = 0xAF10;
__FSIGN = 0xAF14;
__FOSCSEL = 0xAF18;
__FOSC = 0xAF1C;
__FWDT = 0xAF20;
__FPOR = 0xAF24;
__FICD = 0xAF28;
__FDMTIVTL = 0xAF2C;
__FDMTIVTH = 0xAF30;
__FDMTCNTL = 0xAF34;
__FDMTCNTH = 0xAF38;
__FMDT = 0xAF3C;
__FDEVOPT1 = 0xAF40;
__NO_HANDLES = 1;          /* Suppress handles on this device  */
__CODE_BASE = 0x100;
__CODE_LENGTH = 0xAE00;
__IVT_BASE  = 0x4;

__DATA_BASE = 0x800;
__DATA_LENGTH = 0x2000;


/*
** ==================== Section Map ======================
*/
SECTIONS
{
  /*
  ** ========== Program Memory ==========
  */


#if !defined(__CORESIDENT) || defined(__DEFINE_RESET)
  /*
  ** Reset Instruction
  */
  .reset :
  {
        SHORT(ABSOLUTE(__reset));
        SHORT(0x04);
        SHORT((ABSOLUTE(__reset) >> 16) & 0x7F);
        SHORT(0);
  } >reset
#endif


  /*
  ** Interrupt Vector Tables
  **
  ** The primary and alternate tables are loaded
  ** here, between sections .reset and .text.
  ** Vector table source code appears below.
  */


  /*
  ** User Code and Library Code
  **
  ** This section must not be assigned to __CODE_BASE,
  ** because CodeGuard(tm) sections may be located there.
  **
  ** Note that input sections *(.text) are not mapped here.
  ** The best-fit allocator locates them, so that .text
  ** may flow around PSV sections as needed.
  **
  ** Define __USE_BFA to force the following sections to
  ** to also be linked by the best-fit allocator.
  */
#if !defined(__USE_BFA)
  .text :
  {
        *(.init);
        *(.user_init);
        KEEP (*(.handle));
        KEEP (*(.isr*));
        *(.libc) *(.libm) *(.libdsp);  /* keep together in this order */
        *(.lib*);
  } >program
#endif


  /*
  ** User-Defined Section in Program Memory
  **
  ** note: can specify an address using
  **       the following syntax:
  **
  **       usercode 0x1234 :
  **         {
  **           *(usercode);
  **         } >program
  */
  usercode :
  {
        *(usercode);
  } >program


  /*
  ** User-Defined Constants in Program Memory
  **
  ** For PSV type sections, the Load Memory Address (LMA)
  ** should be specified as follows:
  **
  **       userconst : AT(0x1234)
  **         {
  **           *(userconst);
  **         } >program
  **
  ** Note that mapping PSV sections in linker scripts
  ** is not generally recommended.
  **
  ** Because of page alignment restrictions, memory is
  ** often used more efficiently when PSV sections
  ** do not appear in the linker script.
  **
  ** For more information on memory allocation,
  ** please refer to chapter 10, 'Linker Processing'
  ** in the Assembler, Linker manual (DS51317).
  */


  /*
  ** Configuration Words
  */
  __FSEC :
  { KEEP (*(__FSEC.sec*))    } >FSEC
  __FBSLIM :
  { KEEP (*(__FBSLIM.sec*))    } >FBSLIM
  __FSIGN :
  { KEEP (*(__FSIGN.sec*))    } >FSIGN
  __FOSCSEL :
  { KEEP (*(__FOSCSEL.sec*))    } >FOSCSEL
  __FOSC :
  { KEEP (*(__FOSC.sec*))    } >FOSC
  __FWDT :
  { KEEP (*(__FWDT.sec*))    } >FWDT
  __FPOR :
  { KEEP (*(__FPOR.sec*))    } >FPOR
  __FICD :
  { KEEP (*(__FICD.sec*))    } >FICD
  __FDMTIVTL :
  { KEEP (*(__FDMTIVTL.sec*))    } >FDMTIVTL
  __FDMTIVTH :
  { KEEP (*(__FDMTIVTH.sec*))    } >FDMTIVTH
  __FDMTCNTL :
  { KEEP (*(__FDMTCNTL.sec*))    } >FDMTCNTL
  __FDMTCNTH :
  { KEEP (*(__FDMTCNTH.sec*))    } >FDMTCNTH
  __FMDT :
  { KEEP (*(__FMDT.sec*))    } >FMDT
  __FDEVOPT1 :
  { KEEP (*(__FDEVOPT1.sec*))    } >FDEVOPT1






  /*
  ** =========== Data Memory ===========
  */


  /*
  ** ICD Debug Exec
  **
  ** This section provides optional storage for
  ** the ICD2 debugger. Define a global symbol
  ** named __ICD2RAM to enable ICD2. This section
  ** must be loaded at data address 0x800.
  */
  .icd __DATA_BASE (NOLOAD):
  {
    . += (DEFINED (__ICD2RAM) ? 0x50 : 0 );
  } > data


  /*
  ** Other sections in data memory are not explicitly mapped.
  ** Instead they are allocated according to their section
  ** attributes, which is most efficient.
  **
  ** If a specific arrangement of sections is required
  ** (other than what can be achieved using attributes)
  ** additional sections may be defined here. See chapter
  ** 10.5 in the MPLAB ASM30/LINK30 User's Guide (DS51317)
  ** for more information.
  */


  /*
  ** ========== Debug Info ==============
  */

  .comment        0 : { *(.comment) }

  /*
  ** DWARF-2
  */
  .debug_info     0 : { *(.debug_info) *(.gnu.linkonce.wi.*) }
  .debug_abbrev   0 : { *(.debug_abbrev) }
  .debug_line     0 : { *(.debug_line) }
  .debug_frame    0 : { *(.debug_frame) }
  .debug_str      0 : { *(.debug_str) }
  .debug_loc      0 : { *(.debug_loc) }
  .debug_macinfo  0 : { *(.debug_macinfo) }
  .debug_pubnames 0 : { *(.debug_pubnames) }
  .debug_ranges   0 : { *(.debug_ranges) }
  .debug_aranges  0 : { *(.debug_aranges) }

} /* SECTIONS */

/*
** ================= End of Section Map ================
*/

#if __XC16_VERSION < 1026
/*
** These definitions are not required for XC16 versions
** later than XC16 v1.25 as the linker defines the addresses.
**
*/
/*
** Section Map for Interrupt Vector Tables
*/
SECTIONS
{

/*
** Interrupt Vector Table
*/
.ivt __IVT_BASE :
  {
    LONG( DEFINED(__OscillatorFail)    ? ABSOLUTE(__OscillatorFail)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__AddressError)    ? ABSOLUTE(__AddressError)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__NVMError)    ? ABSOLUTE(__NVMError)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__StackError)    ? ABSOLUTE(__StackError)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__MathError)    ? ABSOLUTE(__MathError)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__ReservedTrap5)    ? ABSOLUTE(__ReservedTrap5)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__GeneralError)    ? ABSOLUTE(__GeneralError)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__ReservedTrap7)    ? ABSOLUTE(__ReservedTrap7)    :
         ABSOLUTE(__DefaultInterrupt));

    LONG( DEFINED(__INT0Interrupt)    ? ABSOLUTE(__INT0Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCT1Interrupt)    ? ABSOLUTE(__CCT1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCT2Interrupt)    ? ABSOLUTE(__CCT2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__T1Interrupt)    ? ABSOLUTE(__T1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__DMA0Interrupt)    ? ABSOLUTE(__DMA0Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt5)    ? ABSOLUTE(__Interrupt5)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt6)    ? ABSOLUTE(__Interrupt6)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__T2Interrupt)    ? ABSOLUTE(__T2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__T3Interrupt)    ? ABSOLUTE(__T3Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI1Interrupt)    ? ABSOLUTE(__SPI1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI1TXInterrupt)    ? ABSOLUTE(__SPI1TXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U1RXInterrupt)    ? ABSOLUTE(__U1RXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U1TXInterrupt)    ? ABSOLUTE(__U1TXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__ADC1Interrupt)    ? ABSOLUTE(__ADC1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__DMA1Interrupt)    ? ABSOLUTE(__DMA1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__NVMInterrupt)    ? ABSOLUTE(__NVMInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SI2C1Interrupt)    ? ABSOLUTE(__SI2C1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__MI2C1Interrupt)    ? ABSOLUTE(__MI2C1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CompInterrupt)    ? ABSOLUTE(__CompInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__IOCInterrupt)    ? ABSOLUTE(__IOCInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__INT1Interrupt)    ? ABSOLUTE(__INT1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt21)    ? ABSOLUTE(__Interrupt21)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCP5Interrupt)    ? ABSOLUTE(__CCP5Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt23)    ? ABSOLUTE(__Interrupt23)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt24)    ? ABSOLUTE(__Interrupt24)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt25)    ? ABSOLUTE(__Interrupt25)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt26)    ? ABSOLUTE(__Interrupt26)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt27)    ? ABSOLUTE(__Interrupt27)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt28)    ? ABSOLUTE(__Interrupt28)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__INT2Interrupt)    ? ABSOLUTE(__INT2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U2RXInterrupt)    ? ABSOLUTE(__U2RXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U2TXInterrupt)    ? ABSOLUTE(__U2TXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI2Interrupt)    ? ABSOLUTE(__SPI2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI2TXInterrupt)    ? ABSOLUTE(__SPI2TXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt34)    ? ABSOLUTE(__Interrupt34)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt35)    ? ABSOLUTE(__Interrupt35)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt36)    ? ABSOLUTE(__Interrupt36)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt37)    ? ABSOLUTE(__Interrupt37)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt38)    ? ABSOLUTE(__Interrupt38)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt39)    ? ABSOLUTE(__Interrupt39)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt40)    ? ABSOLUTE(__Interrupt40)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt41)    ? ABSOLUTE(__Interrupt41)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt42)    ? ABSOLUTE(__Interrupt42)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCT3Interrupt)    ? ABSOLUTE(__CCT3Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCT4Interrupt)    ? ABSOLUTE(__CCT4Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt45)    ? ABSOLUTE(__Interrupt45)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt46)    ? ABSOLUTE(__Interrupt46)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCT5Interrupt)    ? ABSOLUTE(__CCT5Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt48)    ? ABSOLUTE(__Interrupt48)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SI2C2Interrupt)    ? ABSOLUTE(__SI2C2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__MI2C2Interrupt)    ? ABSOLUTE(__MI2C2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt51)    ? ABSOLUTE(__Interrupt51)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt52)    ? ABSOLUTE(__Interrupt52)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__INT3Interrupt)    ? ABSOLUTE(__INT3Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__INT4Interrupt)    ? ABSOLUTE(__INT4Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt55)    ? ABSOLUTE(__Interrupt55)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt56)    ? ABSOLUTE(__Interrupt56)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt57)    ? ABSOLUTE(__Interrupt57)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI1RXInterrupt)    ? ABSOLUTE(__SPI1RXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__SPI2RXInterrupt)    ? ABSOLUTE(__SPI2RXInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt60)    ? ABSOLUTE(__Interrupt60)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt61)    ? ABSOLUTE(__Interrupt61)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__RTCCInterrupt)    ? ABSOLUTE(__RTCCInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCP1Interrupt)    ? ABSOLUTE(__CCP1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCP2Interrupt)    ? ABSOLUTE(__CCP2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U1ErrInterrupt)    ? ABSOLUTE(__U1ErrInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__U2ErrInterrupt)    ? ABSOLUTE(__U2ErrInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CRCInterrupt)    ? ABSOLUTE(__CRCInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt68)    ? ABSOLUTE(__Interrupt68)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt69)    ? ABSOLUTE(__Interrupt69)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt70)    ? ABSOLUTE(__Interrupt70)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt71)    ? ABSOLUTE(__Interrupt71)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__HLVDInterrupt)    ? ABSOLUTE(__HLVDInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt73)    ? ABSOLUTE(__Interrupt73)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt74)    ? ABSOLUTE(__Interrupt74)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt75)    ? ABSOLUTE(__Interrupt75)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt76)    ? ABSOLUTE(__Interrupt76)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt77)    ? ABSOLUTE(__Interrupt77)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt78)    ? ABSOLUTE(__Interrupt78)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt79)    ? ABSOLUTE(__Interrupt79)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt80)    ? ABSOLUTE(__Interrupt80)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt81)    ? ABSOLUTE(__Interrupt81)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt82)    ? ABSOLUTE(__Interrupt82)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt83)    ? ABSOLUTE(__Interrupt83)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__I2C1BCInterrupt)    ? ABSOLUTE(__I2C1BCInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__I2C2BCInterrupt)    ? ABSOLUTE(__I2C2BCInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__USB1Interrupt)    ? ABSOLUTE(__USB1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt87)    ? ABSOLUTE(__Interrupt87)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt88)    ? ABSOLUTE(__Interrupt88)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt89)    ? ABSOLUTE(__Interrupt89)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt90)    ? ABSOLUTE(__Interrupt90)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt91)    ? ABSOLUTE(__Interrupt91)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt92)    ? ABSOLUTE(__Interrupt92)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt93)    ? ABSOLUTE(__Interrupt93)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCP3Interrupt)    ? ABSOLUTE(__CCP3Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CCP4Interrupt)    ? ABSOLUTE(__CCP4Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CLC1Interrupt)    ? ABSOLUTE(__CLC1Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CLC2Interrupt)    ? ABSOLUTE(__CLC2Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CLC3Interrupt)    ? ABSOLUTE(__CLC3Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__CLC4Interrupt)    ? ABSOLUTE(__CLC4Interrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt100)    ? ABSOLUTE(__Interrupt100)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt101)    ? ABSOLUTE(__Interrupt101)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt102)    ? ABSOLUTE(__Interrupt102)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt103)    ? ABSOLUTE(__Interrupt103)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt104)    ? ABSOLUTE(__Interrupt104)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt105)    ? ABSOLUTE(__Interrupt105)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__FSTInterrupt)    ? ABSOLUTE(__FSTInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt107)    ? ABSOLUTE(__Interrupt107)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__ECCSBEInterrupt)    ? ABSOLUTE(__ECCSBEInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt109)    ? ABSOLUTE(__Interrupt109)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__RTCCTSInterrupt)    ? ABSOLUTE(__RTCCTSInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt111)    ? ABSOLUTE(__Interrupt111)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt112)    ? ABSOLUTE(__Interrupt112)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt113)    ? ABSOLUTE(__Interrupt113)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt114)    ? ABSOLUTE(__Interrupt114)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt115)    ? ABSOLUTE(__Interrupt115)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__Interrupt116)    ? ABSOLUTE(__Interrupt116)    :
         ABSOLUTE(__DefaultInterrupt));
    LONG( DEFINED(__JTAGInterrupt)    ? ABSOLUTE(__JTAGInterrupt)    :
         ABSOLUTE(__DefaultInterrupt));
  } >ivt


/*
** Alternate Interrupt Vector Table
*/
.aivt :
  {
    LONG(0); /* RESERVED */
    LONG(0); /* RESERVED */
    LONG( DEFINED(__AltOscillatorFail)    ? ABSOLUTE(__AltOscillatorFail)    :
         (DEFINED(__OscillatorFail)       ? ABSOLUTE(__OscillatorFail)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltAddressError)    ? ABSOLUTE(__AltAddressError)    :
         (DEFINED(__AddressError)       ? ABSOLUTE(__AddressError)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltNVMError)    ? ABSOLUTE(__AltNVMError)    :
         (DEFINED(__NVMError)       ? ABSOLUTE(__NVMError)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltStackError)    ? ABSOLUTE(__AltStackError)    :
         (DEFINED(__StackError)       ? ABSOLUTE(__StackError)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltMathError)    ? ABSOLUTE(__AltMathError)    :
         (DEFINED(__MathError)       ? ABSOLUTE(__MathError)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltReservedTrap5)    ? ABSOLUTE(__AltReservedTrap5)    :
         (DEFINED(__ReservedTrap5)       ? ABSOLUTE(__ReservedTrap5)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltGeneralError)    ? ABSOLUTE(__AltGeneralError)    :
         (DEFINED(__GeneralError)       ? ABSOLUTE(__GeneralError)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltReservedTrap7)    ? ABSOLUTE(__AltReservedTrap7)    :
         (DEFINED(__ReservedTrap7)       ? ABSOLUTE(__ReservedTrap7)       :
         ABSOLUTE(__DefaultInterrupt)));

    LONG( DEFINED(__AltINT0Interrupt)    ? ABSOLUTE(__AltINT0Interrupt)    :
         (DEFINED(__INT0Interrupt)       ? ABSOLUTE(__INT0Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCT1Interrupt)    ? ABSOLUTE(__AltCCT1Interrupt)    :
         (DEFINED(__CCT1Interrupt)       ? ABSOLUTE(__CCT1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCT2Interrupt)    ? ABSOLUTE(__AltCCT2Interrupt)    :
         (DEFINED(__CCT2Interrupt)       ? ABSOLUTE(__CCT2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltT1Interrupt)    ? ABSOLUTE(__AltT1Interrupt)    :
         (DEFINED(__T1Interrupt)       ? ABSOLUTE(__T1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltDMA0Interrupt)    ? ABSOLUTE(__AltDMA0Interrupt)    :
         (DEFINED(__DMA0Interrupt)       ? ABSOLUTE(__DMA0Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt5)    ? ABSOLUTE(__AltInterrupt5)    :
         (DEFINED(__Interrupt5)       ? ABSOLUTE(__Interrupt5)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt6)    ? ABSOLUTE(__AltInterrupt6)    :
         (DEFINED(__Interrupt6)       ? ABSOLUTE(__Interrupt6)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltT2Interrupt)    ? ABSOLUTE(__AltT2Interrupt)    :
         (DEFINED(__T2Interrupt)       ? ABSOLUTE(__T2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltT3Interrupt)    ? ABSOLUTE(__AltT3Interrupt)    :
         (DEFINED(__T3Interrupt)       ? ABSOLUTE(__T3Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI1Interrupt)    ? ABSOLUTE(__AltSPI1Interrupt)    :
         (DEFINED(__SPI1Interrupt)       ? ABSOLUTE(__SPI1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI1TXInterrupt)    ? ABSOLUTE(__AltSPI1TXInterrupt)    :
         (DEFINED(__SPI1TXInterrupt)       ? ABSOLUTE(__SPI1TXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU1RXInterrupt)    ? ABSOLUTE(__AltU1RXInterrupt)    :
         (DEFINED(__U1RXInterrupt)       ? ABSOLUTE(__U1RXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU1TXInterrupt)    ? ABSOLUTE(__AltU1TXInterrupt)    :
         (DEFINED(__U1TXInterrupt)       ? ABSOLUTE(__U1TXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltADC1Interrupt)    ? ABSOLUTE(__AltADC1Interrupt)    :
         (DEFINED(__ADC1Interrupt)       ? ABSOLUTE(__ADC1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltDMA1Interrupt)    ? ABSOLUTE(__AltDMA1Interrupt)    :
         (DEFINED(__DMA1Interrupt)       ? ABSOLUTE(__DMA1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltNVMInterrupt)    ? ABSOLUTE(__AltNVMInterrupt)    :
         (DEFINED(__NVMInterrupt)       ? ABSOLUTE(__NVMInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSI2C1Interrupt)    ? ABSOLUTE(__AltSI2C1Interrupt)    :
         (DEFINED(__SI2C1Interrupt)       ? ABSOLUTE(__SI2C1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltMI2C1Interrupt)    ? ABSOLUTE(__AltMI2C1Interrupt)    :
         (DEFINED(__MI2C1Interrupt)       ? ABSOLUTE(__MI2C1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCompInterrupt)    ? ABSOLUTE(__AltCompInterrupt)    :
         (DEFINED(__CompInterrupt)       ? ABSOLUTE(__CompInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltIOCInterrupt)    ? ABSOLUTE(__AltIOCInterrupt)    :
         (DEFINED(__IOCInterrupt)       ? ABSOLUTE(__IOCInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltINT1Interrupt)    ? ABSOLUTE(__AltINT1Interrupt)    :
         (DEFINED(__INT1Interrupt)       ? ABSOLUTE(__INT1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt21)    ? ABSOLUTE(__AltInterrupt21)    :
         (DEFINED(__Interrupt21)       ? ABSOLUTE(__Interrupt21)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCP5Interrupt)    ? ABSOLUTE(__AltCCP5Interrupt)    :
         (DEFINED(__CCP5Interrupt)       ? ABSOLUTE(__CCP5Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt23)    ? ABSOLUTE(__AltInterrupt23)    :
         (DEFINED(__Interrupt23)       ? ABSOLUTE(__Interrupt23)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt24)    ? ABSOLUTE(__AltInterrupt24)    :
         (DEFINED(__Interrupt24)       ? ABSOLUTE(__Interrupt24)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt25)    ? ABSOLUTE(__AltInterrupt25)    :
         (DEFINED(__Interrupt25)       ? ABSOLUTE(__Interrupt25)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt26)    ? ABSOLUTE(__AltInterrupt26)    :
         (DEFINED(__Interrupt26)       ? ABSOLUTE(__Interrupt26)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt27)    ? ABSOLUTE(__AltInterrupt27)    :
         (DEFINED(__Interrupt27)       ? ABSOLUTE(__Interrupt27)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt28)    ? ABSOLUTE(__AltInterrupt28)    :
         (DEFINED(__Interrupt28)       ? ABSOLUTE(__Interrupt28)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltINT2Interrupt)    ? ABSOLUTE(__AltINT2Interrupt)    :
         (DEFINED(__INT2Interrupt)       ? ABSOLUTE(__INT2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU2RXInterrupt)    ? ABSOLUTE(__AltU2RXInterrupt)    :
         (DEFINED(__U2RXInterrupt)       ? ABSOLUTE(__U2RXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU2TXInterrupt)    ? ABSOLUTE(__AltU2TXInterrupt)    :
         (DEFINED(__U2TXInterrupt)       ? ABSOLUTE(__U2TXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI2Interrupt)    ? ABSOLUTE(__AltSPI2Interrupt)    :
         (DEFINED(__SPI2Interrupt)       ? ABSOLUTE(__SPI2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI2TXInterrupt)    ? ABSOLUTE(__AltSPI2TXInterrupt)    :
         (DEFINED(__SPI2TXInterrupt)       ? ABSOLUTE(__SPI2TXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt34)    ? ABSOLUTE(__AltInterrupt34)    :
         (DEFINED(__Interrupt34)       ? ABSOLUTE(__Interrupt34)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt35)    ? ABSOLUTE(__AltInterrupt35)    :
         (DEFINED(__Interrupt35)       ? ABSOLUTE(__Interrupt35)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt36)    ? ABSOLUTE(__AltInterrupt36)    :
         (DEFINED(__Interrupt36)       ? ABSOLUTE(__Interrupt36)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt37)    ? ABSOLUTE(__AltInterrupt37)    :
         (DEFINED(__Interrupt37)       ? ABSOLUTE(__Interrupt37)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt38)    ? ABSOLUTE(__AltInterrupt38)    :
         (DEFINED(__Interrupt38)       ? ABSOLUTE(__Interrupt38)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt39)    ? ABSOLUTE(__AltInterrupt39)    :
         (DEFINED(__Interrupt39)       ? ABSOLUTE(__Interrupt39)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt40)    ? ABSOLUTE(__AltInterrupt40)    :
         (DEFINED(__Interrupt40)       ? ABSOLUTE(__Interrupt40)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt41)    ? ABSOLUTE(__AltInterrupt41)    :
         (DEFINED(__Interrupt41)       ? ABSOLUTE(__Interrupt41)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt42)    ? ABSOLUTE(__AltInterrupt42)    :
         (DEFINED(__Interrupt42)       ? ABSOLUTE(__Interrupt42)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCT3Interrupt)    ? ABSOLUTE(__AltCCT3Interrupt)    :
         (DEFINED(__CCT3Interrupt)       ? ABSOLUTE(__CCT3Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCT4Interrupt)    ? ABSOLUTE(__AltCCT4Interrupt)    :
         (DEFINED(__CCT4Interrupt)       ? ABSOLUTE(__CCT4Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt45)    ? ABSOLUTE(__AltInterrupt45)    :
         (DEFINED(__Interrupt45)       ? ABSOLUTE(__Interrupt45)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt46)    ? ABSOLUTE(__AltInterrupt46)    :
         (DEFINED(__Interrupt46)       ? ABSOLUTE(__Interrupt46)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCT5Interrupt)    ? ABSOLUTE(__AltCCT5Interrupt)    :
         (DEFINED(__CCT5Interrupt)       ? ABSOLUTE(__CCT5Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt48)    ? ABSOLUTE(__AltInterrupt48)    :
         (DEFINED(__Interrupt48)       ? ABSOLUTE(__Interrupt48)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSI2C2Interrupt)    ? ABSOLUTE(__AltSI2C2Interrupt)    :
         (DEFINED(__SI2C2Interrupt)       ? ABSOLUTE(__SI2C2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltMI2C2Interrupt)    ? ABSOLUTE(__AltMI2C2Interrupt)    :
         (DEFINED(__MI2C2Interrupt)       ? ABSOLUTE(__MI2C2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt51)    ? ABSOLUTE(__AltInterrupt51)    :
         (DEFINED(__Interrupt51)       ? ABSOLUTE(__Interrupt51)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt52)    ? ABSOLUTE(__AltInterrupt52)    :
         (DEFINED(__Interrupt52)       ? ABSOLUTE(__Interrupt52)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltINT3Interrupt)    ? ABSOLUTE(__AltINT3Interrupt)    :
         (DEFINED(__INT3Interrupt)       ? ABSOLUTE(__INT3Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltINT4Interrupt)    ? ABSOLUTE(__AltINT4Interrupt)    :
         (DEFINED(__INT4Interrupt)       ? ABSOLUTE(__INT4Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt55)    ? ABSOLUTE(__AltInterrupt55)    :
         (DEFINED(__Interrupt55)       ? ABSOLUTE(__Interrupt55)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt56)    ? ABSOLUTE(__AltInterrupt56)    :
         (DEFINED(__Interrupt56)       ? ABSOLUTE(__Interrupt56)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt57)    ? ABSOLUTE(__AltInterrupt57)    :
         (DEFINED(__Interrupt57)       ? ABSOLUTE(__Interrupt57)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI1RXInterrupt)    ? ABSOLUTE(__AltSPI1RXInterrupt)    :
         (DEFINED(__SPI1RXInterrupt)       ? ABSOLUTE(__SPI1RXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltSPI2RXInterrupt)    ? ABSOLUTE(__AltSPI2RXInterrupt)    :
         (DEFINED(__SPI2RXInterrupt)       ? ABSOLUTE(__SPI2RXInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt60)    ? ABSOLUTE(__AltInterrupt60)    :
         (DEFINED(__Interrupt60)       ? ABSOLUTE(__Interrupt60)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt61)    ? ABSOLUTE(__AltInterrupt61)    :
         (DEFINED(__Interrupt61)       ? ABSOLUTE(__Interrupt61)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltRTCCInterrupt)    ? ABSOLUTE(__AltRTCCInterrupt)    :
         (DEFINED(__RTCCInterrupt)       ? ABSOLUTE(__RTCCInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCP1Interrupt)    ? ABSOLUTE(__AltCCP1Interrupt)    :
         (DEFINED(__CCP1Interrupt)       ? ABSOLUTE(__CCP1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCP2Interrupt)    ? ABSOLUTE(__AltCCP2Interrupt)    :
         (DEFINED(__CCP2Interrupt)       ? ABSOLUTE(__CCP2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU1ErrInterrupt)    ? ABSOLUTE(__AltU1ErrInterrupt)    :
         (DEFINED(__U1ErrInterrupt)       ? ABSOLUTE(__U1ErrInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltU2ErrInterrupt)    ? ABSOLUTE(__AltU2ErrInterrupt)    :
         (DEFINED(__U2ErrInterrupt)       ? ABSOLUTE(__U2ErrInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCRCInterrupt)    ? ABSOLUTE(__AltCRCInterrupt)    :
         (DEFINED(__CRCInterrupt)       ? ABSOLUTE(__CRCInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt68)    ? ABSOLUTE(__AltInterrupt68)    :
         (DEFINED(__Interrupt68)       ? ABSOLUTE(__Interrupt68)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt69)    ? ABSOLUTE(__AltInterrupt69)    :
         (DEFINED(__Interrupt69)       ? ABSOLUTE(__Interrupt69)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt70)    ? ABSOLUTE(__AltInterrupt70)    :
         (DEFINED(__Interrupt70)       ? ABSOLUTE(__Interrupt70)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt71)    ? ABSOLUTE(__AltInterrupt71)    :
         (DEFINED(__Interrupt71)       ? ABSOLUTE(__Interrupt71)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltHLVDInterrupt)    ? ABSOLUTE(__AltHLVDInterrupt)    :
         (DEFINED(__HLVDInterrupt)       ? ABSOLUTE(__HLVDInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt73)    ? ABSOLUTE(__AltInterrupt73)    :
         (DEFINED(__Interrupt73)       ? ABSOLUTE(__Interrupt73)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt74)    ? ABSOLUTE(__AltInterrupt74)    :
         (DEFINED(__Interrupt74)       ? ABSOLUTE(__Interrupt74)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt75)    ? ABSOLUTE(__AltInterrupt75)    :
         (DEFINED(__Interrupt75)       ? ABSOLUTE(__Interrupt75)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt76)    ? ABSOLUTE(__AltInterrupt76)    :
         (DEFINED(__Interrupt76)       ? ABSOLUTE(__Interrupt76)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt77)    ? ABSOLUTE(__AltInterrupt77)    :
         (DEFINED(__Interrupt77)       ? ABSOLUTE(__Interrupt77)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt78)    ? ABSOLUTE(__AltInterrupt78)    :
         (DEFINED(__Interrupt78)       ? ABSOLUTE(__Interrupt78)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt79)    ? ABSOLUTE(__AltInterrupt79)    :
         (DEFINED(__Interrupt79)       ? ABSOLUTE(__Interrupt79)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt80)    ? ABSOLUTE(__AltInterrupt80)    :
         (DEFINED(__Interrupt80)       ? ABSOLUTE(__Interrupt80)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt81)    ? ABSOLUTE(__AltInterrupt81)    :
         (DEFINED(__Interrupt81)       ? ABSOLUTE(__Interrupt81)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt82)    ? ABSOLUTE(__AltInterrupt82)    :
         (DEFINED(__Interrupt82)       ? ABSOLUTE(__Interrupt82)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt83)    ? ABSOLUTE(__AltInterrupt83)    :
         (DEFINED(__Interrupt83)       ? ABSOLUTE(__Interrupt83)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltI2C1BCInterrupt)    ? ABSOLUTE(__AltI2C1BCInterrupt)    :
         (DEFINED(__I2C1BCInterrupt)       ? ABSOLUTE(__I2C1BCInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltI2C2BCInterrupt)    ? ABSOLUTE(__AltI2C2BCInterrupt)    :
         (DEFINED(__I2C2BCInterrupt)       ? ABSOLUTE(__I2C2BCInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltUSB1Interrupt)    ? ABSOLUTE(__AltUSB1Interrupt)    :
         (DEFINED(__USB1Interrupt)       ? ABSOLUTE(__USB1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt87)    ? ABSOLUTE(__AltInterrupt87)    :
         (DEFINED(__Interrupt87)       ? ABSOLUTE(__Interrupt87)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt88)    ? ABSOLUTE(__AltInterrupt88)    :
         (DEFINED(__Interrupt88)       ? ABSOLUTE(__Interrupt88)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt89)    ? ABSOLUTE(__AltInterrupt89)    :
         (DEFINED(__Interrupt89)       ? ABSOLUTE(__Interrupt89)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt90)    ? ABSOLUTE(__AltInterrupt90)    :
         (DEFINED(__Interrupt90)       ? ABSOLUTE(__Interrupt90)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt91)    ? ABSOLUTE(__AltInterrupt91)    :
         (DEFINED(__Interrupt91)       ? ABSOLUTE(__Interrupt91)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt92)    ? ABSOLUTE(__AltInterrupt92)    :
         (DEFINED(__Interrupt92)       ? ABSOLUTE(__Interrupt92)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt93)    ? ABSOLUTE(__AltInterrupt93)    :
         (DEFINED(__Interrupt93)       ? ABSOLUTE(__Interrupt93)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCP3Interrupt)    ? ABSOLUTE(__AltCCP3Interrupt)    :
         (DEFINED(__CCP3Interrupt)       ? ABSOLUTE(__CCP3Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCCP4Interrupt)    ? ABSOLUTE(__AltCCP4Interrupt)    :
         (DEFINED(__CCP4Interrupt)       ? ABSOLUTE(__CCP4Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCLC1Interrupt)    ? ABSOLUTE(__AltCLC1Interrupt)    :
         (DEFINED(__CLC1Interrupt)       ? ABSOLUTE(__CLC1Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCLC2Interrupt)    ? ABSOLUTE(__AltCLC2Interrupt)    :
         (DEFINED(__CLC2Interrupt)       ? ABSOLUTE(__CLC2Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCLC3Interrupt)    ? ABSOLUTE(__AltCLC3Interrupt)    :
         (DEFINED(__CLC3Interrupt)       ? ABSOLUTE(__CLC3Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltCLC4Interrupt)    ? ABSOLUTE(__AltCLC4Interrupt)    :
         (DEFINED(__CLC4Interrupt)       ? ABSOLUTE(__CLC4Interrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt100)    ? ABSOLUTE(__AltInterrupt100)    :
         (DEFINED(__Interrupt100)       ? ABSOLUTE(__Interrupt100)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt101)    ? ABSOLUTE(__AltInterrupt101)    :
         (DEFINED(__Interrupt101)       ? ABSOLUTE(__Interrupt101)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt102)    ? ABSOLUTE(__AltInterrupt102)    :
         (DEFINED(__Interrupt102)       ? ABSOLUTE(__Interrupt102)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt103)    ? ABSOLUTE(__AltInterrupt103)    :
         (DEFINED(__Interrupt103)       ? ABSOLUTE(__Interrupt103)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt104)    ? ABSOLUTE(__AltInterrupt104)    :
         (DEFINED(__Interrupt104)       ? ABSOLUTE(__Interrupt104)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt105)    ? ABSOLUTE(__AltInterrupt105)    :
         (DEFINED(__Interrupt105)       ? ABSOLUTE(__Interrupt105)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltFSTInterrupt)    ? ABSOLUTE(__AltFSTInterrupt)    :
         (DEFINED(__FSTInterrupt)       ? ABSOLUTE(__FSTInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt107)    ? ABSOLUTE(__AltInterrupt107)    :
         (DEFINED(__Interrupt107)       ? ABSOLUTE(__Interrupt107)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltECCSBEInterrupt)    ? ABSOLUTE(__AltECCSBEInterrupt)    :
         (DEFINED(__ECCSBEInterrupt)       ? ABSOLUTE(__ECCSBEInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt109)    ? ABSOLUTE(__AltInterrupt109)    :
         (DEFINED(__Interrupt109)       ? ABSOLUTE(__Interrupt109)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltRTCCTSInterrupt)    ? ABSOLUTE(__AltRTCCTSInterrupt)    :
         (DEFINED(__RTCCTSInterrupt)       ? ABSOLUTE(__RTCCTSInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt111)    ? ABSOLUTE(__AltInterrupt111)    :
         (DEFINED(__Interrupt111)       ? ABSOLUTE(__Interrupt111)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt112)    ? ABSOLUTE(__AltInterrupt112)    :
         (DEFINED(__Interrupt112)       ? ABSOLUTE(__Interrupt112)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt113)    ? ABSOLUTE(__AltInterrupt113)    :
         (DEFINED(__Interrupt113)       ? ABSOLUTE(__Interrupt113)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt114)    ? ABSOLUTE(__AltInterrupt114)    :
         (DEFINED(__Interrupt114)       ? ABSOLUTE(__Interrupt114)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt115)    ? ABSOLUTE(__AltInterrupt115)    :
         (DEFINED(__Interrupt115)       ? ABSOLUTE(__Interrupt115)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltInterrupt116)    ? ABSOLUTE(__AltInterrupt116)    :
         (DEFINED(__Interrupt116)       ? ABSOLUTE(__Interrupt116)       :
         ABSOLUTE(__DefaultInterrupt)));
    LONG( DEFINED(__AltJTAGInterrupt)    ? ABSOLUTE(__AltJTAGInterrupt)    :
         (DEFINED(__JTAGInterrupt)       ? ABSOLUTE(__JTAGInterrupt)       :
         ABSOLUTE(__DefaultInterrupt)));
  } >program
} /* SECTIONS */
#endif


/*
** ============== Equates for SFR Addresses =============
*/

 WREG0        = 0x0;
_WREG0        = 0x0;
 WREG1        = 0x2;
_WREG1        = 0x2;
 WREG2        = 0x4;
_WREG2        = 0x4;
 WREG3        = 0x6;
_WREG3        = 0x6;
 WREG4        = 0x8;
_WREG4        = 0x8;
 WREG5        = 0xA;
_WREG5        = 0xA;
 WREG6        = 0xC;
_WREG6        = 0xC;
 WREG7        = 0xE;
_WREG7        = 0xE;
 WREG8        = 0x10;
_WREG8        = 0x10;
 WREG9        = 0x12;
_WREG9        = 0x12;
 WREG10       = 0x14;
_WREG10       = 0x14;
 WREG11       = 0x16;
_WREG11       = 0x16;
 WREG12       = 0x18;
_WREG12       = 0x18;
 WREG13       = 0x1A;
_WREG13       = 0x1A;
 WREG14       = 0x1C;
_WREG14       = 0x1C;
 WREG15       = 0x1E;
_WREG15       = 0x1E;
 SPLIM        = 0x20;
_SPLIM        = 0x20;
 PCL          = 0x2E;
_PCL          = 0x2E;
 PCH          = 0x30;
_PCH          = 0x30;
 DSRPAG       = 0x32;
_DSRPAG       = 0x32;
_DSRPAGbits   = 0x32;
 DSWPAG       = 0x34;
_DSWPAG       = 0x34;
_DSWPAGbits   = 0x34;
 RCOUNT       = 0x36;
_RCOUNT       = 0x36;
 SR           = 0x42;
_SR           = 0x42;
_SRbits       = 0x42;
 CORCON       = 0x44;
_CORCON       = 0x44;
_CORCONbits   = 0x44;
 DISICNT      = 0x52;
_DISICNT      = 0x52;
_DISICNTbits  = 0x52;
 TBLPAG       = 0x54;
_TBLPAG       = 0x54;
_TBLPAGbits   = 0x54;
 DMTCON       = 0x5C;
_DMTCON       = 0x5C;
_DMTCONbits   = 0x5C;
 DMTPRECLR    = 0x60;
_DMTPRECLR    = 0x60;
_DMTPRECLRbits = 0x60;
 DMTCLR       = 0x64;
_DMTCLR       = 0x64;
_DMTCLRbits   = 0x64;
 DMTSTAT      = 0x68;
_DMTSTAT      = 0x68;
_DMTSTATbits  = 0x68;
 DMTCNTL      = 0x6C;
_DMTCNTL      = 0x6C;
 DMTCNTH      = 0x6E;
_DMTCNTH      = 0x6E;
 DMTHOLDREG   = 0x70;
_DMTHOLDREG   = 0x70;
 DMTPSCNTL    = 0x74;
_DMTPSCNTL    = 0x74;
 DMTPSCNTH    = 0x76;
_DMTPSCNTH    = 0x76;
 DMTPSINTVL   = 0x78;
_DMTPSINTVL   = 0x78;
 DMTPSINTVH   = 0x7A;
_DMTPSINTVH   = 0x7A;
 INTCON1      = 0x80;
_INTCON1      = 0x80;
_INTCON1bits  = 0x80;
 INTCON2      = 0x82;
_INTCON2      = 0x82;
_INTCON2bits  = 0x82;
 INTCON3      = 0x84;
_INTCON3      = 0x84;
_INTCON3bits  = 0x84;
 INTCON4      = 0x86;
_INTCON4      = 0x86;
_INTCON4bits  = 0x86;
 IFS0         = 0x88;
_IFS0         = 0x88;
_IFS0bits     = 0x88;
 IFS1         = 0x8A;
_IFS1         = 0x8A;
_IFS1bits     = 0x8A;
 IFS2         = 0x8C;
_IFS2         = 0x8C;
_IFS2bits     = 0x8C;
 IFS3         = 0x8E;
_IFS3         = 0x8E;
_IFS3bits     = 0x8E;
 IFS4         = 0x90;
_IFS4         = 0x90;
_IFS4bits     = 0x90;
 IFS5         = 0x92;
_IFS5         = 0x92;
_IFS5bits     = 0x92;
 IFS6         = 0x94;
_IFS6         = 0x94;
_IFS6bits     = 0x94;
 IFS7         = 0x96;
_IFS7         = 0x96;
_IFS7bits     = 0x96;
 IEC0         = 0x98;
_IEC0         = 0x98;
_IEC0bits     = 0x98;
 IEC1         = 0x9A;
_IEC1         = 0x9A;
_IEC1bits     = 0x9A;
 IEC2         = 0x9C;
_IEC2         = 0x9C;
_IEC2bits     = 0x9C;
 IEC3         = 0x9E;
_IEC3         = 0x9E;
_IEC3bits     = 0x9E;
 IEC4         = 0xA0;
_IEC4         = 0xA0;
_IEC4bits     = 0xA0;
 IEC5         = 0xA2;
_IEC5         = 0xA2;
_IEC5bits     = 0xA2;
 IEC6         = 0xA4;
_IEC6         = 0xA4;
_IEC6bits     = 0xA4;
 IEC7         = 0xA6;
_IEC7         = 0xA6;
_IEC7bits     = 0xA6;
 IPC0         = 0xA8;
_IPC0         = 0xA8;
_IPC0bits     = 0xA8;
 IPC1         = 0xAA;
_IPC1         = 0xAA;
_IPC1bits     = 0xAA;
 IPC2         = 0xAC;
_IPC2         = 0xAC;
_IPC2bits     = 0xAC;
 IPC3         = 0xAE;
_IPC3         = 0xAE;
_IPC3bits     = 0xAE;
 IPC4         = 0xB0;
_IPC4         = 0xB0;
_IPC4bits     = 0xB0;
 IPC5         = 0xB2;
_IPC5         = 0xB2;
_IPC5bits     = 0xB2;
 IPC7         = 0xB6;
_IPC7         = 0xB6;
_IPC7bits     = 0xB6;
 IPC8         = 0xB8;
_IPC8         = 0xB8;
_IPC8bits     = 0xB8;
 IPC9         = 0xBA;
_IPC9         = 0xBA;
 IPC10        = 0xBC;
_IPC10        = 0xBC;
_IPC10bits    = 0xBC;
 IPC11        = 0xBE;
_IPC11        = 0xBE;
_IPC11bits    = 0xBE;
 IPC12        = 0xC0;
_IPC12        = 0xC0;
_IPC12bits    = 0xC0;
 IPC13        = 0xC2;
_IPC13        = 0xC2;
_IPC13bits    = 0xC2;
 IPC14        = 0xC4;
_IPC14        = 0xC4;
_IPC14bits    = 0xC4;
 IPC15        = 0xC6;
_IPC15        = 0xC6;
_IPC15bits    = 0xC6;
 IPC16        = 0xC8;
_IPC16        = 0xC8;
_IPC16bits    = 0xC8;
 IPC17        = 0xCA;
_IPC17        = 0xCA;
 IPC18        = 0xCC;
_IPC18        = 0xCC;
_IPC18bits    = 0xCC;
 IPC19        = 0xCE;
_IPC19        = 0xCE;
 IPC20        = 0xD0;
_IPC20        = 0xD0;
 IPC21        = 0xD2;
_IPC21        = 0xD2;
_IPC21bits    = 0xD2;
 IPC22        = 0xD4;
_IPC22        = 0xD4;
 IPC23        = 0xD6;
_IPC23        = 0xD6;
_IPC23bits    = 0xD6;
 IPC24        = 0xD8;
_IPC24        = 0xD8;
_IPC24bits    = 0xD8;
 IPC25        = 0xDA;
_IPC25        = 0xDA;
 IPC26        = 0xDC;
_IPC26        = 0xDC;
_IPC26bits    = 0xDC;
 IPC27        = 0xDE;
_IPC27        = 0xDE;
_IPC27bits    = 0xDE;
 IPC28        = 0xE0;
_IPC28        = 0xE0;
 IPC29        = 0xE2;
_IPC29        = 0xE2;
_IPC29bits    = 0xE2;
 INTTREG      = 0xE4;
_INTTREG      = 0xE4;
_INTTREGbits  = 0xE4;
 OSCCON       = 0x100;
_OSCCON       = 0x100;
_OSCCONbits   = 0x100;
 OSCCONL      = 0x100;
_OSCCONL      = 0x100;
 OSCCONH      = 0x101;
_OSCCONH      = 0x101;
 CLKDIV       = 0x102;
_CLKDIV       = 0x102;
_CLKDIVbits   = 0x102;
 OSCTUN       = 0x106;
_OSCTUN       = 0x106;
_OSCTUNbits   = 0x106;
 OSCDIV       = 0x10C;
_OSCDIV       = 0x10C;
_OSCDIVbits   = 0x10C;
 OSCFDIV      = 0x10E;
_OSCFDIV      = 0x10E;
_OSCFDIVbits  = 0x10E;
 RCON         = 0x110;
_RCON         = 0x110;
_RCONbits     = 0x110;
 HLVDCON      = 0x114;
_HLVDCON      = 0x114;
_HLVDCONbits  = 0x114;
 CRCCON1      = 0x158;
_CRCCON1      = 0x158;
_CRCCON1bits  = 0x158;
 CRCCON2      = 0x15A;
_CRCCON2      = 0x15A;
_CRCCON2bits  = 0x15A;
 CRCXORL      = 0x15C;
_CRCXORL      = 0x15C;
_CRCXORLbits  = 0x15C;
 CRCXORH      = 0x15E;
_CRCXORH      = 0x15E;
_CRCXORHbits  = 0x15E;
 CRCDAT       = 0x160;
_CRCDAT       = 0x160;
 CRCDATL      = 0x160;
_CRCDATL      = 0x160;
 CRCDATH      = 0x162;
_CRCDATH      = 0x162;
 CRCWDAT      = 0x164;
_CRCWDAT      = 0x164;
 CRCWDATL     = 0x164;
_CRCWDATL     = 0x164;
 CRCWDATH     = 0x166;
_CRCWDATH     = 0x166;
 REFOCON1     = 0x168;
_REFOCON1     = 0x168;
_REFOCON1bits = 0x168;
 REFOCONL     = 0x168;
_REFOCONL     = 0x168;
_REFOCONLbits = 0x168;
 REFOCON2     = 0x16A;
_REFOCON2     = 0x16A;
_REFOCON2bits = 0x16A;
 REFOCONH     = 0x16A;
_REFOCONH     = 0x16A;
_REFOCONHbits = 0x16A;
 PMD1         = 0x178;
_PMD1         = 0x178;
_PMD1bits     = 0x178;
 PMD2         = 0x17A;
_PMD2         = 0x17A;
 PMD3         = 0x17C;
_PMD3         = 0x17C;
_PMD3bits     = 0x17C;
 PMD4         = 0x17E;
_PMD4         = 0x17E;
_PMD4bits     = 0x17E;
 PMD5         = 0x180;
_PMD5         = 0x180;
_PMD5bits     = 0x180;
 PMD6         = 0x182;
_PMD6         = 0x182;
 PMD7         = 0x184;
_PMD7         = 0x184;
_PMD7bits     = 0x184;
 PMD8         = 0x186;
_PMD8         = 0x186;
_PMD8bits     = 0x186;
 TMR1         = 0x190;
_TMR1         = 0x190;
 PR1          = 0x192;
_PR1          = 0x192;
 T1CON        = 0x194;
_T1CON        = 0x194;
_T1CONbits    = 0x194;
 TMR2         = 0x196;
_TMR2         = 0x196;
 TMR3HLD      = 0x198;
_TMR3HLD      = 0x198;
 TMR3         = 0x19A;
_TMR3         = 0x19A;
 PR2          = 0x19C;
_PR2          = 0x19C;
 PR3          = 0x19E;
_PR3          = 0x19E;
 T2CON        = 0x1A0;
_T2CON        = 0x1A0;
_T2CONbits    = 0x1A0;
 T3CON        = 0x1A2;
_T3CON        = 0x1A2;
_T3CONbits    = 0x1A2;
 RTCCON1L     = 0x1CC;
_RTCCON1L     = 0x1CC;
_RTCCON1Lbits = 0x1CC;
 RTCCON1H     = 0x1CE;
_RTCCON1H     = 0x1CE;
_RTCCON1Hbits = 0x1CE;
 RTCCON2L     = 0x1D0;
_RTCCON2L     = 0x1D0;
_RTCCON2Lbits = 0x1D0;
 RTCCON2H     = 0x1D2;
_RTCCON2H     = 0x1D2;
 RTCCON3L     = 0x1D4;
_RTCCON3L     = 0x1D4;
_RTCCON3Lbits = 0x1D4;
 RTCSTATL     = 0x1D8;
_RTCSTATL     = 0x1D8;
_RTCSTATLbits = 0x1D8;
 TIMEL        = 0x1DC;
_TIMEL        = 0x1DC;
_TIMELbits    = 0x1DC;
 TIMEH        = 0x1DE;
_TIMEH        = 0x1DE;
_TIMEHbits    = 0x1DE;
 DATEL        = 0x1E0;
_DATEL        = 0x1E0;
_DATELbits    = 0x1E0;
 DATEH        = 0x1E2;
_DATEH        = 0x1E2;
_DATEHbits    = 0x1E2;
 ALMTIMEL     = 0x1E4;
_ALMTIMEL     = 0x1E4;
_ALMTIMELbits = 0x1E4;
 ALMTIMEH     = 0x1E6;
_ALMTIMEH     = 0x1E6;
_ALMTIMEHbits = 0x1E6;
 ALMDATEL     = 0x1E8;
_ALMDATEL     = 0x1E8;
_ALMDATELbits = 0x1E8;
 ALMDATEH     = 0x1EA;
_ALMDATEH     = 0x1EA;
_ALMDATEHbits = 0x1EA;
 TSATIMEL     = 0x1EC;
_TSATIMEL     = 0x1EC;
_TSATIMELbits = 0x1EC;
 TSATIMEH     = 0x1EE;
_TSATIMEH     = 0x1EE;
_TSATIMEHbits = 0x1EE;
 TSADATEL     = 0x1F0;
_TSADATEL     = 0x1F0;
_TSADATELbits = 0x1F0;
 TSADATEH     = 0x1F2;
_TSADATEH     = 0x1F2;
_TSADATEHbits = 0x1F2;
 CCP1CON1L    = 0x26C;
_CCP1CON1L    = 0x26C;
_CCP1CON1Lbits = 0x26C;
 CCP1CON1H    = 0x26E;
_CCP1CON1H    = 0x26E;
_CCP1CON1Hbits = 0x26E;
 CCP1CON2L    = 0x270;
_CCP1CON2L    = 0x270;
_CCP1CON2Lbits = 0x270;
 CCP1CON2H    = 0x272;
_CCP1CON2H    = 0x272;
_CCP1CON2Hbits = 0x272;
 CCP1CON3L    = 0x274;
_CCP1CON3L    = 0x274;
_CCP1CON3Lbits = 0x274;
 CCP1CON3H    = 0x276;
_CCP1CON3H    = 0x276;
_CCP1CON3Hbits = 0x276;
 CCP1STAT     = 0x278;
_CCP1STAT     = 0x278;
_CCP1STATbits = 0x278;
 CCP1STATL    = 0x278;
_CCP1STATL    = 0x278;
_CCP1STATLbits = 0x278;
 CCP1TMRL     = 0x27C;
_CCP1TMRL     = 0x27C;
 CCP1TMRH     = 0x27E;
_CCP1TMRH     = 0x27E;
 CCP1PRL      = 0x280;
_CCP1PRL      = 0x280;
 CCP1PRH      = 0x282;
_CCP1PRH      = 0x282;
 CCP1RA       = 0x284;
_CCP1RA       = 0x284;
 CCP1RAL      = 0x284;
_CCP1RAL      = 0x284;
 CCP1RAH      = 0x286;
_CCP1RAH      = 0x286;
 CCP1RB       = 0x288;
_CCP1RB       = 0x288;
 CCP1RBL      = 0x288;
_CCP1RBL      = 0x288;
 CCP1RBH      = 0x28A;
_CCP1RBH      = 0x28A;
 CCP1BUFL     = 0x28C;
_CCP1BUFL     = 0x28C;
 CCP1BUFH     = 0x28E;
_CCP1BUFH     = 0x28E;
 CCP2CON1L    = 0x290;
_CCP2CON1L    = 0x290;
_CCP2CON1Lbits = 0x290;
 CCP2CON1H    = 0x292;
_CCP2CON1H    = 0x292;
_CCP2CON1Hbits = 0x292;
 CCP2CON2L    = 0x294;
_CCP2CON2L    = 0x294;
_CCP2CON2Lbits = 0x294;
 CCP2CON2H    = 0x296;
_CCP2CON2H    = 0x296;
_CCP2CON2Hbits = 0x296;
 CCP2CON3L    = 0x298;
_CCP2CON3L    = 0x298;
_CCP2CON3Lbits = 0x298;
 CCP2CON3H    = 0x29A;
_CCP2CON3H    = 0x29A;
_CCP2CON3Hbits = 0x29A;
 CCP2STAT     = 0x29C;
_CCP2STAT     = 0x29C;
_CCP2STATbits = 0x29C;
 CCP2STATL    = 0x29C;
_CCP2STATL    = 0x29C;
_CCP2STATLbits = 0x29C;
 CCP2TMRL     = 0x2A0;
_CCP2TMRL     = 0x2A0;
 CCP2TMRH     = 0x2A2;
_CCP2TMRH     = 0x2A2;
 CCP2PRL      = 0x2A4;
_CCP2PRL      = 0x2A4;
 CCP2PRH      = 0x2A6;
_CCP2PRH      = 0x2A6;
 CCP2RA       = 0x2A8;
_CCP2RA       = 0x2A8;
 CCP2RAL      = 0x2A8;
_CCP2RAL      = 0x2A8;
 CCP2RAH      = 0x2AA;
_CCP2RAH      = 0x2AA;
 CCP2RB       = 0x2AC;
_CCP2RB       = 0x2AC;
 CCP2RBL      = 0x2AC;
_CCP2RBL      = 0x2AC;
 CCP2RBH      = 0x2AE;
_CCP2RBH      = 0x2AE;
 CCP2BUFL     = 0x2B0;
_CCP2BUFL     = 0x2B0;
 CCP2BUFH     = 0x2B2;
_CCP2BUFH     = 0x2B2;
 CCP3CON1L    = 0x2B4;
_CCP3CON1L    = 0x2B4;
_CCP3CON1Lbits = 0x2B4;
 CCP3CON1H    = 0x2B6;
_CCP3CON1H    = 0x2B6;
_CCP3CON1Hbits = 0x2B6;
 CCP3CON2L    = 0x2B8;
_CCP3CON2L    = 0x2B8;
_CCP3CON2Lbits = 0x2B8;
 CCP3CON2H    = 0x2BA;
_CCP3CON2H    = 0x2BA;
_CCP3CON2Hbits = 0x2BA;
 CCP3CON3L    = 0x2BC;
_CCP3CON3L    = 0x2BC;
_CCP3CON3Lbits = 0x2BC;
 CCP3CON3H    = 0x2BE;
_CCP3CON3H    = 0x2BE;
_CCP3CON3Hbits = 0x2BE;
 CCP3STAT     = 0x2C0;
_CCP3STAT     = 0x2C0;
_CCP3STATbits = 0x2C0;
 CCP3STATL    = 0x2C0;
_CCP3STATL    = 0x2C0;
_CCP3STATLbits = 0x2C0;
 CCP3TMRL     = 0x2C4;
_CCP3TMRL     = 0x2C4;
 CCP3TMRH     = 0x2C6;
_CCP3TMRH     = 0x2C6;
 CCP3PRL      = 0x2C8;
_CCP3PRL      = 0x2C8;
 CCP3PRH      = 0x2CA;
_CCP3PRH      = 0x2CA;
 CCP3RA       = 0x2CC;
_CCP3RA       = 0x2CC;
 CCP3RAL      = 0x2CC;
_CCP3RAL      = 0x2CC;
 CCP3RAH      = 0x2CE;
_CCP3RAH      = 0x2CE;
 CCP3RB       = 0x2D0;
_CCP3RB       = 0x2D0;
 CCP3RBL      = 0x2D0;
_CCP3RBL      = 0x2D0;
 CCP3RBH      = 0x2D2;
_CCP3RBH      = 0x2D2;
 CCP3BUFL     = 0x2D4;
_CCP3BUFL     = 0x2D4;
 CCP3BUFH     = 0x2D6;
_CCP3BUFH     = 0x2D6;
 CMSTAT       = 0x2E6;
_CMSTAT       = 0x2E6;
_CMSTATbits   = 0x2E6;
 CVRCON       = 0x2E8;
_CVRCON       = 0x2E8;
_CVRCONbits   = 0x2E8;
 CM1CON       = 0x2EA;
_CM1CON       = 0x2EA;
_CM1CONbits   = 0x2EA;
 CM2CON       = 0x2EC;
_CM2CON       = 0x2EC;
_CM2CONbits   = 0x2EC;
 CM3CON       = 0x2EE;
_CM3CON       = 0x2EE;
_CM3CONbits   = 0x2EE;
 ANCFG        = 0x2F4;
_ANCFG        = 0x2F4;
_ANCFGbits    = 0x2F4;
 CCP4CON1L    = 0x300;
_CCP4CON1L    = 0x300;
_CCP4CON1Lbits = 0x300;
 CCP4CON1H    = 0x302;
_CCP4CON1H    = 0x302;
_CCP4CON1Hbits = 0x302;
 CCP4CON2L    = 0x304;
_CCP4CON2L    = 0x304;
_CCP4CON2Lbits = 0x304;
 CCP4CON2H    = 0x306;
_CCP4CON2H    = 0x306;
_CCP4CON2Hbits = 0x306;
 CCP4CON3L    = 0x308;
_CCP4CON3L    = 0x308;
_CCP4CON3Lbits = 0x308;
 CCP4CON3H    = 0x30A;
_CCP4CON3H    = 0x30A;
_CCP4CON3Hbits = 0x30A;
 CCP4STAT     = 0x30C;
_CCP4STAT     = 0x30C;
_CCP4STATbits = 0x30C;
 CCP4STATL    = 0x30C;
_CCP4STATL    = 0x30C;
_CCP4STATLbits = 0x30C;
 CCP4TMRL     = 0x310;
_CCP4TMRL     = 0x310;
 CCP4TMRH     = 0x312;
_CCP4TMRH     = 0x312;
 CCP4PRL      = 0x314;
_CCP4PRL      = 0x314;
 CCP4PRH      = 0x316;
_CCP4PRH      = 0x316;
 CCP4RA       = 0x318;
_CCP4RA       = 0x318;
 CCP4RAL      = 0x318;
_CCP4RAL      = 0x318;
 CCP4RAH      = 0x31A;
_CCP4RAH      = 0x31A;
 CCP4RB       = 0x31C;
_CCP4RB       = 0x31C;
 CCP4RBL      = 0x31C;
_CCP4RBL      = 0x31C;
 CCP4RBH      = 0x31E;
_CCP4RBH      = 0x31E;
 CCP4BUFL     = 0x320;
_CCP4BUFL     = 0x320;
 CCP4BUFH     = 0x322;
_CCP4BUFH     = 0x322;
 CCP5CON1L    = 0x324;
_CCP5CON1L    = 0x324;
_CCP5CON1Lbits = 0x324;
 CCP5CON1H    = 0x326;
_CCP5CON1H    = 0x326;
_CCP5CON1Hbits = 0x326;
 CCP5CON2L    = 0x328;
_CCP5CON2L    = 0x328;
_CCP5CON2Lbits = 0x328;
 CCP5CON2H    = 0x32A;
_CCP5CON2H    = 0x32A;
_CCP5CON2Hbits = 0x32A;
 CCP5CON3L    = 0x32C;
_CCP5CON3L    = 0x32C;
_CCP5CON3Lbits = 0x32C;
 CCP5CON3H    = 0x32E;
_CCP5CON3H    = 0x32E;
_CCP5CON3Hbits = 0x32E;
 CCP5STAT     = 0x330;
_CCP5STAT     = 0x330;
_CCP5STATbits = 0x330;
 CCP5STATL    = 0x330;
_CCP5STATL    = 0x330;
_CCP5STATLbits = 0x330;
 CCP5TMRL     = 0x334;
_CCP5TMRL     = 0x334;
 CCP5TMRH     = 0x336;
_CCP5TMRH     = 0x336;
 CCP5PRL      = 0x338;
_CCP5PRL      = 0x338;
 CCP5PRH      = 0x33A;
_CCP5PRH      = 0x33A;
 CCP5RA       = 0x33C;
_CCP5RA       = 0x33C;
 CCP5RAL      = 0x33C;
_CCP5RAL      = 0x33C;
 CCP5RAH      = 0x33E;
_CCP5RAH      = 0x33E;
 CCP5RB       = 0x340;
_CCP5RB       = 0x340;
 CCP5RBL      = 0x340;
_CCP5RBL      = 0x340;
 CCP5RBH      = 0x342;
_CCP5RBH      = 0x342;
 CCP5BUFL     = 0x344;
_CCP5BUFL     = 0x344;
 CCP5BUFH     = 0x346;
_CCP5BUFH     = 0x346;
 U1MODE       = 0x398;
_U1MODE       = 0x398;
_U1MODEbits   = 0x398;
 U1STA        = 0x39A;
_U1STA        = 0x39A;
_U1STAbits    = 0x39A;
 U1TXREG      = 0x39C;
_U1TXREG      = 0x39C;
 U1RXREG      = 0x39E;
_U1RXREG      = 0x39E;
 U1BRG        = 0x3A0;
_U1BRG        = 0x3A0;
 U2MODE       = 0x3AE;
_U2MODE       = 0x3AE;
_U2MODEbits   = 0x3AE;
 U2STA        = 0x3B0;
_U2STA        = 0x3B0;
_U2STAbits    = 0x3B0;
 U2TXREG      = 0x3B2;
_U2TXREG      = 0x3B2;
 U2RXREG      = 0x3B4;
_U2RXREG      = 0x3B4;
 U2BRG        = 0x3B6;
_U2BRG        = 0x3B6;
 SPI1CON1     = 0x3F4;
_SPI1CON1     = 0x3F4;
_SPI1CON1bits = 0x3F4;
 SPI1CON1L    = 0x3F4;
_SPI1CON1L    = 0x3F4;
_SPI1CON1Lbits = 0x3F4;
 SPI1CON1H    = 0x3F6;
_SPI1CON1H    = 0x3F6;
_SPI1CON1Hbits = 0x3F6;
 SPI1CON2     = 0x3F6;
_SPI1CON2     = 0x3F6;
_SPI1CON2bits = 0x3F6;
 SPI1CON2L    = 0x3F8;
_SPI1CON2L    = 0x3F8;
_SPI1CON2Lbits = 0x3F8;
 SPI1CON3     = 0x3F8;
_SPI1CON3     = 0x3F8;
_SPI1CON3bits = 0x3F8;
 SPI1STATL    = 0x3FC;
_SPI1STATL    = 0x3FC;
_SPI1STATLbits = 0x3FC;
 SPI1STATH    = 0x3FE;
_SPI1STATH    = 0x3FE;
_SPI1STATHbits = 0x3FE;
 SPI1BUFL     = 0x400;
_SPI1BUFL     = 0x400;
_SPI1BUFLbits = 0x400;
 SPI1BUFH     = 0x402;
_SPI1BUFH     = 0x402;
_SPI1BUFHbits = 0x402;
 SPI1BRGL     = 0x404;
_SPI1BRGL     = 0x404;
_SPI1BRGLbits = 0x404;
 SPI1IMSK1    = 0x408;
_SPI1IMSK1    = 0x408;
_SPI1IMSK1bits = 0x408;
 SPI1IMSKL    = 0x408;
_SPI1IMSKL    = 0x408;
_SPI1IMSKLbits = 0x408;
 SPI1IMSK2    = 0x40A;
_SPI1IMSK2    = 0x40A;
_SPI1IMSK2bits = 0x40A;
 SPI1IMSKH    = 0x40A;
_SPI1IMSKH    = 0x40A;
_SPI1IMSKHbits = 0x40A;
 SPI1URDTL    = 0x40C;
_SPI1URDTL    = 0x40C;
_SPI1URDTLbits = 0x40C;
 SPI1URDTH    = 0x40E;
_SPI1URDTH    = 0x40E;
_SPI1URDTHbits = 0x40E;
 SPI2CON1     = 0x410;
_SPI2CON1     = 0x410;
_SPI2CON1bits = 0x410;
 SPI2CON1L    = 0x410;
_SPI2CON1L    = 0x410;
_SPI2CON1Lbits = 0x410;
 SPI2CON1H    = 0x412;
_SPI2CON1H    = 0x412;
_SPI2CON1Hbits = 0x412;
 SPI2CON2     = 0x412;
_SPI2CON2     = 0x412;
_SPI2CON2bits = 0x412;
 SPI2CON2L    = 0x414;
_SPI2CON2L    = 0x414;
_SPI2CON2Lbits = 0x414;
 SPI2CON3     = 0x414;
_SPI2CON3     = 0x414;
_SPI2CON3bits = 0x414;
 SPI2STATL    = 0x418;
_SPI2STATL    = 0x418;
_SPI2STATLbits = 0x418;
 SPI2STATH    = 0x41A;
_SPI2STATH    = 0x41A;
_SPI2STATHbits = 0x41A;
 SPI2BUFL     = 0x41C;
_SPI2BUFL     = 0x41C;
_SPI2BUFLbits = 0x41C;
 SPI2BUFH     = 0x41E;
_SPI2BUFH     = 0x41E;
_SPI2BUFHbits = 0x41E;
 SPI2BRGL     = 0x420;
_SPI2BRGL     = 0x420;
_SPI2BRGLbits = 0x420;
 SPI2IMSK1    = 0x424;
_SPI2IMSK1    = 0x424;
_SPI2IMSK1bits = 0x424;
 SPI2IMSKL    = 0x424;
_SPI2IMSKL    = 0x424;
_SPI2IMSKLbits = 0x424;
 SPI2IMSK2    = 0x426;
_SPI2IMSK2    = 0x426;
_SPI2IMSK2bits = 0x426;
 SPI2IMSKH    = 0x426;
_SPI2IMSKH    = 0x426;
_SPI2IMSKHbits = 0x426;
 SPI2URDTL    = 0x428;
_SPI2URDTL    = 0x428;
_SPI2URDTLbits = 0x428;
 SPI2URDTH    = 0x42A;
_SPI2URDTH    = 0x42A;
_SPI2URDTHbits = 0x42A;
 CLC1CONL     = 0x464;
_CLC1CONL     = 0x464;
_CLC1CONLbits = 0x464;
 CLC1CONH     = 0x466;
_CLC1CONH     = 0x466;
_CLC1CONHbits = 0x466;
 CLC1SEL      = 0x468;
_CLC1SEL      = 0x468;
_CLC1SELbits  = 0x468;
 CLC1SELL     = 0x468;
_CLC1SELL     = 0x468;
_CLC1SELLbits = 0x468;
 CLC1GLSL     = 0x46C;
_CLC1GLSL     = 0x46C;
_CLC1GLSLbits = 0x46C;
 CLC1GLSH     = 0x46E;
_CLC1GLSH     = 0x46E;
_CLC1GLSHbits = 0x46E;
 CLC2CONL     = 0x470;
_CLC2CONL     = 0x470;
_CLC2CONLbits = 0x470;
 CLC2CONH     = 0x472;
_CLC2CONH     = 0x472;
_CLC2CONHbits = 0x472;
 CLC2SEL      = 0x474;
_CLC2SEL      = 0x474;
_CLC2SELbits  = 0x474;
 CLC2SELL     = 0x474;
_CLC2SELL     = 0x474;
_CLC2SELLbits = 0x474;
 CLC2GLSL     = 0x478;
_CLC2GLSL     = 0x478;
_CLC2GLSLbits = 0x478;
 CLC2GLSH     = 0x47A;
_CLC2GLSH     = 0x47A;
_CLC2GLSHbits = 0x47A;
 CLC3CONL     = 0x47C;
_CLC3CONL     = 0x47C;
_CLC3CONLbits = 0x47C;
 CLC3CONH     = 0x47E;
_CLC3CONH     = 0x47E;
_CLC3CONHbits = 0x47E;
 CLC3SEL      = 0x480;
_CLC3SEL      = 0x480;
_CLC3SELbits  = 0x480;
 CLC3SELL     = 0x480;
_CLC3SELL     = 0x480;
_CLC3SELLbits = 0x480;
 CLC3GLSL     = 0x484;
_CLC3GLSL     = 0x484;
_CLC3GLSLbits = 0x484;
 CLC3GLSH     = 0x486;
_CLC3GLSH     = 0x486;
_CLC3GLSHbits = 0x486;
 CLC4CONL     = 0x488;
_CLC4CONL     = 0x488;
_CLC4CONLbits = 0x488;
 CLC4CONH     = 0x48A;
_CLC4CONH     = 0x48A;
_CLC4CONHbits = 0x48A;
 CLC4SEL      = 0x48C;
_CLC4SEL      = 0x48C;
_CLC4SELbits  = 0x48C;
 CLC4SELL     = 0x48C;
_CLC4SELL     = 0x48C;
_CLC4SELLbits = 0x48C;
 CLC4GLSL     = 0x490;
_CLC4GLSL     = 0x490;
_CLC4GLSLbits = 0x490;
 CLC4GLSH     = 0x492;
_CLC4GLSH     = 0x492;
_CLC4GLSHbits = 0x492;
 I2C1RCV      = 0x494;
_I2C1RCV      = 0x494;
_I2C1RCVbits  = 0x494;
 I2C1TRN      = 0x496;
_I2C1TRN      = 0x496;
_I2C1TRNbits  = 0x496;
 I2C1BRG      = 0x498;
_I2C1BRG      = 0x498;
 I2C1CON1     = 0x49A;
_I2C1CON1     = 0x49A;
_I2C1CON1bits = 0x49A;
 I2C1CONL     = 0x49A;
_I2C1CONL     = 0x49A;
_I2C1CONLbits = 0x49A;
 I2C1CON2     = 0x49C;
_I2C1CON2     = 0x49C;
_I2C1CON2bits = 0x49C;
 I2C1CONH     = 0x49C;
_I2C1CONH     = 0x49C;
_I2C1CONHbits = 0x49C;
 I2C1STAT     = 0x49E;
_I2C1STAT     = 0x49E;
_I2C1STATbits = 0x49E;
 I2C1ADD      = 0x4A0;
_I2C1ADD      = 0x4A0;
_I2C1ADDbits  = 0x4A0;
 I2C1MSK      = 0x4A2;
_I2C1MSK      = 0x4A2;
_I2C1MSKbits  = 0x4A2;
 I2C2RCV      = 0x4A4;
_I2C2RCV      = 0x4A4;
_I2C2RCVbits  = 0x4A4;
 I2C2TRN      = 0x4A6;
_I2C2TRN      = 0x4A6;
_I2C2TRNbits  = 0x4A6;
 I2C2BRG      = 0x4A8;
_I2C2BRG      = 0x4A8;
 I2C2CON1     = 0x4AA;
_I2C2CON1     = 0x4AA;
_I2C2CON1bits = 0x4AA;
 I2C2CONL     = 0x4AA;
_I2C2CONL     = 0x4AA;
_I2C2CONLbits = 0x4AA;
 I2C2CON2     = 0x4AC;
_I2C2CON2     = 0x4AC;
_I2C2CON2bits = 0x4AC;
 I2C2CONH     = 0x4AC;
_I2C2CONH     = 0x4AC;
_I2C2CONHbits = 0x4AC;
 I2C2STAT     = 0x4AE;
_I2C2STAT     = 0x4AE;
_I2C2STATbits = 0x4AE;
 I2C2ADD      = 0x4B0;
_I2C2ADD      = 0x4B0;
_I2C2ADDbits  = 0x4B0;
 I2C2MSK      = 0x4B2;
_I2C2MSK      = 0x4B2;
_I2C2MSKbits  = 0x4B2;
 DMACON       = 0x4C4;
_DMACON       = 0x4C4;
_DMACONbits   = 0x4C4;
 DMABUF       = 0x4C6;
_DMABUF       = 0x4C6;
 DMAL         = 0x4C8;
_DMAL         = 0x4C8;
 DMAH         = 0x4CA;
_DMAH         = 0x4CA;
 DMACH0       = 0x4CC;
_DMACH0       = 0x4CC;
_DMACH0bits   = 0x4CC;
 DMAINT0      = 0x4CE;
_DMAINT0      = 0x4CE;
_DMAINT0bits  = 0x4CE;
 DMASRC0      = 0x4D0;
_DMASRC0      = 0x4D0;
 DMADST0      = 0x4D2;
_DMADST0      = 0x4D2;
 DMACNT0      = 0x4D4;
_DMACNT0      = 0x4D4;
 DMACH1       = 0x4D6;
_DMACH1       = 0x4D6;
_DMACH1bits   = 0x4D6;
 DMAINT1      = 0x4D8;
_DMAINT1      = 0x4D8;
_DMAINT1bits  = 0x4D8;
 DMASRC1      = 0x4DA;
_DMASRC1      = 0x4DA;
 DMADST1      = 0x4DC;
_DMADST1      = 0x4DC;
 DMACNT1      = 0x4DE;
_DMACNT1      = 0x4DE;
 U1OTGIR      = 0x600;
_U1OTGIR      = 0x600;
_U1OTGIRbits  = 0x600;
 U1OTGIE      = 0x602;
_U1OTGIE      = 0x602;
_U1OTGIEbits  = 0x602;
 U1OTGSTAT    = 0x604;
_U1OTGSTAT    = 0x604;
_U1OTGSTATbits = 0x604;
 U1OTGCON     = 0x606;
_U1OTGCON     = 0x606;
_U1OTGCONbits = 0x606;
 U1PWRC       = 0x608;
_U1PWRC       = 0x608;
_U1PWRCbits   = 0x608;
 U1IR         = 0x60A;
_U1IR         = 0x60A;
_U1IRbits     = 0x60A;
 U1IE         = 0x60C;
_U1IE         = 0x60C;
_U1IEbits     = 0x60C;
 U1EIR        = 0x60E;
_U1EIR        = 0x60E;
_U1EIRbits    = 0x60E;
 U1EIE        = 0x610;
_U1EIE        = 0x610;
_U1EIEbits    = 0x610;
 U1STAT       = 0x612;
_U1STAT       = 0x612;
_U1STATbits   = 0x612;
 U1CON        = 0x614;
_U1CON        = 0x614;
_U1CONbits    = 0x614;
 U1ADDR       = 0x616;
_U1ADDR       = 0x616;
_U1ADDRbits   = 0x616;
 U1BDTP1      = 0x618;
_U1BDTP1      = 0x618;
_U1BDTP1bits  = 0x618;
 U1FRML       = 0x61A;
_U1FRML       = 0x61A;
_U1FRMLbits   = 0x61A;
 U1FRMH       = 0x61C;
_U1FRMH       = 0x61C;
_U1FRMHbits   = 0x61C;
 U1TOK        = 0x61E;
_U1TOK        = 0x61E;
_U1TOKbits    = 0x61E;
 U1SOF        = 0x620;
_U1SOF        = 0x620;
_U1SOFbits    = 0x620;
 U1BDTP2      = 0x622;
_U1BDTP2      = 0x622;
_U1BDTP2bits  = 0x622;
 U1BDTP3      = 0x624;
_U1BDTP3      = 0x624;
_U1BDTP3bits  = 0x624;
 U1CNFG1      = 0x626;
_U1CNFG1      = 0x626;
_U1CNFG1bits  = 0x626;
 U1CNFG2      = 0x628;
_U1CNFG2      = 0x628;
_U1CNFG2bits  = 0x628;
 U1EP0        = 0x62A;
_U1EP0        = 0x62A;
_U1EP0bits    = 0x62A;
 U1EP1        = 0x62C;
_U1EP1        = 0x62C;
_U1EP1bits    = 0x62C;
 U1EP2        = 0x62E;
_U1EP2        = 0x62E;
_U1EP2bits    = 0x62E;
 U1EP3        = 0x630;
_U1EP3        = 0x630;
_U1EP3bits    = 0x630;
 U1EP4        = 0x632;
_U1EP4        = 0x632;
_U1EP4bits    = 0x632;
 U1EP5        = 0x634;
_U1EP5        = 0x634;
_U1EP5bits    = 0x634;
 U1EP6        = 0x636;
_U1EP6        = 0x636;
_U1EP6bits    = 0x636;
 U1EP7        = 0x638;
_U1EP7        = 0x638;
_U1EP7bits    = 0x638;
 U1EP8        = 0x63A;
_U1EP8        = 0x63A;
_U1EP8bits    = 0x63A;
 U1EP9        = 0x63C;
_U1EP9        = 0x63C;
_U1EP9bits    = 0x63C;
 U1EP10       = 0x63E;
_U1EP10       = 0x63E;
_U1EP10bits   = 0x63E;
 U1EP11       = 0x640;
_U1EP11       = 0x640;
_U1EP11bits   = 0x640;
 U1EP12       = 0x642;
_U1EP12       = 0x642;
_U1EP12bits   = 0x642;
 U1EP13       = 0x644;
_U1EP13       = 0x644;
_U1EP13bits   = 0x644;
 U1EP14       = 0x646;
_U1EP14       = 0x646;
_U1EP14bits   = 0x646;
 U1EP15       = 0x648;
_U1EP15       = 0x648;
_U1EP15bits   = 0x648;
 PADCON       = 0x65E;
_PADCON       = 0x65E;
_PADCONbits   = 0x65E;
 IOCSTAT      = 0x660;
_IOCSTAT      = 0x660;
_IOCSTATbits  = 0x660;
 TRISA        = 0x662;
_TRISA        = 0x662;
_TRISAbits    = 0x662;
 PORTA        = 0x664;
_PORTA        = 0x664;
_PORTAbits    = 0x664;
 LATA         = 0x666;
_LATA         = 0x666;
_LATAbits     = 0x666;
 ODCA         = 0x668;
_ODCA         = 0x668;
_ODCAbits     = 0x668;
 ANSA         = 0x66A;
_ANSA         = 0x66A;
_ANSAbits     = 0x66A;
 ANSELA       = 0x66A;
_ANSELA       = 0x66A;
_ANSELAbits   = 0x66A;
 IOCPA        = 0x66C;
_IOCPA        = 0x66C;
_IOCPAbits    = 0x66C;
 IOCNA        = 0x66E;
_IOCNA        = 0x66E;
_IOCNAbits    = 0x66E;
 IOCFA        = 0x670;
_IOCFA        = 0x670;
_IOCFAbits    = 0x670;
 CNPUA        = 0x672;
_CNPUA        = 0x672;
_CNPUAbits    = 0x672;
 IOCPUA       = 0x672;
_IOCPUA       = 0x672;
_IOCPUAbits   = 0x672;
 CNPDA        = 0x674;
_CNPDA        = 0x674;
_CNPDAbits    = 0x674;
 IOCPDA       = 0x674;
_IOCPDA       = 0x674;
_IOCPDAbits   = 0x674;
 TRISB        = 0x676;
_TRISB        = 0x676;
_TRISBbits    = 0x676;
 PORTB        = 0x678;
_PORTB        = 0x678;
_PORTBbits    = 0x678;
 LATB         = 0x67A;
_LATB         = 0x67A;
_LATBbits     = 0x67A;
 ODCB         = 0x67C;
_ODCB         = 0x67C;
_ODCBbits     = 0x67C;
 ANSB         = 0x67E;
_ANSB         = 0x67E;
_ANSBbits     = 0x67E;
 ANSELB       = 0x67E;
_ANSELB       = 0x67E;
_ANSELBbits   = 0x67E;
 IOCPB        = 0x680;
_IOCPB        = 0x680;
_IOCPBbits    = 0x680;
 IOCNB        = 0x682;
_IOCNB        = 0x682;
_IOCNBbits    = 0x682;
 IOCFB        = 0x684;
_IOCFB        = 0x684;
_IOCFBbits    = 0x684;
 CNPUB        = 0x686;
_CNPUB        = 0x686;
_CNPUBbits    = 0x686;
 IOCPUB       = 0x686;
_IOCPUB       = 0x686;
_IOCPUBbits   = 0x686;
 CNPDB        = 0x688;
_CNPDB        = 0x688;
_CNPDBbits    = 0x688;
 IOCPDB       = 0x688;
_IOCPDB       = 0x688;
_IOCPDBbits   = 0x688;
 TRISC        = 0x68A;
_TRISC        = 0x68A;
_TRISCbits    = 0x68A;
 PORTC        = 0x68C;
_PORTC        = 0x68C;
_PORTCbits    = 0x68C;
 LATC         = 0x68E;
_LATC         = 0x68E;
_LATCbits     = 0x68E;
 ODCC         = 0x690;
_ODCC         = 0x690;
_ODCCbits     = 0x690;
 ANSC         = 0x692;
_ANSC         = 0x692;
_ANSCbits     = 0x692;
 ANSELC       = 0x692;
_ANSELC       = 0x692;
_ANSELCbits   = 0x692;
 IOCPC        = 0x694;
_IOCPC        = 0x694;
_IOCPCbits    = 0x694;
 IOCNC        = 0x696;
_IOCNC        = 0x696;
_IOCNCbits    = 0x696;
 IOCFC        = 0x698;
_IOCFC        = 0x698;
_IOCFCbits    = 0x698;
 CNPUC        = 0x69A;
_CNPUC        = 0x69A;
_CNPUCbits    = 0x69A;
 IOCPUC       = 0x69A;
_IOCPUC       = 0x69A;
_IOCPUCbits   = 0x69A;
 CNPDC        = 0x69C;
_CNPDC        = 0x69C;
_CNPDCbits    = 0x69C;
 IOCPDC       = 0x69C;
_IOCPDC       = 0x69C;
_IOCPDCbits   = 0x69C;
 ADC1BUF0     = 0x700;
_ADC1BUF0     = 0x700;
 ADC1BUF1     = 0x702;
_ADC1BUF1     = 0x702;
 ADC1BUF2     = 0x704;
_ADC1BUF2     = 0x704;
 ADC1BUF3     = 0x706;
_ADC1BUF3     = 0x706;
 ADC1BUF4     = 0x708;
_ADC1BUF4     = 0x708;
 ADC1BUF5     = 0x70A;
_ADC1BUF5     = 0x70A;
 ADC1BUF6     = 0x70C;
_ADC1BUF6     = 0x70C;
 ADC1BUF7     = 0x70E;
_ADC1BUF7     = 0x70E;
 ADC1BUF9     = 0x712;
_ADC1BUF9     = 0x712;
 ADC1BUF10    = 0x714;
_ADC1BUF10    = 0x714;
 ADC1BUF11    = 0x716;
_ADC1BUF11    = 0x716;
 ADC1BUF12    = 0x718;
_ADC1BUF12    = 0x718;
 ADC1BUF13    = 0x71A;
_ADC1BUF13    = 0x71A;
 AD1CON1      = 0x734;
_AD1CON1      = 0x734;
_AD1CON1bits  = 0x734;
 AD1CON2      = 0x736;
_AD1CON2      = 0x736;
_AD1CON2bits  = 0x736;
 AD1CON3      = 0x738;
_AD1CON3      = 0x738;
_AD1CON3bits  = 0x738;
 AD1CHS       = 0x73A;
_AD1CHS       = 0x73A;
_AD1CHSbits   = 0x73A;
 AD1CHS0      = 0x73A;
_AD1CHS0      = 0x73A;
_AD1CHS0bits  = 0x73A;
 AD1CSSH      = 0x73C;
_AD1CSSH      = 0x73C;
_AD1CSSHbits  = 0x73C;
 AD1CSSL      = 0x73E;
_AD1CSSL      = 0x73E;
_AD1CSSLbits  = 0x73E;
 AD1CON4      = 0x740;
_AD1CON4      = 0x740;
_AD1CON4bits  = 0x740;
 AD1CON5      = 0x742;
_AD1CON5      = 0x742;
_AD1CON5bits  = 0x742;
 AD1CHITH     = 0x744;
_AD1CHITH     = 0x744;
 AD1CHITL     = 0x746;
_AD1CHITL     = 0x746;
_AD1CHITLbits = 0x746;
 AD1DMBUF     = 0x74C;
_AD1DMBUF     = 0x74C;
_AD1DMBUFbits = 0x74C;
 AD1RESDMA    = 0x74C;
_AD1RESDMA    = 0x74C;
_AD1RESDMAbits = 0x74C;
 NVMCON       = 0x760;
_NVMCON       = 0x760;
_NVMCONbits   = 0x760;
 NVMADR       = 0x762;
_NVMADR       = 0x762;
_NVMADRbits   = 0x762;
 NVMADRL      = 0x762;
_NVMADRL      = 0x762;
_NVMADRLbits  = 0x762;
 NVMADRH      = 0x764;
_NVMADRH      = 0x764;
_NVMADRHbits  = 0x764;
 NVMADRU      = 0x764;
_NVMADRU      = 0x764;
_NVMADRUbits  = 0x764;
 NVMKEY       = 0x766;
_NVMKEY       = 0x766;
 ECCCONL      = 0x76C;
_ECCCONL      = 0x76C;
_ECCCONLbits  = 0x76C;
 ECCCONH      = 0x76E;
_ECCCONH      = 0x76E;
_ECCCONHbits  = 0x76E;
 ECCADDRL     = 0x770;
_ECCADDRL     = 0x770;
 ECCADDRH     = 0x772;
_ECCADDRH     = 0x772;
 ECCSTATL     = 0x774;
_ECCSTATL     = 0x774;
_ECCSTATLbits = 0x774;
 ECCSTATH     = 0x776;
_ECCSTATH     = 0x776;
_ECCSTATHbits = 0x776;
 RPINR0       = 0x790;
_RPINR0       = 0x790;
_RPINR0bits   = 0x790;
 RPINR1       = 0x792;
_RPINR1       = 0x792;
_RPINR1bits   = 0x792;
 RPINR2       = 0x794;
_RPINR2       = 0x794;
_RPINR2bits   = 0x794;
 RPINR3       = 0x796;
_RPINR3       = 0x796;
_RPINR3bits   = 0x796;
 RPINR5       = 0x79A;
_RPINR5       = 0x79A;
_RPINR5bits   = 0x79A;
 RPINR6       = 0x79C;
_RPINR6       = 0x79C;
_RPINR6bits   = 0x79C;
 RPINR11      = 0x7A6;
_RPINR11      = 0x7A6;
_RPINR11bits  = 0x7A6;
 RPINR12      = 0x7A8;
_RPINR12      = 0x7A8;
_RPINR12bits  = 0x7A8;
 RPINR13      = 0x7AA;
_RPINR13      = 0x7AA;
_RPINR13bits  = 0x7AA;
 RPINR14      = 0x7AC;
_RPINR14      = 0x7AC;
_RPINR14bits  = 0x7AC;
 RPINR18      = 0x7B4;
_RPINR18      = 0x7B4;
_RPINR18bits  = 0x7B4;
 RPINR19      = 0x7B6;
_RPINR19      = 0x7B6;
_RPINR19bits  = 0x7B6;
 RPINR20      = 0x7B8;
_RPINR20      = 0x7B8;
_RPINR20bits  = 0x7B8;
 RPINR21      = 0x7BA;
_RPINR21      = 0x7BA;
_RPINR21bits  = 0x7BA;
 RPINR22      = 0x7BC;
_RPINR22      = 0x7BC;
_RPINR22bits  = 0x7BC;
 RPINR23      = 0x7BE;
_RPINR23      = 0x7BE;
_RPINR23bits  = 0x7BE;
 RPINR25      = 0x7C2;
_RPINR25      = 0x7C2;
_RPINR25bits  = 0x7C2;
 RPINR26      = 0x7C4;
_RPINR26      = 0x7C4;
_RPINR26bits  = 0x7C4;
 RPOR0        = 0x7D4;
_RPOR0        = 0x7D4;
_RPOR0bits    = 0x7D4;
 RPOR1        = 0x7D6;
_RPOR1        = 0x7D6;
_RPOR1bits    = 0x7D6;
 RPOR2        = 0x7D8;
_RPOR2        = 0x7D8;
_RPOR2bits    = 0x7D8;
 RPOR3        = 0x7DA;
_RPOR3        = 0x7DA;
_RPOR3bits    = 0x7DA;
 RPOR4        = 0x7DC;
_RPOR4        = 0x7DC;
_RPOR4bits    = 0x7DC;
 RPOR5        = 0x7DE;
_RPOR5        = 0x7DE;
_RPOR5bits    = 0x7DE;
 RPOR6        = 0x7E0;
_RPOR6        = 0x7E0;
_RPOR6bits    = 0x7E0;
 RPOR7        = 0x7E2;
_RPOR7        = 0x7E2;
_RPOR7bits    = 0x7E2;
 RPOR8        = 0x7E4;
_RPOR8        = 0x7E4;
_RPOR8bits    = 0x7E4;
 RPOR9        = 0x7E6;
_RPOR9        = 0x7E6;
_RPOR9bits    = 0x7E6;
 RPOR10       = 0x7E8;
_RPOR10       = 0x7E8;
_RPOR10bits   = 0x7E8;
 RPOR11       = 0x7EA;
_RPOR11       = 0x7EA;
_RPOR11bits   = 0x7EA;
 RPOR12       = 0x7EC;
_RPOR12       = 0x7EC;
_RPOR12bits   = 0x7EC;
 RPOR13       = 0x7EE;
_RPOR13       = 0x7EE;
_RPOR13bits   = 0x7EE;
 RPOR14       = 0x7F0;
_RPOR14       = 0x7F0;
_RPOR14bits   = 0x7F0;
/*
** ======= Base Addresses for Various Peripherals and ACC ======
*/

 UART1        = 0x398;
_UART1        = 0x398;
 UART2        = 0x3AE;
_UART2        = 0x3AE;
