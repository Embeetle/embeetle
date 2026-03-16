Trick to determine the linkerscript for an Arduino board
========================================================

1) Create a file named: `linkerscript_{chip.get_chip_enum().get_mmcu()}.ld`
   The content doesn't matter for now.

2) Generate an embeetle project.

3) Open `dashboard.mk` and delete the references to the linkerscript. Add a line
   to increase verbosity instead:
   ```
   TARGET_LDFLAGS = -w \
                    -flto \
                    -fuse-linker-plugin \
                    -Wl,--verbose \
                    # -T $(LINKERSCRIPT) \
                    # -L $(dir $(LINKERSCRIPT)) \
                    # -L $(MAKEFILE_DIR) \
   ```

4) Run a build. The used linkerscript will be printed out in the output (even
   its content as well). That's because the avr toolchain determins the linker-
   script automatically based on the `-mmcu` flag. More info see:
   https://stackoverflow.com/questions/64898849/what-linkerscript-does-arduino-ide-use-when-compiling-for-the-arduino-uno