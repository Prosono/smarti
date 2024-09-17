SMARTi
SMARTi is a custom integration for Home Assistant, specifically designed for the SMARTi HUB. This integration automates the download and update of various configuration files, including Node-RED flows, themes, dashboards, and more, from a GitHub repository. Its purpose is to ensure that the pre-installed and pre-configured Home Assistant environment for the SMARTi HUB remains up-to-date, providing users with the latest configurations for an optimized experience.

⚠️ WARNING
Do NOT install this integration unless you are using a SMARTi HUB (Available here). Installing this on a non-SMARTi Home Assistant setup may cause instability or issues with your installation.

Table of Contents
Overview
Installation
Configuration
Usage
Troubleshooting
Contributing
License
Overview
The SMARTi integration provides the following features:

Automatic Updates: Seamlessly download and update configuration files from a specified GitHub repository.
Node-RED Flow Merging: Automatically merge the latest "Strømpriser" flow into your existing Node-RED flows.
Customizable Paths: Customize file paths for different configuration types (themes, images, dashboards, etc.).
Version Control: Always stay updated with the latest configuration versions.
Installation
To install the SMARTi integration:

Download the Integration Files:
Clone or download the integration files from the GitHub repository.
Place the Files in Home Assistant:
Copy the smarti directory into the custom_components directory of your Home Assistant configuration.
Restart Home Assistant:
After copying the files, restart your Home Assistant instance to recognize the new integration.
Configuration
To configure the SMARTi integration:

Basic Configuration:

Navigate to your Home Assistant configuration directory.
Modify the configuration.yaml file to include the SMARTi integration.
yaml
Copy code
smarti:
  domain: "smarti"
Custom Paths (Optional):

Customize the paths where configuration files are stored by editing constants in the smarti.py file.
Example:

python
Copy code
PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
NODE_RED_PATH = "/homeassistant/flows.json"
Automation:

Set up an automation in Home Assistant to trigger the updater at a specific time or event.
Usage
Once installed and configured, SMARTi will automatically:

Download the latest configuration files from the GitHub repository.
Merge the specified Node-RED flows into your existing configurations.
Update version information in the manifest.json file.
Running the Updater
You can manually trigger the update process using Home Assistant’s service call feature.

Example:

yaml
Copy code
service: smarti.update_files
Troubleshooting
Common Issues
File Not Found Errors:

Ensure the specified paths exist and have the correct permissions.
Check Home Assistant logs for detailed error messages.
Permissions Errors:

Verify that Home Assistant has write access to the directories specified in the configuration.
Logs
Enable debug logging for the SMARTi integration to get more detailed logs.

Example:

yaml
Copy code
logger:
  default: info
  logs:
    custom_components.smarti: debug
Contributing
Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request on the GitHub repository.

License
This project is licensed under the MIT License. See the LICENSE file for details.

This README version should look clean and professional on GitHub. Let me know if you need any additional tweaks!
