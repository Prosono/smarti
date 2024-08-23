import os
import logging
import aiofiles
import aiohttp
import json
import time

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smartiupdater"

GITHUB_REPO_URL = "https://api.github.com/repos/Prosono/smarti/contents/"
PACKAGES_URL = GITHUB_REPO_URL + "packages/"
DASHBOARDS_URL = GITHUB_REPO_URL + "dashboards/"
SMARTIUPDATER_URL = GITHUB_REPO_URL + "custom_components/smartiupdater/"
NODE_RED_FLOW_URL = GITHUB_REPO_URL + "node_red_flows/"
THEMES_URL = GITHUB_REPO_URL + "themes/smarti_themes/"
IMAGES_URL = GITHUB_REPO_URL + "www/images/smarti_images/"
CSS_URL = GITHUB_REPO_URL + "www/"
VERSION_URL = GITHUB_REPO_URL + "version.json"

PACKAGES_PATH = "/config/packages/"
THEMES_PATH = "/config/themes/smarti_themes/"
DASHBOARDS_PATH = "/config/dashboards/"
SMARTIUPDATER_PATH = "/config/custom_components/smartiupdater/"
IMAGES_PATH = "/config/www/images/smarti_images/"
CSS_PATH = "/config/www/"
NODE_RED_API_URL = "http://localhost:1880/flows"  # Node-RED API endpoint
NODE_RED_USERNAME = ""  # Replace with your Node-RED username
NODE_RED_PASSWORD = ""  # Replace with your Node-RED password

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

            if isinstance(files, list):
                file_urls = [file['download_url'] for file in files if file.get('type') == 'file']
                _LOGGER.info(f"Found {len(file_urls)} files at {url}")
                return file_urls
            elif isinstance(files, dict) and 'download_url' in files:
                _LOGGER.info(f"Found a single file at {url}")
                return [files['download_url']]
            else:
                _LOGGER.error(f"Unexpected format from {url}")
                return []
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
    ensure_directory(CSS_PATH)
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

    # Get and download Node-RED flows and merge them
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
            _LOGGER.info(f"Saving themes file to {dest_path}")
            await download_file(file_url, dest_path, session)

    # Get and download CSS files
    css_files = await get_files_from_github(CSS_URL, session)
    for file_url in css_files:
        if file_url:
            file_name = os.path.basename(file_url)
            dest_path = os.path.join(CSS_PATH, file_name)
            _LOGGER.info(f"Saving themes file to {dest_path}")
            await download_file(file_url, dest_path, session)            

async def get_latest_version(session: aiohttp.ClientSession):
    try:
        cache_buster = f"?nocache={str(time.time())}"
        async with session.get(VERSION_URL + cache_buster) as response:
            response.raise_for_status()
            version_info = await response.json()
            _LOGGER.debug(f"Fetched version info: {version_info}")

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

async def fetch_node_red_flows(session: aiohttp.ClientSession):
    """Fetch the current flows from Node-RED."""
    try:
        auth = aiohttp.BasicAuth(NODE_RED_USERNAME, NODE_RED_PASSWORD)
        async with session.get(NODE_RED_API_URL, auth=auth) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        _LOGGER.error(f"Error fetching flows from Node-RED: {str(e)}")
        return None
    
async def update_node_red_flows(session: aiohttp.ClientSession, new_flows):
    """Update the flows in Node-RED."""
    try:
        auth = aiohttp.BasicAuth(NODE_RED_USERNAME, NODE_RED_PASSWORD)
        async with session.post(NODE_RED_API_URL, json=new_flows, auth=auth) as response:
            response.raise_for_status()
            _LOGGER.info("Node-RED flows updated successfully.")
    except Exception as e:
        _LOGGER.error(f"Error updating flows in Node-RED: {str(e)}")

async def merge_strømpriser_flow(session: aiohttp.ClientSession):
    """Merge the strømpriser flow into the existing Node-RED flows using the Node-RED API."""
    try:
        # Fetch the current flows from Node-RED
        existing_flows = await fetch_node_red_flows(session)
        if existing_flows is None:
            return

        # Fetch the new strømpriser flow from GitHub
        strømpriser_files = await get_files_from_github(NODE_RED_FLOW_URL, session)
        for file_url in strømpriser_files:
            if "flows.json" in file_url:
                async with session.get(file_url) as response:
                    response.raise_for_status()
                    new_flows = await response.json()

                strømpriser_flow = next((flow for flow in new_flows if flow.get('label') == 'Strømpriser'), None)
                if strømpriser_flow:
                    _LOGGER.debug(f"Found strømpriser flow: {strømpriser_flow}")
                else:
                    _LOGGER.error("No strømpriser flow found in the fetched data.")
                    return

                # Merge strømpriser flow into existing flows
                updated_flows = [
                    flow if flow.get('label') != 'Strømpriser' else strømpriser_flow
                    for flow in existing_flows
                ]

                if not any(flow.get('label') == 'Strømpriser' for flow in updated_flows):
                    updated_flows.append(strømpriser_flow)

                # Update the flows in Node-RED
                await update_node_red_flows(session, updated_flows)

    except Exception as e:
        _LOGGER.error(f"Error merging strømpriser flow: {str(e)}")
