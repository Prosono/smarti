import os
import logging
import base64
import aiofiles
import aiohttp
import json
import time  # Import for cache-busting
import stat  # Import for file permissions

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smarti"

GITHUB_REPO_URL = "https://api.github.com/repos/Prosono/smarti/contents/"
PACKAGES_URL = GITHUB_REPO_URL + "packages/"
DASHBOARDS_URL = GITHUB_REPO_URL + "dashboards/"
SMARTIUPDATER_URL = GITHUB_REPO_URL + "custom_components/smartiupdater/"
NODE_RED_FLOW_URL = GITHUB_REPO_URL + "node_red_flows/"
THEMES_URL = GITHUB_REPO_URL + "themes/smarti_themes/"
IMAGES_URL = GITHUB_REPO_URL + "www/images/smarti_images/"
CUSTOM_CARD_RADAR_URL = GITHUB_REPO_URL + "www/community/weather-radar-card/"

VERSION_URL = GITHUB_REPO_URL + "version.json"

PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
DASHBOARDS_PATH = "/config/dashboards/"
SMARTIUPDATER_PATH = "/config/custom_components/smartiupdater/"
IMAGES_PATH = "/config/www/images/smarti_images/"
CUSTOM_CARD_RADAR_PATH = "/config/www/community/weather-radar-card/"

# Updated Node-RED paths
NODE_RED_DIR = "/config/node-red/"
NODE_RED_FLOW_FILE = os.path.join(NODE_RED_DIR, "flows.json")

_LOGGER = logging.getLogger(__name__)

def log_file_size(filepath: str, description: str):
    """Log the size of a file with a description."""
    try:
        file_size = os.path.getsize(filepath)
        _LOGGER.info(f"{description} - File size of {filepath}: {file_size} bytes")
    except Exception as e:
        _LOGGER.error(f"Failed to get file size for {filepath}: {str(e)}")

def ensure_writable(filepath: str):
    """Ensure that the file has writable permissions."""
    try:
        # Set the file permissions to be writable by the user (owner)
        os.chmod(filepath, stat.S_IWUSR | stat.S_IRUSR)
        _LOGGER.info(f"Permissions set to writable for {filepath}.")
    except Exception as e:
        _LOGGER.error(f"Failed to set writable permissions for {filepath}: {str(e)}")

def ensure_directory(path: str):
    """Ensure that a directory exists."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            _LOGGER.info(f"Created directory {path}")
        else:
            _LOGGER.info(f"Directory {path} already exists")
    except Exception as e:
        _LOGGER.error(f"Error creating directory {path}: {str(e)}")

async def download_file(url: str, dest: str, session: aiohttp.ClientSession):
    """Download a file from a URL to a destination path."""
    try:
        _LOGGER.info(f"Attempting to download file from {url} to {dest}")
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()
            async with aiofiles.open(dest, "wb") as file:
                await file.write(content)
        _LOGGER.info(f"File successfully downloaded and saved to {dest}")
    except aiohttp.ClientError as http_err:
        _LOGGER.error(f"HTTP error occurred while downloading {url}: {http_err}")
    except Exception as e:
        _LOGGER.error(f"Error occurred while downloading {url}: {str(e)}")

async def get_files_from_github(url: str, session: aiohttp.ClientSession):
    """Get a list of file URLs from a GitHub repository directory."""
    try:
        _LOGGER.info(f"Fetching file list from {url}")
        async with session.get(url) as response:
            response.raise_for_status()
            files = await response.json()

            _LOGGER.debug(f"API response from {url}: {files}")

            # Check if 'files' is a list (directory) or a dictionary (single file)
            if isinstance(files, list):
                file_urls = [file['download_url'] for file in files if file.get('type') == 'file']
                _LOGGER.info(f"Found {len(file_urls)} files at {url}")
            elif isinstance(files, dict):
                if 'download_url' in files:
                    file_urls = [files['download_url']]
                    _LOGGER.info(f"Found a single file at {url}")
                else:
                    _LOGGER.error(f"No download URL found for the file at {url}")
                    return []
            else:
                _LOGGER.error(f"Unexpected format from {url}")
                return []

            return file_urls
    except aiohttp.ClientError as http_err:
        _LOGGER.error(f"HTTP error occurred while fetching file list from {url}: {http_err}")
        return []
    except Exception as e:
        _LOGGER.error(f"Error occurred while fetching file list from {url}: {str(e)}")
        return []

def check_file_permissions(filepath: str):
    """Check if a file is writable and log the result."""
    if os.access(filepath, os.W_OK):
        _LOGGER.info(f"File {filepath} is writable.")
    else:
        _LOGGER.error(f"File {filepath} is not writable. Check permissions.")

async def update_files(session: aiohttp.ClientSession, hass):
    """Update files from GitHub and restart Node-RED."""
    ensure_directory(PACKAGES_PATH)
    ensure_directory(DASHBOARDS_PATH)
    ensure_directory(SMARTIUPDATER_PATH)
    ensure_directory(THEMES_PATH)
    ensure_directory(IMAGES_PATH)
    ensure_directory(NODE_RED_DIR)
    ensure_directory(CUSTOM_CARD_RADAR_PATH)

    # Get and download package files
    package_files = await get_files_from_github(PACKAGES_URL, session)
    for file_url in package_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(PACKAGES_PATH, file_name)
            _LOGGER.info(f"Saving package file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download dashboard files
    dashboard_files = await get_files_from_github(DASHBOARDS_URL, session)
    for file_url in dashboard_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(DASHBOARDS_PATH, file_name)
            _LOGGER.info(f"Saving dashboard file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download custom component files
    smartiupdater_files = await get_files_from_github(SMARTIUPDATER_URL, session)
    for file_url in smartiupdater_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(SMARTIUPDATER_PATH, file_name)
            _LOGGER.info(f"Saving SmartiUpdater file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Download Node-RED flows.json file
    node_red_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
    for file_url in node_red_files:
        if file_url.endswith('flows.json'):
            dest_path = NODE_RED_FLOW_FILE
            _LOGGER.info(f"Saving Node-RED flows to {dest_path}")
            await download_file(file_url, dest_path, session)
            break  # Assuming only one flows.json

    _LOGGER.info("Starting merge of strømpriser flow.")
    await merge_strømpriser_flow(session)

    # Get and download Themes files
    themes_files = await get_files_from_github(THEMES_URL, session)
    for file_url in themes_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(THEMES_PATH, file_name)
            _LOGGER.info(f"Saving themes file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download IMAGE files
    image_files = await get_files_from_github(IMAGES_URL, session)
    for file_url in image_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(IMAGES_PATH, file_name)
            _LOGGER.info(f"Saving image file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download CUSTOM CARD files
    radar_card_files = await get_files_from_github(CUSTOM_CARD_RADAR_URL, session)
    for file_url in radar_card_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(CUSTOM_CARD_RADAR_PATH, file_name)
            _LOGGER.info(f"Saving custom card file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Restart Node-RED after updating flows
    await restart_node_red(hass)

async def get_latest_version(session: aiohttp.ClientSession):
    """Fetch the latest version information from GitHub."""
    try:
        cache_buster = f"?nocache={str(time.time())}"
        async with session.get(VERSION_URL + cache_buster) as response:
            response.raise_for_status()
            version_info = await response.json()
            _LOGGER.debug(f"Fetched version info: {version_info}")

            # Decode the base64 content
            encoded_content = version_info.get("content", "")
            if encoded_content:
                decoded_content = base64.b64decode(encoded_content).decode("utf-8")
                version_data = json.loads(decoded_content)
                latest_version = version_data.get("version", "unknown")
                return latest_version
            else:
                _LOGGER.error("No content found in the version info.")
                return "unknown"
    except aiohttp.ClientError as http_err:
        _LOGGER.error(f"HTTP error occurred while fetching version info: {http_err}")
        return "unknown"
    except Exception as e:
        _LOGGER.error(f"Error occurred while fetching version info: {str(e)}")
        return "unknown"

async def check_for_update(session: aiohttp.ClientSession, current_version: str):
    """Check if an update is available by comparing versions."""
    try:
        latest_version = await get_latest_version(session)
        _LOGGER.debug(f"Current version: {current_version}, Latest version: {latest_version}")
        return current_version != latest_version, latest_version
    except aiohttp.ClientError as http_err:
        _LOGGER.error(f"HTTP error occurred while checking for update: {http_err}")
        return False, "unknown"
    except Exception as e:
        _LOGGER.error(f"Error occurred while checking for update: {str(e)}")
        return False, "unknown"

async def update_manifest_version(latest_version: str):
    """Update the version in the manifest file."""
    manifest_file = "/config/custom_components/smartiupdater/manifest.json"
    try:
        async with aiofiles.open(manifest_file, 'r+') as file:
            manifest_data = json.loads(await file.read())
            manifest_data['version'] = latest_version
            await file.seek(0)
            await file.write(json.dumps(manifest_data, indent=4))
            await file.truncate()
        _LOGGER.info(f"Updated manifest file version to {latest_version}")
    except Exception as e:
        _LOGGER.error(f"Error updating manifest file: {str(e)}")

async def merge_strømpriser_flow(session: aiohttp.ClientSession):
    """Merge the 'Strømpriser' flow into the existing Node-RED flows."""
    strømpriser_file_url = NODE_RED_FLOW_FILE  # Use the Node-RED flows.json file

    # Ensure the flows.json file exists
    if not os.path.exists(strømpriser_file_url):
        _LOGGER.error(f"The file {strømpriser_file_url} does not exist. Creating a new one.")
        async with aiofiles.open(strømpriser_file_url, 'w') as file:
            await file.write(json.dumps([]))  # Initialize with an empty list

    log_file_size(strømpriser_file_url, "Before writing")

    try:
        # Read the existing flows.json
        async with aiofiles.open(strømpriser_file_url, 'r') as file:
            existing_flows = json.loads(await file.read())

        # Fetch the new strømpriser flow from GitHub
        strømpriser_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
        strømpriser_flow = None
        for file_url in strømpriser_files:
            if "strompriser.json" in file_url or "strømpriser.json" in file_url:
                async with session.get(file_url) as response:
                    response.raise_for_status()
                    response_text = await response.text()
                    _LOGGER.debug(f"Fetched strømpriser flow content: {response_text[:200]}")
                    try:
                        strømpriser_flow = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        _LOGGER.error(f"Failed to decode JSON from response: {e}, response content: {response_text[:200]}")
                        return
                break

        if strømpriser_flow:
            _LOGGER.debug("Found strømpriser flow.")
        else:
            _LOGGER.error("No strømpriser flow found in the fetched data.")
            return

        # Remove any existing 'Strømpriser' flow
        existing_flows = [flow for flow in existing_flows if flow.get('label') != 'Strømpriser']

        # Merge the strømpriser flow
        if isinstance(strømpriser_flow, list):
            existing_flows.extend(strømpriser_flow)
        else:
            existing_flows.append(strømpriser_flow)

        # Write back to flows.json
        async with aiofiles.open(strømpriser_file_url, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(existing_flows, indent=4))
            await file.flush()  # Ensure all data is written to disk
            _LOGGER.info(f"Merged strømpriser flow successfully into {strømpriser_file_url}.")
            _LOGGER.debug(f"Final updated flows content: {json.dumps(existing_flows, indent=4)}")

        log_file_size(strømpriser_file_url, "After writing")
    except Exception as e:
        _LOGGER.error(f"Error merging strømpriser flow: {str(e)}")

async def restart_node_red(hass):
    """Restart the Node-RED add-on in Home Assistant."""
    _LOGGER.info("Restarting Node-RED add-on.")
    try:
        await hass.services.async_call('hassio', 'addon_restart', {
            'addon': 'a0d7b954_nodered'  # Replace with your actual Node-RED add-on ID
        })
        _LOGGER.info("Node-RED add-on restarted successfully.")
    except Exception as e:
        _LOGGER.error(f"Failed to restart Node-RED add-on: {e}")