# Home Assistant Integration - GoXLR Utility

[GoXLR Utility](https://github.com/GoXLR-on-Linux/goxlr-utility) integration for [Home Assistant](https://www.home-assistant.io/) using the [goxlrutilityapi](https://github.com/timmo001/goxlr-utility-api-py) Python package. This is a third party application from [@GoXLR-on-Linux](https://github.com/GoXLR-on-Linux) that allows for control of the GoXLR on Linux, Mac and Windows.

> This integration does not connect to the official GoXLR application!

Be sure to check out the [GoXLR Utility](https://github.com/GoXLR-on-Linux/goxlr-utility) project for more information.

![Screenshot](https://github.com/timmo001/homeassistant-integration-goxlr-utility/assets/28114703/cb6f6dac-e571-45ce-8848-45c8449ed84c)

## Installation

> The original repository (timmo001/homeassistant-integration-goxlr-utility) is archived and was removed from the HACS default store. This copy is maintained to keep it installable.

### HACS (custom repository)

1. Push this repository to your own GitHub account.
2. In Home Assistant: HACS → ⋮ → Custom repositories → add your repository URL, category **Integration**.
3. Download "GoXLR Utility" and restart Home Assistant.

### Manual

Copy `custom_components/goxlr_utility` into your Home Assistant `config/custom_components/` folder (e.g. with the Samba share or File editor/SSH add-on) and restart Home Assistant.

## Setup and Configuration

- Enable `Allow UI network access` the the settings to allow remote access on the network
- Add to Home Assistant using the UI

## Features

### Binary Sensors

- Button Pressed

### Media Players

Slider control (volume, muted)

### Sensors

- Profile

### Lights

- Accent
- Buttons (Inactive, Active)
- Faders (Bottom, Top)
