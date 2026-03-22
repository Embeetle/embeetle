# Embeetle
> The clean and efficient IDE, tailor-made for your MCU

**Embeetle IDE** is a lightweight IDE built from scratch, specifically for embedded software. Unlike general-purpose editors based on Eclipse or VS Code, Embeetle focuses on keeping microcontroller programming intuitive, fast, and uncomplicated. Embeetle projects are self-contained where everything you need, from source code to makefiles and linker scripts, is easily accessible right in your project folder.

For more information on the Embeetle IDE, check our website:
https://embeetle.com

Below is a quick guide on how to run and build Embeetle.

## 1. Run from executable (release)

If you just want to use Embeetle, download the latest release from GitHub:
https://github.com/Embeetle/embeetle/releases

Embeetle runs on Windows 10/11 and most recent Linux distros. On Linux it requires `glibc version 2.28` or higher (check with `$ ldd --version`).

## 2. Run from source code

> **Requirement:** Python 3.12 or higher is required.

### Windows CMD

Open a CMD terminal. Clone the repository and move into it:

```bat
git clone https://github.com/Embeetle/embeetle.git
cd embeetle
```

Create and activate a Python virtual environment, then install dependencies:

```bat
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Run Embeetle:

```bat
run.cmd
```

The first time you run Embeetle, it downloads the required tools (such as the source analyzer, 7zip, ...). Wait a few minutes.

From now onwards you can simply launch `run.cmd`. It searches for a Python virtual environment in `.venv/`, activates it, then launches Embeetle.

### Windows PowerShell

Open a PowerShell terminal. Clone the repository and move into it:

```powershell
git clone https://github.com/Embeetle/embeetle.git
cd embeetle
```

Create and activate a Python virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> **Note:** If you get a script execution error on the activation step, run this first:
> ```powershell
> Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Run Embeetle:

```powershell
.\run.ps1
```

The first time you run Embeetle, it downloads the required tools (such as the source analyzer, 7zip, ...). Wait a few minutes.

From now onwards you can simply launch `run.ps1`. It searches for a Python virtual environment in `.venv/`, activates it, then launches Embeetle.


### Linux

Open a terminal. Clone the repository and move into it:

```bash
git clone https://github.com/Embeetle/embeetle.git
cd embeetle
```

Create and activate a Python virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

> **Note:** If `python3 -m venv .venv` fails, install the venv package first:
> ```bash
> sudo apt install python3-venv
> ```

Make the run script executable and launch Embeetle:

```bash
chmod +x run.sh
./run.sh
```

The first time you run Embeetle, it downloads the required tools (such as the source analyzer, 7zip, ...). Wait a few minutes.

From now onwards, you can simply launch `run.sh`. It searches for a Python virtual environment in `.venv/`, activates it, then launches Embeetle.

> **Troubleshooting (Linux):** If Embeetle fails to start with an error like
> `Could not load the Qt platform plugin "xcb"`, Embeetle normally handles this
> automatically by bundling `libxcb-cursor.so.0` in its `sys/lib` directory and
> setting `LD_LIBRARY_PATH` at startup. If for some reason that mechanism doesn't
> work on your system, install the library manually as a last resort.
>
> Debian / Ubuntu / Mint:
> ```bash
> sudo apt install libxcb-cursor0
> ```
> Fedora / Red Hat:
> ```bash
> sudo dnf install xcb-util-cursor
> ```
> Arch / Manjaro:
> ```bash
> sudo pacman -S xcb-util-cursor
> ```
> openSUSE:
> ```bash
> sudo zypper install xcb-util-cursor
> ```

## 3. Build

Embeetle consists of several software modules (`LLVM`, `SA` and `Embeetle` itself), so the build procedure is quite complex. To build Embeetle and all its components, we've set up a separate repo with the build scripts:

https://github.com/Embeetle/automate_builds

It's really quite simple: the automated build script clones the three required repos (`LLVM`, `SA` and `Embeetle` itself), builds them one-by-one and merges the result in the `~/bld/` folder. Clone this repo and follow the instructions in its `README.md`.