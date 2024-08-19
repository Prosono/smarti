import os
import logging
import base64
import aiofiles
import aiohttp
import json
import time  # Import for cache-busting
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smartiupdater"

GITHUB_REPO_URL = "https://api.github.com/repos/Prosono/smarti/contents/"
PACKAGES_URL = GITHUB_REPO_URL + "packages/"
DASHBOARDS_URL = GITHUB_REPO_URL + "dashboards/"
SMARTIUPDATER_URL = GITHUB_REPO_URL + "custom_components/smartiupdater/"
NODE_RED_FLOW_URL = "https://raw.githubusercontent.com/Prosono/smarti/main/node_red_flows/"
VERSION_URL = GITHUB_REPO_URL + "version.json"

PACKAGES_PATH = "/config/packages/"
DASHBOARDS_PATH = "/config/dashboards/"
SMARTIUPDATER_PATH = "/config/custom_components/smartiupdater/"
NODE_RED_PATH = "/addon_configs/a0d7b954_nodered/"

async def get_files_from_github(url: str, session: aiohttp.ClientSession):
    try:
        _LOGGER.info(f"Fetching file list from {url}")
        async with session.get(url) as response:
            response.raise_for_status()
            files = await response.json()

            # Check if 'files' is a list (multiple files) or a dictionary (single file)
            if isinstance(files, list):
                file_urls = [file['download_url'] for file in files if file['type'] == 'file']
                _LOGGER.info(f"Found {len(file_urls)} files at {url}")
            elif isinstance(files, dict):
                # It's a single file, add its download URL to the list
                file_urls = [files['download_url']]
                _LOGGER.info(f"Found a single file at {url}")
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
    ensure_directory(NODE_RED_PATH)

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

    # Get and download node red files
    node_red_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
    for file_url in node_red_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(NODE_RED_PATH, file_name)
            _LOGGER.info(f"Saving SmartiUpdater file to {dest_path}")
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
        _LOGGER.error(f"HTTP error occurred while fetching version info: {http_err}")
        return False, "unknown"
    except Exception as e:
        _LOGGER.error(f"Error occurred while fetching version info: {str(e)}")
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
