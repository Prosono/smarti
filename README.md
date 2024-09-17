# SMARTi

**SMARTi** is a custom integration for Home Assistant, specifically designed for the [SMARTi HUB](https://www.smarti.dev/smarti-store/p/smarti-hub-63mmp-lfckw-7l3tx). This integration automates the download and update of various configuration files, including Node-RED flows, themes, dashboards, and more, from a GitHub repository. Its purpose is to ensure that the pre-installed and pre-configured Home Assistant environment for the SMARTi HUB remains up-to-date, providing users with the latest configurations for an optimized experience.

---

## ⚠️ WARNING

**Do NOT install this integration unless you are using a SMARTi HUB** ([Available here](https://www.smarti.dev/smarti-store/p/smarti-hub-63mmp-lfckw-7l3tx)). Installing this on a non-SMARTi Home Assistant setup may cause instability or issues with your installation.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)
6. [Contributing](#contributing)
7. [License](#license)

---

## Overview

The SMARTi integration provides the following features:

- **Automatic Updates**: Seamlessly download and update configuration files from a specified GitHub repository.
- **Node-RED Flow Merging**: Automatically merge the latest "Strømpriser" flow into your existing Node-RED flows.
- **Customizable Paths**: Customize file paths for different configuration types (themes, images, dashboards, etc.).
- **Version Control**: Always stay updated with the latest configuration versions.

---

## Installation

To install the SMARTi integration:

1. **Download the Integration Files:**
   - Clone or download the integration files from the GitHub repository.

2. **Place the Files in Home Assistant:**
   - Copy the `smarti` directory into the `custom_components` directory of your Home Assistant configuration.

3. **Restart Home Assistant:**
   - After copying the files, restart your Home Assistant instance to recognize the new integration.

---

## Configuration

To configure the SMARTi integration:

1. **Basic Configuration**:
   - Navigate to your Home Assistant configuration directory.
   - Modify the `configuration.yaml` file to include the SMARTi integration.

   ```yaml
   smarti:
     domain: "smarti"

Custom Paths (Optional):

Customize the paths where configuration files are stored by editing constants in the `smarti.py` file.

Example:

```python
PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
NODE_RED_PATH = "/homeassistant/flows.json"

Automation:

Set up an automation in Home Assistant to trigger the updater at a specific time or event.

## Usage

Once installed and configured, SMARTi will automatically:

- Download the latest configuration files from the GitHub repository.
- Merge the specified Node-RED flows into your existing configurations.
- Update version information in the `manifest.json` file.

### Running the Updater

You can manually trigger the update process using Home Assistant’s service call feature.

Example:

```yaml
service: smarti.update_files

