# SensorTile Bridge App

Cross-platform application to pair STEVAL-STLCX01V1 BLE devices to send sensor data via OSC (Open Sound Control) messages.

## Installation

Download the compressed file accordingly from the [Releases](https://github.com/pauloesteban/sensor-tile-osc/releases) page.

### macOS

- Uncompress the `tar.xz` file into a folder of your preference.
- Using a terminal application, remove quarantine from the `bridge.app`

```
sudo xattr -r -d com.apple.quarantine bridge.app
```

## Build from source

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

#### EV Signing

```
signtool sign /tr http://timestamp.sectigo.com /td sha256 /a sensor-tile-osc\dist\metabow_bridge.exe
```


## References

- [MP730026 DMM BLE Tutorial using Python](https://www.element14.com/community/community/element14-presents/workbenchwednesdays/blog/2020/03/09/connecting-to-mp730026-ble-dmm-with-python-and-bleak)

## Credits

Developed by Paulo Chiliguano, Travis West and KA HO Wong.

Conducted by Roberto Alonso Trillo @ HKBU Department of Music.
