/*
 * cmsdk_cm0_flash_rom.ld
 * Linker script for Sydney FLASHROM
 *
 * Copyright (C) Atmosic 2018-2019
 */

INCLUDE "lib-nosys.ld"
INCLUDE "memory_flash_rom.ld"

__NVDS_Flash = ORIGIN(NVDS);
__NVDS_FlashEnd = ORIGIN(NVDS) + LENGTH(NVDS);

__User_Flash = ORIGIN(USER);
__User_FlashEnd = ORIGIN(USER) + LENGTH(USER);

INCLUDE "sections.ld"
