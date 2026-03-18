# Embeetle
> The clean and efficient IDE, tailor-made for your MCU

**Embeetle IDE** is a lightweight IDE built from scratch, specifically for embedded software. Unlike general-purpose editors based on Eclipse or VS Code, Embeetle focuses on keeping microcontroller programming intuitive, fast, and uncomplicated. Embeetle projects are self-contained where everything you need, from source code to makefiles and linker scripts, is easily accessible right in your project folder.

## 1. Run from executable (release)

If you just want to use Embeetle, download the latest release from GitHub:
https://github.com/Embeetle/embeetle/releases

Also check out our website:
https://embeetle.com

Embeetle runs on Windows 10/11 and most recent Linux distros. On Linux it requires `glibc version 2.28` or higher (check with `$ ldd --version`).

## 2. Run from source code

### Windows

Open a Windows CMD terminal and enter these commands:

```
# Clone the repository
> git clone https://github.com/Embeetle/embeetle.git

# Move into the repository
> cd embeetle

# Create a Python virtual environment
> python -m venv .venv

# Activate it
> call .venv/Scripts/activate.bat

# Install the required python packages in the virtual environment
> python -m pip install -r requirements.txt

# Run Embeetle
> run.cmd
```

The first time you run Embeetle, it downloads the required tools (such as the source analyzer, 7zip, ...). Wait a few minutes.

From now onwards, you can simply launch `run.cmd` to run Embeetle. It searches for a Python virtual environment in `.venv/`, activates it, then launches Embeetle.


### Linux

Open a terminal and enter these commands:

```bash
# Clone the repository
$ git clone https://github.com/Embeetle/embeetle.git

# Move into the repository
$ cd embeetle

# Create a Python virtual environment
$ python3 -m venv .venv

# Activate it
$ source .venv/bin/activate

# Install the required python packages in the virtual environment
$ python3 -m pip install -r requirements.txt

# Make the run script executable
$ chmod +x run.sh

# Run Embeetle
$ ./run.sh
```

The first time you run Embeetle, it downloads the required tools (such as the source analyzer, 7zip, ...). Wait a few minutes.

From now onwards, you can simply launch `run.sh` to run Embeetle. It searches for a Python virtual environment in `.venv/`, activates it, then launches Embeetle.

## 3. Build

Embeetle consists of several software modules, so the build procedure is quite complex. To build Embeetle and all its components, we've set up a separate repo with the build scripts:

https://github.com/Embeetle/automate_builds

Clone this repo and follow the instructions in its `README.md`.


