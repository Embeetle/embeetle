===========================================
|       STEPS FOR ARDUINO IMPORTER        |
===========================================

1. DELETE ALL TEMP FOLDERS
==========================
$ arduino-cli cache clean

Linux: /tmp/arduino_build_xxx    (from IDE)
       /tmp/arduino_cache_xxx    (from IDE)
       /tmp/arduino-core-cache   (from arduino-cli)
       /tmp/arduino-sketch-xxx   (from arduino-cli)

2. COMPILE WITH ARDUINO-CLI
===========================
Note: The standard AVR core might not yet be in the ~/.arduino15/ folder.
Then you need to issue the command:
$ arduino-cli core install arduino:avr

Compile the sketch:
$ arduino-cli compile --fqbn arduino:avr:uno ~/Arduino/Blink --verbose

3. EXTRACT INFO FROM COMPILATION OUTPUT
=======================================
3.1 extract sketch cpp-file
---------------------------
The following regex extracts the filepath to the .ino.cpp file:
regex = r"-o\s(.+[.]ino[.]cpp)[.]o"

example = "/tmp/arduino-sketch-8303805852C3F4A2B9C90C8384F7B83E/sketch/Blink.ino.cpp"


3.2 List all files
------------------
.S   => r"([\w]+[.]S)\s"
.c   => r"([\w]+[.]c)\s"
.cpp => r"([\w]+[.]cpp)\s"

Extract full path from a file, like Print.cpp:
regex = r"\s([\w\d/\.]*Print[.]cpp)\s"

================================================================================
cd /home/kristof/beetle_projects/foobar/build

/home/kristof/.arduino15/packages/esp32/tools/xtensa-esp32-elf-gcc/1.22.0-97-gc752ad5-5.2.0/bin/xtensa-esp32-elf-gcc

"/home/kristof/.embeetle/beetle_tools/gnu_xtensa_esp32_toolchain_5.2.0_1.22.0-97-gc752ad5_64b/bin/xtensa-esp32-elf-gcc" \
    -nostdlib \
    -L ../source/precompiled_libraries \
    -L ../config/ \
    -T esp32_out.ld \
    -T esp32.project.ld \
    -T esp32.rom.ld \
    -T esp32.peripherals.ld \
    -T esp32.rom.libgcc.ld \
    -T esp32.rom.spiram_incompatible_fns.ld \
    -u esp_app_desc \
    -u ld_include_panic_highint_hdl \
    -u call_user_start_cpu0 \
    -Wl,--gc-sections \
    -Wl,-static \
    -Wl,--undefined=uxTopUsedPriority \
    -u __cxa_guard_dummy \
    -u __cxx_fatal_exception \
    -Wl,--start-group \
    user_code/WiFiScan.ino.cpp.o \
    libraries/WiFi/src/ETH.cpp.o \
    libraries/WiFi/src/WiFi.cpp.o \
    libraries/WiFi/src/WiFiAP.cpp.o \
    libraries/WiFi/src/WiFiClient.cpp.o \
    libraries/WiFi/src/WiFiGeneric.cpp.o \
    libraries/WiFi/src/WiFiMulti.cpp.o \
    libraries/WiFi/src/WiFiSTA.cpp.o \
    libraries/WiFi/src/WiFiScan.cpp.o \
    libraries/WiFi/src/WiFiServer.cpp.o \
    libraries/WiFi/src/WiFiUdp.cpp.o \
    core/esp32/esp32-hal-adc.c.o \
    core/esp32/esp32-hal-bt.c.o \
    core/esp32/esp32-hal-cpu.c.o \
    core/esp32/esp32-hal-dac.c.o \
    core/esp32/esp32-hal-gpio.c.o \
    core/esp32/esp32-hal-i2c.c.o \
    core/esp32/esp32-hal-ledc.c.o \
    core/esp32/esp32-hal-log.c.o \
    core/esp32/esp32-hal-matrix.c.o \
    core/esp32/esp32-hal-misc.c.o \
    core/esp32/esp32-hal-psram.c.o \
    core/esp32/esp32-hal-rmt.c.o \
    core/esp32/esp32-hal-sigmadelta.c.o \
    core/esp32/esp32-hal-spi.c.o \
    core/esp32/esp32-hal-time.c.o \
    core/esp32/esp32-hal-timer.c.o \
    core/esp32/esp32-hal-touch.c.o \
    core/esp32/esp32-hal-uart.c.o \
    core/esp32/libb64/cdecode.c.o \
    core/esp32/libb64/cencode.c.o \
    core/esp32/stdlib_noniso.c.o \
    core/esp32/wiring_pulse.c.o \
    core/esp32/wiring_shift.c.o \
    core/esp32/Esp.cpp.o \
    core/esp32/FunctionalInterrupt.cpp.o \
    core/esp32/HardwareSerial.cpp.o \
    core/esp32/IPAddress.cpp.o \
    core/esp32/IPv6Address.cpp.o \
    core/esp32/MD5Builder.cpp.o \
    core/esp32/Print.cpp.o \
    core/esp32/Stream.cpp.o \
    core/esp32/StreamString.cpp.o \
    core/esp32/WMath.cpp.o \
    core/esp32/WString.cpp.o \
    core/esp32/base64.cpp.o \
    core/esp32/cbuf.cpp.o \
    core/esp32/main.cpp.o \
    -lgcc \
    -lesp_websocket_client \
    -lwpa2 \
    -ldetection \
    -lesp_https_server \
    -lwps \
    -lhal \
    -lconsole \
    -lpe \
    -lsoc \
    -lsdmmc \
    -lpthread \
    -llog \
    -lesp_http_client \
    -ljson \
    -lmesh \
    -lesp32-camera \
    -lnet80211 \
    -lwpa_supplicant \
    -lc \
    -lmqtt \
    -lcxx \
    -lesp_https_ota \
    -lulp \
    -lefuse \
    -lpp \
    -lmdns \
    -lbt \
    -lwpa \
    -lspiffs \
    -lheap \
    -limage_util \
    -lunity \
    -lrtc \
    -lmbedtls \
    -lface_recognition \
    -lnghttp \
    -ljsmn \
    -lopenssl \
    -lcore \
    -lfatfs \
    -lm \
    -lprotocomm \
    -lsmartconfig \
    -lxtensa-debug-module \
    -ldl \
    -lesp_event \
    -lesp-tls \
    -lfd \
    -lespcoredump \
    -lesp_http_server \
    -lfr \
    -lsmartconfig_ack \
    -lwear_levelling \
    -ltcp_transport \
    -llwip \
    -lphy \
    -lvfs \
    -lcoap \
    -lesp32 \
    -llibsodium \
    -lbootloader_support \
    -ldriver \
    -lcoexist \
    -lasio \
    -lod \
    -lmicro-ecc \
    -lesp_ringbuf \
    -ldetection_cat_face \
    -lapp_update \
    -lespnow \
    -lface_detection \
    -lapp_trace \
    -lnewlib \
    -lbtdm_app \
    -lwifi_provisioning \
    -lfreertos \
    -lfreemodbus \
    -lethernet \
    -lnvs_flash \
    -lspi_flash \
    -lc_nano \
    -lexpat \
    -lfb_gfx \
    -lprotobuf-c \
    -lesp_adc_cal \
    -ltcpip_adapter \
    -lstdc++ \
    -Wl,--end-group \
    -Wl,-EL \
    -o application.elf

COMPARE COMPILED FILES
======================
ARDUINO:                                EMBEETLE

/sketch/WiFiScan.ino.cpp.o              => user_code/WiFiScan.ino.cpp.o
/libraries/WiFi/ETH.cpp.o               => libraries/WiFi/src/ETH.cpp.o
/libraries/WiFi/WiFi.cpp.o              => libraries/WiFi/src/WiFi.cpp.o
/libraries/WiFi/WiFiAP.cpp.o            => libraries/WiFi/src/WiFiAP.cpp.o
/libraries/WiFi/WiFiClient.cpp.o        => libraries/WiFi/src/WiFiClient.cpp.o
/libraries/WiFi/WiFiGeneric.cpp.o       => libraries/WiFi/src/WiFiGeneric.cpp.o
/libraries/WiFi/WiFiMulti.cpp.o         => libraries/WiFi/src/WiFiMulti.cpp.o
/libraries/WiFi/WiFiSTA.cpp.o           => libraries/WiFi/src/WiFiSTA.cpp.o
/libraries/WiFi/WiFiScan.cpp.o          => libraries/WiFi/src/WiFiScan.cpp.o
/libraries/WiFi/WiFiServer.cpp.o        => libraries/WiFi/src/WiFiServer.cpp.o
/libraries/WiFi/WiFiUdp.cpp.o           => libraries/WiFi/src/WiFiUdp.cpp.o
/core/esp32-hal-adc.c.o                 => core/esp32/esp32-hal-adc.c.o
/core/esp32-hal-bt.c.o                  => core/esp32/esp32-hal-bt.c.o
/core/esp32-hal-cpu.c.o                 => core/esp32/esp32-hal-cpu.c.o
/core/esp32-hal-dac.c.o                 => core/esp32/esp32-hal-dac.c.o
/core/esp32-hal-gpio.c.o                => core/esp32/esp32-hal-gpio.c.o
/core/esp32-hal-i2c.c.o                 => core/esp32/esp32-hal-i2c.c.o
/core/esp32-hal-ledc.c.o                => core/esp32/esp32-hal-ledc.c.o
/core/esp32-hal-log.c.o                 => core/esp32/esp32-hal-log.c.o
/core/esp32-hal-matrix.c.o              => core/esp32/esp32-hal-matrix.c.o
/core/esp32-hal-misc.c.o                => core/esp32/esp32-hal-misc.c.o
/core/esp32-hal-psram.c.o               => core/esp32/esp32-hal-psram.c.o
/core/esp32-hal-rmt.c.o                 => core/esp32/esp32-hal-rmt.c.o
/core/esp32-hal-sigmadelta.c.o          => core/esp32/esp32-hal-sigmadelta.c.o
/core/esp32-hal-spi.c.o                 => core/esp32/esp32-hal-spi.c.o
/core/esp32-hal-time.c.o                => core/esp32/esp32-hal-time.c.o
/core/esp32-hal-timer.c.o               => core/esp32/esp32-hal-timer.c.o
/core/esp32-hal-touch.c.o               => core/esp32/esp32-hal-touch.c.o
/core/esp32-hal-uart.c.o                => core/esp32/esp32-hal-uart.c.o
/core/libb64/cdecode.c.o                => core/esp32/libb64/cdecode.c.o
/core/libb64/cencode.c.o                => core/esp32/libb64/cencode.c.o
/core/stdlib_noniso.c.o                 => core/esp32/stdlib_noniso.c.o
/core/wiring_pulse.c.o                  => core/esp32/wiring_pulse.c.o
/core/wiring_shift.c.o                  => core/esp32/wiring_shift.c.o
/core/Esp.cpp.o                         => core/esp32/Esp.cpp.o
/core/FunctionalInterrupt.cpp.o         => core/esp32/FunctionalInterrupt.cpp.o
/core/HardwareSerial.cpp.o              => core/esp32/HardwareSerial.cpp.o
/core/IPAddress.cpp.o                   => core/esp32/IPAddress.cpp.o
/core/IPv6Address.cpp.o                 => core/esp32/IPv6Address.cpp.o
/core/MD5Builder.cpp.o                  => core/esp32/MD5Builder.cpp.o
/core/Print.cpp.o                       => core/esp32/Print.cpp.o
/core/Stream.cpp.o                      => core/esp32/Stream.cpp.o
/core/StreamString.cpp.o                => core/esp32/StreamString.cpp.o
/core/WMath.cpp.o                       => core/esp32/WMath.cpp.o
/core/WString.cpp.o                     => core/esp32/WString.cpp.o
/core/base64.cpp.o                      => core/esp32/base64.cpp.o
/core/cbuf.cpp.o                        => core/esp32/cbuf.cpp.o
/core/main.cpp.o                        => core/esp32/main.cpp.o
