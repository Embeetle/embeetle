import strutils

mode = ScriptMode.Verbose

if defined(windows):
    var commands = [
        "C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Auxiliary/Build/vcvars64.bat",
        "cd /d " & thisDir(),
        "windres winim_splash.rs -O coff -o winim_splash.res",
        "nim c -d:release --showAllMismatches:on --threads:on --passL:winim_splash.res --passC:/O1 --opt:size --out:embeetle.exe winim_splash.nim",
        
        "mt.exe -nologo -manifest \"winim_splash.manifest\" -outputresource:\"embeetle.exe;#1\""
    ]
    writeFile("winim_splash.rs", "0 ICON \"beetle_face.ico\"\nSPLASH BITMAP \"splash_screen.bmp\"")
    
    exec commands.join(" & ")

else:
    echo "This is a Windows only program!"