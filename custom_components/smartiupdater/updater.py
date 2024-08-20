import os
import logging
import base64
import aiofiles
import aiohttp
import json
import time  # Import for cache-busting

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smartiupdater"

GITHUB_REPO_URL = "https://api.github.com/repos/Prosono/smarti/contents/"
PACKAGES_URL = GITHUB_REPO_URL + "packages/"
DASHBOARDS_URL = GITHUB_REPO_URL + "dashboards/"
SMARTIUPDATER_URL = GITHUB_REPO_URL + "custom_components/smartiupdater/"
NODE_RED_FLOW_URL = GITHUB_REPO_URL + "node_red_flows/"
THEMES_URL = GITHUB_REPO_URL + "themes/smarti_themes/"
VERSION_URL = GITHUB_REPO_URL + "version.json"

PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
DASHBOARDS_PATH = "/config/dashboards/"
SMARTIUPDATER_PATH = "/config/custom_components/smartiupdater/"
NODE_RED_PATH = "/addon_configs/a0d7b954_nodered/"

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
    ensure_directory(THEMES_PATH)

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

    # Get and download Node-RED files
    node_red_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
    for file_url in node_red_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(NODE_RED_PATH, file_name)
            _LOGGER.info(f"Saving Node-RED file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download Themes files
    themes_files = await get_files_from_github(THEMES_URL, session)
    for file_url in themes_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(THEMES_PATH, file_name)
            _LOGGER.info(f"Saving themes file to {dest_path}")
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

# Implement the merge function for Node-RED flows
async def merge_strømpriser_flow(session: aiohttp.ClientSession):
    strømpriser_file_url = os.path.join(NODE_RED_PATH, "flows.json")
    if not os.path.exists(strømpriser_file_url):
        _LOGGER.error(f"The file {strømpriser_file_url} does not exist.")
        return

    try:
        # Read existing flows.json
        _LOGGER.debug(f"Reading existing flows.json from {strømpriser_file_url}")
        async with aiofiles.open(strømpriser_file_url, 'r') as file:
            existing_flows = json.loads(await file.read())
            _LOGGER.debug(f"Existing flows.json content: {existing_flows}")

        # Fetch the new strømpriser flow from GitHub
        strømpriser_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
        for file_url in strømpriser_files:
            if "flows.json" in file_url:
                async with session.get(file_url) as response:
                    response.raise_for_status()
                    new_flows = await response.json()
                    _LOGGER.debug(f"New flows fetched from GitHub: {new_flows}")

                # Find the strømpriser flow in the new flows
                strømpriser_flow = None
                for flow in new_flows:
                    if flow.get('label') == 'strømpriser':
                        strømpriser_flow = flow
                        break

                if not strømpriser_flow:
                    _LOGGER.error("No strømpriser flow found in the fetched data.")
                    return

                # Merge or replace the strømpriser flow in existing flows
                for i, flow in enumerate(existing_flows):
                    if flow.get('label') == 'strømpriser':
                        _LOGGER.debug(f"Replacing existing strømpriser flow at index {i}.")
                        existing_flows[i] = strømpriser_flow  # Replace existing flow
                        break
                else:
                    _LOGGER.debug("Adding new strømpriser flow to existing flows.")
                    existing_flows.append(strømpriser_flow)  # Add new flow if it doesn't exist

                # Log the final merged content before saving
                _LOGGER.debug(f"Final merged flows.json content: {existing_flows}")

                # Save the merged flows.json back to the file
                async with aiofiles.open(strømpriser_file_url, 'w') as file:
                    await file.write(json.dumps(existing_flows, indent=4))
                    _LOGGER.info(f"Merged strømpriser flow successfully into {strømpriser_file_url}.")
    except Exception as e:
        _LOGGER.error(f"Error merging strømpriser flow: {str(e)}")

#Comment to check if changes are coming with        