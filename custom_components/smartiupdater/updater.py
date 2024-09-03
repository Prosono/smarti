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
VERSION_URL = GITHUB_REPO_URL + "version.json"

PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
DASHBOARDS_PATH = "/config/dashboards/"
SMARTIUPDATER_PATH = "/config/custom_components/smartiupdater/"
IMAGES_PATH = "/config/www/images/smarti_images"
NODE_RED_PATH = "/homeassistant/flows.json"  # Full path to the file in Node-RED

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

def ensure_directory_exists(directory_path: str):
    """Ensure that a directory exists."""
    if not os.path.exists(directory_path):
        _LOGGER.error(f"The directory {directory_path} does not exist.")
        raise FileNotFoundError(f"The directory {directory_path} does not exist.")
    else:
        _LOGGER.info(f"Directory {directory_path} exists.")

async def download_file(url: str, dest: str, session: aiohttp.ClientSession):
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
    try:
        _LOGGER.info(f"Fetching file list from {url}")
        async with session.get(url) as response:
            response.raise_for_status()
            files = await response.json()

            _LOGGER.debug(f"API response from {url}: {files}")

            # Check if 'files' is a list (directory) or a dictionary (single file)
            if isinstance(files, list):
                for file in files:
                    _LOGGER.debug(f"Processing file: {file}")
                    if isinstance(file, dict) and file.get('type') == 'file':
                        _LOGGER.debug(f"Found file: {file['name']} with download URL: {file['download_url']}")
                    else:
                        _LOGGER.warning(f"Unexpected item in list: {file}")

                file_urls = [file['download_url'] for file in files if file.get('type') == 'file']
                _LOGGER.info(f"Found {len(file_urls)} files at {url}")
            elif isinstance(files, dict):
                # Handle case where a single file dict is returned
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

def ensure_directory(path: str):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            _LOGGER.info(f"Created directory {path}")
        else:
            _LOGGER.info(f"Directory {path} already exists")
    except Exception as e:
        _LOGGER.error(f"Error creating directory {path}: {str(e)}")

async def update_files(session: aiohttp.ClientSession):
    ensure_directory(PACKAGES_PATH)
    ensure_directory(DASHBOARDS_PATH)
    ensure_directory(SMARTIUPDATER_PATH)
    ensure_directory(THEMES_PATH)
    ensure_directory(IMAGES_PATH)

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

    # Download Node-RED files and log at each step
    node_red_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
    for file_url in node_red_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = NODE_RED_PATH  # Save directly to the Node-RED path in Home Assistant
            _LOGGER.info(f"Saving Node-RED file to {dest_path}")
            await download_file(file_url, dest_path, session)

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

async def get_latest_version(session: aiohttp.ClientSession):
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

# Implement the merge function for Node-RED flows
async def merge_strømpriser_flow(session: aiohttp.ClientSession):
    strømpriser_file_url = NODE_RED_PATH  # Use the Node-RED path for merging
    if not os.path.exists(strømpriser_file_url):
        _LOGGER.error(f"The file {strømpriser_file_url} does not exist.")
        return

    log_file_size(strømpriser_file_url, "Before writing")

    try:
        # Read the existing flows.json from the local temporary path
        async with aiofiles.open(strømpriser_file_url, 'r') as file:
            existing_flows = json.loads(await file.read())

        # Fetch the new strømpriser flow from GitHub
        strømpriser_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
        for file_url in strømpriser_files:
            if "flows.json" in file_url:
                async with session.get(file_url) as response:
                    response.raise_for_status()

                    response_text = await response.text()
                    _LOGGER.debug(f"Fetched flows.json raw content: {response_text[:200]}")

                    try:
                        new_flows = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        _LOGGER.error(f"Failed to decode JSON from response: {e}, response content: {response_text[:200]}")
                        return

                strømpriser_flow = next((flow for flow in new_flows if flow.get('label') == 'Strømpriser'), None)

                if strømpriser_flow:
                    _LOGGER.debug(f"Found strømpriser flow: {strømpriser_flow}")
                else:
                    _LOGGER.error("No strømpriser flow found in the fetched data.")
                    return

                updated_flows = [
                    flow if flow.get('label') != 'Strømpriser' else strømpriser_flow
                    for flow in existing_flows
                ]

                if not any(flow.get('label') == 'Strømpriser' for flow in updated_flows):
                    updated_flows.append(strømpriser_flow)

                async with aiofiles.open(strømpriser_file_url, 'w', encoding='utf-8') as file:
                    await file.write(json.dumps(updated_flows, indent=4))
                    await file.flush()  # Ensure all data is written to disk
                    _LOGGER.info(f"Merged strømpriser flow successfully into {strømpriser_file_url}.")
                    _LOGGER.debug(f"Final updated flows content: {json.dumps(updated_flows, indent=4)}")
        
        log_file_size(strømpriser_file_url, "After writing")
    except Exception as e:
        _LOGGER.error(f"Error merging strømpriser flow: {str(e)}")