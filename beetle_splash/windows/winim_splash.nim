
#[
    Copyright (c) 2018-2021 Embeetle.
]#

import
    os,
    osproc,
    parseopt,
    strutils,
    winim/lean

var
    hBitmap: HBITMAP
    first_run = true
    timeout_flag = false
    quit_flag = false
    quit_flag_pointer: ptr bool = addr(quit_flag)

proc WindowProc(hwnd: HWND, message: UINT, wParam: WPARAM, lParam: LPARAM): LRESULT {.stdcall.} =
    case message
    of WM_PAINT:
        var
            ps: PAINTSTRUCT
            hdc = BeginPaint(hwnd, ps)
            bitmap: BITMAP
            hdcMem: HDC
            oldBitmap: HGDIOBJ
        defer: EndPaint(hwnd, ps)
    
        hdcMem = CreateCompatibleDC(hdc)
        oldBitmap = SelectObject(hdcMem, hBitmap)
    
        GetObject(hBitmap, int32(sizeof(bitmap)), addr(bitmap))
        BitBlt(hdc, 0, 0, bitmap.bmWidth, bitmap.bmHeight, hdcMem, 0, 0, SRCCOPY)
        SelectObject(hdcMem, oldBitmap)
        DeleteDC(hdcMem)
        
        var
            rect: RECT
            msg: string
        if timeout_flag:
            msg = "Timeout exceeded! Please contact support or try again."
        else:
            if first_run:
                msg = "This is first time you run Embeetle.\nPlease wait for Windows to check the signatures ..."
            else:
                msg = "Embeetle is starting up ..."
        GetClientRect(hwnd, rect)
        let hFont = CreateFont(
            0,
            0,
            0,
            0,
            FW_BOLD,
            false,
            false,
            false,
            DEFAULT_CHARSET,
            OUT_OUTLINE_PRECIS,
            CLIP_DEFAULT_PRECIS,
            CLEARTYPE_QUALITY,
            VARIABLE_PITCH,
            "SourceCodePro-Bold" #"Consolas"
        )
        SelectObject(hdc, hFont)
        DrawText(
            hdc,
            msg,
            -1,
            rect,
            DT_NOCLIP or DT_CENTER or DT_BOTTOM #DT_SINGLELINE or DT_NOCLIP or DT_CENTER or DT_BOTTOM
        )
        return 0

    of WM_DESTROY:
        PostQuitMessage(0)
        return 0

    else:
        return DefWindowProc(hwnd, message, wParam, lParam)

proc clean_error_file() =
    let error_file = os.joinPath(getAppDir(), "error.btl")
    if os.fileExists(error_file):
        os.removeFile(error_file)

proc write_error(msg: string) =
    let
        error_file = os.joinPath(getAppDir(), "error.btl")
#        f = open(error_file, fmWrite)
        f = open(error_file, fmAppend)
    defer: f.close()
    f.writeLine(msg)

proc threadFunc(data: tuple[hwnd: HWND, timeout_flag: ptr bool, cmd_parameters: seq[string]]) {.thread.} =
    let
        embeetle_home_directory = os.joinPath(getHomeDir(), ".embeetle")
        embeetle_core_directory = os.joinPath(getAppDir(), "beetle_core")
        embeetle_executable = os.joinPath(embeetle_core_directory, "beetle_core.exe")
        check_file = os.joinPath(embeetle_home_directory, "startup.btl")
    # Delete the error file if needed
    clean_error_file()
    # Check if you are in the right place
    if not os.dirExists(embeetle_core_directory):
        write_error("!! This is not the top-level Embeetle directory !!")
#        quit()
        quit_flag_pointer[] = true
        return
    # Check the Embeetle home directory
    if not os.dirExists(embeetle_home_directory):
        os.createDir(embeetle_home_directory)
    # Check the test file
    if os.fileExists(check_file):
        os.removeFile(check_file)
    # Run Embeetle
    if os.fileExists(embeetle_executable):
        discard osproc.startProcess(embeetle_executable, args=data[2], workingDir=embeetle_core_directory)
        sleep(500)
    else:
        write_error("Embeetle executable doesn't exist!")
    # Wait until the test file is deleted
    var cnt = 60
    if first_run:
        cnt = 360
    while not os.fileExists(check_file) and cnt > 0:
        sleep(500)
        cnt -= 1
        if cnt == 0:
            data[1][] = true
            write_error("The main Embeetle application took too long to respond!")
            sleep(2000)
    # Clean up the test file
    if os.fileExists(check_file):
        os.removeFile(check_file)
    
    # Close
#    quit()
    quit_flag_pointer[] = true

proc main() =
    let
        embeetle_home_directory = os.joinPath(getHomeDir(), ".embeetle")
    
    var
        hInstance = GetModuleHandle(nil)
        appName = "EmbeetleSplash"
        hwnd: HWND
        msg: MSG
        wndclass: WNDCLASS
        thr: Thread[tuple[hwnd: HWND, timeout_flag: ptr bool, cmd_parameters: seq[string]]]
        imageResHandle: HRSRC
    
    if dirExists(embeetle_home_directory):
        first_run = false
    
    createThread(thr, threadFunc, (hwnd, addr(timeout_flag), os.commandLineParams()))
    
    imageResHandle = FindResource(
        0,             # This component.
        LPCWSTR("SPLASH"),   # Resource name.
        RT_BITMAP)        # Resource type.
    if imageResHandle == FALSE:
        raise newException(OSError, "Error loading image from resource!")
  
    hBitmap = LoadImage(
        hInstance,
        LPCWSTR("SPLASH"), #"splash_screen.bmp",
        IMAGE_BITMAP,
        0,
        0,
        0, #LR_LOADFROMFILE
    )
    if hBitmap == FALSE:
        raise newException(OSError, "Error loading image!")
    
    wndclass.style = CS_HREDRAW or CS_VREDRAW
    wndclass.lpfnWndProc = WindowProc
    wndclass.cbClsExtra = 0
    wndclass.cbWndExtra = 0
    wndclass.hInstance = hInstance
    #  wndclass.hIcon = LoadIcon(0, IDI_APPLICATION)
    wndclass.hIcon = LoadIcon(0, MAKEINTRESOURCE(1))
    wndclass.hCursor = LoadCursor(0, IDC_ARROW)
    wndclass.hbrBackground = GetStockObject(WHITE_BRUSH)
    wndclass.lpszMenuName = nil
    wndclass.lpszClassName = appName
    
    if RegisterClass(wndclass) == 0:
        MessageBox(0, "This program requires Windows NT!", appName, MB_ICONERROR)
        return
    
    let
        screen_width = GetSystemMetrics(SM_CXSCREEN)
        screen_height = GetSystemMetrics(SM_CYSCREEN)
        width = 500.int32
        height = 100.int32
        position_x = int32(screen_width/2 - width/2)
        position_y = int32(screen_height/2 - height/2)
    
    # Load font file
    let
        embeetle_font_directory = os.joinPath(getAppDir(), "beetle_core/resources/fonts")
        font_file = os.joinPath(embeetle_font_directory, "SourceCodePro/SourceCodePro-Bold.ttf")
    if AddFontResourceW(font_file) == 0:
        write_error("!! The font file '" & font_file & "' could not be loaded !!")
        quit()
    # Clean up font resource from Windows on exit
    defer:
        if RemoveFontResourceW(font_file) == 0:
            write_error("!! The font file '" & font_file & "' could not be unloaded !!")
    
    hwnd = CreateWindow(
        appName,
        "Embeetle splash",
        WS_POPUP or WS_OVERLAPPED or WS_SYSMENU or WS_MAXIMIZEBOX or WS_MINIMIZEBOX or WS_EX_TOPMOST,
        position_x,
        position_y,
        width,
        height,
        0,
        0,
        hInstance,
        nil
    )
    SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        0,
        0,
        0,
        0,
        SWP_NOMOVE or SWP_NOSIZE
    )

    ShowWindow(hwnd, SW_SHOW)
    UpdateWindow(hwnd)
    
    var flag_change = false
    while GetMessage(msg, 0, 0, 0) != 0 and not quit_flag:
        TranslateMessage(msg)
        DispatchMessage(msg)
        if timeout_flag and not flag_change:
            RedrawWindow(hwnd, nil, HRGN(0), RDW_INVALIDATE or RDW_INTERNALPAINT)
            flag_change = true

proc just_start() =
    let
        embeetle_home_directory = os.joinPath(getHomeDir(), ".embeetle")
        embeetle_core_directory = os.joinPath(getAppDir(), "beetle_core")
        embeetle_executable = os.joinPath(embeetle_core_directory, "beetle_core.exe")
        check_file = os.joinPath(embeetle_home_directory, "startup.btl")

    # Run Embeetle
    if os.fileExists(embeetle_executable):
        discard osproc.startProcess(
            embeetle_executable,
            args=os.commandLineParams(),
            workingDir=embeetle_core_directory
        )
    
    # Close
    quit()

if isMainModule:
#    just_start()
    main()