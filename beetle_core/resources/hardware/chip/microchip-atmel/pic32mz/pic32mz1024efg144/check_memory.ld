/***********************************************************************
 *
 * This script checks if memory regions definef in target_memory.ld overlap.
 *
 * We need to manually check if memory regions overlap because linker
 * can't detect overlapping due to different VMA and LMA addresses of
 * the output sections (see "3.6.8.2 Output Section LMA" in "The GNU
 * Linker")
 *
 **********************************************************************/

/* get start and end address of each memory region,
 * convert all start variables to physical address. */
s_rom    = ORIGIN(ROM)    & 0x1FFFFFFF;
e_rom    = LENGTH(ROM)    + s_rom;

s_status = ORIGIN(STATUS) & 0x1FFFFFFF;
e_status = LENGTH(STATUS) + s_status;

s_data   = ORIGIN(DATA)   & 0x1FFFFFFF;
e_data   = LENGTH(DATA)   + s_data;

s_stack  = ORIGIN(STACK)  & 0x1FFFFFFF;
e_stack  = LENGTH(STACK)  + s_stack;

/* check ROM overlappings */
ASSERT( ( (e_rom > s_status) && (s_rom < e_status) ) == 0, "ROM overlaps with STATUS, check MEMORY definition in target_memory.ld" );
ASSERT( ( (e_rom > s_data)   && (s_rom < e_data)   ) == 0, "ROM overlaps with DATA, check MEMORY definition in target_memory.ld" );
ASSERT( ( (e_rom > s_stack)  && (s_rom < e_stack)  ) == 0, "ROM overlaps with STACK, check MEMORY definition in target_memory.ld" );

/* check DATA overlappings (no need to check overlapping with ROM) */
ASSERT( ( (e_data > s_status) && (s_data < e_status) ) == 0, "DATA overlaps with STATUS, check MEMORY definition in target_memory.ld" );
ASSERT( ( (e_data > s_stack)  && (s_data < e_stack)  ) == 0, "DATA overlaps with STACK, check MEMORY definition in target_memory.ld" );

/* check STATUS and STACK overlapping */
ASSERT( ( (e_status > s_stack) && (s_status < e_stack) ) == 0, "STATUS overlaps with STACK, check MEMORY definition in target_memory.ld" );
