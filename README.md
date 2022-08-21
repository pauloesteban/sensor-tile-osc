# SensorTile Bridge App

Cross-platform application to pair STEVAL-STLCX01V1 BLE devices to send sensor data via OSC (Open Sound Control) messages.

## Installation

Download the compressed file accordingly from the [Releases](https://github.com/pauloesteban/sensor-tile-osc/releases) page.

### Windows

- Uncompress the `tar.gz` file on a folder of your preference.
- Add a Windows security [exclusion](https://support.microsoft.com/en-us/windows/add-an-exclusion-to-windows-security-811816c0-4dfd-af4a-47e4-c301afe13b26) to the `bridge` folder.
- Execute `bridge.exe`
### macOS

- Uncompress the `tar.xz` file on a folder of your preference.
- Using a terminal application, remove quarantine from the `bridge.app`

```
sudo xattr -r -d com.apple.quarantine bridge.app
```

## References

- [MP730026 DMM BLE Tutorial using Python](https://www.element14.com/community/community/element14-presents/workbenchwednesdays/blog/2020/03/09/connecting-to-mp730026-ble-dmm-with-python-and-bleak)

## Credits

Developed by Paulo Chiliguano, Travis West and KA HO Wong.

Conducted by Roberto Alonso Trillo @ HKBU Department of Music.