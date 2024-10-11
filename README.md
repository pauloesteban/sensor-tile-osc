# Metabow Bridge App

Cross-platform application to pair "Metabow IMU" to send sensor data via OSC (Open Sound Control) messages.

## Build from source (Recommended)

> We assume you already have cloned this repository and you are in the corresponding folder.

## macOS

> The following instructions are intended for Apple Silicon. They might work on Intel-based machines, althought, the software is no longer tested on X86_64 architecture.

- Install [Homebrew](https://brew.sh)
- Install packages via Homebrew

```
brew install python@3.11
brew install python-tk@3.11
brew install tcl-tk
brew install pyenv
brew install pyenv-virtualenv
```

- Install Python **3.11** via Pyenv

```
PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.11
```

- Create a Python virtual environment. The environment name is the following line is `nordic`. (It can have a different name).

```
PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv virtualenv 3.11 nordic
```

- Activate your environment. (If you chose a different environment name, change accordingly)

```
pyenv activate nordic
```

- Install the dependencies

```
pip install -r requirements.txt
```

- Run from the command line

```
python metabow_bridge.py
```

### Windows

- Install [Chocolatey](https://chocolatey.org/install#individual).
- Install Python 3.11 via Chocolatey

```
choco install python311
```

- Create a virtual environment with [venv](https://docs.python.org/3.11/library/venv.html) and activate it.

- Install requirements

```
python -m pip install -r requirements.txt
python -m pip install -U "pyinstaller<5.14,>=5.5"
```

- Make the PyInstaller spec file

```
pyi-makespec --onefile --windowed metabow_bridge.py
```

- Build the executable

```
pyinstaller --clean metabow_bridge.spec --noconfirm
```

## Installation

Download the compressed file accordingly from the [Releases](https://github.com/pauloesteban/sensor-tile-osc/releases) page.

### macOS

- Uncompress the `tar.xz` file into a folder of your preference.
- Using a terminal application, remove quarantine from the `bridge.app`

```
sudo xattr -r -d com.apple.quarantine bridge.app
```

#### EV Signing

```
signtool sign /tr http://timestamp.sectigo.com /td sha256 /a sensor-tile-osc\dist\metabow_bridge.exe
```


## References

- [MP730026 DMM BLE Tutorial using Python](https://www.element14.com/community/community/element14-presents/workbenchwednesdays/blog/2020/03/09/connecting-to-mp730026-ble-dmm-with-python-and-bleak)

## Credits

Developed by Paulo Chiliguano, Travis West and KA HO Wong.

Conducted by Dr Roberto Alonso Trillo @ HKBU Academy of Music.
