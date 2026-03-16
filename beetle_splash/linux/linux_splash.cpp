
/*
    Copyright (c) 2018-2021 Embeetle
*/

#include <stdio.h>
#include <stdlib.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/Xutil.h>
#include <Imlib2.h>
#include <unistd.h>
#include <pwd.h>
#include <cstdlib>
#include <memory.h>
#include <dirent.h>
#include <errno.h>
#include <sys/stat.h>

char* join_paths(const char* path_0, const char* path_1)
{
    char* mergerd_path = (char *) malloc(
        1 + strlen(path_0) + 1 + strlen(path_1)
    );
    strcpy(mergerd_path, path_0);
    strcat(mergerd_path, "/");
    strcat(mergerd_path, path_1);
    return mergerd_path;
}

int file_exists(char* filename)
{
    FILE* file = fopen(filename, "r");
    if (file)
    {
        fclose(file);
        return 1;
    }
    return 0;
}

int directory_exists(const char* directory_name)
{
    DIR* directory = opendir(directory_name);
    if (directory)
    {
        closedir(directory);
        return 1;
    }
    return 0;
}

// Determine the Embeetle installation directory based on arg0,
// i.e. based on the path of this executable.
static char *get_install_dir_name(const char *arg0)
{
    const char *last_slash_in_arg0 = strrchr(arg0, '/');
    size_t install_dir_len = last_slash_in_arg0 ? last_slash_in_arg0 - arg0 + 1 : 0;
    char *install_dir = (char*)malloc(install_dir_len + 1);
    strncpy(install_dir, arg0, install_dir_len);
    install_dir[install_dir_len] = '\0';
    return install_dir;
}



int main(int argc, char *argv[])
{
    Imlib_Image  m_img;
    Display     *main_display;
    Pixmap       picture;
    Window       main_window;
    XEvent       e;
    Screen      *screen;
    int m_width, m_height;
    
    const char *image_file = "beetle_core/resources/icons/splash_screen.png";
//    const char *embeetle_executable = "beetle_core/beetle_core";
    const char *embeetle_executable = "beetle_core/embeetle";
    const char *startup_file = "startup.btl";
    
    // Get directories
    struct passwd *pw = getpwuid(getuid());
    const char* home_directory = pw->pw_dir;
    const char* install_directory = get_install_dir_name(argv[0]);
    const char* current_directory = get_current_dir_name();
    const char* embeetle_directory = join_paths(home_directory, ".embeetle");
    char* embeetle_executable_path = join_paths(install_directory, embeetle_executable);
    char* startup_file_path = join_paths(embeetle_directory, startup_file);
    char* image_path = join_paths(install_directory, image_file);
    
    if (false)
    {
        printf("Current directory: %s\n", current_directory);
        printf("Embeetle install directory: %s\n", install_directory);
        printf("Home directory: %s\n", home_directory);
        printf("Startup file: %s\n", startup_file_path);
        printf("Image file: %s\n", image_path);
    }
    
    // Check if Embeetle directory exists
    if (!directory_exists(embeetle_directory))
    {
        //printf("Embeetle directory does not exist, creating it ...");
        mkdir(embeetle_directory, 0777);
    }
    else if (file_exists(startup_file_path))
    {
        remove(startup_file_path);
    }
    else if (!file_exists(embeetle_executable_path))
    {
        printf("Core executable not found!\n");
        return 1;
    }
    else if (!file_exists(image_path))
    {
        printf("Splash image '%s' not found!\n", image_path);
        return 1;
    }
    

    m_img = imlib_load_image(image_path);
    if(!m_img)
    {
        printf("%s\n","init m_img failed");
    }
    imlib_context_set_image(m_img);
    m_width = imlib_image_get_width();
    m_height = imlib_image_get_height();

    main_display = XOpenDisplay(NULL);
    if(!main_display)
    {
        printf("%s\n","open display failed");
    }
    
    XVisualInfo vinfo;
    XMatchVisualInfo(main_display, DefaultScreen(main_display), 32, TrueColor, &vinfo);
    XSetWindowAttributes attr;
    attr.colormap = XCreateColormap(main_display, DefaultRootWindow(main_display), vinfo.visual, AllocNone);
    attr.border_pixel = 0;
    attr.background_pixel = 0;
    attr.override_redirect = 1;
    
    screen = DefaultScreenOfDisplay(main_display);
    int s = DefaultScreen(main_display);
    main_window = XCreateSimpleWindow(
        main_display,
        RootWindow(main_display,s),
        10,
        10,
        m_width,
        m_height,
        0,
        BlackPixel(main_display, s),
        WhitePixel(main_display, s)
    );
    picture = XCreatePixmap(
        main_display,
        main_window,
        m_width,
        m_height,
        DefaultDepthOfScreen(screen)
    );

    Atom type = XInternAtom(main_display, "_NET_WM_WINDOW_TYPE", False);
    Atom value = XInternAtom(main_display, "_NET_WM_WINDOW_TYPE_SPLASH", False);
    XChangeProperty(
        main_display,
        main_window,
        type,
        XA_ATOM,
        32,
        PropModeReplace,
        reinterpret_cast<unsigned char*>(&value), 1
    );
    
    // Draw background image
    imlib_context_set_display(main_display);
    imlib_context_set_visual(DefaultVisualOfScreen(screen));
    imlib_context_set_colormap(DefaultColormapOfScreen(screen));
    imlib_context_set_drawable(picture);
    imlib_render_image_on_drawable(0,0);
    XSetWindowBackgroundPixmap(main_display, main_window, picture);
    
    XClearWindow(main_display, main_window);
    Atom wmDeleteMessage = XInternAtom(main_display, "WM_DELETE_WINDOW", False);
    XSetWMProtocols(main_display, main_window, &wmDeleteMessage, 1);
    
    // Needed to accept events
    XSelectInput(main_display, main_window, ExposureMask);
    
    XMapWindow(main_display, main_window);
    
    // Draw text
    bool done = false;
    const char* msg = "Embeetle is starting up ...";
    while (done == false)
    {
        XNextEvent(main_display, &e);
        if (e.type == Expose)
        {
            XDrawString(
                main_display,
                main_window,
                DefaultGC(main_display, s),
                170,
                94,
                msg,
                strlen(msg)
            );
            done = true;
        }
    }
    
    // Flush to screen
    XFlush(main_display);
    
    // Start Embeetle executable
    FILE* pf = popen(embeetle_executable_path, "r");
    
    // Check for startup file
    for (int i = 0; i < 40; i++)
    {
        if (file_exists(startup_file_path))
        {
            remove(startup_file_path);
            break;
        }
        usleep(500000);
    }
    
    // Destroy the window
    XUnmapWindow(main_display, main_window);
    
    return 0;
}